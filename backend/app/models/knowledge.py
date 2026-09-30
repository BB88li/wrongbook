"""知识点表：直接采用教科书目录，两级结构（章 -> 节），parent_id 为 null 表示章。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(20), index=True)  # 高数 / 线代
    name: Mapped[str] = mapped_column(String(100))  # 章节名
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_points.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)  # 章内排序

    parent: Mapped["KnowledgePoint | None"] = relationship(remote_side=[id], backref="children")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
