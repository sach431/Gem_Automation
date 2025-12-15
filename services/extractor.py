import pandas as pd
import re
from pypdf import PdfReader

# Remove Hindi + unwanted symbols
def clean_text(text):
    # Remove Hindi characters
    text = re.sub(r'[\u0900-\u097F]+', ' ', text)
    # Remove bullets, dashes
    text = re.sub(r'[•●–—\-]+', ' ', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_pdf_to_table(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += "\n" + t

    text = clean_text(text)

    # --- PREDEFINED PATTERNS FOR GEM CONTRACT PDFs ---
    name_pattern = r"Name[:\s]+([A-Za-z ]{3,50})"
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    mobile_pattern = r"\b[6-9]\d{9}\b"
    state_pattern = r"\b(Jharkhand|UP|Uttar Pradesh|Delhi|Bihar|Assam|Punjab|Jammu|Kashmir)\b"
    brand_pattern = r"Brand[:\s]+([A-Za-z0-9 ]{2,40})"

    name = ""
    email = ""
    mobile = ""
    state = ""
    brand = ""

    # Extract Name
    match = re.search(name_pattern, text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()

    # Extract Email
    match = re.search(email_pattern, text)
    if match:
        email = match.group(0)

    # Extract Mobile
    match = re.search(mobile_pattern, text)
    if match:
        mobile = match.group(0)

    # Extract State
    match = re.search(state_pattern, text, re.IGNORECASE)
    if match:
        state = match.group(0)

    # Extract Brand
    match = re.search(brand_pattern, text, re.IGNORECASE)
    if match:
        brand = match.group(1).strip()

    # Create clean table
    df = pd.DataFrame([{
        "Name": name,
        "Email": email,
        "Mobile": mobile,
        "State": state,
        "Brand": brand
    }])

    return df
