# backend — FastAPI 后端

考研智能错题本的后端服务。完整说明见项目根目录 README.md。

- 启动：`uv run uvicorn app.main:app --reload`（端口 8000，接口文档 /docs）
- 初始化：`uv run python -m app.init_db`
- 依赖：uv 管理（pyproject.toml + uv.lock）
- 模块：app/main.py 入口 / models ORM / services/sm2.py 遗忘曲线算法 / api 路由
