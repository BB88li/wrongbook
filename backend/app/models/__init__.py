"""模型统一导出。

所有模型必须经过这里注册到 Base.metadata。此前每个模块各自 import，
漏掉一个（比如只 import Mistake 不 import KnowledgePoint）就会在建表/写入时
抛 NoReferencedTableError，排查成本很高。
"""
from app.models.knowledge import KnowledgePoint
from app.models.mistake import Mistake
from app.models.review import ReviewLog, ReviewState
from app.models.user import User

__all__ = ["KnowledgePoint", "Mistake", "ReviewLog", "ReviewState", "User"]
