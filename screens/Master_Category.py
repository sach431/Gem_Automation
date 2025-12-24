import streamlit as st
import os

from services.category_folder import setup_category
from services.file_store import load_saved_excel, save_excel_file
from services.custom_pdf_extractor import extract_pdf_to_text
from services.gem_automation import run_gem_automation


# =========================================================
# MASTER CATEGORY – FINAL STABLE VERSION
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

        # ▶ START AUTOMATION (NO THREAD)
        with col1:
            if st.button("▶ Start GeM Download"):

                os.makedirs(base_dir, exist_ok=True)

                if os.path.exists(stop_file):
                    os.remove(stop_file)

                st.warning("Automation running. Do not refresh the page.")

                # IMPORTANT: Playwright must run in main thread
                run_gem_automation(
                    st.session_state.selected_category,
                    stop_file
                )

        # ⏹ STOP AUTOMATION
        with col2:
            if st.button("⏹ Stop Download"):
                os.makedirs(base_dir, exist_ok=True)
                with open(stop_file, "w") as f:
                    f.write("STOP")
                st.warning("Stop signal sent")

        # ℹ INFO
        with col3:
            st.info("Semi-automation mode")
            st.caption("Manual captcha")
            st.caption("Inline PDF capture")
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

    # ---------------- TAB 2: MANUAL PDF ----------------
    with tab2:
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf_file:
            extracted_text = extract_pdf_to_text(pdf_file)
            if extracted_text:
                st.text_area(
                    "Extracted Clean Text",
                    extracted_text,
                    height=300
                )
