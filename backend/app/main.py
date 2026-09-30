"""FastAPI 应用入口。开发启动：uv run uvicorn app.main:app --reload"""
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
