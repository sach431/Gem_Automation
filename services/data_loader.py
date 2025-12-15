# services/data_loader.py

import os
import pandas as pd

def get_excel_path():
    """
    Compute absolute path to the Excel file (project-root/data/excel/...)
    """
    # __file__ is services/data_loader.py → go up one level to project root
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # expected relative location of your excel file
    rel = os.path.join("data", "excel", "CHIKUNGUNYA_GEM+2024-25.xlsx")
    return os.path.join(base, rel)

def load_excel_file():
    """
    Returns a pandas DataFrame loaded from Excel or raises FileNotFoundError.
    """
    path = get_excel_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found at: {path}")
    # read with openpyxl engine
    df = pd.read_excel(path, engine="openpyxl")
    return df
