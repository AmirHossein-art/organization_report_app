from pathlib import Path

import pandas as pd
import streamlit as st

from utils.file_service import format_file_size

from utils.auth import require_manager, show_user_sidebar
from utils.format_helpers import (
    report_type_label,
    to_jalali_date,
    to_jalali_datetime,
    to_persian_digits,
)
from utils.manager_dashboard_service import (
    get_dashboard_filter_options,
    get_manager_dashboard_data,
)

from utils.export_service import build_dashboard_excel, build_dashboard_word

from utils.ui import setup_page

from utils.ai_service import analyze_reports_with_ai


setup_page(
    title="داشبورد مدیریتی",
    icon="📊",
    layout="wide",
)

require_manager()
show_user_sidebar()

st.title("داشبورد مدیریتی گزارش‌ها")

st.info(
    "در این داشبورد، وضعیت ثبت گزارش‌ها بر اساس بازه‌های تعریف‌شده، کاربران، پروژه‌ها و وضعیت تأخیر بررسی می‌شود."
)

filter_options = get_dashboard_filter_options()

periods = filter_options["periods"]
projects = filter_options["projects"]
users = filter_options["users"]

if not periods:
    st.warning("هنوز هیچ بازه گزارشی تعریف نشده است. ابتدا از صفحه مدیریت بازه‌های گزارش، بازه بسازید.")
    st.stop()

st.divider()

period_options = {
    (
        f"{period['title']} | "
        f"{report_type_label(period['report_type'])} | "
        f"{to_jalali_date(period['period_start'])} تا {to_jalali_date(period['period_end'])}"
    ): period["id"]
    for period in periods
}

project_options = {"همه پروژه‌ها": None}
project_options.update(
    {
        project["title"]: project["id"]
        for project in projects
    }
)

user_options = {"همه کاربران": None}
user_options.update(
    {
        f"{user['full_name']} | {user['username']}": user["id"]
        for user in users
    }
)

status_options = {
    "همه وضعیت‌ها": "all",
    "ثبت‌شده": "submitted",
    "تأخیری": "late",
    "ثبت‌نشده": "missing",
}

with st.container(border=True):
    st.subheader("فیلترها")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        selected_period_label = st.selectbox(
            "بازه گزارش",
            options=list(period_options.keys()),
        )

    with filter_col2:
        selected_status_label = st.selectbox(
            "وضعیت گزارش",
            options=list(status_options.keys()),
        )

    filter_col3, filter_col4 = st.columns(2)

    with filter_col3:
        selected_project_label = st.selectbox(
            "پروژه",
            options=list(project_options.keys()),
        )

    with filter_col4:
        selected_user_label = st.selectbox(
            "کاربر",
            options=list(user_options.keys()),
        )

selected_period_id = period_options[selected_period_label]
selected_project_id = project_options[selected_project_label]
selected_user_id = user_options[selected_user_label]
selected_status = status_options[selected_status_label]

dashboard_data = get_manager_dashboard_data(
    period_id=selected_period_id,
    project_id=selected_project_id,
    user_id=selected_user_id,
)

period = dashboard_data["period"]
summary = dashboard_data["summary"]
rows = dashboard_data["rows"]

if not period:
    st.error("بازه گزارش انتخاب‌شده پیدا نشد.")
    st.stop()

if selected_status != "all":
    rows = [
        row for row in rows
        if row["status_key"] == selected_status
    ]

st.divider()

st.subheader("خلاصه وضعیت")

metric_col1, metric_col2, metric_col3, metric_col4, metric_col5, metric_col6 = st.columns(6)

with metric_col1:
    st.metric(
        "مورد انتظار",
        to_persian_digits(summary.get("total_expected", 0)),
    )

with metric_col2:
    st.metric(
        "ثبت‌شده",
        to_persian_digits(summary.get("submitted_count", 0)),
    )

with metric_col3:
    st.metric(
        "ثبت‌نشده",
        to_persian_digits(summary.get("missing_count", 0)),
    )

with metric_col4:
    st.metric(
        "تأخیری",
        to_persian_digits(summary.get("late_count", 0)),
    )

with metric_col5:
    st.metric(
        "دارای پیوست",
        to_persian_digits(summary.get("with_files_count", 0)),
    )

with metric_col6:
    st.metric(
        "مشارکت",
        f"{to_persian_digits(summary.get('participation_rate', 0))}٪",
    )

