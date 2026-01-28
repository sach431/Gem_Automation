import streamlit as st
import os
import subprocess
import sys
import pandas as pd

from services.category_folder import setup_category
from services.file_store import load_saved_excel, save_excel_file
from services.custom_pdf_extractor import (
    extract_pdf_structured_data,
    generate_powerbi_tables
)


# =========================================================
# MASTER CATEGORY – FINAL CLIENT-READY VERSION
# =========================================================
def app(search=None, start_date=None, end_date=None, quarter=None):

    st.header("📂 Master Category & Data Management")

    # =====================================================
    # SESSION STATE
    # =====================================================
    if "categories" not in st.session_state:
        st.session_state.categories = ["Malaria", "Dengue", "Typhoid", "Other"]

    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None

    categories = st.session_state.categories

    # =====================================================
    # CATEGORY SELECT
    # =====================================================
    selected_category = st.selectbox(
        "Select Category",
        categories,
        index=categories.index(st.session_state.selected_category)
        if st.session_state.selected_category in categories else 0
    )

    if selected_category:
        pdf_dir, excel_dir = setup_category(selected_category)
        st.session_state.selected_category = selected_category

        st.success(f"Category ready: {selected_category}")
        st.caption(f"PDF Folder   : {pdf_dir}")
        st.caption(f"Excel Folder : {excel_dir}")

    st.divider()

    # =====================================================
    # GEM ASSISTED PDF AUTOMATION
    # =====================================================
    st.subheader("📥 GeM Assisted PDF Downloader")

    if st.session_state.selected_category:

        category = st.session_state.selected_category
        base_dir = os.path.join(os.getcwd(), "downloads", category)
        stop_file = os.path.join(base_dir, "STOP")

        col1, col2, col3 = st.columns(3)

        # ▶ START AUTOMATION
        with col1:
            if st.button("▶ Start GeM Download"):
                os.makedirs(base_dir, exist_ok=True)

                if os.path.exists(stop_file):
                    os.remove(stop_file)

                st.warning("Automation running. Do not refresh this page.")

                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "services.gem_automation",
                        category
                    ],
                    cwd=os.getcwd()
                )

        # ⏹ STOP AUTOMATION
        with col2:
            if st.button("⏹ Stop Download"):
                os.makedirs(base_dir, exist_ok=True)
                with open(stop_file, "w") as f:
                    f.write("STOP")

                st.warning("Stop signal sent. Automation will stop safely.")

        # ℹ INFO
        with col3:
            st.info("Semi-automation mode")
            st.caption("Manual CAPTCHA required")
            st.caption("Unlimited PDFs")
            st.caption("Client-safe approach")

    else:
        st.info("Please select a category first")

    st.divider()

    # =====================================================
    # TABS
    # =====================================================
    tab_upload, tab_pdf = st.tabs(
        ["📁 Upload Excel", "📄 Manual PDF Extract"]
    )

    # ---------------- TAB 1: EXCEL UPLOAD ----------------
    with tab_upload:
        excel_file = st.file_uploader("Upload Excel", type=["xls", "xlsx"])
        if excel_file:
            df = save_excel_file(excel_file)
            if df is not None:
                df = df.reset_index(drop=True)
                df.insert(0, "S.No", range(1, len(df) + 1))

                st.dataframe(
                    df.head(200),
                    hide_index=True,
                    use_container_width=True
                )
                st.success("Excel uploaded successfully")

        saved_df = load_saved_excel()
        if saved_df is not None:
            st.subheader("Last Saved Excel")

            saved_df = saved_df.reset_index(drop=True)
            saved_df.insert(0, "S.No", range(1, len(saved_df) + 1))

            st.dataframe(
                saved_df.head(200),
                hide_index=True,
                use_container_width=True
            )

    # ---------------- TAB 2: MANUAL PDF EXTRACT ----------------
    with tab_pdf:
        st.subheader("📄 Manual PDF Extract (Final Output)")

        uploaded_pdfs = st.file_uploader(
            "Upload one or more GeM Contract PDFs",
            type=["pdf"],
            accept_multiple_files=True
        )

        if uploaded_pdfs:
            from io import BytesIO

            structured_rows = []

            for idx, pdf_file in enumerate(uploaded_pdfs, start=1):
                st.markdown(f"### 📘 {idx}. {pdf_file.name}")

                data = extract_pdf_structured_data(pdf_file)

                if not any(data.values()):
                    st.warning("No valid data extracted from this PDF")
                    continue

                structured_rows.append(data)

            if structured_rows:
                powerbi_tables = generate_powerbi_tables(structured_rows)

                df = pd.DataFrame(structured_rows)

                excluded_cols = [
                    "Generated Date",
                    "Ministry",
                    "PDF Name",
                    "Buyer GSTIN"
                ]

                df_display = df.drop(
                    columns=[c for c in excluded_cols if c in df.columns],
                    errors="ignore"
                )

                df_display = df_display.reset_index(drop=True)
                df_display.insert(0, "S.No", range(1, len(df_display) + 1))

                st.subheader("📊 Extracted Contract Data")
                st.dataframe(
                    df_display,
                    hide_index=True,
                    use_container_width=True
                )

                st.subheader("📈 Power BI Ready Tables")

                t1, t2, t3, t4 = st.tabs([
                    "Dim_Buyer",
                    "Dim_Seller",
                    "Dim_Product",
                    "Fact_Contract_Sales"
                ])

                for key, tab in zip(
                    ["Dim_Buyer", "Dim_Seller", "Dim_Product", "Fact_Contract_Sales"],
                    [t1, t2, t3, t4]
                ):
                    with tab:
                        table_df = powerbi_tables[key].reset_index(drop=True)
                        table_df.insert(0, "S.No", range(1, len(table_df) + 1))

                        st.dataframe(
                            table_df,
                            hide_index=True,
                            use_container_width=True
                        )

                col1, col2 = st.columns(2)

                with col1:
                    buffer = BytesIO()
                    df_display.to_excel(buffer, index=False)
                    buffer.seek(0)

                    st.download_button(
                        "⬇️ Download Original Excel",
                        data=buffer,
                        file_name="GEM_Final_Structured_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col2:
                    buffer_pbi = BytesIO()
                    with pd.ExcelWriter(buffer_pbi, engine="xlsxwriter") as writer:
                        for key in [
                            "Dim_Buyer",
                            "Dim_Seller",
                            "Dim_Product",
                            "Fact_Contract_Sales"
                        ]:
                            temp_df = powerbi_tables[key].reset_index(drop=True)
                            temp_df.insert(0, "S.No", range(1, len(temp_df) + 1))
                            temp_df.to_excel(writer, sheet_name=key, index=False)

                    buffer_pbi.seek(0)

                    st.download_button(
                        "⬇️ Download Power BI Excel",
                        data=buffer_pbi,
                        file_name="GEM_PowerBI_Tables.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
