import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fda_detection")

engine = create_engine(DATABASE_URL)

def update_schema():
    with engine.connect() as conn:
        print("Checking for missing columns...")
        
        # Add product_category
        try:
            conn.execute(text("ALTER TABLE scan_records ADD COLUMN product_category VARCHAR;"))
            print("Added product_category")
        except Exception: pass
        
        # Add shop_location
        try:
            conn.execute(text("ALTER TABLE scan_records ADD COLUMN shop_location VARCHAR;"))
            print("Added shop_location")
        except Exception: pass
        
        # Add scraped_fda_number
        try:
            conn.execute(text("ALTER TABLE scan_records ADD COLUMN scraped_fda_number VARCHAR;"))
            print("Added scraped_fda_number")
        except Exception: pass
        
        # Add risk_reason
        try:
            conn.execute(text("ALTER TABLE scan_records ADD COLUMN risk_reason TEXT;"))
            print("Added risk_reason")
        except Exception: pass
        
        conn.commit()
        print("Schema update completed.")

if __name__ == "__main__":
    update_schema()
