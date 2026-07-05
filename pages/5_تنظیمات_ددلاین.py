import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.deadline_service import (
    get_all_deadline_settings,
    update_deadline_setting,
)
from utils.format_helpers import to_persian_digits
from utils.ui import setup_page


setup_page(
    title="تنظیمات ددلاین",
    icon="⏰",
    layout="wide",
)


require_manager()
show_user_sidebar()

st.title("تنظیمات ددلاین گزارش‌دهی")

st.markdown(
    """
    در این صفحه می‌توانید ددلاین ثبت و ویرایش گزارش‌ها را تنظیم کنید.
    
    منطق فعلی:
    """
)

st.markdown(
    """
    <ul class="rtl-bullet-list">
        <li>ددلاین بر اساس تاریخ بازه‌‌های درنظر گرفته شده محاسبه می‌شود.</li>
        <li>اگر گزارش بعد از ددلاین اصلی ولی قبل از پایان مهلت اضافه ثبت یا ویرایش شود، تأخیری محسوب می‌شود.</li>
        <li>بعد از پایان مهلت اضافه، ثبت و ویرایش بسته می‌شود.</li>
    </ul>
    """,
    unsafe_allow_html=True,
)

st.divider()

deadline_flash = st.session_state.get("deadline_flash")

if deadline_flash:
    if deadline_flash.get("type") == "success":
        st.success(deadline_flash.get("message"))
    else:
        st.error(deadline_flash.get("message"))

    st.session_state.pop("deadline_flash", None)

report_type_labels = {
    "weekly": "گزارش هفتگی",
    "monthly": "گزارش ماهانه",
}


settings = get_all_deadline_settings()

for setting in settings:
    report_type = setting["report_type"]
    title = report_type_labels.get(report_type, report_type)

    with st.container(border=True):
        st.subheader(title)

        if setting["is_active"]:
            st.markdown(
                '<span class="status-chip status-chip-active">ددلاین فعال است</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-chip status-chip-inactive">ددلاین غیرفعال است</span>',
                unsafe_allow_html=True,
            )

        with st.form(f"deadline_setting_form_{report_type}"):
            col1, col2 = st.columns(2)

            with col1:
                deadline_time = st.time_input(
                    "ساعت پایان مهلت اصلی",
                    value=setting["deadline_time"],
                    key=f"deadline_time_{report_type}",
                    help="مهلت اصلی در تاریخ پایان بازه گزارش و در این ساعت بسته می‌شود.",
                )

            with col2:
                grace_days = st.number_input(
                    "مهلت اضافه بعد از مهلت اصلی چند روز باشد؟",
                    min_value=0,
                    max_value=30,
                    value=int(setting["grace_days"]),
                    step=1,
                    key=f"grace_days_{report_type}",
                    help="در این مدت گزارش هنوز قابل ثبت یا ویرایش است، ولی تأخیری محسوب می‌شود.",
                )

            st.markdown("")

            is_active = st.toggle(
                "فعال‌سازی محدودیت زمانی برای این نوع گزارش",
                value=setting["is_active"],
                key=f"is_active_deadline_{report_type}",
            )

            submitted = st.form_submit_button("ذخیره تنظیمات")

        if submitted:
            success, message = update_deadline_setting(
                report_type=report_type,
                deadline_time=deadline_time,
                grace_days=int(grace_days),
                is_active=is_active,
            )

            if success:
                st.session_state["deadline_flash"] = {
                    "type": "success",
                    "message": "تنظیمات ددلاین با موفقیت ذخیره شد.",
                }
                st.rerun()
            else:
                st.session_state["deadline_flash"] = {
                    "type": "error",
                    "message": message,
                }
                st.rerun()

        st.caption(
            f"تنظیم فعلی: مهلت اصلی ثبت و ویرایش، در تاریخ پایان بازه گزارش "
            f"و ساعت {to_persian_digits(setting['deadline_time'].strftime('%H:%M'))} است. "
            f"بعد از آن، تا {to_persian_digits(setting['grace_days'])} روز مهلت اضافه وجود دارد "
            f"و گزارش تأخیری محسوب می‌شود."
        )