"""初始化数据库：建表 + 种子数据（默认用户、教科书知识点目录）。

用法：uv run python -m app.init_db

注意：create_all 只建缺失的表，不会修改已存在表的结构。
调整字段后如果报 column 不存在，删掉 data/wrongbook.db 重新初始化即可
（跑之前先执行 scripts/backup_db.py 备份）。
"""
from app.db.base import Base, SessionLocal, engine
from app.models import KnowledgePoint, User  # 统一导入，确保所有表注册到 metadata
from app.models import Mistake, ReviewLog, ReviewState  # noqa: F401

# 教科书目录（章级别，节后续按需补）——高数同济版 / 线代同济版
KNOWLEDGE_SEED = {
    "高数": [
        "函数与极限",
        "导数与微分",
        "微分中值定理与导数的应用",
        "不定积分",
        "定积分",
        "定积分的应用",
        "微分方程",
        "空间解析几何与向量代数",
        "多元函数微分法及其应用",
        "重积分",
        "曲线积分与曲面积分",
        "无穷级数",
    ],
    "线代": [
        "行列式",
        "矩阵及其运算",
        "矩阵的初等变换与线性方程组",
        "向量组的线性相关性",
        "相似矩阵及二次型",
    ],
}


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 默认用户（骨架单用户；考试日期后续在设置页填）
        if db.query(User).filter_by(username="cache").first() is None:
            db.add(User(username="cache", password_hash=""))
            print("已创建默认用户: cache")

        # 知识点种子（幂等：按 (subject, name) 去重）
        existing = {(kp.subject, kp.name) for kp in db.query(KnowledgePoint).all()}
        for subject, chapters in KNOWLEDGE_SEED.items():
            for i, chapter in enumerate(chapters):
                if (subject, chapter) not in existing:
                    db.add(KnowledgePoint(subject=subject, name=chapter, sort_order=i))
        db.commit()
        print(
            "知识点目录已就绪（高数 %d 章 / 线代 %d 章）"
            % (len(KNOWLEDGE_SEED["高数"]), len(KNOWLEDGE_SEED["线代"]))
        )
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成 ->", engine.url.render_as_string(hide_password=True))
