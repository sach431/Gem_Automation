# services/pdf_to_excel.py

import os
import shutil
from datetime import datetime

import pdfplumber
import pandas as pd


# =========================================================
# STEP 1: Downloads folder se latest PDF uthana
# =========================================================
def move_latest_pdf_from_downloads(target_pdf_dir):

    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(download_dir):
        return None

    pdf_files = [
        f for f in os.listdir(download_dir)
        if f.lower().endswith(".pdf")
    ]
    if not pdf_files:
        return None

    latest_pdf = max(
        pdf_files,
        key=lambda f: os.path.getmtime(os.path.join(download_dir, f))
    )

    os.makedirs(target_pdf_dir, exist_ok=True)

    src = os.path.join(download_dir, latest_pdf)
    dst = os.path.join(target_pdf_dir, latest_pdf)

    shutil.move(src, dst)
    return dst


# =========================================================
# STEP 2: PDF rename
# =========================================================
def rename_pdf_datewise(pdf_path, category):

    pdf_dir = os.path.dirname(pdf_path)
    today = datetime.now().strftime("%Y-%m-%d")

    safe_category = category.replace(" ", "_")

    base = f"{safe_category}_{today}"
    new_path = os.path.join(pdf_dir, base + ".pdf")

    if not os.path.exists(new_path):
        os.rename(pdf_path, new_path)
        return new_path

    counter = 2
    while True:
        path = os.path.join(pdf_dir, f"{base}_{counter}.pdf")
        if not os.path.exists(path):
            os.rename(pdf_path, path)
            return path
        counter += 1


# =========================================================
# STEP 3: PDF → Excel
# =========================================================
def convert_pdfs_to_excel(pdf_dir, excel_dir, category):

    moved_pdf = move_latest_pdf_from_downloads(pdf_dir)
    if not moved_pdf:
        return None

    final_pdf_path = rename_pdf_datewise(moved_pdf, category)

    all_rows = []
    final_headers = None

    try:
        with pdfplumber.open(final_pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table or len(table) < 2:
                    continue

                headers = [
                    str(h).strip() if h else f"Column_{i+1}"
                    for i, h in enumerate(table[0])
                ]

                if final_headers is None:
                    final_headers = headers

                col_len = len(final_headers)

                for row in table[1:]:
                    if not row or not any(row):
                        continue

                    row = [
                        str(c).strip() if c else ""
                        for c in row
                    ]

                    if len(row) < col_len:
                        row += [""] * (col_len - len(row))
                    elif len(row) > col_len:
                        row = row[:col_len]

                    all_rows.append(row)

    except Exception as e:
        print("PDF extract error:", e)
        return None

    if not all_rows:
        return None

    os.makedirs(excel_dir, exist_ok=True)

    df = pd.DataFrame(all_rows, columns=final_headers)

    excel_name = os.path.splitext(
        os.path.basename(final_pdf_path)
    )[0] + ".xlsx"

    excel_path = os.path.join(excel_dir, excel_name)
    df.to_excel(excel_path, index=False)

    return excel_path
