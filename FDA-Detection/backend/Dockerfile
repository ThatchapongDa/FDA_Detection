FROM python:3.11-slim-bookworm

# 1. Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

# 2. Install System Dependencies (OpenCV + Build tools + Curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Python Dependencies (Pre-install CPU-only PyTorch for fast build and small image)
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 4. Install Playwright Browsers & OS Dependencies
RUN playwright install --with-deps chromium

# 5. Copy Application Code
COPY . .

# 6. Metadata
EXPOSE 8000

# 7. Start Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
