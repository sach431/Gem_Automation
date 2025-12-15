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
# MAIN APP
# =========================================================
def app(search=None, start_date=None, end_date=None, mode=None):

    st.markdown("## 🔍 Category Search")
    st.caption("Filter data dynamically based on uploaded Excel")

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
        # ✅ From blank → FULL DATA
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
        st.info("ℹ️ No records found.")
        return

    # ---------------- AUTO COLUMN DETECTION ----------------
    category_col = detect_column(filtered, ["category", "brand", "type", "segment"])
    city_col     = detect_column(filtered, ["city", "state", "district", "location"])
    name_col     = detect_column(filtered, ["seller", "buyer", "name", "firm"])
    value_col    = detect_column(filtered, ["amount", "value", "price", "total"])

    text_cols = filtered.select_dtypes(include="object").columns.tolist()

    if not category_col:
        category_col = text_cols[0]
    if not city_col:
        city_col = text_cols[0]
    if not name_col:
        name_col = text_cols[0]

    if not value_col:
        filtered["_auto_value"] = 1
        value_col = "_auto_value"

    # ---------------- FILTER PANEL ----------------
    left, right = st.columns([1, 3])

    with left:
        st.subheader("🎯 Filters")

        selected_categories = st.multiselect(
            "Category",
            sorted(filtered[category_col].dropna().unique())
        )

        selected_city = st.selectbox(
            "City",
            ["All"] + sorted(filtered[city_col].dropna().unique())
        )

        name_search = st.text_input("Seller / Buyer / Firm")

    # ---------------- APPLY FILTERS ----------------
    if selected_categories:
        filtered = filtered[filtered[category_col].isin(selected_categories)]

    if selected_city != "All":
        filtered = filtered[filtered[city_col] == selected_city]

    if name_search.strip():
        filtered = filtered[
            filtered[name_col].astype(str)
            .str.contains(name_search, case=False, na=False)
        ]

    if filtered.empty:
        st.info("ℹ️ No data after applying filters.")
        return

    # ---------------- RESULTS ----------------
    with right:
        st.subheader("📊 Results")

        c1, c2 = st.columns(2)
        c1.metric("Total Records", f"{len(filtered):,}")
        c2.metric("Total Value", f"{filtered[value_col].sum():,.0f}")

        st.markdown("---")
        st.dataframe(filtered, use_container_width=True)

        st.download_button(
            "⬇️ Download Excel",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="category_search_output.csv",
            mime="text/csv"
        )
