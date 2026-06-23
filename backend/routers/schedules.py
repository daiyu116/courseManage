# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional, Dict, Set
from datetime import date, datetime
from database import get_db
from models import Settings, Schedule, Course, Teacher, Class, Student, Room, Leave, schedule_student
from schemas import ScheduleCreate, ScheduleUpdate, Schedule as ScheduleSchema, ScheduleFilter, ConflictInfo, ScheduleCompleteFeedback, SchedulePostpone, ScheduleMakeup, ScheduleDeclineMakeup, ScheduleCancel, PaginatedScheduleResponse, ScheduleAttendanceUpdate
from routers.auth import get_teacher_visibility_filter, get_current_user, get_current_superadmin_user, get_current_course_admin_user, User
from optimizer import ScheduleOptimizer
from openpyxl import Workbook
from io import BytesIO
from utils.logger import log_operation
import csv
from utils.holiday_utils import is_holiday
from utils.wechat_notifier import wechat_notifier
from utils.email_notifier import email_notifier
from sqlalchemy.orm import joinedload
from sqlalchemy import select
import json

router = APIRouter()

def get_students_by_class(db: Session, class_id: int, is_active: bool = None) -> List[Student]:
    """查询属于某个班级的学生（使用多对多关系）"""
    query = db.query(Student).options(joinedload(Student.classes))
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)
    students = query.all()
    # 过滤出属于指定班级的学生
    return [s for s in students if any(c.id == class_id for c in s.classes)]

def check_conflicts(db: Session, schedule: Schedule, exclude_id: int = None, class_students_cache: Dict[int, Set[int]] = None, check_room_conflict: bool = True) -> List[ConflictInfo]:
    conflicts = []
    
    # 获取所有启用的条件
    from models import Condition
    active_conditions = db.query(Condition).filter(Condition.is_active == True).all()
    
    # 软性约束字典
    soft_constraints = {}
    for condition in active_conditions:
        if not condition.is_hard_constraint:
            soft_constraints[condition.condition_type] = condition.description
    
    query = db.query(Schedule).filter(
        Schedule.day_of_week == schedule.day_of_week,
        Schedule.start_time < schedule.end_time,
        Schedule.end_time > schedule.start_time,
        Schedule.start_date <= schedule.end_date,
        Schedule.end_date >= schedule.start_date
    )
    
    if exclude_id:
        query = query.filter(Schedule.id != exclude_id)
    
    existing_schedules = query.all()
    
    for existing in existing_schedules:
        # 硬性约束：导师时间冲突（HC_TEACHER_TIME）
        if existing.teacher_id == schedule.teacher_id:
            conflicts.append(ConflictInfo(
                schedule_id=existing.id,
                conflict_type="导师时间冲突",
                conflict_description=f"导师 {schedule.teacher_id} 在 {schedule.day_of_week} {schedule.start_time}-{schedule.end_time} 已有课程安排",
                related_schedules=[existing.id]
            ))
        
        # 硬性约束：班级时间冲突（HC_CLASS_TIME）
        if existing.class_id == schedule.class_id:
            conflicts.append(ConflictInfo(
                schedule_id=existing.id,
                conflict_type="班级时间冲突",
                conflict_description=f"班级 {schedule.class_id} 在 {schedule.day_of_week} {schedule.start_time}-{schedule.end_time} 已有课程安排",
                related_schedules=[existing.id]
            ))
        else:
            # 硬性约束：学员时间冲突（HC_STUDENT_TIME）
            # 检查两个班级是否有共同的学生
            if class_students_cache is None:
                # 如果没有缓存，查询数据库
                class1_students = get_students_by_class(db, schedule.class_id, is_active=True)
                class2_students = get_students_by_class(db, existing.class_id, is_active=True)
                
                class1_student_ids = {s.id for s in class1_students}
                class2_student_ids = {s.id for s in class2_students}
            else:
                # 使用缓存
                class1_student_ids = class_students_cache.get(schedule.class_id, set())
                class2_student_ids = class_students_cache.get(existing.class_id, set())
            
            common_students = class1_student_ids & class2_student_ids
            if common_students:
                conflicts.append(ConflictInfo(
                    schedule_id=existing.id,
                    conflict_type="学生时间冲突",
                    conflict_description=f"班级 {schedule.class_id} 和班级 {existing.class_id} 有共同学生，在 {schedule.day_of_week} {schedule.start_time}-{schedule.end_time} 时间冲突",
                    related_schedules=[existing.id]
                ))

        # 教室时间冲突
        if check_room_conflict and existing.room_id is not None and schedule.room_id is not None and existing.room_id == schedule.room_id:
                conflicts.append(ConflictInfo(
                    schedule_id=existing.id,
                    conflict_type="教室时间冲突",
                    conflict_description=f"教室 {schedule.room_id} 在 {schedule.day_of_week} {schedule.start_time}-{schedule.end_time} 已有课程安排",
                    related_schedules=[existing.id]
                ))
    
    return conflicts

