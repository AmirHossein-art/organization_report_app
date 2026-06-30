import streamlit as st

from utils.auth import current_user, require_login, show_user_sidebar
from utils.project_service import get_active_projects
from utils.report_service import create_report
from utils.ui import setup_page
from utils.file_service import save_uploaded_files

from utils.deadline_service import get_report_timing_status
from utils.format_helpers import to_jalali_datetime


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
    فعلاً ثبت گزارش متنی فعال است و در مرحله بعد آپلود فایل نیز اضافه می‌شود.
    """
)

st.divider()


projects = get_active_projects()

if not projects:
    st.warning("هیچ پروژه فعالی تعریف نشده است. ابتدا مدیر باید پروژه فعال ایجاد کند.")
    st.stop()


project_options = {
    project["title"]: project["id"]
    for project in projects
}


report_type_options = {
    "گزارش هفتگی": "weekly",
    "گزارش ماهانه": "monthly",
}


with st.form("submit_report_form"):
    selected_report_type_label = st.selectbox(
        "نوع گزارش",
        options=list(report_type_options.keys()),
    )

    selected_project_title = st.selectbox(
        "پروژه",
        options=list(project_options.keys()),
    )

    col1, col2 = st.columns(2)

    with col1:
        period_start = st.date_input("تاریخ شروع دوره")

    with col2:
        period_end = st.date_input("تاریخ پایان دوره")

    activities_done = st.text_area(
        "فعالیت‌های انجام‌شده",
        height=160,
        placeholder="کارهایی که در این دوره انجام داده‌اید را وارد کنید.",
    )

    results_achieved = st.text_area(
        "نتایج حاصل‌شده",
        height=140,
        placeholder="نتایج، خروجی‌ها یا دستاوردهای این دوره را وارد کنید.",
    )

    next_actions = st.text_area(
        "اقدامات آتی",
        height=140,
        placeholder="برنامه‌ها و اقدامات بعدی را وارد کنید.",
    )

    kpi_text = st.text_area(
        "شاخص‌ها",
        height=140,
        placeholder="شاخص‌های مرتبط با پروژه یا گزارش را وارد کنید.",
    )

    uploaded_files = st.file_uploader(
        "فایل‌های پیوست گزارش",
        type=["pdf", "doc", "docx", "xls", "xlsx"],
        accept_multiple_files=True,
        help="فرمت‌های مجاز: PDF، Word و Excel",
    )

    submitted = st.form_submit_button("ثبت گزارش")


if submitted:
    selected_report_type = report_type_options[selected_report_type_label]
    selected_project_id = project_options[selected_project_title]

    success, message, report_id = create_report(
        user_id=user["id"],
        project_id=selected_project_id,
        report_type=selected_report_type,
        period_start=period_start,
        period_end=period_end,
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