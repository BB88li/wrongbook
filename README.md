# 考研智能错题本系统（wrongbook）

面向考研复习的错题管理与复习调度系统。**作者本人即第一批用户**，系统在 2026 年 12 月冲刺期实际使用。

技术栈：FastAPI + SQLAlchemy（SQLite / MySQL）+ Vue 3 + Element Plus + ECharts / 大模型 API（规划中）

> 说明：本仓库是本科毕业设计的工程实现部分，论文写作与执行计划见工作区上一级的《毕设执行方案.md》。

## 目录结构

```
wrongbook/
├── backend/                    # Python + FastAPI
│   ├── app/
│   │   ├── main.py             # 入口（CORS + 路由注册）
│   │   ├── init_db.py          # 建表 + 种子数据（用户 / 知识点目录），幂等
│   │   ├── core/
│   │   │   ├── config.py       # 配置，.env 可覆盖
│   │   │   └── constants.py    # 科目 / 错因常量（避免魔法字符串）
│   │   ├── db/base.py          # 引擎与会话；SQLite 打开外键约束
│   │   ├── models/             # ORM：users / knowledge_points / mistakes / review_states / review_logs
│   │   ├── schemas/            # Pydantic 请求响应
│   │   ├── services/sm2.py     # ★ 调度算法：SM-2 + 考试倒计时约束
│   │   └── api/routes.py       # 错题 CRUD / 复习提交 / 今日队列 / 设置 / 知识点
│   ├── scripts/
│   │   ├── smoke_test.py       # 端到端冒烟测试（会自建并清理数据）
│   │   └── backup_db.py        # SQLite 在线备份，保留最近 14 份
│   ├── tests/test_sm2.py       # 算法单元测试（unittest，15 条）
│   └── pyproject.toml          # uv 管理依赖
└── frontend/                   # Vue 3 + Vite + Element Plus
    └── src/
        ├── App.vue             # 布局（桌面侧边栏 / 手机顶部导航）
        ├── router/             # 错题列表 / 录入 / 今日复习 / 学习报告 / 设置
        ├── api/                # axios 封装（统一错误提示，/api 代理到后端）
        └── views/              # 五个页面
```

## 快速启动

### 后端（端口 8000）

```bash
cd backend
uv sync                       # 装依赖（或直接复用已有 .venv）
uv run python -m app.init_db  # 建表 + 种子数据（幂等，可重复跑）
uv run uvicorn app.main:app --reload
# 接口文档：http://127.0.0.1:8000/docs
```

### 前端（端口 5173，/api 自动代理到后端）

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

### 手机上用（录入错题的真实场景是拍照，建议在手机上开）

1. 后端监听所有网卡：`uv run uvicorn app.main:app --host 0.0.0.0 --reload`
2. 前端也监听所有网卡：`npm run dev -- --host`
3. 手机与电脑连同一 WiFi，浏览器打开 `http://<电脑局域网IP>:5173`

> 页面已做窄屏适配（侧边栏变顶部导航、表单单列），但拍照上传功能尚未实现，目前需手动输入题干。

## 已实现

- 错题录入：科目 / 题干 / **正确答案** / 解析 / 我的作答 / 错因 / 知识点 / 来源
- 错题列表：科目筛选、分页参数、删除（级联删除调度状态与复习流水）
- 今日复习：先回忆 → 查看答案与解析 → 三档自评 → 调度下次日期
- 复习调度：修正版 SM-2 + **考试倒计时约束** + 考前模式优先级排序
- 复习流水：每次复习记录质量、前后间隔、EF、是否失败（供报告与实验使用）
- 设置：考试日期、每日复习上限、距考天数
- 知识点目录：高数 12 章 + 线代 5 章（两周内可补节级）
- 统一错误提示、参数校验、SQLite 外键约束

## 待接入（按计划）

