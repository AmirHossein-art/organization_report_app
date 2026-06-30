import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.ui import setup_page


setup_page(
    title="داشبورد مدیریتی",
    icon="📊",
    layout="wide",
)


require_manager()
show_user_sidebar()

st.title("داشبورد مدیریتی")

st.success("شما با نقش مدیر وارد شده‌اید.")

st.write("در این صفحه بعداً گزارش‌ها، پروژه‌ها، KPIها و خروجی‌ها نمایش داده می‌شوند.")