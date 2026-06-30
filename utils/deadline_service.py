from datetime import date, datetime, time, timedelta

from models.deadline_setting import DeadlineSetting
from utils.db import SessionLocal


DEFAULT_DEADLINE_SETTINGS = {
    "weekly": {
        "deadline_offset_days": 0,
        "deadline_time": time(14, 0),
        "grace_days": 2,
    },
    "monthly": {
        "deadline_offset_days": 0,
        "deadline_time": time(14, 0),
        "grace_days": 2,
    },
}


def ensure_default_deadline_settings():
    db = SessionLocal()

    try:
        for report_type, values in DEFAULT_DEADLINE_SETTINGS.items():
            existing = (
                db.query(DeadlineSetting)
                .filter(DeadlineSetting.report_type == report_type)
                .first()
            )

            if existing:
                continue

            setting = DeadlineSetting(
                report_type=report_type,
                deadline_offset_days=values["deadline_offset_days"],
                deadline_time=values["deadline_time"],
                grace_days=values["grace_days"],
                is_active=True,
            )

            db.add(setting)

        db.commit()

    finally:
        db.close()


def get_deadline_setting(report_type: str):
    ensure_default_deadline_settings()

    db = SessionLocal()

    try:
        return (
            db.query(DeadlineSetting)
            .filter(DeadlineSetting.report_type == report_type)
            .first()
        )

    finally:
        db.close()


def get_all_deadline_settings() -> list[dict]:
    ensure_default_deadline_settings()

    db = SessionLocal()

    try:
        settings = (
            db.query(DeadlineSetting)
            .order_by(DeadlineSetting.report_type.asc())
            .all()
        )

        return [
            {
                "id": setting.id,
                "report_type": setting.report_type,
                "deadline_offset_days": setting.deadline_offset_days,
                "deadline_time": setting.deadline_time,
                "grace_days": setting.grace_days,
                "is_active": setting.is_active,
            }
            for setting in settings
        ]

    finally:
        db.close()


def update_deadline_setting(
    report_type: str,
    deadline_time: time,
    grace_days: int,
    is_active: bool,
) -> tuple[bool, str]:
    ensure_default_deadline_settings()

    db = SessionLocal()

    try:
        setting = (
            db.query(DeadlineSetting)
            .filter(DeadlineSetting.report_type == report_type)
            .first()
        )

        if not setting:
            return False, "تنظیمات مهلت گزارش پیدا نشد."

        if grace_days < 0:
            return False, "مهلت اضافه نمی‌تواند منفی باشد."

        # منطق جدید: ددلاین همیشه خود تاریخ پایان بازه گزارش است.
        setting.deadline_offset_days = 0
        setting.deadline_time = deadline_time
        setting.grace_days = grace_days
        setting.is_active = is_active

        db.commit()

        return True, "تنظیمات مهلت گزارش با موفقیت ذخیره شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ذخیره تنظیمات مهلت گزارش: {e}"

    finally:
        db.close()


def calculate_deadline_datetimes(
    report_type: str,
    period_end: date,
) -> tuple[datetime | None, datetime | None]:
    setting = get_deadline_setting(report_type)

    if not setting or not setting.is_active:
        return None, None

    # منطق جدید:
    # مهلت اصلی دقیقاً همان تاریخ پایان بازه گزارش است، در ساعتی که مدیر تعیین می‌کند.
    deadline_at = datetime.combine(
        period_end,
        setting.deadline_time,
    )

    # مهلت نهایی = مهلت اصلی + مهلت اضافه
    closes_at = deadline_at + timedelta(days=setting.grace_days)

    return deadline_at, closes_at


def get_report_timing_status(
    report_type: str,
    period_end: date,
    now: datetime | None = None,
) -> dict:
    if now is None:
        now = datetime.now()

    deadline_at, closes_at = calculate_deadline_datetimes(
        report_type=report_type,
        period_end=period_end,
    )

    if deadline_at is None or closes_at is None:
        return {
            "is_deadline_active": False,
            "can_submit_or_edit": True,
            "is_late": False,
            "deadline_at": None,
            "closes_at": None,
            "message": "ددلاین برای این نوع گزارش فعال نیست.",
        }

    if now <= deadline_at:
        return {
            "is_deadline_active": True,
            "can_submit_or_edit": True,
            "is_late": False,
            "deadline_at": deadline_at,
            "closes_at": closes_at,
            "message": "مهلت ثبت و ویرایش گزارش هنوز به پایان نرسیده است.",
        }

    if deadline_at < now <= closes_at:
        return {
            "is_deadline_active": True,
            "can_submit_or_edit": True,
            "is_late": True,
            "deadline_at": deadline_at,
            "closes_at": closes_at,
            "message": "مهلت اصلی گذشته است. گزارش با وضعیت تأخیری ثبت یا ویرایش می‌شود.",
        }

    return {
        "is_deadline_active": True,
        "can_submit_or_edit": False,
        "is_late": True,
        "deadline_at": deadline_at,
        "closes_at": closes_at,
        "message": "مهلت نهایی ثبت و ویرایش این گزارش پایان یافته است.",
    }