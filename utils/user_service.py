from datetime import datetime

from models.user import User
from utils.db import SessionLocal
from utils.security import hash_password, verify_password


VALID_ROLES = ["user", "manager"]


def get_all_users() -> list[dict]:
    db = SessionLocal()

    try:
        users = db.query(User).order_by(User.created_at.desc()).all()

        return [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "must_change_password": getattr(user, "must_change_password", False),
                "created_at": user.created_at,
                "password_changed_at": getattr(user, "password_changed_at", None),
            }
            for user in users
        ]

    finally:
        db.close()


def create_user_by_manager(
    username: str,
    full_name: str,
    role: str,
    temporary_password: str,
    must_change_password: bool = True,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        username = username.strip()
        full_name = full_name.strip()
        role = role.strip().lower()

        if not username:
            return False, "نام کاربری را وارد کنید."

        if not full_name:
            return False, "نام کامل کاربر را وارد کنید."

        if role not in VALID_ROLES:
            return False, "نقش کاربر معتبر نیست."

        if not temporary_password:
            return False, "رمز اولیه را وارد کنید."

        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user:
            return False, "این نام کاربری قبلاً ثبت شده است."

        user = User(
            username=username,
            full_name=full_name,
            role=role,
            password_hash=hash_password(temporary_password),
            is_active=True,
            must_change_password=must_change_password,
            password_changed_at=None,
        )

        db.add(user)
        db.commit()

        return True, "کاربر جدید با موفقیت ساخته شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ساخت کاربر: {e}"

    finally:
        db.close()


def reset_user_password_by_manager(
    user_id: int,
    temporary_password: str,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        if not temporary_password:
            return False, "رمز موقت را وارد کنید."

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return False, "کاربر پیدا نشد."

        user.password_hash = hash_password(temporary_password)
        user.must_change_password = True
        user.password_changed_at = None

        db.commit()

        return True, "رمز کاربر با موفقیت بازنشانی شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در بازنشانی رمز: {e}"

    finally:
        db.close()


def toggle_user_status(user_id: int) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return False, "کاربر پیدا نشد."

        user.is_active = not user.is_active

        db.commit()

        return True, "وضعیت کاربر با موفقیت تغییر کرد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در تغییر وضعیت کاربر: {e}"

    finally:
        db.close()


def change_own_password(
    user_id: int,
    current_password: str,
    new_password: str,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .filter(User.is_active == True)
            .first()
        )

        if not user:
            return False, "کاربر فعال پیدا نشد."

        if not verify_password(current_password, user.password_hash):
            return False, "رمز فعلی اشتباه است."

        if not new_password:
            return False, "رمز جدید را وارد کنید."

        if len(new_password) < 6:
            return False, "رمز جدید باید حداقل ۶ کاراکتر باشد."

        if new_password == "123456":
            return False, "رمز جدید نباید همان رمز پیش‌فرض 123456 باشد."

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        user.password_changed_at = datetime.now()

        db.commit()

        return True, "رمز عبور با موفقیت تغییر کرد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در تغییر رمز عبور: {e}"

    finally:
        db.close()

def update_user_by_manager(
    user_id: int,
    username: str,
    full_name: str,
    role: str,
    is_active: bool,
    must_change_password: bool,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        username = username.strip()
        full_name = full_name.strip()
        role = role.strip().lower()

        if not username:
            return False, "نام کاربری را وارد کنید."

        if not full_name:
            return False, "نام کامل کاربر را وارد کنید."

        if role not in VALID_ROLES:
            return False, "نقش کاربر معتبر نیست."

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return False, "کاربر پیدا نشد."

        duplicate_username = (
            db.query(User)
            .filter(User.username == username)
            .filter(User.id != user_id)
            .first()
        )

        if duplicate_username:
            return False, "این نام کاربری قبلاً برای کاربر دیگری ثبت شده است."

        # جلوگیری از حذف یا تغییر نقش آخرین مدیر فعال سایت
        if user.role == "manager" and (role != "manager" or not is_active):
            other_active_managers_count = (
                db.query(User)
                .filter(User.id != user_id)
                .filter(User.role == "manager")
                .filter(User.is_active == True)
                .count()
            )

            if other_active_managers_count == 0:
                return (
                    False,
                    "این کاربر آخرین مدیر فعال سایت است و نمی‌توان نقش او را تغییر داد یا غیرفعالش کرد.",
                )

        user.username = username
        user.full_name = full_name
        user.role = role
        user.is_active = is_active
        user.must_change_password = must_change_password

        db.commit()

        return True, "اطلاعات کاربر با موفقیت ویرایش شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ویرایش کاربر: {e}"

    finally:
        db.close()