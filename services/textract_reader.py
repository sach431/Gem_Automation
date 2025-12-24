# services/textract_reader.py

import textract


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract raw text from PDF using textract
    (FOR TEXT / NON-TABLE PDFs ONLY)
    """
    try:
        text = textract.process(
            pdf_path,
            method="pdfminer"   # IMPORTANT: force stable parser
        )

        decoded = text.decode("utf-8", errors="ignore").strip()
        return decoded

    except Exception as e:
        print("Textract error:", e)
        return ""
