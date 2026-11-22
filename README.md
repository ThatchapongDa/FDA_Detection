# FDA & Drug Registration Detection System (FDA Detection System)
### ระบบตรวจจับและตรวจสอบข้อความบนฉลากยาและผลิตภัณฑ์สุขภาพบนแพลตฟอร์มพาณิชย์อิเล็กทรอนิกส์

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.1-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.5_(CPU_Stable)-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.3-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

---

## 1. บทนำและที่มาของโครงงาน (Project Overview)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ในปัจจุบันการซื้อขายยาและผลิตภัณฑ์สุขภาพผ่านแพลตฟอร์มพาณิชย์อิเล็กทรอนิกส์ (E-Commerce) เช่น Shopee ได้รับความนิยมอย่างแพร่หลาย อย่างไรก็ดี พบปัญหาการจำหน่ายยาอันตราย ยาที่ไม่ได้ขึ้นทะเบียนตำรับยา หรือผลิตภัณฑ์ที่มีการแสดงเลข อย. ปลอม/ไม่ตรงกับความเป็นจริงเป็นจำนวนมาก ซึ่งส่งผลกระทบโดยตรงต่อความปลอดภัยของผู้บริโภคและขัดต่อข้อกฎหมายตาม **พระราชบัญญัติยา พ.ศ. 2510** และ **พระราชบัญญัติอาหาร พ.ศ. 2522**

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**FDA Detection System** เป็นระบบปัญญาประดิษฐ์อัตโนมัติแบบครบวงจร (End-to-End Pipeline) ที่ได้รับการพัฒนาขึ้นเพื่อช่วยเจ้าหน้าที่กำกับดูแลและผู้บริโภคในการตรวจสอบความถูกต้องของสินค้า โดยระบบสามารถดึงภาพและข้อมูลจากหน้าร้านค้าออนไลน์ ทำการตรวจจับตำแหน่งบรรจุภัณฑ์ (Localization), ตัดขอบฉลากอย่างแม่นยำ (Segmentation), สกัดข้อความภาษาไทยและหมายเลขทะเบียนด้วยโมเดลภาษาขนาดใหญ่ (Vision-LLM OCR), พร้อมทั้งประเมินความสอดคล้องทางกฎหมายและแสดงพยานหลักฐานเชิงประจักษ์ (Explainable AI & Legal Compliance)

---

## 2. คุณสมบัติเด่นของระบบ (Key Features)

1. **Autonomous Stealth Scraper :**
   * ระบบดึงข้อมูลรายละเอียดและรูปภาพสินค้าจาก Shopee อัตโนมัติด้วย Playwright
   * รองรับกลไก Failsafe, การจำลองพฤติกรรมมนุษย์ (Stealth Browsing), และระบบ Session Cookie เพื่อป้องกันการถูกจำกัดการเข้าถึง (Anti-Scraping / HTTP 403)
2. **Smart Image Preprocessing & Filtering :**
   * กรองและปฏิเสธภาพขยะ ป้ายโปรโมชั่นส่วนลด และสติกเกอร์ร้านค้าอัตโนมัติด้วย OpenCV (High Transparency Filter > 90% และ Aspect Ratio Validation)
3. **AI Packaging Localization & Precision Cropping :**
   * **Grounding DINO (Open-Vocabulary Object Detection) :** ค้นหาและระบุตำแหน่งกล่องยา แผงยา (Blister Pack) และขวดยา
   * **Segment Anything Model (SAM ViT-Base) :** ตัดภาพขอบฉลากยาเฉพาะส่วนอย่างละเอียดระดับพิกเซล ช่วยลดสัญญาณรบกวนของภาพพื้นหลังได้กว่า 96.8%
4. **Dual-Engine OCR (High-Precision Thai OCR) :**
   * **Typhoon OCR (Vision-LLM API) :** สกัดข้อความภาษาไทยและเลขทะเบียนยาด้วยความแม่นยำสูงถึง **92.4%** แม้ภาพจะมีความเอียงหรือแสงสะท้อนบนฟอยล์แผงยา
   * **EasyOCR (Local Fallback) :** รองรับการประมวลผลบนเครื่องแบบออฟไลน์
5. **Explainable Legal Compliance & Risk Engine :**
   * เปรียบเทียบข้อมูลที่ร้านค้าระบุ (Claimed Data) กับข้อมูลที่ AI ตรวจพบบนภาพจริง (Vision Data)
   * จำแนกระดับความเสี่ยง 4 ระดับ: `MATCH` (ถูกต้อง), `MISMATCH` (ข้อมูลไม่ตรงกัน), `SHOP_ONLY` (มีแต่ข้อความร้านแต่ภาพไม่มี), และ `NOT_FOUND` (ไม่พบเลขทะเบียน)
   * แสดงกล่องข้อกฎหมายสีแดง (**Legal Violation Alert Box**) ระบุชื่อ พ.ร.บ., มาตราที่ฝ่าฝืน (เช่น พ.ร.บ. ยา 2510 มาตรา 72(4)), และบทลงโทษทันที