- [ ] 拍照 + 多模态大模型识别题目（`question_image` 字段与 `python-multipart` 依赖已就绪）
- [ ] AI 解析：考点 / 错因 / 通用解法
- [ ] AI 同类变式题生成
- [ ] 学习报告可视化（ECharts）：知识点分布 / 错因占比 / 掌握度曲线（数据源已就绪）
- [ ] 登录（当前单用户 `cache`）
- [ ] 调度算法对比实验（模拟器 + 真实使用数据）

## 测试

```bash
# 算法单元测试（15 条，秒级）
cd backend && uv run python -m unittest discover -s tests -v

# 端到端冒烟测试（需要后端已在 8123 端口运行）
uv run uvicorn app.main:app --port 8123   # 终端 1
uv run python scripts/smoke_test.py       # 终端 2
```

## 数据备份

```bash
cd backend && uv run python scripts/backup_db.py
```

输出到 `backend/data/backups/`，保留最近 14 份。建议加进 Windows 任务计划每天跑一次——答辩前丢数据是真实发生过的事故。

## 调度算法要点

完整设计与参数表见论文第 4.5 节，代码在 `app/services/sm2.py`：

| 规则 | 取值 | 原因 |
|---|---|---|
| 首次 / 第二次间隔 | 1 / 6 天 | SM-2 原值 |
| 后续间隔 | 上次间隔 × EF | SM-2 原值 |
| 失败 | 计数归零、间隔回 1 天、EF 扣 0.15–0.3 | 原实现不清零，实测会跳到 30 天 |
| 间隔上限 | 180 天 | 原实现无上限，n=20 时算出 3800 万天 |
| EF 范围 | 1.3 – 2.8 | 下限来自 SM-2，上限防爆炸 |
| 错因初始 EF | 粗心 2.7 / 方法 2.4 / 概念 2.1 | 概念性错误遗忘更快 |
| 考试倒计时 | 间隔 ≤ 距考天数 − 3 | 保证考前能排上 |
| 考前模式 | 剩余 ≤ 7 天，每天 + 按优先级 | 冲刺期需求 |

优先级 = 0.5×错因权重 + 0.3×(1−掌握度) + 0.2×历史遗忘比例。

## 接口清单

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/mistakes` | 录入错题（同时建调度状态） |
| GET | `/api/v1/mistakes` | 列表（subject / limit / offset） |
| GET | `/api/v1/mistakes/{id}` | 详情 |
| PUT | `/api/v1/mistakes/{id}` | 更新（必填字段不可置空） |
| DELETE | `/api/v1/mistakes/{id}` | 删除（级联） |
| POST | `/api/v1/reviews` | 提交复习反馈，返回新调度结果 |
| GET | `/api/v1/reviews/due` | 今日队列（富卡片：题干+答案+掌握度） |
| GET/PUT | `/api/v1/settings` | 考试日期 / 每日上限 |
| GET | `/api/v1/knowledge-points` | 知识点目录 |
| GET | `/health` | 健康检查 |

## 数据库切换

默认 SQLite（零配置可跑）。切 MySQL：

1. `CREATE DATABASE wrongbook CHARACTER SET utf8mb4;`
2. `cp .env.example .env`，填 `DATABASE_URL=mysql+pymysql://root:密码@localhost:3306/wrongbook?charset=utf8mb4`
3. `uv run python -m app.init_db`

> 注意：`create_all` 只建新表，不会改已有表结构。字段调整后如果报 column 不存在，先备份再删库重建。

## 已知限制

- 单用户、无登录（`user_id` 未做越权校验，多用户前必须补）
- 无数据库迁移（Alembic 待接入），字段变更靠删库重建
- 每日复习上限只影响队列展示，不是硬性截止
- 学习报告仍是占位页

## 更新日志

- **v0.2.0（2026-11）**：修复 SM-2 失败不清零与间隔无上限；拆 `review_states` / `review_logs`；补正确答案与解析字段；加考试倒计时与考前模式；修级联删除与字段校验；加设置页、统一错误提示、移动端适配、单元测试、冒烟测试、备份脚本
- **v0.1.0（2026-09）**：骨架版，错题 CRUD + 基础 SM-2 + 四个页面
