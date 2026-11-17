"""FastAPI 应用入口。

开发启动（前端走 Vite，端口 5173，/api 代理到这里）：
    uv run uvicorn app.main:app --reload

单端口模式（手机/答辩演示用，一个进程同时提供接口和页面）：
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
    浏览器访问 http://<电脑局域网IP>:8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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


# --------------------------------------------------------------------------
# 可选：如果前端已经构建过（frontend/dist 存在），由后端直接托管。
# 好处是手机只需要一个地址、一个端口，不用同时跑 Vite，也不用管代理。
# --------------------------------------------------------------------------
DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if DIST_DIR.is_dir():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        """静态资源命中就返回文件，否则回退到 index.html（支持前端路由刷新）。"""
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
