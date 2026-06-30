from sqlalchemy import Boolean, Column, DateTime, Integer, String, Time, func

from utils.db import Base


class DeadlineSetting(Base):
    __tablename__ = "deadline_settings"

    id = Column(Integer, primary_key=True, index=True)

    report_type = Column(String(20), nullable=False, unique=True)
    # weekly / monthly

    deadline_offset_days = Column(Integer, nullable=False, default=0)
    # چند روز بعد از پایان دوره

    deadline_time = Column(Time, nullable=False)
    # ساعت ددلاین

    grace_days = Column(Integer, nullable=False, default=0)
    # چند روز بعد از ددلاین اصلی هنوز ثبت/ویرایش مجاز است

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())