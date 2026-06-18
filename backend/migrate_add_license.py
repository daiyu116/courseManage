# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
"""
数据库迁移：为 Settings 表增加 License 相关字段
"""
from sqlalchemy import text, inspect
from database import engine, SessionLocal


def migrate_add_license_fields():
    """添加 license_key 和 premium_features 字段"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("settings")]

        changes_made = False

        if "license_key" not in columns:
            db.execute(text("ALTER TABLE settings ADD COLUMN license_key TEXT"))
            db.commit()
            print("  + 已添加 license_key 字段")
            changes_made = True
        else:
            print("  - license_key 字段已存在")

        if "premium_features" not in columns:
            db.execute(text(
                "ALTER TABLE settings ADD COLUMN premium_features TEXT DEFAULT '{}'"
            ))
            db.commit()
            print("  + 已添加 premium_features 字段")
            changes_made = True
        else:
            print("  - premium_features 字段已存在")

        if not changes_made:
            print("  = License 字段均存在，无需变更")

    except Exception as e:
        print(f"  ! 迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("执行 License 字段迁移...")
    migrate_add_license_fields()
    print("迁移完成")