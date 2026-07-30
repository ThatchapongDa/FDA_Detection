from app.core.database import SessionLocal, engine, Base
from sqlalchemy import text

def clean_db():
    db = SessionLocal()
    try:
        print("Cleaning database...")
        # ล้างข้อมูลในตาราง scan_records และ Reset ID
        db.execute(text("TRUNCATE TABLE scan_records RESTART IDENTITY CASCADE;"))
        db.commit()
        print("Database cleaned successfully!")
    except Exception as e:
        print(f"Error cleaning database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_db()
