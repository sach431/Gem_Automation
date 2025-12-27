import os
import pandas as pd
from io import BytesIO


def export_to_excel(
    df: pd.DataFrame,
    category: str = "general",
    filename: str = "GEM_Final_Report"
):
    """
    Export structured DataFrame to Excel safely.

    Returns:
        (excel_bytes, saved_path)
    """

    if df is None or df.empty:
        raise ValueError("DataFrame is empty. Nothing to export.")

    # Category wise folder
    base_dir = os.path.join(
        "downloads",
        category.lower(),
        "excel"
    )
    os.makedirs(base_dir, exist_ok=True)

    file_path = os.path.join(base_dir, f"{filename}.xlsx")

    # Save to disk
    df.to_excel(file_path, index=False)

    # Also prepare bytes for Streamlit download
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    return buffer, file_path
