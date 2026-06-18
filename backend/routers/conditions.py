# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Condition
from schemas import ConditionCreate, ConditionUpdate, Condition as ConditionSchema, PaginatedConditionResponse
from routers.auth import  get_current_course_admin_user, User
from utils.logger import log_operation

router = APIRouter()

HARD_CONSTRAINTS = [
    {
        "id": "HC_CLASS_TIME",
        "name": "班级时间约束",
        "description": "一个班级在同一个时间（课节）内只能安排一门课程",
        "is_hard_constraint": True,
        "is_active": True
    },
    {
        "id": "HC_ROOM_TIME",
        "name": "教室时间约束",
        "description": "一个教室在同一个时间（课节）内只能安排一门课程",
        "is_hard_constraint": True,
        "is_active": True
    },
    {
        "id": "HC_TEACHER_TIME",
        "name": "导师时间约束",
        "description": "一个导师在同一个时间（课节）内只能安排一门课程",
        "is_hard_constraint": True,
        "is_active": True
    },
    {
        "id": "HC_STUDENT_TIME",
        "name": "学员时间约束",
        "description": "一个学员在同一个时间（课节）内只能被安排一门课程",
        "is_hard_constraint": True,
        "is_active": True
    }
]

@router.get("/hard")
def get_hard_constraints():
    return HARD_CONSTRAINTS

@router.get("/soft", response_model=PaginatedConditionResponse)
def get_soft_conditions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Condition).filter(Condition.is_hard_constraint == False)
    total = query.count()
    conditions = query.offset(skip).limit(limit).all()
    
    return {
        "items": conditions,
        "total": total
    }

@router.get("", response_model=PaginatedConditionResponse)
def get_all_conditions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Condition)
    total = query.count()
    conditions = query.offset(skip).limit(limit).all()
    
    return {
        "items": conditions,
        "total": total
    }

@router.post("", response_model=ConditionSchema)
def create_condition(
    condition: ConditionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    if condition.is_hard_constraint:
        log_operation(db, "条件管理", "创建条件失败", f"尝试创建硬性约束: {condition.condition_type} - {condition.description}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="不能创建硬性约束，硬性约束由系统预设")
    
    db_condition = Condition(
        name=condition.name,
        condition_type=condition.condition_type,
        description=condition.description,
        is_hard_constraint=False,
        is_active=condition.is_active
    )
    db.add(db_condition)
    db.commit()
    db.refresh(db_condition)
    log_operation(db, "条件管理", "新建", f"条件被成功创建: {db_condition.condition_type} - {db_condition.description}", current_user.username)
    return db_condition

@router.put("/{condition_id}", response_model=ConditionSchema)
def update_condition(
    condition_id: int,
    condition: ConditionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_condition = db.query(Condition).filter(Condition.id == condition_id).first()
    if not db_condition:
        log_operation(db, "条件管理", "修改条件失败", f"条件ID: {condition_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="条件不存在")
    
    if db_condition.is_hard_constraint:
        log_operation(db, "条件管理", "修改条件失败", f"尝试修改硬性约束: {db_condition.condition_type} - {db_condition.description}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="不能修改硬性约束")
    
    if condition.description is not None:
        db_condition.description = condition.description
    if condition.is_active is not None:
        db_condition.is_active = condition.is_active
    
    db.commit()
    db.refresh(db_condition)
    return db_condition

@router.delete("/{condition_id}")
def delete_condition(
    condition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_condition = db.query(Condition).filter(Condition.id == condition_id).first()
    if not db_condition:
        log_operation(db, "条件管理", "删除条件失败", f"条件ID: {condition_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="条件不存在")
    
    if db_condition.is_hard_constraint:
        log_operation(db, "条件管理", "删除条件失败", f"尝试删除硬性约束: {db_condition.condition_type} - {db_condition.description}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="不能删除硬性约束")
    
    db.delete(db_condition)
    db.commit()
    log_operation(db, "条件管理", "删除", f"条件被成功删除: {db_condition.condition_type} - {db_condition.description}", current_user.username,  "WARNING")
    return {"message": "删除成功"}