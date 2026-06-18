# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
为运营大屏统计查询添加性能优化索引
"""
from sqlalchemy import text
from database import engine

def add_performance_indexes():
    """添加统计查询所需的索引"""
    
    indexes = [
        # Schedule表索引优化
        "CREATE INDEX IF NOT EXISTS idx_schedules_execution_status ON schedules(execution_status)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_start_date ON schedules(start_date)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_end_date ON schedules(end_date)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_schedule_type ON schedules(schedule_type)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_teacher_id ON schedules(teacher_id)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_room_id ON schedules(room_id)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_class_id ON schedules(class_id)",
        
        # schedule_student关联表索引
        "CREATE INDEX IF NOT EXISTS idx_schedule_student_schedule_id ON schedule_student(schedule_id)",
        "CREATE INDEX IF NOT EXISTS idx_schedule_student_student_id ON schedule_student(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_schedule_student_attendance_status ON schedule_student(attendance_status)",
        
        # StudentFee表索引
        "CREATE INDEX IF NOT EXISTS idx_student_fees_is_active ON student_fees(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_student_fees_student_id ON student_fees(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_student_fees_course_id ON student_fees(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_student_fees_remaining_hours ON student_fees(remaining_hours)",
        
        # FeeLog表索引
        "CREATE INDEX IF NOT EXISTS idx_fee_logs_log_type ON fee_logs(log_type)",
        "CREATE INDEX IF NOT EXISTS idx_fee_logs_created_at ON fee_logs(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_fee_logs_student_id ON fee_logs(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_fee_logs_course_id ON fee_logs(course_id)",
        
        # StudentGrade表索引
        "CREATE INDEX IF NOT EXISTS idx_student_grades_student_id ON student_grades(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_student_grades_course_id ON student_grades(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_student_grades_total_score ON student_grades(total_score)",
        "CREATE INDEX IF NOT EXISTS idx_student_grades_score_change ON student_grades(score_change)",
        
        # Student表索引
        "CREATE INDEX IF NOT EXISTS idx_students_is_active ON students(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_students_created_at ON students(created_at)",
        
        # Room表索引
        "CREATE INDEX IF NOT EXISTS idx_rooms_is_active ON rooms(is_active)",
        
        # Teacher表索引
        "CREATE INDEX IF NOT EXISTS idx_teachers_is_active ON teachers(is_active)",
    ]
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
                print(f"✅ 索引创建成功: {index_sql[:60]}...")
            except Exception as e:
                print(f"❌ 索引创建失败: {index_sql[:60]}... 错误: {e}")
    
    print("\n🎉 所有索引创建完成！")

if __name__ == "__main__":
    add_performance_indexes()