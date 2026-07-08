import pandas as pd
import streamlit as st

from utils.auth import require_manager, show_user_sidebar
from utils.format_helpers import to_persian_digits
from utils.ui import setup_page
from utils.user_service import (
    create_user_by_manager,
    get_all_users,
    reset_user_password_by_manager,
    toggle_user_status,
    update_user_by_manager,
)


setup_page(
    title="مدیریت کاربران",
    icon="👤",
    layout="wide",
)

require_manager()
show_user_sidebar()

st.title("مدیریت کاربران")

st.info(
    "در این صفحه می‌توانید کاربر جدید بسازید، رمز موقت تعریف کنید، "
    "رمز کاربران را بازنشانی کنید و کاربران را فعال یا غیرفعال کنید."
)

user_flash = st.session_state.get("user_flash")

if user_flash:
    if user_flash.get("type") == "success":
        st.success(user_flash.get("message"))
    else:
        st.error(user_flash.get("message"))

    st.session_state.pop("user_flash", None)

st.divider()


role_options = {
    "کاربر عادی": "user",
    "مدیر": "manager",
}


with st.container(border=True):
    st.subheader("ساخت کاربر جدید")

    with st.form("create_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "نام کاربری",
                placeholder="مثلاً ahmadi",
            )

        with col2:
            full_name = st.text_input(
                "نام و نام خانوادگی",
                placeholder="مثلاً علی احمدی",
            )

        col3, col4 = st.columns(2)

        with col3:
            role_label = st.selectbox(
                "نقش کاربر",
                options=list(role_options.keys()),
            )

        with col4:
            temporary_password = st.text_input(
                "رمز اولیه",
                value="123456",
                type="password",
            )

        must_change_password = st.checkbox(
            "کاربر در اولین ورود مجبور به تغییر رمز باشد",
            value=True,
        )

        submitted = st.form_submit_button("ساخت کاربر")

    if submitted:
        success, message = create_user_by_manager(
            username=username,
            full_name=full_name,
            role=role_options[role_label],
            temporary_password=temporary_password,
            must_change_password=must_change_password,
        )

        if success:
            st.session_state["user_flash"] = {
                "type": "success",
                "message": message,
            }
            st.rerun()
        else:
            st.session_state["user_flash"] = {
                "type": "error",
                "message": message,
            }
            st.rerun()


st.divider()

st.subheader("کاربران ثبت‌شده")

users = get_all_users()

if not users:
    st.info("هنوز هیچ کاربری ثبت نشده است.")
    st.stop()

display_rows = []

for user in users:
    display_rows.append(
        {
            "تغییر رمز اجباری": "بله" if user["must_change_password"] else "خیر",
            "وضعیت": "فعال" if user["is_active"] else "غیرفعال",
            "نقش": "مدیر" if user["role"] == "manager" else "کاربر عادی",
            "نام کاربری": user["username"],
            "نام": user["full_name"],
            "شناسه": to_persian_digits(user["id"]),
        }
    )

display_df = pd.DataFrame(display_rows)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)

st.markdown("### عملیات کاربران")

for user in users:
    status_text = "فعال" if user["is_active"] else "غیرفعال"
    role_text = "مدیر" if user["role"] == "manager" else "کاربر عادی"

    with st.expander(
        f"{user['full_name']} | {user['username']} | {role_text} | {status_text}"
    ):
        st.write(f"نام کامل: {user['full_name']}")
        st.write(f"نام کاربری: {user['username']}")
        st.write(f"نقش: {role_text}")
        st.write(f"وضعیت: {status_text}")

        if user["must_change_password"]:
            st.warning("این کاربر باید در ورود بعدی رمز خود را تغییر دهد.")
        else:
            st.success("رمز این کاربر قبلاً توسط خودش تغییر کرده یا نیاز به تغییر اجباری ندارد.")

        st.divider()

        st.markdown("#### ویرایش اطلاعات کاربر")

        reverse_role_options = {
            "user": "کاربر عادی",
            "manager": "مدیر",
        }

        role_labels = list(role_options.keys())

        current_role_label = reverse_role_options.get(
            user["role"],
            "کاربر عادی",
        )

        if current_role_label in role_labels:
            default_role_index = role_labels.index(current_role_label)
        else:
            default_role_index = 0

        with st.form(f"edit_user_form_{user['id']}"):
            edit_col1, edit_col2 = st.columns(2)

            with edit_col1:
                edited_username = st.text_input(
                    "نام کاربری",
                    value=user["username"],
                    key=f"edit_username_{user['id']}",
                )

            with edit_col2:
                edited_full_name = st.text_input(
                    "نام و نام خانوادگی",
                    value=user["full_name"],
                    key=f"edit_full_name_{user['id']}",
                )

            edit_col3, edit_col4 = st.columns(2)

            with edit_col3:
                edited_role_label = st.selectbox(
                    "نقش کاربر",
                    options=role_labels,
                    index=default_role_index,
                    key=f"edit_role_{user['id']}",
                )

            with edit_col4:
                edited_is_active = st.toggle(
                    "کاربر فعال باشد",
                    value=user["is_active"],
                    key=f"edit_is_active_{user['id']}",
                )

            edited_must_change_password = st.checkbox(
                "کاربر در ورود بعدی مجبور به تغییر رمز باشد",
                value=user["must_change_password"],
                key=f"edit_must_change_password_{user['id']}",
            )

            save_user_edit = st.form_submit_button("ذخیره ویرایش کاربر")

        if save_user_edit:
            success, message = update_user_by_manager(
                user_id=user["id"],
                username=edited_username,
                full_name=edited_full_name,
                role=role_options[edited_role_label],
                is_active=edited_is_active,
                must_change_password=edited_must_change_password,
            )

            if success:
                st.session_state["user_flash"] = {
                    "type": "success",
                    "message": message,
                }
                st.rerun()
            else:
                st.session_state["user_flash"] = {
                    "type": "error",
                    "message": message,
                }
                st.rerun()

        st.divider()

        st.markdown("#### بازنشانی رمز عبور")

        with st.form(f"reset_password_form_{user['id']}"):
            new_temp_password = st.text_input(
                "رمز موقت جدید",
                value="123456",
                type="password",
                key=f"temp_password_{user['id']}",
            )

            reset_submitted = st.form_submit_button("بازنشانی رمز")

        if reset_submitted:
            success, message = reset_user_password_by_manager(
                user_id=user["id"],
                temporary_password=new_temp_password,
            )

            if success:
                st.session_state["user_flash"] = {
                    "type": "success",
                    "message": message,
                }
                st.rerun()
            else:
                st.session_state["user_flash"] = {
                    "type": "error",
                    "message": message,
                }
                st.rerun()

        st.divider()

        button_label = "غیرفعال کردن کاربر" if user["is_active"] else "فعال کردن کاربر"

        if st.button(button_label, key=f"toggle_user_{user['id']}"):
            success, message = toggle_user_status(user["id"])

            if success:
                st.session_state["user_flash"] = {
                    "type": "success",
                    "message": message,
                }
                st.rerun()
            else:
                st.session_state["user_flash"] = {
                    "type": "error",
                    "message": message,
                }
                st.rerun()