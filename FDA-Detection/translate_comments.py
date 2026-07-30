import os

translations = {
    "Format a description string from attributes for classification and storage": "จัดรูปแบบสตริงคำอธิบายจากคุณลักษณะเพื่อใช้ในการจำแนกและจัดเก็บ",
    "Medical labels on white backgrounds have high detail. Banners are mostly flat white.": "ฉลากยาบนพื้นหลังสีขาวมีรายละเอียดสูง ส่วนป้ายแบนเนอร์มักจะเป็นสีขาวเรียบๆ",
    "Normalized score": "คะแนนที่ถูกปรับให้เป็นมาตรฐาน",
    "Smart Category Inference: Fallback if Shopee fails to provide category": "การอนุมานหมวดหมู่อัจฉริยะ: ใช้ทำงานแทนหาก Shopee ไม่ระบุหมวดหมู่มาให้",
    "Check for overwhelming white or black areas": "ตรวจสอบพื้นที่สีขาวหรือดำที่มากเกินไป",
    "Global offset was causing skips across unrelated keywords.": "Global offset ทำให้เกิดการข้ามคีย์เวิร์ดที่ไม่เกี่ยวข้อง",
    "Detail View Sync: Universal Reg Box": "อัปเดตหน้าต่างรายละเอียด: กล่องข้อมูลทะเบียน",
    "Ensure it's marked as stopped even on weird exits": "ตรวจสอบให้แน่ใจว่าได้เปลี่ยนสถานะเป็นหยุดทำงานแม้จะออกด้วยวิธีแปลกๆ",
    "Clean and Store OCR Text": "ทำความสะอาดและบันทึกข้อความ OCR",
    "OCR: Targeted pass": "OCR: ตรวจสอบเฉพาะจุดเป้าหมาย",
    "Logic for OCR: DINO detections, crops refined with SAM in detector": "ตรรกะสำหรับ OCR: ตรวจจับด้วย DINO, ตัดรูปภาพให้แม่นยำขึ้นด้วย SAM ใน detector",
    "Visual Evidence crops": "รูปภาพหลักฐานเชิงประจักษ์",
    "OCR & Evidence extraction follows...": "เริ่มต้นการดึงข้อความ OCR และหลักฐาน...",
    "Scraper already handles cache, retry, and circuit breaker internally": "Scraper จัดการเรื่องแคช การลองใหม่ และ circuit breaker ไว้ภายในแล้ว",
    "Support drug reg": "รองรับข้อมูลทะเบียนยา",
    "Use parallel dual OCR if Typhoon available, else standard": "ใช้ OCR แบบคู่ขนานถ้า Typhoon พร้อมใช้งาน มิฉะนั้นใช้แบบมาตรฐาน",
    "Tight Aspect Ratio Filter: Discard Banners (Most products are square 1:1)": "ตัวกรองสัดส่วนภาพที่เข้มงวด: ทิ้งป้ายแบนเนอร์ (สินค้าส่วนใหญ่เป็นสี่เหลี่ยมจัตุรัส 1:1)",
    "Has Alpha channel": "มีช่อง Alpha (โปร่งใส)",
    "Map error type to user-friendly message": "แปลงประเภทข้อผิดพลาดเป็นข้อความที่เข้าใจง่าย",
    "Product thumbnail": "ภาพตัวอย่างสินค้า",
    "Fallback download if needed": "ดาวน์โหลดสำรองหากจำเป็น",
    "We reuse the existing generator seamlessly, consuming it completely silently": "นำ generator เดิมมาใช้ใหม่ได้อย่างแนบเนียน โดยทำงานแบบซ่อนเร้นสมบูรณ์แบบ",
    "Check if ANY shop license matches ANY OCR license": "ตรวจสอบว่าใบอนุญาตจากร้านค้าตรงกับใบอนุญาตจาก OCR หรือไม่",
    "Standard products are 0.8 to 1.25. Banners are often > 1.5 or < 0.6": "สินค้าทั่วไปมีสัดส่วน 0.8 ถึง 1.25 ส่วนป้ายแบนเนอร์มักจะ > 1.5 หรือ < 0.6",
    "Initial Load": "โหลดข้อมูลเริ่มต้น",
    "Show skip message briefly": "แสดงข้อความข้ามชั่วคราว",
    "Check Supplement first to avoid Drug label on supplements mentioning ยา": "ตรวจสอบอาหารเสริมก่อนเพื่อป้องกันฉลากยาในอาหารเสริมที่มีคำว่า 'ยา'",
    "Re-compute indicators for detail view": "คำนวณตัวชี้วัดใหม่สำหรับมุมมองรายละเอียด",
    "Aggregate all shop-provided licenses": "รวบรวมใบอนุญาตทั้งหมดที่ร้านค้าระบุไว้",
    "AD is for medicine ads usually": "AD มักใช้สำหรับโฆษณายา",
    "Phase 1 Optimization: Always Include Full Image for Global OCR Coverage": "การเพิ่มประสิทธิภาพระยะที่ 1: รวมภาพเต็มเสมอเพื่อให้ OCR ครอบคลุมทั้งหมด",
    "Use SAM for FDA labels": "ใช้ SAM สำหรับฉลาก อย.",
    "Audit as if it were a regulated product": "ตรวจสอบเสมือนว่าเป็นสินค้าควบคุม",
    "Regex check for specific types": "ตรวจสอบ Regex สำหรับประเภทเฉพาะ",
    "Detect": "ตรวจจับ",
    "ghost check": "ตรวจสอบข้อมูลลวง",
    "Initialize evidence and summary variables": "ตั้งค่าเริ่มต้นสำหรับตัวแปรหลักฐานและบทสรุป",
    "Required to explicitly register AVIF plugin": "จำเป็นต้องลงทะเบียนปลั๊กอิน AVIF อย่างชัดเจน",
    "Save temp file for detector": "บันทึกไฟล์ชั่วคราวสำหรับ detector",
    "Show ALL found text in UI for transparency, ": "แสดงข้อความที่พบทั้งหมดใน UI เพื่อความโปร่งใส, ",
    "Intelligent Category Fallback: Use AI classification if Scraper fails": "การใช้หมวดหมู่สำรองอัจฉริยะ: ใช้ AI จำแนกประเภทหาก Scraper ล้มเหลว",
    "Run with concurrency limit": "ทำงานโดยจำกัดจำนวนการรันพร้อมกัน",
    "Enforce Cap one last time just in case other categories demand it later": "บังคับใช้จำนวนจำกัดสูงสุดอีกครั้งเผื่อหมวดหมู่อื่นต้องการในภายหลัง",
    "Save uploaded file": "บันทึกไฟล์ที่อัปโหลด",
    "Centralized Regex Patterns: Define once, use for both Metadata and OCR": "ศูนย์รวมรูปแบบ Regex: กำหนดครั้งเดียว ใช้สำหรับทั้งข้อมูล Metadata และ OCR",
    "AI Section: Found ON IMAGES (OCR)": "ส่วนของ AI: สิ่งที่พบบนรูปภาพ (ผ่าน OCR)",
    "Post-Processing: Consolidated Holistic Analysis": "การประมวลผลหลังการดึงข้อมูล: การวิเคราะห์แบบองค์รวม",
    "Small delay to ensure stability": "หน่วงเวลาเล็กน้อยเพื่อให้ระบบเสถียร",
    "Fast box crop for non-FDA labels (skip SAM)": "ตัดภาพแบบรวดเร็วสำหรับฉลากที่ไม่ใช่ อย. (ข้าม SAM)",
    "Both flat color AND few edges": "มีทั้งสีเรียบและขอบที่น้อย",
    "This indicates the scraper failed to get the real title, so we must analyze the images.": "นี่แสดงว่า scraper ไม่สามารถดึงชื่อสินค้าจริงได้ เราจึงต้องวิเคราะห์จากภาพ",
    "Fix: Explicitly cast re.search to bool to avoid JSON serializable error": "แก้ไข: แปลง re.search เป็น bool ชัดเจนเพื่อหลีกเลี่ยงข้อผิดพลาด JSON serializable",
    "Update item_name if we can parse it from progress (optional)": "อัปเดตชื่อรายการถ้าสามารถดึงข้อมูลจากความคืบหน้าได้ (ไม่บังคับ)",
    "Holistic Sequential Processing: No ranking, just thorough analysis of all images": "การประมวลผลแบบองค์รวมตามลำดับ: ไม่มีการจัดอันดับ แค่วิเคราะห์ภาพทั้งหมดอย่างละเอียด",
    "Final result of the item": "ผลลัพธ์สุดท้ายของรายการ",
    "This ensures we find text even if DINO/SAM fails to detect a specific label box.": "สิ่งนี้ทำให้มั่นใจว่าเราจะพบข้อความแม้ว่า DINO/SAM จะไม่สามารถตรวจจับกล่องฉลากที่ระบุได้",
    "Use global settings if hours is default": "ใช้การตั้งค่าส่วนกลางหากชั่วโมงเป็นค่าเริ่มต้น",
    "Return last N lines": "คืนค่าบรรทัด N สุดท้าย",
    "Usually if it has Food FDA format + no supplement keywords, it's just Food": "มักจะถ้ามีรูปแบบ อย. อาหาร + ไม่มีคีย์เวิร์ดอาหารเสริม ก็คืออาหาร",
    "Return as list of blocks sorted descending": "คืนค่าเป็นรายการของบล็อกที่จัดเรียงจากมากไปน้อย",
    "Content-Aware Transparency (New v3.2): ": "การรับรู้ความโปร่งใสตามเนื้อหา: ",
    "We will do grouping here in python for simplicity": "เราจะทำการจัดกลุ่มที่นี่ในไพทอนเพื่อความเรียบง่าย",
    "Phase 1 Optimization: Parallel OCR": "การปรับแต่งเฟส 1: OCR แบบขนาน",
    "Save first image for card": "บันทึกภาพแรกสำหรับการ์ด",
    "Column already exists": "คอลัมน์มีอยู่แล้ว",
    "Holistic Approach: Take ALL images from scraper (up to 20 for safety)": "แนวทางแบบองค์รวม: นำภาพทั้งหมดจาก scraper (สูงสุด 20 รูปเพื่อความปลอดภัย)",
    "Download candidates for ranking and processing": "ดาวน์โหลดตัวเลือกสำหรับการจัดอันดับและการประมวลผล",
    "Re-compute detailed stats for the feed": "คำนวณสถิติโดยละเอียดใหม่สำหรับฟีด",
    "Reject > 70% transparency if it lacks Medical Characteristics (low detail).": "ปฏิเสธความโปร่งใส > 70% หากขาดลักษณะทางการแพทย์ (รายละเอียดต่ำ)",
    "Use pre-downloaded image bytes": "ใช้ไบต์รูปภาพที่ดาวน์โหลดมาแล้ว",
    "Fallback Payload for UI": "ข้อมูลสำรองสำหรับหน้า UI",
    "Pre-calculate Metadata Claims (Scraper)": "คำนวณการอ้างอิงข้อมูลล่วงหน้า (Scraper)",
    "Spin up a new db session for each item to avoid thread issues": "สร้างเซสชันฐานข้อมูลใหม่สำหรับแต่ละรายการเพื่อหลีกเลี่ยงปัญหาเรื่องเธรด",
    "CRAWLER ENGINE (Auto-Scan Background Task)": "กลไกคราว์เลอร์ (งานสแกนอัตโนมัติเบื้องหลัง)",
    "Build Verified Credentials Object (Upload)": "สร้างออบเจ็กต์ใบรับรองที่ตรวจสอบแล้ว (อัปโหลด)",
    "Stream image results back to UI in real-time": "ส่งผลลัพธ์ภาพกลับไปที่ UI แบบเรียลไทม์",
    "Reset Pagination: Always start from page 0 for new searches ": "รีเซ็ตการแบ่งหน้า: เริ่มจากหน้า 0 เสมอสำหรับการค้นหาใหม่ ",
    "Clear name on finish": "ลบชื่อเมื่อทำงานเสร็จ",
    "Build Verified Credentials Object for Modern UI": "สร้างออบเจ็กต์ใบรับรองที่ตรวจสอบแล้วสำหรับ UI สมัยใหม่",
    "Detection Pass (DINO)": "ขั้นตอนการตรวจจับ (DINO)",
    "hour string: \"YYYY-MM-DD HH:00\"": "สตริงชั่วโมง: \"YYYY-MM-DD HH:00\"",
    "Auto-migrate: Add product_image column if not exists": "อพยพข้อมูลอัตโนมัติ: เพิ่มคอลัมน์ product_image หากยังไม่มี",
    "Fallback to fast box crop": "ใช้การตัดภาพแบบเร็วเป็นตัวเลือกสำรอง",
    "Extreme flat color (likely logo/icon)": "สีเรียบจัด (น่าจะเป็นโลโก้/ไอคอน)",
    "Initialize default vars in case OCR fails completely on all images": "ตั้งค่าเริ่มต้นของตัวแปรเผื่อกรณีที่ OCR ล้มเหลวทั้งหมดทุกภาพ",
    "This is more robust than a simple exclusion list.": "วิธีนี้แข็งแกร่งกว่าการใช้รายการละเว้นแบบธรรมดา",
    "but we still track 'valid' for the holistic logic later.": "แต่เรายังคงติดตาม 'ความถูกต้อง' เพื่อใช้กับตรรกะแบบองค์รวมในภายหลัง",
    "Update DB Record": "อัปเดตข้อมูลในฐานข้อมูล",
    "Save Scraped Metadata": "บันทึกข้อมูลที่ขูดมาได้",
    "Encode crops as base64 for UI": "เข้ารหัสรูปภาพที่ถูกตัดเป็น base64 สำหรับ UI",
    " Usually if it has Food FDA format + no supplement keywords, it's just Food": " มักจะถ้ามีรูปแบบ อย. อาหาร + ไม่มีคีย์เวิร์ดอาหารเสริม ก็คืออาหาร",
    " We will do grouping here in python for simplicity": " เราจะทำการจัดกลุ่มที่นี่ในไพทอนเพื่อความเรียบง่าย"
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

def main():
    root_dirs = ['backend/app', 'frontend/src']
    for root_dir in root_dirs:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py') or file.endswith('.js'):
                    process_file(os.path.join(root, file))

if __name__ == '__main__':
    main()
