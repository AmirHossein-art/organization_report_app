from html import escape

from pathlib import Path
from utils.file_service import format_file_size

import pandas as pd
import streamlit as st

from utils.auth import current_user, require_login, show_user_sidebar
from utils.format_helpers import (
    report_period_label,
    report_status_label,
    report_type_label,
    to_jalali_datetime,
    to_persian_digits,
)
from utils.ui import setup_page

from utils.user_project_service import get_assigned_projects_for_user
from utils.report_service import get_reports_by_user, update_report
from utils.deadline_service import get_report_timing_status

setup_page(
    title="گزارش‌های من",
    icon="📄",
    layout="wide",
)


require_login()
show_user_sidebar()

user = current_user()

st.title("گزارش‌های من")

reports = get_reports_by_user(user["id"])

assigned_projects = get_assigned_projects_for_user(user["id"])

project_options = {
    project["title"]: project["id"]
    for project in assigned_projects
}

project_titles = list(project_options.keys())

report_type_options = {
    "هفتگی": "weekly",
    "ماهانه": "monthly",
}

reverse_report_type_options = {
    "weekly": "هفتگی",
    "monthly": "ماهانه",
}

if not reports:
    st.info("هنوز گزارشی ثبت نکرده‌اید.")
    st.stop()


# -----------------------------
# Filters
# -----------------------------
st.markdown("### فیلتر گزارش‌ها")

project_titles = sorted({report["project_title"] for report in reports})
report_types = sorted({report["report_type"] for report in reports})
report_statuses = sorted({report["status"] for report in reports})

min_period_start = min(report["period_start"] for report in reports)
max_period_end = max(report["period_end"] for report in reports)

with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        search_text = st.text_input(
            "جستجو در پروژه یا متن گزارش",
            placeholder="مثلاً عنوان پروژه، فعالیت، نتیجه یا شاخص",
        )

    with col2:
        selected_project = st.selectbox(
            "پروژه",
            options=["همه پروژه‌ها"] + project_titles,
        )

    col3, col4, col5 = st.columns(3)

    with col3:
        selected_report_type = st.selectbox(
            "نوع گزارش",
            options=["همه انواع"] + [report_type_label(item) for item in report_types],
        )

    with col4:
        selected_status = st.selectbox(
            "وضعیت",
            options=["همه وضعیت‌ها"] + [report_status_label(item) for item in report_statuses],
        )

    with col5:
        period_range = st.date_input(
            "بازه تاریخ دوره",
            value=(min_period_start, max_period_end),
        )


filtered_reports = reports.copy()


# Search filter
if search_text.strip():
    query = search_text.strip().lower()

    filtered_reports = [
        report
        for report in filtered_reports
        if query in (report["project_title"] or "").lower()
        or query in (report["activities_done"] or "").lower()
        or query in (report["results_achieved"] or "").lower()
        or query in (report["next_actions"] or "").lower()
        or query in (report["kpi_text"] or "").lower()
    ]


# Project filter
if selected_project != "همه پروژه‌ها":
    filtered_reports = [
        report
        for report in filtered_reports
        if report["project_title"] == selected_project
    ]


# Report type filter
if selected_report_type != "همه انواع":
    filtered_reports = [
        report
        for report in filtered_reports
        if report_type_label(report["report_type"]) == selected_report_type
    ]


# Status filter
if selected_status != "همه وضعیت‌ها":
    filtered_reports = [
        report
        for report in filtered_reports
        if report_status_label(report["status"]) == selected_status
    ]


# Period range filter
if isinstance(period_range, tuple) and len(period_range) == 2:
    range_start, range_end = period_range

    filtered_reports = [
        report
        for report in filtered_reports
        if report["period_start"] >= range_start
        and report["period_end"] <= range_end
    ]


st.divider()

st.markdown(
    f"### نتیجه فیلتر: {to_persian_digits(len(filtered_reports))} گزارش"
)

if not filtered_reports:
    st.warning("هیچ گزارشی با فیلترهای انتخاب‌شده پیدا نشد.")
    st.stop()


# -----------------------------
# Summary table
# -----------------------------

