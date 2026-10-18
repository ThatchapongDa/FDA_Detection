from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, engine
from app.models import scan_record
from app.services.scraper import ShopeeScraper
from app.services.detector import FDADetector
from app.services.ocr_engine import OCREngine
from app.utils.text_cleaner import clean_text, normalize_fda, is_valid_fda, calculate_thai_density
from app.utils.explain_engine import ExplainEngine
from app.core.logger import setup_logger
from app.config import MAX_IMAGE_SIZE_MB
from pydantic import BaseModel
import logging
import os
import requests
import tempfile
import re
import asyncio
from datetime import datetime, timedelta, timezone
import numpy as np
import cv2
import base64 as b64mod

# สร้างตารางในฐานข้อมูล (เบื้องต้นใช้ create_all แทน Alembic)
scan_record.Base.metadata.create_all(bind=engine)

# อพยพข้อมูลอัตโนมัติ: เพิ่มคอลัมน์ product_image หากยังไม่มี
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE scan_records ADD COLUMN product_image VARCHAR"))
        conn.commit()
except Exception:
    pass  # คอลัมน์มีอยู่แล้ว

import json

router = APIRouter()
logger = setup_logger("api")

# กำหนดที่อยู่ไฟล์ตั้งค่าต่างๆ
KEYWORDS_FILE = os.path.join(os.path.dirname(__file__), "../config/product_keywords.json")
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "../config/settings.json")

def load_keyword_map():
    try:
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load keywords config: {e}")
        return { "DRUG": [], "SUPPLEMENT": [], "COSMETIC": [], "FOOD": [], "GENERAL": [] }

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "crawler_delay": 30,
            "cache_expiry_hours": 24,
            "enable_medicine_filter": True,
            "max_scan_limit": 10,
            "detection_state": "B",
            "grounding_dino_prompt": "thai fda registration box . fda registration number . drug registration number . reg no . ยาสามัญประจำบ้าน . foil blister pack . medicine strip . pill blister . logo . registration label",
            "crawler_keywords": []
        }

# โหลดข้อมูลเริ่มต้น
KEYWORD_MAP = load_keyword_map()
SETTINGS = load_settings()

detector = None
ocr_engine = None
scraper = None

def ensure_services_ready():
    if detector is None or ocr_engine is None or scraper is None:
        raise HTTPException(status_code=503, detail="AI services are still starting up. Please try again in a moment.")

class ScanRequest(BaseModel):
    url: str
    force: bool = False

class SettingsUpdate(BaseModel):
    crawler_delay: int
    cache_expiry_hours: int
    enable_medicine_filter: bool
    max_scan_limit: int
    detection_state: str = "B"
    grounding_dino_prompt: str = "thai fda registration box . fda registration number . drug registration number . reg no . ยาสามัญประจำบ้าน . foil blister pack . medicine strip . pill blister . logo . registration label"
    crawler_keywords: list = []

class KeywordsUpdate(BaseModel):
    keywords: dict

