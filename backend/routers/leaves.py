# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Leave, Teacher, Student
from schemas import LeaveCreate, LeaveUpdate, Leave as LeaveSchema, PaginatedLeaveResponse
from routers.auth import  get_current_course_admin_user, User
from utils.logger import log_operation

router = APIRouter()

@router.get("", response_model=PaginatedLeaveResponse)
def get_leaves(
    skip: int = 0,
    limit: int = 100,
    leave_type: Optional[str] = None,
    teacher_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Leave)
    if leave_type:
        query = query.filter(Leave.leave_type == leave_type)
    if teacher_id:
        query = query.filter(Leave.teacher_id == teacher_id)
    if student_id:
        query = query.filter(Leave.student_id == student_id)
    
    total = query.count()
    leaves = query.offset(skip).limit(limit).all()
    
    return {
        "items": leaves,
        "total": total
    }

@router.get("/{leave_id}", response_model=LeaveSchema)
def get_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        log_operation(db, "假期管理", "查询请假详情", f"请假ID: {leave_id} 不存在", "system", "WARNING")    
        raise HTTPException(status_code=404, detail="请假记录不存在")
    return leave

@router.post("", response_model=LeaveSchema)
def create_leave(
    leave: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    if leave.leave_type == "teacher" and leave.teacher_id:
        teacher = db.query(Teacher).filter(Teacher.id == leave.teacher_id).first()
        if not teacher:
            log_operation(db, "假期管理", "创建请假", f"导师ID: {leave.teacher_id} 不存在", current_user.username, "WARNING")
            raise HTTPException(status_code=404, detail="导师不存在")
    elif leave.leave_type == "student" and leave.student_id:
        student = db.query(Student).filter(Student.id == leave.student_id).first()
        if not student:
            log_operation(db, "假期管理", "创建请假", f"学员ID: {leave.student_id} 不存在", current_user.username, "WARNING")
            raise HTTPException(status_code=404, detail="学员不存在")
    else:
        log_operation(db, "假期管理", "创建请假", f"请假类型和对应的导师/学员ID不匹配, 请假类型: {leave.leave_type}, 导师ID: {leave.teacher_id}, 学员ID: {leave.student_id}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="请假类型和对应的导师/学员ID不匹配")
    
    db_leave = Leave(
        leave_type=leave.leave_type,
        teacher_id=leave.teacher_id,
        student_id=leave.student_id,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason
    )
    db.add(db_leave)
    db.commit()
    db.refresh(db_leave)
    log_operation(db, "假期管理", "新增", f"成功创建请假: {db_leave.leave_type} - {db_leave.reason}", current_user.username)
    return db_leave

@router.put("/{leave_id}", response_model=LeaveSchema)
def update_leave(
    leave_id: int,
    leave: LeaveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not db_leave:
        log_operation(db, "假期管理", "更新请假", f"请假ID: {leave_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="请假记录不存在")
    
    if leave.start_date is not None:
        db_leave.start_date = leave.start_date
    if leave.end_date is not None:
        db_leave.end_date = leave.end_date
    if leave.reason is not None:
        db_leave.reason = leave.reason
    
    db.commit()
    db.refresh(db_leave)
    log_operation(db, "假期管理", "更新",  f"成功更新请假: {db_leave.leave_type} - {db_leave.reason}", current_user.username)
    return db_leave

@router.delete("/{leave_id}")
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not db_leave:
        log_operation(db, "假期管理", "删除请假", f"请假ID: {leave_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="请假记录不存在")
    
    db.delete(db_leave)
    db.commit()
    log_operation(db, "假期管理", "删除", f"请假被成功删除: {db_leave.leave_type} - {db_leave.reason}", current_user.username,  "WARNING")
    return {"message": "删除成功"}