def render_rtl_table(df: pd.DataFrame) -> str:
    columns = list(df.columns)

    header_html = "".join(
        f"<th>{escape(str(column))}</th>"
        for column in columns
    )

    rows_html = ""

    for _, row in df.iterrows():
        cells_html = "".join(
            f"<td>{escape(str(row[column]))}</td>"
            for column in columns
        )

        rows_html += f"<tr>{cells_html}</tr>"

    return f"""
    <table class="rtl-custom-table">
        <thead>
            <tr>{header_html}</tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """

reports_df = pd.DataFrame(filtered_reports)

reports_df["نوع گزارش"] = reports_df["report_type"].apply(report_type_label)
reports_df["وضعیت"] = reports_df["status"].apply(report_status_label)
reports_df["دوره"] = reports_df.apply(
    lambda row: report_period_label(row["period_start"], row["period_end"]),
    axis=1,
)
reports_df["تاریخ ثبت"] = reports_df["submitted_at"].apply(to_jalali_datetime)
reports_df["شناسه"] = reports_df["id"].apply(to_persian_digits)

display_df = reports_df[
    [
        "تاریخ ثبت",
        "وضعیت",
        "دوره",
        "نوع گزارش",
        "project_title",
        "شناسه",
    ]
].rename(
    columns={
        "project_title": "پروژه",
    }
)

display_df = display_df[
    [
        "شناسه",
        "پروژه",
        "نوع گزارش",
        "دوره",
        "وضعیت",
        "تاریخ ثبت",
    ]
]

st.markdown(
    render_rtl_table(display_df),
    unsafe_allow_html=True,
)


st.divider()


# -----------------------------
# Report detail cards
# -----------------------------

st.markdown("### جزئیات گزارش‌ها")

def safe_html(value) -> str:
    if value is None:
        return "ثبت نشده"

    text = str(value).strip()

    if not text:
        return "ثبت نشده"

    return escape(text)


