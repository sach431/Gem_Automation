import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from services.file_store import load_saved_excel
from services.date_filter import apply_date_filter

# ================== CONFIG ==================
TOP_N = 5
# ============================================

# ----------------- GLOBAL CSS -----------------
st.markdown("""
<style>
h1, h2, h3, h4, h5, h6 {
    text-transform: uppercase !important;
    font-weight:700 !important;
}

.block-container { 
    font-size: 15px !important; 
    padding-top: 1rem;
    padding-bottom: 1rem;
}

div[data-testid="stDataFrame"] thead tr th {
    background-color: #1f2937 !important;
    color: #ffffff !important;
    font-size: 13px !important;
}
div[data-testid="stDataFrame"] tbody tr td {
    font-size: 13px !important;
    padding: 6px 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------- HELPERS -----------------
def sanitize_strings(df):
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.strip()
    return df


def detect_date_column(df):
    patterns = ["date", "orderdate", "order_date", "created", "timestamp"]
    for c in df.columns:
        name = c.lower().replace(" ", "")
        if any(p in name for p in patterns):
            df[c] = pd.to_datetime(df[c], errors="coerce")
            if df[c].dropna().any():
                return c
    return None


def detect_columns(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()

    value_col = next(
        (c for c in df.columns if any(k in c.lower() for k in ["amount", "value", "price", "total"])),
        numeric_cols[0] if numeric_cols else None
    )

    org_col = next(
        (c for c in text_cols if any(k in c.lower() for k in [
            "organisation", "organization", "seller", "buyer", "company", "name"
        ])),
        None
    )

    city_col = next(
        (c for c in text_cols if "city" in c.lower()),
        None
    )

    return value_col, org_col, city_col


def apply_search_filter(df, search):
    if not search:
        return df
    s = search.lower()
    return df[df.apply(lambda r: s in " ".join(r.astype(str)).lower(), axis=1)]

# ----------------- MAIN APP -----------------
def app(search=None, start_date=None, end_date=None, mode=None):

    st.header("📊 KPI Dashboard")

    # -------- LOAD DATA --------
    df = load_saved_excel()
    if df is None or df.empty:
        st.warning("⚠ Upload an Excel in Master Category first.")
        return

    df = sanitize_strings(df.copy())
    df.columns = df.columns.str.strip()

    # -------- DATE FILTER --------
    date_col = detect_date_column(df)
    if date_col and start_date is not None and mode is not None:
        df, label, d1, d2 = apply_date_filter(
            df,
            date_col=date_col,
            from_date=start_date,
            to_date=end_date,
            mode=mode
        )
        if label:
            st.caption(
                f"📌 Period Applied: **{label}** "
                f"({d1.strftime('%Y-%m-%d')} → {d2.strftime('%Y-%m-%d')})"
            )

    # -------- SEARCH --------
    df = apply_search_filter(df, search)
    if df.empty:
        st.info("ℹ️ No data available.")
        return

    # -------- COLUMN DETECTION --------
    value_col, org_col, city_col = detect_columns(df)

    if value_col:
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)

    # -------- KPI --------
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Records", len(df))
    c2.metric("Total Value", f"{df[value_col].sum():,.0f}" if value_col else "N/A")
    c3.metric("Average Value", f"{df[value_col].mean():,.2f}" if value_col else "N/A")

    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

    # -------- TOP 5 TABLES --------
    col1, col2 = st.columns(2)

    # --- Top Organizations ---
    with col1:
        st.subheader("🏥 Top 5 Organizations")

        if org_col and value_col:
            top_org = (
                df.groupby(org_col, as_index=False)[value_col]
                .sum()
                .sort_values(value_col, ascending=False)
                .head(TOP_N)
            )
            top_org.insert(0, "Rank", range(1, len(top_org) + 1))

            st.dataframe(
                top_org,
                hide_index=True,
                use_container_width=True,
                height=220
            )
        else:
            st.info("ℹ️ Organization / Value column not found")

    # --- Top Cities ---
    with col2:
        st.subheader("🏙️ Top 5 Cities")

        if city_col:
            top_city = (
                df[city_col]
                .value_counts()
                .head(TOP_N)
                .reset_index()
            )
            top_city.columns = ["City", "Count"]
            top_city.insert(0, "Rank", range(1, len(top_city) + 1))

            st.dataframe(
                top_city,
                hide_index=True,
                use_container_width=True,
                height=220
            )
        else:
            st.info("ℹ️ City column not found")

    # -------- DATA PREVIEW --------
    st.subheader("📄 Data Preview")

    preview_df = df.head(100).reset_index(drop=True)
    preview_df.insert(0, "S.No", range(1, len(preview_df) + 1))

    st.dataframe(
        preview_df,
        hide_index=True,
        use_container_width=True,
        height=320
    )
