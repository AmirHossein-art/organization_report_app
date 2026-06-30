from datetime import date, datetime

import jdatetime


PERSIAN_DIGITS = {
    "0": "۰",
    "1": "۱",
    "2": "۲",
    "3": "۳",
    "4": "۴",
    "5": "۵",
    "6": "۶",
    "7": "۷",
    "8": "۸",
    "9": "۹",
}


def to_persian_digits(value) -> str:
    if value is None:
        return ""

    text = str(value)

    for english_digit, persian_digit in PERSIAN_DIGITS.items():
        text = text.replace(english_digit, persian_digit)

    return text


def to_jalali_date(value: date | datetime | None) -> str:
    if not value:
        return "-"

    if isinstance(value, datetime):
        jalali_value = jdatetime.datetime.fromgregorian(datetime=value)
        formatted = jalali_value.strftime("%Y/%m/%d")
    else:
        jalali_value = jdatetime.date.fromgregorian(date=value)
        formatted = jalali_value.strftime("%Y/%m/%d")

    return to_persian_digits(formatted)


def to_jalali_datetime(value: datetime | None) -> str:
    if not value:
        return "-"

    jalali_value = jdatetime.datetime.fromgregorian(datetime=value)
    formatted = jalali_value.strftime("%Y/%m/%d - %H:%M")

    return to_persian_digits(formatted)


def report_type_label(report_type: str) -> str:
    labels = {
        "weekly": "هفتگی",
        "monthly": "ماهانه",
    }

    return labels.get(report_type, report_type or "-")


def report_status_label(status: str) -> str:
    labels = {
        "submitted": "ثبت‌شده",
        "late": "تأخیری",
        "approved": "تأییدشده",
        "rejected": "ردشده",
    }

    return labels.get(status, status or "-")


def report_period_label(period_start, period_end) -> str:
    return f"{to_jalali_date(period_start)} تا {to_jalali_date(period_end)}"