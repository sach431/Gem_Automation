import streamlit as st
import os
import subprocess
import sys

from services.category_folder import setup_category
from services.file_store import load_saved_excel, save_excel_file
from services.custom_pdf_extractor import extract_pdf_structured_data


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

        base_dir = os.path.join(
            os.getcwd(),
            "downloads",
            st.session_state.selected_category.lower()
        )
        stop_file = os.path.join(base_dir, "STOP")

        col1, col2, col3 = st.columns(3)

        # ▶ START
        with col1:
            if st.button("▶ Start GeM Download"):
                os.makedirs(base_dir, exist_ok=True)

                if os.path.exists(stop_file):
                    os.remove(stop_file)

                st.warning("Automation running. Do not refresh.")

                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "services.gem_automation",
                        st.session_state.selected_category
                    ],
                    cwd=os.getcwd()
                )

        # ⏹ STOP
        with col2:
            if st.button("⏹ Stop Download"):
                os.makedirs(base_dir, exist_ok=True)
                with open(stop_file, "w") as f:
                    f.write("STOP")
                st.warning("Stop signal sent")

        # ℹ INFO
        with col3:
            st.info("Semi-automation mode")
            st.caption("Manual captcha required")
            st.caption("Unlimited PDFs")
            st.caption("Client safe")

    else:
        st.info("Please select a category first")

    st.divider()

    # =====================================================
    # TABS
    # =====================================================
    tab1, tab2 = st.tabs(
        ["📁 Upload Excel", "📄 Manual PDF Extract"]
    )

    # ---------------- TAB 1: EXCEL UPLOAD ----------------
    with tab1:
        excel_file = st.file_uploader("Upload Excel", type=["xls", "xlsx"])
        if excel_file:
            df = save_excel_file(excel_file)
            if df is not None:
                st.dataframe(df.head(200), width="stretch")
                st.success("Excel uploaded successfully")

        saved_df = load_saved_excel()
        if saved_df is not None:
            st.subheader("Last Saved Excel")
            st.dataframe(saved_df.head(200), width="stretch")

    # ---------------- TAB 2: MANUAL PDF EXTRACT (FINAL) ----------------
    with tab2:
        st.subheader("📄 Manual PDF Extract (Final Output)")

        uploaded_pdfs = st.file_uploader(
            "Upload one or more GeM Contract PDFs",
            type=["pdf"],
            accept_multiple_files=True
        )

        if uploaded_pdfs:
            import pandas as pd
            from io import BytesIO

            structured_rows = []

            for idx, pdf_file in enumerate(uploaded_pdfs, start=1):
                st.markdown(f"### 📘 {idx}. {pdf_file.name}")

                # 🔥 ONE-LINE FINAL EXTRACTION
                data = extract_pdf_structured_data(pdf_file)

                if not any(data.values()):
                    st.warning("❌ No valid data extracted from this PDF")
                    continue

                data["PDF Name"] = pdf_file.name
                structured_rows.append(data)

            # ---------------- PREVIEW + EXCEL ----------------
            if structured_rows:
                df = pd.DataFrame(structured_rows)

                st.subheader("📊 Extracted Contract Data")
                st.dataframe(df, width="stretch")

                buffer = BytesIO()
                df.to_excel(buffer, index=False)
                buffer.seek(0)

                st.download_button(
                    label="⬇️ Download Final Structured Excel",
                    data=buffer,
                    file_name="GEM_Final_Structured_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
