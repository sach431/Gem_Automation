import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re
import tempfile
import os

def has_bad_encoding(text):
    return "(cid:" in text or re.search(r'[\u0900-\u097F]', text)

def clean_text(text):
    text = re.sub(r'\(cid:\d+\)', ' ', text)
    text = re.sub(r'[\u0900-\u097F]+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_pdf(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        pdf_path = tmp.name

    text = ""

    # Try pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        pass

    # OCR fallback
    if not text or has_bad_encoding(text):
        images = convert_from_path(pdf_path, dpi=300)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img, lang="eng")

    os.remove(pdf_path)
    return clean_text(text)
