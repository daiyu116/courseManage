# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
"""
迁移脚本：为settings表添加课程配置字段
"""
from database import engine, SessionLocal
from sqlalchemy import text

def migrate_add_course_config():
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            print("开始迁移：为settings表添加课程配置字段...")
            
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' 
                AND column_name = 'hours_per_lesson'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN hours_per_lesson FLOAT DEFAULT 2.0
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN settings.hours_per_lesson IS '每节课课时数（小时），默认2.0'
                """))
                conn.commit()
                print("✓ 添加 settings.hours_per_lesson 字段")
            else:
                print("✓ settings.hours_per_lesson 字段已存在")
            
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' 
                AND column_name = 'course_config'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN course_config TEXT DEFAULT '{}'
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN settings.course_config IS '课程配置(JSON格式)：考试阶段、年级选项等'
                """))
                conn.commit()
                print("✓ 添加 settings.course_config 字段")
            else:
                print("✓ settings.course_config 字段已存在")
            
            print("\n✓ 课程配置字段迁移完成！")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_course_config()