import cv2
import numpy as np

def calculate_sharpness(image_bgr: np.ndarray) -> float:
    """
    Calculates image sharpness using Laplacian variance.
    Normalized to 0.0 - 1.0 (based on var/500 baseline).
    """
    if image_bgr is None or image_bgr.size == 0:
        return 0.0
    try:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normalize: Standard sharp image is usually > 100. High quality > 500.
        return min(1.0, variance / 500.0)
    except Exception:
        return 0.0

def calculate_area_ratio(box: dict, image_shape: tuple) -> float:
    """
    Calculates the ratio of the detection box area to the total image area.
    box: {'width': float, 'height': float} in pixel coordinates.
    image_shape: (height, width, ...)
    """
    if not box or not image_shape or image_shape[0] == 0 or image_shape[1] == 0:
        return 0.0
    
    img_h, img_w = image_shape[0], image_shape[1]
    box_area = box.get('width', 0) * box.get('height', 0)
    img_area = img_w * img_h
    
    return min(1.0, box_area / img_area)

def calculate_text_density(ocr_results: list, image_shape: tuple) -> dict:
    """
    Computes text-related metrics for Soft Rejection bypass logic.
    ocr_results: List of (box, text, confidence) from EasyOCR.
    """
    if not ocr_results or not image_shape:
        return {"area_ratio": 0.0, "count": 0}
    
    img_h, img_w = image_shape[0], image_shape[1]
    img_area = img_w * img_h
    total_text_area = 0
    
    for box, text, conf in ocr_results:
        # box is usually list of 4 points [[x,y], [x,y], [x,y], [x,y]]
        try:
            # Simple rectangle approximation from 4 points
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            total_text_area += (w * h)
        except:
            continue
            
    return {
        "area_ratio": min(1.0, total_text_area / img_area),
        "count": len(ocr_results)
    }
