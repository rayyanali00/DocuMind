"""OCR extraction for images and scanned PDFs (FR-020..FR-026)."""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.config import get_settings

settings = get_settings()


def ocr_image(path: Path) -> str:
    """Run Tesseract OCR on a single image file."""
    import pytesseract
    from PIL import Image

    with Image.open(path) as img:
        return pytesseract.image_to_string(img, lang=settings.tesseract_lang).strip()


def ocr_pdf(path: Path, dpi: int = 200) -> str:
    """Rasterize a PDF and OCR each page. Used for scanned PDFs."""
    import pytesseract
    from pdf2image import convert_from_path

    pages = convert_from_path(str(path), dpi=dpi)
    parts: list[str] = []
    for i, page_img in enumerate(pages, start=1):
        try:
            text = pytesseract.image_to_string(page_img, lang=settings.tesseract_lang)
            if text.strip():
                parts.append(text.strip())
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"OCR failed on page {i} of {path}: {exc}")
    return "\n\n".join(parts).strip()


def pdf_appears_scanned(extracted_text: str, min_chars: int = 40) -> bool:
    """Heuristic: a PDF with almost no extractable text is likely scanned."""
    return len((extracted_text or "").strip()) < min_chars
