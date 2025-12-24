# services/custom_pdf_extractor.py

"""
Custom PDF extractor
--------------------
This module acts as a wrapper for hybrid PDF extraction.
It automatically handles:
- Normal text PDFs
- CID / Hindi / font-encoded PDFs using OCR
"""

from services.hybrid_pdf_extractor import extract_pdf


def extract_pdf_to_text(pdf_file):
    """
    Extract clean text from uploaded PDF file (Streamlit file object)

    Args:
        pdf_file: Uploaded PDF file from Streamlit (st.file_uploader)

    Returns:
        str: Clean extracted text
    """
    if pdf_file is None:
        return ""

    return extract_pdf(pdf_file)
