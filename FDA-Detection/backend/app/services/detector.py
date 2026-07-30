import io
import os
import tempfile
import json
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import requests
import torch
import logging
from PIL import Image
from roboflow import Roboflow

logger = logging.getLogger("api")

class FDADetector:
    """
    State-based detector:
    - A: Grounding DINO (open-vocabulary detection)
    - B: Grounding DINO + SAM (segmentation-enhanced crops)
    - C: Pure Vision (Grounding DINO + SAM only, No Roboflow)
    Fallback: Roboflow hosted model (if State A/B)
    """

    def __init__(self, api_key=None, project_id=None, version=None, workspace=None):
        self.api_key = api_key or os.getenv("ROBOFLOW_API_KEY", "YOUR_API_KEY_PLACEHOLDER")
        self.project_id = project_id or os.getenv("ROBOFLOW_PROJECT_ID", "package-fl0a2")
        self.version = version or int(os.getenv("ROBOFLOW_VERSION", "1"))
        self.workspace = workspace or os.getenv("ROBOFLOW_WORKSPACE", "henrik-lauridsen-msqpz")

        # DETECTION_STATE=A|B|C ; default=B
        self.detection_state = (os.getenv("DETECTION_STATE", "B") or "B").upper()
        # อนุกรมวิธานที่มีโครงสร้างสำหรับการจำแนกประเภทด้วย AI
        self.gdino_prompt = os.getenv(
            "GROUNDING_DINO_PROMPT",
            "product packaging . label . blister pack . marketing banner . user interface screen",
        )

        self.model = None  # Roboflow model
        self.gdino_model = None
        self.gdino_processor = None
        self.sam_model = None
        self.sam_processor = None

        # [ย้อนกลับ] บังคับใช้ CPU เพื่อความเสถียรและความเรียบง่าย
        self.device = torch.device("cpu")
        print(f"🚀 FDADetector Device: {self.device}")

        self._initialize_models()

    def _runtime_config_path(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/settings.json"))

    def _refresh_runtime_state(self):
        try:
            cfg_path = self._runtime_config_path()
            if not os.path.exists(cfg_path):
                return
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            state = (cfg.get("detection_state") or self.detection_state or "B").upper()
            if state not in {"A", "B", "C"}:
                state = "B"
            self.detection_state = state
            if cfg.get("grounding_dino_prompt"):
                self.gdino_prompt = cfg["grounding_dino_prompt"]
        except Exception:
            # รักษาสถานะตัวตรวจจับเดิมไว้หากการตั้งค่าตอนรันไทม์ล้มเหลว
            pass

    def _initialize_models(self):
        self._initialize_grounding_dino()
        self._initialize_sam()

        # เก็บ Roboflow ไว้เป็นตัวเลือกสำรองเพื่อความปลอดภัย
        self._initialize_roboflow_model()

    def _initialize_grounding_dino(self):
        try:
            from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

            model_id = os.getenv("GROUNDING_DINO_MODEL_ID", "IDEA-Research/grounding-dino-base")
            self.gdino_processor = AutoProcessor.from_pretrained(model_id)
            # [ย้อนกลับ] ใช้ FP32 มาตรฐานบน CPU
            self.gdino_model = AutoModelForZeroShotObjectDetection.from_pretrained(
                model_id, 
                dtype=torch.float32
            ).to(self.device)
            self.gdino_model.eval()
            print(f"Grounding DINO initialized on {self.device}: {model_id}")
        except Exception as e:
            print(f"Grounding DINO init failed, fallback to Roboflow only: {e}")
            self.gdino_model = None
            self.gdino_processor = None

    def _initialize_sam(self):
        try:
            from transformers import SamModel, SamProcessor

            model_id = os.getenv("SAM_MODEL_ID", "facebook/sam-vit-base")
            self.sam_processor = SamProcessor.from_pretrained(model_id)
            # [ย้อนกลับ] ใช้ FP32 มาตรฐานบน CPU
            self.sam_model = SamModel.from_pretrained(
                model_id,
                dtype=torch.float32
            ).to(self.device)
            self.sam_model.eval()
            
            print(f"SAM initialized on {self.sam_model.device} (FP16={torch.cuda.is_available()}): {model_id}")
        except Exception as e:
            print(f"SAM init failed (state B will use box crops): {e}")
            self.sam_model = None
            self.sam_processor = None

    def _initialize_roboflow_model(self):
        if self.api_key == "YOUR_API_KEY_PLACEHOLDER":
            print("Warning: Roboflow API Key not set. Roboflow fallback disabled.")
            return

        try:
            rf = Roboflow(api_key=self.api_key)
            project = rf.workspace(self.workspace).project(self.project_id) if self.workspace else rf.workspace().project(self.project_id)
            self.model = project.version(self.version).model
            print(f"Roboflow fallback initialized: {self.workspace}/{self.project_id}/{self.version}")
        except Exception as e:
            print(f"Failed to initialize Roboflow model fallback: {e}")
            self.model = None

    def _load_image(self, image_source: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
        temp_file_path = None
        if image_source.startswith("http://") or image_source.startswith("https://"):
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://shopee.co.th/",
            }
            response = requests.get(image_source, headers=headers, timeout=15)
            response.raise_for_status()
            arr = np.frombuffer(response.content, dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(response.content)
                temp_file_path = tmp.name
            return image, temp_file_path

        image = cv2.imread(image_source)
        return image, temp_file_path

    def _cleanup_temp(self, temp_file_path: Optional[str]):
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

    def nms(self, predictions: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """
        Non-Maximum Suppression to filter redundant boxes.
        Sorts by confidence and removes boxes with IoU > threshold.
        """
        if not predictions:
            return []

        # เรียงลำดับตามความมั่นใจจากมากไปน้อย
        sorted_preds = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
        keep = []
        
        while sorted_preds:
            best_pred = sorted_preds.pop(0)
            keep.append(best_pred)
            best_box = self._to_xyxy(best_pred)
            
            # เก็บเฉพาะการทำนายที่ไม่ทับซ้อนกับการทำนายที่ดีที่สุด (best_pred) มากเกินไป
            sorted_preds = [
                p for p in sorted_preds 
                if self._iou(best_box, self._to_xyxy(p)) < iou_threshold
            ]
            
        return keep

    def _gdino_detect(self, image_bgr: np.ndarray, confidence: float) -> Dict:
        if self.gdino_model is None or self.gdino_processor is None:
            return {"predictions": []}

        import torch

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        inputs = self.gdino_processor(images=pil_image, text=self.gdino_prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.gdino_model(**inputs)

        target_sizes = torch.tensor([pil_image.size[::-1]])
        box_thr = max(0.1, confidence / 100.0)
        try:
            # API ใหม่ (เช่น กลุ่ม GroundingDinoProcessor)
            results = self.gdino_processor.post_process_grounded_object_detection(
                outputs=outputs,
                input_ids=inputs.input_ids,
                box_threshold=box_thr,
                text_threshold=0.2,
                target_sizes=target_sizes,
            )
        except TypeError:
            # API ที่รองรับเวอร์ชันเก่าจะใช้ `threshold` แทน `box_threshold`
            results = self.gdino_processor.post_process_grounded_object_detection(
                outputs=outputs,
                input_ids=inputs.input_ids,
                threshold=box_thr,
                text_threshold=0.2,
                target_sizes=target_sizes,
            )

        predictions = []
        if results:
            scores = results[0]["scores"]
            boxes = results[0]["boxes"]
            labels = results[0].get("text_labels", results[0].get("labels", []))
            
            for score, label, box in zip(scores, labels, boxes):
                x1, y1, x2, y2 = box.tolist()
                
                width = max(0.0, x2 - x1)
                height = max(0.0, y2 - y1)
                
                # การจับคู่หมวดหมู่ (Taxonomy)
                raw_label = str(label).lower().strip().replace(".", "")
                mapped_class = "UNKNOWN"
                
                if any(k in raw_label for k in ["product", "packaging"]): mapped_class = "PRODUCT"
                elif any(k in raw_label for k in ["label", "registration"]): mapped_class = "LABEL"
                elif any(k in raw_label for k in ["blister", "strip"]): mapped_class = "BLISTER"
                elif any(k in raw_label for k in ["marketing", "banner"]): mapped_class = "MARKETING"
                elif any(k in raw_label for k in ["interface", "ui", "screen"]): mapped_class = "UI"

                predictions.append(
                    {
                        "x": x1 + width / 2.0,
                        "y": y1 + height / 2.0,
                        "width": width,
                        "height": height,
                        "confidence": float(score.item() * 100.0),
                        "class": mapped_class,
                        "raw_class": raw_label
                    }
                )
        return {"predictions": predictions}

    def _roboflow_detect(self, image_source: str, confidence: float, overlap: float) -> Dict:
        if not self.model:
            return {"predictions": []}
        return self.model.predict(image_source, confidence=confidence, overlap=overlap).json()

    def _to_xyxy(self, pred: Dict) -> Tuple[float, float, float, float]:
        x = float(pred.get("x", 0.0))
        y = float(pred.get("y", 0.0))
        w = float(pred.get("width", 0.0))
        h = float(pred.get("height", 0.0))
        return (x - w / 2.0, y - h / 2.0, x + w / 2.0, y + h / 2.0)

    def _iou(self, a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        iw = max(0.0, ix2 - ix1)
        ih = max(0.0, iy2 - iy1)
        inter = iw * ih
        if inter <= 0:
            return 0.0
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        denom = area_a + area_b - inter
        return inter / denom if denom > 0 else 0.0

    def _filter_dino_with_package(self, dino_preds: List[Dict], rf_preds: List[Dict]) -> List[Dict]:
        """
        Filters DINO predictions (internal details) to only keep those 
        that are inside a detected Package/Bottle/Box.
        """
        if not dino_preds:
            return []
        if not rf_preds:
            # หากไม่พบกล่องบรรจุภัณฑ์จาก Roboflow ให้เก็บผลลัพธ์ DINO ทั้งหมดไว้ (อาจมีขยะปน แต่ก็ดีกว่าไม่ได้อะไรเลย)
            return dino_preds

        package_boxes = []
        for r in rf_preds:
            cls = str(r.get("class", "")).lower()
            if any(k in cls for k in ["package", "box", "bottle", "label"]):
                package_boxes.append(self._to_xyxy(r))

        if not package_boxes:
            package_boxes = [self._to_xyxy(r) for r in rf_preds]

        out = []
        for d in dino_preds:
            dbox = self._to_xyxy(d)
            # การทำนายของ DINO ต้องทับซ้อนกับกล่องบรรจุภัณฑ์อย่างน้อยหนึ่งกล่อง
            if any(self._iou(dbox, pbox) >= 0.05 for pbox in package_boxes):
                # ปรับให้เป็นป้ายกำกับที่ผู้ใช้เข้าใจง่ายแทนชื่อทางเทคนิคของโมเดล
                d["class"] = "FDA / Registration Label"
                out.append(d)
        return out

    def detect(self, image_source, confidence=25, overlap=30):
        temp_file_path = None
        try:
            self._refresh_runtime_state()
            image, temp_file_path = self._load_image(image_source)
            if image is None:
                return {"predictions": []}

            base_conf = min(20, confidence)
            prediction_source = temp_file_path or image_source
            img_h, img_w = image.shape[:2]

            # ─────────────────────────────────────────────────────────────
            # STAGE 1: Roboflow → Product Locator
            # Find the product packaging (box/bottle/blister) in the full image
            # ─────────────────────────────────────────────────────────────
            rf_result = self._roboflow_detect(prediction_source, base_conf, overlap)
            rf_preds = rf_result.get("predictions", [])

            product_boxes = []
            for r in rf_preds:
                if r.get("confidence", 0) <= 1.0:
                    r["confidence"] = r["confidence"] * 100.0
                c = str(r.get("class", "")).lower()
                if any(k in c for k in ["package", "bottle", "box", "label", "blister"]):
                    r["class"] = "PRODUCT"
                product_boxes.append(r)

            print(f"[Stage 1] Roboflow found {len(product_boxes)} product(s).")

            # ─────────────────────────────────────────────────────────────
            # STAGE 2: DINO → FDA Label Finder (within each product crop)
            # ─────────────────────────────────────────────────────────────
            label_preds = []

            if product_boxes and self.detection_state != "C":
                for prod in product_boxes:
                    px, py = float(prod["x"]), float(prod["y"])
                    pw, ph = float(prod["width"]), float(prod["height"])

                    # 5% padding for context
                    pad_x = int(pw * 0.05)
                    pad_y = int(ph * 0.05)
                    x1 = max(0, int(px - pw / 2) - pad_x)
                    y1 = max(0, int(py - ph / 2) - pad_y)
                    x2 = min(img_w, int(px + pw / 2) + pad_x)
                    y2 = min(img_h, int(py + ph / 2) + pad_y)

                    if x2 <= x1 or y2 <= y1:
                        continue

                    product_crop = image[y1:y2, x1:x2]
                    if product_crop.size == 0:
                        continue

                    # รัน DINO บนบริเวณภาพสินค้าที่ตัดมา
                    dino_result = self._gdino_detect(product_crop, base_conf)
                    crop_preds = dino_result.get("predictions", [])

                    # ปรับขนาดพิกัด DINO กลับไปยังพื้นที่ภาพเต็ม
                    for p in crop_preds:
                        p["x"] = p["x"] + x1
                        p["y"] = p["y"] + y1
                        p["product_region"] = [x1, y1, x2, y2]
                        label_preds.append(p)

                    print(f"  Product [{x1},{y1},{x2},{y2}] -> DINO found {len(crop_preds)} label(s)")
            else:
                # Fallback: No product box from Roboflow -> full image DINO
                print("[Stage 2 Fallback] No product found. Running DINO on full image.")
                dino_result = self._gdino_detect(image, base_conf)
                label_preds = dino_result.get("predictions", [])

            # ─────────────────────────────────────────────────────────────
            # COMBINE + FILTER
            # ─────────────────────────────────────────────────────────────
            combined_raw = product_boxes + label_preds
            dedup_preds = self.nms(combined_raw, iou_threshold=0.45)

            thresholds = {
                "LABEL": 40, "BLISTER": 35, "PRODUCT": 25,
                "MARKETING": 25, "UI": 25, "UNKNOWN": 25
            }
            final_preds = [
                p for p in dedup_preds
                if p["confidence"] >= thresholds.get(p.get("class", "UNKNOWN"), 25)
            ]

            print(f"[Detection Complete] {len(final_preds)} final prediction(s).")
            return {"predictions": final_preds}

        except Exception as e:
            print(f"Prediction error: {e}")
            return {"predictions": []}
        finally:
            self._cleanup_temp(temp_file_path)


    def _sam_refine_crop(self, image_bgr: np.ndarray, pred: Dict) -> Optional[np.ndarray]:
        if self.sam_model is None or self.sam_processor is None:
            return None
        try:
            import torch

            x, y, w, h = pred["x"], pred["y"], pred["width"], pred["height"]
            x1, y1 = max(0, int(x - w / 2)), max(0, int(y - h / 2))
            x2, y2 = int(x + w / 2), int(y + h / 2)
            if x2 <= x1 or y2 <= y1:
                return None

            rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)
            input_boxes = [[[x1, y1, x2, y2]]]
            
            inputs = self.sam_processor(images=pil_image, input_boxes=input_boxes, return_tensors="pt").to(self.sam_model.device)
            
            with torch.no_grad():
                outputs = self.sam_model(**inputs)

            masks = self.sam_processor.image_processor.post_process_masks(
                outputs.pred_masks.to("cpu"),
                inputs["original_sizes"].to("cpu"),
                inputs["reshaped_input_sizes"].to("cpu"),
            )
            if not masks:
                return None

            mask = masks[0][0][0].numpy() > 0.5
            ys, xs = np.where(mask)
            if len(xs) == 0 or len(ys) == 0:
                return None

            mx1, my1, mx2, my2 = xs.min(), ys.min(), xs.max(), ys.max()
            crop = image_bgr[my1:my2, mx1:mx2]
            if crop.size == 0:
                return None
            return crop
        except Exception:
            return None

    def crop_fda_labels(self, image_path, predictions):
        self._refresh_runtime_state()
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")

        cropped_images: List[np.ndarray] = []
        if "predictions" not in predictions:
            return cropped_images

        for pred in predictions["predictions"]:
            x = pred["x"]
            y = pred["y"]
            w = pred["width"]
            h = pred["height"]

            pad_w = int(w * 0.10)
            pad_h = int(h * 0.10)

            x1 = int(x - (w / 2) - pad_w)
            y1 = int(y - (h / 2) - pad_h)
            x2 = int(x + (w / 2) + pad_w)
            y2 = int(y + (h / 2) + pad_h)

            height, width, _ = image.shape
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)

            if x2 <= x1 or y2 <= y1:
                continue

            # [ข้อจำกัด SAM] จำกัดการปรับแต่งสูงสุด 2 ครอปต่อคำขอเพื่อประหยัด VRAM
            if len(cropped_images) < 2:
                sam_crop = self._sam_refine_crop(image, pred)
                if sam_crop is not None and sam_crop.size > 0:
                    cropped_images.append(sam_crop)
                    continue

            crop = image[y1:y2, x1:x2]
            if crop.size > 0:
                cropped_images.append(crop)

        return cropped_images
    
    def crop_fda_labels_with_sam(self, image_bgr: np.ndarray, pred: Dict) -> List[np.ndarray]:
        """
        Phase 1 Optimization: Crop with conditional SAM.
        Returns list of cropped images using SAM refinement.
        """
        cropped_images = []
        try:
            x = pred["x"]
            y = pred["y"]
            w = pred["width"]
            h = pred["height"]

            pad_w = int(w * 0.10)
            pad_h = int(h * 0.10)

            x1 = int(x - (w / 2) - pad_w)
            y1 = int(y - (h / 2) - pad_h)
            x2 = int(x + (w / 2) + pad_w)
            y2 = int(y + (h / 2) + pad_h)

            height, width, _ = image_bgr.shape
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)

            if x2 <= x1 or y2 <= y1:
                return cropped_images

            # ลองใช้ SAM ปรับแต่งรายละเอียดก่อน
            sam_crop = self._sam_refine_crop(image_bgr, pred)
            if sam_crop is not None and sam_crop.size > 0:
                cropped_images.append(sam_crop)
                return cropped_images

            # Fallback to box crop
            crop = image_bgr[y1:y2, x1:x2]
            if crop.size > 0:
                cropped_images.append(crop)
                
        except Exception as e:
            print(f"SAM crop error: {e}")
        
        return cropped_images
