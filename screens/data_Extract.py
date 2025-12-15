# screens/data_Extract_ai_final.py
import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from pytesseract import Output
import re
import unicodedata
import pandas as pd
from io import BytesIO
import zipfile
import os

# ---------------- CONFIG ----------------
DEFAULT_TESSERACT = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if os.path.exists(DEFAULT_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT

# Final fixed columns (your required structure)
FINAL_COLUMNS = [
    "Seller Name","Buyer Name","Order ID","Product Name","GST","Quantity",
    "Email","Mobile","City","Category","Value","Date","Year"
]

# ----------------- UTILITIES -----------------
def clean_text(t: str) -> str:
    """Normalize, remove non-ascii/hindi/gibberish, collapse spaces."""
    if not t:
        return ""
    # Unicode normalize
    t = unicodedata.normalize("NFKD", t)
    # Remove Devanagari/Hindi range and other non-ascii (keep basic punctuation)
    t = re.sub(r'[\u0900-\u097F]+', ' ', t)
    # Replace non-printable or weird symbols with space
    t = re.sub(r'[^A-Za-z0-9@.\-/:,()%&\n ]+', ' ', t)
    # Collapse multiple spaces/newlines
    t = re.sub(r'[ \t]{2,}', ' ', t)
    t = re.sub(r'\n+', '\n', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def first_regex(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return ""
    # prefer group 1 if present
    try:
        return m.group(1).strip()
    except Exception:
        return m.group(0).strip()

def try_text_layer(pdf_bytes):
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as doc:
            parts = []
            for p in doc.pages:
                t = p.extract_text()
                if t:
                    parts.append(t)
            return "\n".join(parts)
    except Exception:
        return ""

def ocr_pdf_bytes(pdf_bytes, dpi=300):
    # convert pages to images and OCR them
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=dpi)
    except Exception:
        return ""
    texts = []
    for img in pages:
        try:
            t = pytesseract.image_to_string(img, lang='eng')
            texts.append(t)
        except Exception:
            pass
    return "\n".join(texts)

# ----------------- FIELD EXTRACTORS (tuned) -----------------
def extract_order_id(text):
    return first_regex(r"(GEMC-\d+)", text)

def extract_email(text):
    return first_regex(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,})", text)

def extract_mobile(text):
    return first_regex(r"\b([6-9]\d{9})\b", text)

def extract_value(text):
    # handle "Total Order Value in INR 9,920" or "INR 9,920"
    v = first_regex(r"Total\s*Order\s*Value.*?INR[:\s]*([0-9,]+)", text)
    if not v:
        v = first_regex(r"INR[:\s]*([0-9,]+)", text)
    if v:
        return v.replace(",", "")
    return ""

def extract_date(text):
    d = first_regex(r"(\d{1,2}-[A-Za-z]{3}-\d{4})", text)
    if not d:
        d = first_regex(r"(\d{4}-\d{2}-\d{2})", text)
    return d

def extract_year_from_date(date_str):
    if not date_str:
        y = first_regex(r"\b(20\d{2})\b", text_provide_for_year if 'text_provide_for_year' in globals() else "")
        return y
    m = re.search(r"(20\d{2})", date_str)
    return m.group(1) if m else ""

def extract_quantity(text):
    # look for "Ordered Quantity 400" or "Quantity 400" nearby
    q = first_regex(r"(?:Ordered\s*Quantity|Quantity|Qty)[:\s\-]*([0-9]{1,6})", text)
    if not q:
        # fallback: number followed by "Test" or "Tests"
        q = first_regex(r"([0-9]{1,6})\s+(?:Test|Tests|Nos)\b", text)
    return q

def extract_gst(text):
    # maybe present as percentage or GSTIN; keep both possibilities
    g = first_regex(r"\bGST[:\s\-]*([0-9\.%]+)", text)
    if not g:
        # sometimes they write IGST/CGST numeric; capture if present
        g = first_regex(r"(?:GSTIN|GST No\.?)[:\s\-]*([A-Za-z0-9]+)", text)
    return g

def extract_product(text):
    # try common headers
    p = first_regex(r"(?:Product\s*Name|Item\s*Description|Product\s*Details)[:\s\-]*([A-Za-z0-9 ,\-/\(\)]+)", text)
    if p:
        return p
    # fallback: look for "Product Name :" like patterns or "Product Name ::"
    p = first_regex(r"Product(?:\s*Name)?\s*[:\-]{1,2}\s*([A-Za-z0-9 ,\-/\(\)]+)", text)
    if p:
        return p
    # last fallback: try to find line with 'Test' and 'Kit'
    m = re.search(r"([A-Za-z0-9 ]+Test[A-Za-z0-9 ]+Kit)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""

def extract_seller(text):
    s = first_regex(r"(?:Seller|Company Name|Seller Details)[:\s\-]*([A-Za-z0-9 &,\.\-/]{3,80})", text)
    if s:
        return s
    # fallback: first uppercase block before 'Buyer' or 'Contact'
    m = re.search(r"([A-Z][A-Z0-9 &,\-]{4,80})\s+(?:Buyer|Contact|Phone|Email)", text)
    if m:
        return m.group(1)
    return ""

def extract_buyer(text):
    b = first_regex(r"(?:Buyer\s*Details|Buyer\s*Name|Buyer)[:\s\-]*([A-Za-z0-9 &,\.\-/]{3,80})", text)
    if b:
        return b
    # fallback: find 'Buyer' nearby
    m = re.search(r"Buyer[:\s\-]*([A-Z0-9\w ,&\-/]{3,80})", text, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""

def extract_city(text):
    # check common words (Lucknow etc.) else return blank
    common = ["Lucknow","Kanpur","Varanasi","Delhi","Sultanpur","Muzaffarnagar","Bhopal","Mumbai","Aligarh"]
    for c in common:
        if c.lower() in text.lower():
            return c
    # fallback try "City:" pattern
    c = first_regex(r"(?:City|Place|Location)[:\s\-]*([A-Za-z ]{2,40})", text)
    return c

def extract_category(text):
    c = first_regex(r"(?:Category|Brand)[:\s\-]*([A-Za-z0-9 &\-]{2,40})", text)
    return c

# ----------------- MAIN SINGLE PDF PROCESS -----------------
def process_single_pdf_bytes(pdf_bytes):
    # try text-layer first
    text = try_text_layer(pdf_bytes)
    used_ocr = False
    if not text or len(text.strip()) < 50:
        # fallback to OCR
        used_ocr = True
        text = ocr_pdf_bytes(pdf_bytes, dpi=300)

    text = clean_text(text)

    # keep a global sample for year fallback
    global text_provide_for_year
    text_provide_for_year = text

    row = {
        "Seller Name": extract_seller(text),
        "Buyer Name": extract_buyer(text),
        "Order ID": extract_order_id(text),
        "Product Name": extract_product(text),
        "GST": extract_gst(text),
        "Quantity": extract_quantity(text),
        "Email": extract_email(text),
        "Mobile": extract_mobile(text),
        "City": extract_city(text),
        "Category": extract_category(text),
        "Value": extract_value(text),
        "Date": extract_date(text),
        "Year": extract_year_from_date(extract_date(text))
    }

    # final cleaning per field
    for k,v in list(row.items()):
        if isinstance(v, str):
            row[k] = clean_text(v)
    return row, used_ocr, text[:1500]

# ----------------- STREAMLIT UI -----------------
def app():
    st.header("🛠 Final GeM PDF → Clean Excel Extractor (Fixed Table)")

    st.markdown("Upload one or multiple GeM PDFs. Output will always follow the fixed 13-column structure. Edit the combined table if needed before download.")

    uploaded = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True)

    if not uploaded:
        st.info("Please upload PDF files to extract.")
        return

    if st.button("Extract & Build Clean Table"):
        rows = []
        zip_buf = BytesIO()
        zf = zipfile.ZipFile(zip_buf, mode="w")

        for f in uploaded:
            st.write("Processing:", f.name)
            try:
                pdf_bytes = f.read()
                row, used_ocr, sample = process_single_pdf_bytes(pdf_bytes)
                row["Source File"] = f.name  # keep for trace
                rows.append(row)

                # show per-file short table row (single-row)
                st.markdown(f"**File:** {f.name}")
                display_df = pd.DataFrame([row])[FINAL_COLUMNS]
                st.dataframe(display_df, use_container_width=True)

                # also write per-file excel of the fields
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                    pd.DataFrame([row]).to_excel(writer, index=False, sheet_name="Fields")
                zf.writestr(f"{f.name.replace('.pdf','')}_fields.xlsx", buf.getvalue())

                st.success("Done: " + f.name)

            except Exception as e:
                st.error(f"Error processing {f.name}: {e}")

        # Combined table
        if rows:
            combined = pd.DataFrame(rows)
            # ensure columns order and presence
            for c in FINAL_COLUMNS:
                if c not in combined.columns:
                    combined[c] = ""
            combined = combined[FINAL_COLUMNS]

            st.subheader("🔎 Combined Extracted Data — verify & edit")
            try:
                edited = st.data_editor(combined, num_rows="dynamic")
            except Exception:
                edited = combined
                st.dataframe(edited, use_container_width=True)

            # write combined excel and add to zip
            out_buf = BytesIO()
            with pd.ExcelWriter(out_buf, engine="xlsxwriter") as writer:
                edited.to_excel(writer, index=False, sheet_name="All_Files")
            zf.writestr("All_Files_Combined.xlsx", out_buf.getvalue())

            zf.close()

            st.download_button("📥 Download ALL extracted files as ZIP", data=zip_buf.getvalue(), file_name="gem_extracted_clean.zip", mime="application/zip")
        else:
            st.warning("No rows extracted.")

# allow running this screen directly for debug
if __name__ == "__main__":
    app()
