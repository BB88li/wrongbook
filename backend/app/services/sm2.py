"""复习调度算法：修正后的 SM-2 + 考试倒计时约束。

与教科书 SM-2 的差异（也是论文第 4.5 节要讲清楚的部分）：

1. 失败必须重置复习计数。原实现只把间隔打回 1 天、n 不清零，
   结果一道题失败后，下一次成功会直接跳到第 n 档间隔（实测会跳到 30 天），
   等于把最该复习的题推远了。
2. 间隔上限。原实现的指数增长没有封顶，n=20 时算出 3800 万天。
3. EF 上下限。下限 1.3 来自 SM-2 原文，上限 2.8 防止间隔爆炸。
4. 错因先验：粗心题的初始 EF 高于概念不清的题（见 INITIAL_EF）。
5. 截止日期约束：通用记忆软件假设无限期学习，而考研有考试日期。
   剩余天数不足时压缩间隔；进入考前 7 天改为每天按优先级排。
"""
from dataclasses import dataclass
from datetime import date, timedelta

# ---- 参数（论文里要有一张参数表，改动时同步更新）----
MAX_INTERVAL = 180  # 最大间隔（天）
MIN_EF = 1.3  # SM-2 规定的 EF 下限
MAX_EF = 2.8  # 自定上限，防止 EF 单调上涨导致间隔爆炸
RESERVE_DAYS = 3  # 考前预留天数
EXAM_MODE_WINDOW = 7  # 剩余天数 <= 7 进入考前模式

# 错因 -> 初始 EF：概念不清的题遗忘更快，给的 EF 更低
INITIAL_EF = {"careless": 2.7, "method": 2.4, "concept": 2.1}
# 错因 -> 失败时 EF 的惩罚幅度
FAIL_PENALTY = {"careless": 0.15, "method": 0.2, "concept": 0.3}

# 错因权重：考前模式排序用
ERROR_WEIGHT = {"concept": 1.0, "method": 0.8, "careless": 0.4}


def initial_ef(error_type: str) -> float:
    """新建错题时的初始 EF。"""
    return INITIAL_EF.get(error_type, 2.5)


@dataclass(frozen=True)
class ScheduleResult:
    """一次调度计算的结果。"""

    due_date: date
    interval_days: int
    review_count: int
    ease_factor: float
    lapses: int
    mode: str  # normal / capped / exam


def next_interval(
    review_count: int,
    prev_interval: int,
    ease_factor: float,
    quality: int,
    error_type: str = "careless",
) -> tuple[int, int, float]:
    """纯 SM-2 部分，不涉及考试日期，便于单元测试。

    参数:
        review_count: 已连续成功次数 n
        prev_interval: 上一次的间隔（天），SM-2 要用它乘以 EF
        ease_factor: 当前 EF
        quality: 本次反馈 0-5（0-2 忘了 / 3 模糊 / 4-5 记得）
        error_type: 错因，决定失败时的 EF 惩罚
    返回:
        (新的 n, 新的间隔天数, 新的 EF)
    """
    if quality < 3:
        # 失败：计数归零、间隔回到 1 天，EF 按错因打折
        penalty = FAIL_PENALTY.get(error_type, 0.2)
        new_ef = max(MIN_EF, round(ease_factor - penalty, 2))
        return 0, 1, new_ef

    # 成功：SM-2 的 EF 更新公式
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = round(min(MAX_EF, max(MIN_EF, new_ef)), 2)

    if review_count == 0:
        days = 1
    elif review_count == 1:
        days = 6
    else:
        days = round(prev_interval * new_ef)

    days = max(1, min(MAX_INTERVAL, days))
    return review_count + 1, days, new_ef


def schedule(
    *,
    review_count: int,
    interval_days: int,
    ease_factor: float,
    lapses: int,
    quality: int,
    error_type: str,
    today: date,
    exam_date: date | None,
) -> ScheduleResult:
    """完整调度：SM-2 + 考试倒计时约束。"""
    new_count, days, new_ef = next_interval(
        review_count, interval_days, ease_factor, quality, error_type
    )
    new_lapses = lapses + (1 if quality < 3 else 0)

    mode = "normal"
    if exam_date is not None:
        remain = (exam_date - today).days
        if remain > 0:
            if remain <= EXAM_MODE_WINDOW:
                # 考前模式：每天过一遍，顺序改由优先级决定
                days, mode = 1, "exam"
            else:
                cap = remain - RESERVE_DAYS
                if cap < 1:
                    days, mode = 1, "exam"
                elif days > cap:
                    days, mode = cap, "capped"

    return ScheduleResult(
        due_date=today + timedelta(days=days),
        interval_days=days,
        review_count=new_count,
        ease_factor=new_ef,
        lapses=new_lapses,
        mode=mode,
    )


def mastery_of(review_count: int, last_quality: int | None, lapses: int) -> float:
    """错题掌握度（0-1），用于报告与考前排序。

    刻意做得简单：一半看复习次数，一半看最近一次回忆质量，失败次数扣分。
    论文里说明这是经验公式即可，不必包装成模型。
    """
    if review_count == 0 and last_quality is None:
        return 0.0
    quality_part = (last_quality / 5) if last_quality is not None else 0.0
    score = 0.5 * min(1.0, review_count / 5) + 0.5 * quality_part
    score -= 0.1 * lapses
    return round(max(0.0, min(1.0, score)), 2)


def priority_of(
    error_type: str,
    mastery: float,
    lapses: int,
    review_count: int,
) -> float:
    """考前模式的排序分（越大越先复习）。

    0.5 错因权重 + 0.3 掌握度缺口 + 0.2 历史遗忘比例
    """
    weight = ERROR_WEIGHT.get(error_type, 0.6)
    attempts = max(1, review_count + lapses)
    lapse_ratio = lapses / attempts
    return round(0.5 * weight + 0.3 * (1.0 - mastery) + 0.2 * lapse_ratio, 3)
