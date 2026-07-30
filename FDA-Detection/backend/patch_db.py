import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fda_detection")

# We use the engine to perform the heavy lifting
engine = create_engine(DATABASE_URL)

def migrate():
    print(f"🚀 Starting Migration on: {DATABASE_URL}")
    with engine.connect() as conn:
        try:
            # 1. Add the new column
            print("🛡️  Adding column 'scraped_ad_license'...")
            conn.execute(text("ALTER TABLE scan_records ADD COLUMN IF NOT EXISTS scraped_ad_license VARCHAR;"))
            conn.commit()
            print("✅  Successfully added 'scraped_ad_license'!")
        except Exception as e:
            print(f"❌  Migration failed: {e}")

if __name__ == "__main__":
    migrate()
