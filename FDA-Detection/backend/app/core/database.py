import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# [Environment Aware] Use 'localhost' for Native Windows, 'db' for Docker
default_host = "localhost" if os.name == "nt" else "db"
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://postgres:postgres@{default_host}:5432/fda_detection")
if os.name == "nt" and "@db:" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("@db:", "@localhost:")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
