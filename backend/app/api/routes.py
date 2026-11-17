"""错题 API：CRUD + 复习提交（SM-2 + 倒计时约束）+ 今日复习队列 + 设置。"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ERROR_TYPE_LABELS, SUBJECTS
from app.db.base import get_db
from app.models.knowledge import KnowledgePoint
from app.models.mistake import Mistake
from app.models.review import ReviewLog, ReviewState
from app.models.user import User
from app.schemas.mistake import (
    MistakeCreate,
    MistakeOut,
    MistakeUpdate,
    ReviewCardOut,
    ReviewSubmit,
    ReviewSubmitOut,
    SettingsOut,
    SettingsUpdate,
)
from app.services.sm2 import (
    EXAM_MODE_WINDOW,
    initial_ef,
    mastery_of,
    priority_of,
    schedule,
)

router = APIRouter(prefix="/api/v1", tags=["wrongbook"])

# 骨架阶段单用户：取固定用户（登录功能后置）
DEFAULT_USERNAME = "cache"

# 这三个字段在库里是 NOT NULL，更新时不允许被置空
NON_NULLABLE_FIELDS = ("subject", "question_text", "error_type")


def _get_default_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == DEFAULT_USERNAME))
    if user is None:
        raise HTTPException(status_code=500, detail="数据库还没有用户，请先运行 python -m app.init_db")
    return user


def _days_to_exam(user: User, today: date) -> int | None:
    if user.exam_date is None:
        return None
    return (user.exam_date - today).days


# --------------------------------------------------------------------------
# 错题 CRUD
# --------------------------------------------------------------------------
@router.post("/mistakes", response_model=MistakeOut, status_code=201)
def create_mistake(payload: MistakeCreate, db: Session = Depends(get_db)):
    """录入一条错题，同时建立调度状态（首次复习安排在明天）。"""
    user = _get_default_user(db)
    mistake = Mistake(
        user_id=user.id,
        subject=payload.subject,
        question_text=payload.question_text,
        knowledge_point_id=payload.knowledge_point_id,
        error_type=payload.error_type,
        my_answer=payload.my_answer,
        correct_answer=payload.correct_answer,
        analysis=payload.analysis,
        source=payload.source,
        question_image=payload.question_image,
    )
    db.add(mistake)
    db.flush()  # 拿到 mistake.id

    # 初始 EF 由错因决定：概念不清的题起点更低，复习更密
    state = ReviewState(
        mistake_id=mistake.id,
        user_id=user.id,
        review_count=0,
        ease_factor=initial_ef(payload.error_type),
        interval_days=1,
        lapses=0,
        due_date=date.today() + timedelta(days=1),
    )
    db.add(state)
    db.commit()
    db.refresh(mistake)
    return mistake


@router.get("/mistakes", response_model=list[MistakeOut])
def list_mistakes(
    subject: str | None = Query(None, description="按科目过滤"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """错题列表，按录入时间倒序，支持科目过滤与分页。"""
    user = _get_default_user(db)
    stmt = (
        select(Mistake)
        .where(Mistake.user_id == user.id)
        .order_by(Mistake.created_at.desc(), Mistake.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if subject:
        if subject not in SUBJECTS:
            raise HTTPException(status_code=422, detail=f"科目必须是 {SUBJECTS} 之一")
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

    data = payload.model_dump(exclude_unset=True)
    for field in NON_NULLABLE_FIELDS:
        if field in data:
            value = data[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                raise HTTPException(status_code=422, detail=f"字段 {field} 不能为空")

    for field, value in data.items():
        setattr(mistake, field, value)
    db.commit()
    db.refresh(mistake)
    return mistake


@router.delete("/mistakes/{mistake_id}")
def delete_mistake(mistake_id: int, db: Session = Depends(get_db)):
    """删除错题，级联删除调度状态与复习流水（ORM cascade + 数据库 ondelete）。"""
    mistake = db.get(Mistake, mistake_id)
    if mistake is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    db.delete(mistake)
    db.commit()
    return {"ok": True, "deleted_id": mistake_id}


# --------------------------------------------------------------------------
# 复习
# --------------------------------------------------------------------------
@router.post("/reviews", response_model=ReviewSubmitOut)
def submit_review(payload: ReviewSubmit, db: Session = Depends(get_db)):
    """提交一次复习反馈，按 SM-2 + 考试倒计时算出下次复习日期，并写一条流水。"""
    user = _get_default_user(db)
    state = db.scalar(
        select(ReviewState).where(
            ReviewState.mistake_id == payload.mistake_id,
            ReviewState.user_id == user.id,
        )
    )
    if state is None:
        raise HTTPException(status_code=404, detail="该错题没有复习状态记录")

    mistake = db.get(Mistake, state.mistake_id)
    if mistake is None:
        raise HTTPException(status_code=404, detail="错题不存在")

    today = payload.reviewed_at or date.today()
    result = schedule(
        review_count=state.review_count,
        interval_days=state.interval_days,
        ease_factor=state.ease_factor,
        lapses=state.lapses,
        quality=payload.quality,
        error_type=mistake.error_type,
        today=today,
        exam_date=user.exam_date,
    )

    db.add(
        ReviewLog(
            mistake_id=state.mistake_id,
            user_id=user.id,
            quality=payload.quality,
            prev_interval=state.interval_days,
            next_interval=result.interval_days,
            prev_ef=state.ease_factor,
            next_ef=result.ease_factor,
            response_seconds=payload.response_seconds,
            is_lapse=payload.quality < 3,
        )
    )

    state.review_count = result.review_count
    state.ease_factor = result.ease_factor
    state.interval_days = result.interval_days
    state.due_date = result.due_date
    state.lapses = result.lapses
    state.last_quality = payload.quality
    db.commit()

    return ReviewSubmitOut(
        mistake_id=state.mistake_id,
        review_count=result.review_count,
        ease_factor=result.ease_factor,
        interval_days=result.interval_days,
        due_date=result.due_date,
        lapses=result.lapses,
        is_lapse=payload.quality < 3,
        mode=result.mode,
    )


@router.get("/reviews/due", response_model=list[ReviewCardOut])
def due_reviews(db: Session = Depends(get_db)):
    """今日复习队列。

    - 普通模式：到期记录按 due_date 升序返回。
    - 考前模式（距考试 <= 7 天）：按优先级排序，并截断到每日上限。
    """
    user = _get_default_user(db)
    today = date.today()

    rows = db.execute(
        select(ReviewState, Mistake, KnowledgePoint.name)
        .join(Mistake, ReviewState.mistake_id == Mistake.id)
        .outerjoin(KnowledgePoint, Mistake.knowledge_point_id == KnowledgePoint.id)
        .where(ReviewState.user_id == user.id, ReviewState.due_date <= today)
    ).all()

    cards: list[ReviewCardOut] = []
    for state, mistake, kp_name in rows:
        mastery = mastery_of(state.review_count, state.last_quality, state.lapses)
        cards.append(
            ReviewCardOut(
                mistake_id=mistake.id,
                subject=mistake.subject,
                error_type=mistake.error_type,
                error_type_label=ERROR_TYPE_LABELS.get(mistake.error_type, mistake.error_type),
                question_text=mistake.question_text,
                question_image=mistake.question_image,
                correct_answer=mistake.correct_answer,
                analysis=mistake.analysis,
                source=mistake.source,
                knowledge_point=kp_name,
                review_count=state.review_count,
                ease_factor=state.ease_factor,
                interval_days=state.interval_days,
                due_date=state.due_date,
                last_quality=state.last_quality,
                lapses=state.lapses,
                mastery=mastery,
                priority=priority_of(
                    mistake.error_type, mastery, state.lapses, state.review_count
                ),
            )
        )

    remain = _days_to_exam(user, today)
    exam_mode = remain is not None and 0 < remain <= EXAM_MODE_WINDOW

    if exam_mode:
        cards.sort(key=lambda c: (-c.priority, c.due_date))
        cards = cards[: user.daily_review_limit]
    else:
        cards.sort(key=lambda c: (c.due_date, -c.priority))

    return cards


# --------------------------------------------------------------------------
# 设置（考试日期、每日上限）
# --------------------------------------------------------------------------
@router.get("/settings", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    user = _get_default_user(db)
    return SettingsOut(
        exam_date=user.exam_date,
        daily_review_limit=user.daily_review_limit,
        days_to_exam=_days_to_exam(user, date.today()),
    )


@router.put("/settings", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    user = _get_default_user(db)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return SettingsOut(
        exam_date=user.exam_date,
        daily_review_limit=user.daily_review_limit,
        days_to_exam=_days_to_exam(user, date.today()),
    )


# --------------------------------------------------------------------------
# 知识点
# --------------------------------------------------------------------------
@router.get("/knowledge-points")
def list_knowledge_points(db: Session = Depends(get_db)):
    """教科书目录知识点（章/节两级）。"""
    points = db.scalars(
        select(KnowledgePoint).order_by(KnowledgePoint.subject, KnowledgePoint.sort_order)
    ).all()
    return [
        {
            "id": p.id,
            "subject": p.subject,
            "name": p.name,
            "parent_id": p.parent_id,
        }
        for p in points
    ]
