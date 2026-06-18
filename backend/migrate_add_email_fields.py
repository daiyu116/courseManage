# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from database import engine, SessionLocal
from sqlalchemy import text

def migrate_add_email_fields():
    """添加电子邮箱字段"""
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            print("开始迁移...")
            
            # 添加 email 字段到 teachers 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'teachers' 
                AND column_name = 'email'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE teachers 
                    ADD COLUMN email VARCHAR(100)
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN teachers.email IS '电子邮箱'
                """))
                conn.commit()
                print("✓ 添加 teachers.email 字段")
            else:
                print("✓ teachers.email 字段已存在")
            
            # 添加 email 字段到 students 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'students' 
                AND column_name = 'email'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE students 
                    ADD COLUMN email VARCHAR(100)
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN students.email IS '电子邮箱'
                """))
                conn.commit()
                print("✓ 添加 students.email 字段")
            else:
                print("✓ students.email 字段已存在")
            
            # 添加 email_config 字段到 settings 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' 
                AND column_name = 'email_config'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN email_config TEXT DEFAULT '{}'
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN settings.email_config IS '邮件配置(JSON格式)'
                """))
                conn.commit()
                print("✓ 添加 settings.email_config 字段")
            else:
                print("✓ settings.email_config 字段已存在")
            
            # 添加 email_notification_settings 字段到 settings 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' 
                AND column_name = 'email_notification_settings'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN email_notification_settings TEXT DEFAULT '{}'
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN settings.email_notification_settings IS '邮件通知设置(JSON格式)'
                """))
                conn.commit()
                print("✓ 添加 settings.email_notification_settings 字段")
            else:
                print("✓ settings.email_notification_settings 字段已存在")
            
            print("\n✓ 迁移完成！")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_email_fields()