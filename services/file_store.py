# services/file_store.py

import os
import pandas as pd
import streamlit as st

# -------------------------------------------------
# PERMANENT STORAGE PATHS
# -------------------------------------------------
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "uploaded_file.csv")
EXCEL_PATH = os.path.join(DATA_DIR, "uploaded_file.xlsx")

# Ensure directory exists
os.makedirs(DATA_DIR, exist_ok=True)


# -------------------------------------------------
# CACHE INVALIDATION HELPER
# -------------------------------------------------
@st.cache_data
def _cache_buster(ts: float):
    """
    Dummy cached function.
    Cache invalidates automatically when timestamp changes.
    """
    return ts


# -------------------------------------------------
# SAVE EXCEL FILE (OVERWRITE ALWAYS)
# -------------------------------------------------
def save_excel_file(uploaded_file):
    """
    Saves uploaded Excel file safely.

    Steps:
    1. Read Excel
    2. Save Excel (backup)
    3. Save CSV (fast loading)
    4. Invalidate cache automatically

    Returns:
        DataFrame or None
    """
    try:
        if uploaded_file is None:
            return None

        # Read Excel
        df = pd.read_excel(uploaded_file)

        if df.empty:
            st.warning("⚠ Uploaded Excel is empty.")
            return None

        # Save Excel (backup)
        df.to_excel(EXCEL_PATH, index=False)

        # Save CSV (primary read source)
        df.to_csv(CSV_PATH, index=False)

        # Bust cache
        ts = os.path.getmtime(CSV_PATH)
        _cache_buster.clear()
        _cache_buster(ts)

        return df

    except Exception as e:
        st.error(f"❌ Error while saving Excel file: {e}")
        return None


# -------------------------------------------------
# LOAD CSV WITH CACHE (FAST)
# -------------------------------------------------
@st.cache_data
def _load_csv_cached(ts: float):
    """
    Loads CSV using Streamlit cache.
    Cache refreshes only when file timestamp changes.
    """
    df = pd.read_csv(CSV_PATH)
    return df


# -------------------------------------------------
# PUBLIC LOADER (USE EVERYWHERE)
# -------------------------------------------------
def load_saved_excel():
    """
    Universal loader used across all screens.

    Logic:
    - Load CSV if exists
    - Respect cache timestamp
    - Return DataFrame or None
    """
    try:
        if not os.path.exists(CSV_PATH):
            return None

        ts = os.path.getmtime(CSV_PATH)
        df = _load_csv_cached(ts)

        if df is None or df.empty:
            return None

        return df

    except Exception as e:
        st.error(f"❌ Error while loading saved data: {e}")
        return None
