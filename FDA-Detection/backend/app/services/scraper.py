import asyncio
import os
import re
import urllib.parse
import json
import io
import time
import random
import logging
import httpx
from PIL import Image
from typing import Any, Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async
from pydantic import BaseModel
from sqlalchemy import select, func
from app.core.database import SessionLocal
from app.models import scan_record

from app.core.logger import setup_logger
from app.utils.cache_manager import cache_manager

logger = setup_logger(__name__)

# ชุด User Agents มาตรฐานสำหรับการสลับใช้งาน
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
]

class ScrapedData(BaseModel):
    title: str = "Unknown Product"
    images: List[str] = []
    scraped_fda_number: Optional[str] = None
    scraped_drug_number: Optional[str] = None # รองรับข้อมูลทะเบียนยา
    scraped_ad_license: Optional[str] = None # ข้อเท็จจริงสนับสนุน
    attributes: Dict[str, str] = {}
    success: bool = False
    error_type: Optional[str] = None # หมดเวลา, ถูกบล็อก, อื่นๆ, วงจรตัด (Circuit Breaker)

class ShopeeScraper:
    _browser = None
    _context = None # [NEW] Singleton Context for Session Persistence
    _semaphore = asyncio.Semaphore(1) # [NEW] Reduced Concurrency (Max 1)
    _request_count = 0
    _last_context_time: float = 0.0
    
    def __init__(self):
        self.timeout_ms = 30000 
        
    @classmethod
    async def get_browser(cls) -> Browser:
        if not cls._browser:
            logger.info("🚀 Launching Headful-like Browser...")
            cls._playwright = await async_playwright().start()
            cls._browser = await cls._playwright.chromium.launch(
                headless=True, # เก็บไว้เป็น True แต่ใช้ Stealth และ Fingerprints
                args=["--disable-dev-shm-usage", "--no-sandbox"]
            )
        return cls._browser

    @classmethod
    async def get_context(cls, use_cookies: bool = True) -> BrowserContext:
        """[FIX 14] Persistent Context with Cookie Injection Support."""
        now = time.time()
        # รีเฟรช Context ทุกๆ 45 นาที หรือถ้าต้องการ Guest Context ใหม่
        if not cls._context or (now - cls._last_context_time > 2700):
            if cls._context: await cls._context.close()
            
            browser = await cls.get_browser()
            
            # [ใหม่] ลองโหลดคุกกี้จากการ Login จริง (ถ้ามี)
            storage_state = None
            if use_cookies:
                cookie_path = "app/config/shopee_cookies.json"
                if os.path.exists(cookie_path):
                    try:
                        with open(cookie_path, 'r') as f:
                            raw_cookies = json.load(f)
                            # Sanitize cookies (Playwright only accepts Strict, Lax, None)
                            cookie_list = raw_cookies if isinstance(raw_cookies, list) else raw_cookies.get("cookies", [])
                            for cookie in cookie_list:
                                if cookie.get("sameSite") not in ["Strict", "Lax", "None"]:
                                    cookie.pop("sameSite", None)
                            storage_state = raw_cookies if not isinstance(raw_cookies, list) else {"cookies": raw_cookies, "origins": []}
                        logger.info("🍪 Authenticated Session: Loaded cookies from shopee_cookies.json")
                    except Exception as e:
                        logger.error(f"⚠️ Failed to load cookies: {e}")
            else:
                logger.info("🎭 Using Guest Context (No Cookies)")

            cls._context = await browser.new_context(
                user_agent=USER_AGENTS[0], # [FIX] ใช้ UA ตัวเดียวกับ Header เพื่อความเนียน
                viewport={"width": random.randint(1024, 1440), "height": random.randint(768, 900)},
                locale="th-TH",
                timezone_id="Asia/Bangkok",
                storage_state=storage_state,
                extra_http_headers={
                    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": "https://www.google.com/"
                }
            )
            cls._last_context_time = now
            logger.info("🎭 New Persisted Session Context Created.")
            
        return cls._context

    @classmethod
    async def close_browser(cls):
        if cls._browser:
            await cls._browser.close()
            await cls._playwright.stop()
            cls._browser = None

    def _extract_ids(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(r'i\.(\d+)\.(\d+)', url)
        if match: return match.group(1), match.group(2)
        match = re.search(r'product/(\d+)/(\d+)', url)
        if match: return match.group(1), match.group(2)
        return None, None

    def _sanitize_shopee_url(self, url: str) -> str:
        """Remove thumbnail suffixes or compression paths to get original image."""
        if not url or "http" in url: return url
        url = re.sub(r'(_tn|_th|_heic|_[0-9]+x[0-9]+)$', '', url)
        url = re.sub(r'(_tn|_th|_heic|_[0-9]+x[0-9]+)\.[a-zA-Z]+$', '', url)
        if url.startswith("//"): url = "https:" + url
        return url

    async def _extract_hierarchical(self, page: Page, url: str) -> Tuple[bool, Optional[str], List[str], Dict[str, str], Optional[str], Optional[str], Optional[str]]:
        """
        v7.2.2 Hybrid Core Strategy (The 'Best of Both' Restoration):
        1. JSON-based extraction (Highest reliability for complete galleries)
        2. Strict Gallery Guard (Skip DOM if JSON succeeded)
        3. Mandatory Atomic Scan (Metadata recovery insurance)
        """
        title = None
        images_set = []
        attributes = {}
        scraped_fda = None
        scraped_drug = None # กำหนดค่าเริ่มต้นเพื่อหลีกเลี่ยง UnboundLocalError
        scraped_ad_license = None
        gallery_found = False
        json_data = None

        # ตัวกรอง v4.0: ละเว้น tracking ทั่วไปของ Shopee หรือขยะใน UI
        BLACKLIST = [
            "voucher", "banner", "promo", "shopee_logo", "label_badge", "free_shipping", "coupon", "coins", 
            "mall_logo", "similar", "recommend", "related", "sponsored", "official", "store", "brand", 
            "delivery", "shipping", "promotion", "guarantee", "return", "refund", "authentic"
        ]

        try:
            # [STAGE 1] การขุดข้อมูล JSON (window.__INITIAL_STATE__ หรือ mfe-initial-data)
            json_data = await page.evaluate("""() => {
                const scripts = Array.from(document.querySelectorAll('script'));
                const stateScript = scripts.find(s => s.innerText.includes('window.__INITIAL_STATE__ ='));
                if (stateScript) {
                    const match = stateScript.innerText.match(/window\.__INITIAL_STATE__\s*=\s*({.*?});/s);
                    return match ? JSON.parse(match[1]) : null;
                }
                const mfeScript = document.querySelector('script[type="text/mfe-initial-data"]');
                return mfeScript ? JSON.parse(mfeScript.innerText) : null;
            }""")

            if json_data:
                # [FIX v7.31] Deep Regex Scan on raw JSON string
                # ค้นหาเฉพาะใน key ที่เกี่ยวข้องกับ อย. เท่านั้น (ป้องกัน productid/shopid หลุดเข้ามา)
                json_str = json.dumps(json_data, ensure_ascii=False)
                # [FIX] Pattern ใหม่: ห้าม dot (.) เป็น separator เพราะ Shopee productid ใช้รูปแบบ NNNNN.NNNNN
                # รูปแบบเลข อย. ที่ถูกต้อง: XX-X-XXXXX-X-XXXX (dash หรือ space เท่านั้น ไม่ใช่ dot)
                FDA_STRICT = r'\b(\d{2}[-\s]?\d[-\s]?\d{5}[-\s]?\d[-\s]?\d{4})\b'
                if not scraped_drug:
                    m_d = re.search(r'([1-2]?[A-Z]{1,2}\s?\d{1,5}\s?/\s?\d{2,4})', json_str)
                    if m_d: 
                        scraped_drug = m_d.group(1).strip()
                        logger.info(f"🧬 JSON Deep Scan found Drug Reg: {scraped_drug}")
                if not scraped_fda:
                    # [FIX] ค้นหาเฉพาะบริเวณที่มี keyword อย./จดแจ้ง ก่อน/หลังไม่เกิน 100 ตัวอักษร
                    fda_ctx_pattern = re.compile(r'(?:อย|จดแจ้ง|fda_no|license_no|registration).{0,80}?' + FDA_STRICT, re.IGNORECASE | re.DOTALL)
                    m_f = fda_ctx_pattern.search(json_str)
                    if m_f: 
                        scraped_fda = m_f.group(1).replace('-', '').strip()
                        logger.info(f"🧬 JSON Deep Scan (context-validated) found FDA: {scraped_fda}")

                # ค้นหาข้อมูลหลักของสินค้า (ขยายพาธเพื่อความยืดหยุ่นทนทาน)
                item = json_data.get("item")
                if not item: item = json_data.get("props", {}).get("pageProps", {}).get("item", {})
                if not item: item = json_data.get("product", {}) # เส้นทางสำรอง
                
                if item:
                    title = item.get("name") or item.get("title")
                    
                    # เก็บคุณลักษณะ (อย./ทะเบียนยาใน Metadata) - v7.28 แยกประเภทชัดเจน
                    for attr in item.get("attributes", []):
                        aname, aval = str(attr.get("name", "")), str(attr.get("value", ""))
                        if aname and aval:
                            attributes[aname] = aval
                            # ตรวจสอบคีย์เวิร์ดที่เกี่ยวข้องกับใบอนุญาต (v7.29 - Expanded)
                            if any(k.lower() in aname.lower() for k in ["อย", "ใบอนุญาต", "จดแจ้ง", "FDA", "ทะเบียน", "reg", "license"]):
                                # 1. ตรวจสอบรูปแบบอาหาร/เสริม
                                # [FIX] ใช้ dash/space เท่านั้น ห้าม dot เป็น separator เพราะ Shopee ID ใช้ dot
                                m_f = re.search(r'\b(\d{2}[-\s]?\d[-\s]?\d{5}[-\s]?\d[-\s]?\d{4})\b', aval)
                                if m_f and not scraped_fda:
                                    scraped_fda = m_f.group(1).replace('-', '').strip()
                                
                                # 2. ตรวจสอบรูปแบบทะเบียนยา (v7.29 - เพิ่มความยืดหยุ่นเรื่องช่องว่าง / )
                                m_d = re.search(r'([1-2]?[A-Z]{1,2}[\s\.\-]?\d{1,5}\s?/\s?\d{2,4})', aval)
                                if m_d and not scraped_drug:
                                    scraped_drug = m_d.group(1).strip()

                    # รวบรวมรูปภาพ (จาก JSON อย่างเคร่งครัดเพื่อรักษาความครบถ้วน)
                    img_ids = item.get("images", [])
                    for img_id in img_ids:
                        clean_url = f"https://down-th.img.susercontent.com/file/{img_id}"
                        if clean_url not in images_set and not any(k in clean_url.lower() for k in BLACKLIST):
                            images_set.append(clean_url)

            # [ใหม่] การดึงคุณลักษณะและหมวดหมู่จาก DOM (ระบบสำรอง) (v7.26 - Robust)
            if not attributes or "หมวดหมู่" not in attributes:
                logger.info("🔍 Attempting Advanced DOM Extraction (Attributes & Breadcrumbs)...")
                dom_data = await page.evaluate("""() => {
                    const data = { attributes: {}, category: null };
                    
                    // 1. Scrape Breadcrumbs for Category
                    const breadcrumbs = Array.from(document.querySelectorAll('.shopee-category-view__breadcrumb-item, .flex.items-center.WvYvN_, .breadcrumb__item, ._2-vX2h'));
                    if (breadcrumbs.length > 0) {
                        const cats = breadcrumbs.map(el => el.innerText.trim()).filter(t => t && t !== '>');
                        if (cats.length > 1) {
                            data.category = cats.slice(1).join(' > '); // Skip 'Shopee'
                        }
                    }

                    // 2. Robust Attribute Matching (Text-Based)
                    const allDivs = Array.from(document.querySelectorAll('div, label, span'));
                    allDivs.forEach(el => {
                        const text = el.innerText.trim();
                        if (text.includes(':')) {
                            const parts = text.split(':');
                            if (parts.length >= 2) {
                                const key = parts[0].trim();
                                const val = parts.slice(1).join(':').trim();
                                if (key.length < 30 && val.length > 1 && val.length < 200) {
                                    data.attributes[key] = val;
                                }
                            }
                        }
                    });

                    // 3. Fallback: Search for labels and siblings
                    const labelKeywords = ['หมวดหมู่', 'เลข', 'อย', 'ใบอนุญาต', 'ทะเบียน', 'แบรนด์', 'ยี่ห้อ'];
                    allDivs.forEach(el => {
                        const text = el.innerText.trim();
                        if (labelKeywords.some(k => text === k || text === k + ':')) {
                            let valEl = el.nextElementSibling || el.parentElement?.nextElementSibling;
                            if (valEl) {
                                const key = text.replace(':', '');
                                const val = valEl.innerText.trim();
                                if (val && val.length < 200) data.attributes[key] = val;
                            }
                        }
                    });

                    return data;
                }""")
                
                if dom_data:
                    if dom_data['attributes']:
                        attributes.update(dom_data['attributes'])
                    if dom_data['category']:
                        attributes["หมวดหมู่"] = dom_data['category']
                        logger.info(f"🧬 Breadcrumb Category Found: {dom_data['category']}")

            # [การสแกนหลังสกัดข้อมูล] การระบุใบอนุญาตแบบรวมศูนย์
            # การสแกนแบบครอบคลุม: สแกนข้อความทั้งหน้าเป็นตัวเลือกสำรองด้วย
            page_text = ""
            try: page_text = await page.evaluate("document.body.innerText")
            except: pass

            license_patterns = {
                # [FIX v7.31] ห้าม dot (.) เป็น separator — ป้องกัน Shopee productid (NNNNN.NNNNN) หลุดเข้ามา
                # รูปแบบเลข อย. ที่ถูกต้อง: XX-X-XXXXX-X-XXXX
                "FDA": r'\b(\d{2}[-\s]?\d[-\s]?\d{5}[-\s]?\d[-\s]?\d{4})\b',
                "DRUG": r'([1-2]?[A-Z]{1,2}[\s\-]?\d{3,5}/(?:\d{2}|\d{4}))'
            }

            # ตรวจสอบคุณลักษณะที่เป็นทางการก่อน
            for aname, aval in attributes.items():
                aname_clean = aname.lower()
                if any(k in aname_clean for k in ["อย", "จดแจ้ง", "fda", "เลขใบอนุญาต", "license"]):
                    m = re.search(license_patterns["FDA"], aval)
                    if m and not scraped_fda:
                        scraped_fda = m.group(1)
                        logger.info(f"🎯 Found Scraped FDA (Attr): {scraped_fda}")
                
                if any(k in aname_clean for k in ["ทะเบียนยา", "ทะเบียนตำรับ", "drug reg", "reg no"]):
                    m = re.search(license_patterns["DRUG"], aval)
                    if m and not scraped_drug:
                        scraped_drug = m.group(1)
                        logger.info(f"💊 Found Scraped Drug Reg (Attr): {scraped_drug}")

            # การสแกนครอบคลุมแบบสำรอง (หากยังหาไม่พบ)
            if not scraped_fda or not scraped_drug:
                logger.info("🔍 Performing Global Text Scan for missing licenses...")
                if not scraped_fda:
                    matches = re.finditer(license_patterns["FDA"], page_text)
                    for match in matches:
                        start, end = match.start(), match.end()
                        context = page_text[max(0, start-50):min(len(page_text), end+50)].lower()
                        if any(k in context for k in ["อย", "จดแจ้ง", "fda", "license"]):
                            scraped_fda = match.group(1)
                            logger.info(f"🎯 Found Scraped FDA (Global): {scraped_fda}")
                            break
                
                if not scraped_drug:
                    matches = re.finditer(license_patterns["DRUG"], page_text)
                    for match in matches:
                        start, end = match.start(), match.end()
                        context = page_text[max(0, start-50):min(len(page_text), end+50)].lower()
                        if any(k in context for k in ["ทะเบียน", "drug", "reg"]):
                            scraped_drug = match.group(1)
                            logger.info(f"💊 Found Scraped Drug Reg (Global): {scraped_drug}")
                            break

            gallery_found = len(images_set) > 0
            if gallery_found:
                logger.info(f"⚡ [HYBRID CORE] Gallery found in JSON ({len(images_set)} images). Setting Gallery Guard.")
            
        except Exception as e:
            logger.warning(f"JSON/DOM Attribute Recovery failed: {e}")

        # [ขั้นตอนที่ 2] การสกัดจาก DOM (การสำรองรูปภาพอย่างเคร่งครัด)
        if not gallery_found:
            logger.info("🔍 Gallery not found in JSON. Starting Targeted DOM Extraction...")
            try:
                from app.core.selectors import SH_SELECTORS
                
                # กระตุ้นการโหลดแบบ Lazy Loading (การคลิกที่เป็นทางเลือก)
                next_btns = SH_SELECTORS.get("PRODUCT_IMAGE_NEXT_BUTTON", [])
                for btn_sel in next_btns:
                    try:
                        btn = await page.query_selector(btn_sel)
                        if btn and await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(0.5)
                            break
                    except: pass

                # 1. การสกัดจาก DOM แบบเจาะจง (ความสำคัญสูง)
                gallery_selectors = [
                    ".UBG7wZ",          # คลาสของรูปย่อแบบใหม่
                    ".airUhU",          # คอนเทนเนอร์รูปภาพแบบใหม่
                    ".jA1mTx",          # คลาสรูปย่อแบบดั้งเดิม
                    ".UdI7e2"           # ภาพเด่น
                ]
                dom_images = []
                for sel in gallery_selectors:
                    try:
                        container = await page.query_selector(sel)
                        if container:
                            imgs = await container.query_selector_all("img")
                            for img in imgs:
                                # การป้องกันด้วยภาพแบบผสม: ตรวจสอบการมองเห็น + สติกเกอร์
                                is_valid_visual = await img.evaluate("""(el) => {
                                    const style = window.getComputedStyle(el);
                                    const isVisible = style.display !== 'none' && 
                                                    style.visibility !== 'hidden' && 
                                                    parseFloat(style.opacity) > 0.5 &&
                                                    el.getBoundingClientRect().width > 20;
                                    if (!isVisible) return false;

                                    const junkWords = ['sticker', 'overlay', 'badge', 'promotion', 'voucher', 'discount', 'ส่งฟรี', 'ส่วนลด', 'คุ้ม'];
                                    const src = (el.src || '').toLowerCase();
                                    const alt = (el.alt || '').toLowerCase();
                                    if (junkWords.some(k => src.includes(k) || alt.includes(k))) return false;
                                    let parent = el.parentElement;
                                    let depth = 0;
                                    while (parent && depth < 6) {
                                        const className = (parent.className || '').toString().toLowerCase();
                                        if (junkWords.some(k => className.includes(k))) return false;
                                        if (className.includes('shopee-product-sticker') || className.includes('custom-label')) return false;
                                        if (parent.tagName === 'DIV' && parent.children.length > 8) break; 
                                        parent = parent.parentElement;
                                    }
                                    return true;
                                }""")
                                if not is_valid_visual: continue

                                src = await img.get_attribute("src") or await img.get_attribute("data-src")
                                if src:
                                    clean = self._sanitize_shopee_url(src)
                                    # เพิ่มคีย์เวิร์ดโปรโมชันภาษาไทยลงในการตรวจสอบบัญชีดำ
                                    thai_junk = ["ส่งฟรี", "ส่วนลด", "คุ้ม", "ราคา", "sale", "deal", "cheap"]
                                    if any(k in clean.lower() for k in (BLACKLIST + thai_junk)):
                                        continue
                                    
                                    if clean and "img.susercontent.com" in clean and clean not in dom_images:
                                        dom_images.append(clean)
                    except: pass
                
                # เพิ่มภาพจาก DOM ก่อนเนื่องจากมีความน่าเชื่อถือสูง
                for img in dom_images:
                    if img not in images_set:
                        images_set.append(img)

                # การสแกนแบบลึกด้วย Regex (เลิกใช้แล้ว - ใช้เฉพาะเมื่อไม่พบรูปภาพเลย)
                if len(images_set) == 0:
                    html_source = await page.content()
                    found_ids = re.findall(r'https://down-th\.img\.susercontent\.com/file/([a-z0-9]{32})', html_source)
                    for img_id in found_ids:
                        clean_url = f"https://down-th.img.susercontent.com/file/{img_id}"
                        if clean_url not in images_set and not any(k in clean_url.lower() for k in BLACKLIST):
                            images_set.append(clean_url)
                            if len(images_set) >= 5: break # ระบบสำรองแบบอนุรักษ์นิยม
                
            except Exception as e:
                logger.warning(f"Image Extraction Fallback failed: {e}")

        # [ขั้นตอนที่ 3] การสแกน Meta & ระดับย่อย (ต้องทำงานเสมอ: จำเป็นสำหรับความแม่นยำของ อย.)
        try:
            # กู้คืนชื่อจาก Meta หากยังคงขาดหายไป
            if not title or "Shopee" in title:
                m_title = await page.get_attribute('meta[property="og:title"]', "content")
                if m_title: title = m_title

            # การครอบคลุมของ Regex ระดับย่อย (สไตล์ OCR จากเนื้อหาดิบ)
            page_text = await page.evaluate("() => document.body.innerText")
            
            # รวมแหล่งข้อความทั้งหมดที่เป็นไปได้เพื่อเพิ่มโอกาสในการตรวจจับสูงสุด
            description = ""
            if 'json_data' in locals() and json_data:
                item = json_data.get("item") or json_data.get("props", {}).get("pageProps", {}).get("item", {})
                description = item.get("description", "")
                
            big_blob = f"{title or ''} {' '.join(attributes.values())} {description} {page_text}"
            big_blob_clean = clean_text(big_blob) # ตรวจสอบให้แน่ใจว่าทำให้อยู่ในรูปแบบมาตรฐานสำหรับ regex แล้ว
            
            # 1. รูปแบบอาหาร/อาหารเสริม (13 หลัก)
            if not scraped_fda:
                m_f = re.search(r'\b\d{13}\b|\b\d{2}-\d-\d{5}-\d-\d{4}\b', big_blob_clean)
                if m_f: scraped_fda = m_f.group(0).replace('-', '').strip()
            
            # 2. รูปแบบทะเบียนยา (v7.30 - ถอด \b ออกเพื่อความครอบคลุมสูงสุด)
            if not scraped_drug:
                m_d = re.search(r'([1-2]?[A-Z]{1,2}\s?\d{1,5}\s?/\s?\d{2,4})', big_blob_clean)
                if m_d: scraped_drug = m_d.group(0).strip()

            # 3. Ad License Recovery (ฆพ. / ฆอ.)
            if not scraped_ad_license:
                m_ad = re.search(r'([ฆม][พ-อ]\.?\s?\d{1,4}/\d{4})', big_blob_clean)
                if m_ad: scraped_ad_license = m_ad.group(0).strip()
                
            if scraped_fda or scraped_drug or scraped_ad_license:
                logger.info(f"🧬 Atomic Scan Success: FDA:{scraped_fda} | DRUG:{scraped_drug} | AD:{scraped_ad_license}")

        except Exception as e:
            logger.debug(f"Metadata Recovery failed: {e}")

        # การกำจัดข้อมูลซ้ำซ้อนและทำความสะอาดขั้นตอนสุดท้าย (ไม่มีการจำกัดฮาร์ดโค้ด 10 อันอีกต่อไป) images_set = list(dict.fromkeys(images_set))
        is_complete = bool(title and len(images_set) > 0)
        
        logger.info(f"🏁 Scraper Summary: FINAL_IMAGES:{len(images_set)} | TITLE:{(title or '')[:30]}... | SUCCESS:{is_complete}")
        return is_complete, title, images_set, attributes, scraped_fda, scraped_drug, scraped_ad_license

    async def _fetch_with_playwright(self, url: str, use_session: bool = True, ua: Optional[str] = None, fast_mode: bool = False) -> ScrapedData:
        """Fetch: Restoration - Single Scan uses EXACT original logic / Crawler uses New Stealth."""
        async with self._semaphore:
            if fast_mode:
                # [โหมดดั้งเดิมเป๊ะๆ สำหรับ Single Scan + รองรับคุกกี้]
                browser = await self.get_browser()
                current_ua = ua or USER_AGENTS[0]
                
                # ลองใช้คุกกี้จากไฟล์ก่อน (ลำดับความสำคัญสูงสุด)
                storage_state = None
                cookie_path = "app/config/shopee_cookies.json"
                if os.name == 'nt' and not os.path.exists(cookie_path):
                    # ถ้าอยู่บน Windows ให้เช็ค path เต็มเผื่อกรณีรันจากโฟลเดอร์อื่น
                    alt_path = os.path.join(os.getcwd(), "app", "config", "shopee_cookies.json")
                    if os.path.exists(alt_path): cookie_path = alt_path

                if os.path.exists(cookie_path):
                    try:
                        with open(cookie_path, 'r') as f:
                            raw_cookies = json.load(f)
                            
                            cookie_list = raw_cookies if isinstance(raw_cookies, list) else raw_cookies.get("cookies", [])
                            for cookie in cookie_list:
                                if cookie.get("sameSite") not in ["Strict", "Lax", "None"]:
                                    cookie.pop("sameSite", None)

                            if isinstance(raw_cookies, list):
                                storage_state = {"cookies": raw_cookies, "origins": []}
                            else:
                                storage_state = raw_cookies
                    except: pass
                
                # ถ้าไม่มีคุกกี้จากไฟล์ ค่อยใช้จาก Cache
                if not storage_state and use_session:
                    storage_state = cache_manager.get_session_state()
                
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=current_ua,
                    storage_state=storage_state,
                    extra_http_headers={"Referer": "https://www.google.com/"}
                )
                page = await context.new_page()
                await stealth_async(page)
                
                try:
                    logger.info(f"🚀 [ORIGINAL MODE] Fast Scan: {url}")
                    # Warm up home (Original logic)
                    await page.goto("https://shopee.co.th/", wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(1)
                    
                    # Navigate to product (Original logic)
                    await page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)
                    
                    success, title, images, attributes, fda, drug, ad = await self._extract_hierarchical(page, url)
                    if success:
                        return ScrapedData(
                            title=title or "Unknown Product", images=images, attributes=attributes,
                            scraped_fda_number=fda, scraped_drug_number=drug, 
                            scraped_ad_license=ad, success=True
                        )
                    return ScrapedData(success=False, error_type="EXTRACTION_FAILED")
                except Exception as e:
                    return ScrapedData(success=False, error_type=str(e))
                finally:
                    await page.close()
                    await context.close()
            else:
                # [โหมด Stealth สำหรับ Crawler]
                ShopeeScraper._request_count += 1
                if ShopeeScraper._request_count % 7 == 0:
                    await asyncio.sleep(random.uniform(25.0, 45.0))

                context = await self.get_context()
                page = await context.new_page()
                await stealth_async(page)
                try:
                    logger.info(f"👤 Stealth Scan (Crawler): {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    await asyncio.sleep(random.uniform(3.0, 5.0))
                    for _ in range(random.randint(2, 3)):
                        await page.mouse.wheel(0, random.randint(400, 800))
                        await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    # ตรวจสอบการบล็อก
                    content = await page.content()
                    if any(k in content.lower() for k in ["verify", "captcha", "robot"]):
                        await asyncio.sleep(60.0)
                        return ScrapedData(success=False, error_type="BLOCKED")
                    
                    success, title, images, attributes, fda, drug, ad = await self._extract_hierarchical(page, url)
                    if success:
                        return ScrapedData(
                            title=title or "Unknown Product", images=images, attributes=attributes,
                            scraped_fda_number=fda, scraped_drug_number=drug, 
                            scraped_ad_license=ad, success=True
                        )
                    return ScrapedData(success=False, error_type="INCOMPLETE")
                except Exception as e:
                    return ScrapedData(success=False, error_type=str(e))
                finally:
                    await page.close()
                

    async def scrape_product_data(self, url: str, fast_mode: bool = True) -> Dict:
        # ด่านตรวจสอบความถูกต้องล่วงหน้า (ความสำคัญ 5)
        if not self._is_valid_shopee_product_url(url) and not self._is_soft_valid(url):
            logger.error(f"❌ INVALID_PRODUCT_URL Blocked: {url}")
            return {"success": False, "error_type": "INVALID_PRODUCT_URL"}
            
        shopid, itemid = self._extract_ids(url)
        cache_key = f"{itemid}_{shopid}" if itemid and shopid else url
        
        cached = cache_manager.get_metadata(cache_key)
        if cached: return cached

        if not cache_manager.check_scraper_status():
            return {"success": False, "error_type": "CIRCUIT_BREAKER"}

        max_attempts = 2
        last_result = None
        for attempt in range(max_attempts):
            current_ua = USER_AGENTS[0] if attempt == 0 else random.choice(USER_AGENTS[1:])
            last_result = await self._fetch_with_playwright(url, ua=current_ua, fast_mode=fast_mode)
            if last_result.success:
                cache_manager.record_success()
                data = last_result.model_dump()
                cache_manager.set_metadata(cache_key, data)
                return data
            logger.warning(f"⚠️ [ATTEMPT {attempt+1}] Failed: {last_result.error_type}")
                
        return last_result.model_dump() if last_result else {"success": False, "error_type": "FAILED"}

    def _is_valid_shopee_product_url(self, url: str) -> bool:
        """Strict validation layer (Phase 1 High Priority)."""
        if not url or not isinstance(url, str): return False
        
        # 1. รายชื่อโดเมนที่อนุญาต (Whitelist)
        if "shopee.co.th" not in url: return False
        
        # 2. บัญชีดำ (Google sorry, การเปลี่ยนเส้นทางการค้นหา ฯลฯ)
        blacklist = ["google.com", "/sorry/", "/search", "facebook.com", "twitter.com"]
        if any(b in url.lower() for b in blacklist): return False
        
        # 3. การจับคู่รูปแบบสินค้า (-i. หรือ /product/)
        if "-i." in url or "/product/" in url:
            return True
            
        return False

    def _is_soft_valid(self, url: str) -> bool:
        """Relaxed but safe filter (Priority 1 Fix)."""
        if not url or not isinstance(url, str): return False
        return (
            "shopee.co.th" in url and
            "google.com" not in url and
            "/sorry/" not in url and
            len(url) > 40
        )

    async def search_shopee(self, keyword: str, limit: int = 10, page: int = 1) -> List[str]:
        """[FIX 12] Strict Keyword Discovery: ยึด Keyword เป็นหลัก ห้ามเอาของที่ไม่เกี่ยวข้องมาปน"""
        
        # [ใหม่] รองรับกรณีผู้ใช้ก๊อปปี้ลิงก์หน้าค้นหามาวาง (เช่น https://shopee.co.th/search?keyword=ยา)
        import urllib.parse
        if "shopee.co.th/search" in keyword and "keyword=" in keyword:
            parsed = urllib.parse.urlparse(keyword)
            qs = urllib.parse.parse_qs(parsed.query)
            if "keyword" in qs:
                keyword = qs["keyword"][0]
                logger.info(f"🔗 Extracted keyword from URL: '{keyword}'")

        logger.info(f"🚀 [DISCOVERY] Strict keyword scan for NEW items: '{keyword}' (Page: {page})")
        
        # 1. ยิง API ค้นหาด้วย Keyword แบบตรงๆ (Auth/Guest)
        new_found = await self._search_via_googlebot_category(keyword, limit * 2, page)
        
        # [ fallback ] หากค้นหาไม่เจอเลย ให้ใช้ระบบ SEED (ลายแทงสินค้าที่เตรียมไว้)
        if not new_found:
            logger.info(f"🔄 Search failed. Triggering SEED Fallback for '{keyword}'...")
            new_found = self._discovery_via_seeds(keyword)
        
        if not new_found:
            logger.warning(f"⚠️ ไม่พบสินค้าใหม่สำหรับคำว่า '{keyword}' (อาจโดนบล็อกหน้าค้นหา หรือสินค้าหมด)")
            return []

        # 2. กรองข้อมูลที่เคยสแกนไปแล้วออกจากผลลัพธ์ (เช็คจาก DB)
        unscanned = []
        try:
            with SessionLocal() as db:
                stmt = select(scan_record.ScanRecord.product_url)
                result = db.execute(stmt)
                db_scanned_urls = set([r[0] for r in result.all()])
                
                # เอาเฉพาะลิงก์ที่หามาได้สดๆ ร้อนๆ และยังไม่เคยอยู่ใน DB
                unscanned = [u for u in new_found if u not in db_scanned_urls]
        except Exception as e:
            logger.error(f"⚠️ DB Filter failed: {e}")
            unscanned = new_found # ถ้าระบบกรองพัง ให้ยอมสแกนทั้งหมดไปก่อน

        # 3. สุ่มเลือกให้ได้จำนวนตาม limit
        if unscanned:
            sample_size = min(len(unscanned), limit)
            batch = random.sample(unscanned, sample_size)
            logger.info(f"✅ ดึงสินค้าใหม่ที่ตรงกับ '{keyword}' ได้ {len(batch)} รายการ")
            return batch
        
        # [FIX] หาก Seed URLs ถูกสแกนไปหมดแล้ว ให้สแกนซ้ำ (re-scan) แทนที่จะหยุดเงียบ
        # เนื่องจาก API ถูกบล็อก Seed คือทางเดียวที่มี
        if new_found:
            sample_size = min(len(new_found), limit)
            batch = random.sample(new_found, sample_size)
            logger.warning(f"⚠️ สินค้าทั้ง {len(new_found)} รายการถูกสแกนแล้ว แต่จะ Re-scan เพื่อรีเฟรชข้อมูล")
            return batch
            
        logger.warning(f"⚠️ ไม่พบสินค้าใหม่หรือ Seed สำหรับคำว่า '{keyword}'")
        return []

    async def _search_via_googlebot_category(self, keyword: str, limit: int = 10, page: int = 1, use_cookies: bool = True) -> List[str]:
        """[FIX 9] API-based Discovery Layer: ยิงตรงไปที่ API แทน Browser พร้อมระบบ Pagination"""
        # ปิดระบบสุ่มเปลี่ยนคำ เพื่อให้ผลลัพธ์ตรงกับที่ผู้ใช้ค้นหา 100%
        actual_keyword = keyword

        # [FIX 9] Shopee Search API v4
        api_url = "https://shopee.co.th/api/v4/search/search_items"
        # หน้าค้นหาเริ่มที่ 0
        offset = page * limit
        params = {
            "by": "relevancy",
            "keyword": actual_keyword,
            "limit": limit,
            "newest": offset,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2
        }
        
        headers = {
            "User-Agent": USER_AGENTS[0], 
            "Referer": f"https://shopee.co.th/search?keyword={urllib.parse.quote(actual_keyword)}",
            "Origin": "https://shopee.co.th",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
            "x-shopee-language": "th",
            "x-api-source": "pc",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
        
        cookie_dict = {}
        if use_cookies:
            try:
                with open("app/config/shopee_cookies.json", "r", encoding="utf-8") as f:
                    raw_cookies = json.load(f)
                    cookie_list = raw_cookies if isinstance(raw_cookies, list) else raw_cookies.get("cookies", [])
                    for cookie in cookie_list:
                        cookie_dict[cookie["name"]] = cookie["value"]
                
                # [FIX] เพิ่ม CSRF Token ถ้ามี
                if "csrftoken" in cookie_dict:
                    headers["x-csrftoken"] = cookie_dict["csrftoken"]
            except Exception as e:
                logger.warning(f"⚠️ API Discovery: Could not load cookies ({e})")
        else:
            logger.info("📡 API Discovery: Using GUEST mode (No Cookies)")

        links = []
        try:
            logger.info(f"📡 API Discovery: Calling search API for '{actual_keyword}'")
            async with httpx.AsyncClient(timeout=15.0, cookies=cookie_dict) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    # ตรวจสอบโครงสร้างข้อมูล API ของ Shopee
                    items = data.get("items") or []
                    for item in items:
                        item_basic = item.get("item_basic")
                        if item_basic:
                            shopid = item_basic.get("shopid")
                            itemid = item_basic.get("itemid")
                            if shopid and itemid:
                                links.append(f"https://shopee.co.th/product-i.{shopid}.{itemid}")
                else:
                    logger.warning(f"⚠️ API Discovery failed (Status {resp.status_code}). Trying Browser-API fallback...")
        except Exception as e:
            logger.error(f"🔥 API Discovery Crash: {e}")

        # [Failsafe] หาก API ล้มเหลว ให้ใช้ Browser เข้าหน้าค้นหาจริงๆ
        if not links:
            try:
                context = await self.get_context(use_cookies=use_cookies)
                
                # [NEW] ลองใช้ Playwright Context Request (โอกาสผ่านสูงกว่า httpx เพราะเลียนแบบเบราว์เซอร์เป๊ะ)
                try:
                    logger.info("📡 API Discovery Fallback: Fetching API via Browser Context...")
                    api_resp = await context.request.get(api_url, params=params, headers=headers)
                    if api_resp.status == 200:
                        data = await api_resp.json()
                        items = data.get("items") or []
                        for item in items:
                            item_basic = item.get("item_basic")
                            if item_basic:
                                shopid = item_basic.get("shopid")
                                itemid = item_basic.get("itemid")
                                if shopid and itemid:
                                    links.append(f"https://shopee.co.th/product-i.{shopid}.{itemid}")
                        if links:
                            logger.info(f"✨ Browser-API Discovery Success: Found {len(links)} products.")
                            return links
                        else:
                            logger.warning("⚠️ Browser-API Success but 0 items found in JSON.")
                    else:
                        logger.warning(f"⚠️ Browser-API Fallback failed (Status {api_resp.status})")
                        if api_resp.status == 403:
                            logger.error("🚫 Browser-API is also blocked (403). Session/IP might be flagged.")
                except Exception as api_err:
                    logger.warning(f"⚠️ Browser-API Fallback failed: {api_err}")

                page_obj = await context.new_page()
                await stealth_async(page_obj)
                
                target_url = f"https://shopee.co.th/search?keyword={urllib.parse.quote(actual_keyword)}&page={page}"
                logger.info(f"📡 Failsafe Discovery: Visiting Search Page {target_url}")
                
                try:
                    await page_obj.goto(target_url, wait_until="networkidle", timeout=30000)
                except:
                    # หากเข้าหน้าค้นหาตรงๆ ไม่ได้ ให้ลองพิมพ์ค้นหาจากหน้า Home
                    success = await self._manual_search_fallback(page_obj, actual_keyword)
                    if not success:
                        await page_obj.close()
                        raise Exception("Failed to navigate to search page via direct URL or manual typing.")
                
                # รอให้เจอ Selector ของสินค้า (ลองหลายแบบ)
                try:
                    await page_obj.wait_for_selector(".shopee-search-item-result, [data-sqe='item']", timeout=10000)
                except:
                    logger.warning("⚠️ Failsafe Discovery: Timeout waiting for search results selector. Trying to close popups...")
                    try:
                        # ลองปิด Popup ที่อาจจะบังหน้าจอ
                        await page_obj.click(".shopee-popup__close-btn", timeout=2000)
                        await asyncio.sleep(1)
                        await page_obj.wait_for_selector(".shopee-search-item-result, [data-sqe='item']", timeout=5000)
                    except:
                        pass

                # สุ่มเลื่อนหน้าเพื่อให้ภาพและลิงก์โหลดขึ้นมา (Lazy load)
                for _ in range(3):
                    await page_obj.mouse.wheel(0, random.randint(800, 1200))
                    await asyncio.sleep(1.5)
                
                # ถ่ายภาพเก็บไว้ดูเล่นเผื่อพัง (Debug)
                try: await page_obj.screenshot(path="debug_failsafe.png")
                except: pass

                links_all = await page_obj.evaluate("""() => {
                    // ดึงทุกลิงก์ที่มีรูปแบบของสินค้า
                    const results = Array.from(document.querySelectorAll('a')).map(a => a.href);
                    // ถ้าหาไม่เจอจริงๆ ลองหาจาก data-sqe="item"
                    if (results.length === 0) {
                        return Array.from(document.querySelectorAll('[data-sqe="item"] a')).map(a => a.href);
                    }
                    return results;
                }""")
                
                logger.info(f"📡 Failsafe Debug: Found {len(links_all)} total <a> tags on page.")
                if links_all:
                    logger.info(f"📡 Failsafe Debug: Sample links: {links_all[:5]}")
                else:
                    html_content = await page_obj.content()
                    inner_text = await page_obj.inner_text("body")
                    with open("debug_failsafe.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info(f"📡 Failsafe Debug: Body text snippet: {inner_text[:500]}...")
                    logger.info("📡 Failsafe Debug: Saved raw HTML to debug_failsafe.html")

                links = [href for href in links_all if '-i.' in href and 'search' not in href]
                
                # [GUEST FALLBACK] หากยังไม่เจอลิงก์อีก และปัจจุบันใช้คุกกี้อยู่ ให้ลองแบบไม่ใช้คุกกี้ (Guest)
                if not links and use_cookies:
                    logger.info("🔄 Failsafe: Search returned 0. Retrying as GUEST (No Cookies)...")
                    await page_obj.close()
                    # [FIX] รีเซ็ต context เป็น guest — ใช้ ShopeeScraper แทน cls (ซึ่งไม่มีใน instance method)
                    if ShopeeScraper._context: await ShopeeScraper._context.close()
                    ShopeeScraper._context = None
                    return await self._search_via_googlebot_category(keyword, limit, page, use_cookies=False)

                await page_obj.close()
            except Exception as e:
                logger.error(f"🔥 Failsafe Discovery failed: {e}")

        # กรองเฉพาะ URL ที่ถูกต้องและกำจัดข้อมูลซ้ำซ้อน
        links = [l for l in list(dict.fromkeys(links)) if self._is_valid_shopee_product_url(l)]
        if links:
            logger.info(f"💎 Discovery Success: Found {len(links)} products via API/Failsafe")
            return links
        
        return []

    async def _extract_product_ids_from_text(self, text: str) -> List[str]:
        """Nuclear Regex: Extract any Shopee-like IDs from raw text."""
        decoded = urllib.parse.unquote(text)
        links = []
        
        # กวาดทุกอย่างที่คล้าย ID สินค้า
        patterns = [
            r'https?://shopee\.co\.th/[^\"\'\s]+-i\.(\d+)\.(\d+)',
            r'i\.(\d+)\.(\d+)',
            r'product/(\d+)/(\d+)',
            r'itemId\":(\d+),\"shopId\":(\d+)'
        ]
        
        for p in patterns:
            for match in re.findall(p, decoded):
                # Ensure we have (shop, item) or (item, shop) based on pattern
                if 'itemId' in p:
                    item_id, shop_id = match
                else:
                    shop_id, item_id = match
                links.append(f"https://shopee.co.th/product-i.{shop_id}.{item_id}")

        return list(dict.fromkeys(links))

    async def auto_scan_continuous(self, keyword: str, batch_size: int = 5, 
                                 max_products: int = 10, 
                                 delay_between_batches: float = 5.0) -> Dict:
        """
        🚀 High-level orchestration for continuous scanning as documented.
        - Discovers URLs
        - Processes in batches
        - Tracks stats
        """
        logger.info(f"🤖 AUTO-SCAN START: keyword='{keyword}', target={max_products}")
        
        stats: Dict[str, Any] = {
            "keyword": keyword,
            "total_scanned": 0,
            "successful": 0,
            "failed": 0,
            "pool_size": 0,
            "results": []
        }
        
        while stats["total_scanned"] < max_products:
            # 1. Discovery Phase
            remaining = max_products - stats["total_scanned"]
            current_batch_limit = min(batch_size, remaining)
            
            urls = await self.search_shopee(keyword, limit=current_batch_limit)
            if not urls:
                logger.warning("🏁 Discovery exhausted. No more products found.")
                break
                
            stats["pool_size"] = len(self._seed_urls) + len(self._collected_urls)
            logger.info(f"📦 Batch Start: Processing {len(urls)} products. (Pool: {stats['pool_size']})")
            
            # 2. Batch Processing Phase
            for i, url in enumerate(urls):
                try:
                    logger.info(f"🔍 [{stats['total_scanned'] + 1}/{max_products}] Scanning: {url}")
                    # Reuse the robust single product scraper (with Stealth for Auto-scan)
                    data = await self._fetch_with_playwright(url, fast_mode=False)
                    
                    stats["total_scanned"] += 1
                    if data.success:
                        stats["successful"] += 1
                        stats["results"].append({
                            "url": url,
                            "title": data.title,
                            "fda": data.scraped_fda_number,
                            "success": True
                        })
                        logger.info(f"✅ Success: {data.title[:40]}...")
                    else:
                        stats["failed"] += 1
                        logger.warning(f"❌ Failed: {url} (Type: {data.error_type})")
                        
                except Exception as e:
                    stats["total_scanned"] += 1
                    stats["failed"] += 1
                    logger.error(f"🔥 Crash during batch item: {e}")
                
                # Small delay between items to be polite
                await asyncio.sleep(random.uniform(1.0, 2.0))

            # 3. Batch Cooldown
            if stats["total_scanned"] < max_products:
                logger.info(f"⏸️ Batch complete. Waiting {delay_between_batches}s before next batch...")
                await asyncio.sleep(delay_between_batches)

        # Final Summary
        stats["success_rate"] = f"{(stats['successful'] / stats['total_scanned'] * 100):.1f}%" if stats["total_scanned"] > 0 else "0%"
        logger.info(f"🏁 AUTO-SCAN COMPLETE: {stats['successful']}/{stats['total_scanned']} successful ({stats['success_rate']})")
        
        return stats

    def _discovery_via_seeds(self, keyword: str) -> List[str]:
        """[SEED PROTOCOL] ดึงลิงก์จากคลังลายแทงที่เตรียมไว้ (ใช้เมื่อ Search ปกติล่ม)"""
        seeds_path = "app/config/seeds.json"
        if not os.path.exists(seeds_path):
            return []
        
        try:
            with open(seeds_path, "r", encoding="utf-8") as f:
                seeds_data = json.load(f)
                # ค้นหาด้วย Keyword ตรงๆ หรือคำที่ใกล้เคียง
                found_seeds = seeds_data.get(keyword) or []
                if not found_seeds:
                    # ถ้าไม่เจอ Keyword ตรงๆ ให้ลองวนลูปหาคำที่อยู่ในคีย์
                    for k, v in seeds_data.items():
                        if k in keyword or keyword in k:
                            found_seeds.extend(v)
                
                if found_seeds:
                    logger.info(f"✨ Seed Discovery: Found {len(found_seeds)} URLs for '{keyword}'")
                    return found_seeds
        except Exception as e:
            logger.error(f"⚠️ Seed Discovery error: {e}")
        return []

    async def _manual_search_fallback(self, page_obj: Page, keyword: str):
        """[HUMAN FALLBACK] เข้าหน้า Home แล้วพิมพ์ค้นหาเอง (ข้าม WAF ได้ดีที่สุด)"""
        try:
            logger.info(f"🕵️ Manual Search: Navigating to Home and typing '{keyword}'...")
            await page_obj.goto("https://shopee.co.th/", wait_until="networkidle", timeout=30000)
            
            # ปิด Popup ถ้ามี
            try: await page_obj.click(".shopee-popup__close-btn", timeout=3000)
            except: pass
            
            # หาช่องค้นหาและพิมพ์
            search_input = await page_obj.wait_for_selector("input.shopee-searchbar-input__input", timeout=5000)
            if search_input:
                await search_input.fill(keyword)
                await asyncio.sleep(0.5)
                await search_input.press("Enter")
                await page_obj.wait_for_load_state("networkidle")
                await asyncio.sleep(2) # รอผลลัพธ์ขึ้น
                return True
        except Exception as e:
            logger.warning(f"⚠️ Manual Search failed: {e}")
        return False