def _get_fast_box_crop(image_bgr, pred, pad_ratio=0.1):
    """
    Fast box crop without SAM refinement (Phase 1 optimization).
    Returns cropped image or None if invalid.
    """
    try:
        x, y, w, h = int(pred['x']), int(pred['y']), int(pred['width']), int(pred['height'])
        pad_w = int(w * pad_ratio)
        pad_h = int(h * pad_ratio)
        
        x1 = max(0, x - w//2 - pad_w)
        y1 = max(0, y - h//2 - pad_h)
        x2 = min(image_bgr.shape[1], x + w//2 + pad_w)
        y2 = min(image_bgr.shape[0], y + h//2 + pad_h)
        
        if x2 > x1 and y2 > y1:
            crop = image_bgr[y1:y2, x1:x2]
            if crop.size > 0:
                return crop
    except Exception as e:
        logger.warning(f"Fast crop error: {e}")
    
    return None

def classify_product_type(text_content: str, fda_found_types: dict) -> str:
    """
    Categorize product dynamically based on external JSON configuration.
    Refined Priority: Supplement/Cosmetic/Drug Keywords -> Regex -> Fallback
    """
    text_lower = text_content.lower()
    
    # 1. ตรวจสอบคีย์เวิร์ดก่อน (ความแม่นยำสูงสุด)
    # ตรวจสอบอาหารเสริมก่อนเพื่อป้องกันการจัดเป็นยาในอาหารเสริมที่มีคำว่า "ยา"
    priority_order = ["DRUG", "SUPPLEMENT", "COSMETIC", "FOOD", "GENERAL"]
    
    found_categories = []
    scores = {}
    for category in ["DRUG", "SUPPLEMENT", "COSMETIC", "FOOD", "GENERAL"]:
        keywords = KEYWORD_MAP.get(category, [])
        count = sum(1 for kw in keywords if kw.lower() in text_lower)
        if count > 0:
            scores[category] = count

    if scores:
        priority_order = ["DRUG", "SUPPLEMENT", "COSMETIC", "FOOD", "GENERAL"]
        best_score = max(scores.values())
        for cat in priority_order:
            if scores.get(cat, 0) >= best_score * 0.6:
                return cat

    # 2. ใช้ Regex ตรวจสอบกรณีที่ไม่พบคีย์เวิร์ดชัดเจน
    if fda_found_types.get('drug'):
        return "DRUG"
    if fda_found_types.get('food'):
        # มักจะถ้ามีรูปแบบ อย. อาหาร + ไม่มีคีย์เวิร์ดอาหารเสริม ก็คืออาหาร
        return "FOOD"
    if fda_found_types.get('ad'):
        return "DRUG" # AD มักใช้สำหรับโฆษณายา

    # 3. ใช้หมวดหมู่ที่เหลือที่ตรวจพบจากคีย์เวิร์ดเป็นตัวเลือกสำรอง
    if found_categories:
        return found_categories[0]
            
    return "UNKNOWN"

from typing import Dict, Tuple

def calculate_risk_score(shop_data: dict, ocr_data: dict) -> Tuple[int, str, dict]:
    """
    Weighted scoring engine for FDA risk assessment, strictly separating Claim (Shop Data) and Evidence (OCR Data).
    Support multi-license (FDA + Drug Reg)
    """
    score = 0
    reasons = []
    
    # รวบรวมใบอนุญาตทั้งหมดที่ร้านค้าระบุไว้
    shop_licenses = []
    if shop_data.get('license'): shop_licenses.append(clean_text(shop_data['license']))
    if shop_data.get('drug_license'): shop_licenses.append(clean_text(shop_data['drug_license']))
    shop_licenses = list(set([l for l in shop_licenses if l]))
    
    shop_category = shop_data.get('category', 'UNKNOWN')
    
    ocr_fdas = [clean_text(f) for f in ocr_data.get('detected_licenses', [])]
    has_ocr_fda = len(ocr_fdas) > 0
    
    thai_density = ocr_data.get('thai_density', 0.0)
    has_fda_box = ocr_data.get('vision_detected', False)
    keywords_found = ocr_data.get('keywords_found', [])
    
    # --- ระบบเปรียบเทียบข้อมูล (รองรับหลายใบอนุญาต) ---
    comp_status = "NOT_FOUND"
    is_match = False
    
    if shop_licenses and has_ocr_fda:
        norm_shop_licenses = [normalize_fda(l) for l in shop_licenses]
        norm_ocr_candidates = [normalize_fda(c) for c in ocr_fdas]
        
        # ตรวจสอบว่าใบอนุญาตจากร้านค้าตรงกับใบอนุญาตจาก OCR หรือไม่
        matches = [l for l in norm_shop_licenses if l in norm_ocr_candidates]
        if matches:
            comp_status = "MATCH"
            is_match = True
        else:
            comp_status = "MISMATCH"
    elif shop_licenses and not has_ocr_fda:
        comp_status = "SHOP_ONLY"
    elif not shop_licenses and has_ocr_fda:
        comp_status = "PRODUCT_ONLY"
    else:
        comp_status = "NOT_FOUND"
        
    comparison = {
        "status": comp_status,
        "is_match": is_match
    }
    # --- สิ้นสุดระบบเปรียบเทียบ ---

    # 0. ข้อจำกัดเข้มงวด: ขีดจำกัดบทลงโทษกรณีเป็นยาและพบข้อมูลเฉพาะในร้านค้า
    if shop_category == "DRUG" and comp_status == "SHOP_ONLY":
        reasons.append("SHOP ONLY (DRUG): ผู้ขายอ้างอิงเลขทะเบียนยา แต่ AI ไม่พบหลักฐานบนสินค้า [Score Capped at 39]")
        return 39, " | ".join(reasons), comparison

    # 1. Negative Rule (Hard Constraint) for DRUG
    if shop_category == "DRUG" and thai_density < 1.0:
        return 0, "Non-Thai Drug Check Failed: ไม่พบภาษาไทยบนผลิตภัณฑ์ยา (Immediate Risk)", comparison
    
    # 2. Valid Reg. No. (OCR validated) - 30 Points
    if has_ocr_fda:
        score += 30
        reasons.append(f"พบรูปแบบเลข อย. จากภาพ ({', '.join(ocr_fdas)}) [+30]")
    
    # 3. Cross-match (Shop vs OCR) - 40 Points
    shop_display = ", ".join(shop_licenses)
    if comp_status == "MATCH":
        score += 40
        reasons.append(f"เลขทะเบียนจากภาพตรงกับที่ร้านระบุ ({shop_display}) [+40]")
    elif comp_status == "MISMATCH":
        reasons.append(f"เลขทะเบียนขัดแย้งกัน: ร้านระบุ ({shop_display}) แต่สแกนพบ ({', '.join(ocr_fdas)}) [0]")
    elif comp_status == "SHOP_ONLY":
        reasons.append(f"ผู้ขายระบุเลข ({shop_display}) แต่ไม่พบในภาพ [0]")
    elif comp_status == "PRODUCT_ONLY":
        reasons.append(f"พบเลขบนกล่อง ({', '.join(ocr_fdas)}) แต่ไม่มีการระบุจากร้านค้า [0]")
        
    # 4. คีย์เวิร์ดบังคับ - 15 คะแนน
    if keywords_found:
        score += 15
        reasons.append(f"พบคำบังคับบนฉลาก ({', '.join(keywords_found)}) [+15]")
        
    # 5. การปรากฏของภาษาไทย - 10 คะแนน
    if thai_density >= 1.0:
        score += 10
        reasons.append("พบภาษาไทยในเกณฑ์ผ่าน [+10]")
        
    # 6. Vision Model ตรวจจับion - 5 Points
    if has_fda_box:
        score += 5
        reasons.append("Vision AI ตรวจพบกรอบ/สัญลักษณ์ อย. [+5]")
        
    # 7. การเพิ่มคะแนนในหมวดหมู่ทางการแพทย์
    if shop_category == "DRUG" and score > 0:
        score += 5
        reasons.append("Medical Verification Boost [+5]")
        
    if not reasons:
        reasons.append("ไม่พบเกณฑ์ที่ผ่านเลย (Score: 0)")
        
    summary = " | ".join(reasons)
    
    # บังคับใช้จำนวนจำกัดสูงสุดอีกครั้งเผื่อหมวดหมู่อื่นต้องการในภายหลัง
    if comp_status == "SHOP_ONLY" and shop_category == "DRUG" and score >= 40:
        score = 39
        summary += " [Score strictly capped at 39 due to SHOP_ONLY violation]"
        
    return score, summary, comparison

def assess_risk_level(score: int, shop_category: str, comparison: dict, processed_images_count: int,  ocr_success_count: int, reasons_summary: str) -> tuple[str, str]:
    """
    Determines status label based on threshold scoring logic and data separation guidelines.
    """
    LICENSED_CATEGORIES = ["FOOD", "DRUG", "SUPPLEMENT", "COSMETIC"]
    comp_status = comparison.get("status", "NOT_FOUND")

    # การตัดจบคะแนน (Early Exits)
    # ถ้าหมวดหมู่ร้านค้าคือ GENERAL แต่เราพบใบอนุญาตบนตัวสินค้า, 
    # เราต้องไม่ข้าม เนื่องจากอาจเป็นสินค้าควบคุมที่ถูกจัดหมวดหมู่ผิด
    if shop_category == "GENERAL":
        if comp_status in ["MATCH", "PRODUCT_ONLY"]:
            # ตรวจสอบเสมือนว่าเป็นสินค้าควบคุม
            pass 
        else:
            return "SKIPPED", "ตรวจพบว่าเป็นสินค้าทั่วไป/บรรจุภัณฑ์ ไม่จำเป็นต้องมีเลข อย."
    
    if shop_category == "UNKNOWN":
        return "NEED_REVIEW", "ไม่สามารถระบุประเภทสินค้าได้แน่ชัด ข้อมูลไม่เพียงพอ"
    
    if processed_images_count == 0:
        return "NEED_REVIEW", "ไม่สามารถประมวลผลรูปภาพได้ (อาจมีปัญหาการดึงข้อมูล)"

    # ขั้นตอนการประเมินผล (รวมถึงสินค้าทั่วไปที่พบหลักฐาน)
    if shop_category in LICENSED_CATEGORIES or (shop_category == "GENERAL" and comp_status in ["MATCH", "PRODUCT_ONLY"]):
        if ocr_success_count == 0:
             return "UNVERIFIED", "ไม่สามารถอ่านข้อมูลจากภาพได้ (ภาพไม่ชัด/ถูกบล็อก) — ไม่สามารถยืนยันเลข อย. ได้"
            
        # Interpretation thresholds (v2.7 Evidence-based labels)
        # Interpretation thresholds (v2.7 Evidence-based labels)
        risk_level = "UNKNOWN"
        risk_reason = "Unknown"
        
        if score >= 75:
            risk_level, risk_reason = "MATCH", f"ตรวจสอบพบหลักฐานครบถ้วน (คะแนน: {score}/100) - {reasons_summary}"
        elif 40 <= score <= 74:
            if comp_status == "PRODUCT_ONLY":
                risk_level, risk_reason = "PRODUCT_ONLY", f"ตรวจพบหลักฐานบนสินค้าแต่ไม่มีข้อมูลจากผู้ขาย (คะแนน: {score}/100) - {reasons_summary}"
            elif comp_status == "SHOP_ONLY":
                risk_level, risk_reason = "SHOP_ONLY", f"พบข้อมูลจากผู้ขายแต่ไม่พบหลักฐานบนสินค้า (คะแนน: {score}/100) - {reasons_summary}"
            else:
                risk_level, risk_reason = "MISMATCH", f"พบข้อมูลขัดแย้งกัน (คะแนน: {score}/100) - {reasons_summary}"
        else: # < 40
            if comp_status in ["SHOP_ONLY", "MISMATCH", "PRODUCT_ONLY"]:
                risk_level, risk_reason = "MISMATCH", f"พบข้อพิรุธหรือหลักฐานไม่เพียงพอ (คะแนน: {score}/100) - {reasons_summary}"
            else:
                risk_level, risk_reason = "NOT_FOUND", f"ไม่พบหลักฐานที่ยืนยันได้ (คะแนน: {score}/100) - ไม่พบเลข อย. หรือฉลากที่ถูกต้อง"

        return risk_level, risk_reason

    return "MATCH", "สินค้าที่อยู่นอกเหนือการควบคุมบังคับ"

# ส่วนจัดการการตั้งค่า API ----------------------------------------------------
@router.get("/config/settings")
def get_settings():
    return load_settings()

@router.post("/config/settings")
def update_settings(update: SettingsUpdate):
    try:
        data = update.dict()
        data["detection_state"] = (data.get("detection_state") or "B").upper()
        if data["detection_state"] not in ["A", "B"]:
            raise HTTPException(status_code=400, detail="detection_state must be 'A' or 'B'")
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        global SETTINGS
        SETTINGS = data
        return {"status": "success", "message": "Settings updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/keywords")
def get_keywords():
    return load_keyword_map()

@router.post("/config/keywords")
def update_keywords(update: KeywordsUpdate):
    try:
        data = update.keywords
        with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        global KEYWORD_MAP
        KEYWORD_MAP = data
        return {"status": "success", "message": "Keywords updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ---------------------------------------------------------------------------

def get_recent_scan(db: Session, url: str, hours: int = 24):
    """Check for a recently completed scan of the same URL."""
    # ใช้การตั้งค่าส่วนกลางหากชั่วโมงเป็นค่าเริ่มต้น
    if hours == 24:
        hours = SETTINGS.get("cache_expiry_hours", 24)
        
    threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    return db.query(scan_record.ScanRecord).filter(
        scan_record.ScanRecord.product_url == url,
        scan_record.ScanRecord.status == "completed",
        scan_record.ScanRecord.created_at >= threshold
    ).order_by(scan_record.ScanRecord.created_at.desc()).first()

async def download_images_parallel(image_urls, max_workers=4):
    """
    Download multiple images in parallel using asyncio.
    Returns list of (url, img_bytes, temp_path) tuples.
    Optimization: Phase 1 - Parallel image download
    """
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "image/*"
    }
    
    async def download_image(url):
        """Download a single image"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers, timeout=15)
            )
            
            if response.status_code == 200:
                img_bytes = response.content
                
                # บันทึกไฟล์ชั่วคราวสำหรับ detector
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(img_bytes)
                    temp_path = tmp.name
                
                return (url, img_bytes, temp_path)
            else:
                logger.warning(f"Failed to download {url}: Status {response.status_code}")
                return (url, None, None)
        
        except Exception as e:
            logger.warning(f"Failed to download {url}: {e}")
            return (url, None, None)
    
    # สร้าง Task สำหรับดาวน์โหลดรูปภาพทั้งหมด
    tasks = [download_image(url) for url in image_urls]
    
    # ทำงานโดยจำกัดจำนวนการรันพร้อมกัน
    semaphore = asyncio.Semaphore(max_workers)
    
    async def bounded_download(task):
        async with semaphore:
            return await task
    
    bounded_tasks = [bounded_download(task) for task in tasks]
    results = await asyncio.gather(*bounded_tasks)
    
    return [r for r in results if r[1] is not None]

def is_junk_image(img_url, img_bytes) -> bool:
    """Enhanced v2.9 heuristic to identify junk banners while sparing low-entropy product photos (Medication packs)."""
    if not img_bytes: return True
    try:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_unchanged = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        # [การแก้ไขสำคัญ] cv2.imdecode มักจะล้มเหลวกับ WebP/AVIF จาก Shopee ให้เปลี่ยนไปใช้ Pillow แทน
        if img_unchanged is None:
            from PIL import Image
            import io
            try:
                import pillow_avif # จำเป็นต้องลงทะเบียนปลั๊กอิน AVIF อย่างชัดเจน
            except ImportError: pass
            
            try:
                pil_img = Image.open(io.BytesIO(img_bytes))
                if pil_img.mode == 'RGBA':
                    img_unchanged = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)
                else:
                    img_unchanged = cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)
                logger.info("ℹ️ Decoded image with PIL fallback (WebP/AVIF).")
            except Exception as e:
                logger.warning(f"⏭️  Reject Image: Unreadable Image Format (cv2 and PIL failed): {e}")
                return True
                
        if img_unchanged is None: 
            logger.warning("⏭️  Reject Image: Decoding strictly returned None.")
            return True
        
        h, w = img_unchanged.shape[:2]
        ratio = w / h
        is_square = 0.9 <= ratio <= 1.1
        
        # 1. ข้ามรูปภาพที่เป็น Icon หรือ UI ของระบบ
        if w < 250 or h < 250: 
            logger.info(f"⏭️  Reject Image: Too Small ({w}x{h})")
            return True
        
        # 3. คำนวณค่าวัดพื้นฐานของภาพ (คำนวณครั้งเดียว)
        img_bgr = img_unchanged[:, :, :3] if img_unchanged.shape[-1] == 4 else img_unchanged
        std_dev = np.std(img_bgr)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = (np.count_nonzero(edges) / (h * w)) * 100
        
        # 4. คำนวณเปอร์เซ็นต์ความโปร่งใส
        transparency_pct = 0
        if img_unchanged.shape[-1] == 4: # มีช่อง Alpha (โปร่งใส)
            alpha = img_unchanged[:, :, 3]
            transparency_pct = (np.sum(alpha < 127) / (h * w)) * 100
            
            # ตรวจสอบข้อมูลลวง
            if transparency_pct > 99.9:
                logger.info(f"⏭️  Reject Image: Ghost Image (100% Transparent)")
                return True
                
            # การรับรู้ความโปร่งใสตามเนื้อหา: 
            # ปฏิเสธความโปร่งใส > 70% หากขาดลักษณะทางการแพทย์ (รายละเอียดต่ำ)
            if transparency_pct > 70:
                if std_dev < 35 and edge_density < 1.5:
                    logger.info(f"⏭️  Reject Image: Empty Content / High transparency with low detail ({transparency_pct:.1f}%)")
                    return True
        else:
            # [ใหม่] การป้องกันสีพื้นเรียบ (ตัดป้ายแบนเนอร์ที่มีพื้นหลังสีขาว/ดำ)
            # ตรวจสอบพื้นที่สีขาวหรือดำที่มากเกินไป
            white_mask = np.all(img_unchanged >= 250, axis=-1)
            white_pct = (np.sum(white_mask) / (h * w)) * 100
            
            if white_pct > 70:
                # ฉลากยาบนพื้นหลังสีขาวมีรายละเอียดสูง ส่วนป้ายแบนเนอร์มักจะเป็นสีขาวเรียบๆ
                if std_dev < 35 and edge_density < 1.5:
                    logger.info(f"⏭️  Reject Image: Solid White Background ({white_pct:.1f}% white, Low Detail)")
                    return True

        # 5. Square Bypass (v3.1 Fix): Soft Pass for large square images.
        is_bypassed = False
        if is_square and w >= 500:
            is_bypassed = True
            
        # 6. High Transparency Guard (v2.7 - Strict) - No bypass for transparent images
        if img_unchanged.shape[-1] == 4:
            # รูปสินค้าจริงไม่ควรมีความโปร่งใสสูง (สติกเกอร์ Shopee มัก > 20%)
            transparency_threshold = 20.0 
            if transparency_pct > transparency_threshold:
                logger.info(f"⏭️  Reject Image: High Transparency ({transparency_pct:.1f}%) - Likely a Sticker/Overlay")
                return True
        
        # logger.debug(f"📊 Image Audit: StdDev: {std_dev:.1f}, Edges: {edge_density:.1f}%, Trans: {transparency_pct:.1f}%")
        
        # 7. Color Complexity / Flatness (Entropy Guard) (v2.9)
        if std_dev < 20 and edge_density < 1.0: # มีทั้งสีเรียบและขอบที่น้อย
            logger.info(f"⏭️  Reject Image: Junk Content (StdDev: {std_dev:.1f}, Edges: {edge_density:.1f}%)")
            return True
        
        if std_dev < 10: # สีเรียบจัด (น่าจะเป็นโลโก้/ไอคอน)
            logger.info(f"⏭️  Reject Image: Extreme Flatness (StdDev: {std_dev:.1f})")
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Guard logic failed: {e}")
        return False

@router.post("/scan")
async def create_scan(request: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """SSE endpoint for scanning"""
    return StreamingResponse(create_scan_generator(request, background_tasks, db), media_type="text/event-stream")

async def create_scan_generator(request: ScanRequest, background_tasks: BackgroundTasks, db: Session):
    """
    Receives a Shopee URL, starts the scanning process (inline for MVP), and returns results with visuals.
    """
    ensure_services_ready()
    logger.info(f"Incoming Scan Request for: {request.url}")
    
    # [NEW] Check for duplicate/cache (skip if force=True, e.g. Single Scan)
    hours = SETTINGS.get("cache_expiry_hours", 24)
    recent_record = get_recent_scan(db, request.url, hours=hours) if not request.force else None
    if recent_record:
        logger.info(f"Using cached result for URL: {request.url} (ID: {recent_record.id})")
        yield f"data: {json.dumps({'status': 'progress', 'message': f'พบข้อมูลเดิมที่เคยสแกนไว้ (ใช้ข้อมูล Cache ย้อนหลัง {hours} ชม.)...'})}\n\n"
        await asyncio.sleep(0.5)
        
        legal_info = []
        if recent_record.risk_level in ["NOT_FOUND", "SHOP_ONLY", "MISMATCH"]:
            legal_info = ExplainEngine.get_legal_violation(recent_record.product_type, ["fda_number"])

        result_payload = {
            "id": recent_record.id,
            "status": "completed",
            "risk_level": recent_record.risk_level,
            "risk_reason": recent_record.risk_reason,
            "legal_compliance": legal_info,
            "product_type": recent_record.product_type,
            "product_info": {
                "title": recent_record.product_name,
                "description": recent_record.product_description[:200] if recent_record.product_description else "",
                "category": recent_record.product_category,
                "scraped_fda": recent_record.scraped_fda_number,
                "location": recent_record.shop_location
            },
            "fda_numbers": recent_record.fda_numbers,
            "results": recent_record.scan_results if recent_record.scan_results else [],
            "is_cached": True,
            "cached_at": recent_record.created_at.isoformat()
        }
        # [CLEANUP] นำระบบ Spider ออกเพื่อป้องกันการค้นหาหลุดหมวดหมู่

        yield f"data: {json.dumps({'status': 'complete', 'result': result_payload})}\n\n"
        return

    db_record = scan_record.ScanRecord(
        product_url=request.url,
        status="processing"
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    try:
        # 1. ดึงข้อมูลด้วย Scraper ที่มีความยืดหยุ่นทนทาน
        logger.info(f"Starting Scraper for ID: {db_record.id}")
        # ตรวจสอบสถานะเบื้องต้นเพื่อแจ้งผู้ใช้
        import os
        cookie_path = "app/config/shopee_cookies.json"
        if os.path.exists(cookie_path):
            yield f"data: {json.dumps({'status': 'progress', 'message': '🍪 ตรวจพบเซสชันจริง: กำลังเข้าถึงข้อมูลด้วยบัญชีที่ลงทะเบียน...'})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'progress', 'message': '🚀 เริ่มการสแกนแบบ Stealth (Guest Mode)...'})}\n\n"
            
        yield f"data: {json.dumps({'status': 'progress', 'message': '🏠 กำลังวอร์มอัพและจำลองพฤติกรรมมนุษย์ (Simulation)...'})}\n\n"
        
        # Scraper จัดการเรื่องแคช การลองใหม่ และ circuit breaker ไว้ภายในแล้ว
        scraped_res = await scraper.scrape_product_data(request.url)
        
        if not scraped_res.get("success", False):
            error_type = scraped_res.get("error_type", "UNKNOWN")
            db_record.status = "scrape_failed"
            db_record.risk_level = "NEED_REVIEW"
            
            # แปลงประเภทข้อผิดพลาดเป็นข้อความที่เข้าใจง่าย
            if error_type == "BLOCKED":
                db_record.risk_reason = "🧱 ระบบตรวจพบการป้องกัน (WAF) แนะนำให้ใช้ Cookie จากการ Login จริงเพื่อความเสถียร"
            elif error_type == "TIMEOUT":
                db_record.risk_reason = "⏳ การเชื่อมต่อหมดเวลา (Shopee อาจจะช้าหรืออินเทอร์เน็ตมีปัญหา)"
            elif error_type == "CIRCUIT_BREAKER":
                db_record.risk_reason = "🛡️ ระบบป้องกันทำงานชั่วคราวเพื่อลดความเสี่ยงจากการโดนแบน"
            else:
                db_record.risk_reason = f"❌ เกิดปัญหาทางเทคนิค: {error_type}"
                
            db.commit()
            
            # ข้อมูลสำรองสำหรับหน้า UI
            fail_payload = {
                "id": db_record.id,
                "status": "scrape_failed",
                "risk_level": "NEED_REVIEW",
                "risk_reason": db_record.risk_reason,
                "product_info": {
                    "title": scraped_res.get("title", "Unknown Product"),
                    "category": "UNKNOWN",
                    "description": "Manual intervention required due to scraping failure."
                },
                "results": []
            }
            yield f"data: {json.dumps({'status': 'complete', 'result': fail_payload})}\n\n"
            return

        # 2. สกัดข้อมูลจากผลลัพธ์ของ Scraper
        image_urls = scraped_res.get("images", [])
        product_title = clean_text(scraped_res.get("title", ""))
        scraped_fda = scraped_res.get("scraped_fda_number")
        attributes = scraped_res.get("attributes", {})
        
        # บันทึกข้อมูลที่ขูดมาได้
        db_record.product_name = product_title
        db_record.product_image = image_urls[0] if image_urls else None  # บันทึกภาพแรกสำหรับการ์ด
        db_record.scraped_fda_number = scraped_res.get("scraped_fda_number")
        db_record.scraped_drug_number = scraped_res.get("scraped_drug_number") # รองรับข้อมูลทะเบียนยา
        db_record.scraped_ad_license = scraped_res.get("scraped_ad_license")
        
        # จัดรูปแบบสตริงคำอธิบายจากคุณลักษณะเพื่อใช้ในการจำแนกและจัดเก็บ
        attr_str = json.dumps(attributes, ensure_ascii=False)
        product_description = f"Attributes: {attr_str}"
        db_record.product_description = product_description
        
        
        # การอนุมานหมวดหมู่อัจฉริยะ: ใช้ทำงานแทนหาก Shopee ไม่ระบุหมวดหมู่มาให้
        scraped_cat = attributes.get("หมวดหมู่", "UNKNOWN")
        if scraped_cat == "UNKNOWN" and db_record.scraped_fda_number:
            if re.search(r'[1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}/\d{2,4}', db_record.scraped_fda_number):
                scraped_cat = "ยาสามัญประจำบ้าน (ยา)"
                logger.info(f"🧬 Inferred Category from FDA: {scraped_cat}")
            elif re.search(r'\d{2}[-.\s]?\d[-.\s]?\d{5}[-.\s]?\d[-.\s]?\d{4}', db_record.scraped_fda_number):
                scraped_cat = "อาหารและอาหารเสริม"
                logger.info(f"🧬 Inferred Category from FDA: {scraped_cat}")

        db_record.product_category = scraped_cat
        db_record.shop_location = attributes.get("ส่งจาก", "UNKNOWN")
        db.commit()
        
        # การใช้หมวดหมู่สำรองอัจฉริยะ: ใช้ AI จำแนกประเภทหาก Scraper ล้มเหลว
        # [ใหม่] จำแนกประเภทล่วงหน้าเพื่อหลีกเลี่ยงสถานะ UNKNOWN ใน UI
        if db_record.product_category == "UNKNOWN":
            ai_inferred_cat = classify_product_type(f"{product_title} {product_description}", {})
            friendly_cats = {
                "DRUG": "ผลิตภัณฑ์ยา (Drug)",
                "FOOD": "อาหารและอาหารเสริม (Food/Supplement)",
                "COSMETIC": "เครื่องสำอาง (Cosmetic)",
                "GENERAL": "สินค้าทั่วไป (General)"
            }
            db_record.product_category = friendly_cats.get(ai_inferred_cat, "ผลิตภัณฑ์สุขภาพ")
            logger.info(f"🧬 Scraper failed category. Fallback to AI: {db_record.product_category}")
            db.commit()
        
        logger.info(f"Scraped Title: {product_title[:50]}...")
        logger.info(f"Found {len(image_urls)} images.")
        if db_record.scraped_fda_number:
            logger.info(f"🧬 Metadata FDA Found by Scraper: {db_record.scraped_fda_number}")
        
        # ------------------------------------------------------------------
        # [แบบไดนามิก] ตัวกรองยา: ใช้กลไกการจำแนกประเภทอัจฉริยะ
        # ------------------------------------------------------------------
        filter_enabled = SETTINGS.get("enable_medicine_filter", True)
        
        if filter_enabled:
            # [ปรับปรุง] ใช้ตัวจำแนกตามคะแนนสำหรับการตัดสินใจกรองเบื้องต้น
            # วิธีนี้แข็งแกร่งกว่าการใช้รายการละเว้นแบบธรรมดา
            current_category = classify_product_type(f"{product_title} {product_description}", {})
            
            # ข้ามเฉพาะในกรณีที่หมวดหมู่ถูกระบุเป็น GENERAL หรือ UNKNOWN
            # If the title is generic or looks like a script/code placeholder (e.g. '__', '.js', 'tanstack'), DO NOT skip.
            # นี่แสดงว่า scraper ไม่สามารถดึงชื่อสินค้าจริงได้ เราจึงต้องวิเคราะห์จากภาพ
            is_generic_title = any(x in product_title.lower() for x in ["shopee", "domain", "__", ".js", "tanstack", "react-query"]) and len(product_title) < 60
            if current_category in ["GENERAL", "UNKNOWN"] and not is_generic_title:
                reason = "สินค้าไม่อยู่ในกลุ่มเป้าหมาย (ยา/อาหารเสริม/เครื่องสำอาง/อาหาร) ที่ต้องสแกน อย. ตามการตั้งค่าปัจจุบัน"
                logger.warning(f"⛔ Skipped: {product_title} - Category: {current_category} - Reason: {reason}")
                
                db_record.status = "skipped"
                db_record.result = "N/A"
                db_record.risk_level = "SKIPPED"
                db_record.product_type = "GENERAL"
                db_record.risk_reason = reason
                db_record.extracted_text = reason
                db.commit()
                
                skipped_results = [{"url": image_urls[0], "detections": [], "text": ""}] if image_urls else []
                yield f"data: {json.dumps({'status': 'complete', 'result': {'id': db_record.id, 'status': 'success', 'risk_level': 'SKIPPED', 'product_type': 'GENERAL', 'risk_summary': reason, 'product_info': {'title': product_title, 'category': 'GENERAL', 'description': product_description[:200] + '...'}, 'results': skipped_results}})}\n\n"
                return

        # 2. Process Images (Intelligent Selection & ตรวจจับ)
        all_text = []
        scan_results = []
        ocr_success_count = 0  
        
        # แนวทางแบบองค์รวม: นำภาพทั้งหมดจาก scraper (สูงสุด 20 รูปเพื่อความปลอดภัย)
        max_candidates = 20
        candidate_urls = image_urls[:max_candidates]
        
        yield f"data: {json.dumps({'status': 'progress', 'message': f'2/4 พบรูปภาพ {len(image_urls)} รูป กำลังคัดกรอง {len(candidate_urls)} ภาพที่มีคุณภาพสูงสุด...'})}\n\n"
        
        # ดาวน์โหลดตัวเลือกสำหรับการจัดอันดับและการประมวลผล
        logger.info(f"Downloading {len(candidate_urls)} candidates for ranking...")
        candidates_data = await download_images_parallel(candidate_urls, max_workers=6)
        
        if not candidates_data:
            logger.warning("Failed to download any images.")
            yield f"data: {json.dumps({'status': 'error', 'message': 'ไม่สามารถดาวน์โหลดรูปภาพเพื่อวิเคราะห์ได้'})}\n\n"
            return
        
        # การประมวลผลแบบองค์รวมตามลำดับ: ไม่มีการจัดอันดับ แค่วิเคราะห์ภาพทั้งหมดอย่างละเอียด
        yield f"data: {json.dumps({'status': 'progress', 'message': f'เริ่มการวิเคราะห์พยานหลักฐานจากรูปภาพทั้งหมด {len(candidates_data)} ภาพ...'})}\n\n"
        
        # ตั้งค่าเริ่มต้นสำหรับตัวแปรหลักฐานและบทสรุป
        food_valid, drug_valid, has_thai, shop_category = [], [], False, "UNKNOWN"
        ocr_candidates, meta_candidates, scan_results = [], [], []
        all_text = []
        
        # ศูนย์รวมรูปแบบ Regex: กำหนดครั้งเดียว ใช้สำหรับทั้งข้อมูล Metadata และ OCR
        food_pattern_strict = r'\b(?:[1-9]\d|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|30|31|32|33|34|35|36|37|38|39|40|41|42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|60|61|62|63|64|65|66|67|70|71|72|73|74|75|76|77|80|81|82|83|84|85|86|90|91|92|93|94|95|96)[-\s\.]?[1-2][-\s\.]?\d{5}[-\s\.]?\d[-\s\.]?\d{4}\b'
        food_pattern_relaxed = r'\b\d{2}[-\s\.]?\d[-\s\.]?\d{5}[-\s\.]?\d[-\s\.]?\d{4}\b'
        drug_pattern = r'\b(?:Reg\.?\s?No\.?|ทะเบียน(?:ยา)?(?:เลขที่)?|เลขที่)?[\s:\-\.]*([1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}/\d{2,4})\b'
        ad_pattern = r'ฆ[\u0E00-\u0E7F]\.?\s?\d{1,5}/\d{2,4}'

        # ตั้งค่าเริ่มต้นของตัวแปรเผื่อกรณีที่ OCR ล้มเหลวทั้งหมดทุกภาพ
        food_valid, drug_valid, has_thai, shop_category = [], [], False, "UNKNOWN"
        fda_candidates = []
        
        # 1. Establish Shop Data (Claim)
        shop_cat_raw = (db_record.product_category or '').upper()
        if any(k in shop_cat_raw for k in ["ยา", "DRUG", "HEALTH", "PHAR"]): shop_category = "DRUG"
        elif any(k in shop_cat_raw for k in ["อาหาร", "FOOD", "SUPPLEMENT", "SNACK"]): shop_category = "FOOD"
        elif any(k in shop_cat_raw for k in ["เครื่องสำอาง", "COSMETIC"]): shop_category = "COSMETIC"
            
        shop_data = {
            "license": db_record.scraped_fda_number,
            "drug_license": db_record.scraped_drug_number, # รองรับข้อมูลทะเบียนยา
            "category": shop_category,
            "title": db_record.product_name,
            "description": db_record.product_description
        }
        
        # คำนวณการอ้างอิงข้อมูลล่วงหน้า (Scraper)
        meta_food, meta_drug = [], []
        if db_record.scraped_fda_number:
            m_f = re.search(food_pattern_strict, db_record.scraped_fda_number)
            if m_f: meta_food.append(m_f.group(0))
            
        if db_record.scraped_drug_number:
            m_d = re.search(drug_pattern, db_record.scraped_drug_number)
            if m_d: meta_drug.append(m_d.group(0))
            
        meta_candidates = list(set([c for c in (meta_food + meta_drug) if c]))
        
        # 2. Main Sequential Processing Loop (Unified ตรวจจับion + OCR)
        for idx, (img_url, img_bytes, temp_path) in enumerate(candidates_data):
            # [NEW] Junk Image Filter (v3.0) - ข้ามรูปภาพที่เป็นสติกเกอร์ หรือ Banner โปรโมชัน
            if is_junk_image(img_url, img_bytes):
                logger.info(f"⏭️ Skipping Junk Image: {img_url}")
                continue
                
            yield f"data: {json.dumps({'status': 'progress', 'message': f'กำลังตรวจสอบรูปที่ {idx+1} จาก {len(candidates_data)}...'})}\n\n"
            try:
                # ตรวจจับion Pass (DINO)
                preds_raw = detector.detect(temp_path if temp_path else img_url)
                preds = preds_raw.get('predictions', [])
                relevant_preds = [p for p in preds if p.get('confidence', p.get('conf', 0)) >= 25]
                
                # เริ่มต้นการดึงข้อความ OCR และหลักฐาน...
                final_ocr_texts, crop_b64_list = [], []
                
                
                # หน่วงเวลาเล็กน้อยเพื่อให้ระบบเสถียร
                await asyncio.sleep(0.3)
                
                # OCR: ตรวจสอบเฉพาะจุดเป้าหมาย
                final_ocr_texts, crop_b64_list = [], []
                
                try:
                    def decode_bytes_safe(b):
                        img = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
                        if img is None:
                            from PIL import Image
                            import io
                            try:
                                import pillow_avif
                            except ImportError: pass
                            
                            try:
                                img = cv2.cvtColor(np.array(Image.open(io.BytesIO(b)).convert('RGB')), cv2.COLOR_RGB2BGR)
                            except: pass
                        return img

                    # ใช้ไบต์รูปภาพที่ดาวน์โหลดมาแล้ว
                    if img_bytes:
                        image_bgr = decode_bytes_safe(img_bytes)
                    else:
                        # ดาวน์โหลดสำรองหากจำเป็น
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*"
                        }
                        img_resp = requests.get(img_url, headers=headers, timeout=15)
                        img_resp.raise_for_status()
                        image_bgr = decode_bytes_safe(img_resp.content)
                        
                    if image_bgr is None:
                        logger.error(f"  > OCR/Crop Failed: Could not decode image bytes for {img_url}. It might be corrupted.")
                        continue
                    
                    # ตัวกรองสัดส่วนภาพที่เข้มงวด: ทิ้งป้ายแบนเนอร์ (สินค้าส่วนใหญ่เป็นสี่เหลี่ยมจัตุรัส 1:1)
                    h, w = image_bgr.shape[:2]
                    ratio = w / h if h > 0 else 0
                    # สินค้าทั่วไปมีสัดส่วน 0.8 ถึง 1.25 ส่วนป้ายแบนเนอร์มักจะ > 1.5 หรือ < 0.6
                    if ratio > 1.4 or ratio < 0.6:
                        logger.info(f"  > Skipping non-product image (Banner/Icon) based on ratio {ratio:.2f}: {img_url}")
                        continue
                    
                    # [PERF] Smart resize: cap ที่ 800px ถ้าภาพใหญ่กว่า (ไม่ขยายภาพเล็ก)
                    # เดิมใช้ resize → 1024×1024 เสมอ ทำให้ภาพเล็กถูกขยายโดยไม่จำเป็น
                    h, w = image_bgr.shape[:2]
                    MAX_SIDE = 800
                    if max(h, w) > MAX_SIDE:
                        scale = MAX_SIDE / max(h, w)
                        image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                    cropped_images = [image_bgr] 
                    for pred in relevant_preds:
                        if (pred['class'] in ["FDA/Registration Label", "FDA Box"] and 
                            detector.sam_model is not None):
                            # ใช้ SAM สำหรับฉลาก อย.
                            try:
                                crops = detector.crop_fda_labels_with_sam(image_bgr, pred)
                                if crops and len(crops) > 0:
                                    cropped_images.extend(crops)
                                else:
                                    # ใช้การตัดภาพแบบเร็วเป็นตัวเลือกสำรอง
                                    fast_crop = _get_fast_box_crop(image_bgr, pred)
                                    if fast_crop is not None and fast_crop.size > 0:
                                        cropped_images.append(fast_crop)
                            except Exception as e:
                                logger.warning(f"SAM refinement failed for pred: {e}, using fast crop")
                                fast_crop = _get_fast_box_crop(image_bgr, pred)
                                if fast_crop is not None and fast_crop.size > 0:
                                    cropped_images.append(fast_crop)
                        else:
                            # ตัดภาพแบบรวดเร็วสำหรับฉลากที่ไม่ใช่ อย. (ข้าม SAM)
                            fast_crop = _get_fast_box_crop(image_bgr, pred, pad_ratio=0.1)
                            if fast_crop is not None and fast_crop.size > 0:
                                cropped_images.append(fast_crop)
                    
                    # การปรับแต่งเฟส 1: OCR แบบขนาน
                    if cropped_images:
                        # ใช้ OCR แบบคู่ขนานถ้า Typhoon พร้อมใช้งาน มิฉะนั้นใช้แบบมาตรฐาน
                        if ocr_engine.typhoon_key:
                            ocr_results = await ocr_engine.process_crops_parallel_dual(
                                cropped_images, context="fda", max_workers=4
                            )
                        else:
                            ocr_results = await ocr_engine.process_crops(cropped_images, context="fda")
                        
                        # แสดงข้อความที่พบทั้งหมดใน UI เพื่อความโปร่งใส, 
                        # แต่เรายังคงติดตาม 'ความถูกต้อง' เพื่อใช้กับตรรกะแบบองค์รวมในภายหลัง
                        final_ocr_texts = [res['text'] for res in ocr_results if res.get('text')]
                        valid_ocr_texts = [res['text'] for res in ocr_results if res.get('text') and res.get('valid', True)]
                        ocr_success_count += 1
                        
                        # เข้ารหัสรูปภาพที่ถูกตัดเป็น base64 สำหรับ UI
                        for crop in cropped_images[:4]:
                            try:
                                _, buf = cv2.imencode('.jpg', crop)
                                crop_b64_list.append(
                                    b64mod.b64encode(buf.tobytes()).decode('utf-8')
                                )
                            except Exception:
                                pass
                
                except Exception as ocr_err:
                    logger.error(f"  > OCR/Crop Error: {ocr_err}")
                
                cleaned_texts = [clean_text(t) for t in final_ocr_texts if t and t.strip()]
                combined = " ".join(list(dict.fromkeys(cleaned_texts)))
                
                res = {
                    "url": img_url,
                    "detections": relevant_preds,
                    "text": combined,
                    "raw_texts": cleaned_texts,
                    "crops_b64": crop_b64_list  # รูปภาพหลักฐานเชิงประจักษ์
                }
                scan_results.append(res)
                all_text.extend(res['raw_texts'])
                
                # ส่งผลลัพธ์ภาพกลับไปที่ UI แบบเรียลไทม์
                yield f"data: {json.dumps({'status': 'image_result', 'index': idx, 'result': res})}\n\n"
                
            except Exception as e:
                logger.error(f"Error processing image {img_url}: {e}")
            
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                
        # การประมวลผลหลังการดึงข้อมูล: การวิเคราะห์แบบองค์รวม
        logger.info(f"Finished processing images. Total evaluated: {len(scan_results)}.")
        
        # 1. Consolidated Regex Extraction (OCR)
        combined_ocr_clean = " ".join(all_text) if all_text else ""
        ocr_found_food = re.findall(food_pattern_strict, combined_ocr_clean) + re.findall(food_pattern_relaxed, combined_ocr_clean)
        ocr_found_drug = re.findall(drug_pattern, combined_ocr_clean)
        ocr_found_ad = re.findall(ad_pattern, combined_ocr_clean)
        
        ocr_food_valid = [f.strip() for f in ocr_found_food if is_valid_fda(f, "FOOD")]
        ocr_drug_valid = [d.strip() for d in ocr_found_drug if is_valid_fda(d, "DRUG")]
        ocr_ad_valid = [a.strip() for a in ocr_found_ad]
        
        ocr_candidates = list(set([c for c in (ocr_food_valid + ocr_drug_valid + ocr_ad_valid) if c]))
        fda_candidates = list(set(ocr_candidates + meta_candidates))
        
        # 2. การวิเคราะห์หาคำตอบและการจำแนกประเภทสินค้า
        thai_density = calculate_thai_density(combined_ocr_clean)
        has_thai = thai_density >= 1.0
        has_fda_box = any(p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'] for r in scan_results for p in r.get('detections', []))
        
        keywords = ["คำเตือน", "เลขทะเบียนตำรับยา", "ยาสามัญประจำบ้าน", "เอกสารกำกับยา"]
        found_kws = [kw for kw in keywords if kw in combined_ocr_clean]
        
        fda_found_types = {"food": len(ocr_food_valid) > 0, "drug": len(ocr_drug_valid) > 0, "ad": len(ocr_ad_valid) > 0}
        ocr_category = classify_product_type(combined_ocr_clean, fda_found_types)
        
        # 3. Risk Assessment (Holistic)
        ocr_data = {
            "detected_licenses": ocr_candidates,
            "metadata_licenses": meta_candidates,
            "thai_density": thai_density,
            "thai_text": has_thai,
            "keywords_found": found_kws,
            "vision_detected": has_fda_box,
            "ocr_category": ocr_category
        }
        
        risk_score, score_summary, comparison = calculate_risk_score(
            shop_data=shop_data,
            ocr_data=ocr_data
        )
        
        risk_level, risk_reason = assess_risk_level(
            score=risk_score,
            shop_category=shop_category,
            comparison=comparison,
            processed_images_count=len(scan_results),
            ocr_success_count=ocr_success_count,
            reasons_summary=score_summary
        )
        
        # 4. การซิงค์ฐานข้อมูลขั้นตอนสุดท้าย
        db_record.status = "completed"
        db_record.extracted_text = combined_ocr_clean
        db_record.fda_numbers = fda_candidates
        db_record.scan_results = scan_results
        db_record.risk_level = risk_level
        db_record.risk_reason = risk_reason
        db_record.product_type = shop_category
        db.commit()

        logger.info(f"✅ Finished Holistic Analysis. Total images: {len(scan_results)}, Registration Numbers found: {len(fda_candidates)}")
        yield f"data: {json.dumps({'status': 'progress', 'message': f'3/4 วิเคราะห์เสร็จสิ้น! พบพยานหลักฐานรวม {len(fda_candidates)} ชุด จากรูปภาพ {len(scan_results)} ใบ...'})}\n\n"
        
        yield f"data: {json.dumps({'status': 'progress', 'message': '4/4 ประเมินความเสี่ยงเสร็จสิ้น กำลังเตรียมผลลัพธ์...'})}\n\n"
        
        # สร้างออบเจ็กต์ใบรับรองที่ตรวจสอบแล้วสำหรับ UI สมัยใหม่
        verified_credentials = {
            "fda_info": {
                # ส่วนของ AI: สิ่งที่พบบนรูปภาพ (ผ่าน OCR)
                "found": len(ocr_candidates) > 0,
                "text": ocr_candidates[0] if ocr_candidates else None,
                "claimed_fda": db_record.scraped_fda_number,
                "claimed_drug": db_record.scraped_drug_number
            },
            "fda_label": {
                # แก้ไข: แปลง re.search เป็น bool ชัดเจนเพื่อหลีกเลี่ยงข้อผิดพลาด JSON serializable
                "found": any(p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'] for r in scan_results for p in r.get('detections', [])) or \
                         bool(re.search(r'\b\d{13}\b', combined_ocr_clean)) or \
                         any(kw in combined_ocr_clean for kw in ["Batch", "Mfg", "Exp", "Lot No", "ครั้งที่ผลิต", "วันหมดอายุ"]),
                "count": sum(1 for r in scan_results for p in r.get('detections', []) if p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'])
            },
            "thai_language": {
                "found": has_thai,
                "text": "พบฉลากภาษาไทย" if has_thai else "ไม่พบภาษาไทย"
            },
            "drug_reg": {
                "found": len(ocr_drug_valid) > 0,
                "text": ocr_drug_valid[0] if ocr_drug_valid else None
            }
        }
        
        # [NEW] Add separate Legal Compliance Info for UI
        legal_info = []
        if db_record.risk_level in ["NOT_FOUND", "SHOP_ONLY", "MISMATCH"]:
            legal_info = ExplainEngine.get_legal_violation(db_record.product_type, ["fda_number"])

        final_res = {
            "id": db_record.id,
            "status": "completed",
            "risk_level": db_record.risk_level,
            "risk_reason": risk_reason if 'risk_reason' in locals() else "Unknown",
            "legal_compliance": legal_info, # [NEW] Detailed legal metadata for dedicated UI
            "product_type": db_record.product_type,
            "verified_credentials": verified_credentials,
            "shop_data": shop_data,
            "ocr_data": ocr_data if 'ocr_data' in locals() else {
                "detected_licenses": [],
                "thai_density": 0.0,
                "thai_text": False,
                "keywords_found": [],
                "vision_detected": False,
                "ocr_category": "UNKNOWN"
            },
            "comparison": comparison if 'comparison' in locals() else {
                "status": "NOT_FOUND",
                "is_match": False
            },
            "score": risk_score if 'risk_score' in locals() else 0,
            "product_info": {
                "title": db_record.product_name,
                "description": db_record.product_description,
                "category": shop_category,
                "scraped_fda": db_record.scraped_fda_number,
                "scraped_category": db_record.product_category,
                "location": db_record.shop_location
            },
            "fda_numbers": fda_candidates,
            "results": scan_results
        }
        yield f"data: {json.dumps({'status': 'complete', 'result': final_res})}\n\n"

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        db_record.status = "error"
        db.commit()
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

from fastapi import File, UploadFile
import shutil

@router.post("/scan/upload")
async def create_scan_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Directly scans an uploaded image file without scraping.
    Useful for testing or integrating with other systems.
    """
    ensure_services_ready()
    logger.info(f"Incoming Image Upload: {file.filename}")
    
    db_record = scan_record.ScanRecord(
        product_url="UPLOADED_FILE",
        product_name=f"Upload: {file.filename}",
        status="processing"
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    temp_file_path = None
    try:
        # บันทึกไฟล์ที่อัปโหลด
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_file_path = tmp.name
            
        logger.info(f"Saved upload to temp: {temp_file_path}")
        
        # 1. Processing (ตรวจจับ & OCR)
        all_text = []
        scan_results = []
        
        img_result = {
            "url": "local_file",
            "detections": [],
            "text": ""
        }
            
        try:
            # ตรวจจับ
            predictions = detector.detect(temp_file_path)
            preds = predictions.get('predictions', [])
            logger.info(f"  > ตรวจจับion Count: {len(preds)}")
            
            relevant_preds = []
            for p in preds:
                relevant_preds.append({
                    "x": p['x'],
                    "y": p['y'],
                    "width": p['width'],
                    "height": p['height'],
                    "confidence": p['confidence'],
                    "class": p['class']
                })
            
            img_result['detections'] = relevant_preds
            
            # ตรรกะสำหรับ OCR: ตรวจจับด้วย DINO, ตัดรูปภาพให้แม่นยำขึ้นด้วย SAM ใน detector
            ocr_texts = []
            
            if relevant_preds:
                crops = detector.crop_fda_labels(temp_file_path, predictions)
                logger.info(f"  > Cropped {len(crops)} regions for OCR.")
                
                if crops:
                    ocr_texts = ocr_engine.process_crops(crops)

            # ทำความสะอาดและบันทึกข้อความ OCR
            cleaned_ocr_texts = [clean_text(t) for t in ocr_texts if t.strip()]
            combined_ocr = " ".join(cleaned_ocr_texts)
            logger.info(f"  > OCR Result (cleaned): {combined_ocr[:50]}...")
            
            img_result['text'] = combined_ocr
            all_text.extend(cleaned_ocr_texts)

        except Exception as e:
            logger.error(f"Error processing upload: {e}", exc_info=True)
        
        scan_results.append(img_result)

        # 2. Analyze Results
        combined_ocr_clean = " ".join(all_text)
        logger.info("Starting Regex Analysis for Upload...")

        # 2.1 OCR Data (Evidence)
        food_pattern = r'\b(?:[1-9]\d|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|30|31|32|33|34|35|36|37|38|39|40|41|42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|60|61|62|63|64|65|66|67|70|71|72|73|74|75|76|77|80|81|82|83|84|85|86|90|91|92|93|94|95|96)[-\s\.]?[1-2][-\s\.]?\d{5}[-\s\.]?\d[-\s\.]?\d{4}\b'
        drug_pattern = r'\b(?:Reg\.?\s?No\.?|ทะเบียน(?:ยา)?(?:เลขที่)?|เลขที่)?[\s:\-\.]*([1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}/\d{2,4})\b'
        ad_pattern = r'ฆ[\u0E00-\u0E7F]\.?\s?\d{1,5}/\d{2,4}'
        
        found_food = re.findall(food_pattern, combined_ocr_clean)
        found_drug = re.findall(drug_pattern, combined_ocr_clean)
        found_ad = re.findall(ad_pattern, combined_ocr_clean)
        
        food_valid = [f.strip() for f in found_food if is_valid_fda(f, "FOOD")]
        drug_valid = [d.strip() for d in found_drug if is_valid_fda(d, "DRUG")]
        ad_valid = [a.strip() for a in found_ad]
        
        all_candidates = food_valid + drug_valid + ad_valid
        fda_candidates = list(set([clean_text(c) for c in all_candidates]))
        
        fda_found_types = {"food": len(food_valid) > 0, "drug": len(drug_valid) > 0, "ad": len(ad_valid) > 0}
        ocr_category = classify_product_type(combined_ocr_clean, fda_found_types)
        
        thai_density = calculate_thai_density(combined_ocr_clean)
        has_thai = thai_density >= 1.0
        has_fda_box = any(p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'] for r in scan_results for p in r.get('detections', []))
        
        keywords = ["คำเตือน", "เลขทะเบียนตำรับยา", "ยาสามัญประจำบ้าน", "เอกสารกำกับยา"]
        found_kws = [kw for kw in keywords if kw in combined_ocr_clean]
        
        ocr_data = {
            "detected_licenses": fda_candidates,
            "thai_density": thai_density,
            "thai_text": has_thai,
            "keywords_found": found_kws,
            "vision_detected": has_fda_box,
            "ocr_category": ocr_category
        }
        
        # 2.2 Mock Shop Data (Claim) for Dev Mode Testing
        # ในโหมดอัปโหลด เราไม่มีการกล่าวอ้างจากร้านค้า เราจะถือว่าร้านค้าระบุข้อมูลตรงกับที่ OCR พบ
        # เพื่อทดสอบตรรกะ 'PRODUCT_ONLY' หรือ 'MATCH' โดยจำลองว่าสินค้ามีความสอดคล้องกัน
        mock_shop_category = ocr_category if ocr_category != "UNKNOWN" else "GENERAL"
        shop_data = {
            "license": fda_candidates[0] if fda_candidates else None,
            "category": mock_shop_category,
            "title": "DEV_MODE_UPLOAD",
            "description": ""
        }

        # 3. คำนวณความเสี่ยง
        risk_score, score_summary, comparison = calculate_risk_score(
            shop_data=shop_data,
            ocr_data=ocr_data
        )
        
        risk_level, risk_reason = assess_risk_level(
            score=risk_score,
            shop_category=mock_shop_category,
            comparison=comparison,
            processed_images_count=1,
            ocr_success_count=1 if len(all_text) > 0 else 0,
            reasons_summary=score_summary
        )
        
        # อัปเดตข้อมูลในฐานข้อมูล
        db_record.status = "completed"
        db_record.extracted_text = combined_ocr_clean
        db_record.fda_numbers = fda_candidates
        db_record.scan_results = scan_results
        db_record.risk_level = risk_level
        db_record.risk_reason = risk_reason
        db_record.product_type = mock_shop_category
        db.commit()
        
        # สร้างออบเจ็กต์ใบรับรองที่ตรวจสอบแล้ว (อัปโหลด)
        verified_credentials = {
            "fda_info": {"found": len(food_valid) > 0, "text": food_valid[0] if food_valid else None},
            "fda_label": {
                "found": has_fda_box,
                "count": sum(1 for r in scan_results for p in r.get('detections', []) if p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'])
            },
            "thai_language": {"found": has_thai, "text": "พบภาษาไทย" if has_thai else "ไม่พบภาษาไทย"},
            "drug_reg": {"found": len(drug_valid) > 0, "text": drug_valid[0] if drug_valid else None}
        }

        # [NEW] Add separate Legal Compliance Info for UI
        legal_info = []
        if db_record.risk_level in ["NOT_FOUND", "SHOP_ONLY", "MISMATCH"]:
            legal_info = ExplainEngine.get_legal_violation(db_record.product_type, ["fda_number"])

        return {
            "id": db_record.id,
            "status": "completed",
            "risk_level": db_record.risk_level,
            "risk_reason": risk_reason,
            "legal_compliance": legal_info,
            "product_type": db_record.product_type,
            "verified_credentials": verified_credentials,
            "shop_data": shop_data,
            "ocr_data": ocr_data,
            "comparison": comparison,
            "score": risk_score,
            "product_info": {
                "title": db_record.product_name,
                "description": "Uploaded Image",
                "category": mock_shop_category
            },
            "fda_numbers": fda_candidates,
            "results": scan_results
        }
    
    except Exception as e:
        logger.error(f"Upload Pipeline failed: {e}", exc_info=True)
        db_record.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.get("/search")
async def search_endpoint(q: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Search Shopee by keyword and return a list of product URLs.
    Limit is usually small (e.g., 5-10) to avoid IP bans.
    """
    ensure_services_ready()
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required and must be at least 2 characters.")
        
    try:
        urls = await scraper.search_shopee(keyword=q.strip(), limit=limit)
        return {"urls": urls, "count": len(urls), "keyword": q.strip()}
    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while scraping search results.")


@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    records = db.query(scan_record.ScanRecord).order_by(scan_record.ScanRecord.id.desc()).all()
    results = []
    
    food_pattern = r'\b(?:[1-9]\d|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|30|31|32|33|34|35|36|37|38|39|40|41|42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|60|61|62|63|64|65|66|67|70|71|72|73|74|75|76|77|80|81|82|83|84|85|86|90|91|92|93|94|95|96)[-\s\.]?[1-2][-\s\.]?\d{5}[-\s\.]?\d[-\s\.]?\d{4}\b'
    drug_pattern = r'[1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}/\d{2,4}'
    
    for r in records:
        extracted_text = r.extracted_text or ""
        fda_numbers = r.fda_numbers or []
        scan_results = json.loads(r.scan_results) if isinstance(r.scan_results, str) and r.scan_results != "N/A" else (r.scan_results or [])
        
        has_food = any(re.search(food_pattern, str(n)) for n in fda_numbers)
        has_drug = any(re.search(drug_pattern, str(n)) for n in fda_numbers)
        has_thai = bool(re.search(r'[\u0E00-\u0E7F]', extracted_text))
        has_label = any(p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'] for res in scan_results for p in res.get('detections', []))

        legal_info = []
        if r.risk_level in ["NOT_FOUND", "SHOP_ONLY", "MISMATCH"]:
            legal_info = ExplainEngine.get_legal_violation(r.product_type, ["fda_number"])

        results.append({
            "id": r.id,
            "product_name": r.product_name,
            "product_url": r.product_url,
            "product_category": r.product_category,
            "product_type": r.product_type,
            "product_image": r.product_image,
            "scraped_fda_number": r.scraped_fda_number,
            "scraped_drug_number": r.scraped_drug_number,
            "risk_level": r.risk_level,
            "risk_reason": r.risk_reason,
            "legal_compliance": legal_info,
            "score": (r.confidence_score or 0) / 100 if hasattr(r, 'confidence_score') else 0,
            "created_at": r.created_at.isoformat(),
            "fda_numbers": r.fda_numbers,
            "status": r.status,
            "verified_credentials": {
                "fda_info": { "found": has_food },
                "fda_label": { "found": has_label },
                "thai_language": { "found": has_thai },
                "drug_reg": { "found": has_drug }
            }
        })
    return results

@router.delete("/history/clear")
def clear_history(db: Session = Depends(get_db)):
    """
    Deletes all records from the scan history.
    """
    try:
        num_deleted = db.query(scan_record.ScanRecord).delete()
        db.commit()
        logger.info(f"Cleared history: {num_deleted} records deleted.")
        return {"status": "success", "message": f"Deleted {num_deleted} records."}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear history.")


@router.get("/logs")
def get_system_logs(limit: int = 500):
    """
    Retrieves the system logs from the backend log file.
    Returns the last 'limit' lines.
    """
    log_file = "app.log"
    if not os.path.exists(log_file):
        return {"logs": ["Log file not found."]}
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # คืนค่าบรรทัด N สุดท้าย
            lines_out = [line.strip() for line in lines[-limit:]]
            return {"logs": lines_out}
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"logs": [f"Error reading logs: {str(e)}"]}

# ==========================================
# กลไกคราว์เลอร์ (งานสแกนอัตโนมัติเบื้องหลัง)
# ==========================================

from app.core.database import SessionLocal

crawler_state = {
    "is_running": False,
    "current_keyword": "",
    "current_status": "IDLE",
    "progress": {
        "current": 0,
        "total": 0,
        "item_name": ""
    }
}

class CrawlerRequest(BaseModel):
    keyword: str
    limit: int = 10

async def crawler_worker(keyword: str, limit: int):
    ensure_services_ready()
    crawler_state["is_running"] = True
    crawler_state["current_keyword"] = keyword
    crawler_state["current_status"] = "SEARCHING"
    crawler_state["progress"] = {"current": 0, "total": 0, "item_name": ""}
    
    try:
        # รีเซ็ตการแบ่งหน้า: เริ่มจากหน้า 0 เสมอสำหรับการค้นหาใหม่ 
        # Global offset ทำให้เกิดการข้ามคีย์เวิร์ดที่ไม่เกี่ยวข้อง
        page_offset = 0
        logger.info(f"Crawler starting fresh search for '{keyword}' from page 0")
        
        urls = await scraper.search_shopee(keyword=keyword, limit=limit, page=page_offset)
        
        if urls and urls[0] == "BLOCKED_BY_CAPTCHA":
            crawler_state["current_status"] = "BLOCKED_BY_SHOPEE"
            crawler_state["is_running"] = False
            logger.error("Crawler ABORTED: Shopee Search Blocked.")
            return

        crawler_state["progress"]["total"] = len(urls)
        
        if not urls:
            crawler_state["current_status"] = "FINISHED_NO_RESULTS"
            crawler_state["is_running"] = False
            return
            
        for i, url in enumerate(urls):
            if not crawler_state["is_running"]:
                crawler_state["current_status"] = "STOPPED_BY_USER"
                break
                
            crawler_state["progress"]["current"] = i + 1
            crawler_state["current_status"] = f"SCANNING"
            crawler_state["progress"]["item_name"] = f"รอกำลังวิเคราะห์สินค้าที่ {i+1}..."
            
            # [ใหม่] ข้ามหากเพิ่งสแกนไปเมื่อเร็วๆ นี้
            db = SessionLocal()
            try:
                # [ใหม่] ในโหมด Crawler อนุญาตให้สแกนซ้ำได้ถ้าข้อมูลเก่ากว่า 1 ชม. (เพื่อกระตุ้น Spider)
                recent = get_recent_scan(db, url, hours=1)
                if recent:
                    logger.info(f"Crawler skipping duplicate URL: {url}")
                    crawler_state["progress"]["item_name"] = f"ข้ามสินค้าที่เคยสแกนแล้ว: {recent.product_name or 'Unknown'}"
                    await asyncio.sleep(1.5) # แสดงข้อความข้ามชั่วคราว
                    continue
            finally:
                db.close()

            # สร้างเซสชันฐานข้อมูลใหม่สำหรับแต่ละรายการเพื่อหลีกเลี่ยงปัญหาเรื่องเธรด
            db = SessionLocal()
            try:
                # นำ generator เดิมมาใช้ใหม่ได้อย่างแนบเนียน โดยทำงานแบบซ่อนเร้นสมบูรณ์แบบ
                generator = create_scan_generator(ScanRequest(url=url), None, db)
                async for chunk in generator:
                    # อัปเดตชื่อรายการถ้าสามารถดึงข้อมูลจากความคืบหน้าได้ (ไม่บังคับ)
                    if isinstance(chunk, str) and "product_info" in chunk:
                        try:
                            data_str = chunk.replace("data: ", "").strip()
                            data = json.loads(data_str)
                            res = data.get("result", {})
                            if res.get("product_info", {}).get("title"):
                                title = res["product_info"]["title"]
                                crawler_state["progress"]["item_name"] = f"กำลังสแกน: {title[:40]}..."
                            
                            # ผลลัพธ์สุดท้ายของรายการ
                            if data.get("status") == "complete":
                                risk = res.get("risk_level", "UNKNOWN")
                                crawler_state["progress"]["item_name"] = f"✅ เสร็จสิ้น: {risk}"
                        except:
                            pass
            except Exception as e:
                logger.error(f"Crawler error on {url}: {e}")
            finally:
                db.close()
                
            if i < len(urls) - 1 and crawler_state["is_running"]:
                crawler_state["current_status"] = f"WAITING_ANTI_BAN"
                DELAY_SECONDS = SETTINGS.get("crawler_delay", 30)
                for w in range(DELAY_SECONDS):
                    if not crawler_state["is_running"]: break
                    crawler_state["progress"]["item_name"] = f"พักระบบ {DELAY_SECONDS-w} วิ ป้องกัน IP Block..."
                    await asyncio.sleep(1)
                    
        if crawler_state["is_running"]:
            crawler_state["current_status"] = "FINISHED_SUCCESS"
            crawler_state["is_running"] = False
            crawler_state["progress"]["item_name"] = "" # ลบชื่อเมื่อทำงานเสร็จ
            
    except Exception as e:
        logger.error(f"Crawler worker crashed: {e}")
        crawler_state["current_status"] = "ERROR_CRASHED"
        crawler_state["is_running"] = False
        crawler_state["progress"]["item_name"] = ""
    finally:
        # ตรวจสอบให้แน่ใจว่าได้เปลี่ยนสถานะเป็นหยุดทำงานแม้จะออกด้วยวิธีแปลกๆ
        crawler_state["is_running"] = False

@router.get("/scan/{scan_id}")
def get_scan_detail(scan_id: int, db: Session = Depends(get_db)):
    """Fetch deep dive details for a specific scan."""
    record = db.query(scan_record.ScanRecord).filter(scan_record.ScanRecord.id == scan_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    # คำนวณตัวชี้วัดใหม่สำหรับมุมมองรายละเอียด
    extracted_text = record.extracted_text or ""
    fda_numbers = record.fda_numbers or []
    scan_results = json.loads(record.scan_results) if isinstance(record.scan_results, str) and record.scan_results != "N/A" else (record.scan_results or [])
    
    food_pattern = r'\b(?:[1-9]\d|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|30|31|32|33|34|35|36|37|38|39|40|41|42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|60|61|62|63|64|65|66|67|70|71|72|73|74|75|76|77|80|81|82|83|84|85|86|90|91|92|93|94|95|96)[-\s\.]?[1-2][-\s\.]?\d{5}[-\s\.]?\d[-\s\.]?\d{4}\b'
    drug_pattern = r'[1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}/\d{2,4}'
    
    has_food = any(re.search(food_pattern, str(n)) for n in fda_numbers)
    has_drug = any(re.search(drug_pattern, str(n)) for n in fda_numbers)
    has_thai = bool(re.search(r'[\u0E00-\u0E7F]', extracted_text))
    has_label = any(p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'] for res in scan_results for p in res.get('detections', []))

    # [NEW] Build legal compliance metadata
    legal_info = []
    if record.risk_level in ["NOT_FOUND", "SHOP_ONLY", "MISMATCH"]:
        legal_info = ExplainEngine.get_legal_violation(record.product_type or "FOOD", ["fda_number"])

    return {
        "id": record.id,
        "product_name": record.product_name,
        "product_url": record.product_url,
        "product_category": record.product_category,
        "product_type": record.product_type,
        "scraped_fda_number": record.scraped_fda_number,
        "scraped_drug_number": record.scraped_drug_number,
        "scraped_ad_license": record.scraped_ad_license,
        "risk_level": record.risk_level,
        "risk_reason": record.risk_reason,
        "legal_compliance": legal_info, # [NEW] Thai Act/Section for modal display
        "created_at": record.created_at.isoformat(),
        "fda_numbers": record.fda_numbers,
        "status": record.status,
        "results": scan_results,
        "extracted_text": record.extracted_text,
        "verified_credentials": {
            "fda_info": { 
                "found": len(fda_numbers) > 0, 
                "text": fda_numbers[0] if fda_numbers else None 
            },
            "fda_label": { "found": has_label },
            "thai_language": { "found": has_thai },
            "drug_reg": { "found": has_drug, "text": next((n for n in fda_numbers if re.search(drug_pattern, str(n))), None) }
        }
    }

@router.post("/crawler/start")
async def start_crawler(req: CrawlerRequest, background_tasks: BackgroundTasks):
    ensure_services_ready()
    if crawler_state["is_running"]:
        raise HTTPException(status_code=400, detail="Crawler is already running.")
    background_tasks.add_task(crawler_worker, req.keyword, req.limit)
    return {"status": "success", "message": "Crawler started in background.", "keyword": req.keyword}

@router.post("/crawler/stop")
async def stop_crawler():
    crawler_state["is_running"] = False
    return {"status": "success", "message": "Crawler stopping gracefully."}

@router.get("/crawler/status")
async def get_crawler_status():
    return crawler_state

@router.get("/crawler/history")
def get_crawler_history(db: Session = Depends(get_db)):
    """ Group history records by hour for the Dashboard. """
    from sqlalchemy import desc
    records = db.query(scan_record.ScanRecord).order_by(desc(scan_record.ScanRecord.created_at)).all()
    
    # เราจะทำการจัดกลุ่มที่นี่ในไพทอนเพื่อความเรียบง่าย
    # สตริงชั่วโมง: "YYYY-MM-DD HH:00"
    grouped = {}
    for r in records:
        hour_str = r.created_at.strftime("%Y-%m-%d %H:00")
        if hour_str not in grouped:
            grouped[hour_str] = []
        
        # คำนวณสถิติโดยละเอียดใหม่สำหรับฟีด
        extracted_text = r.extracted_text or ""
        fda_numbers = r.fda_numbers or []
        scan_results = json.loads(r.scan_results) if isinstance(r.scan_results, str) and r.scan_results != "N/A" else (r.scan_results or [])
        
        # ตรวจสอบ Regex สำหรับประเภทเฉพาะ
        food_pattern = r'\b(?:[1-9]\d|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|30|31|32|33|34|35|36|37|38|39|40|41|42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|60|61|62|63|64|65|66|67|70|71|72|73|74|75|76|77|80|81|82|83|84|85|86|90|91|92|93|94|95|96)[-\s\.]?[1-2][-\s\.]?\d{5}[-\s\.]?\d[-\s\.]?\d{4}\b'
        drug_pattern = r'[1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}/\d{2,4}'
        
        has_food = any(re.search(food_pattern, str(n)) for n in fda_numbers)
        has_drug = any(re.search(drug_pattern, str(n)) for n in fda_numbers)
        has_thai = bool(re.search(r'[\u0E00-\u0E7F]', extracted_text))
        has_label = any(p.get('class') in ['FDA Box', 'FDA / Registration Label', 'FDA/Registration Label'] for res in scan_results for p in res.get('detections', []))

        grouped[hour_str].append({
            "id": r.id,
            "product_name": r.product_name,
            "product_url": r.product_url,
            "product_category": r.product_category,
            "product_type": r.product_type,
            "product_image": r.product_image,  # ภาพตัวอย่างสินค้า
            "scraped_fda_number": r.scraped_fda_number,
            "scraped_drug_number": r.scraped_drug_number, # รองรับข้อมูลทะเบียนยา
            "risk_level": r.risk_level,
            "risk_reason": r.risk_reason,
            "score": (r.confidence_score or 0) / 100,  # คะแนนที่ถูกปรับให้เป็นมาตรฐาน
            "created_at": r.created_at.isoformat(),
            "fda_numbers": r.fda_numbers,
            "status": r.status,
            "verified_credentials": {
                "fda_info": { "found": has_food },
                "fda_label": { "found": has_label },
                "thai_language": { "found": has_thai },
                "drug_reg": { "found": has_drug }
            }
        })
        
    # คืนค่าเป็นรายการของบล็อกที่จัดเรียงจากมากไปน้อย
    results = [{"hour": k, "records": v} for k, v in grouped.items()]
    return results
