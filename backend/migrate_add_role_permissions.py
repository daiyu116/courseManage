# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from database import engine, SessionLocal
from sqlalchemy import text

def migrate_add_role_permissions():
    """添加三权分立角色权限字段"""
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            print("开始迁移...")
            
            # 添加 teacher_visibility_restricted 字段到 settings 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' 
                AND column_name = 'teacher_visibility_restricted'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN teacher_visibility_restricted BOOLEAN DEFAULT TRUE
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN settings.teacher_visibility_restricted IS '课程管理员可见性限制开关：True-课程管理员只能看到自己相关的内容，False-课程管理员可以看到所有内容'
                """))
                conn.commit()
                print("✓ 添加 settings.teacher_visibility_restricted 字段")
            else:
                print("✓ settings.teacher_visibility_restricted 字段已存在")
            
            # 更新现有admin用户的角色为super_admin
            conn.execute(text("""
                UPDATE users 
                SET role = 'super_admin' 
                WHERE role = 'admin'
            """))
            conn.commit()
            print("✓ 更新现有admin用户角色为super_admin")
            
            # 更新现有teacher用户的角色为course_admin
            conn.execute(text("""
                UPDATE users 
                SET role = 'course_admin' 
                WHERE role = 'teacher'
            """))
            conn.commit()
            print("✓ 更新现有teacher用户角色为course_admin")
            
            print("\n✓ 迁移完成！")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_role_permissions()