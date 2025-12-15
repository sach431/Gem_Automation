import streamlit as st
import pandas as pd

from services.file_store import load_saved_excel
from services.date_filter import apply_date_filter


# =========================================================
# DATE COLUMN DETECTION (ROBUST)
# =========================================================
def detect_date_column(df):
    patterns = ["date", "orderdate", "order_date", "created", "timestamp"]

    for c in df.columns:
        name = c.lower().replace(" ", "")
        if any(p in name for p in patterns):
            df[c] = pd.to_datetime(df[c], errors="coerce")
            if df[c].dropna().any():
                return c

    for c in df.columns:
        sample = df[c].dropna().astype(str).head(15)
        parsed = pd.to_datetime(sample, errors="coerce")
        if parsed.notna().mean() >= 0.6:
            df[c] = pd.to_datetime(df[c], errors="coerce")
            if df[c].dropna().any():
                return c

    return None


# =========================================================
# GENERIC COLUMN FINDER
# =========================================================
def detect_column(df, keywords):
    cols = {c.lower(): c for c in df.columns}
    for key in keywords:
        for c in cols:
            if key in c:
                return cols[c]
    return None


# =========================================================
# MAIN REPORTS PAGE
# =========================================================
def app(search=None, start_date=None, end_date=None, mode=None):

    st.markdown("## 📄 Reports & Insights")
    st.caption("Generate dynamic reports from uploaded Excel data")

    # ---------------- LOAD DATA ----------------
    df = load_saved_excel()
    if df is None or df.empty:
        st.warning("⚠ Please upload Excel in **Master Category** first.")
        return

    df = df.copy()
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
        # ✅ Date blank → FULL DATA
        filtered = df.copy()

    # ---------------- GLOBAL SEARCH ----------------
    if search and search.strip():
        s = search.lower()
        filtered = filtered[
            filtered.apply(
                lambda r: r.astype(str).str.lower().str.contains(s).any(),
                axis=1
            )
        ]

    if filtered.empty:
        st.info("ℹ️ No data found for selected filters.")
        return

    # ---------------- SMART COLUMN DETECTION ----------------
    category_col = detect_column(filtered, ["category", "brand", "type", "segment"])
    city_col     = detect_column(filtered, ["city", "state", "district", "location"])
    seller_col   = detect_column(filtered, ["seller", "buyer", "name", "firm"])
    value_col    = detect_column(filtered, ["value", "amount", "price", "total"])

    text_cols = filtered.select_dtypes(include="object").columns.tolist()
    if not category_col:
        category_col = text_cols[0]
    if not city_col:
        city_col = text_cols[0]
    if not seller_col:
        seller_col = text_cols[0]

    if not value_col:
        filtered["_auto_value"] = 1
        value_col = "_auto_value"

    # ---------------- REPORT CONTROLS ----------------
    st.subheader("📝 Report Configuration")

    c1, c2 = st.columns([2, 1])

    with c1:
        report_type = st.selectbox(
            "Report Type",
            [
                "Summary",
                "Detailed",
                "Category-wise",
                "City-wise",
                "Seller-wise",
                "Custom Columns"
            ]
        )

        selected_columns = st.multiselect(
            "Select Columns (for Detailed / Custom)",
            filtered.columns.tolist(),
            default=filtered.columns.tolist()[:6]
        )

    # ---------------- GENERATE REPORT ----------------
    if st.button("🚀 Generate Report"):

        if report_type in ["Detailed", "Custom Columns"]:
            report_df = (
                filtered[selected_columns]
                if selected_columns else filtered
            )

        elif report_type == "Summary":
            report_df = pd.DataFrame({
                "Metric": ["Total Records", "Total Value"],
                "Value": [
                    len(filtered),
                    filtered[value_col].sum()
                ]
            })

        elif report_type == "Category-wise":
            report_df = (
                filtered.groupby(category_col)[value_col]
                .sum()
                .reset_index(name="Total Value")
                .sort_values("Total Value", ascending=False)
            )

        elif report_type == "City-wise":
            report_df = (
                filtered.groupby(city_col)[value_col]
                .sum()
                .reset_index(name="Total Value")
                .sort_values("Total Value", ascending=False)
            )

        elif report_type == "Seller-wise":
            report_df = (
                filtered.groupby(seller_col)[value_col]
                .sum()
                .reset_index(name="Total Value")
                .sort_values("Total Value", ascending=False)
            )

        st.success("✅ Report generated successfully")

        st.download_button(
            "⬇️ Download Report",
            data=report_df.to_csv(index=False).encode("utf-8"),
            file_name="reports_output.csv",
            mime="text/csv"
        )

        st.markdown("### 📑 Report Preview")
        st.dataframe(report_df, use_container_width=True)

    # ---------------- RAW DATA PREVIEW ----------------
    st.divider()
    st.subheader("📊 Filtered Data Preview")
    st.dataframe(filtered, use_container_width=True)
