import os
try:
    import pytesseract
    from PIL import Image
    TESSERACT_OK = True
except Exception:
    TESSERACT_OK = False

def ocr_from_path(fp):
    """Return text from an image file. If pytesseract not installed, return empty string."""
    if not TESSERACT_OK:
        return ""
    try:
        text = pytesseract.image_to_string(Image.open(fp), lang='eng')
        return text or ""
    except Exception as e:
        print("OCR error:", e)
        return ""
