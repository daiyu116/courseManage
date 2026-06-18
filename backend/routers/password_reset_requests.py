# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import PasswordResetRequest, User
from schemas import PasswordResetRequest as PasswordResetRequestSchema, PasswordResetRequestUpdate
from routers.auth import get_current_system_admin_user, get_password_hash
from pydantic import BaseModel

router = APIRouter()

class PasswordReset(BaseModel):
    new_password: str

@router.get("", response_model=List[PasswordResetRequestSchema])
def get_password_reset_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """管理员获取所有密码重置请求"""
    requests = db.query(PasswordResetRequest).order_by(PasswordResetRequest.created_at.desc()).all()
    return requests

@router.put("/{request_id}", response_model=PasswordResetRequestSchema)
def update_password_reset_request(
    request_id: int,
    request_update: PasswordResetRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """管理员更新密码重置请求状态"""
    reset_request = db.query(PasswordResetRequest).filter(PasswordResetRequest.id == request_id).first()
    if not reset_request:
        raise HTTPException(status_code=404, detail="重置请求不存在")
    
    reset_request.status = request_update.status
    db.commit()
    db.refresh(reset_request)
    return reset_request

@router.post("/reset-password/{user_id}")
def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """管理员重置用户密码"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "密码重置成功"}