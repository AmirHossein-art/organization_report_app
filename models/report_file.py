from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from utils.db import Base


class ReportFile(Base):
    __tablename__ = "report_files"

    id = Column(Integer, primary_key=True, index=True)

    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)

    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)

    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())

    report = relationship("Report")