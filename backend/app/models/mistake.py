"""错题表：核心业务表。AI 识别/解析结果落在这里。"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.review import ReviewRecord

# 错误原因分类（学习报告的数据基石）
ERROR_TYPES = ("careless", "concept", "method")  # 粗心 / 概念不清 / 方法不会


class Mistake(Base):
    __tablename__ = "mistakes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(20), index=True)  # 高数 / 线代
    knowledge_point_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_points.id"), nullable=True)
    error_type: Mapped[str] = mapped_column(String(20), default="careless")  # 粗心/概念不清/方法不会

    # 题目本体：照片原图（存本地文件路径，骨架先存文件名）+ 结构化文本
    question_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    question_text: Mapped[str] = mapped_column(Text)  # AI 识别或手动输入
    my_answer: Mapped[str | None] = mapped_column(Text, nullable=True)  # 我的错误解答（可选）

    # AI 解析结果
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)  # 考点/错因/通用解法
    ai_variant: Mapped[str | None] = mapped_column(Text, nullable=True)  # 同类变式题

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    reviews: Mapped[list["ReviewRecord"]] = relationship(back_populates="mistake")  # noqa: F821
