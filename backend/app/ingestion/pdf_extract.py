from __future__ import annotations

import io
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPDF:
    pages: list[str]
    tables: list[tuple[int, list[list[str | None]]]]
    ocr_skipped_pages: list[int]
    ocr_error: str | None = None
    ocr_pages: list[int] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(f"[PAGE {number}]\n{text}" for number, text in enumerate(self.pages, 1))


def extract_pdf(source: str | Path | bytes, min_text_chars: int = 40) -> ExtractedPDF:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("PDF extraction requires pdfplumber; install backend/requirements.txt") from exc

    document = io.BytesIO(source) if isinstance(source, bytes) else source
    pages: list[str] = []
    tables: list[tuple[int, list[list[str | None]]]] = []
    skipped: list[int] = []
    ocr_pages: list[int] = []
    ocr_error: str | None = None

    with pdfplumber.open(document) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = (page.extract_text() or "").strip()
            tables.extend((page_number, table) for table in (page.extract_tables() or []))
            if len(text) < min_text_chars:
                if shutil.which("tesseract") is None:
                    skipped.append(page_number)
                    ocr_error = "Tesseract is unavailable; OCR skipped. Install Tesseract with eng+hin language data to enable OCR."
                    logger.warning("%s (page %d)", ocr_error, page_number)
                else:
                    try:
                        import pytesseract

                        text = pytesseract.image_to_string(page.to_image(resolution=250).original, lang="eng+hin").strip()
                        if text:
                            ocr_pages.append(page_number)
                    except Exception as exc:
                        skipped.append(page_number)
                        ocr_error = f"OCR failed and was skipped: {exc}"
                        logger.warning("%s (page %d)", ocr_error, page_number)
            pages.append(text)

    return ExtractedPDF(pages=pages, tables=tables, ocr_skipped_pages=skipped, ocr_error=ocr_error, ocr_pages=ocr_pages)