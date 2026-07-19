# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
数据库迁移脚本：为schedule_student表添加is_extra列，支持临时增员功能
"""
from sqlalchemy import create_engine, text
from database import engine

def migrate():
    """执行迁移"""
    print("开始迁移：为schedule_student表添加is_extra列...")
    
    with engine.connect() as conn:
        try:
            # 检查列是否已存在
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='schedule_student' AND column_name='is_extra'
            """))
            if result.fetchone():
                print("✓ is_extra列已存在，跳过迁移")
                return
            
            # 添加is_extra列
            conn.execute(text("""
                ALTER TABLE schedule_student 
                ADD COLUMN is_extra BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✓ is_extra列添加成功")
            print("✓ 迁移完成！")
            
        except Exception as e:
            print(f"✗ 迁移失败: {str(e)}")
            raise

if __name__ == "__main__":
    migrate()