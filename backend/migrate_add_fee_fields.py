# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from database import engine, SessionLocal
from sqlalchemy import text

def migrate_add_fee_fields():
    """添加课时费表的新字段"""
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'student_fees' 
                AND column_name = 'total_receivable_amount'
            """))
            
            if result.fetchone():
                print("字段已存在，无需迁移")
                return
            
            print("开始迁移...")
            
            # 添加新字段
            conn.execute(text("""
                ALTER TABLE student_fees 
                ADD COLUMN total_receivable_amount FLOAT DEFAULT 0.0
            """))
            print("✓ 添加 total_receivable_amount 字段")
            
            conn.execute(text("""
                ALTER TABLE student_fees 
                ADD COLUMN total_actual_amount FLOAT DEFAULT 0.0
            """))
            print("✓ 添加 total_actual_amount 字段")
            
            conn.execute(text("""
                ALTER TABLE student_fees 
                ADD COLUMN total_refund_amount FLOAT DEFAULT 0.0
            """))
            print("✓ 添加 total_refund_amount 字段")
            
            conn.execute(text("""
                ALTER TABLE student_fees 
                ADD COLUMN total_lesson_count FLOAT DEFAULT 0.0
            """))
            print("✓ 添加 total_lesson_count 字段")
            
            conn.execute(text("""
                ALTER TABLE student_fees 
                ADD COLUMN consumed_hours FLOAT DEFAULT 0.0
            """))
            print("✓ 添加 consumed_hours 字段")
            
            # 迁移现有数据
            conn.execute(text("""
                UPDATE student_fees 
                SET total_actual_amount = total_amount
            """))
            print("✓ 迁移现有数据：total_amount -> total_actual_amount")
            
            conn.execute(text("""
                UPDATE student_fees 
                SET total_receivable_amount = total_amount
            """))
            print("✓ 迁移现有数据：total_amount -> total_receivable_amount")
            
            conn.execute(text("""
                UPDATE student_fees 
                SET total_lesson_count = remaining_hours / 2
            """))
            print("✓ 迁移现有数据：计算 total_lesson_count")
            
            conn.commit()
            print("\n✓ 迁移完成！")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_fee_fields()