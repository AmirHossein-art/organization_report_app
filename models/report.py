from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from utils.db import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    report_type = Column(String(20), nullable=False)  # weekly / monthly

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    activities_done = Column(Text, nullable=True)
    results_achieved = Column(Text, nullable=True)
    next_actions = Column(Text, nullable=True)
    kpi_text = Column(Text, nullable=True)

    status = Column(String(30), nullable=False, default="submitted")
    # submitted / late / approved / rejected

    is_late = Column(Boolean, nullable=False, default=False)

    submitted_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    user = relationship("User")
    project = relationship("Project")