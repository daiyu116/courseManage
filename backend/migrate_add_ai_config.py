# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
迁移脚本：为settings表添加ai_config字段
"""
from sqlalchemy import text
from database import engine, SessionLocal

def migrate():
    """执行迁移"""
    print("开始迁移：为settings表添加ai_config字段...")
    
    db = SessionLocal()
    try:
        # 检查字段是否已存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('settings')]
        
        if 'ai_config' in columns:
            print("✓ ai_config字段已存在，跳过迁移")
            return
        
        # 添加字段
        db.execute(text("ALTER TABLE settings ADD COLUMN ai_config TEXT DEFAULT '{}'"))
        db.commit()
        
        print("✓ 成功添加ai_config字段")
        
    except Exception as e:
        db.rollback()
        print(f"✗ 迁移失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()