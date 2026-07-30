import easyocr
import numpy as np
import cv2
import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

class EasyOCREngine:
    def __init__(self, languages=['th', 'en'], gpu=False):
        print(f"Loading EasyOCR with languages: {languages} (GPU={gpu})...")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        print("EasyOCR loaded.")

    def extract_text(self, image_input, context="general"):
        """
        Now returns (text, confidence) for better evidence ranking.
        """
        try:
            if isinstance(image_input, np.ndarray) and image_input.size == 0:
                 return "", 0.0
                 
            # ใช้ detail=1 เพื่อดึงข้อมูลกรอบข้อความ, ข้อความ, และความมั่นใจ
            results = self.reader.readtext(image_input, detail=1)
            
            if not results:
                return "", 0.0
                
            texts = [r[1] for r in results]
            confidences = [r[2] for r in results]
            
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            return " ".join(texts), avg_conf
            
        except Exception as e:
            print(f"EasyOCR Error: {e}")
            return "", 0.0

class TyphoonOCREngine:
    def __init__(self, api_key, base_url="https://api.opentyphoon.ai/v1/chat/completions", model="typhoon-ocr"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
        # ตั้งค่าเซสชันพร้อมการลองใหม่เพื่อความเสถียรระดับ Full Throttle
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        
        print(f"🚀 Initialized Typhoon OCR (Full Throttle) with model: {model}")

    def _encode_image(self, image_input):
        """Convert OpenCV image (numpy), path, or bytes to base64 string"""
        try:
            if isinstance(image_input, str):
                if image_input.startswith("http"):
                    print(f"Warning: URL string passed to _encode_image: {image_input}")
                    return None
                if os.path.exists(image_input):
                    with open(image_input, "rb") as image_file:
                        return base64.b64encode(image_file.read()).decode('utf-8')
                else:
                    return None
            elif isinstance(image_input, bytes):
                return base64.b64encode(image_input).decode('utf-8')
            elif isinstance(image_input, np.ndarray):
                success, buffer = cv2.imencode('.jpg', image_input)
                if not success:
                    return None
                return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            print(f"Image encoding error: {e}")
            return None

    def extract_text(self, image_input, context="general"):
        """
        Typhoon doesn't return character confidence, 
        returning a default of 0.9 for non-empty results as per approved plan.
        """
        base64_image = self._encode_image(image_input)
        if not base64_image:
            return "", 0.0

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # [STRICT PROMPT] ปรับจูนให้เป็นงาน OCR บริสุทธิ์ ป้องกัน AI บรรยายภาพเกินหน้าที่
        base_instruction = "Return ONLY the exact transcribed text from the image. Do NOT include descriptions, summaries, observations, or any extra commentary like 'Observation:' or 'Final Summary:'. Transcription only."
        
        if context == "fda":
            prompt = f"{base_instruction} Extract all text and numbers from this Thai FDA label. Focus on registration numbers (e.g., 1A 1/2566 or 10-1-12345-1-0001)."
        else:
            prompt = f"{base_instruction} Extract all readable Thai and English text in the order it appears."

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            "max_tokens": 1000
        }

        try:
            response = self.session.post(self.base_url, headers=headers, json=payload, timeout=25)
            response.raise_for_status()
            result = response.json()
            text = result['choices'][0]['message']['content'].strip()
            # [แบบเต็มสปีด] ค่าเริ่มต้นความมั่นใจสูงสำหรับ Typhoon
            return text, (0.95 if text else 0.0)
        except Exception as e:
            print(f"Typhoon API Error (Retries exhausted): {e}")
            return "", 0.0

