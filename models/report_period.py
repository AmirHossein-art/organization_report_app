from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text, func

from utils.db import Base


class ReportPeriod(Base):
    __tablename__ = "report_periods"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    report_type = Column(String(20), nullable=False, index=True)
    # weekly / monthly

    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)

    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())