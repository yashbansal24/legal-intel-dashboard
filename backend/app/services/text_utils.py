from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
import os

def extract_text_from_pdf(path: str) -> str:
    return pdf_extract_text(path) or ""

def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_file(path: str, content_type: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if content_type.endswith("pdf") or ext == ".pdf":
        return extract_text_from_pdf(path)
    if "word" in content_type or ext in (".docx",):
        return extract_text_from_docx(path)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""
