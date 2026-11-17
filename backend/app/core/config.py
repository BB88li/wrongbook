"""应用配置：数据库连接等，支持 .env 覆盖。"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录 = backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 默认用 SQLite（开发零配置兜底），生产/答辩切 MySQL：
# 在 .env 里写 DATABASE_URL=mysql+pymysql://root:密码@localhost:3306/wrongbook?charset=utf8mb4
DEFAULT_DATABASE_URL = f"sqlite:///{DATA_DIR / 'wrongbook.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "考研智能错题本系统"
    app_version: str = "0.2.0"

    # SQLite: sqlite:///绝对路径    MySQL: mysql+pymysql://user:pass@host:port/db?charset=utf8mb4
    database_url: str = DEFAULT_DATABASE_URL

    # 与指导老师确认前先用占位；AI 密钥放 .env，不进 git
    ai_multimodal_api_key: str = ""
    ai_text_api_key: str = ""

    # 允许跨域的来源，逗号分隔；* 表示全部放开（仅开发/演示）
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
