# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
数据库迁移脚本：为daily_words表添加phrases列
"""
from sqlalchemy import create_engine, text
from database import SessionLocal, engine

def migrate_add_daily_words_phrases():
    print("开始迁移：为daily_words表添加phrases列...")

    db = SessionLocal()
    try:
        result = db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='daily_words' AND column_name='phrases'"
        ))
        if result.fetchone():
            print("✓ phrases列已存在，跳过")
        else:
            db.execute(text("ALTER TABLE daily_words ADD COLUMN phrases JSONB DEFAULT '[]'"))
            db.commit()
            print("✓ phrases列添加成功")
    except Exception as e:
        db.rollback()
        print(f"✗ 迁移失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_daily_words_phrases()