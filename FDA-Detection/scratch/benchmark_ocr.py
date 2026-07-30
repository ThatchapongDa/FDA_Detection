import time
import cv2
import numpy as np
import easyocr
import requests
import base64
import os
from typing import Dict, Any

# Mock Typhoon API Key if not in env for script safety
TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY", "")

def preprocess_image(image_path: str, resize_factor: float = 1.0, grayscale: bool = False):
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    if grayscale:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if resize_factor != 1.0:
        h, w = img.shape[:2]
        new_size = (int(w * resize_factor), int(h * resize_factor))
        img = cv2.resize(img, new_size, interpolation=cv2.INTER_LANCZOS4)
    
    return img

def test_easyocr(image: np.ndarray, languages=['th', 'en']):
    reader = easyocr.Reader(languages, gpu=False)
    start = time.time()
    results = reader.readtext(image)
    end = time.time()
    
    text = " ".join([r[1] for r in results])
    return {
        "engine": "EasyOCR",
        "time": end - start,
        "text_len": len(text),
        "preview": text[:100]
    }

def test_typhoon(image: np.ndarray):
    if not TYPHOON_API_KEY:
        return {"engine": "Typhoon", "error": "No API Key"}
    
    # Encode image
    success, buffer = cv2.imencode('.jpg', image)
    if not success:
        return {"engine": "Typhoon", "error": "Encode failed"}
    
    base64_image = base64.b64encode(buffer).decode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TYPHOON_API_KEY}"
    }
    
    payload = {
        "model": "typhoon-ocr",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    start = time.time()
    try:
        response = requests.post("https://api.opentyphoon.ai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        text = result['choices'][0]['message']['content']
    except Exception as e:
        return {"engine": "Typhoon", "error": str(e)}
    end = time.time()
    
    return {
        "engine": "Typhoon",
        "time": end - start,
        "text_len": len(text),
        "preview": text[:100]
    }

def run_benchmarks(image_path: str):
    print(f"Benchmarking Image: {image_path}")
    results = []
    
    configs = [
        {"name": "Original", "resize": 1.0, "gray": False},
        {"name": "Resize 0.5x", "resize": 0.5, "gray": False},
        {"name": "Resize 2.0x", "resize": 2.0, "gray": False},
        {"name": "Grayscale", "resize": 1.0, "gray": True},
        {"name": "Resize 0.5x + Gray", "resize": 0.5, "gray": True},
    ]
    
    for config in configs:
        print(f"\n--- Testing Config: {config['name']} ---")
        img = preprocess_image(image_path, config['resize'], config['gray'])
        if img is None:
            print("Failed to load image")
            continue
        
        # EasyOCR
        e_res = test_easyocr(img)
        e_res["config"] = config["name"]
        results.append(e_res)
        print(f"EasyOCR: {e_res['time']:.2f}s | Len: {e_res['text_len']}")
        
        # Typhoon (Only once per config to save budget, or just once overall)
        # For this test, let's run it on Original and Resize 0.5
        if config['name'] in ["Original", "Resize 0.5x"]:
            t_res = test_typhoon(img)
            t_res["config"] = config["name"]
            results.append(t_res)
            print(f"Typhoon: {t_res.get('time', 0):.2f}s | Len: {t_res.get('text_len', 0)}")

    return results

if __name__ == "__main__":
    img_path = r"D:\Project\FDA detectionV2\FDA-Detection\backend\debug_failsafe.png"
    if os.path.exists(img_path):
        bench_results = run_benchmarks(img_path)
        # Print summary
        print("\n\n" + "="*30)
        print("BENCHMARK SUMMARY")
        print("="*30)
        for r in bench_results:
            if "error" in r:
                print(f"{r['engine']} ({r['config']}): ERROR {r['error']}")
            else:
                print(f"{r['engine']} ({r['config']}): {r['time']:.2f}s | Len: {r['text_len']}")
    else:
        print(f"Image not found at {img_path}")
