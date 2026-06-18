# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
# migrate_add_payment_method.py
from database import engine, SessionLocal
from sqlalchemy import text

def migrate_add_payment_method():
    """添加收费途径字段"""
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在（PostgreSQL 兼容）
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'student_fees' 
                AND column_name = 'payment_method'
            """))
            
            if result.fetchone():
                print("字段已存在，无需迁移")
                return
            
            print("开始迁移...")
            
            # 添加 payment_method 字段（PostgreSQL 语法）
            conn.execute(text("""
                ALTER TABLE student_fees 
                ADD COLUMN payment_method VARCHAR(50) DEFAULT ''
            """))
            print("✓ 添加 payment_method 字段")
            
            conn.commit()
            print("\n✓ 迁移完成！")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_payment_method()