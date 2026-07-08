from collections import defaultdict

from sqlalchemy import func

from models.project import Project
from models.report import Report
from models.report_file import ReportFile
from models.report_period import ReportPeriod
from models.user import User
from models.user_project import UserProject
from utils.db import SessionLocal


def get_dashboard_filter_options() -> dict:
    db = SessionLocal()

    try:
        periods = (
            db.query(ReportPeriod)
            .order_by(ReportPeriod.period_start.desc())
            .all()
        )

        projects = (
            db.query(Project)
            .filter(Project.is_active == True)
            .order_by(Project.title.asc())
            .all()
        )

        users = (
            db.query(User)
            .filter(User.role == "user")
            .filter(User.is_active == True)
            .order_by(User.full_name.asc())
            .all()
        )

        return {
            "periods": [
                {
                    "id": period.id,
                    "title": period.title,
                    "report_type": period.report_type,
                    "period_start": period.period_start,
                    "period_end": period.period_end,
                    "is_active": period.is_active,
                }
                for period in periods
            ],
            "projects": [
                {
                    "id": project.id,
                    "title": project.title,
                }
                for project in projects
            ],
            "users": [
                {
                    "id": user.id,
                    "full_name": user.full_name,
                    "username": user.username,
                }
                for user in users
            ],
        }

    finally:
        db.close()


