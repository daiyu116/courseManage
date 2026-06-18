# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
# backend/migrate_add_operation_managers.py
"""
添加运营管理导师配置字段 (适配 PostgreSQL)
"""
from database import SessionLocal
from models import Settings
from sqlalchemy import text

def add_operation_managers():
    db = SessionLocal()
    try:
        # 1. 检查表是否存在该列
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'settings' AND column_name = 'operation_managers'
        """))
        
        if result.fetchone():
            print("✅ operation_managers 字段已存在，跳过迁移")
            return True
        
        # 2. 添加新列
        db.execute(text("ALTER TABLE settings ADD COLUMN operation_managers TEXT DEFAULT '[]'"))
        
        # 3. 添加列注释 (PostgreSQL 需要单独执行)
        db.execute(text("COMMENT ON COLUMN settings.operation_managers IS '运营管理导师ID列表(JSON格式)'"))
        
        db.commit()
        
        print("✅ 成功添加 operation_managers 字段到 settings 表")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ 迁移失败: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    add_operation_managers()