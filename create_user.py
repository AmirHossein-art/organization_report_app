from getpass import getpass

from models.user import User
from utils.db import SessionLocal
from utils.security import hash_password


VALID_ROLES = ["user", "manager"]


def main():
    print("Create new user")
    print("----------------")

    username = input("Username: ").strip()
    full_name = input("Full name: ").strip()
    role = input("Role (user/manager): ").strip().lower()

    if role not in VALID_ROLES:
        print("Invalid role. Use 'user' or 'manager'.")
        return

    password = getpass("Password: ")
    password_confirm = getpass("Confirm password: ")

    if not username:
        print("Username is required.")
        return

    if not full_name:
        print("Full name is required.")
        return

    if not password:
        print("Password is required.")
        return

    if password != password_confirm:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user:
            print("A user with this username already exists.")
            return

        user = User(
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()

        print("User created successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()