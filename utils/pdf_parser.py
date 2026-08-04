import os
from typing import Optional

def extract_pdf_text(pdf_path: str) -> str:
    """
    Extracts text content from a given PDF file path.
    Uses pypdf if available, otherwise returns fallback text.
    """
    if not os.path.exists(pdf_path):
        return f"[Error] PDF file not found at: {pdf_path}"

    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        # Fallback text extraction if PDF library fails or PDF is plain text sample
        try:
            with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return f"[Error extracting PDF text: {str(e)}]"

def create_sample_pdf_if_missing(pdf_path: str, content: str):
    """
    Creates a sample PDF or text report file if it does not exist.
    """
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    if os.path.exists(pdf_path):
        return

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(pdf_path, pagesize=letter)
        y = 750
        for line in content.split("\n"):
            c.drawString(50, y, line)
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
        c.save()
    except Exception:
        # Fallback: write text directly if reportlab is not installed
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(content)
