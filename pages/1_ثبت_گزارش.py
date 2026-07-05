import streamlit as st

from utils.auth import current_user, require_login, show_user_sidebar
from utils.user_project_service import get_assigned_projects_for_user
from utils.report_service import create_report
from utils.ui import setup_page
from utils.file_service import save_uploaded_files

from utils.report_period_service import get_open_report_periods_for_submission
from utils.format_helpers import report_period_label, to_jalali_date

from utils.deadline_service import get_report_timing_status


setup_page(
    title="ثبت گزارش",
    icon="📝",
    layout="wide",
)


require_login()
show_user_sidebar()

user = current_user()

st.title("ثبت گزارش")

st.markdown(
    """
    در این صفحه می‌توانید گزارش هفتگی یا ماهانه خود را ثبت کنید.
    """
)

st.divider()


projects = get_assigned_projects_for_user(user["id"])

if not projects:
    st.warning(
        "هیچ پروژه‌ای برای شما تعریف نشده است. "
        "برای ثبت گزارش، مدیر باید ابتدا پروژه‌های مجاز شما را مشخص کند."
    )
    st.stop()


project_options = {
    project["title"]: project["id"]
    for project in projects
}


report_type_options = {
    "گزارش هفتگی": "weekly",
    "گزارش ماهانه": "monthly",
}

selected_report_type_label = st.selectbox(
    "نوع گزارش",
    options=list(report_type_options.keys()),
)

selected_report_type = report_type_options[selected_report_type_label]

open_periods = get_open_report_periods_for_submission(selected_report_type)

if not open_periods:
    st.warning("در حال حاضر هیچ بازه فعالی برای ثبت این نوع گزارش وجود ندارد.")
    st.stop()

period_options = {
    f"{period['title']} | {to_jalali_date(period['period_start'])} تا {to_jalali_date(period['period_end'])}": period["id"]
    for period in open_periods
}

with st.form("submit_report_form"):
    selected_period_label = st.selectbox(
        "بازه گزارش",
        options=list(period_options.keys()),
    )

    selected_period_id = period_options[selected_period_label]

    selected_project_title = st.selectbox(
        "پروژه",
        options=list(project_options.keys()),
    )

    selected_project_id = project_options[selected_project_title]

    activities_done = st.text_area(
        "فعالیت‌های انجام‌شده",
        height=160,
    )

    results_achieved = st.text_area(
        "نتایج حاصل‌شده",
        height=160,
    )

    next_actions = st.text_area(
        "اقدامات آتی",
        height=160,
    )

    kpi_text = st.text_area(
        "شاخص‌ها",
        height=160,
    )

    uploaded_files = st.file_uploader(
        "فایل‌های پیوست گزارش",
        type=["pdf", "doc", "docx", "xls", "xlsx"],
        accept_multiple_files=True,
        help="فرمت‌های مجاز: PDF، Word و Excel",
    )

    submitted = st.form_submit_button("ثبت گزارش")

if submitted:
    success, message, report_id = create_report(
        user_id=user["id"],
        project_id=selected_project_id,
        report_type=selected_report_type,
        period_id=selected_period_id,
        activities_done=activities_done,
        results_achieved=results_achieved,
        next_actions=next_actions,
        kpi_text=kpi_text,
    )

    if success:
        if uploaded_files:
            files_success, files_message = save_uploaded_files(
                report_id=report_id,
                uploaded_files=uploaded_files,
            )

            if files_success:
                st.success(f"{message} {files_message}")
            else:
                st.warning(
                    f"{message} اما در ذخیره فایل‌ها مشکل وجود داشت: {files_message}"
                )
        else:
            st.success(message)
    else:
        st.error(message)