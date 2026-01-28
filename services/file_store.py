# services/file_store.py
# =====================================================
# CENTRAL FILE STORE (EXCEL / CSV ONLY)
#
# - Streamlit safe
# - Cached CSV loading
# - Excel upload handling
# - No PDF logic
# - No folder creation
# =====================================================

import os
import pandas as pd
import streamlit as st

# =====================================================
# BASE PATHS
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_PATH = os.path.join(DATA_DIR, "uploaded_file.csv")
EXCEL_PATH = os.path.join(DATA_DIR, "uploaded_file.xlsx")

os.makedirs(DATA_DIR, exist_ok=True)

# =====================================================
# CACHE INVALIDATION
# =====================================================
@st.cache_data
def _cache_buster(ts: float):
    return ts


# =====================================================
# SAVE EXCEL FILE (UPLOAD)
# =====================================================
def save_excel_file(uploaded_file):
    """
    Save uploaded Excel file safely.
    - Excel backup
    - CSV for fast load
    - Cache invalidation
    """
    try:
        if uploaded_file is None:
            return None

        df = pd.read_excel(uploaded_file)

        if df.empty:
            st.warning("Uploaded Excel file is empty.")
            return None

        df.to_excel(EXCEL_PATH, index=False)
        df.to_csv(CSV_PATH, index=False)

        ts = os.path.getmtime(CSV_PATH)
        _cache_buster.clear()
        _cache_buster(ts)

        return df

    except Exception as e:
        st.error(f"Error while saving Excel file: {e}")
        return None


# =====================================================
# LOAD SAVED EXCEL DATA (CACHED)
# =====================================================
@st.cache_data
def _load_csv_cached(ts: float):
    return pd.read_csv(CSV_PATH)


def load_saved_excel():
    """
    Load last saved Excel data.
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
        st.error(f"Error while loading saved data: {e}")
        return None
