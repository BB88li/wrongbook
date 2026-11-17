"""错题表：核心业务表。

字段分三组：题目本体、我的作答、标准答案与解析。
标准答案是复习闭环的关键——没有它，复习时无法自测对错。
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ERROR_TYPES  # noqa: F401  （保持向后兼容的导出）
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.review import ReviewLog, ReviewState


class Mistake(Base):
    __tablename__ = "mistakes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(20), index=True)  # 高数 / 线代
    knowledge_point_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_points.id"), nullable=True)
    error_type: Mapped[str] = mapped_column(String(20), default="careless")  # 粗心/概念不清/方法不会

    # 题目本体：照片路径 + 结构化文本
    question_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    question_text: Mapped[str] = mapped_column(Text)  # AI 识别或手动输入
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 2023 数一真题 / 660 题

    # 我的作答
    my_answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 标准答案与解析（复习时先自评、再对答案）
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI 生成结果（与人工整理的解析分开存，便于论文里统计 AI 产出质量）
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_variant: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 每道错题只有一条当前调度状态；删除错题时级联删除状态与复习流水
    review_state: Mapped["ReviewState | None"] = relationship(
        back_populates="mistake",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
    review_logs: Mapped[list["ReviewLog"]] = relationship(
        back_populates="mistake",
        cascade="all, delete-orphan",
    )