def get_manager_dashboard_data(
    period_id: int,
    project_id: int | None = None,
    user_id: int | None = None,
) -> dict:
    db = SessionLocal()

    try:
        period = (
            db.query(ReportPeriod)
            .filter(ReportPeriod.id == period_id)
            .first()
        )

        if not period:
            return {
                "period": None,
                "summary": {},
                "rows": [],
            }

        report_query = (
            db.query(Report, User, Project)
            .join(User, Report.user_id == User.id)
            .join(Project, Report.project_id == Project.id)
            .filter(Report.period_id == period_id)
        )

        if project_id:
            report_query = report_query.filter(Report.project_id == project_id)

        if user_id:
            report_query = report_query.filter(Report.user_id == user_id)

        report_records = report_query.all()

        report_ids = [
            report.id
            for report, _, _ in report_records
        ]

        file_counts = defaultdict(int)

        if report_ids:
            file_count_records = (
                db.query(
                    ReportFile.report_id,
                    func.count(ReportFile.id),
                )
                .filter(ReportFile.report_id.in_(report_ids))
                .group_by(ReportFile.report_id)
                .all()
            )

            for report_id_value, count_value in file_count_records:
                file_counts[report_id_value] = count_value

        reports_by_user_project = {}

        for report, user, project in report_records:
            reports_by_user_project[(report.user_id, report.project_id)] = {
                "report": report,
                "user": user,
                "project": project,
            }

        assignment_query = (
            db.query(UserProject, User, Project)
            .join(User, UserProject.user_id == User.id)
            .join(Project, UserProject.project_id == Project.id)
            .filter(UserProject.is_active == True)
            .filter(User.is_active == True)
            .filter(User.role == "user")
            .filter(Project.is_active == True)
        )

        if project_id:
            assignment_query = assignment_query.filter(UserProject.project_id == project_id)

        if user_id:
            assignment_query = assignment_query.filter(UserProject.user_id == user_id)

        assignment_records = assignment_query.all()

        rows = []
        seen_keys = set()

        for assignment, user, project in assignment_records:
            key = (user.id, project.id)
            seen_keys.add(key)

            matched_report = reports_by_user_project.get(key)

            if matched_report:
                report = matched_report["report"]

                if report.is_late or report.status == "late":
                    status_label = "تأخیری"
                    status_key = "late"
                else:
                    status_label = "ثبت‌شده"
                    status_key = "submitted"

                rows.append(
                    {
                        "user_id": user.id,
                        "user_full_name": user.full_name,
                        "username": user.username,
                        "project_id": project.id,
                        "project_title": project.title,
                        "period_id": period.id,
                        "period_title": period.title,
                        "report_id": report.id,
                        "status_key": status_key,
                        "status_label": status_label,
                        "is_late": report.is_late,
                        "submitted_at": report.submitted_at,
                        "has_report": True,
                        "file_count": file_counts[report.id],
                        "activities_done": report.activities_done or "",
                        "results_achieved": report.results_achieved or "",
                        "next_actions": report.next_actions or "",
                        "kpi_text": report.kpi_text or "",
                    }
                )

            else:
                rows.append(
                    {
                        "user_id": user.id,
                        "user_full_name": user.full_name,
                        "username": user.username,
                        "project_id": project.id,
                        "project_title": project.title,
                        "period_id": period.id,
                        "period_title": period.title,
                        "report_id": None,
                        "status_key": "missing",
                        "status_label": "ثبت‌نشده",
                        "is_late": False,
                        "submitted_at": None,
                        "has_report": False,
                        "file_count": 0,
                        "activities_done": "",
                        "results_achieved": "",
                        "next_actions": "",
                        "kpi_text": "",
                    }
                )

        # اگر گزارشی وجود دارد ولی تخصیص فعلی آن کاربر/پروژه دیگر فعال نیست،
        # آن را حذف نمی‌کنیم؛ در داشبورد با وضعیت جدا نمایش می‌دهیم.
        for key, matched_report in reports_by_user_project.items():
            if key in seen_keys:
                continue

            report = matched_report["report"]
            user = matched_report["user"]
            project = matched_report["project"]

            if report.is_late or report.status == "late":
                status_label = "تأخیری - خارج از تخصیص فعلی"
                status_key = "late"
            else:
                status_label = "ثبت‌شده - خارج از تخصیص فعلی"
                status_key = "submitted"

            rows.append(
                {
                    "user_id": user.id,
                    "user_full_name": user.full_name,
                    "username": user.username,
                    "project_id": project.id,
                    "project_title": project.title,
                    "period_id": period.id,
                    "period_title": period.title,
                    "report_id": report.id,
                    "status_key": status_key,
                    "status_label": status_label,
                    "is_late": report.is_late,
                    "submitted_at": report.submitted_at,
                    "has_report": True,
                    "file_count": file_counts[report.id],
                    "activities_done": report.activities_done or "",
                    "results_achieved": report.results_achieved or "",
                    "next_actions": report.next_actions or "",
                    "kpi_text": report.kpi_text or "",
                }
            )

        total_expected = len([
            row for row in rows
            if row["status_label"] != "ثبت‌شده - خارج از تخصیص فعلی"
            and row["status_label"] != "تأخیری - خارج از تخصیص فعلی"
        ])

        submitted_count = len([
            row for row in rows
            if row["has_report"]
        ])

        missing_count = len([
            row for row in rows
            if row["status_key"] == "missing"
        ])

        late_count = len([
            row for row in rows
            if row["is_late"]
        ])

        on_time_count = len([
            row for row in rows
            if row["has_report"] and not row["is_late"]
        ])

        with_files_count = len([
            row for row in rows
            if row["file_count"] > 0
        ])

        participation_rate = 0

        if total_expected > 0:
            participation_rate = round(
                ((submitted_count - len([
                    row for row in rows
                    if "خارج از تخصیص فعلی" in row["status_label"]
                ])) / total_expected) * 100,
                1,
            )

        return {
            "period": {
                "id": period.id,
                "title": period.title,
                "report_type": period.report_type,
                "period_start": period.period_start,
                "period_end": period.period_end,
            },
            "summary": {
                "total_expected": total_expected,
                "submitted_count": submitted_count,
                "missing_count": missing_count,
                "late_count": late_count,
                "on_time_count": on_time_count,
                "with_files_count": with_files_count,
                "participation_rate": participation_rate,
            },
            "rows": rows,
        }

    finally:
        db.close()