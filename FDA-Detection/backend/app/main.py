from fastapi import FastAPI
from app.api import endpoints
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.services.detector import FDADetector
from app.services.ocr_engine import OCREngine
from app.services.scraper import ShopeeScraper
from app.core.logger import setup_logger
import numpy as np
import logging
# Silence noisy uvicorn access logs (polling status/history)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = setup_logger("main")

app = FastAPI(title="FDA Detection System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "FDA Detection System API is running"}

@app.on_event("startup")
async def startup_event():
    """
    Model warm-up at startup for CPU mode.
    """
    logger.info("🚀 Starting up FDA Detection System (CPU Stable Mode)...")
    logger.info("Warming up models...")
    
    try:
        # Initialize Detector (DINO + SAM)
        logger.info("Loading Detector (DINO + SAM)...")
        endpoints.detector = FDADetector()
        
        # Warm-up Inference
        logger.info("Warming up AI models...")
        try:
            dummy_img = np.zeros((640, 480, 3), dtype=np.uint8)
            # Warm-up DINO
            _ = endpoints.detector._gdino_detect(dummy_img, confidence=25)
            # Warm-up SAM
            dummy_pred = {"x": 320, "y": 240, "width": 100, "height": 100}
            _ = endpoints.detector._sam_refine_crop(dummy_img, dummy_pred)
            
            logger.info("✓ AI models warmed up")
        except Exception as e:
            logger.warning(f"Warm-up partially failed: {e}")
        
        # Initialize OCR Engine
        logger.info("Loading OCR Engine...")
        endpoints.ocr_engine = OCREngine()
        logger.info("✓ OCR Engine loaded")
        
        # Initialize Scraper
        logger.info("Initializing Scraper...")
        endpoints.scraper = ShopeeScraper()
        logger.info("✓ Scraper ready")
        
        logger.info("✅ Startup Complete (CPU Stable Mode)")
    
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up at shutdown"""
    logger.info("Shutting down FDA Detection System...")
    # Clean up resources if needed
