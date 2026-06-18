# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional
from database import get_db
from models import Teacher, Course
from schemas import TeacherCreate, TeacherUpdate, Teacher as TeacherSchema, PaginatedTeacherResponse
from routers.auth import  get_teacher_visibility_filter, is_subject_teacher, get_current_course_admin_user, get_current_user, User
from utils.logger import log_operation

router = APIRouter()

@router.get("", response_model=PaginatedTeacherResponse)
def get_teachers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    teacher_id: Optional[int] = None,
    sort_field: Optional[str] = Query(None, description="排序字段，如：id, code, name"),
    sort_order: Optional[str] = Query("asc", description="排序顺序：asc 或 desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Teacher)

    # 应用导师可见性过滤
    teacher_filter = get_teacher_visibility_filter(db, current_user)
    
    if teacher_filter is not None:
        # 如果开启了导师可见性限制且用户不是超级导师
        if not is_subject_teacher(db, current_user):
            # 只返回当前导师关联的导师信息
            if current_user.teacher_id:
                query = query.filter(Teacher.id == current_user.teacher_id)
            else:
                # 如果没有关联导师，返回空列表
                return {"items": [], "total": 0}
    
    # 如果指定了teacher_id参数，只返回该导师
    if teacher_id is not None:
        query = query.filter(Teacher.id == teacher_id)

    if search:
        query = query.filter(
            (Teacher.name.ilike(f'%{search}%')) | 
            (Teacher.code.ilike(f'%{search}%')) |
            (Teacher.department.ilike(f'%{search}%'))|
            (Teacher.contact_phone.ilike(f'%{search}%'))|
            (Teacher.email.ilike(f'%{search}%'))
        )
    if is_active is not None:
        query = query.filter(Teacher.is_active == is_active)
    
    # 应用排序
    if sort_field:
        sort_column = getattr(Teacher, sort_field, None)
        if sort_column:
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
    else:
        # 默认按ID降序排列
        query = query.order_by(desc(Teacher.id))

    total = query.count()
    teachers = query.offset(skip).limit(limit).all()
    
    result = []
    for teacher in teachers:
        course_ids = [c.id for c in teacher.courses]
        result.append(TeacherSchema(
            id=teacher.id,
            code=teacher.code,
            name=teacher.name,
            title=teacher.title,
            department=teacher.department,
            contact_phone=teacher.contact_phone,
            email=teacher.email,
            max_weekly_hours=teacher.max_weekly_hours,
            available_days=teacher.available_days,
            available_time_slots=teacher.available_time_slots,
            allow_holiday_scheduling=teacher.allow_holiday_scheduling,
            is_active=teacher.is_active,
            end_date=teacher.end_date,
            no_feedback_required=teacher.no_feedback_required,
            course_ids=course_ids,
            created_at=teacher.created_at,
            updated_at=teacher.updated_at
        ))
    
    return {
        "items": result,
        "total": total
    }

@router.get("/{teacher_id}", response_model=TeacherSchema)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        log_operation(db, "导师管理", "查询导师详情失败", f"导师ID {teacher_id} 不存在", "system", "WARNING")
        raise HTTPException(status_code=404, detail="导师不存在")
    
    course_ids = [c.id for c in teacher.courses]
    return TeacherSchema(
        id=teacher.id,
        code=teacher.code,
        name=teacher.name,
        title=teacher.title,
        department=teacher.department,
        contact_phone=teacher.contact_phone,
        email=teacher.email,
        max_weekly_hours=teacher.max_weekly_hours,
        available_days=teacher.available_days,
        available_time_slots=teacher.available_time_slots,
        allow_holiday_scheduling=teacher.allow_holiday_scheduling,
        is_active=teacher.is_active,
        end_date=teacher.end_date,
        no_feedback_required=teacher.no_feedback_required,
        course_ids=course_ids,
        created_at=teacher.created_at,
        updated_at=teacher.updated_at
    )

@router.post("", response_model=TeacherSchema)
def create_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_teacher = db.query(Teacher).filter(Teacher.code == teacher.code).first()
    if db_teacher:
        log_operation(db, "导师管理", "创建导师失败", f"导师代码 {teacher.code} 已存在", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="导师代码已存在")
    
    db_teacher = Teacher(
        code=teacher.code,
        name=teacher.name,
        title=teacher.title,
        department=teacher.department,
        contact_phone=teacher.contact_phone,
        email=teacher.email,
        max_weekly_hours=teacher.max_weekly_hours,
        available_days=teacher.available_days,
        available_time_slots=teacher.available_time_slots,
        allow_holiday_scheduling=teacher.allow_holiday_scheduling,
        is_active=teacher.is_active,
        end_date=teacher.end_date,
        no_feedback_required=teacher.no_feedback_required,
        created_at=teacher.created_at,
        updated_at=teacher.updated_at
    )
    db.add(db_teacher)
    db.commit()
    log_operation(db, "导师管理", "新增", f"成功新增导师: {teacher.code} -{teacher.name}", current_user.username)
    db.refresh(db_teacher)
    
    course_ids = [c.id for c in db_teacher.courses]
    return TeacherSchema(
        id=db_teacher.id,
        code=db_teacher.code,
        name=db_teacher.name,
        title=db_teacher.title,
        department=db_teacher.department,
        contact_phone=teacher.contact_phone,
        email=teacher.email,
        max_weekly_hours=db_teacher.max_weekly_hours,
        available_days=db_teacher.available_days,
        available_time_slots=db_teacher.available_time_slots,
        allow_holiday_scheduling=db_teacher.allow_holiday_scheduling,
        is_active=db_teacher.is_active,
        end_date=db_teacher.end_date,
        no_feedback_required=db_teacher.no_feedback_required,
        course_ids=course_ids,
        created_at=db_teacher.created_at,
        updated_at=db_teacher.updated_at
    )

@router.put("/{teacher_id}", response_model=TeacherSchema)
def update_teacher(
    teacher_id: int,
    teacher: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not db_teacher:
        log_operation(db, "导师管理", "修改导师失败", f"导师ID {teacher_id} 不存在", current_user.username, "WARNING") 
        raise HTTPException(status_code=404, detail="导师不存在")
    
    # 检查是否是导师本人，如果是则禁止修改"无需填写反馈"属性
    # 只有当no_feedback_required的值发生改变时，才禁止修改
    if current_user.teacher_id == teacher_id:
        if teacher.no_feedback_required is not None and teacher.no_feedback_required != db_teacher.no_feedback_required:
            log_operation(db, "导师管理", "修改导师失败", f"导师不能修改自己的'无需填写反馈'属性", current_user.username, "WARNING")
            raise HTTPException(status_code=403, detail="导师不能修改自己的'无需填写反馈'属性")
    
    # 检查is_active是否从True变为False
    is_becoming_inactive = (db_teacher.is_active == True and teacher.is_active == False)
    
    if teacher.name is not None:
        db_teacher.name = teacher.name
    if teacher.title is not None:
        db_teacher.title = teacher.title
    if teacher.department is not None:
        db_teacher.department = teacher.department
    if teacher.contact_phone is not None:
        db_teacher.contact_phone = teacher.contact_phone
    if teacher.email is not None:
        db_teacher.email = teacher.email
    if teacher.max_weekly_hours is not None:
        db_teacher.max_weekly_hours = teacher.max_weekly_hours
    if teacher.available_days is not None:
        db_teacher.available_days = teacher.available_days
    if teacher.available_time_slots is not None:
        db_teacher.available_time_slots = teacher.available_time_slots
    if teacher.allow_holiday_scheduling is not None:
        db_teacher.allow_holiday_scheduling = teacher.allow_holiday_scheduling
    if teacher.is_active is not None:
        db_teacher.is_active = teacher.is_active
    if teacher.end_date is not None:
        db_teacher.end_date = teacher.end_date
    if teacher.no_feedback_required is not None:
        db_teacher.no_feedback_required = teacher.no_feedback_required
    
    # 如果从在职变为离职，检查是否填写了离职日期
    if is_becoming_inactive and db_teacher.end_date is None:
        log_operation(db, "导师管理", "修改导师失败", f"导师 {db_teacher.code} - {db_teacher.name} 离职时未填写离职日期", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="导师离职时必须填写离职日期")
    
    db.commit()
    log_operation(db, "导师管理", "修改", f"成功更新导师: {db_teacher.code} -{db_teacher.name}", current_user.username)  # 修改这里，使用db_teacher.code而不是teacher.code
    db.refresh(db_teacher)
    
    # 如果从在职变为离职，写入日志
    if is_becoming_inactive:
        log_operation(db, "导师管理", "修改",  f"导师 {db_teacher.name} (ID: {db_teacher.id}) 离职，离职日期: {db_teacher.end_date}")

    course_ids = [c.id for c in db_teacher.courses]
    return TeacherSchema(
        id=db_teacher.id,
        code=db_teacher.code,
        name=db_teacher.name,
        title=db_teacher.title,
        department=db_teacher.department,
        contact_phone=db_teacher.contact_phone,
        max_weekly_hours=db_teacher.max_weekly_hours,
        available_days=db_teacher.available_days,
        available_time_slots=db_teacher.available_time_slots,
        allow_holiday_scheduling=db_teacher.allow_holiday_scheduling,
        contact_email=db_teacher.email,
        teacher_ids=course_ids,
        courses=[{"id": c.id, "name": c.name} for c in db_teacher.courses],
        no_feedback_required=db_teacher.no_feedback_required,
        is_active=db_teacher.is_active,
        end_date=db_teacher.end_date,
        created_at=db_teacher.created_at,
        updated_at=db_teacher.updated_at
    )

@router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not db_teacher:
        log_operation(db, "导师管理", "删除导师失败", f"导师ID {teacher_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="导师不存在")
    
    if db_teacher.schedules:
        log_operation(db, "导师管理", "删除导师失败", f"导师 {db_teacher.code} - {db_teacher.name} 已有课程安排，无法删除", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="该导师已有课程安排，无法删除")
    
    db.delete(db_teacher)
    db.commit()
    log_operation(db, "导师管理", "删除", f"成功删除导师: {db_teacher.code} - {db_teacher.name}", current_user.username, "WARNING")
    return {"message": "删除成功"}