import os
import re
import pandas as pd
from pypdf import PdfReader

PDF_DIR = "data/pdf_files"
OUT_FILE = "data/extracted_excels/final_output.xlsx"


# ---------------------------------------------------------
# CLEAN TEXT FUNCTION – Removes Hindi + symbols safely
# ---------------------------------------------------------
def clean_text(text):
    if not text:
        return ""

    # Remove only Hindi (Devanagari range)
    text = re.sub(r"[\u0900-\u097F]+", " ", text)

    # Remove junk symbols
    text = re.sub(r"[•►★–…□■▪◘○●♦▼▲▽◾◽│┃]", " ", text)

    # Replace pipe/separators
    text = text.replace("|", " ").replace("¦", " ")

    # Remove control characters
    text = re.sub(r"[\x00-\x1F\x7F]+", " ", text)

    # Normalize spacing
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ---------------------------------------------------------
# Regex helper
# ---------------------------------------------------------
def find(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if m:
        return clean_text(m.group(1))
    return ""


# ---------------------------------------------------------
# EXTRACT FIELDS FROM ONE PDF
# ---------------------------------------------------------
def extract_fields(pdf_path, debug=False):

    reader = PdfReader(pdf_path)
    raw_text = ""

    for page in reader.pages:
        t = page.extract_text()
        if t:
            raw_text += t + "\n"

    if debug:
        print("\n=== RAW TEXT ===")
        print(raw_text[:1000])
        print("\n=== END RAW TEXT ===\n")

    text = clean_text(raw_text)

    if debug:
        print("\n=== CLEANED TEXT ===")
        print(text[:1000])
        print("\n=== END CLEANED TEXT ===\n")

    data = {}

    # Seller Name
    data["Name"] = find(r"Company Name\s*:\s*(.*?)(?:Email|Contact|$)", text)

    # Email (first valid)
    data["Email"] = find(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text)

    # Mobile (10-digit)
    data["Mobile"] = find(r"Contact\s*No\.?\s*[:\-]?\s*(\d{10})", text)

    # State
    data["State"] = find(r"Address\s*:.*?,\s*([A-Za-z ]+)-\d+", text)

    # Brand (stop before brand type)
    data["Brand"] = find(r"Brand\s*:\s*(.*?)(?:Brand Type|Model|HSN|Category|$)", text)

    # Buyer Name
    data["Buyer Name"] = find(r"Organisation Name\s*:\s*(.*?)(?:Email|Contact|Address|$)", text)

    # Seller Name same
    data["Seller Name"] = data["Name"]

    # Order Number
    data["Order Number"] = find(r"(GEMC-[0-9]+)", text)

    # Order Date
    data["Order Date"] = find(r"Generated Date\s*[:\-]?\s*(\d{2}-[A-Za-z]{3}-\d{4})", text)

    # Price
    data["Price"] = find(r"Total Order Value.*?([0-9,]+\.\d+|[0-9,]+)", text)

    # Quantity (25 Test, 2,000 Test)
    data["Quantity"] = find(r"(\d[\d,]*\s*(?:Test|Nos|Units|Kit))", text)

    # Value = Price
    data["Value"] = data["Price"]

    # ⭐ FIXED CATEGORY REGEX
    data["Category"] = find(
        r"Category Name\s*(?:\:)?\s*([A-Za-z0-9\s]*(?:Malaria|Dengue|Typhoid|CHIKUNGUNYA)[A-Za-z0-9\s]*)",
        text
    )

    if debug:
        print("\n=== EXTRACTED DATA ===")
        for k, v in data.items():
            print(f"{k}: {v}")
        print("=== END EXTRACTED DATA ===\n")

    return data


# ---------------------------------------------------------
# PROCESS ALL PDFs
# ---------------------------------------------------------
def process_all(debug=False):
    rows = []

    for file in os.listdir(PDF_DIR):
        if file.lower().endswith(".pdf"):
            print("Processing:", file)
            pdf_path = os.path.join(PDF_DIR, file)

            try:
                row = extract_fields(pdf_path, debug=debug)
                rows.append(row)
            except Exception as e:
                print("❌ Error:", e)

    df = pd.DataFrame(rows)

    df = df.fillna("")

    df = df.applymap(lambda x: clean_text(x) if isinstance(x, str) else x)

    df.to_excel(OUT_FILE, index=False)

    print("\n✅ EXTRACTION DONE!")
    print("Saved:", OUT_FILE)
    print(df.to_string(index=False))


if __name__ == "__main__":
    process_all(debug=True)
