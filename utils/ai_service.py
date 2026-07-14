import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1" 
)

def analyze_reports_with_ai(period_title, reports_data):
    """
    این تابع داده‌های خام گزارش‌ها را می‌گیرد و یک تحلیل مدیریتی برمی‌گرداند
    """
    
    # ۱. ساختن پرامپت (دستور) برای هوش مصنوعی
    system_prompt = """
    شما یک دستیار هوشمند مدیریت پروژه هستید.
    وظیفه شما این است که گزارش‌های ارائه‌شده توسط پرسنل را مطالعه کرده و یک خلاصه مدیریتی ۲ پاراگرافی ارائه دهید.
    در پاراگراف اول: وضعیت کلی پیشرفت پروژه‌ها را خلاصه کنید.
    در پاراگراف دوم: ریسک‌ها، تأخیرها یا مشکلاتی که در گزارش‌ها می‌بینید را برجسته کنید.
    پاسخ باید کاملاً به زبان فارسی رسمی و اداری باشد.
    """
    
    user_prompt = f"گزارش‌های بازه {period_title}:\n{reports_data}"

    # ۲. ارسال درخواست به مدل هوش مصنوعی
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192", # اگر از Groq استفاده کردی این را به llama3-8b-8192 تغییر بده
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"خطا در ارتباط با هوش مصنوعی: {str(e)}"