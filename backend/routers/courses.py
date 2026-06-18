# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional
from database import get_db
from models import Course, Teacher, course_teacher
from schemas import CourseCreate, CourseUpdate, Course as CourseSchema, PaginatedCourseResponse
from routers.auth import get_teacher_visibility_filter,  get_current_user, get_current_course_admin_user, User
from utils.logger import log_operation

router = APIRouter()

@router.get("", response_model=PaginatedCourseResponse)
def get_courses(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_field: Optional[str] = Query(None, description="排序字段，如：id, code, name"),
    sort_order: Optional[str] = Query("asc", description="排序顺序：asc 或 desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Course)
    
    # 应用导师可见性过滤
    teacher_filter = get_teacher_visibility_filter(db, current_user)
    
    if teacher_filter is not None:
        if hasattr(teacher_filter, 'compile'):
            query = query.filter(teacher_filter)
        else:
            # 过滤出该导师教授的科目
            query = query.filter(Course.teachers.any(Teacher.id == teacher_filter))
    else:
        log_operation(db, "科目管理", "查询科目列表", f"导师可见性限制未启用（Filter为None）", current_user.username, "DEBUG")
    
    if search:
        query = query.filter(
            (Course.name.ilike(f'%{search}%')) | 
            (Course.code.ilike(f'%{search}%'))
        )
    
    # 应用排序
    if sort_field:
        sort_column = getattr(Course, sort_field, None)
        if sort_column:
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
    else:
        # 默认按ID降序排列
        query = query.order_by(desc(Course.id))
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    
    result = []
    for course in courses:
        # 如果 is_active 为 true，只返回关联了在职教师的科目
        if is_active is True:
            active_teachers = [t for t in course.teachers if t.is_active]
            if not active_teachers:
                continue  # 如果没有关联在职教师，跳过该科目
            teacher_ids = [t.id for t in active_teachers]
            teachers_list = [{"id": t.id, "name": t.name, "contact_phone": t.contact_phone} for t in active_teachers]
        else:
            # 返回所有关联的教师ID
            teacher_ids = [t.id for t in course.teachers]
            teachers_list = [{"id": t.id, "name": t.name, "contact_phone": t.contact_phone} for t in course.teachers]
        
        result.append(CourseSchema(
            id=course.id,
            code=course.code,
            name=course.name,
            priority=course.priority,
            teacher_ids=teacher_ids,
            teachers=teachers_list,
            created_at=course.created_at,
            updated_at=course.updated_at
        ))
    
    return {
        "items": result,
        "total": total
    }


@router.get("/{course_id}", response_model=CourseSchema)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        log_operation(db, "科目管理", "查询科目详情失败", f"科目ID {course_id} 不存在", "system", "WARNING")
        raise HTTPException(status_code=404, detail="科目不存在")
    
    teacher_ids = [t.id for t in course.teachers]
    return CourseSchema(
        id=course.id,
        code=course.code,
        name=course.name,
        priority=course.priority,
        teacher_ids=teacher_ids,
        created_at=course.created_at,
        updated_at=course.updated_at
    )

@router.post("", response_model=CourseSchema)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_course = db.query(Course).filter(Course.code == course.code).first()
    if db_course:
        log_operation(db, "科目管理", "创建科目失败", f"科目代码 {course.code} 已存在", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="科目代码已存在")
    
    db_course = Course(
        code=course.code,
        name=course.name,
        priority=course.priority
    )
    db.add(db_course)
    db.commit()
    log_operation(db, "科目管理", "新增",  f"成功创建科目: {course.code} - {course.name}", current_user.username)
    db.refresh(db_course)
    
    if course.teacher_ids:
        teachers = db.query(Teacher).filter(Teacher.id.in_(course.teacher_ids)).all()
        db_course.teachers = teachers
        db.commit()
        db.refresh(db_course)
        log_operation(db, "科目管理", "修改", f"成功更新科目: {db_course.code} - {db_course.name}", current_user.username)
    
    teacher_ids = [t.id for t in db_course.teachers]
    return CourseSchema(
        id=db_course.id,
        code=db_course.code,
        name=db_course.name,
        priority=db_course.priority,
        teacher_ids=teacher_ids,
        created_at=db_course.created_at,
        updated_at=db_course.updated_at
    )

@router.put("/{course_id}", response_model=CourseSchema)
def update_course(
    course_id: int,
    course: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        log_operation(db, "科目管理", "更新科目失败", f"科目ID {course_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="科目不存在")
    
    if course.name is not None:
        db_course.name = course.name
    if course.priority is not None:
        db_course.priority = course.priority
    
    if course.teacher_ids is not None:
        db_course.teachers = []
        if course.teacher_ids:
            teachers = db.query(Teacher).filter(Teacher.id.in_(course.teacher_ids)).all()
            db_course.teachers = teachers
    
    db.commit()
    db.refresh(db_course)
    
    teacher_ids = [t.id for t in db_course.teachers]
    log_operation(db, "科目管理", "修改", f"成功更新科目: {db_course.code} - {db_course.name}", current_user.username)
    return CourseSchema(
        id=db_course.id,
        code=db_course.code,
        name=db_course.name,
        priority=db_course.priority,
        teacher_ids=teacher_ids,
        created_at=db_course.created_at,
        updated_at=db_course.updated_at
    )

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        log_operation(db, "科目管理", "删除科目失败", f"科目ID {course_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="科目不存在")
    
    if db_course.schedules:
        log_operation(db, "科目管理", "删除科目失败", f"科目 {db_course.code} - {db_course.name} 已有课程安排，无法删除", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="该科目已有课程安排，无法删除")
    
    db.delete(db_course)
    db.commit()
    log_operation(db, "科目管理", "删除", f"成功删除科目: {db_course.code} - {db_course.name}", current_user.username, "WARNING")
    return {"message": "删除成功"}