6. **Interactive Modern Web Interface :**
   * **Single Scan Center :** ตรวจสอบสินค้าแบบเจาะจงรายชิ้น พร้อมแถบสถานะ Progress Bar และการ์ดพยานหลักฐาน 4 มิติ (Credential Cards)
   * **Deep Dive Evidence Audit :** หน้าต่าง Modal แสดงภาพต้นฉบับพร้อม Bounding Box และภาพฉลากตัดย่อย (SAM Crops)
   * **Autonomous Crawler & Incident History :** ระบบเฝ้าสังเกตการณ์ตลาดออนไลน์อัตโนมัติตามคีย์เวิร์ด

---

## 3. สถาปัตยกรรมการทำงานของระบบ (System Architecture)

```
[ Shopee Product URL ]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ 1. Data Acquisition & Scraping (Playwright)             │
│    - Metadata Extraction (Title, Description, Category)│
│    - Multi-image Download & Transparency Filter        │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ 2. Visual Detection & Segmentation (AI Vision)         │
│    - Grounding DINO: Detect Package/Blister/Label Box  │
│    - Segment Anything Model (SAM): Pixel-level Crop    │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ 3. Text Extraction (Dual OCR Engine)                   │
│    - Typhoon OCR (Vision-LLM) & EasyOCR                │
│    - Regex Validation (Thai FDA 13 Digits / Drug Reg)  │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ 4. Explainable Risk & Legal Assessment                 │
│    - Cross-validation: Claimed vs Vision Data          │
│    - Legal Rule Mapping (พ.ร.บ. ยา 2510 / อาหาร 2522)  │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ 5. Presentation Layer (Next.js / React 18 Web UI)      │
│    - Single Scan / Incident Dashboard                  │
│    - 4D Credential Cards & Legal Violation Alert Box   │
│    - Deep Dive Bounding Box Modal                      │
└────────────────────────────────────────────────────────┘
```

---

## 4. วิธีการติดตั้งและรันระบบ (Quick Start Guide)

ระบบรองรับการรัน 2 รูปแบบ โดยขอแนะนำให้ **รันผ่าน Docker** เพื่อความสะดวกและไม่ต้องติดตั้งสภาพแวดล้อมปัญญาประดิษฐ์บนเครื่องโฮสต์

### วิธีที่ 1: รันผ่าน Docker Compose (แนะนำสำหรับการตรวจโครงงาน)

