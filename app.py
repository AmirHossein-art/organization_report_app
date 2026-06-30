import streamlit as st

from utils.auth import (
    current_user,
    init_auth_state,
    is_logged_in,
    show_login_form,
    show_user_sidebar,
)

from utils.ui import setup_page


setup_page(
    title="سامانه گزارش‌دهی سازمانی",
    icon="📊",
    layout="wide",
)


init_auth_state()

init_auth_state()

if not is_logged_in():
    show_login_form()
    st.stop()


show_user_sidebar()

user = current_user()

st.title("سامانه گزارش‌دهی سازمانی")

st.success(f"{user['full_name']} عزیز، خوش آمدید.")

st.markdown("در نسخه اول، امکانات اصلی زیر پیاده‌سازی خواهد شد:")
st.markdown(
    """
    <ul class="rtl-bullet-list">
        <li>ورود کاربران با نام کاربری و رمز عبور</li>
        <li>ثبت گزارش هفتگی و ماهانه</li>
        <li>آپلود فایل گزارش</li>
        <li>مدیریت پروژه‌ها</li>
        <li>تنظیم ددلاین گزارش‌دهی</li>
        <li>داشبورد مدیریتی و خروجی اکسل</li>
    </ul>
    """,
    unsafe_allow_html=True,
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("تعداد کاربران", "کمتر از ۵۰ نفر")

with col2:
    st.metric("نوع گزارش‌ها", "هفتگی / ماهانه")

with col3:
    st.metric("وضعیت پروژه", "مرحله شروع")

st.info("ورود به سامانه با موفقیت انجام شده است.")