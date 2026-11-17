"""用户表。骨架阶段单用户，字段为登录与个性化预留。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), default="")

    # 考试日期：调度算法要用它判断剩余窗口（创新点 1 的输入）
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    daily_review_limit: Mapped[int] = mapped_column(Integer, default=20)  # 考前模式每日上限

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
