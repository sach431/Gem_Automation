import pandas as pd
import os

def export_to_excel(df, prefix="report"):
    os.makedirs("downloads", exist_ok=True)
    filename = f"{prefix}.xlsx"
    df.to_excel(f"downloads/{filename}", index=False)
    return filename
