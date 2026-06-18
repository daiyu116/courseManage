# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
添加课程安排编辑和删除限制的迁移脚本
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    _db_user = os.getenv("POSTGRES_USER", "cadbuser")
    _db_pass = os.getenv("POSTGRES_PASSWORD", "")
    _db_host = os.getenv("DB_HOST", "localhost")
    _db_port = os.getenv("DB_PORT", "5432")
    _db_name = os.getenv("POSTGRES_DB", "cadb")
    DATABASE_URL = f"postgresql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}"

def run_migration():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 检查并添加 schedule_edit_restricted 字段
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'settings' 
            AND column_name = 'schedule_edit_restricted'
        """))
        
        if not result.fetchone():
            conn.execute(text("""
                ALTER TABLE settings 
                ADD COLUMN schedule_edit_restricted BOOLEAN DEFAULT TRUE
            """))
            conn.execute(text("""
                COMMENT ON COLUMN settings.schedule_edit_restricted IS '课程安排编辑限制：True-仅超级管理员可编辑已完训/延期/取消的课程，False-课程管理导师也可编辑'
            """))
            print("✓ 添加 settings.schedule_edit_restricted 字段")
        else:
            print("✓ settings.schedule_edit_restricted 字段已存在")
        
        # 检查并添加 schedule_delete_restricted 字段
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'settings' 
            AND column_name = 'schedule_delete_restricted'
        """))
        
        if not result.fetchone():
            conn.execute(text("""
                ALTER TABLE settings 
                ADD COLUMN schedule_delete_restricted BOOLEAN DEFAULT TRUE
            """))
            conn.execute(text("""
                COMMENT ON COLUMN settings.schedule_delete_restricted IS '课程安排删除限制：True-仅超级管理员可删除已完训/延期/取消的课程，False-课程管理导师也可删除'
            """))
            print("✓ 添加 settings.schedule_delete_restricted 字段")
        else:
            print("✓ settings.schedule_delete_restricted 字段已存在")
        
        conn.commit()
        print("✅ 迁移完成！")

if __name__ == "__main__":
    run_migration()