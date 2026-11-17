"""全局常量：科目与错因分类。集中一处，避免前后端各写一遍魔法字符串。"""

SUBJECTS = ("高数", "线代")

# 错因：light 阶段只有三类，够用且便于统计
ERROR_TYPES = ("careless", "concept", "method")
ERROR_TYPE_LABELS = {
    "careless": "粗心",
    "concept": "概念不清",
    "method": "方法不会",
}
