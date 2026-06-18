# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
# migrate_database.py
from sqlalchemy import text
from database import engine

def migrate_database():
    """执行数据库迁移，添加缺失的字段"""
    with engine.connect() as conn:
        try:
            # 检查并添加 notification_settings 字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' AND column_name = 'notification_settings'
            """))
            
            if not result.fetchone():
                print("添加 notification_settings 字段...")
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN notification_settings TEXT DEFAULT '{}'
                """))
                conn.commit()
                print("✓ notification_settings 字段已添加")
            else:
                print("✓ notification_settings 字段已存在")

            # 检查并添加 site_url 字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' AND column_name = 'site_url'
            """))
            
            if not result.fetchone():
                print("添加 site_url 字段...")
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN site_url VARCHAR(500)
                """))
                conn.commit()
                print("✓ site_url 字段已添加")
            else:
                print("✓ site_url 字段已存在")

            # 检查并添加 wechat_webhook 字段到 classes 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'classes' AND column_name = 'wechat_webhook'
            """))
            
            if not result.fetchone():
                print("添加 wechat_webhook 字段...")
                conn.execute(text("""
                    ALTER TABLE classes 
                    ADD COLUMN wechat_webhook TEXT DEFAULT NULL
                """))
                conn.commit()
                print("✓ wechat_webhook 字段已添加")
            else:
                print("✓ wechat_webhook 字段已存在")

            # 检查并添加 homework_regular 字段到 schedules 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'schedules' AND column_name = 'homework_regular'
            """))
            
            if not result.fetchone():
                print("添加 homework_regular 字段...")
                conn.execute(text("""
                    ALTER TABLE schedules 
                    ADD COLUMN homework_regular TEXT DEFAULT ''
                """))
                conn.commit()
                print("✓ homework_regular 字段已添加")
            else:
                print("✓ homework_regular 字段已存在")
            
            # 检查并添加 homework_images 字段到 schedules 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'schedules' AND column_name = 'homework_images'
            """))
            
            if not result.fetchone():
                print("添加 homework_images 字段...")
                conn.execute(text("""
                    ALTER TABLE schedules 
                    ADD COLUMN homework_images TEXT DEFAULT ''
                """))
                conn.commit()
                print("✓ homework_images 字段已添加")
            else:
                print("✓ homework_images 字段已存在")

            print("\n数据库迁移完成！")
            
        except Exception as e:
            print(f"数据库迁移失败: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate_database()