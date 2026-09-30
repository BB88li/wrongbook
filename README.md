# 考研智能错题本系统（wrongbook）

基于遗忘曲线（SM-2）与 AI 讲解的考研错题管理系统。**本人即第一批用户。**

技术栈：FastAPI + SQLAlchemy / MySQL + Vue 3 + Element Plus + ECharts / 大模型 API（识别、讲解、出题）

## 项目结构

```
wrongbook/
├── backend/            # Python + FastAPI
│   ├── app/
│   │   ├── main.py         # 入口：uv run uvicorn app.main:app --reload
│   │   ├── init_db.py      # 初始化：建表 + 种子数据（用户/知识点目录）
│   │   ├── core/config.py  # 配置（.env 可覆盖，默认 SQLite）
│   │   ├── db/base.py      # SQLAlchemy 引擎与会话
│   │   ├── models/         # ORM：users / knowledge_points / mistakes / review_records
│   │   ├── schemas/        # Pydantic 请求响应
│   │   ├── services/sm2.py # ★ 遗忘曲线调度算法（答辩理论点）
│   │   └── api/routes.py   # 错题 CRUD / 复习提交 / 今日队列 / 知识点
│   ├── .env.example        # 复制为 .env 填数据库与 AI 密钥
│   └── pyproject.toml      # uv 管理依赖
└── frontend/           # Vue 3 + Vite + Element Plus
    └── src/
        ├── App.vue         # 布局（侧边菜单）
        ├── router/         # 错题列表 / 录入 / 今日复习 / 学习报告
        ├── api/            # axios 封装（/api/v1 代理到后端）
        └── views/          # 四个页面
```

## 快速启动

后端（端口 8000）：
```bash
cd backend
uv sync                       # 装依赖
uv run python -m app.init_db  # 建表 + 种子数据（幂等，可重复跑）
uv run uvicorn app.main:app --reload
# 接口文档：http://127.0.0.1:8000/docs
```

前端（端口 5173，/api 自动代理到后端）：
```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

## 已实现的骨架功能

- 错题录入：科目 / 题目文本 / 错误原因（粗心·概念不清·方法不会）/ 知识点（教科书目录）
- 错题列表：按科目筛选、删除
- 今日复习队列：到期自动进入，反馈"还记得 / 模糊 / 忘了"→ SM-2 动态调整下次间隔
- 知识点目录：高数 12 章 + 线代 5 章（教科书目录，两级结构预留）

## 待接入（按毕设时间线 2027-02 开发主力期）

- [ ] 拍照 + 多模态大模型识别题目（当前是手动输入）
- [ ] AI 解析：考点 / 错因 / 通用解法
- [ ] AI 同类变式题生成
- [ ] 学习报告可视化（ECharts）：知识点分布 / 错因占比 / 掌握度曲线
- [ ] 切 MySQL（.env 里配 DATABASE_URL）
- [ ] 登录（当前单用户 cache）

## 数据库切换

默认 SQLite（零配置可跑）。切 MySQL：
1. MySQL 里建库：`CREATE DATABASE wrongbook CHARACTER SET utf8mb4;`
2. `cp .env.example .env`，填 `DATABASE_URL=mysql+pymysql://root:密码@localhost:3306/wrongbook?charset=utf8mb4`
3. `uv run python -m app.init_db`

## 答辩要点（备忘）

- 卖点实现：`backend/app/services/sm2.py` —— 借鉴 Anki SM-2，间隔随回忆质量动态变化
- 全栈无"发明"环节：成熟 API + 本科课程覆盖，AI 部分全走大模型接口
