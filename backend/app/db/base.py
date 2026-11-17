"""数据库引擎与会话。"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

IS_SQLITE = settings.database_url.startswith("sqlite")

# SQLite 多线程需要 check_same_thread=False；MySQL 不需要但无副作用
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


if IS_SQLITE:
    # SQLite 默认不启用外键约束！不打开的话，删除错题时数据库层面的
    # ON DELETE CASCADE 形同虚设，会留下孤儿复习记录。
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db():
    """FastAPI 依赖：每个请求一个会话，用完关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
