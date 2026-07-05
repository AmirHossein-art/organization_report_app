import pandas as pd
import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.format_helpers import to_persian_digits
from utils.project_service import get_active_projects
from utils.ui import setup_page
from utils.user_project_service import (
    get_assigned_project_ids_for_user,
    get_users_for_project_assignment,
    save_user_project_assignments,
)


setup_page(
    title="تخصیص پروژه‌ها",
    icon="👥",
    layout="wide",
)

require_manager()
show_user_sidebar()

st.title("تخصیص پروژه‌ها به کاربران")

st.info(
    "در این صفحه مشخص می‌کنید هر کاربر مجاز است برای کدام پروژه‌ها گزارش ثبت کند. "
    "کاربر در صفحه ثبت گزارش فقط پروژه‌های تخصیص‌داده‌شده به خودش را می‌بیند."
)

assignment_flash = st.session_state.get("assignment_flash")

if assignment_flash:
    if assignment_flash.get("type") == "success":
        st.success(assignment_flash.get("message"))
    else:
        st.error(assignment_flash.get("message"))

    st.session_state.pop("assignment_flash", None)

st.divider()

users = get_users_for_project_assignment()
projects = get_active_projects()

if not users:
    st.warning("هیچ کاربر فعالی برای تخصیص پروژه پیدا نشد.")
    st.stop()

if not projects:
    st.warning("هیچ پروژه فعالی وجود ندارد. ابتدا از صفحه مدیریت پروژه‌ها پروژه تعریف کنید.")
    st.stop()

user_options = {
    f"{user['full_name']} | {user['username']}": user["id"]
    for user in users
}

selected_user_label = st.selectbox(
    "انتخاب کاربر",
    options=list(user_options.keys()),
)

selected_user_id = user_options[selected_user_label]

assigned_project_ids = get_assigned_project_ids_for_user(selected_user_id)

project_options = {
    f"{project['title']}": project["id"]
    for project in projects
}

default_selected_project_labels = [
    label
    for label, project_id in project_options.items()
    if project_id in assigned_project_ids
]

with st.container(border=True):
    st.subheader("پروژه‌های مجاز برای این کاربر")

    with st.form(f"user_project_assignment_form_{selected_user_id}"):
        selected_project_labels = st.multiselect(
            "پروژه‌ها",
            options=list(project_options.keys()),
            default=default_selected_project_labels,
            help="کاربر فقط برای پروژه‌های انتخاب‌شده می‌تواند گزارش ثبت کند.",
        )

        submitted = st.form_submit_button("ذخیره تخصیص پروژه‌ها")

    if submitted:
        selected_project_ids = [
            project_options[label]
            for label in selected_project_labels
        ]

        success, message = save_user_project_assignments(
            user_id=selected_user_id,
            selected_project_ids=selected_project_ids,
        )

        if success:
            st.session_state["assignment_flash"] = {
                "type": "success",
                "message": message,
            }
            st.rerun()
        else:
            st.session_state["assignment_flash"] = {
                "type": "error",
                "message": message,
            }
            st.rerun()

st.divider()

st.subheader("خلاصه تخصیص‌های فعلی")

summary_rows = []

for user in users:
    user_project_ids = get_assigned_project_ids_for_user(user["id"])

    assigned_titles = [
        project["title"]
        for project in projects
        if project["id"] in user_project_ids
    ]

    summary_rows.append(
        {
            "کاربر": user["full_name"],
            "نام کاربری": user["username"],
            "تعداد پروژه‌ها": to_persian_digits(len(assigned_titles)),
            "پروژه‌ها": "، ".join(assigned_titles) if assigned_titles else "بدون پروژه",
        }
    )

summary_df = pd.DataFrame(summary_rows)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
)