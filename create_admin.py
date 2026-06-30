from sqlalchemy.exc import IntegrityError

from models.user import User
from utils.db import SessionLocal
from utils.security import hash_password


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_FULL_NAME = "مدیر سیستم"


def main():
    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.username == ADMIN_USERNAME).first()

        if existing_user:
            print("Admin user already exists.")
            return

        admin_user = User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_FULL_NAME,
            role="manager",
            is_active=True,
        )

        db.add(admin_user)
        db.commit()

        print("Admin user created successfully.")
        print(f"Username: {ADMIN_USERNAME}")
        print(f"Password: {ADMIN_PASSWORD}")

    except IntegrityError:
        db.rollback()
        print("Admin user could not be created because of duplicate data.")

    finally:
        db.close()


if __name__ == "__main__":
    main()