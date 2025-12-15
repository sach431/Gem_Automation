import streamlit as st

from screens.Dashboard import app as dashboard_page
from screens.Category_Search import app as category_page
from screens.Reports import app as reports_page
from screens.Master_Category import app as master_page

from services.date_filter import get_quarter_range


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Health Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------
# CALLBACKS (ONLY PLACE WHERE STATE CHANGES)
# ---------------------------------------------------------
def on_from_date_change():
    from_date = st.session_state.from_date

    if from_date:
        _, q_end, _ = get_quarter_range(from_date)
        st.session_state.to_date = q_end
        st.session_state.mode = "quarter"
    else:
        st.session_state.to_date = None
        st.session_state.mode = None


def on_to_date_change():
    if st.session_state.from_date:
        st.session_state.mode = "custom"


# ---------------------------------------------------------
# TOP BAR
# ---------------------------------------------------------
def top_bar():

    # -------- INIT STATE (BEFORE WIDGETS) --------
    st.session_state.setdefault("from_date", None)
    st.session_state.setdefault("to_date", None)
    st.session_state.setdefault("mode", None)

    col1, col2, col3 = st.columns([3, 1.5, 1.5])

    # -------- SEARCH --------
    with col1:
        search = st.text_input(
            "🔍 Search",
            placeholder="Search buyer, seller, item..."
        )

    # -------- FROM DATE --------
    with col2:
        st.date_input(
            "📅 From",
            key="from_date",
            format="YYYY/MM/DD",
            on_change=on_from_date_change
        )

    # -------- TO DATE --------
    with col3:
        st.date_input(
            "📅 To",
            key="to_date",
            format="YYYY/MM/DD",
            on_change=on_to_date_change
        )

    # -------- LABEL --------
    if st.session_state.from_date and st.session_state.to_date:
        if st.session_state.mode == "quarter":
            _, _, q_label = get_quarter_range(st.session_state.from_date)
            st.caption(f"📦 Auto Quarter Applied: **{q_label}**")
        elif st.session_state.mode == "custom":
            st.caption(
                f"🧾 Custom Period: "
                f"**{st.session_state.from_date.strftime('%Y/%m/%d')} → "
                f"{st.session_state.to_date.strftime('%Y/%m/%d')}**"
            )

    return (
        search,
        st.session_state.from_date,
        st.session_state.to_date,
        st.session_state.mode
    )


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("📌 Health Dashboard")

menu = st.sidebar.radio(
    "Go to",
    ["📊 Dashboard", "🔍 Category Search", "📄 Reports", "📂 Master Category"]
)


# ---------------------------------------------------------
# GLOBAL FILTERS
# ---------------------------------------------------------
search, start_date, end_date, mode = top_bar()


# ---------------------------------------------------------
# ROUTING
# ---------------------------------------------------------
if menu == "📊 Dashboard":
    dashboard_page(search, start_date, end_date, mode)

elif menu == "🔍 Category Search":
    category_page(search, start_date, end_date, mode)

elif menu == "📄 Reports":
    reports_page(search, start_date, end_date, mode)

elif menu == "📂 Master Category":
    master_page(search, start_date, end_date, mode)
