import pandas as pd
import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.project_service import (
    create_project,
    get_all_projects,
    toggle_project_status,
    update_project,
)
from utils.ui import setup_page



setup_page(
    title="مدیریت پروژه‌ها",
    icon="📁",
    layout="wide",
)


require_manager()
show_user_sidebar()


st.title("مدیریت پروژه‌ها")

st.markdown(
    """
    در این صفحه می‌توانید پروژه‌های سازمان را تعریف، ویرایش یا غیرفعال کنید.
    کاربران هنگام ثبت گزارش، یکی از پروژه‌های فعال را انتخاب خواهند کرد.
    """
)


# -----------------------------
# Flash message after rerun
# -----------------------------
if "project_flash" in st.session_state:
    flash_type, flash_message = st.session_state.pop("project_flash")

    if flash_type == "success":
        st.success(flash_message)
    elif flash_type == "error":
        st.error(flash_message)
    elif flash_type == "warning":
        st.warning(flash_message)
    else:
        st.info(flash_message)


st.divider()


# -----------------------------
# Add new project
# -----------------------------
st.subheader("افزودن پروژه جدید")

with st.form("create_project_form"):
    new_title = st.text_input("عنوان پروژه")
    new_description = st.text_area("توضیحات پروژه", height=120)

    submitted = st.form_submit_button("ثبت پروژه")

if submitted:
    success, message = create_project(
        title=new_title,
        description=new_description,
    )

    if success:
        st.session_state["project_flash"] = ("success", message)
        st.rerun()
    else:
        st.error(message)


st.divider()


# -----------------------------
# Projects list
# -----------------------------
st.subheader("لیست پروژه‌ها")

projects = get_all_projects(include_inactive=True)

if not projects:
    st.info("هنوز پروژه‌ای ثبت نشده است.")
    st.stop()


projects_df = pd.DataFrame(projects)

projects_df["وضعیت"] = projects_df["is_active"].apply(
    lambda value: "فعال" if value else "غیرفعال"
)

# Streamlit columns are visually rendered LTR.
# To make the rightmost column "شناسه", we give the columns in reverse order.
display_df = projects_df[
    [
        "وضعیت",
        "description",
        "title",
        "id",
    ]
].rename(
    columns={
        "id": "شناسه",
        "title": "عنوان پروژه",
        "description": "توضیحات",
    }
)

styled_df = (
    display_df.style
    .set_properties(**{
        "text-align": "right",
        "direction": "rtl",
        "font-family": "Vazirmatn",
    })
    .set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("text-align", "right"),
                    ("direction", "rtl"),
                    ("font-family", "Vazirmatn"),
                ],
            }
        ]
    )
)

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    column_order=[
        "وضعیت",
        "توضیحات",
        "عنوان پروژه",
        "شناسه",
    ],
)

st.divider()


# -----------------------------
# Edit projects
# -----------------------------
st.subheader("ویرایش پروژه‌ها")

for project in projects:
    status_label = "فعال" if project["is_active"] else "غیرفعال"
    status_icon = "✅" if project["is_active"] else "⛔"

    with st.expander(f"{project['title']} - {status_icon} {status_label}"):

        st.caption(
            f"وضعیت فعلی پروژه: {status_icon} {status_label}"
        )

        with st.form(f"edit_project_form_{project['id']}"):
            edited_title = st.text_input(
                "عنوان پروژه",
                value=project["title"],
                key=f"title_{project['id']}",
            )

            edited_description = st.text_area(
                "توضیحات پروژه",
                value=project["description"],
                height=120,
                key=f"description_{project['id']}",
            )

            edited_is_active = st.checkbox(
                "پروژه فعال باشد",
                value=project["is_active"],
                key=f"is_active_{project['id']}_{int(project['is_active'])}",
            )

            col1, col2 = st.columns(2)

            with col1:
                save_changes = st.form_submit_button("ذخیره تغییرات")

            with col2:
                toggle_status = st.form_submit_button(
                    "تغییر وضعیت فعال/غیرفعال"
                )

        if save_changes:
            success, message = update_project(
                project_id=project["id"],
                title=edited_title,
                description=edited_description,
                is_active=edited_is_active,
            )

            if success:
                st.session_state["project_flash"] = (
                    "success",
                    f"{message} پروژه «{edited_title}» به‌روزرسانی شد."
                )
                st.rerun()
            else:
                st.error(message)

        if toggle_status:
            success, message = toggle_project_status(project["id"])

            if success:
                st.session_state["project_flash"] = ("success", message)
                st.rerun()
            else:
                st.error(message)