from pathlib import Path
from typing import BinaryIO

from langchain_core.documents import Document
from pypdf import PdfReader

def extract_pdf(file: BinaryIO) -> list[Document]:
    """Extract one LangChain document per PDF page, preserving citations."""
    reader = PdfReader(file)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(Document(page_content=text, metadata={"page": number, "source": getattr(file, "name", "upload.pdf")}))
    if not pages:
        raise ValueError("The PDF did not contain extractable text. OCR is not enabled in this prototype.")
    return pages

def extract_markdown(path: Path) -> list[Document]:
    """Development-only loader for the included synthetic corpus."""
    text = path.read_text(encoding="utf-8")
    sections = [part.strip() for part in text.split("\n## ") if part.strip()]
    return [Document(page_content=part, metadata={"page": i, "source": path.name}) for i, part in enumerate(sections, start=1)]
