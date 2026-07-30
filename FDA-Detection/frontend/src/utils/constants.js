export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const STATUS_CONFIG = {
    MATCH: { 
        label: 'ข้อมูลสอดคล้อง', 
        fact: 'พบหลักฐานบนสินค้าตรงกับข้อมูลที่ระบุในร้านค้า', 
        colorClass: 'text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-500/10 ring-green-500/30', 
        borderClass: 'border-green-200 dark:border-green-500/20 bg-green-50 dark:bg-green-500/5', 
        mainBg: 'bg-green-50 dark:bg-green-500/5 border-green-200 dark:border-green-500/20 text-green-700 dark:text-green-400' 
    },
    PRODUCT_ONLY: { 
        label: 'พบหลักฐานบนสินค้า', 
        fact: 'พบเลขทะเบียนบนสินค้าแต่ผู้ขายไม่ได้ระบุไว้ในรายละเอียด', 
        colorClass: 'text-indigo-700 dark:text-indigo-400 bg-indigo-100 dark:bg-indigo-500/10 ring-indigo-500/30', 
        borderClass: 'border-indigo-200 dark:border-indigo-500/20 bg-indigo-50 dark:bg-indigo-500/5', 
        mainBg: 'bg-indigo-50 dark:bg-indigo-500/5 border-indigo-200 dark:border-indigo-500/20 text-indigo-700 dark:text-indigo-400' 
    },
    SHOP_ONLY: { 
        label: 'ไม่พบหลักฐานบนสินค้า', 
        fact: 'ผู้ขายระบุเลขทะเบียนแต่ภาพสินค้าไม่ชัดเจนหรือไม่ระบุไว้', 
        colorClass: 'text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-500/10 ring-amber-500/30', 
        borderClass: 'border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/5', 
        mainBg: 'bg-amber-50 dark:bg-amber-500/5 border-amber-200 dark:border-amber-500/20 text-amber-700 dark:text-amber-400' 
    },
    MISMATCH: { 
        label: 'ข้อมูลขัดแย้ง', 
        fact: 'พบเลขทะเบียนบนสินค้าแต่ไม่ตรงกับตัวเลขที่ร้านคาระบุ', 
        colorClass: 'text-white bg-red-500 shadow-sm ring-red-500/30', 
        borderClass: 'border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/5 shadow-[0_0_15px_-3px_rgba(239,68,68,0.15)] ring-1 ring-red-100 dark:ring-red-900/30', 
        mainBg: 'bg-red-50 dark:bg-red-500/5 border-red-200 dark:border-red-500/30 text-red-700 dark:text-red-400' 
    },
    NOT_FOUND: { 
        label: 'ไม่พบข้อมูลทะเบียน', 
        fact: 'ไม่พบข้อมูลทะเบียนทั้งบนตัวสินค้าและหน้าร้านค้า', 
        colorClass: 'text-white bg-red-500 shadow-sm ring-red-500/30', 
        borderClass: 'border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/5 shadow-[0_0_15px_-3px_rgba(239,68,68,0.15)] ring-1 ring-red-100 dark:ring-red-900/30', 
        mainBg: 'bg-red-50 dark:bg-red-500/5 border-red-200 dark:border-red-500/30 text-red-700 dark:text-red-400' 
    },
    UNVERIFIED: { 
        label: 'ไม่สามารถประเมินได้', 
        fact: 'ไม่สามารถระบุสิ่งที่พบได้ (ภาพไม่ชัด/ถูกบล็อก)', 
        colorClass: 'text-slate-700 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 ring-slate-500/30', 
        borderClass: 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50', 
        mainBg: 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-400' 
    },
    NEED_REVIEW: { 
        label: 'รอการตรวจสอบ', 
        fact: 'ข้อมูลไม่เพียงพอที่จะระบุประเภทสินค้าได้แน่ชัด (AI เสนอแนะการตรวจสอบต่อ)', 
        colorClass: 'text-orange-700 dark:text-orange-400 bg-orange-100 dark:bg-orange-500/10 ring-orange-500/30', 
        borderClass: 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm', 
        mainBg: 'bg-orange-50 dark:bg-orange-500/5 border-orange-200 dark:border-orange-500/20 text-orange-700 dark:text-orange-400' 
    },
    SKIPPED: { 
        label: 'ไม่อยู่ในเกณฑ์ควบคุม', 
        fact: 'สินค้าทั่วไปที่เข้าข่ายไม่ต้องระบุเลขทะเบียน อย.', 
        colorClass: 'text-slate-500 bg-slate-100 dark:bg-slate-800 ring-slate-500/30', 
        borderClass: 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm', 
        mainBg: 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400' 
    },
    SCRAPE_FAILED: { 
        label: 'ดึงข้อมูลไม่สำเร็จ', 
        fact: 'ระบบดึงข้อมูลภาพจากต้นทางไม่ได้ (ติดระบบป้องกัน)', 
        colorClass: 'text-orange-700 dark:text-orange-400 bg-orange-100 dark:bg-orange-500/10', 
        borderClass: 'border-orange-200 dark:border-orange-500/20 bg-orange-50 dark:bg-orange-500/5', 
        mainBg: 'bg-orange-50 dark:bg-orange-500/5 border-orange-200 dark:border-orange-500/20 text-orange-700 dark:text-orange-400' 
    },
    INSUFFICIENT: { 
        label: 'ข้อมูลไม่สมบูรณ์', 
        fact: 'ไม่พบรูปภาพผลิตภัณฑ์เบื้องต้นสำหรับการประมวลผล', 
        colorClass: 'text-slate-500 bg-slate-100 dark:bg-slate-800', 
        borderClass: 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm', 
        mainBg: 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400' 
    },
    SCANNING: { 
        label: 'กำลังสแกนและวิเคราะห์', 
        fact: 'ระบบกำลังวิเคราะห์หลักฐานบนภาพถ่าย...', 
        colorClass: 'text-blue-700 dark:text-blue-400 bg-blue-100 dark:bg-blue-500/10 ring-blue-500/30 animate-pulse', 
        borderClass: 'border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/5 shadow-sm', 
        mainBg: 'bg-blue-50 dark:bg-blue-500/5 border-blue-200 dark:border-blue-500/20 text-blue-700 dark:text-blue-400' 
    },
    CANCELLED: { 
        label: 'หยุดการทำงาน', 
        fact: 'กระบวนการวิเคราะห์ภาพโดนขัดจังหวะหรือยกเลิก', 
        colorClass: 'text-slate-500 bg-slate-200 dark:bg-slate-800 ring-slate-500/30', 
        borderClass: 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 border-dashed', 
        mainBg: 'bg-slate-50 dark:bg-slate-900/50 border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400' 
    }
};

export const COMMON_CARD_CLASSES = "bg-white/60 dark:bg-slate-900/60 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 backdrop-blur-md shadow-sm transition-all";
