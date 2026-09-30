"""错题 API：CRUD + 复习提交（SM-2 调度） + 今日复习队列。"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.knowledge import KnowledgePoint
from app.models.mistake import Mistake
from app.models.review import ReviewRecord
from app.models.user import User
from app.schemas.mistake import (
    MistakeCreate,
    MistakeOut,
    MistakeUpdate,
    ReviewOut,
    ReviewSubmit,
)
from app.services.sm2 import next_interval

router = APIRouter(prefix="/api/v1", tags=["mistakes"])

# 骨架阶段单用户：取第一个用户（登录功能后置）
DEFAULT_USERNAME = "cache"


def _get_default_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == DEFAULT_USERNAME))
    if user is None:
        raise HTTPException(status_code=500, detail="数据库还没有用户，请先运行 python -m app.init_db")
    return user


@router.post("/mistakes", response_model=MistakeOut)
def create_mistake(payload: MistakeCreate, db: Session = Depends(get_db)):
    """录入一条错题（AI 识别/解析接入前的骨架版）。"""
    user = _get_default_user(db)
    mistake = Mistake(
        user_id=user.id,
        subject=payload.subject,
        question_text=payload.question_text,
        knowledge_point_id=payload.knowledge_point_id,
        error_type=payload.error_type,
        my_answer=payload.my_answer,
        question_image=payload.question_image,
    )
    db.add(mistake)
    db.flush()  # 拿到 mistake.id

    # 首次加入：创建复习记录，第 1 天到期（明天）
    record = ReviewRecord(
        mistake_id=mistake.id,
        user_id=user.id,
        review_count=0,
        ease_factor=2.5,
        interval_days=1,
        due_date=date.today() + timedelta(days=1),
    )
    db.add(record)
    db.commit()
    db.refresh(mistake)
    return mistake


@router.get("/mistakes", response_model=list[MistakeOut])
def list_mistakes(subject: str | None = None, db: Session = Depends(get_db)):
    """错题列表，可按科目过滤。"""
    user = _get_default_user(db)
    stmt = select(Mistake).where(Mistake.user_id == user.id).order_by(Mistake.created_at.desc())
    if subject:
        stmt = stmt.where(Mistake.subject == subject)
    return db.scalars(stmt).all()


@router.get("/mistakes/{mistake_id}", response_model=MistakeOut)
def get_mistake(mistake_id: int, db: Session = Depends(get_db)):
    mistake = db.get(Mistake, mistake_id)
    if mistake is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    return mistake


@router.put("/mistakes/{mistake_id}", response_model=MistakeOut)
def update_mistake(mistake_id: int, payload: MistakeUpdate, db: Session = Depends(get_db)):
    mistake = db.get(Mistake, mistake_id)
    if mistake is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mistake, field, value)
    db.commit()
    db.refresh(mistake)
    return mistake


@router.delete("/mistakes/{mistake_id}")
def delete_mistake(mistake_id: int, db: Session = Depends(get_db)):
    mistake = db.get(Mistake, mistake_id)
    if mistake is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    db.delete(mistake)  # 级联删除复习记录由数据库外键处理（见 init_db 建表）
    db.commit()
    return {"ok": True}


@router.post("/reviews", response_model=ReviewOut)
def submit_review(payload: ReviewSubmit, db: Session = Depends(get_db)):
    """复习反馈：还记得/模糊/忘了 -> SM-2 动态调整下次间隔。"""
    user = _get_default_user(db)
    record = db.scalar(
        select(ReviewRecord).where(
            ReviewRecord.mistake_id == payload.mistake_id,
            ReviewRecord.user_id == user.id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="该错题没有复习记录")

    days, new_ef = next_interval(record.review_count, record.ease_factor, payload.quality)
    if payload.quality >= 3:
        record.review_count += 1  # 只有成功回忆才累计复习次数

    record.ease_factor = new_ef
    record.interval_days = days
    record.due_date = (payload.reviewed_at or date.today()) + timedelta(days=days)
    record.last_quality = payload.quality
    record.reviewed_at = datetime.now()

    db.commit()
    db.refresh(record)
    return record


@router.get("/reviews/due", response_model=list[ReviewOut])
def due_reviews(db: Session = Depends(get_db)):
    """今日复习队列：due_date <= 今天 的复习记录。"""
    user = _get_default_user(db)
    stmt = (
        select(ReviewRecord)
        .where(ReviewRecord.user_id == user.id, ReviewRecord.due_date <= date.today())
        .order_by(ReviewRecord.due_date)
    )
    return db.scalars(stmt).all()


@router.get("/knowledge-points")
def list_knowledge_points(db: Session = Depends(get_db)):
    """教科书目录知识点（章/节两级）。"""
    points = db.scalars(select(KnowledgePoint).order_by(KnowledgePoint.subject, KnowledgePoint.sort_order)).all()
    return [
        {
            "id": p.id,
            "subject": p.subject,
            "name": p.name,
            "parent_id": p.parent_id,
        }
        for p in points
    ]
