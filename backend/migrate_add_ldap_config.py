# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
迁移脚本：为settings表添加LDAP配置字段
"""
from database import engine, SessionLocal
from sqlalchemy import text

def migrate_add_ldap_config():
    """添加LDAP配置字段"""
    db = SessionLocal()
    
    try:
        with engine.connect() as conn:
            print("开始迁移：为settings表添加LDAP配置字段...")
            
            # 添加 ldap_enabled 字段到 settings 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' 
                AND column_name = 'ldap_enabled'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN ldap_enabled BOOLEAN DEFAULT FALSE
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN settings.ldap_enabled IS '是否启用LDAP认证'
                """))
                conn.commit()
                print("✓ 添加 settings.ldap_enabled 字段")
            else:
                print("✓ settings.ldap_enabled 字段已存在")
            
            # 添加 ldap_config 字段到 settings 表
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settings' 
                AND column_name = 'ldap_config'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE settings 
                    ADD COLUMN ldap_config TEXT DEFAULT '{}'
                """))
                conn.execute(text("""
                    COMMENT ON COLUMN settings.ldap_config IS 'LDAP配置(JSON格式)：服务器地址、端口、DN、密码等'
                """))
                conn.commit()
                print("✓ 添加 settings.ldap_config 字段")
            else:
                print("✓ settings.ldap_config 字段已存在")
            
            print("\n✓ LDAP配置字段迁移完成！")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_ldap_config()