import sys
import os
import asyncio
import time
import json
import logging
import re
import tempfile
from typing import Dict, Any, List, Tuple

# Add project root to sys.path
PROJECT_ROOT = r"d:\Project\FDA detection\fda-detection-system\backend"
sys.path.append(PROJECT_ROOT)

# Setup basic logging
logging.basicConfig(level=logging.INFO)

from app.services.scraper import ShopeeScraper
from app.services.detector import HierarchicalDetector
from app.services.ocr_engine import OCREngine
from app.utils.ranker import EvidenceRanker
from app.utils.explain_engine import ExplainEngine
from app.utils.text_cleaner import clean_text, normalize_fda

def safe_print(msg):
    try:
        print(msg)
    except:
        try:
            print(msg.encode('utf-8', 'ignore').decode('utf-8'))
        except:
            print("[Print Error] - Non-printable message")

# MOCK assess_risk_level to avoid DB issues
def assess_risk_level_mock(has_thai: bool, fda_candidates: list, category: str, scraped_fda: str = None, processed_images_count: int = 0, ocr_success_count: int = 0) -> Tuple[str, str]:
    LICENSED_CATEGORIES = ["FOOD", "DRUG", "SUPPLEMENT", "COSMETIC"]
    has_fda = len(fda_candidates) > 0
    clean_scraped = clean_text(scraped_fda) if scraped_fda else None
    
    if category == "GENERAL": return "SKIPPED", "สินค้าทั่วไป"
    if category == "UNKNOWN": return "NEED_REVIEW", "ข้อมูลไม่เพียงพอ"

    if clean_scraped and has_fda:
        norm_scraped = normalize_fda(scraped_fda)
        norm_candidates = [normalize_fda(c) for c in fda_candidates]
        if norm_scraped in norm_candidates:
            return "MATCH", "เลข อย. ตรงกัน"
        else:
            return "MISMATCH", f"ไม่ตรงกัน: ระบุ {scraped_fda} แต่พบ {', '.join(fda_candidates)}"

    if clean_scraped and not has_fda:
        reason = ExplainEngine.generate_reason(0, False, "yolo", category, "SHOP_ONLY")
        return "SHOP_ONLY", f"{reason} (ระบุ {scraped_fda} แต่ไม่พบหลักฐาน)"

    if not has_fda and not clean_scraped:
        if category in LICENSED_CATEGORIES:
            reason = ExplainEngine.generate_reason(0, False, "yolo", category, "NOT_FOUND")
            return "NOT_FOUND", reason
    
    return "PRODUCT_ONLY" if has_fda else "MATCH", "ตรวจสอบพบเลขบนผลิตภัณฑ์"

async def run_system_benchmark(url: str):
    safe_print(f"\n{'='*60}")
    safe_print(f"SYSTEM BENCHMARK: {url}")
    safe_print(f"{'='*60}\n")
    
    timings = {}
    
    # 1. Hardcoded data
    start = time.time()
    safe_print("Step 1: Retrieving product data (Pre-scraped)...")
    scraped_data = {
        "success": True,
        "title": "[แบ่งขาย] CPM Chlorpheniramine 2mg. คลอเฟน 2มก แผงละ 10เม็ด ยาแก้แพ้ ลดน้ำมูก บริษัท BL. HUA",
        "images": [
            "https://down-th.img.susercontent.com/file/th-11134207-7qul8-lituzvwastxt94",
            "https://down-th.img.susercontent.com/file/th-11134258-7r98z-lza9f5c8o71l63",
            "https://down-th.img.susercontent.com/file/th-11134207-7rasf-m85oju8eu4pb08"
        ],
        "scraped_fda_number": "1A 31/55"
    }
    timings['scraping'] = time.time() - start
    
    safe_print(f"[OK] Scraped: {scraped_data['title']}")
    safe_print(f"Scraped FDA: {scraped_data['scraped_fda_number']}")
    
    # 2. Detection (YOLO ROI)
    start = time.time()
    detector = HierarchicalDetector()
    safe_print("\nStep 2: Running Hierarchical Detector (YOLO ROI)...")
    
    evidence_candidates = []
    ocr_engine = OCREngine()
    
    # Use Image 1 (Blister pack)
    img_url = scraped_data['images'][0] 
    safe_print(f"Processing Image: {img_url}")
    
    try:
        import requests
        resp = requests.get(img_url, timeout=10)
        import numpy as np
        import cv2
        nparr = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is not None:
            # Fix: Properly handle temp file for Windows
            temp_path = os.path.join(tempfile.gettempdir(), f"bench_{int(time.time())}.jpg")
            cv2.imwrite(temp_path, img)
            
            preds = detector.yolo_detect(img)
            crops = detector.get_multi_crops(temp_path, preds)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            safe_print(f"Found {len(crops)} ROIs/Crops")
            
            for crop_data in crops:
                text, conf = ocr_engine.extract_text(crop_data['image'], context="fda")
                evidence_candidates.append({
                    "text": text, "conf": conf, "bbox": crop_data['bbox'], "source_url": img_url, "stage": crop_data['stage']
                })
    except Exception as e:
        safe_print(f"Error during detection/OCR: {e}")
            
    timings['detection_ocr'] = time.time() - start
    
    # 3. Ranking
    start = time.time()
    safe_print("\nStep 3: Ranking Evidence...")
    final_evidence = EvidenceRanker.rank_and_select(evidence_candidates, limit=4)
    timings['ranking'] = time.time() - start
    
    # 4. Risk Assessment
    start = time.time()
    safe_print("\nStep 4: Assessing Risk...")
    
    found_fdas = []
    for ev in final_evidence:
        m = re.search(r'([1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}/\d{2,4})', clean_text(ev['text']))
        if m: found_fdas.append(m.group(0))
        m2 = re.search(r'(\d{13})', clean_text(ev['text']))
        if m2: found_fdas.append(m2.group(0))
    
    risk_level, risk_reason = assess_risk_level_mock(
        has_thai=True,
        fda_candidates=list(set(found_fdas)),
        category="DRUG",
        scraped_fda=scraped_data['scraped_fda_number'],
        processed_images_count=1,
        ocr_success_count=len(evidence_candidates)
    )
    timings['risk_assessment'] = time.time() - start
    
    # 5. Summary Report
    safe_print(f"\n{'='*60}")
    safe_print("BENCHMARK REPORT")
    safe_print(f"{'='*60}")
    safe_print(f"Product: {scraped_data['title']}")
    safe_print(f"Risk Level: {risk_level}")
    safe_print(f"Reason: {risk_reason}")
    
    safe_print(f"\nTIMING BREAKDOWN:")
    for step, duration in timings.items():
        safe_print(f"  - {step.capitalize():<15}: {duration:.2f}s")
    safe_print(f"  - {'TOTAL':<15}: {sum(timings.values()):.2f}s")
    
    safe_print(f"\nEVIDENCE FOUND ({len(final_evidence)}):")
    for i, ev in enumerate(final_evidence):
        txt = ev['text'][:80].replace('\n', ' ')
        safe_print(f"  [{i+1}] {txt}... (Conf: {ev['conf']:.2f})")
    
    safe_print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(run_system_benchmark(""))
