# services/category_folder.py
# =====================================================
# CATEGORY FOLDER SETUP (PRODUCTION SAFE)
# =====================================================

import os


def setup_category(category: str):
    """
    Creates and returns category-specific PDF and Excel folders.

    Structure:
    downloads/<Category>/pdfs
    downloads/<Category>/excel
    """

    if not category or not isinstance(category, str):
        raise ValueError("Invalid category name")

    # Base project directory
    base_dir = os.getcwd()

    category_base = os.path.join(
        base_dir,
        "downloads",
        category.strip()
    )

    pdf_dir = os.path.join(category_base, "pdfs")
    excel_dir = os.path.join(category_base, "excel")

    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(excel_dir, exist_ok=True)

    return pdf_dir, excel_dir
