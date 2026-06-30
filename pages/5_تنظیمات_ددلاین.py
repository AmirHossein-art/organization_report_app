import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.ui import setup_page


setup_page(
    title="تنظیمات ددلاین",
    icon="⏰",
    layout="wide",
)


require_manager()
show_user_sidebar()

st.title("تنظیمات ددلاین")

st.write("اینجا بعداً ددلاین هفتگی و ماهانه تنظیم می‌شود.")