**ข้อกำหนดเบื้องต้น :** ติดตั้ง [Docker Desktop](https://www.docker.com/products/docker-desktop/) บนเครื่องคอมพิวเตอร์

1. **เปิด Terminal และเข้าไปยังโฟลเดอร์โปรเจกต์ :**
   ```bash
   cd FDA-Detection
   ```

2. **เตรียมไฟล์การตั้งค่า Environment :**
   ```bash
   # หากยังไม่มีไฟล์ .env ให้คัดลอกจากไฟล์ตัวอย่าง
   cp .env.example .env
   ```
   *(หมายเหตุ: ไฟล์ `.env.example` ได้ระบุโครงสร้างการตั้งค่าเริ่มต้นสำหรับเตรียมรันระบบไว้แล้ว)*

3. **สั่ง Build และเริ่มทำงานของทุก Service ด้วยคำสั่งเดียว :**
   ```bash
   docker compose up -d --build
   ```

4. **เข้าใช้งานระบบผ่านเว็บเบราว์เซอร์ :**
   * **Frontend (Web Application) :** [http://localhost:3000](http://localhost:3000)
   * **Backend API (Swagger Docs) :** [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Database (PostgreSQL) :** `localhost:5432` (User/Password: `postgres`)

5. **คำสั่งสั่งหยุดการทำงานเมื่อใช้งานเสร็จสิ้น :**
   ```bash
   docker compose down
   ```

---

### วิธีที่ 2: รันแบบ Native (Local Development)

**ข้อกำหนดเบื้องต้น :**
* Python 3.11
* Node.js 18+ (หรือ Node.js 20+)
* PostgreSQL 15+ กำลังทำงานอยู่ที่พอร์ต 5432

#### 1. การเปิดใช้งาน Backend (FastAPI):
```bash
cd FDA-Detection/backend

# 1. ติดตั้ง PyTorch (CPU-Optimized) และแพ็กเกจที่เกี่ยวข้อง
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 2. ติดตั้งเบราว์เซอร์สำหรับ Playwright
playwright install --with-deps chromium

# 3. สั่งรัน Backend Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. การเปิดใช้งาน Frontend (Next.js):
```bash
cd FDA-Detection/frontend

# 1. ติดตั้ง Node Dependencies
npm install

# 2. สั่งรัน Development Server
npm run dev
```
เปิดเบราว์เซอร์ไปที่ [http://localhost:3000](http://localhost:3000)

---

## 5. ตัวอย่างลิงก์สินค้าสำหรับทดสอบระบบ (Test URLs)

ผู้ตรวจสามารถคัดลอกลิงก์ตัวอย่างสินค้าจริงด้านล่างนี้ ไปวางในช่องสแกนหน้า [http://localhost:3000](http://localhost:3000) เพื่อทดสอบการทำงานของระบบได้ทันที:

### กลุ่มผลิตภัณฑ์ยา (Drug Products)
1. **ยาพาราเซตามอล Paracap 500 mg (ทดสอบการตรวจผ่านเกณฑ์ - MATCH):**
   ```text
   https://shopee.co.th/Paracap-Paracetamol-Tablets-500mg.-%E0%B8%9E%E0%B8%B2%E0%B8%A3%E0%B8%B2%E0%B9%81%E0%B8%84%E0%B8%9E-%E0%B8%9E%E0%B8%B2%E0%B8%A3%E0%B8%B2%E0%B9%80%E0%B8%8B%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%AD%E0%B8%A5-500-%E0%B8%A1%E0%B8%B4%E0%B8%A5%E0%B8%A5%E0%B8%B4%E0%B8%81%E0%B8%A3%E0%B8%B1%E0%B8%A1-10-%E0%B9%80%E0%B8%A1%E0%B9%87%E0%B8%94-50-%E0%B9%81%E0%B8%9C%E0%B8%87-1-%E0%B8%81%E0%B8%A5%E0%B9%88%E0%B8%AD%E0%B8%87-FF-6301-%E0%B8%A2%E0%B8%B2%E0%B8%AA%E0%B8%B2%E0%B8%A1%E0%B8%B1%E0%B8%8D%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%88%E0%B8%B3%E0%B8%9A%E0%B9%89%E0%B8%B2%E0%B8%99-i.97475696.26650534704
   ```
2. **ยาแก้ไอ อาปาเช่ (ทดสอบการตรวจจับเลขทะเบียนตำรับยา):**
   ```text
   https://shopee.co.th/Apache-%E0%B8%A2%E0%B8%B2%E0%B9%81%E0%B8%81%E0%B9%89%E0%B9%84%E0%B8%AD-%E0%B8%AD%E0%B8%B2%E0%B8%9B%E0%B8%B2%E0%B8%81%E0%B8%8A%E0%B9%88-%E0%B8%82%E0%B8%B1%E0%B8%9A%E0%B9%80%E0%B8%AA%E0%B8%A1%E0%B8%AB%E0%B8%B0-%E0%B8%8A%E0%B8%B8%E0%B9%88%E0%B8%A1%E0%B8%84%E0%B8%AD-%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%A3%E0%B8%94%E0%B8%B1%E0%B9%89%E0%B8%87%E0%B9%80%E0%B8%94%E0%B8%B4%E0%B8%A1-%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%A3%E0%B8%9C%E0%B8%AA%E0%B8%A1%E0%B8%A1%E0%B8%B0%E0%B8%82%E0%B8%B2%E0%B8%A1%E0%B8%9B%E0%B9%89%E0%B8%AD%E0%B8%A1-%E0%B8%82%E0%B8%99%E0%B8%B2%E0%B8%94-60-%E0%B8%A1%E0%B8%A5.-(1-5-%E0%B8%82%E0%B8%A7%E0%B8%94)-i.1418418965.42715461063
   ```
3. **ยาแก้แพ้ CPM (Chlorpheniramine 2 mg):**
   ```text
   https://shopee.co.th/ยกกล่อง-ยาแก้แพ้-ลดน้ำมูก-คลอร์เฟนิรามีน-Chlorpheniramine-2-mg-10-เม็ด-แผง--ยาแก้แพ้-CPM-i.40713787.27717511326
   ```

### กลุ่มผลิตภัณฑ์เสริมอาหาร (Food & Supplements)
1. **Blackmores Bio C 1000 mg:**
   ```text
   https://shopee.co.th/BLACKMORES-BIO-C-1000-MG.-DAILY-IMU-(Dietary-Supplement-Vitamin-C-and-Quercetin)-แบลคมอร์ส-ไบโอซี-ผลิตภัณฑ์เสริมอาหาร-i.388038998.54205722062
   ```
2. **VISTRA Zinc 15 mg:**
   ```text
   https://shopee.co.th/VISTRA-ZINC-15MG-(45-Tablets)-22.5กรัม-i.13037400.98663756
   ```

---

## 6. สรุปผลการประเมินประสิทธิภาพของระบบ (Performance Benchmark)

จากผลการทดลองในบทที่ 4 บนชุดข้อมูลตัวอย่างจริง 111 รายการ (534 ภาพ):

| มิติการประเมินผล | โมเดล / กระบวนการ | ผลการประเมิน | หมายเหตุ |
| :--- | :--- | :---: | :--- |
| **ความแม่นยำภาษาไทย (Thai OCR)** | Typhoon OCR (Vision-LLM) | **92.4%** | เหนือกว่า EasyOCR (61.2%) อย่างมีนัยสำคัญ |
| **การสกัดเลขทะเบียน/อย.** | Typhoon OCR | **89.6%** | สามารถเติมเต็มตัวเลขที่ขาดหายจากแสงสะท้อนได้ |
| **การระบุตำแหน่งบรรจุภัณฑ์** | Grounding DINO + SAM | **92.0%** | ตัดขอบฉลากและลด Noise จากภาพพื้นหลังได้ดีเยี่ยม |
| **ความแม่นยำการประเมินความเสี่ยง** | 4-Class Legal Rules Engine | **94.6%** | จำแนก MATCH, MISMATCH, SHOP_ONLY, NOT_FOUND |
| **เวลาประมวลผลเฉลี่ย (Latency)** | Complete End-to-End Scan | **7.80 วินาที** | ประหยัดเวลาเจ้าหน้าที่ตรวจสอบลงได้มากกว่า 85% |

---

## 7. โครงสร้างไฟล์ของโปรเจกต์ (Project Structure)

```
FDA_Detection/
├── FDA-Detection/
│   ├── backend/                      # ส่วนประมวลผลหลังบ้าน (FastAPI)
│   │   ├── app/
│   │   │   ├── api/                  # API Endpoints (Scan, History, Search)
│   │   │   ├── config/               # Settings, Seed URLs, Product Keywords
│   │   │   ├── core/                 # Database Connection, Logger, Selectors
│   │   │   ├── models/               # SQLAlchemy Models (ScanRecord)
│   │   │   ├── services/             # AI Detector (DINO+SAM), OCR Engine, Scraper
│   │   │   └── utils/                # Text Cleaner, ExplainEngine, Metrics
│   │   ├── Dockerfile                # Docker Image Build (Python 3.11 Bookworm)
│   │   └── requirements.txt          # Python Dependencies
│   │
│   ├── frontend/                     # ส่วนติดต่อผู้ใช้งาน (Next.js / React)
│   │   ├── src/
│   │   │   ├── components/           # AnalysisCard, DeepDiveModal, CredentialBox
│   │   │   ├── hooks/                # useScanner, useCrawler, useConfig
│   │   │   ├── pages/                # Index (Single Scan), Logs (Incident Queue)
│   │   │   └── styles/               # Tailwind CSS Styles
│   │   ├── Dockerfile                # Docker Image Build (Node.js Alpine)
│   │   └── package.json              # NPM Dependencies
│   │
│   ├── docker-compose.yml            # Multi-container Orchestration (Backend, Frontend, DB)
│   ├── start-docker.bat              # Script รัน Docker แบบอัตโนมัติบน Windows
│   └── .env.example                  # Template ไฟล์ Environment Variables
│
├── diagrams/                         # แผนภาพสถาปัตยกรรมและ Flowchart
├── draft_chapter_4_complete.md       # เนื้อหาร่างบทที่ 4 ผลการดำเนินงานและการทดลองฉบับเต็ม
├── .gitignore                        # Git Ignore Rules
└── README.md                         # เอกสารแนะนำและคู่มือการใช้งานระบบฉบับนี้
```

---

## 8. ข้อจำกัดและการใช้งาน (Disclaimer)

* ระบบนี้เป็นระบบปัญญาประดิษฐ์เพื่อการสนับสนุนการตัดสินใจเบื้องต้น (Decision Support System) เท่านั้น ผลการวิเคราะห์ระดับความเสี่ยงและการตรวจจับข้อกฎหมายมีวัตถุประสงค์เพื่อช่วยคัดกรองสินค้าต้องสงสัยให้แก่เจ้าหน้าที่และผู้บริโภค ไม่สามารถใช้เป็นข้อสรุปทางคดีความโดยปราศจากการตรวจสอบซ้ำโดยเจ้าหน้าที่ผู้มีอำนาจตามกฎหมาย

---

## ข้อมูลโครงงานและการติดต่อ (Project Information)

* **โครงงานปริญญานิพนธ์ระดับปริญญาตรี (Senior Project) :** สาขาวิชาวิทยาการคอมพิวเตอร์
* **ผู้พัฒนา :** นายธัชพงศ์ ดาน้อย (Thatchapong Danoi)
* **GitHub Repository :** [https://github.com/ThatchapongDa/FDA_Detection](https://github.com/ThatchapongDa/FDA_Detection)
