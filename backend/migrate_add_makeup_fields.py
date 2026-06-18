# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from sqlalchemy import text
from database import engine, SessionLocal

def migrate_add_makeup_fields():
    """为schedule_student表添加补课相关字段"""
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            print("开始迁移：为schedule_student表添加补课相关字段...")
            
            # 检查并添加 makeup_status 字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'schedule_student' 
                AND column_name = 'makeup_status'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE schedule_student 
                    ADD COLUMN makeup_status VARCHAR(20) DEFAULT NULL
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN schedule_student.makeup_status IS '补课状态：pending-待补课, completed-已补课, declined-不补课'
                """))
                conn.commit()
                print("✓ 添加 schedule_student.makeup_status 字段")
            else:
                print("✓ schedule_student.makeup_status 字段已存在")
            
            # 检查并添加 makeup_schedule_id 字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'schedule_student' 
                AND column_name = 'makeup_schedule_id'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE schedule_student 
                    ADD COLUMN makeup_schedule_id INTEGER DEFAULT NULL
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN schedule_student.makeup_schedule_id IS '补课课程ID（关联到schedules表的id）'
                """))
                conn.commit()
                print("✓ 添加 schedule_student.makeup_schedule_id 字段")
            else:
                print("✓ schedule_student.makeup_schedule_id 字段已存在")
            
            # 检查并添加 declined_reason 字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'schedule_student' 
                AND column_name = 'declined_reason'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE schedule_student 
                    ADD COLUMN declined_reason TEXT DEFAULT NULL
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN schedule_student.declined_reason IS '不补课原因'
                """))
                conn.commit()
                print("✓ 添加 schedule_student.declined_reason 字段")
            else:
                print("✓ schedule_student.declined_reason 字段已存在")
            
            print("\n✓ 补课字段迁移完成！")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_makeup_fields()