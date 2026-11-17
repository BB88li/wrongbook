"""复习调度相关表，拆成两张：

- review_states：每道错题一条「当前调度状态」，SM-2 的 n / EF / 间隔 / 到期日存在这里。
- review_logs：每复习一次写一条流水，保留历史。

为什么拆：原实现把状态和历史混在一张表里，reviewed_at 每次被覆盖，
导致「掌握度曲线」「间隔预测误差」这类分析没有数据源，论文第 6 章做不了。
"""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReviewState(Base):
    """一道错题的当前调度状态（每题每用户一条）。"""

    __tablename__ = "review_states"
    __table_args__ = (
        UniqueConstraint("mistake_id", "user_id", name="uq_review_state_mistake_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mistake_id: Mapped[int] = mapped_column(
        ForeignKey("mistakes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # SM-2 状态量
    review_count: Mapped[int] = mapped_column(Integer, default=0)  # 连续成功次数 n
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)  # EF
    interval_days: Mapped[int] = mapped_column(Integer, default=1)  # 当前间隔
    lapses: Mapped[int] = mapped_column(Integer, default=0)  # 复习失败次数（用来识别顽固错题）

    due_date: Mapped[date] = mapped_column(Date, index=True)
    last_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    mistake: Mapped["Mistake"] = relationship(back_populates="review_state")  # noqa: F821


class ReviewLog(Base):
    """一次复习的流水记录，只增不改。"""

    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mistake_id: Mapped[int] = mapped_column(
        ForeignKey("mistakes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    reviewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    quality: Mapped[int] = mapped_column(Integer)  # 0-5
    prev_interval: Mapped[int] = mapped_column(Integer)
    next_interval: Mapped[int] = mapped_column(Integer)
    prev_ef: Mapped[float] = mapped_column(Float)
    next_ef: Mapped[float] = mapped_column(Float)
    response_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 思考用时，选填
    is_lapse: Mapped[bool] = mapped_column(Boolean, default=False)  # 本次是否失败

    mistake: Mapped["Mistake"] = relationship(back_populates="review_logs")  # noqa: F821
