import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ExplainEngine:
    """
    [PHASE 3] Explainability & Trust Engine.
    Handles legal mapping and reason generation.
    """

    @staticmethod
    def get_legal_violation(category: str, missing_fields: List[str]) -> List[Dict[str, str]]:
        """
        Maps missing fields to specific Thai Laws, Sections, and Penalties.
        """
        # Normalize category to match mapping keys
        cat = category.upper()
        if "DRUG" in cat or "ยา" in cat: cat = "DRUG"
        elif "FOOD" in cat or "อาหาร" in cat: cat = "FOOD"
        elif "COSMETIC" in cat or "เครื่องสำอาง" in cat: cat = "COSMETIC"
        elif "SUPPLEMENT" in cat or "เสริม" in cat: cat = "SUPPLEMENT"
        else: cat = "FOOD" # Default fallback for licensed categories

        law_mapping = {
            "DRUG": {
                "fda_number": {
                    "law": "พระราชบัญญัติยา พ.ศ. 2510", 
                    "section": "มาตรา 72(4)", 
                    "details": "ขายยาที่มิได้ขึ้นทะเบียนตำรับยา",
                    "penalty": "จำคุกไม่เกิน 3 ปี หรือปรับไม่เกิน 5,000 บาท หรือทั้งจำทั้งปรับ",
                    "full_ref": "พระราชบัญญัติยา พ.ศ. 2510 มาตรา 72(4) ห้ามมิให้ผู้ใดผลิต ขาย หรือนำหรือสั่งเข้ามาในราชอาณาจักรซึ่งยาที่มิได้ขึ้นทะเบียนตำรับยา"
                },
            },
            "FOOD": {
                "fda_number": {
                    "law": "พระราชบัญญัติอาหาร พ.ศ. 2522", 
                    "section": "มาตรา 25(1)", 
                    "details": "อาหารไม่บริสุทธิ์/ไม่ได้มาตรฐาน (ไม่มีเลขสารบบอาหาร)",
                    "penalty": "จำคุกไม่เกิน 2 ปี หรือปรับไม่เกิน 20,000 บาท หรือทั้งจำทั้งปรับ",
                    "full_ref": "พระราชบัญญัติอาหาร พ.ศ. 2522 มาตรา 25(1) ห้ามมิให้ผู้ใดผลิต หรือจำหน่ายอาหารไม่บริสุทธิ์"
                },
            },
            "COSMETIC": {
                "fda_number": {
                    "law": "พระราชบัญญัติเครื่องสำอาง พ.ศ. 2558", 
                    "section": "มาตรา 14", 
                    "details": "เครื่องสำอางที่ไม่ได้จดแจ้ง",
                    "penalty": "จำคุกไม่เกิน 6 เดือน หรือปรับไม่เกิน 50,000 บาท หรือทั้งจำทั้งปรับ",
                    "full_ref": "พระราชบัญญัติเครื่องสำอาง พ.ศ. 2558 มาตรา 14 กำหนดให้การผลิตหรือนำเข้าเครื่องสำอางต้องจดแจ้งต่อผู้รับจดแจ้ง"
                },
            },
            "SUPPLEMENT": {
                "fda_number": {
                    "law": "พระราชบัญญัติอาหาร พ.ศ. 2522", 
                    "section": "มาตรา 25(1)", 
                    "details": "อาหารไม่บริสุทธิ์ (ไม่มีเลขสารบบอาหาร)",
                    "penalty": "จำคุกไม่เกิน 2 ปี หรือปรับไม่เกิน 20,000 บาท หรือทั้งจำทั้งปรับ",
                    "full_ref": "มาตรา 25(1) ห้ามมิให้ผลิตหรือจำหน่ายอาหารที่ไม่มีการจดทะเบียนหรือแจ้งรายละเอียดที่ถูกต้อง"
                },
            }
        }
        
        results = []
        for field in missing_fields:
            if cat in law_mapping and field in law_mapping[cat]:
                results.append(law_mapping[cat][field])
        
        return results

    @staticmethod
    def generate_legal_snippet(category: str, risk_level: str) -> str:
        """
        Generates a concise legal snippet for summary display.
        """
        if risk_level in ["MATCH", "SKIPPED", "PRODUCT_ONLY"]:
            return ""
            
        violations = ExplainEngine.get_legal_violation(category, ["fda_number"])
        if violations:
            v = violations[0]
            prefix = "⚠ ผิดกฎหมาย"
            return f"{prefix}: {v['details']} ตาม {v['law']} {v['section']}"
        return ""
