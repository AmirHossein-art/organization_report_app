import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.ui import setup_page


setup_page(
    title="مدیریت کاربران",
    icon="👥",
    layout="wide",
)


require_manager()
show_user_sidebar()

st.title("مدیریت کاربران")

st.write("اینجا بعداً افزودن کاربر، تغییر رمز و فعال/غیرفعال کردن کاربران ساخته می‌شود.")