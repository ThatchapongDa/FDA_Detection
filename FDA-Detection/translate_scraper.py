import os

translations = {
    "Standard User Agents for Rotation": "ชุด User Agents มาตรฐานสำหรับการสลับใช้งาน",
    "Supporting Drug Reg": "รองรับข้อมูลทะเบียนยา",
    "Supporting Fact": "ข้อเท็จจริงสนับสนุน",
    "TIMEOUT, BLOCKED, OTHER, CIRCUIT_BREAKER": "หมดเวลา, ถูกบล็อก, อื่นๆ, วงจรตัด (Circuit Breaker)",
    "Concurrency Control": "การควบคุมการทำงานพร้อมกัน",
    "Initialize to avoid UnboundLocalError": "กำหนดค่าเริ่มต้นเพื่อหลีกเลี่ยง UnboundLocalError",
    "JSON Excavation (window.__INITIAL_STATE__ or mfe-initial-data)": "การขุดข้อมูล JSON (window.__INITIAL_STATE__ หรือ mfe-initial-data)",
    "Find product core data (Expanded paths for resilience)": "ค้นหาข้อมูลหลักของสินค้า (ขยายพาธเพื่อความยืดหยุ่นทนทาน)",
    "Fallback path": "เส้นทางสำรอง",
    "Store Attributes (FDA/Drug Reg in Metadata)": "เก็บคุณลักษณะ (อย./ทะเบียนยาใน Metadata)",
    "COLLECT GALLERY (Strictly from JSON to maintain completeness)": "รวบรวมรูปภาพ (จาก JSON อย่างเคร่งครัดเพื่อรักษาความครบถ้วน)",
    "[NEW] DOM Attribute & Category Scraper Fallback": "[ใหม่] การดึงคุณลักษณะและหมวดหมู่จาก DOM (ระบบสำรอง)",
    "First check formal attributes": "ตรวจสอบคุณลักษณะที่เป็นทางการก่อน",
    "Global Fallback Scan (if still missing)": "การสแกนครอบคลุมแบบสำรอง (หากยังหาไม่พบ)",
    "[STAGE 2] DOM Extraction (Strict Gallery Fallback)": "[ขั้นตอนที่ 2] การสกัดจาก DOM (การสำรองรูปภาพอย่างเคร่งครัด)",
    "Trigger Lazy Loading (Optional click)": "กระตุ้นการโหลดแบบ Lazy Loading (การคลิกที่เป็นทางเลือก)",
    "1. Targeted DOM Extraction (High Priority)": "1. การสกัดจาก DOM แบบเจาะจง (ความสำคัญสูง)",
    "New Thumbnail Class": "คลาสของรูปย่อแบบใหม่",
    "New Gallery Container": "คอนเทนเนอร์รูปภาพแบบใหม่",
    "Legacy Gallery Thumbnails": "คลาสรูปย่อแบบดั้งเดิม",
    "Featured Image": "ภาพเด่น",
    "Regex Deep Scan (DEPRECATED - Only if zero images found)": "การสแกนแบบลึกด้วย Regex (เลิกใช้แล้ว - ใช้เฉพาะเมื่อไม่พบรูปภาพเลย)",
    "Conservative fallback": "ระบบสำรองแบบอนุรักษ์นิยม",
    "[STAGE 3] Meta & Atomic Scan (ALWAYS RUN: Essential for FDA accuracy)": "[ขั้นตอนที่ 3] การสแกน Meta & ระดับย่อย (ต้องทำงานเสมอ: จำเป็นสำหรับความแม่นยำของ อย.)",
    "Recover title from Meta if still missing": "กู้คืนชื่อจาก Meta หากยังคงขาดหายไป",
    "Atomic Regex Coverage (OCR-style from raw content)": "การครอบคลุมของ Regex ระดับย่อย (สไตล์ OCR จากเนื้อหาดิบ)",
    "1. Food/Supplement Pattern (13 digits)": "1. รูปแบบอาหาร/อาหารเสริม (13 หลัก)",
    "2. Drug Registration Pattern (e.g. 1A 123/45)": "2. รูปแบบทะเบียนยา (เช่น 1A 123/45)",
    "Final Deduplication & Cleanup (No more hardcoded 10 limit)": "การกำจัดข้อมูลซ้ำซ้อนและทำความสะอาดขั้นตอนสุดท้าย (ไม่มีการจำกัดฮาร์ดโค้ด 10 อันอีกต่อไป)",
    "images_set = list(dict.fromkeys(images_set))": "images_set = list(dict.fromkeys(images_set))",
    "[MAIN NAV] Navigate to Product": "[การนำทางหลัก] ไปที่หน้าสินค้า",
    "Human-like delay for React hydration": "การหน่วงเวลาแบบมนุษย์สำหรับการเรนเดอร์ React",
    "[HIERARCHICAL EXTRACTION] - Fixed 7-value unpacking success, title, images, attributes, fda, drug, ad = await self._extract_hierarchical(page, url)": "[การสกัดแบบลำดับขั้น] - สำเร็จในการแยก 7 ค่า",
    "Check for hydration delay (skeleton state)": "ตรวจสอบความล่าช้าของการเรนเดอร์ (สถานะกำลังโหลด)",
    "Pre-validation Guard (Priority 5)": "ด่านตรวจสอบความถูกต้องล่วงหน้า (ความสำคัญ 5)",
    "2. Blacklist (Google sorry, search redirects, etc.)": "2. บัญชีดำ (Google sorry, การเปลี่ยนเส้นทางการค้นหา ฯลฯ)",
    "3. Product Pattern Match (-i. or /product/)": "3. การจับคู่รูปแบบสินค้า (-i. หรือ /product/)",
    "KNOWN ENTRY POINTS SYSTEM": "ระบบจุดเข้าสู่เว็บไซต์ที่ทราบ",
    "Pre-seeded URLs + organic collection from Single Scans.": "URL ที่เตรียมไว้ล่วงหน้า + การรวบรวมอัตโนมัติจากการสแกนเดี่ยว",
    "URLs from successful Single Scans": "URL จากการสแกนเดี่ยวที่สำเร็จ",
    "Track already-scanned URLs": "ติดตาม URL ที่สแกนแล้ว",
    "Combine all sources, deduplicate": "รวมแหล่งที่มาทั้งหมด, กำจัดข้อมูลซ้ำซ้อน",
    "Separate unscanned vs already-scanned": "แยก URL ที่ยังไม่ได้สแกนกับที่สแกนแล้ว",
    "All URLs scanned re-check oldest ones (continuous monitoring)": "URL ทั้งหมดถูกสแกนแล้ว เริ่มตรวจสอบอันที่เก่าที่สุดใหม่ (การติดตามต่อเนื่อง)",
    "Reset scan tracking and serve first batch": "รีเซ็ตการติดตามการสแกนและส่งกลุ่มแรก",
    "Fallback: try Googlebot category crawl": "ตัวเลือกสำรอง: ลองใช้ Googlebot ขุดหมวดหมู่",
    "URL-decode the text first (Google encodes URLs as %2F, %3A etc.)": "ถอดรหัส URL ข้อความก่อน (Google เข้ารหัส URL เป็น %2F, %3A ฯลฯ)"
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    for eng, thai in translations.items():
        new_content = new_content.replace(eng, thai)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Translated comments in: {filepath}")

if __name__ == '__main__':
    process_file('backend/app/services/scraper.py')
