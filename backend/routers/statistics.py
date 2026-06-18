# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
"""
统计模块
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc, and_, or_, case
from typing import Optional
from datetime import datetime, date, timedelta
from database import get_db, get_pool_status
from models import (
    Course, Teacher, Student, Class, Schedule, 
    StudentFee, FeeLog, StudentGrade, Settings, schedule_student, Room
)
from routers.auth import get_current_user, User
import json
from utils.logger import log_operation

router = APIRouter()

def get_hours_per_lesson(db: Session) -> float:
    settings = db.query(Settings).first()
    if settings and settings.hours_per_lesson is not None:
        return settings.hours_per_lesson
    return 2.0
 
def get_exam_stage_order(db: Session) -> dict:
    settings = db.query(Settings).first()
    default_stages = [
        '秋季月考A', '秋季月考B', '秋季期中', '秋季月考C', '秋季月考D', '秋季期末',
        '春季月考A', '春季月考B', '春季期中', '春季月考C', '春季月考D', '春季期末',
        '中考一模', '中考二模', '中考三模', '中考', '会考',
        '高考特训A', '高考特训B', '高考特训C', '春季高考',
        '高考一模', '高考二模', '高考三模', '夏季高考'
    ]
    stages = default_stages
    if settings and settings.course_config:
        try:
            config = json.loads(settings.course_config)
            if 'exam_stages' in config and config['exam_stages']:
                stages = config['exam_stages']
        except (json.JSONDecodeError, TypeError):
            pass
    return {stage: idx + 1 for idx, stage in enumerate(stages)}

def check_dashboard_permission(db: Session, current_user: User):
    """检查用户是否有运营大屏访问权限"""
    # 超级管理员和系统管理员可以直接访问
    if current_user.role in ['super_admin', 'system_admin']:
        return True
    
    # 课程管理员需要是运营管理导师
    if current_user.role == 'course_admin' and current_user.teacher_id:
        settings = db.query(Settings).first()
        if settings and settings.operation_managers:
            try:
                operation_managers = json.loads(settings.operation_managers)
                if current_user.teacher_id in operation_managers:
                    return True
            except:
                pass
    return False

@router.get("/kpi")
def get_kpi_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取关键指标数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员或运营管理导师权限")
    
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 总科目数
    total_courses = db.query(Course).count()
    
    # 在职导师数
    active_teachers = db.query(Teacher).filter(Teacher.is_active == True).count()
    
    # 在读学员数
    active_students = db.query(Student).filter(Student.is_active == True).count()
    
    # 活跃班级数
    active_classes = db.query(Class).filter(Class.is_active == True).count()
    
    # 总教室数
    total_rooms = db.query(Room).filter(Room.is_active == True).count()
    
    # 总排课数
    total_schedules = db.query(Schedule).count()
    
    # 本月总收入（实收）
    monthly_revenue = db.query(func.sum(FeeLog.amount)).filter(
        FeeLog.log_type == 'payment',
        FeeLog.payment_date >= month_start.date(),
        FeeLog.payment_date <= now.date()
    ).scalar() or 0.0
    
    # 本月退费
    monthly_refund = db.query(func.sum(FeeLog.amount)).filter(
        FeeLog.log_type == 'refund',
        FeeLog.refund_date >= month_start.date(),
        FeeLog.refund_date <= now.date()
    ).scalar() or 0.0
    
    # 净收入
    net_income = monthly_revenue - abs(monthly_refund)
    
    # 待收费预警数（剩余课时低于阈值的学生费用记录）
    payment_alerts = db.query(StudentFee).filter(
        StudentFee.is_active == True,
        StudentFee.remaining_hours <= StudentFee.alert_threshold,
        StudentFee.remaining_hours > 0
    ).count()
    
    # 平均成绩比例
    grades_with_total = db.query(StudentGrade).filter(
        StudentGrade.total_score > 0
    ).all()
    
    avg_grade_ratio = 0.0
    if grades_with_total:
        total_ratio = sum((g.score / g.total_score * 100) for g in grades_with_total)
        avg_grade_ratio = round(total_ratio / len(grades_with_total), 2)
    
    # 今日课程数
    today = date.today()
    today_schedules = db.query(Schedule).filter(
        Schedule.start_date == today,
        Schedule.execution_status == 'pending'
    ).count()

    # 今日试听课数
    today_trial_schedules = db.query(Schedule).filter(
        Schedule.start_date == today,
        Schedule.schedule_type == 'trial',
        Schedule.execution_status == 'pending'
    ).count()

    # 已完训课程数（截止当前日期的所有已完训课程数量）
    completed_schedules = db.query(Schedule).filter(
        Schedule.end_date <= today,
        Schedule.execution_status == 'completed'
    ).count()
    
    # 未完训课程安排数量（截止当前日期的所有未完训、延期、取消的课程数量）
    incomplete_schedules = db.query(Schedule).filter(
        Schedule.end_date <= today,
        Schedule.execution_status.in_(['pending', 'postponed', 'cancelled'])
    ).count()

    # 本周完训率
    week_start = today - timedelta(days=today.weekday())
    week_schedules = db.query(Schedule).filter(
        Schedule.start_date >= week_start,
        Schedule.start_date <= today
    ).all()
    
    completed_count = sum(1 for s in week_schedules if s.execution_status == 'completed')
    completion_rate = round((completed_count / len(week_schedules) * 100), 2) if week_schedules else 0.0
    
    # 本周试听转正数（简单逻辑：试听课后产生了费用记录或关联了正式课，此处暂以试听课完训数代替基础数据）
    week_trial_completed = sum(1 for s in week_schedules if s.execution_status == 'completed' and s.schedule_type == 'trial')

    # ========== 新增KPI指标 ==========
    
    # 1. 待补课学员数：在完训课程中有请假状态的学员数量
    pending_makeup_students = db.query(func.count(func.distinct(schedule_student.c.student_id))).join(
        Schedule, schedule_student.c.schedule_id == Schedule.id
    ).filter(
        Schedule.execution_status == 'completed',
        schedule_student.c.attendance_status.in_(['absent', 'leave']),
        (schedule_student.c.makeup_status == None) | (schedule_student.c.makeup_status == 'pending')
    ).scalar() or 0

    # 2. 退费总额（历史累计）
    total_refund_amount = db.query(func.sum(FeeLog.amount)).filter(
        FeeLog.log_type == 'refund'
    ).scalar() or 0.0

    # 3. 欠费总额：所有学生费用的剩余应收金额总和
    total_owed_amount = db.query(func.sum(
        StudentFee.total_receivable_amount - StudentFee.total_actual_amount
    )).filter(
        StudentFee.is_active == True,
        StudentFee.total_receivable_amount > StudentFee.total_actual_amount
    ).scalar() or 0.0

    # 4. 本月转化率：本月试听转化人数 / 本月试听总人数
    # 先获取本月试听课涉及的学生ID
    month_trial_student_ids = db.query(schedule_student.c.student_id).join(
        Schedule, schedule_student.c.schedule_id == Schedule.id
    ).filter(
        Schedule.schedule_type == 'trial',
        Schedule.start_date >= month_start,
        Schedule.start_date <= now
    ).distinct().all()
    
    student_ids = [s[0] for s in month_trial_student_ids]
    month_trial_students = len(student_ids)
    
    if student_ids:
        month_converted_students = db.query(func.count(func.distinct(FeeLog.student_id))).filter(
            FeeLog.student_id.in_(student_ids),
            FeeLog.log_type == 'payment',
            FeeLog.payment_date >= month_start.date(),
            FeeLog.payment_date <= now.date()
        ).scalar() or 0
        conversion_rate = round((month_converted_students / month_trial_students * 100), 2)
    else:
        month_converted_students = 0
        conversion_rate = 0.0
        
    # 5. 学员续费率：本月有续费行为的学员数 / 本月有缴费行为的学员总数
    # 续费行为定义：
    # - 老学员（该科目有历史缴费记录）：本月有缴费（1次就算）
    # - 新学员（该科目无历史缴费记录）：本月有多次缴费（>= 2次）
    
    # 获取本月所有有缴费记录的学员（分母）
    # 获取本月所有有缴费记录的学员（分母）
    all_payment_students = db.query(func.distinct(FeeLog.student_id)).filter(
        FeeLog.log_type == 'payment',
        FeeLog.payment_date >= month_start.date(),
        FeeLog.payment_date <= now.date()
    ).all()
    # 提取学员ID列表
    all_payment_student_ids = [row[0] for row in all_payment_students]
    total_payment_students = len(all_payment_student_ids)
    
    # 统计本月有续费行为的学员（分子）
    renewed_student_ids = set()
    
    # 按科目统计每个学员本月的缴费情况
    student_course_payments = {}
    for payment_log in db.query(FeeLog).filter(
        FeeLog.log_type == 'payment',
        FeeLog.payment_date >= month_start.date(),
        FeeLog.payment_date <= now.date()
    ).all():
        key = (payment_log.student_id, payment_log.course_id)
        if key not in student_course_payments:
            student_course_payments[key] = 0
        student_course_payments[key] += 1
    
    # 判断每个学员在每个科目是否算续费
    for (student_id, course_id), payment_count in student_course_payments.items():
        # 检查该学员在该科目是否有历史缴费记录（本月之前）
        previous_fee = db.query(StudentFee).filter(
            StudentFee.student_id == student_id,
            StudentFee.course_id == course_id,
            StudentFee.start_date < month_start,
            StudentFee.is_active == True
        ).first()
        
        if previous_fee:
            # 老学员：本月有缴费就算续费（>= 1次）
            if payment_count >= 1:
                renewed_student_ids.add(student_id)
        else:
            # 新学员：本月多次缴费才算续费（>= 2次）
            if payment_count >= 2:
                renewed_student_ids.add(student_id)
    
    renewal_count = len(renewed_student_ids)
    renewal_rate = round((renewal_count / total_payment_students * 100), 2) if total_payment_students > 0 else 0.0
    return {
        "total_courses": total_courses,
        "active_teachers": active_teachers,
        "active_students": active_students,
        "active_classes": active_classes,
        "total_rooms": total_rooms,
        "total_schedules": total_schedules,
        "monthly_revenue": round(monthly_revenue, 2),
        "monthly_refund": round(abs(monthly_refund), 2),
        "net_income": round(net_income, 2),
        "payment_alerts_count": payment_alerts,
        "avg_grade_ratio": avg_grade_ratio,
        "today_schedules": today_schedules,
        "today_trial_schedules": today_trial_schedules,
        "completed_schedules": completed_schedules,
        "incomplete_schedules": incomplete_schedules,
        "weekly_completion_rate": completion_rate,
        "week_trial_completed": week_trial_completed,
        "pending_makeup_students": pending_makeup_students,
        "total_refund_amount": round(abs(total_refund_amount), 2),
        "total_owed_amount": round(total_owed_amount, 2),
        "conversion_rate": conversion_rate,
        "renewal_rate": renewal_rate
    }

@router.get("/courses/distribution")
def get_course_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取科目分布数据（按学员人数）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查询每个科目的学员数量（通过费用记录关联）
    course_student_count = db.query(
        Course.id,
        Course.name,
        func.count(func.distinct(StudentFee.student_id)).label('student_count')
    ).join(
        StudentFee, Course.id == StudentFee.course_id
    ).filter(
        StudentFee.is_active == True
    ).group_by(
        Course.id, Course.name
    ).all()
    
    result = [
        {
            "course_id": row[0],
            "course_name": row[1],
            "student_count": row[2]
        }
        for row in course_student_count if row[2] > 0
    ]
    
    # 按学员数降序排列
    result.sort(key=lambda x: x['student_count'], reverse=True)
    
    return result

@router.get("/teachers/workload")
def get_teacher_workload(
    # 默认统计30天，最小1天，最大1080天，根据前端传入数据进行计算
    days: int = Query(default=30, ge=1, le=1080, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导师工作量排行"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 查询每位导师的授课课时
    teacher_workload = db.query(
        Teacher.id,
        Teacher.name,
        func.count(Schedule.id).label('schedule_count')
    ).join(
        Schedule, Teacher.id == Schedule.teacher_id
    ).filter(
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date,
        Schedule.execution_status.in_(['pending', 'completed'])
    ).group_by(
        Teacher.id, Teacher.name
    ).order_by(
        func.count(Schedule.id).desc()
    ).limit(10).all()
    
    result = []
    for row in teacher_workload:
        teacher_id = row[0]
        teacher_name = row[1]
        schedule_count = row[2]
        
        # 单独查询该导师的课程安排，手动计算总时长和完训率
        schedules = db.query(Schedule).filter(
            Schedule.teacher_id == teacher_id,
            Schedule.start_date >= start_date,
            Schedule.start_date <= end_date,
            Schedule.execution_status.in_(['pending', 'completed'])
        ).all()
        
        total_minutes = 0
        completed_count = 0
        
        for schedule in schedules:
            try:
                # 解析时间字符串 "HH:MM"
                start_h, start_m = map(int, schedule.start_time.split(':'))
                end_h, end_m = map(int, schedule.end_time.split(':'))
                duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
                if duration > 0:
                    total_minutes += duration
                
                # 统计完训数量
                if schedule.execution_status == 'completed':
                    completed_count += 1
            except:
                pass
        
        total_hours = round(total_minutes / 60, 2)
        completion_rate = round((completed_count / schedule_count * 100) if schedule_count > 0 else 0, 2)
        
        result.append({
            "teacher_id": teacher_id,
            "teacher_name": teacher_name,
            "schedule_count": schedule_count,
            "total_hours": total_hours,
            "completion_rate": completion_rate
        })
    
    return result

@router.get("/schedules/trend")
def get_schedule_trend(
    # 默认统计30天，最小1天，最大1080天，根据前端传入数据进行计算
    days: int = Query(default=30, ge=1, le=1080, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取课程安排趋势（区分正式课与试听课）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 按日期和类型统计课程数量
    daily_counts = db.query(
        Schedule.start_date,
        Schedule.schedule_type,
        func.count(Schedule.id).label('count')
    ).filter(
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).group_by(
        Schedule.start_date, Schedule.schedule_type
    ).order_by(
        Schedule.start_date.asc()
    ).all()
    
    # 填充缺失日期
    result = []
    current_date = start_date
    count_map = {}
    for row in daily_counts:
        key = (row[0], row[1])
        count_map[key] = row[2]
    
    while current_date <= end_date:
        formal_count = count_map.get((current_date, 'formal'), 0)
        trial_count = count_map.get((current_date, 'trial'), 0)
        result.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "formal_count": formal_count,
            "trial_count": trial_count,
            "total_count": formal_count + trial_count
        })
        current_date += timedelta(days=1)
    
    return result

@router.get("/schedules/type-distribution")
def get_schedule_type_distribution(
    # 默认统计30天，最小1天，最大366天，根据前端传入数据进行计算
    days: int = Query(default=30, ge=1, le=366, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取正式课与试听课分布比例"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    counts = db.query(
        Schedule.schedule_type,
        func.count(Schedule.id).label('count')
    ).filter(
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).group_by(
        Schedule.schedule_type
    ).all()
    
    total = sum(row[1] for row in counts)
    result = {
        "formal": {"count": 0, "percentage": 0},
        "trial": {"count": 0, "percentage": 0}
    }
    
    for row in counts:
        if row[0] in result:
            result[row[0]]["count"] = row[1]
            result[row[0]]["percentage"] = round((row[1] / total * 100), 2) if total > 0 else 0
            
    return result

@router.get("/funnel/trial-conversion")
def get_trial_conversion_funnel(
    # 默认统计30天，最小1天，最大1080天，根据前端传入数据进行计算
    days: int = Query(default=30, ge=1, le=1080, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取试听转化漏斗数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 1. 试听课总数
    total_trials = db.query(func.count(Schedule.id)).filter(
        Schedule.schedule_type == 'trial',
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).scalar() or 0
    
    # 2. 完训试听课数
    completed_trials = db.query(func.count(Schedule.id)).filter(
        Schedule.schedule_type == 'trial',
        Schedule.execution_status == 'completed',
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).scalar() or 0
    
    # 3. 转化为正式课数（逻辑：该学生在试听课后产生了缴费记录或关联了正式课费用）
    # 这里简化为：统计在试听课后有缴费记录的独立学生数
    trial_students = db.query(schedule_student.c.student_id).join(
        Schedule, schedule_student.c.schedule_id == Schedule.id
    ).filter(
        Schedule.schedule_type == 'trial',
        Schedule.execution_status == 'completed',
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).distinct().subquery()
    
    converted_count = db.query(func.count(func.distinct(FeeLog.student_id))).join(
        trial_students, FeeLog.student_id == trial_students.c.student_id
    ).filter(
        FeeLog.log_type == 'payment',
        FeeLog.payment_date  >= start_date
    ).scalar() or 0
    
    return [
        {"name": "试听课总数", "value": total_trials},
        {"name": "完训试听课", "value": completed_trials},
        {"name": "成功转化(缴费)", "value": converted_count}
    ]

@router.get("/teachers/trial-efficiency")
def get_teacher_trial_efficiency(
    # 默认统计30天，最小1天，最大1080天，根据前端传入数据进行计算
    days: int = Query(default=30, ge=1, le=1080, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导师试听效能榜（试听课时数 & 转化率）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 基础数据：每位导师的试听课数和完训数
    teacher_stats = db.query(
        Teacher.id,
        Teacher.name,
        func.count(Schedule.id).label('trial_count'),
        func.sum(
            case(
                (Schedule.execution_status == 'completed', 1),
                else_=0
            )
        ).label('completed_count')
    ).join(
        Schedule, Teacher.id == Schedule.teacher_id
    ).filter(
        Schedule.schedule_type == 'trial',
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).group_by(
        Teacher.id, Teacher.name
    ).order_by(
        func.count(Schedule.id).desc()
    ).limit(10).all()
    
    result = []
    for row in teacher_stats:
        teacher_id, name, trial_count, completed_count = row
        
        # 计算该导师名下试听课学生的转化率
        # 获取这些试听课涉及的学生ID
        trial_student_ids = db.query(schedule_student.c.student_id).join(
            Schedule, schedule_student.c.schedule_id == Schedule.id
        ).filter(
            Schedule.teacher_id == teacher_id,
            Schedule.schedule_type == 'trial',
            Schedule.start_date >= start_date,
            Schedule.start_date <= end_date
        ).distinct().all()
        
        student_ids = [s[0] for s in trial_student_ids]
        if student_ids:
            converted_students = db.query(func.count(func.distinct(FeeLog.student_id))).filter(
                FeeLog.student_id.in_(student_ids),
                FeeLog.log_type == 'payment',
                FeeLog.payment_date  >= start_date
            ).scalar() or 0
            conversion_rate = round((converted_students / len(student_ids) * 100), 2) if student_ids else 0
        else:
            converted_students = 0
            conversion_rate = 0
            
        result.append({
            "teacher_id": teacher_id,
            "teacher_name": name,
            "trial_count": trial_count,
            "completed_count": completed_count,
            "converted_students": converted_students,
            "conversion_rate": conversion_rate
        })
        
    return result

@router.get("/fees/composition")
def get_fee_composition(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取收入构成（按科目）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 按科目统计收入
    course_revenue = db.query(
        Course.id,
        Course.name,
        func.sum(FeeLog.amount).label('total_amount')
    ).join(
        FeeLog, Course.id == FeeLog.course_id
    ).filter(
        FeeLog.log_type == 'payment'
    ).group_by(
        Course.id, Course.name
    ).all()
    
    result = [
        {
            "course_id": row[0],
            "course_name": row[1],
            "amount": round(row[2], 2) if row[2] else 0
        }
        for row in course_revenue if row[2] and row[2] > 0
    ]
    
    # 按金额降序排列
    result.sort(key=lambda x: x['amount'], reverse=True)
    
    return result

@router.get("/fees/monthly-trend")
def get_fee_monthly_trend(
    # 默认统计12个月，最小1个月，最大36个月，根据前端传入数据进行计算
    months: int = Query(default=12, ge=1, le=36, description="统计月数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取月度收入趋势"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    now = datetime.now()
    result = []
    
    for i in range(months - 1, -1, -1):
        # 计算每月的起止时间（从过去到现在）
        # 计算目标月份的第一天
        target_month = now.month - i
        target_year = now.year
        
        # 处理跨年情况
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        month_start = datetime(target_year, target_month, 1, 0, 0, 0, 0)
        
        # 计算目标月份的最后一天
        if target_month == 12:
            month_end = datetime(target_year + 1, 1, 1, 0, 0, 0, 0)
        else:
            month_end = datetime(target_year, target_month + 1, 1, 0, 0, 0, 0)
        
        # 如果是当前月，使用当前时间作为结束时间
        if target_year == now.year and target_month == now.month:
            month_end = now
        
        # 实收金额
        actual_income = db.query(func.sum(FeeLog.amount)).filter(
            FeeLog.log_type == 'payment',
            FeeLog.payment_date >= month_start.date(),
            FeeLog.payment_date < month_end.date()
        ).scalar() or 0.0
        
        # 应收金额（简化处理：假设所有缴费都是应收）
        receivable_income = actual_income
        
        # 退费金额
        refund_amount = db.query(func.sum(FeeLog.amount)).filter(
            FeeLog.log_type == 'refund',
            FeeLog.refund_date >= month_start.date(),
            FeeLog.refund_date < month_end.date()
        ).scalar() or 0.0
        
        result.append({
            "month": month_start.strftime('%Y-%m'),
            "actual_income": round(actual_income, 2),
            "receivable_income": round(receivable_income, 2),
            "refund_amount": round(abs(refund_amount), 2)
        })
    
    return result

@router.get("/fees/balance-distribution")
def get_balance_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学员课费余额分布"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 统计不同区间的学员数量
    ranges = [
        {"min": 0, "max": 5, "label": "0-5小时"},
        {"min": 5, "max": 10, "label": "5-10小时"},
        {"min": 10, "max": 20, "label": "10-20小时"},
        {"min": 20, "max": 999999, "label": "20+小时"}
    ]
    
    result = []
    for r in ranges:
        count = db.query(func.count(StudentFee.id)).filter(
            StudentFee.is_active == True,
            StudentFee.remaining_hours >= r['min'],
            StudentFee.remaining_hours < r['max']
        ).scalar() or 0
        
        result.append({
            "range": r['label'],
            "count": count
        })
    
    return result

@router.get("/fees/alerts")
def get_fee_alerts(
    # 默认返回20条，最小1条，最大100000条，根据前端传入数据进行计算
    limit: int = Query(default=20, ge=1, le=100000, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取收费预警列表"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    alerts = db.query(StudentFee).join(
        Student, StudentFee.student_id == Student.id
    ).join(
        Course, StudentFee.course_id == Course.id
    ).filter(
        StudentFee.is_active == True,
        StudentFee.remaining_hours <= StudentFee.alert_threshold,
        StudentFee.remaining_hours > 0
    ).order_by(
        StudentFee.remaining_hours.asc()
    ).limit(limit).all()
    
    result = []
    for fee in alerts:
        student = db.query(Student).filter(Student.id == fee.student_id).first()
        course = db.query(Course).filter(Course.id == fee.course_id).first()
        
        # 确定预警等级
        if fee.remaining_hours <= 2:
            alert_level = "danger"
        elif fee.remaining_hours <= fee.alert_threshold * 0.5:
            alert_level = "warning"
        else:
            alert_level = "info"
        
        result.append({
            "fee_id": fee.id,
            "student_id": fee.student_id,
            "student_name": student.name if student else "未知",
            "course_id": fee.course_id,
            "course_name": course.name if course else "未知",
            "remaining_hours": fee.remaining_hours,
            "remaining_amount": fee.remaining_amount,
            "alert_threshold": fee.alert_threshold,
            "alert_level": alert_level
        })
    
    return result

@router.get("/grades/distribution")
def get_grade_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取成绩等级分布（按最新一次考试成绩）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取每个学生每科的最新成绩（按创建时间）
    # 使用窗口函数或子查询获取每个分组的最新记录ID
    from sqlalchemy import text
    
    # 方法：先找到每个学生+科目+年级的最新成绩ID（不限考试阶段）
    latest_grade_ids_subquery = db.query(
        func.max(StudentGrade.id).label('latest_id')
    ).filter(
        StudentGrade.total_score > 0
    ).group_by(
        StudentGrade.student_id,
        StudentGrade.course_id,
        StudentGrade.grade_level
    ).subquery()
    
    # 根据ID获取完整的成绩记录
    grade_records = db.query(
        Course.name.label('course_name'),
        StudentGrade.score,
        StudentGrade.total_score
    ).join(
        latest_grade_ids_subquery,
        StudentGrade.id == latest_grade_ids_subquery.c.latest_id
    ).join(
        Course, StudentGrade.course_id == Course.id
    ).all()
    
    # 统计各等级人数
    courses_data = {}
    for record in grade_records:
        ratio = (record.score / record.total_score * 100) if record.total_score > 0 else 0
        
        if record.course_name not in courses_data:
            courses_data[record.course_name] = {
                "excellent": 0,  # >= 90%
                "good": 0,       # 75-90%
                "pass": 0,       # 60-75%
                "fail": 0        # < 60%
            }
        
        if ratio >= 90:
            courses_data[record.course_name]["excellent"] += 1
        elif ratio >= 75:
            courses_data[record.course_name]["good"] += 1
        elif ratio >= 60:
            courses_data[record.course_name]["pass"] += 1
        else:
            courses_data[record.course_name]["fail"] += 1
    
    result = [
        {
            "course_name": course_name,
            "excellent": data["excellent"],
            "good": data["good"],
            "pass": data["pass"],
            "fail": data["fail"]
        }
        for course_name, data in courses_data.items()
    ]
    
    return result

@router.get("/grades/improvement-ranking")
def get_improvement_ranking(
    limit: int = Query(default=10, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学员进步榜（按学生+科目+年级分组，进步幅度=最高得分比例-最低得分比例）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    ratio_expr = (StudentGrade.score / StudentGrade.total_score * 100)
    
    max_ratio_subquery = db.query(
        StudentGrade.student_id,
        StudentGrade.course_id,
        StudentGrade.grade_level,
        func.max(ratio_expr).label('max_ratio')
    ).filter(
        StudentGrade.total_score > 0
    ).group_by(
        StudentGrade.student_id,
        StudentGrade.course_id,
        StudentGrade.grade_level
    ).subquery()
    
    min_ratio_subquery = db.query(
        StudentGrade.student_id,
        StudentGrade.course_id,
        StudentGrade.grade_level,
        func.min(ratio_expr).label('min_ratio')
    ).filter(
        StudentGrade.total_score > 0
    ).group_by(
        StudentGrade.student_id,
        StudentGrade.course_id,
        StudentGrade.grade_level
    ).subquery()
    
    improvement_query = db.query(
        max_ratio_subquery.c.student_id,
        max_ratio_subquery.c.course_id,
        max_ratio_subquery.c.grade_level,
        max_ratio_subquery.c.max_ratio,
        min_ratio_subquery.c.min_ratio,
        (max_ratio_subquery.c.max_ratio - min_ratio_subquery.c.min_ratio).label('ratio_change')
    ).join(
        min_ratio_subquery,
        and_(
            max_ratio_subquery.c.student_id == min_ratio_subquery.c.student_id,
            max_ratio_subquery.c.course_id == min_ratio_subquery.c.course_id,
            max_ratio_subquery.c.grade_level == min_ratio_subquery.c.grade_level
        )
    ).order_by(
        desc('ratio_change')
    ).limit(limit).all()
    
    result = []
    for record in improvement_query:
        student = db.query(Student).filter(Student.id == record.student_id).first()
        course = db.query(Course).filter(Course.id == record.course_id).first()
        
        EXAM_STAGE_ORDER = get_exam_stage_order(db)
        exam_stage_order = case(
            *[(StudentGrade.exam_stage == stage, order) for stage, order in EXAM_STAGE_ORDER.items()],
            else_=0
        )
        latest_grade = db.query(StudentGrade).filter(
            StudentGrade.student_id == record.student_id,
            StudentGrade.course_id == record.course_id,
            StudentGrade.grade_level == record.grade_level,
            StudentGrade.total_score > 0
        ).order_by(desc(exam_stage_order)).first()
        
        current_ratio = round((latest_grade.score / latest_grade.total_score * 100), 2) if latest_grade and latest_grade.total_score > 0 else 0
        max_ratio = round(record.max_ratio, 2)
        ratio_change = round(record.ratio_change, 2)
 
        max_ratio_grade = db.query(StudentGrade).filter(
            StudentGrade.student_id == record.student_id,
            StudentGrade.course_id == record.course_id,
            StudentGrade.grade_level == record.grade_level,
            StudentGrade.total_score > 0,
            (StudentGrade.score / StudentGrade.total_score * 100) == record.max_ratio
        ).first()
 
        result.append({
            "student_id": record.student_id,
            "student_name": student.name if student else "未知",
            "course_id": record.course_id,
            "course_name": course.name if course else "未知",
            "grade_level": record.grade_level,
            "exam_stage": latest_grade.exam_stage if latest_grade else "",
            "max_ratio_exam_stage": max_ratio_grade.exam_stage if max_ratio_grade else "",
            "score_change": ratio_change,
            "current_score": latest_grade.score if latest_grade else 0,
            "current_ratio": current_ratio,
            "max_ratio": max_ratio,
            "exam_date": latest_grade.exam_date.strftime('%Y-%m-%d') if latest_grade and latest_grade.exam_date else None
        })
    
    return result

@router.get("/fees/unpaid-students")
def get_unpaid_students(
    # 默认返回50条，最小1条，最大100000条，根据前端传入数据进行计算
    limit: int = Query(default=50, ge=1, le=100000, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取未交费学员列表（上过正式课且已完训，但剩余课时数小于0或没有缴费记录的学员）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查询所有在读学员
    active_students = db.query(Student).filter(Student.is_active == True).all()
    
    result = []
    for student in active_students:
        # 查询该学员出席参与过的已完训正式课
        completed_schedules = db.query(Schedule).join(
            schedule_student, Schedule.id == schedule_student.c.schedule_id
        ).filter(
            schedule_student.c.student_id == student.id,
            schedule_student.c.attendance_status == 'present',
            Schedule.schedule_type == 'formal',
            Schedule.execution_status == 'completed'
        ).all()
        
        if not completed_schedules:
            continue
        
        # 按科目分组统计
        hpl = get_hours_per_lesson(db)        
        course_schedule_map = {}
        for schedule in completed_schedules:
            course_id = schedule.course_id
            if course_id not in course_schedule_map:
                course_schedule_map[course_id] = {
                    'course_id': course_id,
                    'course_name': schedule.course.name if schedule.course else '未知科目',
                    'teacher_name': schedule.teacher.name if schedule.teacher else '未知导师',
                    'schedule_count': 0
                    #'schedule_count': 0,
                    #'total_hours': 0.0
                }
            course_schedule_map[course_id]['schedule_count'] += 1
            # 计算每节课的课时
            #try:
            #    start = datetime.strptime(schedule.start_time, "%H:%M")
            #    end = datetime.strptime(schedule.end_time, "%H:%M")
            #    hours = (end - start).total_seconds() / 3600
            #    course_schedule_map[course_id]['total_hours'] += hours
            #except (ValueError, TypeError):
            #    pass
        
        # 检查每个科目的缴费情况
        unpaid_courses = []
        total_unpaid_hours = 0.0
        for course_id, course_info in course_schedule_map.items():
            # 查询该学员在该科目的缴费记录
            fee = db.query(StudentFee).filter(
                StudentFee.student_id == student.id,
                StudentFee.course_id == course_id,
                StudentFee.is_active == True
            ).first()
            
            # 判断是否未缴费：没有缴费记录 或 剩余课时数小于0
            if fee is None or fee.remaining_hours < 0:
                # 计算欠缴课时
                if fee is None:
                    #unpaid_hours = course_info['total_hours']
                    unpaid_hours = course_info['schedule_count'] * hpl
                else:
                    unpaid_hours = abs(fee.remaining_hours)
                course_info['unpaid_hours'] = round(unpaid_hours, 1)
                total_unpaid_hours += unpaid_hours
                unpaid_courses.append(course_info)
        
        if unpaid_courses:
            result.append({
                "student_id": student.id,
                "student_name": student.name,
                "unpaid_courses": unpaid_courses,
                "total_unpaid_hours": round(total_unpaid_hours, 1)
            })
    
    # 按未缴费科目数量降序排序
    result.sort(key=lambda x: len(x['unpaid_courses']), reverse=True)
    
    return result[:limit]

@router.get("/teachers/weekly-workload")
def get_teacher_weekly_workload(
    # 默认计算最近9天，最小2天，最大1080天，根据前端传入数据进行计算
    limit: int = Query(default=8, ge=1, le=1080, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导师周课时排行榜"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=limit)
    
    teacher_workload = db.query(
        Teacher.id,
        Teacher.name,
        func.count(Schedule.id).label('schedule_count')
    ).join(
        Schedule, Teacher.id == Schedule.teacher_id
    ).filter(
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date,
        Schedule.execution_status.in_(['pending', 'completed'])
    ).group_by(
        Teacher.id, Teacher.name
    ).order_by(
        desc(func.count(Schedule.id))
    ).limit(10).all()
    
    result = []
    for row in teacher_workload:
        teacher_id, name, schedule_count = row
        
        schedules = db.query(Schedule).filter(
            Schedule.teacher_id == teacher_id,
            Schedule.start_date >= start_date,
            Schedule.start_date <= end_date,
            Schedule.execution_status.in_(['pending', 'completed'])
        ).all()
        
        total_hours = 0
        for schedule in schedules:
            try:
                start_h, start_m = map(int, schedule.start_time.split(':'))
                end_h, end_m = map(int, schedule.end_time.split(':'))
                duration_minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m)
                if duration_minutes > 0:
                    total_hours += duration_minutes / 60
            except Exception as e:
                log_operation(db, "运营大屏", "计算课程时长失败", f"计算课程时长失败: {schedule.id}, 错误: {e}", current_user.username, "DEBUG")
                pass
        
        total_hours = round(total_hours, 1)
        
        result.append({
            "teacher_id": teacher_id,
            "teacher_name": name,
            "schedule_count": schedule_count,
            "total_hours": total_hours
        })
    
    return result

@router.get("/schedules/incomplete-list")
def get_incomplete_schedules_list(
    # 默认返回50条，最小1条，最大100000条，根据前端传入数据进行计算
    limit: int = Query(default=50, ge=1, le=100000, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取未完训课程安排列表"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    today = date.today()
    
    schedules = db.query(Schedule).join(
        Course, Schedule.course_id == Course.id
    ).join(
        Teacher, Schedule.teacher_id == Teacher.id
    ).join(
        Class, Schedule.class_id == Class.id
    ).join(
        Room, Schedule.room_id == Room.id
    ).filter(
        Schedule.end_date <= today,
        Schedule.execution_status.in_(['pending', 'postponed', 'cancelled'])
    ).order_by(
        Schedule.end_date.asc()
    ).limit(limit).all()
    
    result = []
    for schedule in schedules:
        # 获取该课程的学员列表
        students = db.query(Student).join(
            schedule_student, Student.id == schedule_student.c.student_id
        ).filter(
            schedule_student.c.schedule_id == schedule.id
        ).all()
        
        student_names = [s.name for s in students]
        
        result.append({
            "schedule_id": schedule.id,
            "course_name": schedule.course.name,
            "teacher_name": schedule.teacher.name,
            "class_name": schedule.class_.name,
            "room_name": schedule.room.name,
            "start_date": schedule.start_date.strftime('%Y-%m-%d'),
            "end_date": schedule.end_date.strftime('%Y-%m-%d'),
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "execution_status": schedule.execution_status,
            "schedule_type": schedule.schedule_type,
            "student_count": len(students),
            "student_names": "、".join(student_names[:5]) + ("等" if len(students) > 5 else ""),
            "cancel_reason": schedule.cancel_reason or "",
            "postpone_reason": schedule.postpone_reason or ""
        })
    
    return result

@router.get("/fees/refund-rate")
def get_refund_rate_trend(
    # 默认统计6个月，最小1个月，最大36个月，根据前端传入数据进行计算
    months: int = Query(default=6, ge=1, le=36, description="统计月数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取月度退费率趋势"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    now = datetime.now()
    result = []
    
    for i in range(months - 1, -1, -1):
        target_month = now.month - i
        target_year = now.year
        
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        month_start = datetime(target_year, target_month, 1, 0, 0, 0, 0)
        
        if target_month == 12:
            month_end = datetime(target_year + 1, 1, 1, 0, 0, 0, 0)
        else:
            month_end = datetime(target_year, target_month + 1, 1, 0, 0, 0, 0)
        
        if target_year == now.year and target_month == now.month:
            month_end = now
        
        # 实收金额
        actual_income = db.query(func.sum(FeeLog.amount)).filter(
            FeeLog.log_type == 'payment',
            FeeLog.payment_date >= month_start.date(),
            FeeLog.payment_date < month_end.date()
        ).scalar() or 0.0
        
        # 退费金额
        refund_amount = db.query(func.sum(FeeLog.amount)).filter(
            FeeLog.log_type == 'refund',
            FeeLog.refund_date >= month_start.date(),
            FeeLog.refund_date < month_end.date()
        ).scalar() or 0.0
        
        # 计算退费率
        total_amount = actual_income + abs(refund_amount)
        refund_rate = round((abs(refund_amount) / total_amount * 100), 2) if total_amount > 0 else 0.0
        
        result.append({
            "month": month_start.strftime('%Y-%m'),
            "actual_income": round(actual_income, 2),
            "refund_amount": round(abs(refund_amount), 2),
            "refund_rate": refund_rate
        })
    
    return result

@router.get("/students/growth-rate")
def get_student_growth_rate(
    # 默认统计6个月，最小1个月，最大36个月，根据前端传入数据进行计算
    months: int = Query(default=6, ge=1, le=36, description="统计月数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取新学员增长率趋势"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    now = datetime.now()
    result = []
    
    for i in range(months - 1, -1, -1):
        target_month = now.month - i
        target_year = now.year
        
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        month_start = datetime(target_year, target_month, 1, 0, 0, 0, 0)
        
        if target_month == 12:
            month_end = datetime(target_year + 1, 1, 1, 0, 0, 0, 0)
        else:
            month_end = datetime(target_year, target_month + 1, 1, 0, 0, 0, 0)
        
        if target_year == now.year and target_month == now.month:
            month_end = now
        
        # 当月新增学员数
        new_students = db.query(func.count(Student.id)).filter(
            Student.enrollment_date >= month_start.date(),
            Student.enrollment_date < month_end.date()
        ).scalar() or 0
        
        result.append({
            "month": month_start.strftime('%Y-%m'),
            "new_students": new_students
        })
    
    # 计算增长率
    for i in range(1, len(result)):
        prev_count = result[i-1]['new_students']
        curr_count = result[i]['new_students']
        
        if prev_count > 0:
            growth_rate = round(((curr_count - prev_count) / prev_count * 100), 2)
        else:
            growth_rate = 0.0 if curr_count == 0 else 100.0
        
        result[i]['growth_rate'] = growth_rate
    
    if result:
        result[0]['growth_rate'] = 0.0
    
    return result

@router.get("/courses/popular-topN")
def get_popular_courses_topN(
    # 默认返回5条，最小1条，最大300条，根据前端传入数据进行计算
    limit: int = Query(default=5, ge=1, le=300, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取热门科目TOP5（按学员人数）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查询每个科目的学员数量
    course_stats = db.query(
        Course.id,
        Course.name,
        func.count(func.distinct(StudentFee.student_id)).label('student_count'),
        func.sum(StudentFee.consumed_hours).label('consumed_hours')
    ).join(
        StudentFee, Course.id == StudentFee.course_id
    ).filter(
        StudentFee.is_active == True
    ).group_by(
        Course.id, Course.name
    ).order_by(
        desc(func.count(func.distinct(StudentFee.student_id)))
    ).limit(limit).all()
    
    result = []
    for row in course_stats:
        result.append({
            "course_id": row[0],
            "course_name": row[1],
            "student_count": row[2],
            "consumed_hours": round(row[3], 1) if row[3] else 0
        })
    
    return result

@router.get("/rooms/utilization")
def get_room_utilization(
    # 默认统计7天，最小1天，最大1080天，根据前端传入数据进行计算
    days: int = Query(default=7, ge=1, le=1080, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取近N天各教室利用率（基于出席学员数/教室容量）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 获取所有在用教室
    rooms = db.query(Room).filter(Room.is_active == True).all()
    
    result = []
    for room in rooms:
        # 查询该教室在近N天的课程安排
        schedules = db.query(Schedule).filter(
            Schedule.room_id == room.id,
            Schedule.start_date >= start_date,
            Schedule.start_date <= end_date,
            Schedule.execution_status.in_(['pending', 'completed'])
        ).all()
        
        # 如果没有课程安排，利用率为0
        #if not schedules:
        #    continue
        
        # 计算每个课程安排的出席率并累加
        total_utilization = 0
        schedule_count = len(schedules)
        
        for schedule in schedules:
            # 获取该课程的学员数量（出席状态为present的学员）
            present_students = db.query(func.count(schedule_student.c.student_id)).join(
                Schedule, schedule_student.c.schedule_id == Schedule.id
            ).filter(
                Schedule.id == schedule.id,
                schedule_student.c.attendance_status == 'present'
            ).scalar() or 0
            
            # 计算该课程的利用率
            if room.capacity > 0:
                utilization = (present_students / room.capacity) * 100
                total_utilization += utilization
        
        # 计算平均利用率
        avg_utilization = round(total_utilization / schedule_count, 2) if schedule_count > 0 else 0
        
        result.append({
            "room_id": room.id,
            "room_name": room.name,
            "room_code": room.code,
            "capacity": room.capacity,
            "schedule_count": schedule_count,
            "avg_utilization": avg_utilization
        })
    
    # 按利用率降序排列
    result.sort(key=lambda x: x['avg_utilization'], reverse=True)
    
    return result

@router.get("/db-pool-status")
def get_database_pool_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据库连接池状态（需要管理员权限）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员或运营管理导师权限")
    
    return get_pool_status()

@router.get("/schedules/conversion-details")
def get_conversion_details(
    # 默认统计30天，最小1天，最大90天，根据前端传入数据进行计算
    days: int = Query(default=30, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取本月转化率详细数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 获取完训的试听课
    completed_trials = db.query(Schedule).join(
        schedule_student, Schedule.id == schedule_student.c.schedule_id
    ).filter(
        Schedule.schedule_type == 'trial',
        Schedule.execution_status == 'completed',
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).all()
    
    result = []
    for schedule in completed_trials:
        for student in schedule.students:
            # 检查该学生是否有缴费记录
            has_payment = db.query(FeeLog).filter(
                FeeLog.student_id == student.id,
                FeeLog.log_type == 'payment',
                FeeLog.payment_date >= schedule.start_date
            ).first()
            
            result.append({
                "student_name": student.name,
                "course_name": schedule.course.name if schedule.course else "-",
                "teacher_name": schedule.teacher.name if schedule.teacher else "-",
                "trial_date": schedule.start_date.strftime('%Y-%m-%d'),
                "converted": "是" if has_payment else "否",
                "payment_date": has_payment.payment_date.strftime('%Y-%m-%d') if has_payment else "-",
                "amount": has_payment.amount if has_payment else 0
            })
    
    return result

@router.get("/students/renewal-details")
def get_renewal_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取学员续费率详细数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    # 获取本月所有缴费记录
    payment_logs_this_month = db.query(FeeLog).filter(
        FeeLog.log_type == 'payment',
        FeeLog.payment_date >= month_start.date(),
        FeeLog.payment_date <= now.date()
    ).order_by(FeeLog.payment_date.asc()).all()
    
     # 按科目统计每个学员本月的缴费情况
    student_course_payments = {}
    for payment_log in payment_logs_this_month:
        key = (payment_log.student_id, payment_log.course_id)
        if key not in student_course_payments:
            student_course_payments[key] = []
        student_course_payments[key].append(payment_log)
    
    result = []
    
    # 判断每个学员在每个科目是否算续费
    for (student_id, course_id), payments in student_course_payments.items():
        # 检查该学员在该科目是否有历史缴费记录（本月之前）
        previous_fee = db.query(StudentFee).filter(
            StudentFee.student_id == student_id,
            StudentFee.course_id == course_id,
            StudentFee.start_date < month_start,
            StudentFee.is_active == True
        ).first()
        
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            continue
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if previous_fee:
            # 老学员：本月有缴费就算续费
            for payment in payments:
                result.append({
                    "student_name": student.name,
                    "course_name": course.name if course else "-",
                    "previous_amount": previous_fee.total_actual_amount,
                    "renewal_amount": payment.amount,
                    "renewal_date": payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else "-",
                    "renewal_type": "老学员续费",
                    "renewed": "是"
                })
        else:
            # 新学员：多次缴费才算续费
            if len(payments) >= 2:
                # 第一次缴费
                first_payment = payments[0]
                # 后续缴费
                for i in range(1, len(payments)):
                    payment = payments[i]
                    result.append({
                        "student_name": student.name,
                        "course_name": course.name if course else "-",
                        "previous_amount": first_payment.amount,
                        "renewal_amount": payment.amount,
                        "renewal_date": payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else "-",
                        "renewal_type": "新学员续费",
                        "renewed": "是"
                    })
    
    # 按续费日期降序排列
    result.sort(key=lambda x: x['renewal_date'], reverse=True)
    
    return result

@router.get("/fees/refund-details")
def get_refund_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取退费总额详细数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取所有退费记录
    refund_logs = db.query(FeeLog).filter(
        FeeLog.log_type == 'refund'
    ).order_by(FeeLog.payment_date.desc()).all()
    
    result = []
    for log in refund_logs:
        student = db.query(Student).filter(Student.id == log.student_id).first()
        course = db.query(Course).filter(Course.id == log.course_id).first()
        
        result.append({
            "student_name": student.name if student else "-",
            "course_name": course.name if course else "-",
            "amount": abs(log.amount),
            "refund_date": log.payment_date.strftime('%Y-%m-%d'),
            "status": "已退费",
            "remark": log.description or "-"
        })
    
    return result

@router.get("/fees/owed-details")
def get_owed_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取欠费总额详细数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 获取所有有欠费的学生（应收大于实收）
    owed_fees = db.query(StudentFee).filter(
        StudentFee.total_receivable_amount > StudentFee.total_actual_amount
    ).all()
    
    result = []
    for fee in owed_fees:
        student = db.query(Student).filter(Student.id == fee.student_id).first()
        course = db.query(Course).filter(Course.id == fee.course_id).first()
        
        owed_amount = fee.total_receivable_amount - fee.total_actual_amount
        
        result.append({
            "student_name": student.name if student else "-",
            "course_name": course.name if course else "-",
            "amount": owed_amount,
            "receivable_amount": fee.total_receivable_amount,
            "actual_amount": fee.total_actual_amount,
            "status": "优惠",
            "remark": f"应收{fee.total_receivable_amount}元，实收{fee.total_actual_amount}元"
        })
    
    return result

@router.get("/fees/monthly-details")
def get_monthly_details(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取本月收入详细数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 构建日期范围
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # 获取指定月份的缴费记录
    payment_logs = db.query(FeeLog).filter(
        FeeLog.log_type == 'payment',
        FeeLog.payment_date >= start_date.date(),
        FeeLog.payment_date < end_date.date()
    ).order_by(FeeLog.payment_date.desc()).all()
    
    result = []
    for log in payment_logs:
        student = db.query(Student).filter(Student.id == log.student_id).first()
        course = db.query(Course).filter(Course.id == log.course_id).first()
        
        result.append({
            "student_name": student.name if student else "-",
            "course_name": course.name if course else "-",
            "amount": log.amount,
            "payment_date": log.payment_date.strftime('%Y-%m-%d'),
            "status": "已缴费",
            "remark": log.description or "-"
        })
    
    return result

@router.get("/fees/yearly-details")
def get_yearly_details(
    year: int = Query(..., description="年份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当年收入详细数据"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 构建日期范围
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    
    # 获取指定年份的缴费记录
    payment_logs = db.query(FeeLog).filter(
        FeeLog.log_type == 'payment',
        FeeLog.payment_date >= start_date.date(),
        FeeLog.payment_date < end_date.date()
    ).order_by(FeeLog.payment_date.desc()).all()
    
    result = []
    for log in payment_logs:
        student = db.query(Student).filter(Student.id == log.student_id).first()
        course = db.query(Course).filter(Course.id == log.course_id).first()
        
        result.append({
            "student_name": student.name if student else "-",
            "course_name": course.name if course else "-",
            "amount": log.amount,
            "payment_date": log.payment_date.strftime('%Y-%m-%d'),
            "status": "已缴费",
            "remark": log.description or "-"
        })
    
    return result

@router.get("/students/long-term-ranking")
def get_long_term_students(
    # 默认返回90条，最小1条，最大500条，根据前端传入数据进行计算
    limit: int = Query(default=90, ge=1, le=500, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取长效学员榜（按进入机构日期排序，取最长的学员）"""
    if not check_dashboard_permission(db, current_user):
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查询有进入机构日期的学员，按进入机构日期升序排列（最早的在前）
    students = db.query(
        Student.id,
        Student.code,
        Student.name,
        Student.school,
        Student.grade,
        Student.enrollment_date,
        Student.contact_person,
        Student.contact_phone,
        Student.email,
        Student.is_active
    # 状态为激活的学员
    ).filter(
        Student.is_active == True
    ).filter(
        Student.enrollment_date.isnot(None)
    ).order_by(
        asc(Student.enrollment_date)
    ).limit(limit).all()
    
    result = []
    for student in students:
        # 计算在机构时长（天数）
        today = date.today()
        enrollment_date = student.enrollment_date
        days_in_organization = (today - enrollment_date).days
        
        # 格式化日期
        enrollment_date_str = enrollment_date.strftime('%Y-%m-%d') if enrollment_date else '-'
        
        # 计算累计完成课时：查询该学员出席的所有完训状态课程的课时之和
        # 1.先统计该学员出席的所有完训状态课程的课节数
        completed_schedules = db.query(Schedule).join(
            schedule_student, Schedule.id == schedule_student.c.schedule_id
        ).filter(
            schedule_student.c.student_id == student.id,
            schedule_student.c.attendance_status == 'present',
            Schedule.execution_status == 'completed'
        ).all()
        # 2.计算课时总数（每节课按配置课时数计算）
        total_completed_hours = len(completed_schedules) * get_hours_per_lesson(db)
        
        result.append({
            "student_id": student.id,
            "student_code": student.code,
            "student_name": student.name,
            "school": student.school or '-',
            "grade": student.grade or '-',
            "enrollment_date": enrollment_date_str,
            "days_in_organization": days_in_organization,
            "total_completed_hours": total_completed_hours,
            "contact_person": student.contact_person or '-',
            "contact_phone": student.contact_phone or '-',
            "email": student.email or '-',
            "is_active": student.is_active
        })
    
    return result