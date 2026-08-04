import fitz  # PyMuPDF


def extract_report_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()
    return text


def explain_report(text: str) -> str:
    # Simple rule-based explanation (safe and non-diagnostic)
    text_lower = text.lower()

    findings = []

    if "hemoglobin" in text_lower:
        findings.append(
            "The report includes hemoglobin, which is related to the blood's oxygen-carrying capacity."
        )

    if "glucose" in text_lower or "sugar" in text_lower:
        findings.append(
            "The report includes blood glucose values, which are used to assess blood sugar levels."
        )

    if "cholesterol" in text_lower:
        findings.append(
            "The report includes cholesterol measurements related to heart health."
        )

    if not findings:
        findings.append(
            "The report was read successfully, but a detailed medical interpretation should be provided by a qualified healthcare professional."
        )

    return (
        "Simple explanation:\\n- "
        + "\\n- ".join(findings)
        + "\\n\\nThis is not a diagnosis. Please consult your doctor for clinical interpretation."
    )