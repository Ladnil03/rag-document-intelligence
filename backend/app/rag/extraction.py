"""Plain-text extraction for PDF and DOCX files."""

import os

import docx
import pypdf


def extract_text_from_pdf(file_path: str) -> str:
    """Extract plain text from a PDF file page by page using pypdf."""
    reader = pypdf.PdfReader(file_path)
    extracted_pages = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            extracted_pages.append(page_text.strip())

    return "\n\n".join(extracted_pages)


def extract_text_from_docx(file_path: str) -> str:
    """Extract plain text from a DOCX file paragraph by paragraph using python-docx."""
    doc = docx.Document(file_path)
    paragraphs = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def extract_text(file_path: str, file_type: str) -> str:
    """Extract plain text from a document based on its file type ('pdf' or 'docx')."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at path: {file_path}")

    normalized_type = file_type.lower().strip(".")

    if normalized_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif normalized_type == "docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type for text extraction: {file_type}")
