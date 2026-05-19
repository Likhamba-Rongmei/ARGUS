# backend/extraction/ocr.py
# Handles PDF and image ingestion + text extraction via Tesseract
# Converts any uploaded document into raw text for claim extraction

import os
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path


# ─── PDF TEXT EXTRACTION ───────────────────────────────────────────────────────

def extract_text_from_pdf_native(pdf_path: str) -> str:
    """
    Try to extract text directly from a native/digital PDF.
    Fast. Works when PDF has embedded text layer.
    Falls back to OCR if text is empty or too short.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"[OCR] pdfplumber failed: {e}")

    return text.strip()


def extract_text_from_pdf_ocr(pdf_path: str) -> str:
    """
    Convert each PDF page to image and run Tesseract OCR.
    Used for scanned PDFs with no embedded text layer.
    """
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image at 300 DPI for good OCR accuracy
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=mat)
            img_path = f"/tmp/argus_page_{page_num}.png"
            pix.save(img_path)

            # Run Tesseract on the page image
            img = Image.open(img_path)
            page_text = pytesseract.image_to_string(img, lang="eng")
            text += page_text + "\n"

            # Cleanup temp image
            os.remove(img_path)

        doc.close()
    except Exception as e:
        print(f"[OCR] PDF OCR failed: {e}")

    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Smart PDF extractor.
    Tries native text first, falls back to OCR if needed.
    Returns text + method used.
    """
    native_text = extract_text_from_pdf_native(pdf_path)

    # If native extraction gives reasonable text, use it
    if len(native_text) > 100:
        return {
            "text": native_text,
            "method": "native",
            "page_count": _get_page_count(pdf_path),
            "ocr_used": False
        }

    # Otherwise fall back to OCR
    print("[OCR] Native extraction insufficient, falling back to OCR...")
    ocr_text = extract_text_from_pdf_ocr(pdf_path)
    return {
        "text": ocr_text,
        "method": "ocr",
        "page_count": _get_page_count(pdf_path),
        "ocr_used": True
    }


# ─── IMAGE TEXT EXTRACTION ─────────────────────────────────────────────────────

def extract_text_from_image(image_path: str) -> dict:
    """
    Run Tesseract OCR on a standalone image file.
    Supports JPG, PNG, TIFF.
    """
    try:
        img = Image.open(image_path)

        # Convert to RGB if needed (handles RGBA, grayscale)
        if img.mode != "RGB":
            img = img.convert("RGB")

        text = pytesseract.image_to_string(img, lang="eng")

        # Get confidence score
        data = pytesseract.image_to_data(
            img,
            lang="eng",
            output_type=pytesseract.Output.DICT
        )
        confidences = [
            int(c) for c in data["conf"]
            if str(c).isdigit() and int(c) > 0
        ]
        avg_confidence = (
            sum(confidences) / len(confidences)
            if confidences else 0.0
        )

        return {
            "text": text.strip(),
            "method": "ocr",
            "ocr_used": True,
            "confidence": round(avg_confidence / 100, 2)  # normalize to 0-1
        }

    except Exception as e:
        print(f"[OCR] Image OCR failed: {e}")
        return {
            "text": "",
            "method": "ocr",
            "ocr_used": True,
            "confidence": 0.0
        }


# ─── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def extract_text(file_path: str) -> dict:
    """
    Universal entry point for text extraction.
    Detects file type and routes to correct extractor.

    Returns:
    {
        "text": str,
        "method": "native" | "ocr",
        "ocr_used": bool,
        "confidence": float (0.0 - 1.0, image only),
        "page_count": int (PDF only),
        "file_type": "pdf" | "image"
    }
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if ext == ".pdf":
        result = extract_text_from_pdf(file_path)
        result["file_type"] = "pdf"
        return result

    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"]:
        result = extract_text_from_image(file_path)
        result["file_type"] = "image"
        return result

    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _get_page_count(pdf_path: str) -> int:
    try:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except:
        return 0


def is_text_sufficient(text: str, min_chars: int = 100) -> bool:
    """
    Check if extracted text is long enough to be useful.
    Used to decide whether to flag low-confidence extraction.
    """
    return len(text.strip()) >= min_chars
