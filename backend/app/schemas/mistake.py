"""Pydantic 请求/响应模型。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import ERROR_TYPES, SUBJECTS


class MistakeCreate(BaseModel):
    subject: str = Field(..., description="高数 / 线代")
    question_text: str = Field(..., min_length=1, description="题目内容")
    knowledge_point_id: int | None = None
    error_type: str = Field("careless", description="careless / concept / method")
    my_answer: str | None = None
    correct_answer: str | None = None
    analysis: str | None = None
    source: str | None = Field(None, max_length=100, description="真题年份 / 题集来源")
    question_image: str | None = None

    @field_validator("subject")
    @classmethod
    def _check_subject(cls, v: str) -> str:
        if v not in SUBJECTS:
            raise ValueError(f"科目必须是 {SUBJECTS} 之一")
        return v

    @field_validator("error_type")
    @classmethod
    def _check_error_type(cls, v: str) -> str:
        if v not in ERROR_TYPES:
            raise ValueError(f"错因必须是 {ERROR_TYPES} 之一")
        return v

    @field_validator("question_text")
    @classmethod
    def _strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("题目内容不能为空")
        return v


class MistakeUpdate(BaseModel):
    """更新错题。未传的字段保持原值；传 null 也允许（用于清空选填项），
    但 subject / question_text / error_type 这三个非空字段由路由层额外校验。"""

    subject: str | None = None
    question_text: str | None = None
    knowledge_point_id: int | None = None
    error_type: str | None = None
    my_answer: str | None = None
    correct_answer: str | None = None
    analysis: str | None = None
    source: str | None = None

    @field_validator("subject")
    @classmethod
    def _check_subject(cls, v: str | None) -> str | None:
        if v is not None and v not in SUBJECTS:
            raise ValueError(f"科目必须是 {SUBJECTS} 之一")
        return v

    @field_validator("error_type")
    @classmethod
    def _check_error_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ERROR_TYPES:
            raise ValueError(f"错因必须是 {ERROR_TYPES} 之一")
        return v


class MistakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    question_text: str
    question_image: str | None
    source: str | None
    knowledge_point_id: int | None
    error_type: str
    my_answer: str | None
    correct_answer: str | None
    analysis: str | None
    ai_analysis: str | None
    ai_variant: str | None
    created_at: datetime
    updated_at: datetime


class ReviewSubmit(BaseModel):
    mistake_id: int
    quality: int = Field(..., ge=0, le=5, description="0-5：忘了=0-2，模糊=3，记得=4-5")
    reviewed_at: date | None = None
    response_seconds: int | None = Field(None, ge=0, le=3600, description="思考用时（秒），选填")


class ReviewSubmitOut(BaseModel):
    """复习提交后返回的新调度结果。前端用它显示「下次 N 天后」。"""

    mistake_id: int
    review_count: int
    ease_factor: float
    interval_days: int
    due_date: date
    lapses: int
    is_lapse: bool
    mode: str  # normal / capped / exam


class ReviewCardOut(BaseModel):
    """今日复习队列的一张卡片：把错题内容和调度状态一起返回，
    前端不用再拉一次全量错题列表。"""

    mistake_id: int
    subject: str
    error_type: str
    error_type_label: str
    question_text: str
    question_image: str | None
    correct_answer: str | None
    analysis: str | None
    source: str | None
    knowledge_point: str | None

    review_count: int
    ease_factor: float
    interval_days: int
    due_date: date
    last_quality: int | None
    lapses: int
    mastery: float
    priority: float


class SettingsOut(BaseModel):
    exam_date: date | None
    daily_review_limit: int
    days_to_exam: int | None


class SettingsUpdate(BaseModel):
    exam_date: date | None = None
    daily_review_limit: int | None = Field(None, ge=1, le=200)
