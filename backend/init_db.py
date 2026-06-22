# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from database import SessionLocal, engine, Base
from models import User, Course, Teacher, Student, Room, Class, Settings, RegistrationToken
from passlib.context import CryptContext
from sqlalchemy import inspect, text

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run_migrations():
    insp = inspect(engine)
    if 'users' in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns('users')]
        if 'must_change_password' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE'))
                conn.commit()
            print("✓ 数据库迁移: 添加 must_change_password 字段")
    if 'settings' in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns('settings')]
        if 'open_registration_enabled' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN open_registration_enabled BOOLEAN DEFAULT FALSE'))
                conn.execute(text('ALTER TABLE settings ADD COLUMN open_registration_expiry TIMESTAMP NULL'))
                conn.commit()
            print("✓ 数据库迁移: 添加 open_registration_enabled/open_registration_expiry 字段")
        if 'session_timeout_minutes' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN session_timeout_minutes INTEGER DEFAULT 1440'))
                conn.commit()
            print("✓ 数据库迁移: 添加 session_timeout_minutes 字段")

def init_db():
    Base.metadata.create_all(bind=engine)
    run_migrations()
    
    db = SessionLocal()
    
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin = User(
                username="admin",
                password_hash=pwd_context.hash("Admin.123"),
                is_admin=True,
                role='super_admin',
                must_change_password=True
            )
            db.add(admin)
            db.commit()
            print("✓ 默认管理员账户创建成功")
            print("  用户名: admin")
            print("  密码: Admin.123（首次登录后必须修改）")
        else:
            print("✓ 管理员账户已存在")
        
        existing_settings = db.query(Settings).first()
        if not existing_settings:
            settings = Settings(
                site_name="课程管理系统",
                teacher_visibility_restricted=True,
                schedule_edit_restricted=True,
                schedule_delete_restricted=True,
                log_enabled=True,
                log_level="INFO",
                hours_per_lesson=2.0
            )
            db.add(settings)
            db.commit()
            print("✓ 默认站点参数创建成功")
        else:
            print("✓ 站点参数已存在")
        
        sample_course = db.query(Course).filter(Course.code == "MATH001").first()
        if not sample_course:
            math_course = Course(
                code="MATH001",
                name="数学",
                priority=10
            )
            db.add(math_course)
            db.commit()
            print("✓ 示例科目创建成功")
        
        sample_teacher = db.query(Teacher).filter(Teacher.code == "T001").first()
        if not sample_teacher:
            teacher = Teacher(
                code="T001",
                name="张老师",
                title="高级导师",
                department="数学部",
                max_weekly_hours=40,
                is_active=True
            )
            db.add(teacher)
            db.commit()
            print("✓ 示例导师创建成功")
        
        sample_class = db.query(Class).filter(Class.code == "C001").first()
        if not sample_class:
            default_class = Class(
                code="C001",
                name="数学基础班",
                is_active=True
            )
            db.add(default_class)
            db.commit()
            print("✓ 示例班级创建成功")
        
        sample_student = db.query(Student).filter(Student.code == "S001").first()
        if not sample_student:
            student = Student(
                code="S001",
                name="小明",
                school="第一中学",
                grade="高一",
                available_days="1,2,3,4,5,6,7",
                available_time_slots="",
                is_active=True
            )
            db.add(student)
            db.commit()
            print("✓ 示例学员创建成功")
        
        sample_room = db.query(Room).filter(Room.code == "R001").first()
        if not sample_room:
            room = Room(
                code="R001",
                name="101教室",
                location="一楼东侧",
                capacity=30,
                facilities="多媒体"
            )
            db.add(room)
            db.commit()
            print("✓ 示例教室创建成功")
        
        print("\n数据库初始化完成！")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()