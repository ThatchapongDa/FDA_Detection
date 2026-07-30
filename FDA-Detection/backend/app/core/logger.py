import logging
import sys
import os

def setup_logger(name="app"):
    """
    Sets up a structured logger for the application.
    Output: JSON or formatted string to stdout.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Check if handlers are already set to avoid duplication
    if not logger.handlers:
        # 1. Stream Handler (Console)
        stream_handler = logging.StreamHandler(sys.stdout)
        
        # 2. File Handler (app.log)
        file_handler = logging.FileHandler("app.log", encoding="utf-8")
        
        # Format: timestamp level message
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        
    return logger
