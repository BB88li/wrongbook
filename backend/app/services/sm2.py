"""SM-2 遗忘曲线调度算法（借鉴 Anki 的 SM-2，答辩理论支撑点）。

输入一次复习反馈的质量 q（0-5），更新错题的下次复习间隔。
- q >= 3：回忆成功，间隔拉长
- q < 3：回忆失败，重来（间隔回到 1 天，复习计数不清零）

初始间隔（首次加入后）：1 / 2 / 4 / 7 / 15 天……即复习计数 n 对应的
标准间隔表，与教科书式艾宾浩斯曲线一致，方便答辩对照讲。
"""

# 前几次复习的标准间隔（天）：第 n 次复习在第几天进行
DEFAULT_INTERVALS = [1, 2, 4, 7, 15, 30, 60]


def next_interval(review_count: int, ease_factor: float, quality: int) -> tuple[int, float]:
    """计算下次复习间隔与 EF。

    参数:
        review_count: 已成功复习次数 n
        ease_factor:  当前 EF（默认 2.5）
        quality:      本次反馈质量 0-5（还记得=4/5，模糊=3，忘了=0/1/2）
    返回:
        (下次间隔天数, 更新后的 EF)
    """
    # 回忆失败：无论之前排到哪，明天重来（间隔回到 1 天）
    if quality < 3:
        return 1, ease_factor

    # 回忆成功：更新 EF
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)  # SM-2 规定 EF 下限 1.3

    # 间隔：前几次按标准表走，之后按 EF 指数增长
    if review_count + 1 <= len(DEFAULT_INTERVALS):
        days = DEFAULT_INTERVALS[review_count]
    else:
        days = max(1, round(DEFAULT_INTERVALS[-1] * new_ef ** (review_count + 1 - len(DEFAULT_INTERVALS))))
    return days, round(new_ef, 2)
