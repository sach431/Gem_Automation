# services/category_folder.py

import os

def setup_category(category):
    base = os.path.join("downloads", category.lower())
    pdf_dir = os.path.join(base, "pdfs")
    excel_dir = os.path.join(base, "excel")

    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(excel_dir, exist_ok=True)

    return pdf_dir, excel_dir
