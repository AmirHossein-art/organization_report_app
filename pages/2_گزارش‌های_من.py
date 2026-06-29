import streamlit as st

from utils.ui import setup_page


setup_page(
    title="گزارش‌های من",
    icon="📄",
    layout="wide",
)


st.title("گزارش‌های من")
st.write("اینجا گزارش‌های ثبت‌شده کاربر نمایش داده می‌شود.")