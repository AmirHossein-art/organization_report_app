import pandas as pd
import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.format_helpers import (
    report_type_label,
    to_jalali_date,
    to_persian_digits,
)
from utils.report_period_service import (
    create_report_period,
    delete_report_period,
    get_all_report_periods,
    toggle_report_period_status,
    update_report_period,
)
from utils.ui import setup_page


setup_page(
    title="مدیریت بازه‌های گزارش",
    icon="📅",
    layout="wide",
)

require_manager()
show_user_sidebar()

st.title("مدیریت بازه‌های گزارش")

st.info(
    "از این بخش، مدیر بازه‌های مجاز گزارش‌دهی را تعریف می‌کند. "
)

period_flash = st.session_state.get("period_flash")

if period_flash:
    if period_flash.get("type") == "success":
        st.success(period_flash.get("message"))
    else:
        st.error(period_flash.get("message"))

    st.session_state.pop("period_flash", None)

st.divider()

report_type_options = {
    "هفتگی": "weekly",
    "ماهانه": "monthly",
}

with st.container(border=True):
    st.subheader("ساخت بازه گزارش جدید")

    with st.form("create_report_period_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(
                "عنوان بازه",
                placeholder="مثلاً هفته اول تیر ۱۴۰۵",
            )

        with col2:
            report_type_label_value = st.selectbox(
                "نوع گزارش",
                options=list(report_type_options.keys()),
            )

        date_col1, date_col2 = st.columns(2)

        with date_col1:
            period_start = st.date_input("تاریخ شروع بازه")

        with date_col2:
            period_end = st.date_input("تاریخ پایان بازه")

        description = st.text_area(
            "توضیحات",
            placeholder="اختیاری",
            height=100,
        )

        submitted = st.form_submit_button("ساخت بازه گزارش")

    if submitted:
        success, message = create_report_period(
            title=title,
            report_type=report_type_options[report_type_label_value],
            period_start=period_start,
            period_end=period_end,
            description=description,
        )

        if success:
            st.session_state["period_flash"] = {
                "type": "success",
                "message": message,
            }
            st.rerun()
        else:
            st.session_state["period_flash"] = {
                "type": "error",
                "message": message,
            }
            st.rerun()

st.divider()

st.subheader("بازه‌های تعریف‌شده")

periods = get_all_report_periods()

if not periods:
    st.info("هنوز هیچ بازه گزارشی تعریف نشده است.")
    st.stop()

display_rows = []

for period in periods:
    display_rows.append(
        {
            "وضعیت": "فعال" if period["is_active"] else "غیرفعال",
            "پایان بازه": to_jalali_date(period["period_end"]),
            "شروع بازه": to_jalali_date(period["period_start"]),
            "نوع گزارش": report_type_label(period["report_type"]),
            "عنوان": period["title"],
            "شناسه": to_persian_digits(period["id"]),
        }
    )

display_df = pd.DataFrame(display_rows)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)

st.markdown("### ویرایش و مدیریت بازه‌ها")

reverse_report_type_options = {
    "weekly": "هفتگی",
    "monthly": "ماهانه",
}

for period in periods:
    status_text = "فعال" if period["is_active"] else "غیرفعال"

    title_text = (
        f"{period['title']} - {report_type_label(period['report_type'])} - "
        f"{to_jalali_date(period['period_start'])} تا {to_jalali_date(period['period_end'])} - "
        f"{status_text}"
    )

    with st.expander(title_text):
        st.markdown("#### ویرایش بازه گزارش")

        report_type_labels = list(report_type_options.keys())
        current_report_type_label = reverse_report_type_options.get(
            period["report_type"],
            "هفتگی",
        )

        if current_report_type_label in report_type_labels:
            default_report_type_index = report_type_labels.index(current_report_type_label)
        else:
            default_report_type_index = 0

        with st.form(f"edit_report_period_form_{period['id']}"):
            edit_col1, edit_col2 = st.columns(2)

            with edit_col1:
                edited_title = st.text_input(
                    "عنوان بازه",
                    value=period["title"],
                    key=f"edit_period_title_{period['id']}",
                )

            with edit_col2:
                edited_report_type_label = st.selectbox(
                    "نوع گزارش",
                    options=report_type_labels,
                    index=default_report_type_index,
                    key=f"edit_period_type_{period['id']}",
                )

            date_col1, date_col2 = st.columns(2)

            with date_col1:
                edited_period_start = st.date_input(
                    "تاریخ شروع بازه",
                    value=period["period_start"],
                    key=f"edit_period_start_{period['id']}",
                )

            with date_col2:
                edited_period_end = st.date_input(
                    "تاریخ پایان بازه",
                    value=period["period_end"],
                    key=f"edit_period_end_{period['id']}",
                )

            edited_description = st.text_area(
                "توضیحات",
                value=period["description"],
                height=100,
                key=f"edit_period_description_{period['id']}",
            )

            edited_is_active = st.toggle(
                "فعال بودن این بازه",
                value=period["is_active"],
                key=f"edit_period_is_active_{period['id']}",
            )

            save_period_edit = st.form_submit_button("ذخیره ویرایش بازه")

        if save_period_edit:
            success, message = update_report_period(
                period_id=period["id"],
                title=edited_title,
                report_type=report_type_options[edited_report_type_label],
                period_start=edited_period_start,
                period_end=edited_period_end,
                description=edited_description,
                is_active=edited_is_active,
            )

            if success:
                st.session_state["period_flash"] = {
                    "type": "success",
                    "message": message,
                }
                st.rerun()
            else:
                st.session_state["period_flash"] = {
                    "type": "error",
                    "message": message,
                }
                st.rerun()

        st.divider()

        st.markdown("#### عملیات سریع")

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            button_label = "غیرفعال کردن بازه" if period["is_active"] else "فعال کردن بازه"

            if st.button(button_label, key=f"toggle_period_{period['id']}"):
                success, message = toggle_report_period_status(period["id"])

                if success:
                    st.session_state["period_flash"] = {
                        "type": "success",
                        "message": message,
                    }
                    st.rerun()
                else:
                    st.session_state["period_flash"] = {
                        "type": "error",
                        "message": message,
                    }
                    st.rerun()

        with action_col2:
            delete_confirm = st.checkbox(
                "حذف این بازه را تأیید می‌کنم",
                key=f"confirm_delete_period_{period['id']}",
            )

            if st.button(
                "حذف بازه",
                key=f"delete_period_{period['id']}",
                disabled=not delete_confirm,
            ):
                success, message = delete_report_period(period["id"])

                if success:
                    st.session_state["period_flash"] = {
                        "type": "success",
                        "message": message,
                    }
                    st.rerun()
                else:
                    st.session_state["period_flash"] = {
                        "type": "error",
                        "message": message,
                    }
                    st.rerun()