import re
import pdfplumber
import pandas as pd
import hashlib


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
# CLEAN TEXT - Remove noise and non-ASCII
# =================================================
def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    # Remove font noise like (cid:XX)
    text = re.sub(r"\(cid:\d+\)", " ", text)

    # Remove Hindi/Devanagari characters
    text = re.sub(r"[\u0900-\u097F]+", " ", text)

    # Remove other non-ASCII characters
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    # Stop phrases - remove everything after these
    stop_phrases = [
        "Terms and Conditions",
        "SPECIAL TERMS AND CONDITIONS",
        "General Terms and Conditions",
        "This is system generated file",
        "No signature is required",
        "Print out of this document",
    ]

    for phrase in stop_phrases:
        text = re.sub(
            phrase + r".*",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

    # Remove special characters but keep necessary punctuation
    text = re.sub(r"[|#]+", " ", text)

    # Collapse multiple spaces and newlines
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()


# =================================================
# FIX DOUBLED CHARACTERS (993355,,220000 -> 935,200)
# =================================================
def fix_doubled_chars(text: str) -> str:
    """Fix doubled characters like 993355,,220000 -> 935,200"""
    result = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == text[i + 1]:
            result.append(text[i])
            i += 2
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


# =================================================
# NORMALIZE TEXT
# =================================================
def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


# =================================================
# EXTRACT SECTION BETWEEN MARKERS
# =================================================
def extract_section(text: str, start_marker: str, end_markers: list) -> str:
    pattern = start_marker + r"(.*?)(" + "|".join(end_markers) + ")"
    m = re.search(pattern, text, re.S | re.I)
    return m.group(1) if m else ""


# =================================================
# FIND VALUE AFTER LABEL (inline or next line)
# =================================================
def find_value_after_label(text: str, label: str) -> str:
    # Try inline first: "Label : Value" or "Label: Value"
    pattern = re.escape(label) + r"\s*[:\-]?\s*([A-Za-z0-9@.\-_,/ ()]+)"
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        # Clean up common noise
        val = re.sub(r"^\s*[:\-]\s*", "", val)
        if val and len(val) > 1:
            return val

    # Try next line approach
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        if label.lower() in line.lower():
            # Check if value is on same line after label
            parts = re.split(r"[:\-]", line, 1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()
            # Check next line
            if i + 1 < len(lines):
                return lines[i + 1].strip()
    return ""


# =================================================
# EXTRACT EMAIL
# =================================================
def extract_email(text: str, context: str = "") -> str:
    search_text = context if context else text
    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", search_text)
    return m.group(0) if m else ""


# =================================================
# STRUCTURED EXTRACTION (COMPLETE)
# =================================================
def extract_structured_fields(clean_text: str) -> dict:
    text = normalize_text(clean_text)

    # --- CONTRACT NO ---
    contract_no = ""
    m = re.search(r"GEMC?-?\d{10,}", text)
    if m:
        contract_no = m.group(0)

    # --- GENERATED DATE ---
    generated_date = ""
    d = re.search(r"\d{1,2}-[A-Za-z]{3}-\d{4}", text)
    if d:
        generated_date = d.group(0)

    # --- ORGANISATION NAME ---
    org_name = ""
    # Strategy: Look for "Organisation Name" and get the value from the NEXT line (skip address on same line)
    # Pattern: "Organisation Name" followed by optional address, then newline, then org name
    m = re.search(r"Organisation\s*Name\s*[:\-]?\s*[^\n]*(?:Behind|Near|Road|Address|Office)[^\n]*\n\s*([A-Za-z][A-Za-z0-9 ,.\-()&]+?)(?:\s*[:\-]|\s*Address|\s*Office|\n)", text, re.I | re.MULTILINE)
    if m:
        org_name = m.group(1).strip()
        # Clean up
        org_name = re.sub(r"\s+", " ", org_name)
    # If not found with address pattern, try direct next line
    if not org_name:
        m = re.search(r"Organisation\s*Name\s*[:\-]?\s*\n\s*([A-Za-z][A-Za-z0-9 ,.\-()&]+?)(?:\s*[:\-]|\s*Address|\s*Office|\n)", text, re.I | re.MULTILINE)
        if m:
            org_name = m.group(1).strip()
            org_name = re.sub(r"\s+", " ", org_name)
    
    # Fallback: Look for common org patterns (these are more reliable and avoid address issues)
    if not org_name or len(org_name) < 5 or any(keyword in org_name for keyword in ["Behind", "Near", "Road", "Office", "Zone", "Collector"]):
        org_patterns = [
            r"(National\s+Rural\s+Health\s+Mission\s*\(?NRHM\)?\s*State\s*Health\s*Society)",
            r"(National\s+Rural\s+Health\s+Mission\s*\(?NRHM\)?[A-Za-z ]*)",
            r"(National\s+Health\s+Mission[A-Za-z ]*)",
            r"(State\s+Health\s+Society[A-Za-z ]*)",
            r"(PHC\s+ACCOUNTANT)",
            r"(PHC\s+[A-Za-z ]+)",
            r"(District\s+Hospital[A-Za-z ]*)",
            r"(Government\s+Hospital[A-Za-z ]*)",
            r"(Medical\s+College[A-Za-z ]*)",
            r"(Primary\s+Health\s+Centre[A-Za-z ]*)",
            r"(CHC\s+[A-Za-z ]*)",
        ]
        for pat in org_patterns:
            m = re.search(pat, text, re.I)
            if m:
                candidate = m.group(1).strip()
                # Skip if it contains address keywords
                if not any(keyword in candidate for keyword in ["Behind", "Near", "Road", "Office", "Zone", "Collector", "Barshi"]):
                    org_name = candidate
                    break

    # --- MINISTRY ---
    ministry = ""
    m = re.search(r"Ministry\s*[:\-]?\s*([A-Za-z0-9 ,.\-/()]+?)(?:\s*Contact|\s*Email|\n)", text, re.I)
    if m:
        ministry = m.group(1).strip()
    if not ministry or ministry.strip() == "-":
        ministry = "NA"

    # --- DEPARTMENT ---
    department = ""
    # List of state names to exclude
    state_names = [
        "Gujarat", "Maharashtra", "Uttar Pradesh", "Madhya Pradesh", "Rajasthan",
        "Karnataka", "Tamil Nadu", "West Bengal", "Bihar", "Odisha", "Assam",
        "Punjab", "Haryana", "Jharkhand", "Chhattisgarh", "Uttarakhand",
        "Himachal Pradesh", "Goa", "Delhi", "Jammu", "Kashmir", "Telangana",
        "Andhra Pradesh", "Uttar", "MP", "UP", "MH", "GJ", "RJ", "KA", "TN", "WB"
    ]
    
    # Strategy 1: Look for common department patterns first (most reliable)
    dept_patterns = [
        r"(Health\s*&\s*Family\s*Welfare\s*Department)",
        r"(Public\s+Health\s+[A-Za-z ]*Family\s*Welfare\s*Department)",
        r"(Public\s+Health\s+[A-Za-z ]+Department)",
        r"(Family\s*Welfare\s*Department)",
    ]
    for pat in dept_patterns:
        m = re.search(pat, text, re.I)
        if m:
            department = m.group(1).strip()
            break
    
    # Strategy 2: Extract from "Department :" label, stop before state names
    if not department:
        state_pattern = "|".join([re.escape(s) for s in state_names])
        # Pattern: "Department :" followed by value, stop at state name or next field
        m = re.search(r"Department\s*[:\-]?\s*([A-Za-z][A-Za-z0-9 ,.\-/()&]+?)(?:\s*(?:" + state_pattern + r")\b|\s*Organisation|\s*GSTIN|\s*Email|\n)", text, re.I)
        if m:
            department = m.group(1).strip()
            # Check if the extracted value is just a state name - if so, set to empty
            if department in state_names or department in ["Uttar", "Gujarat"]:
                department = ""
            else:
                # Remove any trailing state name if captured
                for state in state_names:
                    if department.endswith(state):
                        department = department.replace(state, "").strip()
                        break
    
    # Remove any trailing "Email ID" if captured
    department = re.sub(r"\s*Email\s*ID.*$", "", department, flags=re.I)
    # Final cleanup - remove trailing state names
    for state in state_names:
        if department.endswith(state):
            department = department.replace(state, "").strip()
            break

    # --- BUYER SECTION ---
    buyer_section = extract_section(text, r"Buyer Details", 
                                     ["Seller Details", "Financial", "Product Details", "Consignee"])
    
    # --- BUYER NAME (from Designation or Organisation) ---
    buyer_name = ""
    buyer_designation = ""
    m = re.search(r"Designation\s*[:\-]?\s*([A-Za-z0-9 ,.\-/()]+?)(?:\s*Contact|\s*Email|\n)", buyer_section + text, re.I)
    if m:
        buyer_designation = m.group(1).strip()
        buyer_name = buyer_designation  # Use designation as name if available
    
    # If no designation, try to get from organisation
    if not buyer_name:
        m = re.search(r"Organisation Name\s*[:\-]?\s*([A-Za-z][A-Za-z0-9 ,.\-]+)", text, re.I)
        if m:
            buyer_name = m.group(1).strip()

    # --- BUYER EMAIL ---
    buyer_email = ""
    # Get the first email (buyer) from the text
    emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    if emails:
        buyer_email = emails[0]

    # --- BUYER PHONE NUMBER ---
    buyer_phone = ""
    # Look for Contact No in buyer section
    m = re.search(r"Contact\s*(?:No\.?)?\s*[:\-]?\s*([0-9\-]+)", buyer_section + text, re.I)
    if m:
        buyer_phone = m.group(1).strip()
    # Fallback: look for phone pattern in buyer section
    if not buyer_phone:
        m = re.search(r"\b([6-9]\d{2}[-]?\d{3}[-]?\d{4,5})", buyer_section + text)
        if m:
            buyer_phone = m.group(1)

    # --- BUYER ADDRESS ---
    buyer_address = ""
    # Look for Address in buyer section - capture multi-line until we hit next field
    # Try to capture full address including state and PIN
    m = re.search(r"Address\s*[:\-]?\s*([A-Za-z0-9 ,.\-/()\n]+?)(?:\s*Office|\s*GSTIN|\s*Zone|Email|Contact|Paying|Financial)", buyer_section + text, re.I | re.S)
    if m:
        buyer_address = m.group(1).strip()
        # Clean up - remove extra whitespace and newlines, but keep structure
        buyer_address = re.sub(r"\n+", ", ", buyer_address)
        buyer_address = re.sub(r"\s+", " ", buyer_address)
        # Fix multiple consecutive commas
        while ",," in buyer_address or ", ," in buyer_address:
            buyer_address = buyer_address.replace(",,", ",").replace(", ,", ", ")
        buyer_address = re.sub(r",\s*$", "", buyer_address)  # Remove trailing comma
        buyer_address = buyer_address.strip()
    
    # If address is too short, try to get more context
    if len(buyer_address) < 20:
        # Look for address pattern with state and PIN code
        m = re.search(r"Address\s*[:\-]?\s*([A-Za-z0-9 ,.\-/()\n]+?[A-Z]{2,}\s*[A-Z]{2,}[-]?\d{6})", buyer_section + text, re.I | re.S)
        if m:
            buyer_address = m.group(1).strip()
            buyer_address = re.sub(r"\n+", ", ", buyer_address)
            buyer_address = re.sub(r"\s+", " ", buyer_address)

    # --- BUYER GSTIN ---
    buyer_gstin = ""
    # Only search in buyer section, before seller section
    if buyer_section:
        m = re.search(r"GSTIN\s*[:\-]?\s*([A-Z0-9]{15})", buyer_section, re.I)
        if m:
            buyer_gstin = m.group(1).strip()
    # Also try in paying authority section (sometimes buyer GSTIN is there)
    if not buyer_gstin:
        paying_section = extract_section(text, r"Paying Authority", ["Seller Details", "Product Details"])
        if paying_section:
            m = re.search(r"GSTIN\s*[:\-]?\s*([A-Z0-9]{15})", paying_section, re.I)
            if m:
                buyer_gstin = m.group(1).strip()

    # --- BUYER STATE ---
    buyer_state = ""
    # Extract state from Buyer Address field (state is typically at the end of address)
    if buyer_address:
        state_patterns = [
            r"\b(MAHARASHTRA|GUJARAT|UTTAR PRADESH|MADHYA PRADESH|RAJASTHAN|KARNATAKA|TAMIL NADU|WEST BENGAL|BIHAR|ODISHA|ASSAM|PUNJAB|HARYANA|JHARKHAND|CHHATTISGARH|UTTARAKHAND|HIMACHAL PRADESH|GOA|DELHI|JAMMU|KASHMIR|TELANGANA|ANDHRA PRADESH)\b"
        ]
        for pat in state_patterns:
            m = re.search(pat, buyer_address, re.I)
            if m:
                buyer_state = m.group(1).strip().title()
                break

    # --- SELLER SECTION ---
    seller_section = extract_section(text, r"Seller Details", 
                                      ["Product Details", "Consignee", "GST/TAX", "Delivery"])
    # Also try doubled pattern
    seller_idx = text.find("SSeelllleerr DDeettaaiillss")
    if seller_idx < 0:
        seller_idx = text.lower().find("seller details")
    
    if seller_idx > 0:
        seller_text = text[seller_idx:]
        if not seller_section:
            seller_section = seller_text[:2000]  # Limit to avoid too much text

    # --- SELLER NAME (Company Name) / SHOP NAME ---
    seller_name = ""
    seller_shop_name = ""
    m = re.search(r"Company Name\s*[:\-]?\s*([A-Za-z0-9 &,.\-/()]+?)(?:\s*Contact|\s*Email|\s*Address|\n)", seller_section + text, re.I)
    if m:
        seller_name = m.group(1).strip()
        seller_shop_name = seller_name  # Shop name is same as company name

    # --- SELLER EMAIL ---
    seller_email = ""
    if seller_section:
        m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", seller_section)
        if m:
            seller_email = m.group(0)
    
    # If seller email is same as buyer, try to find a different one
    if seller_email == buyer_email or not seller_email:
        # Find all unique emails
        unique_emails = []
        for e in emails:
            if e not in unique_emails:
                unique_emails.append(e)
        # Seller email should be different from buyer email
        for e in unique_emails:
            if e != buyer_email:
                seller_email = e
                break

    # --- SELLER PHONE NUMBER ---
    seller_phone = ""
    # Look for Contact No in seller section
    m = re.search(r"Contact\s*(?:No\.?)?\s*[:\-]?\s*([0-9\-]+)", seller_section + text, re.I)
    if m:
        seller_phone = m.group(1).strip()
    # Fallback: look for phone pattern in seller section
    if not seller_phone:
        m = re.search(r"\b([6-9]\d{2}[-]?\d{3}[-]?\d{4,5})", seller_section + text)
        if m:
            seller_phone = m.group(1)

    # --- SELLER ADDRESS ---
    seller_address = ""
    # Look for Address in seller section - capture multi-line until we hit next field
    m = re.search(r"Address\s*[:\-]?\s*([A-Za-z0-9 ,.\-/()\n]+?)(?:\s*MSME|\s*GSTIN|\s*Registration|Email|Contact|Product)", seller_section + text, re.I | re.S)
    if m:
        seller_address = m.group(1).strip()
        # Clean up - remove extra whitespace and newlines, but keep structure
        seller_address = re.sub(r"\n+", ", ", seller_address)
        seller_address = re.sub(r"\s+", " ", seller_address)
        # Fix multiple consecutive commas
        while ",," in seller_address or ", ," in seller_address:
            seller_address = seller_address.replace(",,", ",").replace(", ,", ", ")
        seller_address = re.sub(r",\s*$", "", seller_address)  # Remove trailing comma
        seller_address = seller_address.strip()
    
    # If address is too short, try to get more context
    if len(seller_address) < 20:
        # Look for address pattern with state and PIN code
        m = re.search(r"Address\s*[:\-]?\s*([A-Za-z0-9 ,.\-/()\n]+?[A-Z]{2,}\s*[A-Z]{2,}[-]?\d{6})", seller_section + text, re.I | re.S)
        if m:
            seller_address = m.group(1).strip()
            seller_address = re.sub(r"\n+", ", ", seller_address)
            seller_address = re.sub(r"\s+", " ", seller_address)

    # --- SELLER GSTIN ---
    seller_gstin = ""
    m = re.search(r"GSTIN\s*[:\-]?\s*([A-Z0-9]{15})", seller_section + text, re.I)
    if m:
        seller_gstin = m.group(1).strip()

    # --- SELLER STATE ---
    seller_state = ""
    # Extract state from Seller Address field (state is typically at the end of address)
    if seller_address:
        state_patterns = [
            r"\b(MAHARASHTRA|GUJARAT|UTTAR PRADESH|MADHYA PRADESH|RAJASTHAN|KARNATAKA|TAMIL NADU|WEST BENGAL|BIHAR|ODISHA|ASSAM|PUNJAB|HARYANA|JHARKHAND|CHHATTISGARH|UTTARAKHAND|HIMACHAL PRADESH|GOA|DELHI|JAMMU|KASHMIR|TELANGANA|ANDHRA PRADESH)\b"
        ]
        for pat in state_patterns:
            m = re.search(pat, seller_address, re.I)
            if m:
                seller_state = m.group(1).strip().title()
                break

    # --- GEM SELLER ID ---
    gem_seller_id = ""
    # GeM Seller ID can be alphanumeric like "2B2418000012P123" - capture full ID
    m = re.search(r"GeM\s*Seller\s*ID\s*[:\-]?\s*([A-Z0-9]{10,})", seller_section + text, re.I)
    if m:
        gem_seller_id = m.group(1).strip()
    # Try doubled pattern if not found
    if not gem_seller_id:
        m = re.search(r"GGeemm\s*SSelleerr\s*IIDD\s*[:\-]?\s*([A-Z0-9]{10,})", text, re.I)
        if m:
            gem_seller_id = m.group(1).strip()

    # --- PRODUCT SECTION ---
    product_section = extract_section(text, r"Product Details", 
                                       ["Consignee", "Specification", "Terms", "Delivery"])

    # --- PRODUCT NAME ---
    product_name = ""
    # Look for doubled label pattern PPrroodduucctt NNaammee
    m = re.search(r"PPrroodduucctt NNaammee\s*[:\-]?\s*:?\s*([A-Za-z0-9 &,.\-/()]+?)(?:\s*BBrraanndd|\s*Brand|\n)", product_section + text)
    if m:
        product_name = m.group(1).strip()
    # Try normal pattern
    if not product_name:
        m = re.search(r"Product Name\s*[:\-]?\s*([A-Za-z0-9 &,.\-/()]+?)(?:\s*Brand|\s*Catalogue|\n)", product_section + text, re.I)
        if m:
            product_name = m.group(1).strip()
    # Try finding common product patterns
    if not product_name:
        m = re.search(r"(TRUSTwell[A-Za-z0-9 ]+(?:Kit|Test))", product_section + text, re.I)
        if m:
            product_name = m.group(1).strip()
        else:
            m = re.search(r"([A-Za-z]+\s+(?:ELISA|Test|Rapid|Diagnostic)\s+[A-Za-z ]+Kit)", product_section + text, re.I)
            if m:
                product_name = m.group(1).strip()
        # Try Pratham pattern
        if not product_name:
            m = re.search(r"(Pratham[A-Za-z0-9 ]+(?:Kit|Test))", product_section + text, re.I)
            if m:
                product_name = m.group(1).strip()

    # --- PRODUCT CATEGORY ---
    product_category = ""
    # Look for Category Name & Quadrant
    m = re.search(r"Category\s*(?:Name\s*&?\s*Quadrant)?\s*[:\-]?\s*([A-Za-z0-9 &,.\-/()]+?)(?:\s*Model|\s*HSN|\n)", product_section + text, re.I)
    if m:
        product_category = m.group(1).strip()
    # Try doubled pattern
    if not product_category:
        m = re.search(r"CCaatteeggoorryy NNaammee.*?([A-Za-z0-9 &,.\-/()]+?)(?:\s*MMooddeell|\n)", product_section + text, re.I)
        if m:
            product_category = m.group(1).strip()

    # --- BRAND ---
    brand = ""
    # Look for Brand field
    m = re.search(r"Brand\s*[:\-]?\s*([A-Za-z0-9 &,.\-/()]+?)(?:\s*Brand Type|\s*Catalogue|\n)", product_section + text, re.I)
    if m:
        brand = m.group(1).strip()
    # Try doubled pattern
    if not brand:
        m = re.search(r"BBrraanndd\s*[:\-]?\s*:?\s*([A-Za-z0-9 &,.\-/()]+?)(?:\s*BBrraanndd TTyyppee|\n)", product_section + text, re.I)
        if m:
            brand = m.group(1).strip()

    # --- UNIT ---
    unit = ""
    # Look for Unit in quantity field (e.g., "13,360 Test")
    m = re.search(r"\b[\d,]+\s+(Test|Tests|Nos|Units?|Kit|Kits|Box|Boxes|Piece|Pieces|Pack|Packs)\b", product_section + text, re.I)
    if m:
        unit = m.group(1).strip()
    # Try Ordered Unit column
    if not unit:
        m = re.search(r"Ordered\s*Unit\s*[:\-]?\s*([A-Za-z]+)", product_section + text, re.I)
        if m:
            unit = m.group(1).strip()

    # --- UNIT PRICE ---
    unit_price = ""
    # Look for Unit Price pattern - try to find in table row
    # Pattern: number after quantity, before tax
    m = re.search(r"\b1\s+[\d,]+\s+(?:Test|Nos)\s+([\d,]+(?:\.\d{2})?)", product_section + text, re.I)
    if m:
        unit_price = m.group(1).replace(",", "")
    # Try explicit Unit Price label
    if not unit_price:
        m = re.search(r"Unit\s*Price\s*(?:\(INR\))?\s*[:\-]?\s*([\d,]+(?:\.\d{2})?)", product_section + text, re.I)
        if m:
            unit_price = m.group(1).replace(",", "")
    # Try doubled pattern
    if not unit_price:
        m = re.search(r"UUnniitt PPrriiccee.*?([\d,]+(?:\.\d{2})?)", product_section + text, re.I)
        if m:
            unit_price = m.group(1).replace(",", "")
    # Try to find price in table: "1 13,360 Test 70 NA 935,200" - 70 is unit price
    if not unit_price:
        m = re.search(r"\b1\s+[\d,]+\s+(?:Test|Nos)\s+([\d,]+)", product_section + text, re.I)
        if m:
            # Check if this looks like a unit price (reasonable range)
            potential_price = m.group(1).replace(",", "")
            if potential_price and len(potential_price) <= 6:  # Unit price usually < 1000000
                unit_price = potential_price

    # --- QUANTITY ---
    quantity = ""
    # Look for patterns like "13,360 Test" - but handle doubled digits
    m = re.search(r"\b1\s+([\d,]+)\s+(?:Test|Nos)", text, re.I)
    if m:
        raw_qty = m.group(1).replace(",", "")
        # Check if it's doubled (e.g., 1133,,336600 -> 13,360)
        if len(raw_qty) > 6 and all(raw_qty[i] == raw_qty[i+1] for i in range(0, len(raw_qty)-1, 2) if i+1 < len(raw_qty)):
            quantity = fix_doubled_chars(raw_qty)
        else:
            quantity = raw_qty
    if not quantity:
        m = re.search(r"(?:Ordered\s*)?Quantity\s*[:\-]?\s*([\d,]+)", text, re.I)
        if m:
            quantity = m.group(1).replace(",", "")

    # --- TOTAL ORDER VALUE (INR) ---
    total_value = ""
    m = re.search(r"Total\s*Order\s*Value\s*(?:\(in\s*INR\))?\s*[:\-]?\s*([\d,]+(?:\.\d{2})?)", text, re.I)
    if m:
        raw_val = m.group(1).replace(",", "")
        # Check if doubled (993355220000 -> 935200)
        if len(raw_val) > 8:
            total_value = fix_doubled_chars(raw_val)
        else:
            total_value = raw_val
    if not total_value:
        m = re.search(r"INR\s*[:\-]?\s*([\d,]+(?:\.\d{2})?)", text, re.I)
        if m:
            raw_val = m.group(1).replace(",", "")
            if len(raw_val) > 8:
                total_value = fix_doubled_chars(raw_val)
            else:
                total_value = raw_val

    # --- CLEAN UP EMPTY VALUES ---
    def clean_value(v):
        if not v or v.strip() in ["-", "", "NA", "N/A"]:
            return "NA"
        # Remove trailing punctuation and clean
        v = re.sub(r"^[\s:\-]+|[\s:\-]+$", "", v)
        return v.strip() if v.strip() else "NA"

    return {
        # Contract Info (EXCLUDED: Generated Date, Ministry, PDF Name)
        "Contract No": clean_value(contract_no),
        "Organisation Name": clean_value(org_name),
        "Department": clean_value(department),
        
        # Buyer Details (EXCLUDED: Buyer GSTIN)
        "Buyer Name": clean_value(buyer_name),
        "Buyer Designation": clean_value(buyer_designation),
        "Buyer Email": clean_value(buyer_email),
        "Buyer Phone Number": clean_value(buyer_phone),
        "Buyer Address": clean_value(buyer_address),
        "Buyer State": clean_value(buyer_state),
        
        # Seller Details
        "Seller Name": clean_value(seller_name),
        "Seller Shop Name": clean_value(seller_shop_name),
        "Seller Email": clean_value(seller_email),
        "Seller Phone Number": clean_value(seller_phone),
        "Seller Address": clean_value(seller_address),
        "Seller GSTIN": clean_value(seller_gstin),
        "Seller State": clean_value(seller_state),
        "GeM Seller ID": clean_value(gem_seller_id),
        
        # Product Details
        "Product Name": clean_value(product_name),
        "Product Category": clean_value(product_category),
        "Brand": clean_value(brand),
        "Unit": clean_value(unit),
        "Quantity": clean_value(quantity),
        "Unit Price": clean_value(unit_price),
        "Total Order Value (INR)": clean_value(total_value),
    }


# =================================================
# ONE-CALL HELPER (IMPORT THIS)
# =================================================
def extract_pdf_structured_data(pdf_file) -> dict:
    raw_text = extract_pdf_to_text(pdf_file)
    cleaned_text = clean_extracted_text(raw_text)
    return extract_structured_fields(cleaned_text)


# =================================================
# POWER BI TABLE GENERATOR
# =================================================
def generate_powerbi_tables(extracted_data_list: list) -> dict:
    """
    Generate Power BI-ready dimension and fact tables from extracted PDF data.
    
    Args:
        extracted_data_list: List of dictionaries from extract_pdf_structured_data()
    
    Returns:
        Dictionary with keys: 'Dim_Buyer', 'Dim_Seller', 'Dim_Product', 'Fact_Contract_Sales'
    """
    
    def clean_value(v):
        if not v or v.strip() in ["-", "", "NA", "N/A"]:
            return "NA"
        v = re.sub(r"^[\s:\-]+|[\s:\-]+$", "", str(v))
        return v.strip() if v.strip() else "NA"
    
    def generate_id(value, prefix=""):
        """Generate unique ID from value"""
        if value and value != "NA":
            # Create hash-based ID
            hash_obj = hashlib.md5(str(value).encode())
            return f"{prefix}{hash_obj.hexdigest()[:8].upper()}"
        return f"{prefix}UNKNOWN"
    
    # Collect all unique buyers
    buyers_dict = {}
    for data in extracted_data_list:
        buyer_key = (
            clean_value(data.get("Buyer Designation", "")),
            clean_value(data.get("Buyer Email", "")),
            clean_value(data.get("Buyer Phone Number", ""))
        )
        if buyer_key not in buyers_dict:
            buyer_id = generate_id(str(buyer_key), "BUYER_")
            buyers_dict[buyer_key] = {
                "Buyer_ID": buyer_id,
                "Buyer Designation": clean_value(data.get("Buyer Designation", "")),
                "Buyer Contact Number": clean_value(data.get("Buyer Phone Number", "")),
                "Buyer Email ID": clean_value(data.get("Buyer Email", "")),
                # Buyer GSTIN excluded as per requirements
                "Buyer State": clean_value(data.get("Buyer State", "")),
            }
    
    # Collect all unique sellers
    sellers_dict = {}
    for data in extracted_data_list:
        seller_id = clean_value(data.get("GeM Seller ID", ""))
        if seller_id == "NA" or not seller_id:
            # Fallback: use seller name + email
            seller_key = (
                clean_value(data.get("Seller Name", "")),
                clean_value(data.get("Seller Email", ""))
            )
            seller_id = generate_id(str(seller_key), "SELLER_")
        
        if seller_id not in sellers_dict:
            sellers_dict[seller_id] = {
                "Seller_ID": seller_id,
                "Seller Name": clean_value(data.get("Seller Name", "")),
                "Seller Contact Number": clean_value(data.get("Seller Phone Number", "")),
                "Seller Email ID": clean_value(data.get("Seller Email", "")),
                "Seller GSTIN": clean_value(data.get("Seller GSTIN", "")),
                "Seller State": clean_value(data.get("Seller State", "")),
            }
    
    # Collect all unique products
    products_dict = {}
    for data in extracted_data_list:
        product_key = (
            clean_value(data.get("Product Name", "")),
            clean_value(data.get("Brand", "")),
            clean_value(data.get("Unit", ""))
        )
        if product_key not in products_dict:
            product_id = generate_id(str(product_key), "PROD_")
            products_dict[product_key] = {
                "Product_ID": product_id,
                "Product Name": clean_value(data.get("Product Name", "")),
                "Brand": clean_value(data.get("Brand", "")),
                "Unit": clean_value(data.get("Unit", "")),
            }
    
    # Create fact table
    fact_rows = []
    for data in extracted_data_list:
        # Find buyer ID
        buyer_key = (
            clean_value(data.get("Buyer Designation", "")),
            clean_value(data.get("Buyer Email", "")),
            clean_value(data.get("Buyer Phone Number", ""))
        )
        buyer_id = buyers_dict.get(buyer_key, {}).get("Buyer_ID", "NA")
        
        # Find seller ID
        seller_id = clean_value(data.get("GeM Seller ID", ""))
        if seller_id == "NA" or not seller_id:
            seller_key = (
                clean_value(data.get("Seller Name", "")),
                clean_value(data.get("Seller Email", ""))
            )
            seller_id = generate_id(str(seller_key), "SELLER_")
            if seller_id not in sellers_dict:
                sellers_dict[seller_id] = {
                    "Seller_ID": seller_id,
                    "Seller Name": clean_value(data.get("Seller Name", "")),
                    "Seller Contact Number": clean_value(data.get("Seller Phone Number", "")),
                    "Seller Email ID": clean_value(data.get("Seller Email", "")),
                    "Seller GSTIN": clean_value(data.get("Seller GSTIN", "")),
                    "Seller State": clean_value(data.get("Seller State", "")),
                }
        
        # Find product ID
        product_key = (
            clean_value(data.get("Product Name", "")),
            clean_value(data.get("Brand", "")),
            clean_value(data.get("Unit", ""))
        )
        product_id = products_dict.get(product_key, {}).get("Product_ID", "NA")
        
        # Get numeric values
        quantity = clean_value(data.get("Quantity", ""))
        try:
            quantity_num = float(quantity) if quantity != "NA" else 0.0
        except:
            quantity_num = 0.0
        
        unit_price = clean_value(data.get("Unit Price", ""))
        try:
            unit_price_num = float(unit_price) if unit_price != "NA" else 0.0
        except:
            unit_price_num = 0.0
        
        total_value = clean_value(data.get("Total Order Value (INR)", ""))
        try:
            total_value_num = float(total_value) if total_value != "NA" else 0.0
        except:
            total_value_num = 0.0
        
        fact_rows.append({
            "Contract Number": clean_value(data.get("Contract No", "")),
            "Buyer_ID": buyer_id,
            "Seller_ID": seller_id,
            "Product_ID": product_id,
            "Ordered Quantity": quantity_num,
            "Unit Price (INR)": unit_price_num,
            "Total Order Value (INR)": total_value_num,
        })
    
    # Create DataFrames
    dim_buyer = pd.DataFrame(list(buyers_dict.values()))
    dim_seller = pd.DataFrame(list(sellers_dict.values()))
    dim_product = pd.DataFrame(list(products_dict.values()))
    fact_contract_sales = pd.DataFrame(fact_rows)
    
    return {
        "Dim_Buyer": dim_buyer,
        "Dim_Seller": dim_seller,
        "Dim_Product": dim_product,
        "Fact_Contract_Sales": fact_contract_sales,
    }
