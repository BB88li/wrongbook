"""备份 SQLite 数据库，保留最近 14 份。

用法（在 backend 目录下）：
    python scripts/backup_db.py

建议每天跑一次（Windows 任务计划 / 手动）。切到 MySQL 后此脚本会自动跳过，
届时请用 mysqldump。
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 允许直接以脚本方式运行：python scripts/backup_db.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import DATA_DIR, settings  # noqa: E402

KEEP = 14


def main() -> int:
    if not settings.database_url.startswith("sqlite"):
        print("当前数据库不是 SQLite，请改用 mysqldump 备份。")
        return 1

    db_path = Path(settings.database_url.replace("sqlite:///", "").replace("sqlite://", ""))
    if not db_path.exists():
        print(f"数据库文件不存在：{db_path}")
        return 1

    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"wrongbook_{datetime.now():%Y%m%d_%H%M%S}.db"

    # 用 sqlite3 的在线备份 API，避免直接复制正在写入的文件
    with sqlite3.connect(db_path) as src, sqlite3.connect(target) as dst:
        src.backup(dst)

    backups = sorted(backup_dir.glob("wrongbook_*.db"))
    for old in backups[:-KEEP]:
        old.unlink()

    print(f"已备份到 {target}（共保留 {min(len(backups), KEEP)} 份）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
