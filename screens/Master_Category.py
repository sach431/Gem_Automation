import streamlit as st
import webbrowser
import subprocess
import sys
import os

from services.excel_export import export_to_excel
from services.extractor import extract_pdf_to_table
from services.file_store import load_saved_excel, save_excel_file
from services.category_folder import setup_category
from services.pdf_to_excel import convert_pdfs_to_excel


# =========================================================
# MASTER CATEGORY SCREEN (FINAL)
# =========================================================
def app(search, start_date, end_date, quarter):

    st.header("📂 Master Category & Data Management")

    # =========================================================
    # CATEGORY SELECTION
    # =========================================================
    if "categories" not in st.session_state:
        st.session_state["categories"] = [
            "Malaria", "Dengue", "Typhoid", "Other"
        ]

    categories = st.session_state["categories"]

    selected_category = st.selectbox(
        "Select Category",
        categories
    )

    # =========================================================
    # CATEGORY FOLDER SETUP
    # =========================================================
    if selected_category:
        pdf_dir, excel_dir = setup_category(selected_category)

        st.session_state["selected_category"] = selected_category
        st.session_state["pdf_dir"] = pdf_dir
        st.session_state["excel_dir"] = excel_dir

        st.success(f"Category ready: {selected_category}")
        st.caption(f"PDF Folder: {pdf_dir}")
        st.caption(f"Excel Folder: {excel_dir}")

    st.divider()

    # =========================================================
    # MAIN ACTION BUTTONS
    # =========================================================
    col1, col2, col3 = st.columns(3)

    # ---------- Open GeM Website ----------
    with col1:
        if st.button("🌐 Open GeM Website"):
            webbrowser.open("https://gem.gov.in/view_contracts")
            st.info(
                "Steps on GeM Website:\n"
                "1. Select date range & category\n"
                "2. Solve captcha and search\n"
                "3. Open contract → solve captcha again\n"
                "4. Keep PDF viewer OPEN\n\n"
                "⚠️ Do NOT close browser tab"
            )

    # ---------- Start PDF Auto Download ----------
    with col2:
        if st.button("📥 Start PDF Auto Download"):
            pdf_dir = st.session_state.get("pdf_dir")

            if not pdf_dir:
                st.error("Please select a category first.")
            else:
                st.warning(
                    "Captcha automation is NOT supported.\n"
                    "Complete captcha manually on GeM website.\n"
                    "Automation will download PDFs AFTER captcha verification."
                )

                creationflags = (
                    subprocess.CREATE_NEW_CONSOLE
                    if os.name == "nt" else 0
                )

                subprocess.Popen(
                    [
                        sys.executable,
                        os.path.join("services", "run_gem_downloader.py"),
                        pdf_dir
                    ],
                    creationflags=creationflags
                )

                st.success("PDF download process started.")

    # ---------- Convert PDFs to Excel ----------
    with col3:
        if st.button("📊 Convert PDFs to Excel"):
            pdf_dir = st.session_state.get("pdf_dir")
            excel_dir = st.session_state.get("excel_dir")
            category = st.session_state.get("selected_category")

            if not pdf_dir or not excel_dir:
                st.error("Category folders are not ready.")
            elif not os.listdir(pdf_dir):
                st.warning("No PDFs found in the selected category folder.")
            else:
                with st.spinner("Converting PDFs to Excel..."):
                    output = convert_pdfs_to_excel(
                        pdf_dir, excel_dir, category
                    )

                if output:
                    st.success(f"Excel generated successfully: {output}")
                else:
                    st.warning("No valid tables found in PDFs.")

    st.divider()

    # =========================================================
    # TABS
    # =========================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Upload Excel",
        "📄 PDF Extractor",
        "📂 Manage Categories",
        "🛠 Data Update"
    ])

    # =========================================================
    # TAB 1 — UPLOAD EXCEL
    # =========================================================
    with tab1:
        st.subheader("Upload Excel File")

        excel_file = st.file_uploader(
            "Upload Excel",
            type=["xls", "xlsx"]
        )

        if excel_file:
            with st.spinner("Saving file..."):
                saved_df = save_excel_file(excel_file)

            if saved_df is not None:
                st.session_state["uploaded_excel_data"] = saved_df
                st.dataframe(
                    saved_df.head(200),
                    use_container_width=True
                )
                st.success("Excel uploaded and saved successfully.")
            else:
                st.error("Failed to save Excel file.")

        st.markdown("---")
        saved_df = load_saved_excel()
        if saved_df is not None:
            st.dataframe(
                saved_df.head(200),
                use_container_width=True
            )

    # =========================================================
    # TAB 2 — MANUAL PDF EXTRACTION (OPTIONAL)
    # =========================================================
    with tab2:
        st.subheader("Manual PDF Table Extraction")

        pdf_file = st.file_uploader(
            "Upload Single PDF",
            type=["pdf"],
            key="pdf_extract_master"
        )

        if pdf_file:
            with st.spinner("Extracting PDF..."):
                df = extract_pdf_to_table(pdf_file)

            st.dataframe(df.head(200), use_container_width=True)

            if st.button("Export Extracted Excel"):
                filename = export_to_excel(
                    df,
                    f"{selected_category}_manual_pdf"
                )
                st.success(f"Download ready: {filename}")

    # =========================================================
    # TAB 3 — MANAGE CATEGORIES
    # =========================================================
    with tab3:
        st.subheader("Manage Categories")

        for idx, cat in enumerate(categories):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(f"{idx + 1}. {cat}")
            with c2:
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    categories.pop(idx)
                    st.experimental_rerun()

        new_cat = st.text_input("Add New Category")
        if st.button("Add Category"):
            if new_cat.strip() and new_cat not in categories:
                categories.append(new_cat.strip())
                st.success(f"Category added: {new_cat}")
                st.experimental_rerun()
            else:
                st.warning("Invalid or duplicate category.")

    # =========================================================
    # TAB 4 — FUTURE MODULE
    # =========================================================
    with tab4:
        st.info("Future data update module placeholder.")
