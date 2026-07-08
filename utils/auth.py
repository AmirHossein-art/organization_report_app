
import os
import streamlit as st
import streamlit.components.v1 as components

from dotenv import load_dotenv
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from streamlit_cookies_controller import CookieController

from models.user import User
from utils.db import SessionLocal
from utils.security import verify_password

load_dotenv()

AUTH_COOKIE_NAME = "org_reporting_auth"
AUTH_COOKIE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 days

SECRET_KEY = os.getenv("SECRET_KEY")

def auto_reload (delay_ms: int = 500):
    components.html(
        f"""
        <script>
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {delay_ms});
        </script>
        """,
        height=0,
        width=0,
    )

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set. Please check your .env file.")


def read_auth_cookie():
    """
    Read auth cookie.

    After browser refresh, st.context.cookies is more reliable because
    it reads cookies sent with the initial request.

    CookieController is kept as a fallback.
    """
    try:
        token = st.context.cookies.get(AUTH_COOKIE_NAME)
        if token:
            return token
    except Exception:
        pass

    try:
        controller = get_cookie_controller()
        return controller.get(AUTH_COOKIE_NAME)
    except Exception:
        return None

def get_serializer():
    return URLSafeTimedSerializer(SECRET_KEY)


def get_cookie_controller():
    if "cookie_controller" not in st.session_state:
        st.session_state.cookie_controller = CookieController()

    return st.session_state.cookie_controller


def clear_auth_cookie():
    try:
        controller = get_cookie_controller()
        controller.remove(AUTH_COOKIE_NAME)
    except Exception:
        pass

    # Extra fallback: overwrite cookie with empty value and immediate expiry.
    try:
        controller = get_cookie_controller()
        controller.set(
            AUTH_COOKIE_NAME,
            "",
            max_age=0,
            same_site="lax",
            path="/",
        )
    except Exception:
        pass

def restore_login_from_cookie():
    token = read_auth_cookie()

    if not token:
        return

    serializer = get_serializer()

    try:
        data = serializer.loads(
            token,
            max_age=AUTH_COOKIE_MAX_AGE_SECONDS,
        )

        user_id = data.get("user_id")

        if not user_id:
            return

        db = SessionLocal()

        try:
            user = (
                db.query(User)
                .filter(User.id == user_id)
                .filter(User.is_active == True)
                .first()
            )

            if not user:
                return

            st.session_state.authenticated = True
            st.session_state.user = {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "must_change_password": getattr(user, "must_change_password", False),
            }

        finally:
            db.close()

    except SignatureExpired:
        clear_auth_cookie()

    except BadSignature:
        clear_auth_cookie()

    except Exception:
        clear_auth_cookie()

def init_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user" not in st.session_state:
        st.session_state.user = None

    if "logout_in_progress" not in st.session_state:
        st.session_state.logout_in_progress = False

    # If user has clicked logout, do not restore from cookie in the same session.
    if st.session_state.logout_in_progress:
        st.session_state.authenticated = False
        st.session_state.user = None
        return

    if not st.session_state.authenticated:
        restore_login_from_cookie()


def authenticate_user(username: str, password: str):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.username == username)
            .filter(User.is_active == True)
            .first()
        )

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "must_change_password": getattr(user, "must_change_password", False),
        }

    finally:
        db.close()

def login_user(user_data: dict):
    st.session_state.logout_in_progress = False
    
    st.session_state.authenticated = True
    st.session_state.user = user_data

    serializer = get_serializer()
    token = serializer.dumps(
        {
            "user_id": user_data["id"],
        }
    )

    controller = get_cookie_controller()
    controller.set(
        AUTH_COOKIE_NAME,
        token,
        max_age=AUTH_COOKIE_MAX_AGE_SECONDS,
        same_site="lax",
        path="/",
    )
def logout_user():
    clear_auth_cookie()

    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.logout_in_progress = True
    
def current_user():
    init_auth_state()
    return st.session_state.user


def is_logged_in() -> bool:
    init_auth_state()
    return bool(st.session_state.authenticated and st.session_state.user)


def is_manager() -> bool:
    user = current_user()
    return bool(user and user.get("role") == "manager")

def show_login_form():
    init_auth_state()

    st.title("ورود به سامانه")

    with st.form("login_form"):
        username = st.text_input("نام کاربری")
        password = st.text_input("رمز عبور", type="password")

        submitted = st.form_submit_button("ورود")

    if submitted:
        username = username.strip()

        if not username or not password:
            st.warning("نام کاربری و رمز عبور را وارد کنید.")
            return

        user_data = authenticate_user(username, password)

        if user_data:
            login_user(user_data)

            st.success("ورود موفقیت‌آمیز بود.")
            st.info("در حال ورود به سامانه...")

            auto_reload(delay_ms=1000)
            st.stop()

        else:
            st.error("نام کاربری یا رمز عبور اشتباه است.")

def show_user_sidebar():
    init_auth_state()

    if not is_logged_in():
        return

    user = current_user()

    role_label = "مدیر" if user["role"] == "manager" else "کاربر"

    st.sidebar.markdown(
        f"""
        <div class="sidebar-user-card">
            <div class="sidebar-user-name">👤 {user['full_name']}</div>
            <div class="sidebar-user-role">نقش: {role_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("خروج از سامانه"):
        logout_user()

        st.success("از سامانه خارج شدید.")
        st.info("در حال انتقال به صفحه ورود...")

        auto_reload(delay_ms=1000)
        st.stop()

def require_login():
    init_auth_state()

    if not is_logged_in():
        st.warning("برای دسترسی به این صفحه ابتدا وارد سامانه شوید.")
        show_login_form()
        st.stop()

    enforce_password_change_if_needed()
    
def require_manager():
    require_login()

    if not is_manager():
        st.error("شما به این صفحه دسترسی مدیریتی ندارید.")
        st.stop()

def show_force_password_change_form():
    from utils.user_service import change_own_password

    user = current_user()

    st.warning(
        "برای ادامه استفاده از سامانه، باید رمز عبور موقت خود را تغییر دهید."
    )

    with st.form("force_password_change_form"):
        current_password = st.text_input(
            "رمز فعلی",
            type="password",
        )

        new_password = st.text_input(
            "رمز جدید",
            type="password",
        )

        confirm_password = st.text_input(
            "تکرار رمز جدید",
            type="password",
        )

        submitted = st.form_submit_button("تغییر رمز و ادامه")

    if submitted:
        if new_password != confirm_password:
            st.error("رمز جدید و تکرار آن یکسان نیستند.")
            return

        success, message = change_own_password(
            user_id=user["id"],
            current_password=current_password,
            new_password=new_password,
        )

        if success:
            st.session_state.user["must_change_password"] = False
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def enforce_password_change_if_needed():
    user = current_user()

    if user and user.get("must_change_password"):
        st.title("تغییر رمز عبور")
        show_force_password_change_form()
        st.stop()