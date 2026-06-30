from datetime import date

from models.project import Project
from models.report import Report
from utils.db import SessionLocal


def create_report(
    user_id: int,
    project_id: int,
    report_type: str,
    period_start: date,
    period_end: date,
    activities_done: str | None,
    results_achieved: str | None,
    next_actions: str | None,
    kpi_text: str | None,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        project = (
            db.query(Project)
            .filter(Project.id == project_id)
            .filter(Project.is_active == True)
            .first()
        )

        if not project:
            return False, "پروژه انتخاب‌شده فعال نیست یا وجود ندارد."

        if report_type not in ["weekly", "monthly"]:
            return False, "نوع گزارش معتبر نیست."

        if period_start > period_end:
            return False, "تاریخ شروع دوره نمی‌تواند بعد از تاریخ پایان باشد."

        report = Report(
            user_id=user_id,
            project_id=project_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            activities_done=activities_done.strip() if activities_done else None,
            results_achieved=results_achieved.strip() if results_achieved else None,
            next_actions=next_actions.strip() if next_actions else None,
            kpi_text=kpi_text.strip() if kpi_text else None,
            status="submitted",
            is_late=False,
        )

        db.add(report)
        db.commit()

        return True, "گزارش با موفقیت ثبت شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ثبت گزارش: {e}"

    finally:
        db.close()


def get_reports_by_user(user_id: int) -> list[dict]:
    db = SessionLocal()

    try:
        reports = (
            db.query(Report, Project)
            .join(Project, Report.project_id == Project.id)
            .filter(Report.user_id == user_id)
            .order_by(Report.submitted_at.desc())
            .all()
        )

        result = []

        for report, project in reports:
            result.append(
                {
                    "id": report.id,
                    "project_title": project.title,
                    "report_type": report.report_type,
                    "period_start": report.period_start,
                    "period_end": report.period_end,
                    "activities_done": report.activities_done or "",
                    "results_achieved": report.results_achieved or "",
                    "next_actions": report.next_actions or "",
                    "kpi_text": report.kpi_text or "",
                    "status": report.status,
                    "is_late": report.is_late,
                    "submitted_at": report.submitted_at,
                }
            )

        return result

    finally:
        db.close()