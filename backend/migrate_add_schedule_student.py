# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
"""
数据库迁移脚本：添加schedule_student表并为现有课程安排创建学员关联记录
"""
from sqlalchemy import create_engine, text
from database import SessionLocal, engine
from models import Schedule, Class, Student, schedule_student
from datetime import datetime

def migrate():
    """执行迁移"""
    print("开始迁移：添加schedule_student表...")
    
    # 创建表
    from database import Base
    Base.metadata.create_all(bind=engine)
    print("✓ schedule_student表创建成功")
    
    # 为现有课程安排创建学员关联记录
    db = SessionLocal()
    try:
        schedules = db.query(Schedule).all()
        total = len(schedules)
        print(f"找到 {total} 个课程安排，开始创建学员关联记录...")
        
        for i, schedule in enumerate(schedules, 1):
            # 获取班级的所有活跃学员
            class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
            if not class_:
                print(f"警告：课程安排ID {schedule.id} 的班级不存在，跳过")
                continue
            
            students = [s for s in class_.students if s.is_active]
            
            if not students:
                print(f"警告：课程安排ID {schedule.id} 的班级没有活跃学员，跳过")
                continue
            
            # 检查是否已有记录
            from sqlalchemy import select
            query = select(schedule_student.c.id).where(
                schedule_student.c.schedule_id == schedule.id
            )
            result = db.execute(query).fetchone()
            
            if result:
                print(f"课程安排ID {schedule.id} 已有学员记录，跳过 ({i}/{total})")
                continue
            
            # 创建学员关联记录
            for student in students:
                # 如果是已完训的课程，默认为出席；否则为pending
                attendance_status = 'present' if schedule.execution_status == 'completed' else 'pending'
                
                association = schedule_student.insert().values(
                    schedule_id=schedule.id,
                    student_id=student.id,
                    attendance_status=attendance_status,
                    created_at=datetime.now()
                )
                db.execute(association)
            
            if i % 10 == 0 or i == total:
                db.commit()
                print(f"进度: {i}/{total}")
        
        db.commit()
        print("✓ 迁移完成！所有课程安排已关联学员记录")
        
    except Exception as e:
        db.rollback()
        print(f"✗ 迁移失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()