class OCREngine:
    def __init__(self):
        self.typhoon_key = os.getenv("TYPHOON_API_KEY")
        self.mode = "typhoon" if self.typhoon_key else "easyocr"
        self.gpu_semaphore = asyncio.Semaphore(4) 
        
        # โหลด engine ทั้งสองไว้ล่วงหน้าแบบ Singleton เพื่อป้องกันความล่าช้าในการโหลดซ้ำ
        print(f"📦 Initializing OCREngine (Mode: {self.mode})")
        
        # โหลด EasyOCR เสมอเพราะเป็นตัวหลักหรือตัวสำรอง
        self.easy_engine = EasyOCREngine(gpu=False)
        
        if self.typhoon_key:
            self.typhoon_engine = TyphoonOCREngine(
                api_key=self.typhoon_key,
                base_url=os.getenv("TYPHOON_ENDPOINT", "https://api.opentyphoon.ai/v1/chat/completions"),
                model=os.getenv("TYPHOON_MODEL", "typhoon-ocr")
            )
            self.engine = self.typhoon_engine
        else:
            self.typhoon_engine = None
            self.engine = self.easy_engine

    def validate_ocr_quality(self, text: str, confidence: float) -> bool:
        """
        Validates if the OCR output is acceptable evidence.
        Checks for length, character diversity, and confidence.
        """
        if not text or len(text.strip()) < 2:
            return False
        
        # ป้องกัน Prompt Echo: หากผลลัพธ์มีคีย์เวิร์ดจาก prompt ถือว่า AI หลอนข้อมูล (Hallucination)
        prompt_keywords = ["extract", "instructions", "return only", "registration", "identify"]
        text_lower = text.lower()
        if any(k in text_lower for k in prompt_keywords) and len(text_lower) < 200:
            if "extract" in text_lower or "instructions" in text_lower:
                return False
            
        if confidence < 0.25: 
            return False
            
        return True

    def clean_ocr_text(self, text: str) -> str:
        """
        Forcefully strips common AI 'chatter' or descriptive headers.
        """
        if not text:
            return ""
            
        # ล้างพวก Observation หรือ Summary ที่ AI ชอบแถมมา
        junk_markers = [
            "Observation:", "Final Summary:", "Summary:", 
            "Description:", "Transcription:", "Image Analysis:",
            "ภาพแสดง", "ลักษณะเป็น", "พื้นหลังเป็น"
        ]
        
        cleaned = text
        for marker in junk_markers:
            # ลบ marker และข้อความที่ตามหลังจนจบประโยคหรือบรรทัด (ถ้าสั้นๆ)
            if marker in cleaned:
                # กรณีเป็น Header ให้ลบแค่ตัวมันเอง
                cleaned = cleaned.replace(marker, "")
        
        # ลบ *** ที่ AI ชอบครอบมา
        cleaned = cleaned.replace("***", "").strip()
        
        return cleaned

    def extract_text(self, image_input, context="general"):
        text, conf = self.engine.extract_text(image_input, context)
        return self.clean_ocr_text(text), conf

    async def process_crops(self, cropped_images, context="general"):
        """
        Automatically uses Dual OCR if Typhoon is available.
        Uses controlled concurrency via Semaphore if running on GPU.
        """
        if self.typhoon_key:
            return await self.process_crops_parallel_dual(cropped_images, context)
            
        results = []
        
        max_workers = 4
        
        async def run_ocr_with_semaphore(img):
            async with self.gpu_semaphore:
                # ครอบการเรียกแบบซิงโครนัสในเธรด
                loop = asyncio.get_event_loop()
                text, confidence = await loop.run_in_executor(None, self.extract_text, img, context)
                return text, confidence

        tasks = [run_ocr_with_semaphore(img) for img in cropped_images]
        ocr_results = await asyncio.gather(*tasks)

        for text, confidence in ocr_results:
            is_valid = self.validate_ocr_quality(text, confidence)
            results.append({
                "text": text,
                "confidence": confidence,
                "valid": is_valid
            })
        return results
    
    async def process_crops_parallel_dual(self, cropped_images, context="general", max_workers=4):
        """
        True Parallel dual OCR execution.
        """
        if not self.typhoon_key:
            return await self.process_crops(cropped_images, context)
        
        final_results = []
        try:
            loop = asyncio.get_event_loop()
            
            def run_dual_ocr(img):
                t_text, t_conf = "", 0.0
                e_text, e_conf = "", 0.0
                
                # [PERF] EasyOCR ได้ประโยชน์จาก grayscale — ลดข้อมูล 3× ทำให้อ่านเร็วขึ้น
                # Typhoon เป็น API ใช้สีได้โดยตรง ไม่ต้อง grayscale
                if isinstance(img, np.ndarray) and len(img.shape) == 3:
                    img_for_easy = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    img_for_easy = img
                
                # รัน EasyOCR ด้วย grayscale
                e_text, e_conf = self.easy_engine.extract_text(img_for_easy, context)
                e_text = self.clean_ocr_text(e_text)
                
                # รัน Typhoon ด้วยภาพสีเดิม (ถ้ามี)
                if self.typhoon_engine:
                    t_text, t_conf = self.typhoon_engine.extract_text(img, context)
                    t_text = self.clean_ocr_text(t_text)

                # การเลือกอัจฉริยะ: ตรวจสอบคุณภาพก่อนเลือก
                t_valid = self.validate_ocr_quality(t_text, t_conf)
                e_valid = self.validate_ocr_quality(e_text, e_conf)
                
                if t_valid:
                    return t_text, t_conf, True
                elif e_valid:
                    return e_text, e_conf, True
                else:
                    best_text = t_text if t_conf >= e_conf else e_text
                    return best_text, max(t_conf, e_conf), False

            tasks = [loop.run_in_executor(None, run_dual_ocr, img) for img in cropped_images]
            ocr_results = await asyncio.gather(*tasks)

            for text, confidence, is_valid in ocr_results:
                final_results.append({
                    "text": text,
                    "confidence": confidence,
                    "valid": is_valid
                })
        except Exception as e:
            print(f"Parallel dual OCR failed: {e}")
            return await self.process_crops(cropped_images, context)
        
        return final_results
    
    def _combine_texts(self, easy_text, typhoon_text):
        """Combine and deduplicate results from both engines"""
        texts = [t.strip() for t in [easy_text, typhoon_text] if t and t.strip()]
        
        # ลบข้อมูลซ้ำโดยยังคงรักษาลำดับเดิมไว้
        seen = set()
        combined = []
        for text in texts:
            if text not in seen:
                seen.add(text)
                combined.append(text)
        
        return " ".join(combined)