st.caption(
    f"بازه انتخاب‌شده: {period['title']} | "
    f"{to_jalali_date(period['period_start'])} تا {to_jalali_date(period['period_end'])}"
)

st.divider()

if not rows:
    st.info("با فیلترهای انتخاب‌شده، داده‌ای برای نمایش وجود ندارد.")
    st.stop()


excel_bytes = build_dashboard_excel(
    period=period,
    rows=rows,
)

word_bytes = build_dashboard_word(
    period=period,
    summary=summary,
    rows=rows,
)

period_start_for_file = to_jalali_date(period["period_start"]).replace("/", "-")
period_end_for_file = to_jalali_date(period["period_end"]).replace("/", "-")

st.divider()
st.subheader("خروجی‌های داشبورد")

export_col1, export_col2 = st.columns(2)

with export_col1:
    # دکمه دانلود اکسل (بدون نیاز به AI)
    excel_bytes = build_dashboard_excel(period=period, rows=rows)
    st.download_button(
        label="دانلود خروجی Excel 📊",
        data=excel_bytes,
        file_name=f"manager_dashboard_{period_start_for_file}_to_{period_end_for_file}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with export_col2:
    # فرآیند تولید Word با AI
    if st.button("تحلیل با هوش مصنوعی و تولید Word 🤖", use_container_width=True):
        with st.spinner("هوش مصنوعی در حال تحلیل گزارش‌هاست... لطفاً چند لحظه صبر کنید."):
            
            # ۱. جمع‌آوری و فرمت‌بندی متن گزارش‌ها برای ارسال به AI
            reports_text_for_ai = ""
            for row in rows:
                if row["has_report"] and not row["is_late"]:
                    reports_text_for_ai += f"پروژه: {row['project_title']} | کاربر: {row['user_full_name']}\n"
                    reports_text_for_ai += f"فعالیت‌ها: {row.get('activities_done', '')}\n"
                    reports_text_for_ai += f"نتایج: {row.get('results_achieved', '')}\n"
                    reports_text_for_ai += f"چالش‌ها/اقدامات: {row.get('next_actions', '')}\n"
                    reports_text_for_ai += "-" * 20 + "\n"
            
            # ۲. دریافت تحلیل از AI
            ai_result = "گزارشی برای تحلیل یافت نشد."
            if reports_text_for_ai.strip():
                ai_result = analyze_reports_with_ai(period["title"], reports_text_for_ai)
            
            # ۳. ساخت فایل Word و ذخیره در سشن
            word_bytes = build_dashboard_word(
                period=period,
                summary=summary,
                rows=rows,
                ai_summary=ai_result
            )
            st.session_state["ready_word_bytes"] = word_bytes

    # اگر فایل آماده شده باشد، دکمه دانلود نمایش داده می‌شود
    if "ready_word_bytes" in st.session_state:
        st.success("تحلیل با موفقیت انجام شد! فایل Word آماده دانلود است.")
        st.download_button(
            label="دانلود فایل Word نهایی 📝",
            data=st.session_state["ready_word_bytes"],
            file_name=f"manager_dashboard_{period_start_for_file}_to_{period_end_for_file}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )


overview_rows = []

for row in rows:
    overview_rows.append(
        {
            "تعداد پیوست": to_persian_digits(row["file_count"]),
            "تاریخ ثبت": to_jalali_datetime(row["submitted_at"]) if row["submitted_at"] else "-",
            "وضعیت": row["status_label"],
            "پروژه": row["project_title"],
            "نام کاربری": row["username"],
            "کاربر": row["user_full_name"],
        }
    )

overview_df = pd.DataFrame(overview_rows)

submitted_rows = [
    row for row in rows
    if row["has_report"]
]

missing_rows = [
    row for row in rows
    if not row["has_report"]
]

late_rows = [
    row for row in rows
    if row["is_late"]
]

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "نمای کلی",
        "گزارش‌های ثبت‌شده",
        "ثبت‌نشده‌ها",
        "تأخیری‌ها",
    ]
)

with tab1:
    st.subheader("نمای کلی وضعیت کاربران و پروژه‌ها")

    st.dataframe(
        overview_df,
        use_container_width=True,
        hide_index=True,
    )

    status_counts = overview_df["وضعیت"].value_counts().reset_index()
    status_counts.columns = ["وضعیت", "تعداد"]

    st.markdown("#### نمودار وضعیت گزارش‌ها")
    st.bar_chart(
        status_counts,
        x="وضعیت",
        y="تعداد",
        use_container_width=True,
    )

