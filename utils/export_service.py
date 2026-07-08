from io import BytesIO

import pandas as pd

from utils.format_helpers import (
    report_type_label,
    to_jalali_date,
    to_jalali_datetime,
    to_persian_digits,
)


def build_dashboard_excel(
    period: dict,
    rows: list[dict],
) -> bytes:
    output = BytesIO()

    total_rows = len(rows)
    submitted_rows = [row for row in rows if row["has_report"]]
    missing_rows = [row for row in rows if not row["has_report"]]
    late_rows = [row for row in rows if row["is_late"]]
    on_time_rows = [
        row for row in rows
        if row["has_report"] and not row["is_late"]
    ]
    with_files_rows = [
        row for row in rows
        if row["file_count"] > 0
    ]

    participation_rate = 0

    if total_rows > 0:
        participation_rate = round((len(submitted_rows) / total_rows) * 100, 1)

    summary_df = pd.DataFrame(
        [
            {
                "شاخص": "عنوان بازه",
                "مقدار": period["title"],
            },
            {
                "شاخص": "نوع گزارش",
                "مقدار": report_type_label(period["report_type"]),
            },
            {
                "شاخص": "شروع بازه",
                "مقدار": to_jalali_date(period["period_start"]),
            },
            {
                "شاخص": "پایان بازه",
                "مقدار": to_jalali_date(period["period_end"]),
            },
            {
                "شاخص": "تعداد مورد انتظار",
                "مقدار": to_persian_digits(total_rows),
            },
            {
                "شاخص": "تعداد ثبت‌شده",
                "مقدار": to_persian_digits(len(submitted_rows)),
            },
            {
                "شاخص": "تعداد ثبت‌نشده",
                "مقدار": to_persian_digits(len(missing_rows)),
            },
            {
                "شاخص": "تعداد به‌موقع",
                "مقدار": to_persian_digits(len(on_time_rows)),
            },
            {
                "شاخص": "تعداد تأخیری",
                "مقدار": to_persian_digits(len(late_rows)),
            },
            {
                "شاخص": "تعداد دارای پیوست",
                "مقدار": to_persian_digits(len(with_files_rows)),
            },
            {
                "شاخص": "درصد مشارکت",
                "مقدار": f"{to_persian_digits(participation_rate)}٪",
            },
        ]
    )

    overview_df = pd.DataFrame(
        [
            {
                "کاربر": row["user_full_name"],
                "نام کاربری": row["username"],
                "پروژه": row["project_title"],
                "بازه": row["period_title"],
                "وضعیت": row["status_label"],
                "تاریخ ثبت": to_jalali_datetime(row["submitted_at"]) if row["submitted_at"] else "-",
                "تعداد پیوست": to_persian_digits(row["file_count"]),
                "فایل‌های پیوست": "، ".join([file["original_filename"] for file in row.get("files", [])]),
            }
            for row in rows
        ]
    )

    submitted_df = pd.DataFrame(
        [
            {
                "کاربر": row["user_full_name"],
                "نام کاربری": row["username"],
                "پروژه": row["project_title"],
                "وضعیت": row["status_label"],
                "تاریخ ثبت": to_jalali_datetime(row["submitted_at"]) if row["submitted_at"] else "-",
                "تعداد پیوست": to_persian_digits(row["file_count"]),
                "فایل‌های پیوست": "، ".join([file["original_filename"] for file in row.get("files", [])]),
                "فعالیت‌های انجام‌شده": row["activities_done"],
                "نتایج حاصل‌شده": row["results_achieved"],
                "اقدامات آتی": row["next_actions"],
                "شاخص‌ها": row["kpi_text"],
            }
            for row in submitted_rows
        ]
    )

    missing_df = pd.DataFrame(
        [
            {
                "کاربر": row["user_full_name"],
                "نام کاربری": row["username"],
                "پروژه": row["project_title"],
                "بازه": row["period_title"],
                "وضعیت": row["status_label"],
            }
            for row in missing_rows
        ]
    )

    late_df = pd.DataFrame(
        [
            {
                "کاربر": row["user_full_name"],
                "نام کاربری": row["username"],
                "پروژه": row["project_title"],
                "تاریخ ثبت": to_jalali_datetime(row["submitted_at"]) if row["submitted_at"] else "-",
                "تعداد پیوست": to_persian_digits(row["file_count"]),
                "فایل‌های پیوست": "، ".join([file["original_filename"] for file in row.get("files", [])]),
                "فعالیت‌های انجام‌شده": row["activities_done"],
                "نتایج حاصل‌شده": row["results_achieved"],
                "اقدامات آتی": row["next_actions"],
                "شاخص‌ها": row["kpi_text"],
            }
            for row in late_rows
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        overview_df.to_excel(writer, sheet_name="Overview", index=False)
        submitted_df.to_excel(writer, sheet_name="Submitted", index=False)
        missing_df.to_excel(writer, sheet_name="Missing", index=False)
        late_df.to_excel(writer, sheet_name="Late", index=False)

        workbook = writer.book

        for worksheet in workbook.worksheets:
            worksheet.sheet_view.rightToLeft = True

            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter

                for cell in column_cells:
                    if cell.value is not None:
                        max_length = max(max_length, len(str(cell.value)))

                adjusted_width = min(max_length + 4, 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    return output.getvalue()