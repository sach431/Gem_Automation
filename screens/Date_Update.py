# screens/Date_Update.py
import streamlit as st
import os
import pandas as pd

def app():
    st.title("Data Update Module")

    st.info("Upload a new Excel file to update dataset. File will overwrite data/gem_orders_clean.xlsx (keep backup!).")

    uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
    if uploaded is not None:
        # save uploaded
        save_path = "data/gem_orders_clean.xlsx"
        df = pd.read_excel(uploaded, engine="openpyxl")
        df.to_excel(save_path, index=False)
        st.success("File uploaded and replaced dataset.")
        st.write("Rows:", len(df))
