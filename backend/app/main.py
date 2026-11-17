"""FastAPI 应用入口。开发启动：uv run uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)

# 开发/答辩演示用：前端可能跑在 5173 或局域网 IP 上，放开跨域。
# 正式部署时应收紧到具体域名（见 .env 的 CORS_ORIGINS）。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
