from datetime import date, datetime

from models.report_period import ReportPeriod
from utils.db import SessionLocal
from utils.deadline_service import get_report_timing_status

from models.report import Report


def get_all_report_periods() -> list[dict]:
    db = SessionLocal()

    try:
        periods = (
            db.query(ReportPeriod)
            .order_by(ReportPeriod.period_start.desc())
            .all()
        )

        return [_period_to_dict(period) for period in periods]

    finally:
        db.close()


def get_active_report_periods(report_type: str | None = None) -> list[dict]:
    db = SessionLocal()

    try:
        query = db.query(ReportPeriod).filter(ReportPeriod.is_active == True)

        if report_type:
            query = query.filter(ReportPeriod.report_type == report_type)

        periods = query.order_by(ReportPeriod.period_start.desc()).all()

        return [_period_to_dict(period) for period in periods]

    finally:
        db.close()


def get_open_report_periods_for_submission(report_type: str) -> list[dict]:
    now = datetime.now()
    today = now.date()

    periods = get_active_report_periods(report_type=report_type)

    open_periods = []

    for period in periods:
        if today < period["period_start"]:
            continue

        timing_status = get_report_timing_status(
            report_type=period["report_type"],
            period_end=period["period_end"],
            now=now,
        )

        if timing_status["can_submit_or_edit"]:
            period["timing_status"] = timing_status
            open_periods.append(period)

    return open_periods


def get_report_period_by_id(period_id: int) -> dict | None:
    db = SessionLocal()

    try:
        period = (
            db.query(ReportPeriod)
            .filter(ReportPeriod.id == period_id)
            .first()
        )

        if not period:
            return None

        return _period_to_dict(period)

    finally:
        db.close()


def create_report_period(
    title: str,
    report_type: str,
    period_start: date,
    period_end: date,
    description: str | None = None,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        title = title.strip()

        if not title:
            return False, "عنوان بازه گزارش را وارد کنید."

        if report_type not in ["weekly", "monthly"]:
            return False, "نوع گزارش معتبر نیست."

        if period_start > period_end:
            return False, "تاریخ شروع بازه نمی‌تواند بعد از تاریخ پایان باشد."

        overlap = (
            db.query(ReportPeriod)
            .filter(ReportPeriod.report_type == report_type)
            .filter(ReportPeriod.is_active == True)
            .filter(ReportPeriod.period_start <= period_end)
            .filter(ReportPeriod.period_end >= period_start)
            .first()
        )

        if overlap:
            return False, "این بازه با یک بازه فعال دیگر هم‌پوشانی دارد."

        period = ReportPeriod(
            title=title,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            description=description.strip() if description else None,
            is_active=True,
        )

        db.add(period)
        db.commit()

        return True, "بازه گزارش با موفقیت ساخته شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ساخت بازه گزارش: {e}"

    finally:
        db.close()


def toggle_report_period_status(period_id: int) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        period = (
            db.query(ReportPeriod)
            .filter(ReportPeriod.id == period_id)
            .first()
        )

        if not period:
            return False, "بازه گزارش پیدا نشد."

        period.is_active = not period.is_active
        db.commit()

        return True, "وضعیت بازه گزارش تغییر کرد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در تغییر وضعیت بازه گزارش: {e}"

    finally:
        db.close()


def _period_to_dict(period: ReportPeriod) -> dict:
    return {
        "id": period.id,
        "title": period.title,
        "report_type": period.report_type,
        "period_start": period.period_start,
        "period_end": period.period_end,
        "description": period.description or "",
        "is_active": period.is_active,
        "created_at": period.created_at,
    }

def update_report_period(
    period_id: int,
    title: str,
    report_type: str,
    period_start: date,
    period_end: date,
    description: str | None,
    is_active: bool,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        period = (
            db.query(ReportPeriod)
            .filter(ReportPeriod.id == period_id)
            .first()
        )

        if not period:
            return False, "بازه گزارش پیدا نشد."

        title = title.strip()

        if not title:
            return False, "عنوان بازه گزارش را وارد کنید."

        if report_type not in ["weekly", "monthly"]:
            return False, "نوع گزارش معتبر نیست."

        if period_start > period_end:
            return False, "تاریخ شروع بازه نمی‌تواند بعد از تاریخ پایان باشد."

        overlap = (
            db.query(ReportPeriod)
            .filter(ReportPeriod.id != period_id)
            .filter(ReportPeriod.report_type == report_type)
            .filter(ReportPeriod.is_active == True)
            .filter(ReportPeriod.period_start <= period_end)
            .filter(ReportPeriod.period_end >= period_start)
            .first()
        )

        if overlap and is_active:
            return False, "این بازه با یک بازه فعال دیگر هم‌پوشانی دارد."

        period.title = title
        period.report_type = report_type
        period.period_start = period_start
        period.period_end = period_end
        period.description = description.strip() if description else None
        period.is_active = is_active

        db.commit()

        return True, "بازه گزارش با موفقیت ویرایش شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ویرایش بازه گزارش: {e}"

    finally:
        db.close()


def delete_report_period(period_id: int) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        period = (
            db.query(ReportPeriod)
            .filter(ReportPeriod.id == period_id)
            .first()
        )

        if not period:
            return False, "بازه گزارش پیدا نشد."

        related_reports_count = (
            db.query(Report)
            .filter(Report.period_id == period_id)
            .count()
        )

        if related_reports_count > 0:
            return (
                False,
                "این بازه گزارش قابل حذف نیست، چون گزارش‌هایی به آن وصل شده‌اند. "
                "می‌توانید آن را غیرفعال کنید.",
            )

        db.delete(period)
        db.commit()

        return True, "بازه گزارش با موفقیت حذف شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در حذف بازه گزارش: {e}"

    finally:
        db.close()