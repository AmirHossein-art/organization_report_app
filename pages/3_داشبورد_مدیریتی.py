import streamlit as st

from utils.ui import setup_page


setup_page(
    title="داشبورد مدیریتی",
    icon="📊",
    layout="wide",
)


st.title("داشبورد مدیریتی")
st.write("اینجا داشبورد مدیر و KPIها نمایش داده می‌شود.")