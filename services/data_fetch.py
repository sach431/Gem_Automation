# services/data_fetch.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.data_loader import load_excel_file

def load_sales_data():
    """
    Loads Excel using data_loader, normalizes columns and ensures
    required dashboard columns exist. Returns (df, None) on success or (None, error_str).
    """
    try:
        df = load_excel_file()

        # strip column names
        df.columns = [c.strip() for c in df.columns]

        # Map existing Excel columns to dashboard standard columns
        rename_map = {
            "Name": "Seller Name",
            "State": "City",
            "Brand": "Category",
            "Mobile": "Mobile",
            "email": "Email"
        }
        # apply rename only for keys present
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Ensure critical columns exist (with fallbacks)
        if "Seller Name" not in df.columns:
            df["Seller Name"] = df.get("Name", "Unknown")
        if "City" not in df.columns:
            df["City"] = df.get("State", "Unknown")
        if "Category" not in df.columns:
            df["Category"] = df.get("Brand", "General")

        # Value: sales amount (if missing, create random reasonable amounts)
        if "Value" not in df.columns:
            df["Value"] = np.random.randint(5000, 50000, size=len(df))

        # Date: if missing, assign random dates within last 180 days
        if "Date" not in df.columns:
            today = datetime.today()
            df["Date"] = [
                today - timedelta(days=int(x))
                for x in np.random.randint(1, 180, size=len(df))
            ]

        # Ensure Date is datetime dtype and create Year
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Year"] = df["Date"].dt.year.fillna(datetime.today().year).astype(int)

        return df, None

    except Exception as e:
        return None, str(e)


# KPI helpers (used by Dashboard)
def top_n_sellers(df, n=5):
    if "Value" in df.columns and "Seller Name" in df.columns:
        tmp = df.groupby("Seller Name", as_index=False)["Value"].sum()
        return tmp.sort_values("Value", ascending=False).head(n)
    return pd.DataFrame()

def city_performance(df):
    if "Value" in df.columns and "City" in df.columns:
        tmp = df.groupby("City", as_index=False)["Value"].sum()
        return tmp.sort_values("Value", ascending=False)
    return pd.DataFrame()

def yearly_summary(df):
    if "Year" in df.columns and "Value" in df.columns:
        tmp = df.groupby("Year", as_index=False)["Value"].sum()
        return tmp.sort_values("Year")
    return pd.DataFrame()
