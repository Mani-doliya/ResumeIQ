import re
from pathlib import Path
from typing import Tuple, Optional
import logging

from app.core.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)


def validate_file(filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
    if not filename:
        return False, "No filename provided"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB"
    if file_size == 0:
        return False, "Empty file uploaded"
    return True, None


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r'[^\w\s\-\.]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:200]


def extract_text_from_pdf(file_path: Path) -> str:
    try:
        import pymupdf
        doc = pymupdf.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text("text"))
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_txt(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"TXT extraction failed: {e}")
        raise ValueError(f"Failed to read text file: {str(e)}")


def extract_text(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs]).strip()
        except ImportError:
            raise ValueError("python-docx not installed for DOCX support")
        except Exception as e:
            raise ValueError(f"Failed to extract DOCX: {str(e)}")
    else:
        raise ValueError(f"Unsupported extension: {ext}")