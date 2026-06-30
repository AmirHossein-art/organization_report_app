from pathlib import Path
from uuid import uuid4

from models.report_file import ReportFile
from utils.db import SessionLocal


UPLOAD_DIR = Path("uploads/reports")

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
}


def ensure_upload_dir():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return suffix in ALLOWED_EXTENSIONS


def save_uploaded_files(report_id: int, uploaded_files) -> tuple[bool, str]:
    if not uploaded_files:
        return True, "فایلی برای ذخیره وجود ندارد."

    ensure_upload_dir()

    db = SessionLocal()

    try:
        for uploaded_file in uploaded_files:
            original_filename = uploaded_file.name

            if not is_allowed_file(original_filename):
                return (
                    False,
                    f"فرمت فایل «{original_filename}» مجاز نیست. فقط PDF، Word و Excel قابل آپلود هستند.",
                )

            file_suffix = Path(original_filename).suffix.lower()
            stored_filename = f"{report_id}_{uuid4().hex}{file_suffix}"
            file_path = UPLOAD_DIR / stored_filename

            file_bytes = uploaded_file.getbuffer()

            with open(file_path, "wb") as file:
                file.write(file_bytes)

            report_file = ReportFile(
                report_id=report_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path),
                file_type=file_suffix.replace(".", ""),
                file_size=len(file_bytes),
            )

            db.add(report_file)

        db.commit()
        return True, "فایل‌ها با موفقیت ذخیره شدند."

    except Exception as e:
        db.rollback()
        return False, f"خطا در ذخیره فایل‌ها: {e}"

    finally:
        db.close()


def get_files_by_report_id(report_id: int) -> list[dict]:
    db = SessionLocal()

    try:
        files = (
            db.query(ReportFile)
            .filter(ReportFile.report_id == report_id)
            .order_by(ReportFile.uploaded_at.desc())
            .all()
        )

        return [
            {
                "id": file.id,
                "original_filename": file.original_filename,
                "stored_filename": file.stored_filename,
                "file_path": file.file_path,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "uploaded_at": file.uploaded_at,
            }
            for file in files
        ]

    finally:
        db.close()


def format_file_size(size_in_bytes: int | None) -> str:
    if not size_in_bytes:
        return "-"

    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"

    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"

    return f"{size_in_bytes / (1024 * 1024):.1f} MB"