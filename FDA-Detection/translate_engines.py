import os

translations = {
    "Use detail=1 to get bounding box, text, and confidence": "ใช้ detail=1 เพื่อดึงข้อมูลกรอบข้อความ, ข้อความ, และความมั่นใจ",
    "Setup session with retries for \"Full Throttle\" robustness": "ตั้งค่าเซสชันพร้อมการลองใหม่เพื่อความเสถียรระดับ Full Throttle",
    "Always load EasyOCR as it's the primary or the fallback": "โหลด EasyOCR เสมอเพราะเป็นตัวหลักหรือตัวสำรอง",
    "Wrap sync call in thread": "ครอบการเรียกแบบซิงโครนัสในเธรด",
    "Run EasyOCR (Pre-loaded)": "รัน EasyOCR (โหลดไว้แล้ว)",
    "Run Typhoon (if available)": "รัน Typhoon (ถ้ามี)",
    "If both are \"invalid\" but not empty, pick the one with better potential": "ถ้าทั้งคู่ไม่ถูกต้อง (invalid) แต่ไม่ว่างเปล่า ให้เลือกอันที่มีศักยภาพดีกว่า",
    "Remove duplicates while preserving order": "ลบข้อมูลซ้ำโดยยังคงรักษาลำดับเดิมไว้",
    "Newer API (e.g. GroundingDinoProcessor variants)": "API ใหม่ (เช่น กลุ่ม GroundingDinoProcessor)",
    "Backward-compatible API uses `threshold` instead of `box_threshold`.": "API ที่รองรับเวอร์ชันเก่าจะใช้ `threshold` แทน `box_threshold`",
    "Mapping Taxonomy": "การจับคู่หมวดหมู่ (Taxonomy)",
    "If no Roboflow package found, keep all DINO (could be noise, but better than nothing)": "หากไม่พบกล่องบรรจุภัณฑ์จาก Roboflow ให้เก็บผลลัพธ์ DINO ทั้งหมดไว้ (อาจมีขยะปน แต่ก็ดีกว่าไม่ได้อะไรเลย)"
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
    process_file('backend/app/services/ocr_engine.py')
    process_file('backend/app/services/detector.py')
