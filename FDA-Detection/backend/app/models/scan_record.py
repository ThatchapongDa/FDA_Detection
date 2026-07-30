from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class ScanRecord(Base):
    __tablename__ = "scan_records"

    id = Column(Integer, primary_key=True, index=True)
    product_url = Column(String, index=True)
    status = Column(String)  # 'pending', 'completed', 'failed'
    
    # Product Metadata
    product_name = Column(String, nullable=True)
    product_description = Column(Text, nullable=True)
    product_category = Column(String, nullable=True)
    product_type = Column(String, nullable=False, default="UNKNOWN")
    product_image = Column(String, nullable=True)  # First product image URL for card display
    shop_location = Column(String, nullable=True)
    
    # Store detected data
    extracted_text = Column(Text, nullable=True) # Full OCR text
    scraped_fda_number = Column(String, nullable=True) # Seller-claimed FDA (Food/Supps)
    scraped_drug_number = Column(String, nullable=True) # Seller-claimed Drug Reg (ยา)
    scraped_ad_license = Column(String, nullable=True) # Advertising License (e.g. ฆพ.)
    fda_numbers = Column(JSON, nullable=True)    # List of detected FDA strings (AI)
    scan_results = Column(JSON, nullable=True)   # Detailed per-image results (boxes, text, etc.)
    
    # Risk Assessment
    risk_level = Column(String, default="UNKNOWN") # LOW, MEDIUM, HIGH
    risk_reason = Column(Text, nullable=True)
    confidence_score = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
