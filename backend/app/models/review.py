"""复习记录表：每次复习一条记录，SM-2 状态字段随反馈更新。"""
from datetime import datetime, date

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mistake_id: Mapped[int] = mapped_column(ForeignKey("mistakes.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # SM-2 状态（从错题"首次加入"开始累计）
    review_count: Mapped[int] = mapped_column(Integer, default=0)  # 已复习次数 n
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)  # EF，记忆难度系数
    interval_days: Mapped[int] = mapped_column(Integer, default=1)  # 当前间隔（天）

    due_date: Mapped[date] = mapped_column(Date, index=True)  # 下次该复习的日期
    last_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-5 回忆质量

    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    mistake: Mapped["Mistake"] = relationship(back_populates="reviews")  # noqa: F821
