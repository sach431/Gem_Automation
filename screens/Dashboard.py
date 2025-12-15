import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from services.file_store import load_saved_excel
from services.date_filter import apply_date_filter

# ----------------- GLOBAL CSS -----------------
st.markdown("""
<style>
h1, h2, h3, h4, h5, h6 {
    text-transform: uppercase !important;
    font-weight:700 !important;
}
.block-container { font-size: 15px !important; }
section[data-testid="stSidebar"] { font-size: 15px !important; }
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
        if any(p in c.lower().replace(" ", "") for p in patterns):
            df[c] = pd.to_datetime(df[c], errors="coerce")
            if df[c].dropna().any():
                df["Year"] = df[c].dt.year
                return c
    return None


def detect_columns(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    text_cols = df.select_dtypes(include=["object"]).columns.tolist()

    value_col = next(
        (c for c in df.columns if any(k in c.lower() for k in ["amount", "value", "price", "total"])),
        numeric_cols[0] if numeric_cols else None
    )

    seller_col = next(
        (c for c in text_cols if any(k in c.lower() for k in ["seller", "buyer", "company", "name"])),
        None
    )

    city_col = next(
        (c for c in text_cols if any(k in c.lower() for k in ["city", "state", "district"])),
        None
    )

    return value_col, seller_col, city_col


def apply_search_filter(df, search):
    if not search:
        return df
    s = search.lower()
    return df[df.apply(lambda r: s in r.astype(str).str.lower().to_string(), axis=1)]


# ----------------- MAIN APP -----------------
def app(search=None, start_date=None, end_date=None, mode=None):

    st.header("📊 KPI Dashboard")

    # ---------------- LOAD DATA ----------------
    df = load_saved_excel()
    if df is None or df.empty:
        st.warning("⚠ Upload an Excel in Master Category first.")
        return

    df = sanitize_strings(df.copy())
    df.columns = df.columns.str.strip()

    # ---------------- DATE COLUMN ----------------
    date_col = detect_date_column(df)

    # ---------------- APPLY DATE FILTER ----------------
    if date_col and start_date is not None and mode is not None:

        filtered, label, d1, d2 = apply_date_filter(
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
    else:
        # ✅ From blank → FULL DATA
        filtered = df.copy()

    # ---------------- SEARCH ----------------
    filtered = apply_search_filter(filtered, search)

    if filtered.empty:
        st.info("ℹ️ No data available.")
        return

    # ---------------- KPI ----------------
    value_col, seller_col, city_col = detect_columns(filtered)

    if value_col:
        filtered[value_col] = pd.to_numeric(filtered[value_col], errors="coerce")

    total_records = len(filtered)
    total_value = filtered[value_col].sum() if value_col else 0
    avg_value = filtered[value_col].mean() if value_col else 0

    top_seller = "N/A"
    if seller_col:
        m = filtered[seller_col].dropna().mode()
        if not m.empty:
            top_seller = m.iloc[0]

    st.subheader("📈 Key Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", total_records)
    c2.metric("Total Value", f"{total_value:,.0f}")
    c3.metric("Average Value", f"{avg_value:,.2f}")
    c4.metric("Top Seller", top_seller)

    st.divider()

    # ---------------- TABLES ----------------
    left, right = st.columns(2)

    with left:
        st.write("### Top Sellers")
        if seller_col and value_col:
            ts = (
                filtered.groupby(seller_col)[value_col]
                .sum()
                .sort_values(ascending=False)
                .head(8)
                .reset_index()
            )
            st.dataframe(ts, use_container_width=True)

    with right:
        st.write("### Top Cities")
        if city_col:
            tc = filtered[city_col].value_counts().head(8).reset_index()
            tc.columns = ["City", "Count"]
            st.dataframe(tc, use_container_width=True)

    st.divider()

    st.subheader("📄 Data Preview")
    st.dataframe(filtered.head(200), use_container_width=True)
