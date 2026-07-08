from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from utils.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(150), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # user / manager

    is_active = Column(Boolean, nullable=False, default=True)

    must_change_password = Column(Boolean, nullable=False, default=False)
    password_changed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())   