def show_mini_info_card(title: str, value: str):
    st.markdown(
        f"""
        <div class="report-info-card">
            <div class="report-info-title">{safe_html(title)}</div>
            <div class="report-info-value">{safe_html(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_report_text_card(title: str, content: str | None):
    st.markdown(
        f"""
        <div class="report-text-card">
            <div class="report-text-card-title">{safe_html(title)}</div>
            <div class="report-text-card-content">{safe_html(content)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for report in filtered_reports:
    report_type = report_type_label(report["report_type"])
    status = report_status_label(report["status"])
    period = report_period_label(report["period_start"], report["period_end"])
    submitted_at = to_jalali_datetime(report["submitted_at"])
    report_id = to_persian_digits(report["id"])

    report_flash = st.session_state.get("report_edit_flash")
    should_expand = bool(
        report_flash and report_flash.get("report_id") == report["id"]
    )

    with st.expander(
        f"{report['project_title']} - {report_type} - {period}",
        expanded=should_expand,
    ):
        with st.container(border=True):
            st.markdown(f"### {report['project_title']}")

            info_col1, info_col2, info_col3 = st.columns(3)

            with info_col1:
                show_mini_info_card("شناسه", report_id)

            with info_col2:
                show_mini_info_card("نوع گزارش", report_type)

            with info_col3:
                show_mini_info_card("وضعیت", status)

            info_col4, info_col5 = st.columns(2)

            with info_col4:
                show_mini_info_card("دوره", period)

            with info_col5:
                show_mini_info_card("تاریخ ثبت", submitted_at)

            st.divider()

            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                show_report_text_card(
                    "فعالیت‌های انجام‌شده",
                    report["activities_done"],
                )

            with row1_col2:
                show_report_text_card(
                    "نتایج حاصل‌شده",
                    report["results_achieved"],
                )

            row2_col1, row2_col2 = st.columns(2)

            with row2_col1:
                show_report_text_card(
                    "اقدامات آتی",
                    report["next_actions"],
                )

            with row2_col2:
                show_report_text_card(
                    "شاخص‌ها",
                    report["kpi_text"],
                )

            files = report.get("files", [])

            if files:
                st.markdown("#### فایل‌های پیوست")

                for file in files:
                    file_path = Path(file["file_path"])

                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()

                        st.download_button(
                            label=f"دانلود {file['original_filename']} ({format_file_size(file['file_size'])})",
                            data=file_bytes,
                            file_name=file["original_filename"],
                            mime="application/octet-stream",
                            key=f"download_file_{file['id']}",
                        )
                    else:
                        st.warning(f"فایل «{file['original_filename']}» در مسیر ذخیره‌شده پیدا نشد.")
            else:
                st.info("برای این گزارش فایل پیوستی ثبت نشده است.")

            st.divider()

            st.markdown("#### ویرایش گزارش")

            # پیام موفقیت یا خطای ویرایش، بعد از rerun همین‌جا نمایش داده می‌شود
            report_flash = st.session_state.get("report_edit_flash")

            if report_flash and report_flash.get("report_id") == report["id"]:
                if report_flash.get("type") == "success":
                    st.success(report_flash.get("message"))
                else:
                    st.error(report_flash.get("message"))

                st.session_state.pop("report_edit_flash", None)


            # بررسی اینکه این گزارش هنوز در مهلت مجاز ویرایش هست یا نه
            timing_status = get_report_timing_status(
                report_type=report["report_type"],
                period_end=report["period_end"],
            )

            if not timing_status["can_submit_or_edit"]:
                st.warning(timing_status["message"])

                deadline_at = timing_status.get("deadline_at")
                closes_at = timing_status.get("closes_at")

                if deadline_at and closes_at:
                    st.caption(
                        f"مهلت اصلی: {to_jalali_datetime(deadline_at)} | "
                        f"زمان قفل شدن نهایی: {to_jalali_datetime(closes_at)}"
                    )

            else:
                current_project_title = report["project_title"]
                project_titles = list(project_options.keys())

                if not project_titles:
                    st.warning(
                        "هیچ پروژه فعالی برای شما تعریف نشده است. "
                        "امکان ویرایش پروژه گزارش وجود ندارد."
                    )

                else:
                    if current_project_title not in project_options:
                        st.warning(
                            "پروژه این گزارش در حال حاضر جزو پروژه‌های مجاز یا فعال شما نیست. "
                            "برای ذخیره ویرایش، باید یکی از پروژه‌های مجاز خود را انتخاب کنید."
                        )

                    if current_project_title in project_titles:
                        default_project_index = project_titles.index(current_project_title)
                    else:
                        default_project_index = 0

                    with st.form(f"edit_report_form_{report['id']}"):
                        edited_project_title = st.selectbox(
                            "پروژه",
                            options=project_titles,
                            index=default_project_index,
                            key=f"edit_project_{report['id']}",
                        )

                        edited_activities_done = st.text_area(
                            "فعالیت‌های انجام‌شده",
                            value=report["activities_done"],
                            height=130,
                            key=f"edit_activities_{report['id']}",
                        )

                        edited_results_achieved = st.text_area(
                            "نتایج حاصل‌شده",
                            value=report["results_achieved"],
                            height=130,
                            key=f"edit_results_{report['id']}",
                        )

                        edited_next_actions = st.text_area(
                            "اقدامات آتی",
                            value=report["next_actions"],
                            height=130,
                            key=f"edit_next_actions_{report['id']}",
                        )

                        edited_kpi_text = st.text_area(
                            "شاخص‌ها",
                            value=report["kpi_text"],
                            height=130,
                            key=f"edit_kpi_{report['id']}",
                        )

                        save_edit = st.form_submit_button("ذخیره ویرایش گزارش")

                    if save_edit:
                        edited_project_id = project_options[edited_project_title]

                        success, message = update_report(
                            report_id=report["id"],
                            user_id=user["id"],
                            project_id=edited_project_id,
                            activities_done=edited_activities_done,
                            results_achieved=edited_results_achieved,
                            next_actions=edited_next_actions,
                            kpi_text=edited_kpi_text,
                        )

                        if success:
                            st.session_state["report_edit_flash"] = {
                                "report_id": report["id"],
                                "type": "success",
                                "message": "تغییرات گزارش با موفقیت ذخیره شد.",
                            }
                            st.rerun()
                        else:
                            st.session_state["report_edit_flash"] = {
                                "report_id": report["id"],
                                "type": "error",
                                "message": message,
                            }
                            st.rerun()

                if success:
                    st.session_state["report_edit_flash"] = {
                        "report_id": report["id"],
                        "type": "success",
                        "message": "تغییرات گزارش با موفقیت ذخیره شد.",
                    }
                    st.rerun()
                else:
                    st.session_state["report_edit_flash"] = {
                        "report_id": report["id"],
                        "type": "error",
                        "message": message,
                    }
                    st.rerun()