from sqlalchemy.exc import IntegrityError

from models.project import Project
from utils.db import SessionLocal


def get_all_projects(include_inactive: bool = True) -> list[dict]:
    db = SessionLocal()

    try:
        query = db.query(Project).order_by(Project.created_at.desc())

        if not include_inactive:
            query = query.filter(Project.is_active == True)

        projects = query.all()

        return [
            {
                "id": project.id,
                "title": project.title,
                "description": project.description or "",
                "is_active": project.is_active,
                "created_at": project.created_at,
            }
            for project in projects
        ]

    finally:
        db.close()


def get_active_projects() -> list[dict]:
    return get_all_projects(include_inactive=False)


def create_project(title: str, description: str | None = None) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        title = title.strip()

        if not title:
            return False, "عنوان پروژه نمی‌تواند خالی باشد."

        existing_project = db.query(Project).filter(Project.title == title).first()

        if existing_project:
            return False, "پروژه‌ای با این عنوان قبلاً ثبت شده است."

        project = Project(
            title=title,
            description=description.strip() if description else None,
            is_active=True,
        )

        db.add(project)
        db.commit()

        return True, "پروژه با موفقیت ثبت شد."

    except IntegrityError:
        db.rollback()
        return False, "پروژه‌ای با این عنوان قبلاً وجود دارد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ثبت پروژه: {e}"

    finally:
        db.close()


def update_project(
    project_id: int,
    title: str,
    description: str | None,
    is_active: bool,
) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        title = title.strip()

        if not title:
            return False, "عنوان پروژه نمی‌تواند خالی باشد."

        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return False, "پروژه پیدا نشد."

        duplicate = (
            db.query(Project)
            .filter(Project.title == title)
            .filter(Project.id != project_id)
            .first()
        )

        if duplicate:
            return False, "پروژه‌ای دیگر با این عنوان وجود دارد."

        project.title = title
        project.description = description.strip() if description else None
        project.is_active = is_active

        db.commit()

        return True, "پروژه با موفقیت به‌روزرسانی شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ویرایش پروژه: {e}"

    finally:
        db.close()


def toggle_project_status(project_id: int) -> tuple[bool, str]:
    db = SessionLocal()

    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return False, "پروژه پیدا نشد."

        project.is_active = not project.is_active
        db.commit()

        if project.is_active:
            return True, "پروژه فعال شد."

        return True, "پروژه غیرفعال شد."

    except Exception as e:
        db.rollback()
        return False, f"خطا در تغییر وضعیت پروژه: {e}"

    finally:
        db.close()