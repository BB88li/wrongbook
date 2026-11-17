"""端到端冒烟测试：起服务后跑一遍完整闭环。

用法：
    # 终端 1
    cd backend && uv run uvicorn app.main:app --port 8123
    # 终端 2
    cd backend && uv run python scripts/smoke_test.py

脚本会创建若干错题并在结束时删除，不会污染日常数据。
"""
import json
import urllib.error
import urllib.request
from datetime import date, timedelta

BASE = "http://127.0.0.1:8123/api/v1"
TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()

failures: list[str] = []


def call(method: str, path: str, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, json.loads(raw) if raw else {}


def check(label: str, cond: bool, extra: str = "") -> None:
    print(("PASS  " if cond else "FAIL  ") + label + (f"   [{extra}]" if extra else ""))
    if not cond:
        failures.append(label)


created: list[int] = []


def create(subject: str, error_type: str, text: str) -> int:
    status, body = call(
        "POST",
        "/mistakes",
        {
            "subject": subject,
            "error_type": error_type,
            "question_text": text,
            "correct_answer": "答案",
            "analysis": "解析",
        },
    )
    assert status == 201, (status, body)
    created.append(body["id"])
    return body["id"]


print("=== 1. 健康检查 ===")
with urllib.request.urlopen("http://127.0.0.1:8123/health") as resp:
    health = json.loads(resp.read().decode("utf-8"))
check("GET /health", health.get("status") == "ok", str(health))

print("\n=== 2. 设置考试日期（20 天后）===")
status, body = call("PUT", "/settings", {"exam_date": (TODAY + timedelta(days=20)).isoformat()})
check("PUT /settings", status == 200 and body["days_to_exam"] == 20, str(body))

print("\n=== 3. 创建错题（三种错因）===")
a = create("高数", "concept", "概念题 A")
b = create("高数", "careless", "粗心题 B")
c = create("线代", "concept", "概念题 C")
d = create("线代", "method", "方法题 D")
check("POST /mistakes x4", len(created) == 4)
status, body = call("GET", "/mistakes")
listed = {item["id"] for item in body}
check("GET /mistakes 能查到 4 条新数据", status == 200 and set(created) <= listed, f"listed={len(listed)}")

print("\n=== 4. 新建错题当天不进队列（明天才到期）===")
status, body = call("GET", "/reviews/due")
queued = {card["mistake_id"] for card in body}
check("今日队列不含新错题", status == 200 and not (set(created) & queued), f"queue={len(queued)}")

print("\n=== 5. 复习提交：失败不清零 ===")
status, body = call("POST", "/reviews", {"mistake_id": a, "quality": 1})
check("忘了 -> 间隔 1 天、lapses=1", status == 200 and body["interval_days"] == 1 and body["lapses"] == 1, str(body))
status, body = call("POST", "/reviews", {"mistake_id": a, "quality": 5})
check("忘了之后再记得 -> 仍是 1 天（不跳档）", status == 200 and body["interval_days"] == 1 and body["review_count"] == 1, str(body))

print("\n=== 6. 补录为「昨天复习过」，让卡片进入今日队列 ===")
for mid in (b, c, d):
    status, _ = call("POST", "/reviews", {"mistake_id": mid, "quality": 5, "reviewed_at": YESTERDAY})
    assert status == 200
status, queue = call("GET", "/reviews/due")
mine = [card for card in queue if card["mistake_id"] in {b, c, d}]
check("3 张新卡片进入队列", status == 200 and len(mine) == 3, f"len={len(mine)}")
check("卡片带题干与答案", bool(mine) and mine[0]["question_text"] and mine[0]["correct_answer"] is not None)
check("卡片带掌握度", bool(mine) and 0 <= mine[0]["mastery"] <= 1, str(mine[0].get("mastery") if mine else None))

print("\n=== 7. 考前模式：按优先级排序并截断 ===")
call("PUT", "/settings", {"exam_date": (TODAY + timedelta(days=5)).isoformat(), "daily_review_limit": 10})
status, queue = call("GET", "/reviews/due")
mine = [card for card in queue if card["mistake_id"] in {b, c, d}]
order = [card["error_type"] for card in mine]
check("剩余 5 天进入考前模式，概念题排第一", order[:1] == ["concept"], str(order))
call("PUT", "/settings", {"daily_review_limit": 2})
status, queue = call("GET", "/reviews/due")
check("每日上限 2 生效", len(queue) == 2, f"len={len(queue)}")

print("\n=== 8. 字段校验 ===")
status, _ = call("PUT", f"/mistakes/{a}", {"question_text": None})
check("把必填字段改成 null -> 422", status == 422, f"status={status}")
status, _ = call("POST", "/mistakes", {"subject": "英语", "question_text": "x"})
check("非法科目 -> 422", status == 422, f"status={status}")

print("\n=== 9. 级联删除 ===")
status, body = call("DELETE", f"/mistakes/{a}")
check("DELETE 成功（修复前会抛 IntegrityError）", status == 200, str(body))
status, _ = call("GET", f"/mistakes/{a}")
check("删除后 404", status == 404, f"status={status}")

print("\n=== 10. 清理 ===")
for mid in (b, c, d):
    call("DELETE", f"/mistakes/{mid}")
call("PUT", "/settings", {"exam_date": None, "daily_review_limit": 20})
status, body = call("GET", "/mistakes")
leftover = set(created) & {item["id"] for item in body}
check("本次创建的数据已全部清理", status == 200 and leftover == set(), f"leftover={leftover}")

print()
if failures:
    print(f"❌ {len(failures)} 项失败: {failures}")
    raise SystemExit(1)
print("✅ 全部通过")
