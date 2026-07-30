import re
import html

def clean_text(text: str) -> str:
    """
    Cleans and normalizes text by:
    - Decoding HTML entities.
    - Removing excessive whitespace.
    - Removing non-printable characters.
    """
    if not text:
        return ""
    
    # Decode HTML entities (e.g., &amp; -> &)
    text = html.unescape(text)
    
    # Remove zero-width spaces and other invisible characters
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()

def normalize_fda(fda_number: str) -> str:
    """
    Normalizes an FDA number to a standard format (digits and uppercase letters only).
    """
    if not fda_number:
        return ""
    return re.sub(r'[^0-9A-Za-z/]', '', fda_number).upper()

def calculate_thai_density(text: str) -> float:
    """
    Calculates the percentage of Thai characters in the given text.
    """
    if not text:
        return 0.0
    # Clean whitespace first to get a more accurate density of actual text
    clean_txt = re.sub(r'\s+', '', text)
    if not clean_txt:
        return 0.0
        
    thai_chars = re.findall(r'[\u0E00-\u0E7F]', clean_txt)
    return (len(thai_chars) / len(clean_txt)) * 100.0

def is_valid_fda(fda_number: str, product_type: str = "FOOD") -> bool:
    """
    Checks if an FDA number looks valid.
    - Filters out 'dummy' numbers like 00000... or 11111...
    - For Food (13 digits), checks length and basic structure.
    - For Drug, checks for minimum digit/char diversity.
    """
    clean = re.sub(r'[^0-9A-Z]', '', fda_number)
    
    # 1. Basic diversity check (avoid 0000000000000)
    if len(set(clean)) < 3:
        return False
        
    if product_type == "FOOD":
        if len(clean) != 13:
            return False
        # Province code check (10-96)
        province = int(clean[:2])
        if not (10 <= province <= 96):
            return False
        return True
        
    elif product_type == "DRUG":
        # Drug numbers like 1A 844/39 or G 456/59
        has_letter = any(c.isalpha() for c in fda_number)
        has_digit = any(c.isdigit() for c in fda_number)
        
        if not (has_letter and has_digit and len(clean) >= 5):
            return False
            
        # Extract potential year if it ends with /XX or /XXXX
        parts = fda_number.split('/')
        if len(parts) >= 2:
            year_part = re.sub(r'[^0-9]', '', parts[-1])
            if len(year_part) in [2, 4]:
                year_int = int(year_part)
                # If 2 digits, expect Thai year between 00-99 (usually 25xx so 20-70 range is common)
                if len(year_part) == 2 and not (10 <= year_int <= 99):
                    return False
                # If 4 digits, expect 25xx
                if len(year_part) == 4 and not (2500 <= year_int <= 2600):
                    return False
        
        # Anti-pattern: Ignore repetitive patterns that often come from hallucinations
        digits_only = re.sub(r'[^0-9]', '', fda_number)
        if len(digits_only) >= 3:
            # e.g., '111', '0000', '1234'
            if len(set(digits_only)) == 1: # All same digits
                return False
            if digits_only in "0123456789" or digits_only in "9876543210": # Sequential digits
                if len(digits_only) >= 4:
                    return False

    return True
