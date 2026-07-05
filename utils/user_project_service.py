from models.project import Project
from models.user import User
from models.user_project import UserProject
from utils.db import SessionLocal


def get_users_for_project_assignment() -> list[dict]:
    db = SessionLocal()

    try:
        users = (
            db.query(User)
            .filter(User.is_active == True)
            .filter(User.role == "user")
            .order_by(User.full_name.asc())
            .all()
        )

        return [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
            }
            for user in users
        ]

    finally:
        db.close()


def get_assigned_project_ids_for_user(user_id: int) -> list[int]:
    db = SessionLocal()

    try:
        assignments = (
            db.query(UserProject)
            .filter(UserProject.user_id == user_id)
            .filter(UserProject.is_active == True)
            .all()
        )

        return [assignment.project_id for assignment in assignments]

    finally:
        db.close()


def get_assigned_projects_for_user(user_id: int) -> list[dict]:
    db = SessionLocal()

    try:
        projects = (
            db.query(Project)
            .join(UserProject, UserProject.project_id == Project.id)
            .filter(UserProject.user_id == user_id)
            .filter(UserProject.is_active == True)
            .filter(Project.is_active == True)
            .order_by(Project.title.asc())
            .all()
        )

        return [
            {
                "id": project.id,
                "title": project.title,
                "description": project.description or "",
                "is_active": project.is_active,
            }
            for project in projects
        ]

    finally:
        db.close()


def save_user_project_assignments(
    user_id: int,
    selected_project_ids: list[int],
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
            return False, "کاربر انتخاب‌شده فعال نیست یا وجود ندارد."

        selected_project_ids = list(set(selected_project_ids))

        if selected_project_ids:
            active_projects_count = (
                db.query(Project)
                .filter(Project.id.in_(selected_project_ids))
                .filter(Project.is_active == True)
                .count()
            )

            if active_projects_count != len(selected_project_ids):
                return False, "یک یا چند پروژه انتخاب‌شده فعال نیستند یا وجود ندارند."

        existing_assignments = (
            db.query(UserProject)
            .filter(UserProject.user_id == user_id)
            .all()
        )

        existing_by_project_id = {
            assignment.project_id: assignment
            for assignment in existing_assignments
        }

        for assignment in existing_assignments:
            assignment.is_active = assignment.project_id in selected_project_ids

        for project_id in selected_project_ids:
            if project_id not in existing_by_project_id:
                db.add(
                    UserProject(
                        user_id=user_id,
                        project_id=project_id,
                        is_active=True,
                    )
                )

        db.commit()

        return True, "پروژه‌های کاربر با موفقیت ذخیره شدند."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ذخیره پروژه‌های کاربر: {e}"

    finally:
        db.close()


def user_has_project_access(db, user_id: int, project_id: int) -> bool:
    assignment = (
        db.query(UserProject)
        .join(Project, UserProject.project_id == Project.id)
        .filter(UserProject.user_id == user_id)
        .filter(UserProject.project_id == project_id)
        .filter(UserProject.is_active == True)
        .filter(Project.is_active == True)
        .first()
    )

    return assignment is not None