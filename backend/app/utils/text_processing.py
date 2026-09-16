import re
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """Removes irregular whitespace and normalizes text."""
    if not text:
        return ""
    # Normalize newlines
    text = re.sub(r"\r\n|\r", "\n", text)
    # Remove repeated excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def truncate_text(text: str, max_chars: int = 15000) -> str:
    """Truncates text safely to avoid exceeding LLM context windows."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[Content truncated for analysis]..."

def extract_sentences(text: str) -> List[str]:
    """Splits text into meaningful sentences."""
    clean = clean_text(text)
    sentences = re.split(r"(?<=[.?!])\s+", clean)
    return [s.strip() for s in sentences if len(s.strip()) > 15]

def extract_keywords_and_headings(text: str) -> List[str]:
    """Finds candidate topic headings or capitalized phrases."""
    lines = text.split("\n")
    candidates = []
    for line in lines:
        stripped = line.strip()
        # Headings often start with # or are short title-like lines
        if stripped.startswith("#"):
            candidates.append(re.sub(r"^#+\s*", "", stripped))
        elif 5 <= len(stripped) <= 60 and not stripped.endswith((".", ";", ":")):
            candidates.append(stripped)
    return list(dict.fromkeys(candidates))

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts raw selectable text from a PDF document byte stream."""
    import io
    import pypdf

    if not pdf_bytes:
        return ""

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages: List[str] = []

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                extracted_pages.append(text.strip())

        full_text = "\n\n".join(extracted_pages)
        return clean_text(full_text)
    except Exception as exc:
        raise ValueError(f"Could not read PDF document: {str(exc)}")
