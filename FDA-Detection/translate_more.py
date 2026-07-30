import os

translations = {
    "Strict Constraint: SHOP_ONLY DRUG Penalty Cap": "ข้อจำกัดเข้มงวด: ขีดจำกัดบทลงโทษกรณีเป็นยาและพบข้อมูลเฉพาะในร้านค้า",
    "Domain Whitelist": "รายชื่อโดเมนที่อนุญาต (Whitelist)",
    "Scrape Data with Resilient Scraper": "ดึงข้อมูลด้วย Scraper ที่มีความยืดหยุ่นทนทาน",
    "Extract Data from Scraper Result": "สกัดข้อมูลจากผลลัพธ์ของ Scraper",
    "Heuristics & Product Classification": "การวิเคราะห์หาคำตอบและการจำแนกประเภทสินค้า",
    "Deep Verification Section": "ส่วนของการตรวจสอบเชิงลึก",
    "Fallback to any remaining categories detected by keyword": "ใช้หมวดหมู่ที่เหลือที่ตรวจพบจากคีย์เวิร์ดเป็นตัวเลือกสำรอง",
    "Final Database Sync": "การซิงค์ฐานข้อมูลขั้นตอนสุดท้าย",
    "Mandatory Keywords - 15 Points": "คีย์เวิร์ดบังคับ - 15 คะแนน",
    "Thai Language Presence - 10 Points": "การปรากฏของภาษาไทย - 10 คะแนน",
    "Medical Score Boost": "การเพิ่มคะแนนในหมวดหมู่ทางการแพทย์",
    "Add DOM images first as they are high confidence": "เพิ่มภาพจาก DOM ก่อนเนื่องจากมีความน่าเชื่อถือสูง",
    "Add Thai promotional keywords to blacklist check": "เพิ่มคีย์เวิร์ดโปรโมชันภาษาไทยลงในการตรวจสอบบัญชีดำ",
    "Anti-Prompt Echo: If output contains prompt keywords, it's a hallucination": "ป้องกัน Prompt Echo: หากผลลัพธ์มีคีย์เวิร์ดจาก prompt ถือว่า AI หลอนข้อมูล (Hallucination)",
    "Auto-collect successful URL into seed database": "รวบรวม URL ที่สำเร็จเข้าสู่ฐานข้อมูลตั้งต้นโดยอัตโนมัติ",
    "Combine all possible text sources for maximum detection probability": "รวมแหล่งข้อความทั้งหมดที่เป็นไปได้เพื่อเพิ่มโอกาสในการตรวจจับสูงสุด",
    "DINO prediction must overlap with at least one package box": "การทำนายของ DINO ต้องทับซ้อนกับกล่องบรรจุภัณฑ์อย่างน้อยหนึ่งกล่อง",
    "Ensure normalized for regex": "ตรวจสอบให้แน่ใจว่าทำให้อยู่ในรูปแบบมาตรฐานสำหรับ regex แล้ว",
    "Factual observation — NOT risk judgment": "การสังเกตจากข้อเท็จจริง — ไม่ใช่การตัดสินความเสี่ยง",
    "Global Scan: Also scan the entire page text as a fallback": "การสแกนแบบครอบคลุม: สแกนข้อความทั้งหน้าเป็นตัวเลือกสำรองด้วย",
    "Hybrid Visual Guard: Visibility + Sticker Check": "การป้องกันด้วยภาพแบบผสม: ตรวจสอบการมองเห็น + สติกเกอร์",
    "If shop_category is GENERAL but we found a license on the product,": "ถ้าหมวดหมู่ร้านค้าคือ GENERAL แต่เราพบใบอนุญาตบนตัวสินค้า,",
    "In upload mode, we don't have a shop claim. We will assume the shop correctly claims whatever the OCR finds": "ในโหมดอัปโหลด เราไม่มีการกล่าวอ้างจากร้านค้า เราจะถือว่าร้านค้าระบุข้อมูลตรงกับที่ OCR พบ",
    "Keep Roboflow as safety fallback": "เก็บ Roboflow ไว้เป็นตัวเลือกสำรองเพื่อความปลอดภัย",
    "Keep existing detector state if runtime config fails.": "รักษาสถานะตัวตรวจจับเดิมไว้หากการตั้งค่าตอนรันไทม์ล้มเหลว",
    "Keep only predictions that don't overlap significantly with the best_pred": "เก็บเฉพาะการทำนายที่ไม่ทับซ้อนกับการทำนายที่ดีที่สุด (best_pred) มากเกินไป",
    "Pattern 1: Direct ID pattern i.SHOPID.ITEMID": "รูปแบบที่ 1: รูปแบบ ID ตรง i.SHOPID.ITEMID",
    "Pattern 2: Full Shopee URLs from search results": "รูปแบบที่ 2: URL ของ Shopee แบบเต็มจากผลการค้นหา",
    "Pre-load both engines as singletons to prevent re-init overhead": "โหลด engine ทั้งสองไว้ล่วงหน้าแบบ Singleton เพื่อป้องกันความล่าช้าในการโหลดซ้ำ",
    "Prioritize unscanned URLs": "ให้ความสำคัญกับ URL ที่ยังไม่ได้สแกนเป็นอันดับแรก",
    "Rescale DINO coordinates back to full-image space": "ปรับขนาดพิกัด DINO กลับไปยังพื้นที่ภาพเต็ม",
    "Run DINO on the cropped product region": "รัน DINO บนบริเวณภาพสินค้าที่ตัดมา",
    "Setup session with retries for Full Throttle robustness": "ตั้งค่าเซสชันพร้อมการลองใหม่เพื่อความเสถียรแบบ Full Throttle",
    "Skip only if the category is determined to be GENERAL or UNKNOWN.": "ข้ามเฉพาะในกรณีที่หมวดหมู่ถูกระบุเป็น GENERAL หรือ UNKNOWN",
    "Smart Selection: Check quality before picking": "การเลือกอัจฉริยะ: ตรวจสอบคุณภาพก่อนเลือก",
    "Sort by confidence descending": "เรียงลำดับตามความมั่นใจจากมากไปน้อย",
    "Standardize to a user-friendly label instead of technical model names": "ปรับให้เป็นป้ายกำกับที่ผู้ใช้เข้าใจง่ายแทนชื่อทางเทคนิคของโมเดล",
    "Structured Taxonomy for AI Classification": "อนุกรมวิธานที่มีโครงสร้างสำหรับการจำแนกประเภทด้วย AI",
    "Try SAM refinement first": "ลองใช้ SAM ปรับแต่งรายละเอียดก่อน",
    "[CRITICAL FIX] cv2.imdecode often fails on WebP/AVIF from Shopee. Fallback to Pillow.": "[การแก้ไขสำคัญ] cv2.imdecode มักจะล้มเหลวกับ WebP/AVIF จาก Shopee ให้เปลี่ยนไปใช้ Pillow แทน",
    "[DYNAMIC] MEDICINE FILTER: Use the intelligent classification engine": "[แบบไดนามิก] ตัวกรองยา: ใช้กลไกการจำแนกประเภทอัจฉริยะ",
    "[Full Throttle] High-confidence default for Typhoon": "[แบบเต็มสปีด] ค่าเริ่มต้นความมั่นใจสูงสำหรับ Typhoon",
    "[MULTI-STAGE] Navigate to Home if no session": "[หลายขั้นตอน] นำทางไปที่หน้าแรกหากไม่มีเซสชัน",
    "[NEW] Pre-classify to avoid UNKNOWN in UI": "[ใหม่] จำแนกประเภทล่วงหน้าเพื่อหลีกเลี่ยงสถานะ UNKNOWN ใน UI",
    "[NEW] Skip if already scanned recently": "[ใหม่] ข้ามหากเพิ่งสแกนไปเมื่อเร็วๆ นี้",
    "[POST-EXTRACTION SCAN] Centralized license identification": "[การสแกนหลังสกัดข้อมูล] การระบุใบอนุญาตแบบรวมศูนย์",
    "[REFINED] Use the score-based classifier for the early filter decision.": "[ปรับปรุง] ใช้ตัวจำแนกตามคะแนนสำหรับการตัดสินใจกรองเบื้องต้น",
    "[REVERTED] Force CPU for stability and simplicity": "[ย้อนกลับ] บังคับใช้ CPU เพื่อความเสถียรและความเรียบง่าย",
    "[REVERTED] Standard FP32 on CPU": "[ย้อนกลับ] ใช้ FP32 มาตรฐานบน CPU",
    "[SAM Hard Limit] Max 2 crops refined per request to save VRAM": "[ข้อจำกัด SAM] จำกัดการปรับแต่งสูงสุด 2 ครอปต่อคำขอเพื่อประหยัด VRAM",
    "to test the 'PRODUCT_ONLY' or 'MATCH' logic, simulating a self-consistent product.": "เพื่อทดสอบตรรกะ 'PRODUCT_ONLY' หรือ 'MATCH' โดยจำลองว่าสินค้ามีความสอดคล้องกัน",
    "v4.0 Filter: Exclude common Shopee tracking or UI garbage": "ตัวกรอง v4.0: ละเว้น tracking ทั่วไปของ Shopee หรือขยะใน UI",
    "we MUST NOT skip as it's likely a miscategorized regulated product.": "เราต้องไม่ข้าม เนื่องจากอาจเป็นสินค้าควบคุมที่ถูกจัดหมวดหมู่ผิด",
    "SPIDER MODE: Extract related product URLs for continuous crawling": "โหมดสไปเดอร์: ดึง URL สินค้าที่เกี่ยวข้องเพื่อการรวบรวมอย่างต่อเนื่อง",
    "usually if it has Food FDA format + no supplement keywords, it's just Food": "มักจะถ้ามีรูปแบบ อย. อาหาร + ไม่มีคีย์เวิร์ดอาหารเสริม ก็คืออาหาร",
    "We will do grouping here in python for simplicity": "เราจะทำการจัดกลุ่มที่นี่ในไพทอนเพื่อความเรียบง่าย",
    "Title & Meta": "ชื่อเรื่องและข้อมูลอภิมาน (Meta)",
    "Calculate Risk": "คำนวณความเสี่ยง"
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
