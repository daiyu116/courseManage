# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
迁移脚本：为schedules表添加schedule_type字段
- 新增schedule_type字段，类型为VARCHAR(20)，默认值为'formal'（正式课）
- 可选值：'formal'（正式课）、'trial'（试听课）
- 将现有所有记录设置为'formal'
"""
from sqlalchemy import create_engine, text
import os

def add_schedule_type():
    # 从环境变量获取数据库URL，或使用默认值
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        db_user = os.getenv("POSTGRES_USER", "cadbuser")
        db_pass = os.getenv("POSTGRES_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "cadb")
        database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'schedules' 
            AND column_name = 'schedule_type'
        """))
        
        if result.fetchone():
            print("schedule_type字段已存在，跳过迁移")
            return
        
        # 添加新字段
        conn.execute(text("""
            ALTER TABLE schedules 
            ADD COLUMN schedule_type VARCHAR(20) NOT NULL DEFAULT 'formal'
        """))
        
        # 添加注释
        conn.execute(text("""
            COMMENT ON COLUMN schedules.schedule_type IS '课程类型：formal-正式课, trial-试听课'
        """))
        
        # 确保现有记录都设置为formal
        #conn.execute(text("""
        #    UPDATE schedules SET schedule_type = 'formal' WHERE schedule_type IS NULL
        #"""))
        
        conn.commit()
        print("迁移完成：已添加schedule_type字段，默认值为'formal'")

if __name__ == "__main__":
    add_schedule_type()