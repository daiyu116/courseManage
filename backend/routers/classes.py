# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from typing import List, Optional
from database import get_db
from models import Class, Student, Schedule, Course, Teacher
from schemas import ClassCreate, ClassUpdate, Class as ClassSchema, PaginatedClassResponse
from routers.auth import get_teacher_visibility_filter,  get_current_user, get_current_course_admin_user, User
from utils.logger import log_operation

router = APIRouter()

@router.get("", response_model=PaginatedClassResponse)
def get_classes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_field: Optional[str] = Query(None, description="排序字段，如：id, code, name"),
    sort_order: Optional[str] = Query("asc", description="排序顺序：asc 或 desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log_operation(db, "班级管理", "查询班级列表", f"参数: skip={skip}, limit={limit}, search={search}, is_active={is_active}, sort_field={sort_field}, sort_order={sort_order}", current_user.username, "DEBUG")
    query = db.query(Class)
    
    # 应用导师可见性过滤
    teacher_filter = get_teacher_visibility_filter(db, current_user)
    
    if teacher_filter is not None:
        if hasattr(teacher_filter, 'compile'):
            # 如果是 false() 对象，则查询结果为空
            query = query.filter(teacher_filter)
        else:
            # 逻辑：只查询该导师（teacher_filter）亲自排过课的班级
            log_operation(db, "班级管理", "应用导师过滤", f"导师ID: {teacher_filter}", current_user.username, "DEBUG")
            
            # 子查询：找出该导师所有排课记录中的 class_id
            related_class_ids_subquery = db.query(Schedule.class_id).filter(
                Schedule.teacher_id == teacher_filter
            ).distinct().subquery()
            
            query = query.filter(Class.id.in_(related_class_ids_subquery))
    else:
        log_operation(db, "班级管理", "导师可见性限制未启用", f"教师ID: {current_user.id} - {current_user.username}", current_user.username, "DEBUG")

    if search:
        query = query.filter(
            (Class.name.ilike(f'%{search}%')) | 
            (Class.code.ilike(f'%{search}%')) |
            (Class.description.ilike(f'%{search}%'))
        )
    if is_active is not None:
        query = query.filter(Class.is_active == is_active)

    # 应用排序
    if sort_field:
        sort_column = getattr(Class, sort_field, None)
        if sort_column:
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
    
    total = query.count()
    classes = query.offset(skip).limit(limit).all()
    log_operation(db, "班级管理", "班级查询",f"DEBUG: get_classes - 查询到的班级数量: {len(classes)} 查询到的班级数据: {classes}", current_user.username, "DEBUG")
    
    return {
        "items": classes,
        "total": total
    }

@router.get("/{class_id}", response_model=ClassSchema)
def get_class(class_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    class_ = db.query(Class).filter(Class.id == class_id).first()
    if not class_:
        log_operation(db, "班级管理", "班级查询",f"DEBUG: get_classes - 获取班级失败: {class_id}", current_user.username, "DEBUG")
        raise HTTPException(status_code=404, detail="班级不存在")
    return ClassSchema(
        id=class_.id,
        code=class_.code,
        name=class_.name,
        description=class_.description,
        is_active=class_.is_active,
        created_at=class_.created_at,
        updated_at=class_.updated_at
    )

@router.post("", response_model=ClassSchema)
def create_class(
    class_: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_class = db.query(Class).filter(Class.code == class_.code).first()
    if db_class:
        log_operation(db, "班级管理", "创建班级失败", f"班级代码 {class_.code} 已存在", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="班级代码已存在")
    
    db_class = Class(
        code=class_.code,
        name=class_.name,
        description=class_.description,
        is_active=class_.is_active
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    log_operation(db, "班级管理", "新增", f"成功创建班级: {db_class.code} - {db_class.name}", current_user.username)
    return ClassSchema(
        id=db_class.id,
        code=db_class.code,
        name=db_class.name,
        description=db_class.description,
        is_active=db_class.is_active,
        created_at=db_class.created_at,
        updated_at=db_class.updated_at
    )

@router.put("/{class_id}", response_model=ClassSchema)
def update_class(
    class_id: int,
    class_: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        log_operation(db, "班级管理", "修改班级失败", f"班级ID {class_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="班级不存在")
    
    if class_.name is not None:
        db_class.name = class_.name
    if class_.description is not None:
        db_class.description = class_.description
    if class_.is_active is not None:
        db_class.is_active = class_.is_active
    if class_.wechat_webhook is not None:
        db_class.wechat_webhook = class_.wechat_webhook

    db.commit()
    db.refresh(db_class)
    log_operation(db, "班级管理", "修改", f"成功更新班级: {db_class.code} - {db_class.name}", current_user.username)
    return ClassSchema(
        id=db_class.id,
        code=db_class.code,
        name=db_class.name,
        description=db_class.description,
        is_active=db_class.is_active,
        wechat_webhook=db_class.wechat_webhook,
        created_at=db_class.created_at,
        updated_at=db_class.updated_at
    )

@router.delete("/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        log_operation(db, "班级管理", "删除班级失败", f"班级ID {class_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="班级不存在")
    
    if db_class.schedules:
        log_operation(db, "班级管理", "删除班级失败", f"班级 {db_class.code} - {db_class.name} 已有课程安排，无法删除", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="该班级已有课程安排，无法删除")
    
    db.delete(db_class)
    db.commit()
    log_operation(db, "班级管理", "删除", f"成功删除班级: {db_class.code} - {db_class.name}", current_user.username)
    return {"message": "删除成功"}