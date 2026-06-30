from utils.db import Base, engine

# Import models so SQLAlchemy can detect them
from models.user import User
from models.project import Project
from models.report import Report
from models.deadline_setting import DeadlineSetting

try:
    from models.report_file import ReportFile
except Exception:
    ReportFile = None


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    main()