with tab2:
    st.subheader("گزارش‌های ثبت‌شده")

    if not submitted_rows:
        st.info("گزارش ثبت‌شده‌ای برای فیلترهای انتخاب‌شده وجود ندارد.")
    else:
        submitted_display_rows = []

        for row in submitted_rows:
            submitted_display_rows.append(
                {
                    "کاربر": row["user_full_name"],
                    "پروژه": row["project_title"],
                    "وضعیت": row["status_label"],
                    "تاریخ ثبت": to_jalali_datetime(row["submitted_at"]),
                    "پیوست": to_persian_digits(row["file_count"]),
                    "فعالیت‌ها": row["activities_done"],
                    "نتایج": row["results_achieved"],
                    "اقدامات آتی": row["next_actions"],
                    "شاخص‌ها": row["kpi_text"],
                }
            )

        submitted_df = pd.DataFrame(submitted_display_rows)

        st.dataframe(
            submitted_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### جزئیات گزارش‌ها و پیوست‌ها")

        for row in submitted_rows:
            expander_title = (
                f"{row['user_full_name']} | "
                f"{row['project_title']} | "
                f"{row['status_label']} | "
                f"{to_jalali_datetime(row['submitted_at'])}"
            )

            with st.expander(expander_title):
                st.markdown("#### متن گزارش")

                detail_col1, detail_col2 = st.columns(2)

                with detail_col1:
                    with st.container(border=True):
                        st.markdown("##### فعالیت‌های انجام‌شده")
                        st.write(row["activities_done"] or "ثبت نشده")

                    with st.container(border=True):
                        st.markdown("##### اقدامات آتی")
                        st.write(row["next_actions"] or "ثبت نشده")

                with detail_col2:
                    with st.container(border=True):
                        st.markdown("##### نتایج حاصل‌شده")
                        st.write(row["results_achieved"] or "ثبت نشده")

                    with st.container(border=True):
                        st.markdown("##### شاخص‌ها")
                        st.write(row["kpi_text"] or "ثبت نشده")

                st.divider()

                st.markdown("#### فایل‌های پیوست")

                files = row.get("files", [])

                if not files:
                    st.info("برای این گزارش فایل پیوستی ثبت نشده است.")

                for file in files:
                    file_path = Path(file["file_path"])

                    with st.container(border=True):
                        st.write(f"**{file['original_filename']}**")
                        st.caption(f"حجم فایل: {format_file_size(file['file_size'])}")

                        if file_path.exists():
                            with open(file_path, "rb") as f:
                                file_bytes = f.read()

                            st.download_button(
                                label="دانلود فایل پیوست",
                                data=file_bytes,
                                file_name=file["original_filename"],
                                mime="application/octet-stream",
                                key=(
                                    f"manager_dashboard_report_{row['report_id']}"
                                    f"_file_{file['id']}"
                                ),
                            )
                        else:
                            st.warning(
                                "فایل در مسیر ذخیره‌شده پیدا نشد. "
                                "ممکن است فایل از پوشه uploads حذف شده باشد."
                            )

with tab3:
    st.subheader("کاربران / پروژه‌های بدون گزارش")

    if not missing_rows:
        st.success("برای فیلترهای انتخاب‌شده، مورد ثبت‌نشده‌ای وجود ندارد.")
    else:
        missing_display_rows = []

        for row in missing_rows:
            missing_display_rows.append(
                {
                    "کاربر": row["user_full_name"],
                    "نام کاربری": row["username"],
                    "پروژه": row["project_title"],
                    "بازه": row["period_title"],
                    "وضعیت": row["status_label"],
                }
            )

        missing_df = pd.DataFrame(missing_display_rows)

        st.dataframe(
            missing_df,
            use_container_width=True,
            hide_index=True,
        )

with tab4:
    st.subheader("گزارش‌های تأخیری")

    if not late_rows:
        st.success("برای فیلترهای انتخاب‌شده، گزارش تأخیری وجود ندارد.")
    else:
        late_display_rows = []

        for row in late_rows:
            late_display_rows.append(
                {
                    "پیوست": to_persian_digits(row["file_count"]),
                    "تاریخ ثبت": to_jalali_datetime(row["submitted_at"]),
                    "پروژه": row["project_title"],
                    "نام کاربری": row["username"],
                    "کاربر": row["user_full_name"],
                }
            )

        late_df = pd.DataFrame(late_display_rows)

        st.dataframe(
            late_df,
            use_container_width=True,
            hide_index=True,
        )