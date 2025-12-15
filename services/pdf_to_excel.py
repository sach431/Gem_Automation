import os
import pdfplumber
import pandas as pd

def convert_pdfs_to_excel(pdf_dir, excel_dir, category):
    rows = []
    headers = None

    for file in os.listdir(pdf_dir):
        if file.endswith(".pdf"):
            path = os.path.join(pdf_dir, file)
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table and len(table) > 1:
                        headers = table[0]
                        rows.extend(table[1:])

    if not rows:
        return None

    df = pd.DataFrame(rows, columns=headers)
    output = os.path.join(excel_dir, f"{category}.xlsx")
    df.to_excel(output, index=False)

    return output
