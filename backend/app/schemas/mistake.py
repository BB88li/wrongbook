"""Pydantic 请求/响应模型。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MistakeCreate(BaseModel):
    subject: str = Field(..., description="高数 / 线代")
    question_text: str = Field(..., description="题目内容（AI 识别或手动输入）")
    knowledge_point_id: int | None = None
    error_type: str = Field("careless", description="careless=粗心 / concept=概念不清 / method=方法不会")
    my_answer: str | None = None
    question_image: str | None = None


class MistakeUpdate(BaseModel):
    subject: str | None = None
    question_text: str | None = None
    knowledge_point_id: int | None = None
    error_type: str | None = None
    my_answer: str | None = None


class MistakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    question_text: str
    knowledge_point_id: int | None
    error_type: str
    my_answer: str | None
    ai_analysis: str | None
    ai_variant: str | None
    created_at: datetime


class ReviewSubmit(BaseModel):
    mistake_id: int
    quality: int = Field(..., ge=0, le=5, description="0-5：忘了=0-2，模糊=3，还记得=4-5")
    reviewed_at: date | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mistake_id: int
    review_count: int
    ease_factor: float
    interval_days: int
    due_date: date
    last_quality: int | None
