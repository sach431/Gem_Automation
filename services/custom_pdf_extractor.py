import re
import pdfplumber

# =================================================
# PDF → RAW TEXT
# =================================================
def extract_pdf_to_text(pdf_file) -> str:
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


# =================================================
# CLEAN TEXT
# =================================================
def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    # remove font noise
    text = re.sub(r"\(cid:\d+\)", " ", text)

    # remove hindi characters
    text = re.sub(r"[\u0900-\u097F]+", " ", text)

    stop_phrases = [
        "Terms and Conditions",
        "SPECIAL TERMS AND CONDITIONS",
        "General Terms and Conditions",
        "This is system generated file",
        "No signature is required",
        "Print out of this document",
        "Note:"
    ]

    for phrase in stop_phrases:
        text = re.sub(
            phrase + r".*",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

    text = re.sub(r"[|•■♦●]", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\n\s*\n", "\n", text)

    return text.strip()


# =================================================
# NORMALIZE TEXT
# =================================================
def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


# =================================================
# BUYER SECTION ONLY
# =================================================
def extract_buyer_section(text: str) -> str:
    m = re.search(
        r"Buyer Details(.*?)(Seller Details|Consignee Details|Product Details)",
        text,
        re.S | re.I
    )
    return m.group(1) if m else ""


# =================================================
# FIND VALUE BELOW LABEL (KEY FIX)
# =================================================
def find_value_below_label(text: str, label: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        if line.lower() == label.lower():
            if i + 1 < len(lines):
                return lines[i + 1]
    return ""


# =================================================
# STRUCTURED EXTRACTION (FINAL)
# =================================================
def extract_structured_fields(clean_text: str) -> dict:
    text = normalize_text(clean_text)
    buyer = extract_buyer_section(text)

    contract_no = ""
    m = re.search(r"GEM-\d{6,}", text)
    if m:
        contract_no = m.group(0)

    generated_date = ""
    d = re.search(r"\d{2}-[A-Za-z]{3}-\d{4}", text)
    if d:
        generated_date = d.group(0)

    return {
        "Contract No": contract_no,
        "Generated Date": generated_date,

        "Organisation Name": find_value_below_label(buyer, "Organisation Name"),
        "Ministry": find_value_below_label(buyer, "Ministry"),
        "Department": find_value_below_label(buyer, "Department"),
        "Buyer Designation": find_value_below_label(buyer, "Designation"),
        "Buyer Email": find_value_below_label(buyer, "Email"),
    }


# =================================================
# ONE-CALL HELPER (IMPORT THIS)
# =================================================
def extract_pdf_structured_data(pdf_file) -> dict:
    raw_text = extract_pdf_to_text(pdf_file)
    cleaned_text = clean_extracted_text(raw_text)
    return extract_structured_fields(cleaned_text)