@router.get("/{schedule_id}/absent-students")
async def get_absent_students(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """获取需要补课的学员列表（缺席或请假且未补课）"""
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    # 查询缺席或请假且未补课的学员
    from sqlalchemy import select
    stmt = select(schedule_student).where(
        (schedule_student.c.schedule_id == schedule_id) &
        (schedule_student.c.attendance_status.in_(['absent', 'leave'])) &
        ((schedule_student.c.makeup_status == None) | (schedule_student.c.makeup_status == 'pending'))
    )
    
    result = db.execute(stmt)
    student_records = result.fetchall()
    
    # 获取学员详细信息
    absent_students = []
    for record in student_records:
        student = db.query(Student).filter(Student.id == record.student_id).first()
        if student and student.is_active:
            absent_students.append({
                'id': student.id,
                'name': student.name,
                'attendance_status': record.attendance_status,
                'absence_reason': record.absence_reason
            })
    
    return absent_students

def check_leave_conflicts(db: Session, schedule: Schedule) -> List[str]:
    conflicts = []
    
    teacher_leaves = db.query(Leave).filter(
        Leave.leave_type == "teacher",
        Leave.teacher_id == schedule.teacher_id,
        Leave.start_date <= schedule.end_date,
        Leave.end_date >= schedule.start_date
    ).all()
    
    for leave in teacher_leaves:
        conflicts.append(f"导师请假冲突: {leave.start_date} 至 {leave.end_date} - {leave.reason}")
    
    # 获取班级的所有学员
    students = get_students_by_class(db, schedule.class_id, is_active=True)
    
    # 检查学员请假
    for student in students:
        student_leaves = db.query(Leave).filter(
            Leave.leave_type == "student",
            Leave.student_id == student.id,
            Leave.start_date <= schedule.end_date,
            Leave.end_date >= schedule.start_date
        ).all()
        
        for leave in student_leaves:
            conflicts.append(f"学员请假冲突: {leave.start_date} 至 {leave.end_date} - {leave.reason}")
    
    return conflicts

def check_teacher_availability(db: Session, teacher_id: int, day_of_week: int, start_time: str, end_time: str) -> bool:
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        return False
    
    # 检查日期
    available_days = [int(d.strip()) for d in teacher.available_days.split(",")]
    if day_of_week not in available_days:
        return False
    
    # 检查时间段
    available_time_slots = [t.strip() for t in teacher.available_time_slots.split(",")]
    time_slot = f"{start_time}-{end_time}"
    
    # 检查是否有包含或被包含的时间段
    for available_slot in available_time_slots:
        available_start, available_end = available_slot.split('-')
        
        # 检查是否完全匹配
        if time_slot == available_slot:
            return True
        
        # 检查是否在可用时间段内
        if (start_time >= available_start and end_time <= available_end):
            return True
    
    return False

def check_class_availability(db: Session, class_id: int, day_of_week: int, start_time: str, end_time: str) -> bool:
    """检查班级的所有学生是否在该时间段可用"""
    students = get_students_by_class(db, class_id, is_active=True)
    
    if not students:
        return False
    
    for student in students:
        # 检查日期
        available_days = [int(d.strip()) for d in student.available_days.split(",")]
        if day_of_week not in available_days:
            return False
        
        # 检查时间段
        available_time_slots = [t.strip() for t in student.available_time_slots.split(",")]
        time_slot = f"{start_time}-{end_time}"
        
        # 检查是否有包含或被包含的时间段
        has_available_slot = False
        for available_slot in available_time_slots:
            available_start, available_end = available_slot.split('-')
            
            # 检查是否完全匹配
            if time_slot == available_slot:
                has_available_slot = True
                break
            
            # 检查是否在可用时间段内
            if start_time >= available_start and end_time <= available_end:
                has_available_slot = True
                break
        
        if not has_available_slot:
            return False
    
    return True

def check_class_availability_with_details(db: Session, class_id: int, day_of_week: int, start_time: str, end_time: str, is_holiday: bool = False) -> dict:
    """检查班级的所有学生是否在该时间段可用，并返回详细信息"""
    students = get_students_by_class(db, class_id, is_active=True)
    
    if not students:
        return {
            'available': False,
            'unavailable_students': [],
            'message': '班级没有活跃学员'
        }
    
    unavailable_students = []
    
    for student in students:
        day_available = True
        time_available = True
        
        # 检查日期
        # 如果是节假日且学生允许节假日排课，则跳过常规星期几的检查
        if not (is_holiday and student.allow_holiday_scheduling):
            if student.available_days:
                available_days = [int(d.strip()) for d in student.available_days.split(",")]
                if day_of_week not in available_days:
                    day_available = False
            else:
                day_available = False
        
        # 检查时间段
        # 如果是节假日且学生允许节假日排课，同样跳过时间段检查
        if not (is_holiday and student.allow_holiday_scheduling):
            if day_available and student.available_time_slots:
                available_time_slots = [t.strip() for t in student.available_time_slots.split(",")]
                time_slot = f"{start_time}-{end_time}"
                
                has_available_slot = False
                for available_slot in available_time_slots:
                    try:
                        available_start, available_end = available_slot.split('-')
                        
                        # 检查是否完全匹配
                        if time_slot == available_slot:
                            has_available_slot = True
                            break
                        
                        # 检查是否在可用时间段内
                        if start_time >= available_start and end_time <= available_end:
                            has_available_slot = True
                            break
                    except:
                        continue
                
                if not has_available_slot:
                    time_available = False
            elif day_available:
                time_available = False
        
        if not day_available or not time_available:
            unavailable_students.append({
                'id': student.id,
                'name': student.name,
                'day_available': day_available,
                'time_available': time_available
            })
    
    return {
        'available': len(unavailable_students) == 0,
        'unavailable_students': unavailable_students,
        'message': '所有学员都可用' if len(unavailable_students) == 0 else f'{len(unavailable_students)}个学员不可用'
    }

def check_teacher_course_availability(db: Session, teacher_id: int, course_id: int) -> bool:
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        return False
    
    teacher_course_ids = [c.id for c in teacher.courses]
    return course_id in teacher_course_ids

@router.get("", response_model=PaginatedScheduleResponse)
def get_schedules(
    skip: int = 0,
    limit: int = 100000,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    teacher_ids: Optional[str] = None,
    class_id: Optional[int] = None,
    class_ids: Optional[str] = None,
    course_id: Optional[int] = None,
    course_ids: Optional[str] = None,
    room_id: Optional[int] = None,
    room_ids: Optional[str] = None,
    day_of_week: Optional[int] = None,
    days_of_week: Optional[str] = None,
    student_ids: Optional[str] = None,
    has_conflict: Optional[bool] = Query(None),
    execution_status: Optional[str] = None,
    schedule_type: Optional[str] = None,
    has_absent_students: Optional[bool] = Query(None),
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    query = db.query(Schedule).options(
        joinedload(Schedule.course),
        joinedload(Schedule.teacher),
        joinedload(Schedule.class_),
        joinedload(Schedule.room)
    )
    
    # 应用导师可见性过滤
    teacher_filter = get_teacher_visibility_filter(db, current_user)
    
    if teacher_filter is not None:
        if hasattr(teacher_filter, 'compile'):
            # 处理 false() 对象
            query = query.filter(teacher_filter)
        else:
            # 现在 teacher_filter 直接就是 ID (int)
            log_operation(db, "课程安排", "应用导师过滤", f"教师ID: {current_user.id} - {current_user.username}, 导师过滤ID: {teacher_filter}", current_user.username, "DEBUG")
            query = query.filter(Schedule.teacher_id == teacher_filter)
    else:
        log_operation(db, "课程安排", "导师可见性限制未启用", f"教师ID: {current_user.id} - {current_user.username}, 导师过滤: None", current_user.username, "DEBUG")

    # 如果指定了ID，直接按ID过滤（最高优先级）
    if id:
        query = query.filter(Schedule.id == id)

    # 学员查询逻辑：直接查询 schedule_student 表中该学员参与的课程安排
    if student_ids:
        try:
            student_id_list = [int(id.strip()) for id in student_ids.split(',')]
            
            # 直接查询该学员在 schedule_student 表中关联的所有课程安排ID
            stmt = select(schedule_student.c.schedule_id).where(
                schedule_student.c.student_id.in_(student_id_list)
            )
            result = db.execute(stmt)
            schedule_ids = [row[0] for row in result.fetchall()]
            
            # 如果学员没有参与任何课程安排，返回空结果
            if not schedule_ids:
                return {
                    "items": [],
                    "total": 0
                }
            
            # 只查询这些课程安排
            query = query.filter(Schedule.id.in_(schedule_ids))
        except ValueError:
            pass
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Schedule.end_date >= start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Schedule.start_date <= end_date_obj)
        except ValueError:
            pass
    
    if teacher_id:
        query = query.filter(Schedule.teacher_id == teacher_id)
    
    if teacher_ids:
        try:
            ids = [int(id.strip()) for id in teacher_ids.split(',')]
            query = query.filter(Schedule.teacher_id.in_(ids))
        except ValueError:
            pass
    
    if class_id:
        query = query.filter(Schedule.class_id == class_id)
    
    if class_ids:
        try:
            ids = [int(id.strip()) for id in class_ids.split(',')]
            query = query.filter(Schedule.class_id.in_(ids))
        except ValueError:
            pass
    
    if course_id:
        query = query.filter(Schedule.course_id == course_id)
    
    if course_ids:
        try:
            ids = [int(id.strip()) for id in course_ids.split(',')]
            query = query.filter(Schedule.course_id.in_(ids))
        except ValueError:
            pass
    
    if room_id:
        query = query.filter(Schedule.room_id == room_id)
    
    if room_ids:
        try:
            ids = [int(id.strip()) for id in room_ids.split(',')]
            query = query.filter(Schedule.room_id.in_(ids))
        except ValueError:
            pass
    
    if day_of_week:
        query = query.filter(Schedule.day_of_week == day_of_week)
    
    if days_of_week:
        try:
            days = [int(day.strip()) for day in days_of_week.split(',')]
            query = query.filter(Schedule.day_of_week.in_(days))
        except ValueError:
            pass
    
    if has_conflict is not None:
        query = query.filter(Schedule.has_conflict == has_conflict)
    
    if execution_status and execution_status.strip():
        # 支持多个执行状态，用逗号分隔
        status_list = [status.strip() for status in execution_status.split(',') if status.strip()]
        if len(status_list) == 1:
            query = query.filter(Schedule.execution_status == status_list[0])
        elif len(status_list) > 1:
            query = query.filter(Schedule.execution_status.in_(status_list))
    
    if schedule_type and schedule_type.strip():
        query = query.filter(Schedule.schedule_type == schedule_type)
    
    if has_absent_students is not None:
        if has_absent_students:
            # 过滤出有缺席或请假学员的课程（未全员出席）
            subquery = db.query(schedule_student.c.schedule_id).filter(
                schedule_student.c.attendance_status.in_(['leave', 'absent'])
            ).distinct()
            query = query.filter(Schedule.id.in_(subquery))
        else:
            # 过滤出全员出席的课程
            subquery = db.query(schedule_student.c.schedule_id).filter(
                schedule_student.c.attendance_status.in_(['leave', 'absent'])
            ).distinct()
            query = query.filter(~Schedule.id.in_(subquery))

    # 构建排序条件列表
    order_by_clauses = []
    
    # 应用排序
    if sort_field and sort_field != 'id':
        # 处理关联对象的排序
        if sort_field == 'course':
            # 按科目名称排序
            query = query.join(Course)
            if sort_order == "desc":
                order_by_clauses.append(desc(Course.name))
            else:
                order_by_clauses.append(asc(Course.name))
        elif sort_field == 'teacher':
            # 按导师名称排序
            query = query.join(Teacher)
            if sort_order == "desc":
                order_by_clauses.append(desc(Teacher.name))
            else:
                order_by_clauses.append(asc(Teacher.name))
        elif sort_field == 'class':
            # 按班级名称排序
            query = query.join(Class)
            if sort_order == "desc":
                order_by_clauses.append(desc(Class.name))
            else:
                order_by_clauses.append(asc(Class.name))
        elif sort_field == 'room':
            # 按教室名称排序
            query = query.join(Room)
            if sort_order == "desc":
                order_by_clauses.append(desc(Room.name))
            else:
                order_by_clauses.append(asc(Room.name))
        else:
            # 按Schedule表的其他字段排序
            sort_column = getattr(Schedule, sort_field, None)
            if sort_column:
                if sort_order == "desc":
                    order_by_clauses.append(desc(sort_column))
                else:
                    order_by_clauses.append(asc(sort_column))
    
    # 始终添加ID作为第二排序条件（保证排序稳定性）
    if sort_order == "desc":
        order_by_clauses.append(desc(Schedule.id))
    else:
        order_by_clauses.append(asc(Schedule.id))
    
    # 一次性应用所有排序条件
    if order_by_clauses:
        query = query.order_by(*order_by_clauses)
    
    # 添加distinct以避免join导致的重复结果
    query = query.distinct()
    total = query.count()
    schedules = query.offset(skip).limit(limit).all()
    
    result = []
    for schedule in schedules:
        # 1. 获取学员列表
        stmt = select(
            schedule_student.c.student_id, 
            schedule_student.c.attendance_status,
            schedule_student.c.makeup_status,
            schedule_student.c.makeup_schedule_id,
            schedule_student.c.declined_reason
        ).where(
            schedule_student.c.schedule_id == schedule.id
        )
        student_result = db.execute(stmt)
        scheduled_students = []
        for row in student_result:
            student = db.query(Student).filter(Student.id == row[0]).first()
            if student:
                scheduled_students.append({
                    "id": student.id,
                    "name": student.name,
                    "attendance_status": row[1] if row[1] else 'pending',
                    "makeup_status": row[2],
                    "makeup_schedule_id": row[3],
                    "declined_reason": row[4]
                })
        
        # 2. 安全地构建字典，严格匹配 Schedule Schema 的字段类型
        try:
            # 处理日期时间格式化，防止 None 或格式错误
            start_date_str = schedule.start_date.isoformat() if isinstance(schedule.start_date, date) else str(schedule.start_date) if schedule.start_date else None
            end_date_str = schedule.end_date.isoformat() if isinstance(schedule.end_date, date) else str(schedule.end_date) if schedule.end_date else None
            created_at_str = schedule.created_at.isoformat() if hasattr(schedule.created_at, 'isoformat') and schedule.created_at else None
            updated_at_str = schedule.updated_at.isoformat() if hasattr(schedule.updated_at, 'isoformat') and schedule.updated_at else None

            schedule_dict = {
                "id": schedule.id,
                "course_id": schedule.course_id,
                "teacher_id": schedule.teacher_id,
                "class_id": schedule.class_id,
                "room_id": schedule.room_id,
                "day_of_week": schedule.day_of_week,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "has_conflict": schedule.has_conflict,
                "conflict_reason": schedule.conflict_reason,
                "execution_status": schedule.execution_status,
                "content_feedback": schedule.content_feedback,
                "cancel_reason": schedule.cancel_reason,
                "postpone_reason": schedule.postpone_reason,
                "homework_regular": schedule.homework_regular,
                "homework_images": schedule.homework_images,
                "room_type": schedule.room_type,
                "meeting_link": schedule.meeting_link,
                "schedule_type": schedule.schedule_type,
                "scheduled_students": scheduled_students,
                "created_at": created_at_str,
                "updated_at": updated_at_str,
                "course": {
                    "id": schedule.course.id,
                    "code": schedule.course.code,
                    "name": schedule.course.name
                } if schedule.course else None,
                "teacher": {
                    "id": schedule.teacher.id,
                    "code": schedule.teacher.code,
                    "name": schedule.teacher.name
                } if schedule.teacher else None,
                "class_": {
                    "id": schedule.class_.id,
                    "code": schedule.class_.code,
                    "name": schedule.class_.name
                } if schedule.class_ else None,
                "room": {
                    "id": schedule.room.id,
                    "code": schedule.room.code,
                    "name": schedule.room.name
                } if schedule.room else None
            }
            result.append(schedule_dict)
        except Exception as e:
            # 打印详细错误以便调试，避免整个接口崩溃
            log_operation(db, "排课管理", "ERROR", f"序列化排课数据失败 ID {schedule.id}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    return {
        "items": result,
        "total": total
    }

@router.get("/conflicts", response_model=List[ConflictInfo])
def get_all_conflicts(db: Session = Depends(get_db)):
    schedules = db.query(Schedule).all()
    all_conflicts = []
    
    for schedule in schedules:
        conflicts = check_conflicts(db, schedule, exclude_id=schedule.id)
        if conflicts:
            schedule.has_conflict = True
            schedule.conflict_reason = "; ".join([c.conflict_description for c in conflicts])
            all_conflicts.extend(conflicts)
        else:
            schedule.has_conflict = False
            schedule.conflict_reason = None
    
    db.commit()
    return all_conflicts

@router.post("/auto-schedule")
def auto_schedule(
    start_date: str,
    end_date: str,
    algorithm: str = "hybrid",
    room_type: str = Query(default="offline_physical", description="教室类型：offline_physical-线下物理, online_virtual-线上虚拟"),
    class_ids: Optional[str] = Query(None, description="班级ID列表，逗号分隔，为空则对所有班级排课"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    from routers.license import _check_premium_feature
    if not _check_premium_feature('smart_scheduling', db):
        raise HTTPException(status_code=403, detail="智能算法排课功能需要购买授权后才能使用")
    # 将日期字符串转换为 datetime 对象（不使用时区，避免时区转换问题）
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    # 解析班级ID
    selected_class_ids = None
    if class_ids and class_ids.strip():
        try:
            selected_class_ids = [int(cid.strip()) for cid in class_ids.split(',') if cid.strip()]
            log_operation(db, "课程安排", "智能算法排课", f"开始智能算法排课: start_date={start_date}, end_date={end_date}, algorithm={algorithm}, class_ids={selected_class_ids}", current_user.username, "INFO")
        except ValueError:
            raise HTTPException(status_code=400, detail="班级ID格式错误")
    else:
        log_operation(db, "课程安排", "智能算法排课", f"开始智能算法排课: start_date={start_date}, end_date={end_date}, algorithm={algorithm}, class_ids=所有班级", current_user.username, "INFO")
    
    # 只获取关联了在职教师的科目
    all_courses = db.query(Course).all()
    courses = []
    for course in all_courses:
        active_teachers = [t for t in course.teachers if t.is_active]
        if active_teachers:
            courses.append(course)

    teachers = db.query(Teacher).filter(Teacher.is_active == True).all()

    # 处理班级筛选
    if selected_class_ids:
        # 如果指定了班级，只使用这些班级
        all_classes = db.query(Class).filter(
            Class.id.in_(selected_class_ids),
            Class.is_active == True
        ).all()
    else:
        # 否则获取所有班级
        all_classes = db.query(Class).filter(Class.is_active == True).all()
    
    classes = []
    for class_ in all_classes:
        active_students = get_students_by_class(db, class_.id, is_active=True)
        if active_students:
            classes.append(class_)

    students = db.query(Student).filter(Student.is_active == True).all()
    rooms = db.query(Room).filter(Room.is_active == True).all()

    if not courses or not teachers or not classes or not students:
        log_operation(db, "课程安排", "错误", "资源不足，无法自动排课，须检查课程、教师、班级、学生", current_user.username, "Error")
        raise HTTPException(status_code=400, detail="资源不足，无法自动排课，须检查课程、教师、班级、学生")
    
    optimizer = ScheduleOptimizer(db)
    
    try:
        # 将班级ID传递给优化器
        optimized_schedules = optimizer.optimize_schedules(start_date_dt, end_date_dt, algorithm, selected_class_ids)
        
        schedules_preview = []
        conflicts_found = 0
        check_room = (room_type == "offline_physical")

        for schedule in optimized_schedules:
            log_operation(db, "课程安排", "检查排课冲突", f"检查排课冲突: schedule_id={schedule.id}, course_id={schedule.course_id}, teacher_id={schedule.teacher_id}, class_id={schedule.class_id}, room_id={schedule.room_id}, day_of_week={schedule.day_of_week}, start_time={schedule.start_time}, end_time={schedule.end_time}", current_user.username, "Debug")
            conflicts = check_conflicts(db, schedule, check_room_conflict=check_room)
            leave_conflicts = check_leave_conflicts(db, schedule)
            
            conflict_reason = None
            if conflicts or leave_conflicts:
                all_conflicts = [c.conflict_description for c in conflicts] + leave_conflicts
                conflict_reason = "; ".join(all_conflicts)
                conflicts_found += 1
            
            # 获取相关信息
            course = db.query(Course).filter(Course.id == schedule.course_id).first()
            teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
            class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
            room = db.query(Room).filter(Room.id == schedule.room_id).first() if room_type == "offline_physical" else None
            
            # 获取班级学员列表
            class_students = []
            if class_:
                class_students = get_students_by_class(db, class_.id, is_active=True)
            
            schedules_preview.append({
                "course_id": schedule.course_id,
                "course_name": course.name if course else "",
                "teacher_id": schedule.teacher_id,
                "teacher_name": teacher.name if teacher else "",
                "teacher_phone": teacher.contact_phone if teacher else "",
                "teacher_email": teacher.email if teacher else "",
                "class_id": schedule.class_id,
                "class_name": class_.name if class_ else "",
                "class_students": [{
                    "id": s.id,
                    "name": s.name,
                    "code": s.code,
                    "contact_phone": s.contact_phone,
                    "email": s.email
                } for s in class_students],
                "room_id": schedule.room_id if room_type == "offline_physical" else None,
                "room_name": room.name if room else "",
                "room_location": room.location if room else "",
                "room_capacity": room.capacity if room else 0,
                "room_facilities": room.facilities if room else "",
                "room_type": room_type,
                "meeting_link": None,
                "day_of_week": schedule.day_of_week,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "start_date": schedule.start_date.isoformat(),
                "end_date": schedule.end_date.isoformat(),
                "has_conflict": bool(conflicts or leave_conflicts),
                "conflict_reason": conflict_reason
            })
        
        log_operation(db, "课程安排", "预览", f"智能算法排课预览: 生成 {len(schedules_preview)} 个排课，共发现 {conflicts_found} 个冲突", current_user.username,"Debug")
        
        return {
            "message": "智能算法排课预览完成",
            "algorithm": algorithm,
            "schedules_preview": schedules_preview,
            "total_schedules": len(schedules_preview),
            "conflicts_found": conflicts_found
        }
    except Exception as e:
        log_operation(db, "课程安排", "错误", f"智能算法排课失败: {str(e)}", current_user.username,"Error")
        raise HTTPException(status_code=500, detail=f"智能算法排课失败: {str(e)}")

@router.post("/check-preview-conflict")
def check_preview_conflict(
    schedule_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    """检查预览排课数据的冲突状态（不保存到数据库）"""
    try:
        room_type = schedule_data.get("room_type", "offline_physical")
        room_id = schedule_data.get("room_id") if room_type == "offline_physical" else None

        schedule = Schedule(
            course_id=schedule_data["course_id"],
            teacher_id=schedule_data["teacher_id"],
            class_id=schedule_data["class_id"],
            room_id=room_id,
            day_of_week=schedule_data["day_of_week"],
            start_time=schedule_data["start_time"],
            end_time=schedule_data["end_time"],
            start_date=datetime.fromisoformat(schedule_data["start_date"]),
            end_date=datetime.fromisoformat(schedule_data["end_date"]),
            room_type=room_type,
            meeting_link=schedule_data.get("meeting_link"),
            schedule_type=schedule_data.get("schedule_type", "formal"),
        )

        check_room = room_type == "offline_physical"
        conflicts = check_conflicts(db, schedule, check_room_conflict=check_room)
        leave_conflicts = check_leave_conflicts(db, schedule)

        if conflicts is None:
            conflicts = []
        if leave_conflicts is None:
            leave_conflicts = []

        has_conflict = bool(conflicts or leave_conflicts)
        conflict_reason = None
        if has_conflict:
            all_conflicts = [c.conflict_description for c in conflicts] + leave_conflicts
            conflict_reason = "; ".join(all_conflicts)

        course = db.query(Course).filter(Course.id == schedule.course_id).first()
        teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
        class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
        room = db.query(Room).filter(Room.id == room_id).first() if room_id else None

        return {
            "has_conflict": has_conflict,
            "conflict_reason": conflict_reason,
            "course_name": course.name if course else "",
            "teacher_name": teacher.name if teacher else "",
            "teacher_phone": teacher.contact_phone if teacher else "",
            "teacher_email": teacher.email if teacher else "",
            "class_name": class_.name if class_ else "",
            "room_name": room.name if room else "",
            "room_location": room.location if room else "",
            "room_capacity": room.capacity if room else 0,
            "room_facilities": room.facilities if room else "",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"冲突检查失败: {str(e)}")

@router.post("/save-preview-schedules")
def save_preview_schedules(
    schedules: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """保存管理员预览后选择的排课"""
    try:
        schedules_created = 0
        conflicts_found = 0
        
        for schedule_data in schedules:
            room_type = schedule_data.get("room_type", "offline_physical")
            meeting_link = schedule_data.get("meeting_link")
            
            if room_type == "online_virtual" and not meeting_link:
                raise HTTPException(
                    status_code=400, 
                    detail=f"线上虚拟课程必须填写会议室链接"
                )
            
            room_id = schedule_data.get("room_id") if room_type == "offline_physical" else None
            
            schedule = Schedule(
                course_id=schedule_data["course_id"],
                teacher_id=schedule_data["teacher_id"],
                class_id=schedule_data["class_id"],
                room_id=room_id,
                day_of_week=schedule_data["day_of_week"],
                start_time=schedule_data["start_time"],
                end_time=schedule_data["end_time"],
                start_date=datetime.fromisoformat(schedule_data["start_date"]),
                end_date=datetime.fromisoformat(schedule_data["end_date"]),
                has_conflict=schedule_data.get("has_conflict", False),
                conflict_reason=schedule_data.get("conflict_reason"),
                room_type=room_type,
                meeting_link=meeting_link,
                schedule_type='formal'  # 自动排课默认为正式课
            )
            
            check_room = (room_type == "offline_physical")
            conflicts = check_conflicts(db, schedule, check_room_conflict=check_room)
            leave_conflicts = check_leave_conflicts(db, schedule)
            
            if conflicts is None:
                conflicts = []
            if leave_conflicts is None:
                leave_conflicts = []
            
            if conflicts or leave_conflicts:
                schedule.has_conflict = True
                all_conflicts = [c.conflict_description for c in conflicts] + leave_conflicts
                schedule.conflict_reason = "; ".join(all_conflicts)
                conflicts_found += 1
            else:
                schedule.has_conflict = False
            
            db.add(schedule)
            db.flush()
            schedules_created += 1
        
        db.commit()
        log_operation(db, "课程安排", "保存预览", f"保存预览排课: 成功创建 {schedules_created} 个排课，共发现 {conflicts_found} 个冲突", current_user.username,"Info")
        
        return {
            "message": "排课保存成功",
            "schedules_created": schedules_created,
            "conflicts_found": conflicts_found
        }
    except Exception as e:
        db.rollback()
        log_operation(db, "课程安排", "错误", f"保存预览排课失败: {str(e)}", current_user.username,"Error")
        raise HTTPException(status_code=500, detail=f"保存排课失败: {str(e)}")

# 创建课程安排时，检查节假日和相关资源的可用性
@router.post("", response_model=ScheduleSchema)
def create_schedule(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    course = db.query(Course).filter(Course.id == schedule.course_id).first()
    teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
    class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
    
    if not course or not teacher or not class_:
        log_operation(db, "课程安排", "错误", f"创建排课失败: 相关资源不存在 (course_id={schedule.course_id}, teacher_id={schedule.teacher_id}, class_id={schedule.class_id})", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="相关资源不存在")
    
    if schedule.room_type == "online_virtual" and not schedule.meeting_link:
        raise HTTPException(status_code=400, detail="线上虚拟课程必须填写会议室链接")
    
    room = None
    if schedule.room_type == "offline_physical":
        room = db.query(Room).filter(Room.id == schedule.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="教室不存在")
    
    if not course or not teacher or not class_:
        log_operation(db, "课程安排", "错误", f"创建排课失败: 相关资源不存在 (course_id={schedule.course_id}, teacher_id={schedule.teacher_id}, class_id={schedule.class_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="相关资源不存在")
    
    # 检查节假日
    is_date_holiday = is_holiday(schedule.start_date)
    if is_date_holiday:
        # 检查导师是否允许节假日排课
        if not teacher.allow_holiday_scheduling:
            raise HTTPException(
                status_code=400,
                detail=f"该日期为节假日，导师{teacher.name}不允许节假日排课"
            )
        
        # 检查班级的所有学生是否允许节假日排课
        students = get_students_by_class(db, class_.id, is_active=True)
        
        for student in students:
            if not student.allow_holiday_scheduling:
                raise HTTPException(
                    status_code=400,
                    detail=f"该日期为节假日，学员{student.name}不允许节假日排课"
                )

    # 检查班级是否有学生
    students = get_students_by_class(db, class_.id)
    if not students:
        log_operation(db, "课程安排", "错误", f"创建排课失败: 班级 {class_.name} 没有学生，无法排课", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="该班级没有学生，无法排课")
    
    # 检查班级的学生是否在该时间段可用
    # 传入 is_date_holiday 参数，如果是节假日且学员允许，则跳过星期几检查
    availability_result = check_class_availability_with_details(db, schedule.class_id, schedule.day_of_week, schedule.start_time, schedule.end_time, is_holiday=is_date_holiday)
    if not availability_result['available']:
        unavailable_students = availability_result['unavailable_students']
        student_names = [s['name'] for s in unavailable_students]
        reasons = []
        for s in unavailable_students:
            if not s['day_available']:
                reasons.append(f"{s['name']}（星期{schedule.day_of_week}不可用）")
            elif not s['time_available']:
                reasons.append(f"{s['name']}（时间段{schedule.start_time}-{schedule.end_time}不可用）")
        
        error_detail = f"以下学员在该时间段不可用：{'、'.join(reasons)}"
        log_operation(db, "课程安排", "错误", f"创建排课失败: {error_detail}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail=error_detail)
    
    # 检查是否已经存在完全相同的排课
    existing_schedule = db.query(Schedule).filter(
        Schedule.course_id == schedule.course_id,
        Schedule.teacher_id == schedule.teacher_id,
        Schedule.class_id == schedule.class_id,
        Schedule.day_of_week == schedule.day_of_week,
        Schedule.start_time == schedule.start_time,
        Schedule.end_time == schedule.end_time,
        Schedule.start_date == schedule.start_date,
        Schedule.end_date == schedule.end_date
    ).first()
    if existing_schedule:
        log_operation(db, "课程安排", "添加", "失败", "已经存在完全相同的排课")
        raise HTTPException(status_code=400, detail="已经存在完全相同的排课")
    
    # 检查导师是否在该时间段可用
    if not check_teacher_availability(db, schedule.teacher_id, schedule.day_of_week, schedule.start_time, schedule.end_time):
        log_operation(db, "课程安排", "错误", f"创建排课失败: 导师 {teacher.name} 在 {schedule.day_of_week} {schedule.start_time}-{schedule.end_time} 时间段不可用", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="该导师在该时间段不可用")

    if not check_teacher_course_availability(db, teacher.id, course.id):
        log_operation(db, "课程安排", "错误", f"创建排课失败: 导师 {teacher.name} 不教授科目 {course.name}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="该导师不能教授此科目")
    
    db_schedule = Schedule(
        course_id=schedule.course_id,
        teacher_id=schedule.teacher_id,
        class_id=schedule.class_id,
        room_id=schedule.room_id if schedule.room_type == "offline_physical" else None,
        day_of_week=schedule.day_of_week,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        content_feedback=schedule.content_feedback,
        room_type=schedule.room_type,
        meeting_link=schedule.meeting_link,
        schedule_type=schedule.schedule_type  # 使用传入的课程类型
    )
    db.add(db_schedule)
    db.flush()
    
    # 创建课程-学员关联记录：将当前班级的所有活跃学员添加到课程安排中
    active_students = get_students_by_class(db, class_.id, is_active=True)
    for student in active_students:
        association = schedule_student.insert().values(
            schedule_id=db_schedule.id,
            student_id=student.id,
            attendance_status='pending'
        )
        db.execute(association)
    
    db.commit()
    db.refresh(db_schedule)

    # 手动获取学员列表，确保序列化为字典（与 get_schedule 保持一致）
    stmt = select(
        schedule_student.c.student_id, 
        schedule_student.c.attendance_status,
        schedule_student.c.makeup_status,
        schedule_student.c.makeup_schedule_id,
        schedule_student.c.declined_reason
    ).where(
        schedule_student.c.schedule_id == db_schedule.id
    )
    student_result = db.execute(stmt)
    scheduled_students = []
    for row in student_result:
        student = db.query(Student).filter(Student.id == row[0]).first()
        if student:
            scheduled_students.append({
                "id": student.id,
                "name": student.name,
                "attendance_status": row[1] if row[1] else 'pending',
                "makeup_status": row[2],
                "makeup_schedule_id": row[3],
                "declined_reason": row[4]
            })
    
    # 构建符合 Schema 的字典
    schedule_dict = {
        "id": db_schedule.id,
        "course_id": db_schedule.course_id,
        "teacher_id": db_schedule.teacher_id,
        "class_id": db_schedule.class_id,
        "room_id": db_schedule.room_id,
        "day_of_week": db_schedule.day_of_week,
        "start_time": db_schedule.start_time,
        "end_time": db_schedule.end_time,
        "start_date": db_schedule.start_date.isoformat() if hasattr(db_schedule.start_date, 'isoformat') else str(db_schedule.start_date),
        "end_date": db_schedule.end_date.isoformat() if hasattr(db_schedule.end_date, 'isoformat') else str(db_schedule.end_date),
        "has_conflict": db_schedule.has_conflict,
        "conflict_reason": db_schedule.conflict_reason,
        "execution_status": db_schedule.execution_status,
        "content_feedback": db_schedule.content_feedback,
        "cancel_reason": db_schedule.cancel_reason,
        "postpone_reason": db_schedule.postpone_reason,
        "homework_regular": db_schedule.homework_regular,
        "homework_images": db_schedule.homework_images,
        "room_type": db_schedule.room_type,
        "meeting_link": db_schedule.meeting_link,
        "schedule_type": db_schedule.schedule_type,
        "scheduled_students": scheduled_students,
        "created_at": db_schedule.created_at.isoformat() if hasattr(db_schedule.created_at, 'isoformat') else str(db_schedule.created_at),
        "updated_at": db_schedule.updated_at.isoformat() if hasattr(db_schedule.updated_at, 'isoformat') else str(db_schedule.updated_at),
        "course": {
            "id": course.id,
            "code": course.code,
            "name": course.name
        } if course else None,
        "teacher": {
            "id": teacher.id,
            "code": teacher.code,
            "name": teacher.name
        } if teacher else None,
        "class_": {
            "id": class_.id,
            "code": class_.code,
            "name": class_.name
        } if class_ else None,
        "room": {
            "id": room.id,
            "code": room.code,
            "name": room.name
        } if room else None
    }

    if hasattr(schedule, 'send_notification') and schedule.send_notification:
        try:
            # 这里我们可以复用之前的通知函数，或者使用原有的微信通知逻辑
            # 为了保持“新建”通知的特殊性（包含学员名单），我们保留原有的微信通知逻辑
            # 但如果需要邮件通知，建议也在这里调用 email_notifier
            settings = db.query(Settings).first()
            # 1. 发送到导师微信群和班级微信群（如果配置了微信通知且已授权）
            if teacher and class_ and course:
                from routers.license import _check_premium_feature
                wechat_authorized = _check_premium_feature('wechat_notify', db)
                if wechat_authorized:
                    log_operation(db, "课程安排", "通知", "teacher/class/course都存在，微信通知已授权，准备发送微信通知", current_user.username, "DEBUG")
                    if settings:
                        wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
                        wechat_notifier.load_promotion_info(
                            website=settings.organization_website,
                            wechat_qr=settings.wechat_qrcode,
                            work_wechat_qr=settings.work_wechat_qrcode
                        )
                        log_operation(db, "课程安排", "通知", "已加载微信配置和推广信息", current_user.username, "DEBUG")
                    else:
                        log_operation(db, "课程安排", "通知", "settings为空，跳过微信配置加载", current_user.username, "DEBUG")
                    
                    enabled_classes = []
                    try:
                        if settings:
                            notif_config = json.loads(settings.notification_settings or "{}")
                            enabled_classes = notif_config.get('enabled_classes', [])
                            log_operation(db, "课程安排", "通知", f"成功解析notification_settings，enabled_classes: {enabled_classes}", current_user.username, "DEBUG")
                        else:
                            log_operation(db, "课程安排", "通知", "settings为空，使用空enabled_classes", current_user.username, "DEBUG")
                    except json.JSONDecodeError as e:
                        log_operation(db, "课程安排", "通知", f"解析notification_settings JSON失败: {e}, 使用空列表", current_user.username, "WARNING")
                        enabled_classes = []
                    except Exception as e:
                        log_operation(db, "课程安排", "通知", f"获取enabled_classes时发生其他错误: {e}, 使用空列表", current_user.username, "WARNING")
                        enabled_classes = []

                    log_operation(db, "课程安排", "通知", f"班级ID: {class_.id}, 班级名称: {class_.name}, 班级webhook: {class_.wechat_webhook}", current_user.username, "DEBUG")
                    log_operation(db, "课程安排", "通知", f"允许的班级列表: {enabled_classes}", current_user.username, "DEBUG")
                                
                    if schedule.room_type == "offline_physical":
                        room_info = f"**教室：** {room.name}" if room else ""
                    else:
                        room_info = f"**会议链接：** {schedule.meeting_link}" if schedule.meeting_link else ""
                    
                    schedule_type_text = '【试听课】' if schedule.schedule_type == 'trial' else '【正式课】'

                    content = f"""## 📅 {schedule_type_text}新课程安排提醒
> **日期：** {schedule.start_date}
> **时间：** {schedule.start_time} - {schedule.end_time}
> **科目：** {course.name}
> **学员：** {", ".join([student.name for student in students])}
> **导师：** {teacher.name}
> **班级：** {class_.name}
> {room_info}

敬请相关导师和学员知悉！"""
                    log_operation(db, "课程安排", "通知", f"准备发送微信通知，内容长度: {len(content)}", current_user.username, "DEBUG")
                    wechat_result = wechat_notifier.send_message_by_type("schedule_arrange", content, class_id=schedule.class_id, class_webhook=class_.wechat_webhook, is_markdown=True, enabled_classes=enabled_classes)
                    log_operation(db, "课程安排", "通知", f"微信发送结果: {wechat_result}", current_user.username, "DEBUG")
                    if not wechat_result.get("success"):
                        log_operation(db, "课程安排", "通知", wechat_result.get('message', '发送失败'), current_user.username, "WARNING")
                        log_operation(db, "课程安排", "新建课程通知", wechat_result.get('message', '发送失败'), current_user.username, "WARNING")
                else:
                    log_operation(db, "课程安排", "通知", "微信通知功能未授权，跳过微信通知", current_user.username, "WARNING")
            else:
                log_operation(db, "课程安排", "通知", "teacher/class/course不全，跳过微信通知", current_user.username, "DEBUG")
            
            # 2. 发送邮件通知（如果配置了邮件通知）
            log_operation(db, "课程安排", "通知", "准备处理邮件通知", current_user.username, "DEBUG")
            if settings:
                log_operation(db, "课程安排", "通知", "settings存在，加载邮件配置", current_user.username, "DEBUG")
                email_config = json.loads(settings.email_config or '{}')
                log_operation(db, "课程安排", "通知", f"邮件配置: {list(email_config.keys()) if email_config else '空'}", current_user.username, "DEBUG")
                email_notifier.load_config(settings.email_config or '{}', settings.site_name or '课程安排系统')
                email_notifier.load_promotion_info(
                    website=settings.organization_website,
                    wechat_qr=settings.wechat_qrcode,
                    work_wechat_qr=settings.work_wechat_qrcode
                )
                log_operation(db, "课程安排", "通知", "已加载邮件配置和推广信息", current_user.username, "DEBUG")
                
                schedule_type_text = '【试听课】' if schedule.schedule_type == 'trial' else '【正式课】'

                recipient_emails = []
                if teacher.email:
                    recipient_emails.append(teacher.email)
                for student in students:
                    if student.email:
                        recipient_emails.append(student.email)
                
                if recipient_emails and email_config.get('smtp_host'):
                    email_subject = f"【新课提醒】{course.name} - {class_.name} - {schedule.start_date}"
                    if schedule.room_type == "offline_physical":
                        email_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head><meta charset="UTF-8"><style>body{{font-family:Arial,sans-serif;line-height:1.6;color:#333;}}.container{{max-width:600px;margin:0 auto;padding:20px;}}.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;text-align:center;border-radius:10px 10px 0 0;}}.content{{background:#f9f9f9;padding:20px;border-radius:0 0 10px 10px;}}.info-item{{background:white;padding:15px;margin:10px 0;border-left:4px solid #667eea;border-radius:5px;}}.label{{color:#667eea;font-weight:bold;}}.value{{color:#333;margin-top:5px;}}</style></head>
                        <body>
                            <div class="container">
                                <div class="header"><h2>📅 {schedule_type_text}新课程安排提醒</h2></div>
                                <div class="content">
                                    <div class="info-item"><div class="label">日期</div><div class="value">{schedule.start_date}</div></div>
                                    <div class="info-item"><div class="label">时间</div><div class="value">{schedule.start_time} - {schedule.end_time}</div></div>
                                    <div class="info-item"><div class="label">班级</div><div class="value">{class_.name}</div></div>
                                    <div class="info-item"><div class="label">学员</div><div class="value">{", ".join([student.name for student in students])}</div></div>
                                    <div class="info-item"><div class="label">导师</div><div class="value">{teacher.name}</div></div>
                                    <div class="info-item"><div class="label">教室</div><div class="value">{room.name}</div></div>
                                    <div class="info-item"><div class="label">科目</div><div class="value">{course.name}</div></div>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                    else:
                        email_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head><meta charset="UTF-8"><style>body{{font-family:Arial,sans-serif;line-height:1.6;color:#333;}}.container{{max-width:600px;margin:0 auto;padding:20px;}}.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;text-align:center;border-radius:10px 10px 0 0;}}.content{{background:#f9f9f9;padding:20px;border-radius:0 0 10px 10px;}}.info-item{{background:white;padding:15px;margin:10px 0;border-left:4px solid #667eea;border-radius:5px;}}.label{{color:#667eea;font-weight:bold;}}.value{{color:#333;margin-top:5px;}}</style></head>
                        <body>
                            <div class="container">
                                <div class="header"><h2>📅 {schedule_type_text}新课程安排提醒</h2></div>
                                <div class="content">
                                    <div class="info-item"><div class="label">日期</div><div class="value">{schedule.start_date}</div></div>
                                    <div class="info-item"><div class="label">时间</div><div class="value">{schedule.start_time} - {schedule.end_time}</div></div>
                                    <div class="info-item"><div class="label">科目</div><div class="value">{course.name}</div></div>
                                    <div class="info-item"><div class="label">学员</div><div class="value">{", ".join([student.name for student in students])}</div></div>
                                    <div class="info-item"><div class="label">导师</div><div class="value">{teacher.name}</div></div>
                                    <div class="info-item"><div class="label">班级</div><div class="value">{class_.name}</div></div>
                                    <div class="info-item"><div class="label">会议室链接</div><div class="value">{schedule.meeting_link}</div></div>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                    log_operation(db, "课程安排", "通知", f"准备发送邮件，收件人: {recipient_emails}", current_user.username, "DEBUG")
                    result = email_notifier.send_email(recipient_emails, email_subject, email_html)
                    log_operation(db, "课程安排", "通知", f"邮件发送结果: {result}", current_user.username, "DEBUG")
            else:
                log_operation(db, "课程安排", "通知", "settings为空，跳过邮件通知", current_user.username, "DEBUG")
                
            log_operation(db, "课程安排", "通知", "通知发送流程完成", current_user.username, "DEBUG")
        except Exception as e:
            import traceback
            log_operation(db, "课程安排", "错误", f"发送新课提醒异常: {str(e)}", current_user.username, "ERROR")
            log_operation(db, "课程安排", "错误", f"发送新课提醒失败: {str(e)}", current_user.username,"Error")
    
    log_operation(db, "课程安排", "添加", f"成功创建排课: ID{db_schedule.id}", current_user.username,"Info")
    return schedule_dict

@router.get("/{schedule_id}", response_model=ScheduleSchema)
def get_schedule(schedule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_course_admin_user)):
    schedule = db.query(Schedule).options(
        joinedload(Schedule.course),
        joinedload(Schedule.teacher),
        joinedload(Schedule.class_),
        joinedload(Schedule.room)
    ).filter(Schedule.id == schedule_id).first()
    
    if not schedule:
        log_operation(db, "课程安排", "查询", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    # 手动获取学员列表，确保序列化为字典
    stmt = select(
        schedule_student.c.student_id, 
        schedule_student.c.attendance_status,
        schedule_student.c.makeup_status,
        schedule_student.c.makeup_schedule_id,
        schedule_student.c.declined_reason
    ).where(
        schedule_student.c.schedule_id == schedule_id
    )
    student_result = db.execute(stmt)
    scheduled_students = []
    for row in student_result:
        student = db.query(Student).filter(Student.id == row[0]).first()
        if student:
            scheduled_students.append({
                "id": student.id,
                "name": student.name,
                "attendance_status": row[1] if row[1] else 'pending',
                "makeup_status": row[2],
                "makeup_schedule_id": row[3],
                "declined_reason": row[4]
            })
    
    # 构建符合 Schema 的字典
    schedule_dict = {
        "id": schedule.id,
        "course_id": schedule.course_id,
        "teacher_id": schedule.teacher_id,
        "class_id": schedule.class_id,
        "room_id": schedule.room_id,
        "day_of_week": schedule.day_of_week,
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "start_date": schedule.start_date.isoformat() if hasattr(schedule.start_date, 'isoformat') else str(schedule.start_date),
        "end_date": schedule.end_date.isoformat() if hasattr(schedule.end_date, 'isoformat') else str(schedule.end_date),
        "has_conflict": schedule.has_conflict,
        "conflict_reason": schedule.conflict_reason,
        "execution_status": schedule.execution_status,
        "content_feedback": schedule.content_feedback,
        "cancel_reason": schedule.cancel_reason,
        "postpone_reason": schedule.postpone_reason,
        "homework_regular": schedule.homework_regular,
        "homework_images": schedule.homework_images,
        "room_type": schedule.room_type,
        "meeting_link": schedule.meeting_link,
        "schedule_type": schedule.schedule_type,
        "scheduled_students": scheduled_students,
        "created_at": schedule.created_at.isoformat() if hasattr(schedule.created_at, 'isoformat') else str(schedule.created_at),
        "updated_at": schedule.updated_at.isoformat() if hasattr(schedule.updated_at, 'isoformat') else str(schedule.updated_at),
        "course": {
            "id": schedule.course.id,
            "code": schedule.course.code,
            "name": schedule.course.name
        } if schedule.course else None,
        "teacher": {
            "id": schedule.teacher.id,
            "code": schedule.teacher.code,
            "name": schedule.teacher.name
        } if schedule.teacher else None,
        "class_": {
            "id": schedule.class_.id,
            "code": schedule.class_.code,
            "name": schedule.class_.name
        } if schedule.class_ else None,
        "room": {
            "id": schedule.room.id,
            "code": schedule.room.code,
            "name": schedule.room.name
        } if schedule.room else None
    }
    
    return schedule_dict

@router.put("/{schedule_id}", response_model=ScheduleSchema)
def update_schedule(
    schedule_id: int,
    schedule: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "更新", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    # 检查权限
    from routers.auth import can_edit_completed_schedule
    if not can_edit_completed_schedule(db, current_user, db_schedule.execution_status):
        log_operation(db, "课程安排", "更新", f"权限不足: 用户{current_user.username}尝试编辑{db_schedule.execution_status}状态的课程ID{schedule_id}", current_user.username, "WARNING")
        raise HTTPException(status_code=403, detail="您没有权限编辑该状态的课程安排")
    
    # 辅助函数：安全地处理日期，防止时区偏移导致日期变更
    def safe_parse_date(date_val):
        if date_val is None:
            return None
        # 如果已经是 date 对象，直接返回
        if isinstance(date_val, date):
            return date_val
        # 如果是 datetime 对象，提取 date
        if isinstance(date_val, datetime):
            return date_val.date()
        # 如果是字符串，尝试解析
        if isinstance(date_val, str):
            try:
                # 尝试解析 ISO 格式
                dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                return dt.date()
            except:
                try:
                    # 尝试解析 YYYY-MM-DD
                    return datetime.strptime(date_val, "%Y-%m-%d").date()
                except:
                    return None
        return None

    if schedule.course_id is not None:
        db_schedule.course_id = schedule.course_id
    if schedule.teacher_id is not None:
        db_schedule.teacher_id = schedule.teacher_id
    if schedule.course_id is not None:
        db_schedule.course_id = schedule.course_id
    if schedule.teacher_id is not None:
        db_schedule.teacher_id = schedule.teacher_id
    if schedule.class_id is not None:
        # 检查班级是否有学生
        class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
        if class_:
            students = get_students_by_class(db, class_.id)
            if not students:
                raise HTTPException(status_code=400, detail="该班级没有学生，无法排课")
        
        # 如果班级ID发生变化，需要更新学员关联记录
        old_class_id = db_schedule.class_id
        db_schedule.class_id = schedule.class_id
        
        # 只有当班级ID真正改变时才更新学员关联
        if old_class_id != schedule.class_id:
            # 删除旧的学员关联记录
            from sqlalchemy import delete as sql_delete
            delete_stmt = sql_delete(schedule_student).where(
                schedule_student.c.schedule_id == schedule_id
            )
            db.execute(delete_stmt)
            
            # 添加新班级的活跃学员记录
            new_class = db.query(Class).filter(Class.id == schedule.class_id).first()
            if new_class:
                active_students = get_students_by_class(db, new_class.id, is_active=True)
                for student in active_students:
                    association = schedule_student.insert().values(
                        schedule_id=schedule_id,
                        student_id=student.id,
                        attendance_status='pending'
                    )
                    db.execute(association)
                
                log_operation(db, "课程安排", "更新", f"课程安排ID{schedule_id}的班级从{old_class_id}变更为{schedule.class_id}，已同步更新学员关联记录", current_user.username, "INFO")
    if schedule.room_id is not None:
        db_schedule.room_id = schedule.room_id
    if schedule.room_id is not None:
        db_schedule.room_id = schedule.room_id
    if schedule.day_of_week is not None:
        db_schedule.day_of_week = schedule.day_of_week
    if schedule.start_time is not None:
        db_schedule.start_time = schedule.start_time
    if schedule.end_time is not None:
        db_schedule.end_time = schedule.end_time
    
    # 修复日期处理：使用安全解析函数
    if schedule.start_date is not None:
        db_schedule.start_date = safe_parse_date(schedule.start_date)
    if schedule.end_date is not None:
        db_schedule.end_date = safe_parse_date(schedule.end_date)
    if schedule.content_feedback is not None:
        db_schedule.content_feedback = schedule.content_feedback
    if schedule.homework_regular is not None:
        db_schedule.homework_regular = schedule.homework_regular
    if schedule.homework_images is not None:
        db_schedule.homework_images = schedule.homework_images
    if schedule.cancel_reason is not None:
        db_schedule.cancel_reason = schedule.cancel_reason
    if schedule.postpone_reason is not None:
        db_schedule.postpone_reason = schedule.postpone_reason
    if schedule.schedule_type is not None:
        db_schedule.schedule_type = schedule.schedule_type
    
    # 检查执行状态是否变为完训
    old_execution_status = db_schedule.execution_status
    if schedule.execution_status is not None:
        db_schedule.execution_status = schedule.execution_status

    # 添加假期检查逻辑
    if schedule.start_date is not None or schedule.end_date is not None:
        # 获取更新后的日期范围
        check_start_date = safe_parse_date(schedule.start_date) if schedule.start_date is not None else db_schedule.start_date
        check_end_date = safe_parse_date(schedule.end_date) if schedule.end_date is not None else db_schedule.end_date
        
        # 检查整个日期范围内的每一天
        from datetime import timedelta
        current_date = check_start_date
        while current_date <= check_end_date:
            is_date_holiday = is_holiday(current_date)
            if is_date_holiday:
                # 获取导师信息
                teacher = db.query(Teacher).filter(Teacher.id == db_schedule.teacher_id).first()
                if teacher and not teacher.allow_holiday_scheduling:
                    log_operation(db, "课程安排", "更新", f"更新失败: 日期 {current_date} 为节假日，导师不允许节假日排课", current_user.username, "Error")
                    raise HTTPException(
                        status_code=400,
                        detail=f"日期 {current_date} 为节假日，导师不允许节假日排课"
                    )
                
                # 检查班级的所有学生是否允许节假日排课
                class_ = db.query(Class).filter(Class.id == db_schedule.class_id).first()
                if class_:
                    students = get_students_by_class(db, class_.id, is_active=True)
                    for student in students:
                        if not student.allow_holiday_scheduling:
                            log_operation(db, "课程安排", "更新", f"更新失败: 日期 {current_date} 为节假日，学员 {student.name} 不允许节假日排课", current_user.username, "Error")
                            raise HTTPException(
                                status_code=400,
                                detail=f"日期 {current_date} 为节假日，学员 {student.name} 不允许节假日排课"
                            )
            
            current_date += timedelta(days=1)

    # 如果日期或班级发生了变化，重新检查可用性（传入节假日状态）
    if (schedule.start_date is not None or schedule.day_of_week is not None or 
        schedule.start_time is not None or schedule.end_time is not None or 
        schedule.class_id is not None):
        
        check_start_date = safe_parse_date(schedule.start_date) if schedule.start_date is not None else db_schedule.start_date
        check_day_of_week = schedule.day_of_week if schedule.day_of_week is not None else db_schedule.day_of_week
        check_start_time = schedule.start_time if schedule.start_time is not None else db_schedule.start_time
        check_end_time = schedule.end_time if schedule.end_time is not None else db_schedule.end_time
        check_class_id = schedule.class_id if schedule.class_id is not None else db_schedule.class_id

        is_date_holiday = is_holiday(check_start_date)
        availability_result = check_class_availability_with_details(db, check_class_id, check_day_of_week, check_start_time, check_end_time, is_holiday=is_date_holiday)
        
        if not availability_result['available']:
            unavailable_students = availability_result['unavailable_students']
            reasons = []
            for s in unavailable_students:
                if not s['day_available']:
                    reasons.append(f"{s['name']}（星期{check_day_of_week}不可用）")
                elif not s['time_available']:
                    reasons.append(f"{s['name']}（时间段{check_start_time}-{check_end_time}不可用）")
            
            error_detail = f"以下学员在该时间段不可用：{'、'.join(reasons)}"
            log_operation(db, "课程安排", "更新", f"更新失败: {error_detail}", current_user.username, "Error")
            raise HTTPException(status_code=400, detail=error_detail)
    
    db.commit()
    # 如果执行状态从非完训变为完训，消耗课时
    if old_execution_status != "completed" and db_schedule.execution_status == "completed":
        try:
            from routers.fees import consume_hours_with_attendance
            
            # 如果没有学员记录，先创建默认的学员记录（全部出席）
            query = select(schedule_student.c.id).where(
                schedule_student.c.schedule_id == schedule_id
            )
            result = db.execute(query).fetchone()
            
            if not result:
                # 获取班级的活跃学员并创建记录
                class_ = db.query(Class).filter(Class.id == db_schedule.class_id).first()
                if class_:
                    active_students = get_students_by_class(db, class_.id, is_active=True)
                    for student in active_students:
                        association = schedule_student.insert().values(
                            schedule_id=schedule_id,
                            student_id=student.id,
                            attendance_status='present'
                        )
                        db.execute(association)
                    db.commit()
            
            consume_hours_with_attendance(schedule_id, db, current_user)
        except Exception as e:
            log_operation(db, "课程安排", "更新", f"消耗课时失败: {str(e)}", current_user.username,"Error")

    db.refresh(db_schedule)
    
    # 手动获取学员列表，确保序列化为字典（与get_schedule保持一致）
    stmt = select(
        schedule_student.c.student_id, 
        schedule_student.c.attendance_status,
        schedule_student.c.makeup_status,
        schedule_student.c.makeup_schedule_id,
        schedule_student.c.declined_reason
    ).where(
        schedule_student.c.schedule_id == schedule_id
    )
    student_result = db.execute(stmt)
    scheduled_students = []
    for row in student_result:
        student = db.query(Student).filter(Student.id == row[0]).first()
        if student:
            scheduled_students.append({
                "id": student.id,
                "name": student.name,
                "attendance_status": row[1] if row[1] else 'pending',
                "makeup_status": row[2],
                "makeup_schedule_id": row[3],
                "declined_reason": row[4]
            })
    
    # 构建符合 Schema 的字典返回
    schedule_dict = {
        "id": db_schedule.id,
        "course_id": db_schedule.course_id,
        "teacher_id": db_schedule.teacher_id,
        "class_id": db_schedule.class_id,
        "room_id": db_schedule.room_id,
        "day_of_week": db_schedule.day_of_week,
        "start_time": db_schedule.start_time,
        "end_time": db_schedule.end_time,
        "start_date": db_schedule.start_date.isoformat() if hasattr(db_schedule.start_date, 'isoformat') else str(db_schedule.start_date),
        "end_date": db_schedule.end_date.isoformat() if hasattr(db_schedule.end_date, 'isoformat') else str(db_schedule.end_date),
        "has_conflict": db_schedule.has_conflict,
        "conflict_reason": db_schedule.conflict_reason,
        "execution_status": db_schedule.execution_status,
        "content_feedback": db_schedule.content_feedback,
        "cancel_reason": db_schedule.cancel_reason,
        "postpone_reason": db_schedule.postpone_reason,
        "homework_regular": db_schedule.homework_regular,
        "homework_images": db_schedule.homework_images,
        "room_type": db_schedule.room_type,
        "meeting_link": db_schedule.meeting_link,
        "schedule_type": db_schedule.schedule_type,
        "scheduled_students": scheduled_students,
        "created_at": db_schedule.created_at.isoformat() if hasattr(db_schedule.created_at, 'isoformat') else str(db_schedule.created_at),
        "updated_at": db_schedule.updated_at.isoformat() if hasattr(db_schedule.updated_at, 'isoformat') else str(db_schedule.updated_at),
        "course": {
            "id": db_schedule.course.id,
            "code": db_schedule.course.code,
            "name": db_schedule.course.name
        } if db_schedule.course else None,
        "teacher": {
            "id": db_schedule.teacher.id,
            "code": db_schedule.teacher.code,
            "name": db_schedule.teacher.name
        } if db_schedule.teacher else None,
        "class_": {
            "id": db_schedule.class_.id,
            "code": db_schedule.class_.code,
            "name": db_schedule.class_.name
        } if db_schedule.class_ else None,
        "room": {
            "id": db_schedule.room.id,
            "code": db_schedule.room.code,
            "name": db_schedule.room.name
        } if db_schedule.room else None
    }
    
    # 发送编辑课程安排通知
    if hasattr(schedule, 'send_notification') and schedule.send_notification:
        try:
            settings = db.query(Settings).first()
            if settings:
                teacher = db.query(Teacher).filter(Teacher.id == db_schedule.teacher_id).first()
                class_ = db.query(Class).filter(Class.id == db_schedule.class_id).first()
                course = db.query(Course).filter(Course.id == db_schedule.course_id).first()
                
                if teacher and class_ and course:
                    students = get_students_by_class(db, db_schedule.class_id, is_active=True)
                    
                    # 构建微信通知内容
                    room = db.query(Room).filter(Room.id == db_schedule.room_id).first()
                    if db_schedule.room_type == "offline_physical":
                        room_info = f"**教室：** {room.name}" if room else ""
                    else:
                        room_info = f"**会议链接：** {db_schedule.meeting_link}" if db_schedule.meeting_link else ""
                    
                    schedule_type_text = '【试听课】' if db_schedule.schedule_type == 'trial' else '【正式课】'

                    content = f"""## 📝 {schedule_type_text}课程安排变更提醒
    > **日期：** {db_schedule.start_date}
    > **时间：** {db_schedule.start_time} - {db_schedule.end_time}
    > **科目：** {course.name}
    > **学员：** {", ".join([student.name for student in students])}
    > **导师：** {teacher.name}
    > **班级：** {class_.name}
    > {room_info}

    敬请相关导师和学员知悉！"""
                    
                    # 1. 发送微信通知(同时支持发送到导师微信群和班级微信群)（如果配置了微信通知且已授权）
                    from routers.license import _check_premium_feature
                    wechat_authorized = _check_premium_feature('wechat_notify', db)
                    if wechat_authorized:
                        wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
                        wechat_notifier.load_promotion_info(
                            website=settings.organization_website,
                            wechat_qr=settings.wechat_qrcode,
                            work_wechat_qr=settings.work_wechat_qrcode
                        )

                        # 获取允许的班级列表
                        enabled_classes = []
                        try:
                            notif_config = json.loads(settings.notification_settings or "{}")
                            enabled_classes = notif_config.get('enabled_classes', [])
                            log_operation(db, "课程安排", "通知", f"更新课程 - 成功解析notification_settings，enabled_classes: {enabled_classes}", current_user.username, "DEBUG")
                        except json.JSONDecodeError as e:
                            log_operation(db, "课程安排", "通知", f"更新课程 - 解析notification_settings JSON失败: {e}, 使用空列表", current_user.username, "WARNING")
                            enabled_classes = []
                        except Exception as e:
                            log_operation(db, "课程安排", "通知", f"更新课程 - 获取enabled_classes时发生其他错误: {e}, 使用空列表", current_user.username, "WARNING")
                            enabled_classes = []

                        wechat_result = wechat_notifier.send_message_by_type("schedule_arrange", content, class_id=db_schedule.class_id, class_webhook=class_.wechat_webhook, is_markdown=True, enabled_classes=enabled_classes)
                        if not wechat_result.get("success"):
                            log_operation(db, "课程安排", "通知", wechat_result.get('message', '发送失败'), current_user.username, "WARNING")
                            log_operation(db, "课程安排", "编辑课程通知", wechat_result.get('message', '发送失败'), current_user.username, "WARNING")
                    else:
                        log_operation(db, "课程安排", "通知", "微信通知功能未授权，跳过微信通知", current_user.username, "WARNING")
                                        
                    # 2. 发送邮件通知（如果配置了邮件通知）
                    email_config = json.loads(settings.email_config or '{}')
                    email_notifier.load_config(settings.email_config or '{}', settings.site_name or '课程安排系统')
                    email_notifier.load_promotion_info(
                        website=settings.organization_website,
                        wechat_qr=settings.wechat_qrcode,
                        work_wechat_qr=settings.work_wechat_qrcode
                    )
                    
                    recipient_emails = []
                    if teacher.email:
                        recipient_emails.append(teacher.email)
                    for student in students:
                        if student.email:
                            recipient_emails.append(student.email)
                    
                    if recipient_emails and email_config.get('smtp_host'):
                        email_subject = f"【课程变更】{course.name} - {class_.name} - {db_schedule.start_date}"
                        if db_schedule.room_type == "offline_physical":
                            email_html = f"""
                            <!DOCTYPE html>
                            <html>
                            <head><meta charset="UTF-8"><style>body{{font-family:Arial,sans-serif;line-height:1.6;color:#333;}}.container{{max-width:600px;margin:0 auto;padding:20px;}}.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;text-align:center;border-radius:10px 10px 0 0;}}.content{{background:#f9f9f9;padding:20px;border-radius:0 0 10px 10px;}}.info-item{{background:white;padding:15px;margin:10px 0;border-left:4px solid #667eea;border-radius:5px;}}.label{{color:#667eea;font-weight:bold;}}.value{{color:#333;margin-top:5px;}}</style></head>
                            <body>
                                <div class="container">
                                    <div class="header"><h2>📝 {schedule_type_text}课程安排变更提醒</h2></div>
                                    <div class="content">
                                        <div class="info-item"><div class="label">日期</div><div class="value">{db_schedule.start_date}</div></div>
                                        <div class="info-item"><div class="label">时间</div><div class="value">{db_schedule.start_time} - {db_schedule.end_time}</div></div>
                                        <div class="info-item"><div class="label">班级</div><div class="value">{class_.name}</div></div>
                                        <div class="info-item"><div class="label">学员</div><div class="value">{", ".join([student.name for student in students])}</div></div>
                                        <div class="info-item"><div class="label">导师</div><div class="value">{teacher.name}</div></div>
                                        <div class="info-item"><div class="label">教室</div><div class="value">{room.name}</div></div>
                                        <div class="info-item"><div class="label">科目</div><div class="value">{course.name}</div></div>
                                    </div>
                                </div>
                            </body>
                            </html>
                            """
                        else:
                            email_html = f"""
                            <!DOCTYPE html>
                            <html>
                            <head><meta charset="UTF-8"><style>body{{font-family:Arial,sans-serif;line-height:1.6;color:#333;}}.container{{max-width:600px;margin:0 auto;padding:20px;}}.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;text-align:center;border-radius:10px 10px 0 0;}}.content{{background:#f9f9f9;padding:20px;border-radius:0 0 10px 10px;}}.info-item{{background:white;padding:15px;margin:10px 0;border-left:4px solid #667eea;border-radius:5px;}}.label{{color:#667eea;font-weight:bold;}}.value{{color:#333;margin-top:5px;}}</style></head>
                            <body>
                                <div class="container">
                                    <div class="header"><h2>📝 {schedule_type_text}课程安排变更提醒</h2></div>
                                    <div class="content">
                                        <div class="info-item"><div class="label">日期</div><div class="value">{db_schedule.start_date}</div></div>
                                        <div class="info-item"><div class="label">时间</div><div class="value">{db_schedule.start_time} - {db_schedule.end_time}</div></div>
                                        <div class="info-item"><div class="label">科目</div><div class="value">{course.name}</div></div>
                                        <div class="info-item"><div class="label">学员</div><div class="value">{", ".join([student.name for student in students])}</div></div>
                                        <div class="info-item"><div class="label">导师</div><div class="value">{teacher.name}</div></div>
                                        <div class="info-item"><div class="label">会议室链接</div><div class="value">{schedule.meeting_link}</div></div>
                                    </div>
                                </div>
                            </body>
                            </html>
                            """
                        email_notifier.send_email(recipient_emails, email_subject, email_html)
        except Exception as e:
            log_operation(db, "课程安排", "错误", f"发送课程变更通知失败: {str(e)}", current_user.username,"Error")

    log_operation(db, "课程安排", "更新", f"成功更新课程安排: ID{db_schedule.id}", current_user.username,"Info")
    return schedule_dict

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "删除", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    from routers.auth import can_delete_completed_schedule
    if not can_delete_completed_schedule(db, current_user, db_schedule.execution_status):
        log_operation(db, "课程安排", "删除", f"权限不足: 用户{current_user.username}尝试删除{db_schedule.execution_status}状态的课程ID{schedule_id}", current_user.username, "WARNING")
        raise HTTPException(status_code=403, detail="您没有权限删除该状态的课程安排")
    
    # 删除关联的学员记录
    from sqlalchemy import delete as sql_delete
    stmt = sql_delete(schedule_student).where(schedule_student.c.schedule_id == schedule_id)
    db.execute(stmt)
    
    # 获取课程信息用于通知（在删除前保存）
    teacher = db.query(Teacher).filter(Teacher.id == db_schedule.teacher_id).first()
    class_ = db.query(Class).filter(Class.id == db_schedule.class_id).first()
    course = db.query(Course).filter(Course.id == db_schedule.course_id).first()
    room = db.query(Room).filter(Room.id == db_schedule.room_id).first()
    students = get_students_by_class(db, db_schedule.class_id, is_active=True)
    
    # 保存课程信息用于通知
    schedule_info = {
        'id': db_schedule.id,
        'start_date': db_schedule.start_date,
        'start_time': db_schedule.start_time,
        'end_time': db_schedule.end_time,
        'room_type': db_schedule.room_type,
        'meeting_link': db_schedule.meeting_link,
        'schedule_type': db_schedule.schedule_type
    }
    db.delete(db_schedule)
    log_operation(db, "课程安排", "删除", f"成功删除课程安排: ID{schedule_info['id']}", current_user.username,"WARNING")
    db.commit()
    
    # 发送微信通知
    if teacher and class_ and course:
        try:
            settings = db.query(Settings).first()
            if settings:
                from routers.license import _check_premium_feature
                wechat_authorized = _check_premium_feature('wechat_notify', db)
                if wechat_authorized:
                    wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
                    wechat_notifier.load_promotion_info(
                        website=settings.organization_website,
                        wechat_qr=settings.wechat_qrcode,
                        work_wechat_qr=settings.work_wechat_qrcode
                    )

                    enabled_classes = []
                    try:
                        notif_config = json.loads(settings.notification_settings or "{}")
                        enabled_classes = notif_config.get('enabled_classes', [])
                    except (json.JSONDecodeError, Exception):
                        enabled_classes = []

                    if schedule_info['room_type'] == "offline_physical":
                        room_info = f"**教室：** {room.name}" if room else ""
                    else:
                        room_info = f"**会议链接：** {schedule_info['meeting_link']}" if schedule_info['meeting_link'] else ""
                    
                    schedule_type_text = '【试听课】' if schedule_info['schedule_type'] == 'trial' else '【正式课】'
                    
                    content = f"""## 🗑️ {schedule_type_text}课程删除提醒
> **日期：** {schedule_info['start_date']}
> **时间：** {schedule_info['start_time']} - {schedule_info['end_time']}
> **科目：** {course.name}
> **学员：** {", ".join([student.name for student in students])}
> **导师：** {teacher.name}
> **班级：** {class_.name}
> {room_info}
 
敬请相关导师和学员知悉！"""
                    
                    wechat_result = wechat_notifier.send_message_by_type("schedule_arrange", content, class_id=class_.id, class_webhook=class_.wechat_webhook, is_markdown=True, enabled_classes=enabled_classes)
                    if not wechat_result.get("success"):
                        log_operation(db, "课程安排", "通知", wechat_result.get('message', '发送失败'), current_user.username, "WARNING")
                    else:
                        log_operation(db, "课程安排", "通知", "删除课程通知发送成功", current_user.username, "INFO")
                else:
                    log_operation(db, "课程安排", "通知", "微信通知功能未授权，跳过微信通知", current_user.username, "WARNING")
        except Exception as e:
            log_operation(db, "课程安排", "通知", f"删除课程通知发送失败: {str(e)}", current_user.username, "ERROR")
            log_operation(db, "课程安排", "删除课程通知", f"删除课程通知发送失败: {str(e)}", current_user.username, "ERROR")
    
    
    # 构建班级学生缓存
    all_classes = db.query(Class).filter(Class.is_active == True).all()
    class_students_cache = {}
    for class_ in all_classes:
        active_students = get_students_by_class(db, class_.id, is_active=True)
        class_students_cache[class_.id] = {s.id for s in active_students}
    
    # 重新检查所有课程的冲突状态
    all_schedules = db.query(Schedule).all()
    for schedule in all_schedules:
        # 排除当前正在检查的课程本身，避免自我冲突
        conflicts = check_conflicts(db, schedule, exclude_id=schedule.id, class_students_cache=class_students_cache)
        leave_conflicts = check_leave_conflicts(db, schedule)
        
        if conflicts or leave_conflicts:
            schedule.has_conflict = True
            all_conflicts = [c.conflict_description for c in conflicts] + leave_conflicts
            schedule.conflict_reason = "; ".join(all_conflicts)
        else:
            schedule.has_conflict = False
            schedule.conflict_reason = None
    
    db.commit()
    return {"message": "删除成功"}

@router.post("/{schedule_id}/complete")
def complete_schedule(
    schedule_id: int,
    feedback: ScheduleCompleteFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "完训", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    # 检查冲突
    conflicts = check_conflicts(db, db_schedule, exclude_id=schedule_id)
    if conflicts:
        log_operation(db, "课程安排", "完训", f"课程安排存在冲突，无法完训: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="课程安排存在冲突，无法完训")
    
    # 试听课不需要强制反馈
    is_trial = db_schedule.schedule_type == "trial"
    if not is_trial and not feedback.content_feedback:
        log_operation(db, "课程安排", "完训", f"正式课必须填写反馈: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="正式课必须填写课程反馈")
    
    db_schedule.execution_status = "completed"
    db_schedule.content_feedback = feedback.content_feedback
    
    # 获取班级的活跃学员
    class_ = db.query(Class).filter(Class.id == db_schedule.class_id).first()
    if not class_:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    active_students = get_students_by_class(db, class_.id, is_active=True)
    
    # 更新学员出勤状态
    if feedback.student_attendance:
        for student_id, status in feedback.student_attendance.items():
            if status not in ['present', 'absent', 'leave']:
                log_operation(db, "课程安排", "完训", f"无效的出勤状态: {status}", current_user.username,"Error")
                raise HTTPException(status_code=400, detail=f"无效的出勤状态: {status}")
            
            # 获取缺勤原因
            absence_reason = None
            if feedback.absence_reasons and student_id in feedback.absence_reasons:
                absence_reason = feedback.absence_reasons[student_id]
            
            # 如果学员状态为请假，自动在假日管理中创建请假记录
            if status == 'leave':
                student = db.query(Student).filter(Student.id == student_id).first()
                if student:
                    # 将Date类型转换为DateTime类型用于创建请假记录
                    from datetime import datetime as dt_datetime
                    start_datetime = dt_datetime.combine(db_schedule.start_date, dt_datetime.min.time())
                    end_datetime = dt_datetime.combine(db_schedule.end_date, dt_datetime.max.time())
                    
                    # 检查是否已存在该学员在此日期范围的请假记录
                    existing_leave = db.query(Leave).filter(
                        Leave.leave_type == "student",
                        Leave.student_id == student_id,
                        Leave.start_date <= end_datetime,
                        Leave.end_date >= start_datetime
                    ).first()
                    
                    if not existing_leave:
                        # 创建新的请假记录，使用DateTime类型
                        new_leave = Leave(
                            leave_type="student",
                            student_id=student_id,
                            start_date=start_datetime,
                            end_date=end_datetime,
                            reason=f"课程请假 - {db_schedule.start_date} {db_schedule.start_time}-{db_schedule.end_time}"
                        )
                        db.add(new_leave)
                        log_operation(db, "假日管理", "自动创建请假", f"为学员 {student.name} 创建请假记录: {db_schedule.start_date} 至 {db_schedule.end_date}", current_user.username, "INFO")
            
            # 更新或创建学员出勤记录
            from sqlalchemy import update as sql_update
            stmt = sql_update(schedule_student).where(
                (schedule_student.c.schedule_id == schedule_id) & 
                (schedule_student.c.student_id == student_id)
            ).values(
                attendance_status=status,
                absence_reason=absence_reason
            )
            result = db.execute(stmt)
            
            if result.rowcount == 0:
                # 如果记录不存在，创建新记录
                association = schedule_student.insert().values(
                    schedule_id=schedule_id,
                    student_id=student_id,
                    attendance_status=status,
                    absence_reason=absence_reason
                )
                db.execute(association)
    else:
        # 如果没有提供出勤状态，先检测学员是否有请假记录，然后设置默认状态
        for student in active_students:
            # 将Date类型转换为DateTime类型用于查询
            from datetime import datetime as dt_datetime
            start_datetime = dt_datetime.combine(db_schedule.start_date, dt_datetime.min.time())
            end_datetime = dt_datetime.combine(db_schedule.end_date, dt_datetime.max.time())
            
            # 检查学员是否有对应日期的请假记录
            student_leave = db.query(Leave).filter(
                Leave.leave_type == "student",
                Leave.student_id == student.id,
                Leave.start_date <= end_datetime,
                Leave.end_date >= start_datetime
            ).first()
            
            # 根据是否有请假记录设置默认状态
            default_status = 'leave' if student_leave else 'present'
            
            # 更新或创建学员出勤记录
            from sqlalchemy import update as sql_update
            stmt = sql_update(schedule_student).where(
                (schedule_student.c.schedule_id == schedule_id) & 
                (schedule_student.c.student_id == student.id)
            ).values(
                attendance_status=default_status,
                absence_reason='已有请假记录' if student_leave else None
            )
            result = db.execute(stmt)
            
            if result.rowcount == 0:
                # 如果记录不存在，创建新记录
                association = schedule_student.insert().values(
                    schedule_id=schedule_id,
                    student_id=student.id,
                    attendance_status=default_status,
                    absence_reason='已有请假记录' if student_leave else None
                )
                db.execute(association)
    
    db.commit()
    
    # 只有正式课才消耗课时
    if db_schedule.schedule_type == "formal":
        try:
            from routers.fees import consume_hours_with_attendance
            consume_hours_with_attendance(schedule_id, db, current_user)
        except Exception as e:
            log_operation(db, "课程安排", "完训", f"消耗课时失败: {str(e)}", current_user.username,"Error")
    
    db.refresh(db_schedule)
    if hasattr(feedback, 'send_notification') and feedback.send_notification:
        try:
            send_schedule_status_notification(db, db_schedule, "completed")
        except Exception as e:
            log_operation(db, "课程安排", "完训", f"发送通知失败: {str(e)}", current_user.username,"Error")
    else:
        # 定时通知：根据设置中的时间安排延迟通知
        try:
            from utils.remainder import scheduler
            from datetime import datetime, timedelta
            
            settings = db.query(Settings).first()
            if settings:
                notif_settings = json.loads(settings.notification_settings or "{}")
                # 获取提醒时间配置（早上7点或晚上7点）
                # 这里简化处理，实际需要根据配置计算下次提醒时间
                current_time = datetime.now()
                # 假设配置的是早上7点提醒
                reminder_time = current_time.replace(hour=7, minute=0, second=0, microsecond=0)
                if current_time.hour >= 7:
                    # 如果已经过了7点，则设置为明早7点
                    reminder_time += timedelta(days=1)
                
                job_id = f"complete_notification_{db_schedule.id}"
                scheduler.add_job(
                    lambda: send_schedule_status_notification(db, db_schedule, "completed"),
                    'date',
                    run_date=reminder_time,
                    id=job_id,
                    replace_existing=True
                )
                log_operation(db, "课程安排", "完训", f"已安排定时通知，将在{reminder_time}发送", current_user.username,"INFO")
        except Exception as e:
            log_operation(db, "课程安排", "完训", f"安排定时通知失败: {str(e)}", current_user.username,"Error")
    return db_schedule

@router.post("/{schedule_id}/postpone")
def postpone_schedule(
    schedule_id: int,
    postpone_data: SchedulePostpone,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """延期：调整日期和时间，生成新的课程安排，将原课程的执行状态设置为 postponed"""
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "延期", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    if db_schedule.has_conflict:
        log_operation(db, "课程安排", "延期", f"课程安排存在冲突，无法延期: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="课程安排存在冲突，无法延期")
    
    # 更新原课程的执行状态为延期
    db_schedule.execution_status = "postponed"
    db_schedule.postpone_reason = postpone_data.postpone_reason
    db.commit()
    log_operation(db, "课程安排", "延期", f"课程安排被延期: ID{db_schedule.id} - {postpone_data.postpone_reason}", current_user.username,"INFO")
    
    # 创建新的课程安排
    new_schedule = Schedule(
        course_id=db_schedule.course_id,
        teacher_id=db_schedule.teacher_id,
        class_id=db_schedule.class_id,
        room_id=db_schedule.room_id,
        day_of_week=postpone_data.start_date.weekday() + 1 if postpone_data.start_date.weekday() != 6 else 7,
        start_time=postpone_data.start_time,
        end_time=postpone_data.end_time,
        start_date=postpone_data.start_date,
        end_date=postpone_data.end_date,
        content_feedback=db_schedule.content_feedback,
        schedule_type=db_schedule.schedule_type  # 继承原课程的类型
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    # 检查新课程安排的冲突状态
    conflicts = check_conflicts(db, new_schedule)
    leave_conflicts = check_leave_conflicts(db, new_schedule)
    
    if conflicts or leave_conflicts:
        new_schedule.has_conflict = True
        all_conflicts = [c.conflict_description for c in conflicts] + leave_conflicts
        new_schedule.conflict_reason = "; ".join(all_conflicts)
    else:
        new_schedule.has_conflict = False
    
    db.commit()

    if hasattr(postpone_data, 'send_notification') and postpone_data.send_notification:
        try:
            send_schedule_status_notification(db, db_schedule, "postponed")
        except Exception as e:
            log_operation(db, "课程安排", "延期", f"发送通知失败: {str(e)}", current_user.username,"Error")
    else:
        # 定时通知：根据设置中的时间安排延迟通知
        try:
            from utils.remainder import scheduler
            from datetime import datetime, timedelta
            
            settings = db.query(Settings).first()
            if settings:
                notif_settings = json.loads(settings.notification_settings or "{}")
                # 获取提醒时间配置（早上7点或晚上7点）
                # 这里简化处理，实际需要根据配置计算下次提醒时间
                current_time = datetime.now()
                # 假设配置的是早上7点提醒
                reminder_time = current_time.replace(hour=7, minute=0, second=0, microsecond=0)
                if current_time.hour >= 7:
                    # 如果已经过了7点，则设置为明早7点
                    reminder_time += timedelta(days=1)
                
                job_id = f"complete_notification_{db_schedule.id}"
                scheduler.add_job(
                    lambda: send_schedule_status_notification(db, db_schedule, "postponed"),
                    'date',
                    run_date=reminder_time,
                    id=job_id,
                    replace_existing=True
                )
                log_operation(db, "课程安排", "延期", f"已安排定时通知，将在{reminder_time}发送", current_user.username,"INFO")
        except Exception as e:
            log_operation(db, "课程安排", "延期", f"安排定时通知失败: {str(e)}", current_user.username,"Error")

    log_operation(db, "课程安排", "延期", f"因延期创建新课程安排: ID{new_schedule.id} - {postpone_data.postpone_reason}", current_user.username,"INFO")
    return {"original_schedule": db_schedule, "new_schedule": new_schedule}

@router.post("/{schedule_id}/cancel")
def cancel_schedule(
    schedule_id: int,
    cancel_data: ScheduleCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """取消：将执行状态设置为 cancelled"""
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "取消", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    if db_schedule.has_conflict:
        log_operation(db, "课程安排", "取消", f"课程安排存在冲突，无法取消: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="课程安排存在冲突，无法取消")
    
    db_schedule.execution_status = "cancelled"
    db_schedule.cancel_reason = cancel_data.cancel_reason
    db.commit()

    if hasattr(cancel_data, 'send_notification') and cancel_data.send_notification:
        try:
            send_schedule_status_notification(db, db_schedule, "cancelled")
        except Exception as e:
            log_operation(db, "课程安排", "取消", f"发送通知失败: {str(e)}", current_user.username,"Error")
    else:
        # 定时通知：根据设置中的时间安排延迟通知
        try:
            from utils.remainder import scheduler
            from datetime import datetime, timedelta
            
            settings = db.query(Settings).first()
            if settings:
                notif_settings = json.loads(settings.notification_settings or "{}")
                # 获取提醒时间配置（早上7点或晚上7点）
                # 这里简化处理，实际需要根据配置计算下次提醒时间
                current_time = datetime.now()
                # 假设配置的是早上7点提醒
                reminder_time = current_time.replace(hour=7, minute=0, second=0, microsecond=0)
                if current_time.hour >= 7:
                    # 如果已经过了7点，则设置为明早7点
                    reminder_time += timedelta(days=1)
                
                job_id = f"complete_notification_{db_schedule.id}"
                scheduler.add_job(
                    lambda: send_schedule_status_notification(db, db_schedule, "cancelled"),
                    'date',
                    run_date=reminder_time,
                    id=job_id,
                    replace_existing=True
                )
                log_operation(db, "课程安排", "取消", f"已安排定时通知，将在{reminder_time}发送", current_user.username,"INFO")
        except Exception as e:
            log_operation(db, "课程安排", "取消", f"安排定时通知失败: {str(e)}", current_user.username,"Error")

    log_operation(db, "课程安排", "取消", f"课程安排被取消: ID{db_schedule.id} - {cancel_data.cancel_reason}", current_user.username,"WARNING")
    db.refresh(db_schedule)
    return db_schedule

@router.put("/{schedule_id}/attendance")
def update_schedule_attendance(
    schedule_id: int,
    attendance_data: ScheduleAttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """更新课程安排的学员出勤状态"""
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "更新出勤状态", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    if db_schedule.execution_status != "completed":
        log_operation(db, "课程安排", "更新出勤状态", f"只有完训的课程才能更新出勤状态: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="只有完训的课程才能更新出勤状态")
    
    # 更新学员出勤状态
    for student_id, status in attendance_data.student_attendance.items():
        if status not in ['present', 'absent', 'leave']:
            log_operation(db, "课程安排", "更新出勤状态", f"无效的出勤状态: {status}", current_user.username,"Error")
            raise HTTPException(status_code=400, detail=f"无效的出勤状态: {status}")
        
        from sqlalchemy import update as sql_update
        absence_reason = None
        if attendance_data.absence_reasons and student_id in attendance_data.absence_reasons:
            absence_reason = attendance_data.absence_reasons[student_id]
        
        stmt = sql_update(schedule_student).where(
            (schedule_student.c.schedule_id == schedule_id) & 
            (schedule_student.c.student_id == student_id)
        ).values(
            attendance_status=status,
            absence_reason=absence_reason
        )
        result = db.execute(stmt)
        
        if result.rowcount == 0:
            log_operation(db, "课程安排", "更新出勤状态", f"学员ID {student_id} 不在该课程安排中", current_user.username,"Error")
            raise HTTPException(status_code=404, detail=f"学员ID {student_id} 不在该课程安排中")
    
    db.commit()
    log_operation(db, "课程安排", "更新出勤状态", f"课程安排ID {schedule_id} 的学员出勤状态已更新", current_user.username,"INFO")
    
    # 重新计算课时消耗
    try:
        from routers.fees import recalculate_consumed_hours
        recalculate_consumed_hours(schedule_id, db, current_user)
    except Exception as e:
        log_operation(db, "课程安排", "更新出勤状态", f"重新计算课时失败: {str(e)}", current_user.username,"Error")
    
    return {"message": "出勤状态更新成功"}

@router.post("/{schedule_id}/makeup")
async def makeup_schedule(
    schedule_id: int,
    makeup_data: ScheduleMakeup,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """学员补课：为选定的学员创建新的课程安排"""
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "补课", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    if db_schedule.execution_status != "completed":
        log_operation(db, "课程安排", "补课", f"课程安排未完训，无法补课: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="只有完训的课程才能安排补课")
    
    # 检查学员是否属于原课程的班级
    original_class = db.query(Class).filter(Class.id == db_schedule.class_id).first()
    if not original_class:
        log_operation(db, "课程安排", "补课", f"原课程的班级不存在: ID{db_schedule.class_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="原课程的班级不存在")
    
    original_class_students = [s for s in original_class.students if s.is_active]
    original_class_student_ids = {s.id for s in original_class_students}
    
    for student_id in makeup_data.student_ids:
        if student_id not in original_class_student_ids:
            log_operation(db, "课程安排", "补课", f"学员ID {student_id} 不属于原课程的班级: ID{db_schedule.class_id}", current_user.username,"Error")
            raise HTTPException(status_code=400, detail=f"学员ID {student_id} 不属于原课程的班级")
    
    # 创建补课课程安排
    new_schedule = Schedule(
        course_id=db_schedule.course_id,
        teacher_id=db_schedule.teacher_id,
        class_id=db_schedule.class_id,
        room_id=makeup_data.room_id,
        day_of_week=makeup_data.start_date.weekday() + 1 if makeup_data.start_date.weekday() != 6 else 7,
        start_time=makeup_data.start_time,
        end_time=makeup_data.end_time,
        start_date=makeup_data.start_date,
        end_date=makeup_data.end_date,
        content_feedback=db_schedule.content_feedback,
        schedule_type=db_schedule.schedule_type
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    # 为补课课程添加学员
    for student_id in makeup_data.student_ids:
        association = schedule_student.insert().values(
            schedule_id=new_schedule.id,
            student_id=student_id,
            attendance_status='present'
        )
        db.execute(association)
    
    # 更新原课程安排中学员的补课状态
    for student_id in makeup_data.student_ids:
        db.execute(
            schedule_student.update()
            .where((schedule_student.c.schedule_id == schedule_id) & (schedule_student.c.student_id == student_id))
            .values(makeup_status='completed', makeup_schedule_id=new_schedule.id)
        )
    
    db.commit()
    
    # 检查新课程安排的冲突状态
    conflicts = check_conflicts(db, new_schedule)
    leave_conflicts = check_leave_conflicts(db, new_schedule)
    
    if conflicts or leave_conflicts:
        new_schedule.has_conflict = True
        all_conflicts = [c.conflict_description for c in conflicts] + leave_conflicts
        new_schedule.conflict_reason = "; ".join(all_conflicts)
    else:
        new_schedule.has_conflict = False
    
    db.commit()
    log_operation(db, "课程安排", "补课", f"课程安排产生学员补课: ID{db_schedule.id} - {len(makeup_data.student_ids)}人", current_user.username,"INFO")
    
    return new_schedule

@router.post("/{schedule_id}/decline-makeup")
async def decline_makeup(
    schedule_id: int,
    decline_data: ScheduleDeclineMakeup,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """学员不补课：记录不补课原因并更新状态"""
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "不补课", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    if db_schedule.execution_status != "completed":
        log_operation(db, "课程安排", "不补课", f"课程安排未完训，无法操作: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="只有完训的课程才能操作")
    
    # 更新学员的不补课状态
    for student_id in decline_data.student_ids:
        db.execute(
            schedule_student.update()
            .where((schedule_student.c.schedule_id == schedule_id) & (schedule_student.c.student_id == student_id))
            .values(makeup_status='declined', declined_reason=decline_data.declined_reason)
        )
    
    db.commit()
    log_operation(db, "课程安排", "不补课", f"课程安排学员不补课: ID{db_schedule.id} - {len(decline_data.student_ids)}人", current_user.username,"INFO")
    
    return {"message": "不补课记录成功"}

@router.get("/{schedule_id}/conflicts")
async def get_schedule_conflicts(schedule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_course_admin_user)):
    """获取与指定课程冲突的课程列表"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        log_operation(db, "课程安排", "查询冲突", f"课程安排不存在: ID{schedule_id}", current_user.username,"Error")
        raise HTTPException(status_code=404, detail="课程安排不存在")
    
    conflicts = []
    
    # 查找同一时间段内的所有课程
    all_schedules = db.query(Schedule).filter(
        Schedule.id != schedule_id,
        Schedule.start_date <= schedule.end_date,
        Schedule.end_date >= schedule.start_date,
        Schedule.day_of_week == schedule.day_of_week,
        Schedule.start_time < schedule.end_time,
        Schedule.end_time > schedule.start_time
    ).all()
    
    for s in all_schedules:
        # 检查是否冲突（同一教室、同一导师或同一班级）
        if (s.room_id == schedule.room_id or 
            s.teacher_id == schedule.teacher_id or 
            s.class_id == schedule.class_id):
            conflicts.append(s)
    
    return conflicts

@router.delete("/clear-all")
def clear_all_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin_user)
):
    """清空所有课程安排 - 仅超级管理员可操作"""
    if current_user.role != 'super_admin':
        log_operation(db, "课程安排", "清空失败", f"权限不足: 用户{current_user.username}尝试清空所有课程安排", current_user.username, "WARNING")
        raise HTTPException(status_code=403, detail="仅超级管理员可以清空所有课程安排")
    
    db.query(Schedule).delete()
    db.commit()
    log_operation(db, "课程安排", "清空", "已清空所有课程安排", current_user.username,"WARNING")
    return {"message": "已清空所有课程安排"}

@router.get("/export/{format}")
async def export_schedules(
    format: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    teacher_ids: Optional[str] = None,
    class_id: Optional[int] = None,
    class_ids: Optional[str] = None,
    course_id: Optional[int] = None,
    course_ids: Optional[str] = None,
    room_id: Optional[int] = None,
    room_ids: Optional[str] = None,
    day_of_week: Optional[int] = None,
    days_of_week: Optional[str] = None,
    has_conflict: Optional[bool] = None,
    execution_status: Optional[str] = None,
    lang: str = "zh-CN",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """导出课程安排"""
    query = db.query(Schedule)
    
    # 如果指定了ID，直接按ID过滤（最高优先级）
    if id:
        query = query.filter(Schedule.id == id)
        
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Schedule.end_date >= start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Schedule.start_date <= end_date_obj)
        except ValueError:
            pass
    
    if teacher_id:
        query = query.filter(Schedule.teacher_id == teacher_id)
    
    if teacher_ids:
        try:
            ids = [int(id.strip()) for id in teacher_ids.split(',')]
            query = query.filter(Schedule.teacher_id.in_(ids))
        except ValueError:
            pass
    
    if class_id:
        query = query.filter(Schedule.class_id == class_id)
    
    if class_ids:
        try:
            ids = [int(id.strip()) for id in class_ids.split(',')]
            query = query.filter(Schedule.class_id.in_(ids))
        except ValueError:
            pass
    
    if course_id:
        query = query.filter(Schedule.course_id == course_id)
    
    if course_ids:
        try:
            ids = [int(id.strip()) for id in course_ids.split(',')]
            query = query.filter(Schedule.course_id.in_(ids))
        except ValueError:
            pass
    
    if room_id:
        query = query.filter(Schedule.room_id == room_id)
    
    if room_ids:
        try:
            ids = [int(id.strip()) for id in room_ids.split(',')]
            query = query.filter(Schedule.room_id.in_(ids))
        except ValueError:
            pass
    
    if day_of_week:
        query = query.filter(Schedule.day_of_week == day_of_week)
    
    if days_of_week:
        try:
            days = [int(day.strip()) for day in days_of_week.split(',')]
            query = query.filter(Schedule.day_of_week.in_(days))
        except ValueError:
            pass
    
    if has_conflict is not None:
        query = query.filter(Schedule.has_conflict == has_conflict)
    
    if execution_status and execution_status.strip():
        query = query.filter(Schedule.execution_status == execution_status)
    
    schedules = query.order_by(Schedule.start_date, Schedule.start_time).all()
    
    if format == 'excel':
        log_operation(db, "课程安排", "导出", f"导出课程安排:格式 {format}, 共 {len(schedules)} 条记录", current_user.username,"Info")
        return export_to_excel(schedules, db, lang)
    elif format == 'csv':
        log_operation(db, "课程安排", "导出", f"导出课程安排:格式 {format}, 共 {len(schedules)} 条记录", current_user.username,"Info")
        return export_to_csv(schedules, db, lang)
    elif format == 'pdf':
        log_operation(db, "课程安排", "导出", f"导出课程安排:格式 {format}, 共 {len(schedules)} 条记录", current_user.username,"Info")
        return export_to_pdf(schedules, db, lang)
    else:
        log_operation(db, "课程安排", "导出", f"导出课程安排失败: 不支持的格式 {format}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail="不支持的导出格式")

def export_to_excel(schedules: List[Schedule], db: Session, lang: str = "zh-CN"):
    """导出为Excel格式"""
    _t_map = {
        "zh-CN": {
            "sheet": "课程安排",
            "headers": ['ID', '科目', '导师', '班级', '课程类型', '教室类型', '教室', '会议室链接', '星期', '开始时间', '结束时间', '开始日期', '结束日期', '冲突状态', '执行状态', '课程反馈', '延期原因', '取消原因'],
            "trial": "试听课", "formal": "正式课",
            "offline": "线下物理", "online": "线上虚拟",
            "conflict": "冲突", "no_conflict": "无冲突",
            "completed": "完训", "postponed": "延期", "cancelled": "取消", "pending": "待执行",
        },
        "en": {
            "sheet": "Course Schedules",
            "headers": ['ID', 'Course', 'Teacher', 'Class', 'Schedule Type', 'Room Type', 'Room', 'Meeting Link', 'Day of Week', 'Start Time', 'End Time', 'Start Date', 'End Date', 'Conflict', 'Status', 'Feedback', 'Postpone Reason', 'Cancel Reason'],
            "trial": "Trial", "formal": "Formal",
            "offline": "Offline", "online": "Online",
            "conflict": "Conflict", "no_conflict": "No Conflict",
            "completed": "Completed", "postponed": "Postponed", "cancelled": "Cancelled", "pending": "Pending",
        },
    }
    t = _t_map.get(lang, _t_map["zh-CN"])

    wb = Workbook()
    ws = wb.active
    ws.title = t["sheet"]
    
    headers = t["headers"]
    ws.append(headers)
    
    courses = {c.id: c.name for c in db.query(Course).all()}
    teacher_names = {tc.id: tc.name for tc in db.query(Teacher).all()}
    class_names = {cl.id: cl.name for cl in db.query(Class).all()}
    rooms = {r.id: r.name for r in db.query(Room).all()}
    
    for schedule in schedules:
        room_type_text = t['offline'] if schedule.room_type == 'offline_physical' else t['online']
        schedule_type_text = t['trial'] if schedule.schedule_type == 'trial' else t['formal']
        room_name = rooms.get(schedule.room_id, '') if schedule.room_type == 'offline_physical' else ''
        meeting_link = schedule.meeting_link or ''
        
        exec_status = t.get(schedule.execution_status, t['pending'])
        
        row = [
            schedule.id,
            courses.get(schedule.course_id, ''),
            teacher_names.get(schedule.teacher_id, ''),
            class_names.get(schedule.class_id, ''),
            schedule_type_text,
            room_type_text,
            room_name,
            meeting_link,
            schedule.day_of_week,
            schedule.start_time,
            schedule.end_time,
            schedule.start_date.strftime('%Y-%m-%d'),
            schedule.end_date.strftime('%Y-%m-%d'),
            t['conflict'] if schedule.has_conflict else t['no_conflict'],
            exec_status,
            schedule.content_feedback or '',
            schedule.postpone_reason or '',
            schedule.cancel_reason or ''
        ]
        ws.append(row)
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=course_schedules_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'}
    )

def export_to_csv(schedules: List[Schedule], db: Session, lang: str = "zh-CN"):
    """导出为CSV格式"""
    import io
    
    _t_map = {
        "zh-CN": {
            "headers": ['ID', '科目', '导师', '班级', '课程类型', '教室类型', '教室', '会议室链接', '星期', '开始时间', '结束时间', '开始日期', '结束日期', '冲突状态', '执行状态', '课程反馈', '延期原因', '取消原因'],
            "trial": "试听课", "formal": "正式课",
            "offline": "线下物理", "online": "线上虚拟",
            "conflict": "冲突", "no_conflict": "无冲突",
            "completed": "完训", "postponed": "延期", "cancelled": "取消", "pending": "待执行",
        },
        "en": {
            "headers": ['ID', 'Course', 'Teacher', 'Class', 'Schedule Type', 'Room Type', 'Room', 'Meeting Link', 'Day of Week', 'Start Time', 'End Time', 'Start Date', 'End Date', 'Conflict', 'Status', 'Feedback', 'Postpone Reason', 'Cancel Reason'],
            "trial": "Trial", "formal": "Formal",
            "offline": "Offline", "online": "Online",
            "conflict": "Conflict", "no_conflict": "No Conflict",
            "completed": "Completed", "postponed": "Postponed", "cancelled": "Cancelled", "pending": "Pending",
        },
    }
    t = _t_map.get(lang, _t_map["zh-CN"])

    output = io.StringIO()
    writer = csv.writer(output)
    
    courses = {c.id: c.name for c in db.query(Course).all()}
    teacher_names = {tc.id: tc.name for tc in db.query(Teacher).all()}
    class_names = {cl.id: cl.name for cl in db.query(Class).all()}
    rooms = {r.id: r.name for r in db.query(Room).all()}
    
    headers = t["headers"]
    writer.writerow(headers)
    
    for schedule in schedules:
        room_type_text = t['offline'] if schedule.room_type == 'offline_physical' else t['online']
        schedule_type_text = t['trial'] if schedule.schedule_type == 'trial' else t['formal']
        room_name = rooms.get(schedule.room_id, '') if schedule.room_type == 'offline_physical' else ''
        meeting_link = schedule.meeting_link or ''
        exec_status = t.get(schedule.execution_status, t['pending'])
        
        row = [
            schedule.id,
            courses.get(schedule.course_id, ''),
            teacher_names.get(schedule.teacher_id, ''),
            class_names.get(schedule.class_id, ''),
            schedule_type_text,
            room_type_text,
            room_name,
            meeting_link,
            schedule.day_of_week,
            schedule.start_time,
            schedule.end_time,
            schedule.start_date.strftime('%Y-%m-%d'),
            schedule.end_date.strftime('%Y-%m-%d'),
            t['conflict'] if schedule.has_conflict else t['no_conflict'],
            exec_status,
            schedule.content_feedback or '',
            schedule.postpone_reason or '',
            schedule.cancel_reason or ''
        ]
        writer.writerow(row)
    
    # 获取字符串内容并转换为字节，添加BOM
    output.seek(0)
    content = output.getvalue().encode('utf-8-sig')
    
    return Response(
        content=content,
        media_type='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=course_schedules_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

def export_to_pdf(schedules: List[Schedule], db: Session, lang: str = "zh-CN"):
    """导出为PDF格式"""
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.units import inch, mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    import os
    import math
    
    _t_map = {
        "zh-CN": {
            "title": "课程安排表",
            "headers": ['ID', '科目', '导师', '班级', '教室类型', '教室', '会议室链接', '星期', '开始时间', '结束时间', '开始日期', '结束日期', '冲突状态', '执行状态', '课程类型', '课程反馈', '延期原因', '取消原因'],
            "trial": "试听课", "formal": "正式课",
            "offline": "线下物理", "online": "线上虚拟",
            "conflict": "冲突", "no_conflict": "无",
            "completed": "完训", "postponed": "延期", "cancelled": "取消", "pending": "待执行",
        },
        "en": {
            "title": "Course Schedule",
            "headers": ['ID', 'Course', 'Teacher', 'Class', 'Room Type', 'Room', 'Meeting Link', 'Day', 'Start', 'End', 'Start Date', 'End Date', 'Conflict', 'Status', 'Type', 'Feedback', 'Postpone Reason', 'Cancel Reason'],
            "trial": "Trial", "formal": "Formal",
            "offline": "Offline", "online": "Online",
            "conflict": "Conflict", "no_conflict": "No",
            "completed": "Completed", "postponed": "Postponed", "cancelled": "Cancelled", "pending": "Pending",
        },
    }
    t = _t_map.get(lang, _t_map["zh-CN"])

    output = BytesIO()
    c = canvas.Canvas(output, pagesize=landscape(A4))
    
    page_width, page_height = landscape(A4)
    margin_left = 0.5 * inch
    margin_right = 0.3 * inch
    margin_top = 0.5 * inch
    margin_bottom = 0.3 * inch
    
    usable_width = page_width - margin_left - margin_right
    usable_height = page_height - margin_top - margin_bottom
    
    use_chinese = False
    data_font = 'Helvetica'
    title_font = 'Helvetica'
    
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
    ]
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                if font_path.endswith('.ttc'):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                data_font = 'ChineseFont'
                title_font = 'ChineseFont'
                use_chinese = True
                log_operation(db, "导出", "DEBUG", f"成功加载字体: {font_path}")
                break
        except Exception as e:
            log_operation(db, "导出", "WARNING", f"字体加载失败 {font_path}: {e}")
    
    c.setFont(title_font, 14)
    title_text = t["title"]
    title_width = c.stringWidth(title_text, title_font, 14)
    c.drawString((page_width - title_width) / 2, page_height - margin_top - 20, title_text)
    
    headers = t["headers"]
    
    courses = {c.id: c.name for c in db.query(Course).all()}
    teacher_names = {tc.id: tc.name for tc in db.query(Teacher).all()}
    class_names = {cl.id: cl.name for cl in db.query(Class).all()}
    rooms = {r.id: r.name for r in db.query(Room).all()}
    
    # 2. & 4. 优化列宽和位置，防止“班级”盖住“教室”，并为长文本留出空间
    # 重新分配列宽（单位：英寸，自适应）
    col_widths = [
        0.28,  # ID
        0.70,  # 科目
        0.50,  # 导师
        0.65,  # 班级
        0.55,  # 教室类型
        0.70,  # 教室
        0.90,  # 会议室链接
        0.32,  # 星期
        0.42,  # 开始时间
        0.42,  # 结束时间
        0.65,  # 开始日期
        0.65,  # 结束日期
        0.45,  # 冲突状态
        0.45,  # 执行状态
        0.45,  # 课程类型
        0.90,  # 课程反馈
        0.90,  # 延期原因
        0.90   # 取消原因
    ]
    
    # 计算每列的起始 X 坐标（转换为点）
    x_positions = [margin_left]
    for w in col_widths[:-1]:
        x_positions.append(x_positions[-1] + w * inch)
    
    # 起始 Y 坐标（标题下方）
    y_position = page_height - margin_top - 50
    
    # 绘制表头
    c.setFont(data_font, 8)
    header_height = 20
    for i, header in enumerate(headers):
        c.drawString(x_positions[i], y_position, header)
    
    # 绘制表头下划线
    c.line(margin_left, y_position - 5, page_width - margin_right, y_position - 5)
    
    # 准备数据行
    y_position -= 25
    
    # 定义段落样式
    styles = getSampleStyleSheet()
    if use_chinese:
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=data_font,
            fontSize=7,
            leading=9,
            alignment=TA_LEFT,
            wordWrap='CJK',
            spaceBefore=0,
            spaceAfter=0
        )
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontName=data_font,
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
            wordWrap='CJK'
        )
    else:
        normal_style = styles['Normal']
        header_style = styles['Normal']
    
    for schedule in schedules:
        room_type_text = t['offline'] if schedule.room_type == 'offline_physical' else t['online']
        room_name = rooms.get(schedule.room_id, '') if schedule.room_type == 'offline_physical' else ''
        meeting_link = schedule.meeting_link or ''
        schedule_type_text = t['formal'] if schedule.schedule_type == 'formal' else t['trial']
        exec_status = t.get(schedule.execution_status, t['pending'])
        
        row_data = [
            str(schedule.id),
            courses.get(schedule.course_id, ''),
            teacher_names.get(schedule.teacher_id, ''),
            class_names.get(schedule.class_id, ''),
            room_type_text,
            room_name,
            meeting_link,
            str(schedule.day_of_week),
            schedule.start_time,
            schedule.end_time,
            schedule.start_date.strftime('%Y-%m-%d') if hasattr(schedule.start_date, 'strftime') else str(schedule.start_date),
            schedule.end_date.strftime('%Y-%m-%d') if hasattr(schedule.end_date, 'strftime') else str(schedule.end_date),
            t['conflict'] if schedule.has_conflict else t['no_conflict'],
            exec_status,
            schedule_type_text,
            schedule.content_feedback or '',
            schedule.postpone_reason or '',
            schedule.cancel_reason or ''
        ]
        
        # 计算当前行需要的最大高度（用于自动调整行高）
        max_height_in_row = 0
        paragraph_objects = []
        
        for i, cell_content in enumerate(row_data):
            # 对于需要换行的列 (3=班级, 6=教室, 15=课程反馈, 16=延期原因, 17=取消原因)
            if i in [3, 6, 15, 16, 17] and cell_content:
                available_width = (x_positions[i + 1] - x_positions[i]) - 4
                
                # 创建 Paragraph 对象
                para = Paragraph(cell_content, normal_style)
                w, h = para.wrap(available_width, 100 * inch)
                
                if h > max_height_in_row:
                    max_height_in_row = h
                
                paragraph_objects.append((i, para, h))
            else:
                # 普通文本的高度固定
                if 12 > max_height_in_row:
                    max_height_in_row = 12
        
        # 3. 自动调整行高：根据内容最高的那个单元格决定这一行占多少空间
        row_height = max(max_height_in_row + 8, 15)
        
        # 检查是否需要分页
        if y_position - row_height < margin_bottom:
            c.showPage()
            # 新页面重置
            c.setFont(title_font, 14)
            title_width = c.stringWidth(title_text, title_font, 14)
            c.drawString((page_width - title_width) / 2, page_height - margin_top - 20, title_text)
            
            y_position = page_height - margin_top - 50
            c.setFont(data_font, 8)
            for i, header in enumerate(headers):
                c.drawString(x_positions[i], y_position, header)
            c.line(margin_left, y_position - 5, page_width - margin_right, y_position - 5)
            y_position -= 25
        
        # 绘制行内容
        for i, cell_content in enumerate(row_data):
            # 检查是否是已创建的 Paragraph 对象
            para_info = next((p for p in paragraph_objects if p[0] == i), None)
            
            if para_info:
                # 绘制 Paragraph
                _, para, h = para_info
                # 计算垂直对齐位置（居中）
                vertical_offset = (row_height - h) / 2
                para.drawOn(c, x_positions[i], y_position - row_height + vertical_offset)
            else:
                # 普通文本直接绘制
                c.setFont(data_font, 7)
                # 计算垂直对齐位置（居中）
                vertical_offset = (row_height - 10) / 2
                c.drawString(x_positions[i], y_position - row_height + vertical_offset, cell_content)
        
        y_position -= row_height
    c.save()
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=course_schedules_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'}
    )

@router.post("/import")
async def import_schedules(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入课程安排"""
    try:
        import pandas as pd

        # 读取上传的文件内容
        content = await file.read()
        
        #使用BytesIO包装bytes对象，然后使用pandas读取Excel文件
        df = pd.read_excel(BytesIO(content))

        # 初始化计数器
        imported_count = 0
        skipped_count = 0
        failed_rows = []
        
        # 检查必需的列是否存在
        required_columns = ['科目', '导师', '班级', '教室类型', '时间', '日期']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"导入文件缺少必需的列: {', '.join(missing_columns)}"
            )
        
        for idx, row in df.iterrows():
            try:
                course = db.query(Course).filter(Course.name == row['科目']).first()
                teacher = db.query(Teacher).filter(Teacher.name == row['导师']).first()
                class_ = db.query(Class).filter(Class.name == row['班级']).first()
                room_type_value = str(row.get('教室类型', '线下物理')).strip()
                room_type = 'offline_physical' if room_type_value in ['线下物理', 'offline_physical'] else 'online_virtual'
                
                room = None
                if room_type == 'offline_physical':
                    room_name = str(row.get('教室', '')).strip()
                    if not room_name:
                        skipped_count += 1
                        failed_rows.append({
                            'row': idx + 2,
                            'reason': f"线下物理课程必须指定教室"
                        })
                        continue
                    room = db.query(Room).filter(Room.name == room_name).first()
                    if not room:
                        skipped_count += 1
                        failed_rows.append({
                            'row': idx + 2,
                            'reason': f"找不到对应的教室: {room_name}"
                        })
                        continue
                
                meeting_link = None
                if room_type == 'online_virtual':
                    meeting_link_value = str(row.get('会议室链接', '')).strip()
                    if not meeting_link_value:
                        skipped_count += 1
                        failed_rows.append({
                            'row': idx + 2,
                            'reason': f"线上虚拟课程必须填写会议室链接"
                        })
                        continue
                    meeting_link = meeting_link_value
                
                if not all([course, teacher, class_]):
                    skipped_count += 1
                    failed_rows.append({
                        'row': idx + 2,
                        'reason': f"找不到对应的资源: 科目={row['科目']}, 导师={row['导师']}, 班级={row['班级']}"
                    })
                    continue
                
                # 解析时间段，格式为 "开始时间-结束时间"，如 "09:00-10:30"
                time_range = str(row['时间']).split('-')
                if len(time_range) != 2:
                    skipped_count += 1
                    failed_rows.append({
                        'row': idx + 2,
                        'reason': f"时间段格式错误: {row['时间']}"
                    })
                    continue
                
                start_time = time_range[0].strip()
                end_time = time_range[1].strip()
                
                # 解析日期，格式为 "YYYY-MM-DD"，如 "2024-01-01"
                try:
                    date_str = str(row['日期']).strip()
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, TypeError):
                    skipped_count += 1
                    failed_rows.append({
                        'row': idx + 2,
                        'reason': f"日期格式错误: {row['日期']}"
                    })
                    continue
                
                # 自动计算周几（0=周一，6=周日）
                day_of_week = date_obj.weekday()
                
                # 日期同时作为开始日期和结束日期
                schedule = Schedule(
                    course_id=course.id,
                    teacher_id=teacher.id,
                    class_id=class_.id,
                    room_id=room.id if room else None,
                    room_type=room_type,
                    meeting_link=meeting_link,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    start_date=date_obj,
                    end_date=date_obj,
                    has_conflict=False,
                    execution_status='pending',
                    schedule_type='formal'  # 默认导入为正式课
                )
                
                db.add(schedule)
                imported_count += 1
            except Exception as e:
                skipped_count += 1
                failed_rows.append({
                    'row': idx + 2,
                    'reason': f"处理失败: {str(e)}"
                })
                continue

        db.commit()
        get_all_conflicts(db)

        # 记录导入日志
        log_message = f"导入课程安排: 成功{imported_count}条"
        if skipped_count > 0:
            log_message += f"，跳过{skipped_count}条"
            # 记录失败详情
            for failed in failed_rows:
                log_operation(db, "课程安排", "导入失败", f"导入失败（第{failed['row']}行）: {failed['reason']}", current_user.username,"WARNING")

        log_operation(db, "课程安排", "导入", log_message, current_user.username,"Info")

        # 返回详细结果
        return {
            "count": imported_count,
            "skipped": skipped_count,
            "failed_rows": failed_rows[:10]  # 只返回前10条失败记录，避免数据量过大
        }
    except Exception as e:
        db.rollback()
        log_operation(db, "课程安排", "导入失败", f"导入课程安排失败: {str(e)}", current_user.username,"Error")
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")

def send_schedule_status_notification(db: Session, schedule: Schedule, status: str):
    """
    发送课程状态变更通知（微信+邮件）
    :param db: 数据库会话
    :param schedule: 课程安排对象
    :param status: 状态类型 'pending', 'completed', 'postponed', 'cancelled'
    """
    from models import Settings
    import json
    
    try:
        settings = db.query(Settings).first()
        if not settings:
            log_operation(db, "课程安排", "通知", "站点配置不存在，跳过发送通知", level="WARNING")
            return
        
        teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
        class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
        course = db.query(Course).filter(Course.id == schedule.course_id).first()
        
        if not teacher or not class_ or not course:
            log_operation(db, "课程安排", "通知", "课程相关信息不完整，跳过发送通知", level="WARNING")
            return
        
        students = get_students_by_class(db, schedule.class_id, is_active=True)
        
        attendance_status_map = {}
        if status == "completed":
            attendance_query = select(schedule_student.c.student_id, schedule_student.c.attendance_status).where(
                schedule_student.c.schedule_id == schedule.id
            )
            attendance_result = db.execute(attendance_query).fetchall()
            attendance_status_map = {row[0]: row[1] for row in attendance_result}
        
        attendance_text_map = {
            "present": "出席",
            "absent": "缺席",
            "leave": "请假",
            "pending": "未记录"
        }
        
        if status == "completed" and attendance_status_map:
            student_display_text = ', '.join([f"{s.name}({attendance_text_map.get(attendance_status_map.get(s.id, 'pending'), '未记录')})" for s in students])
        else:
            student_display_text = ', '.join([s.name for s in students])
        
        # 根据状态类型获取对应的文本和图标
        status_text = {
            "completed": "完训",
            "postponed": "延期",
            "cancelled": "取消排课",
            "pending": "待执行"
        }.get(status, "状态变更")
        
        status_icon = {
            "completed": "✅",
            "postponed": "⏰",
            "cancelled": "❌",
            "pending": "📅"
        }.get(status, "📢")
        
        # *** 1、 构建微信通知内容及发送微信通知 *** 
        # 根据状态类型构建不同的reason_text
        pending_room = db.query(Room).filter(Room.id == schedule.room_id).first() if status == "pending" else None
        reason_text = ""
        if status == "pending":
            if schedule.room_type == "offline_physical":
                reason_text = f"\n> **教室：** {pending_room.name}" if pending_room else ""
            else:
                reason_text = f"\n> **会议链接：** {schedule.meeting_link}" if schedule.meeting_link else ""
        elif status == "completed":
            if schedule.content_feedback:
                feedback_parts = schedule.content_feedback.split('|')
                content_part = feedback_parts[0].replace('内容：', '') if len(feedback_parts) > 0 else ''
                homework_part = feedback_parts[1].replace('作业：', '') if len(feedback_parts) > 1 else ''
                note_part = feedback_parts[2].replace('注意：', '') if len(feedback_parts) > 2 else ''
                reason_text = f"\n> **课程内容：** {content_part}\n> **作业：** {homework_part}\n> **注意事项：** {note_part}"
        elif status == "postponed":
            reason_text = f"\n> **延期原因：** {schedule.postpone_reason or '无'}"
        elif status == "cancelled":
            reason_text = f"\n> **取消原因：** {schedule.cancel_reason or '无'}"
        
        # 根据状态类型构建不同的课程类型schedule_type_text
        schedule_type_text = '【试听课】' if schedule.schedule_type == 'trial' else '【正式课】'
        
        # 构建微信通知内容，使用Markdown格式
        wechat_content = f"""## {status_icon} {schedule_type_text}·课程·{status_text}提醒
> **状态：** 课程ID：{schedule.id}执行{status_icon}{status_text}
> **日期：** {schedule.start_date.strftime('%Y-%m-%d')}
> **时间：** {schedule.start_time} - {schedule.end_time}
> **班级：** {class_.name}
> **科目：** {course.name}
> **学员：** {student_display_text}
> **导师：** {teacher.name}
{reason_text}
""" 
        # 加载微信配置
        wechat_notifier.load_config(settings.wechat_webhook_config or '{}')
        wechat_notifier.load_promotion_info(
            website=settings.organization_website,
            wechat_qr=settings.wechat_qrcode,
            work_wechat_qr=settings.work_wechat_qrcode
        )

        # 获取允许的班级列表
        enabled_classes = []
        try:
            # 使用与remainder.py相同的逻辑，确保解析安全
            notif_config = json.loads(settings.notification_settings or "{}")
            enabled_classes = notif_config.get('enabled_classes', [])
            log_operation(db, "课程安排", "通知", f"状态变更 - 成功解析notification_settings，enabled_classes: {enabled_classes}", level="DEBUG")
        except json.JSONDecodeError as e:
            log_operation(db, "课程安排", "通知", f"状态变更 - 解析notification_settings JSON失败: {e}, 使用空列表", level="WARNING")
            enabled_classes = []
        except Exception as e:
            log_operation(db, "课程安排", "通知", f"状态变更 - 获取enabled_classes时发生其他错误: {e}, 使用空列表", level="WARNING")
            enabled_classes = []

        log_operation(db, "课程安排", "通知", f"状态变更 - 班级ID: {class_.id}, 班级名称: {class_.name}, 班级webhook: {class_.wechat_webhook}", level="DEBUG")
        log_operation(db, "课程安排", "通知", f"状态变更 - 允许的班级列表: {enabled_classes}", level="DEBUG")
                
        # *** 2、 构建邮件通知内容及发送邮件 ***
        # 构建邮件主题
        email_subject = f"【课程{status_text}】{course.name} - {class_.name} - {schedule.start_date.strftime('%Y-%m-%d')}"
        # 构建邮件内容，使用HTML格式
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .info-item {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 5px; }}
                .label {{ color: #667eea; font-weight: bold; }}
                .value {{ color: #333; margin-top: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{status_icon} {"【试听课】" if schedule.schedule_type == "trial" else "【正式课】"}课程{status_text}提醒</h2>
                </div>
                <div class="content">
                    <div class="info-item">
                        <div class="label">日期</div>
                        <div class="value">{schedule.start_date.strftime('%Y-%m-%d')}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">时间</div>
                        <div class="value">{schedule.start_time} - {schedule.end_time}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">班级</div>
                        <div class="value">{class_.name}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">科目</div>
                        <div class="value">{course.name}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">学员</div>
                        <div class="value">{student_display_text}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">导师</div>
                        <div class="value">{teacher.name}</div>
                    </div>
                    
        """
        # 根据状态类型添加不同的邮件内容
        if status == "completed" and schedule.content_feedback:
            feedback_parts = schedule.content_feedback.split('|')
            content_part = feedback_parts[0].replace('内容：', '') if len(feedback_parts) > 0 else ''
            homework_part = feedback_parts[1].replace('作业：', '') if len(feedback_parts) > 1 else ''
            note_part = feedback_parts[2].replace('注意：', '') if len(feedback_parts) > 2 else ''
            email_html += f"""
                    <div class="info-item">
                        <div class="label">课程内容</div>
                        <div class="value">{content_part}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">作业</div>
                        <div class="value">{homework_part}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">注意事项</div>
                        <div class="value">{note_part}</div>
                    </div>
            """
        elif status == "postponed":
            email_html += f"""
                    <div class="info-item">
                        <div class="label">延期原因</div>
                        <div class="value">{schedule.postpone_reason or '无'}</div>
                    </div>
            """
        elif status == "cancelled":
            email_html += f"""
                    <div class="info-item">
                        <div class="label">取消原因</div>
                        <div class="value">{schedule.cancel_reason or '无'}</div>
                    </div>
            """
        elif status == "pending":
            if schedule.room_type == "offline_physical" and pending_room:
                email_html += f"""
                    <div class="info-item">
                        <div class="label">教室</div>
                        <div class="value">{pending_room.name}</div>
                    </div>
                """
            elif schedule.meeting_link:
                email_html += f"""
                    <div class="info-item">
                        <div class="label">会议链接</div>
                        <div class="value">{schedule.meeting_link}</div>
                    </div>
                """
        
        email_html += f"""
                </div>
                <div class="footer">
                    <p>此邮件由课程安排系统自动发送，请勿直接回复。</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 加载邮件配置
        email_config = json.loads(settings.email_config or '{}')
        email_notifier.load_config(settings.email_config or '{}', settings.site_name or '课程安排系统')
        email_notifier.load_promotion_info(
            website=settings.organization_website,
            wechat_qr=settings.wechat_qrcode,
            work_wechat_qr=settings.work_wechat_qrcode
        )
        
        recipient_emails = []
        if teacher.email:
            recipient_emails.append(teacher.email)
        for student in students:
            if student.email:
                recipient_emails.append(student.email)
        
        if recipient_emails and email_config.get('smtp_host'):
            try:
                email_notifier.send_email(recipient_emails, email_subject, email_html)
                log_operation(db, "课程安排", "通知", f"邮件通知发送成功，收件人数量: {len(recipient_emails)}", level="INFO")
            except Exception as e:
                log_operation(db, "课程安排", "通知", f"邮件通知发送失败: {str(e)}", level="ERROR")
        else:
            log_operation(db, "课程安排", "通知", "邮件配置不完整或无收件人，跳过邮件发送", level="DEBUG")
        
        wechat_success = False
        try:
            from routers.license import _check_premium_feature
            wechat_authorized = _check_premium_feature('wechat_notify', db)
            if wechat_authorized:
                wechat_msg_type = "schedule_arrange"
                class_result = wechat_notifier.send_message_by_type(wechat_msg_type, wechat_content, class_id=schedule.class_id, class_webhook=class_.wechat_webhook, is_markdown=True, enabled_classes=enabled_classes)
                if class_result.get("success"):
                    log_operation(db, "课程安排", "通知", "微信通知发送成功", level="INFO")
                    wechat_success = True
                else:
                    log_operation(db, "课程安排", "通知", f"微信通知发送失败: {class_result.get('message', '未知错误')}", level="WARNING")
            else:
                log_operation(db, "课程安排", "通知", "微信通知功能未授权，跳过微信通知", level="WARNING")
        except Exception as e:
            log_operation(db, "课程安排", "通知", f"微信通知发送失败: {str(e)}", level="ERROR")

        if wechat_success:
            log_operation(db, "课程安排", "通知", "微信通知发送完成", level="INFO")
        else:
            log_operation(db, "课程安排", "通知", "微信通知发送失败", level="WARNING")
        
        log_operation(db, "课程安排", "通知", f"课程{status_text}通知发送完成", level="INFO")
        
    except Exception as e:
        import traceback
        log_operation(db, "课程安排", "通知", f"发送通知过程中出错: {str(e)}", level="ERROR")


@router.post("/{schedule_id}/notify")
def notify_schedule_status(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """
    立即发送课程当前状态通知（微信+邮件），不修改课程安排数据
    """
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not db_schedule:
        log_operation(db, "课程安排", "立即通知", f"课程安排不存在: ID{schedule_id}", current_user.username, "ERROR")
        raise HTTPException(status_code=404, detail="课程安排不存在")

    status = db_schedule.execution_status
    status_map = {
        "pending": "待执行",
        "completed": "完训",
        "postponed": "延期",
        "cancelled": "取消排课"
    }
    status_text = status_map.get(status, "状态变更")

    try:
        send_schedule_status_notification(db, db_schedule, status)
        log_operation(db, "课程安排", "立即通知", f"课程ID{schedule_id}当前状态【{status_text}】通知发送成功", current_user.username, "INFO")
        return {"message": f"课程{status_text}通知发送成功", "status": status}
    except Exception as e:
        log_operation(db, "课程安排", "立即通知", f"课程ID{schedule_id}通知发送失败: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"通知发送失败: {str(e)}")