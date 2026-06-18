# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional
from database import get_db
from models import Room
from schemas import RoomCreate, RoomUpdate, Room as RoomSchema, PaginatedRoomResponse
from routers.auth import  get_current_course_admin_user, User
from utils.logger import log_operation

router = APIRouter()

@router.get("", response_model=PaginatedRoomResponse)
def get_rooms(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    facilities: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_field: Optional[str] = Query(None, description="排序字段，如：id, code, name"),
    sort_order: Optional[str] = Query("asc", description="排序顺序：asc 或 desc"),
    db: Session = Depends(get_db)
):
    query = db.query(Room)
    
    if search:
        query = query.filter(
            (Room.name.ilike(f'%{search}%')) | 
            (Room.code.ilike(f'%{search}%')) |
            (Room.location.ilike(f'%{search}%'))
        )

    if facilities:
        query = query.filter(Room.facilities == facilities)

    if is_active is not None:
        query = query.filter(Room.is_active == is_active)
    
    # 应用排序
    if sort_field:
        sort_column = getattr(Room, sort_field, None)
        if sort_column:
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
    else:
        # 默认按ID降序排列
        query = query.order_by(desc(Room.id))
    
    total = query.count()
    rooms = query.offset(skip).limit(limit).all()
    
    return {
        "items": rooms,
        "total": total
    }

@router.get("/{room_id}", response_model=RoomSchema)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        log_operation(db, "教室管理", "查询教室详情", f"教室ID: {room_id} 不存在", "system", "WARNING")
        raise HTTPException(status_code=404, detail="教室不存在")
    return room

@router.post("", response_model=RoomSchema)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_room = db.query(Room).filter(Room.code == room.code).first()
    if db_room:
        log_operation(db, "教室管理", "创建教室", f"教室代码: {room.code} 已存在", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="教室代码已存在")
    
    db_room = Room(
        code=room.code,
        name=room.name,
        location=room.location,
        capacity=room.capacity,
        facilities=room.facilities,
        facility_details=room.facility_details,
        is_active=room.is_active
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    log_operation(db, "教室管理", "新增",  f"成功创建教室: {db_room.code} - {db_room.name}", current_user.username)
    return db_room

@router.put("/{room_id}", response_model=RoomSchema)
def update_room(
    room_id: int,
    room: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        log_operation(db, "教室管理", "修改教室", f"教室ID: {room_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="教室不存在")
    
    if room.name is not None:
        db_room.name = room.name
    if room.location is not None:
        db_room.location = room.location
    if room.capacity is not None:
        db_room.capacity = room.capacity
    if room.facilities is not None:
        db_room.facilities = room.facilities
    if room.facility_details is not None:
        db_room.facility_details = room.facility_details
    if room.is_active is not None:
        db_room.is_active = room.is_active
    
    db.commit()
    db.refresh(db_room)
    log_operation(db, "教室管理", "修改",  f"成功更新教室: {db_room.code} - {db_room.name}", current_user.username)
    return db_room

@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        log_operation(db, "教室管理", "删除教室", f"教室ID: {room_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="教室不存在")
    
    if db_room.schedules:
        log_operation(db, "教室管理", "删除教室", f"教室 {db_room.code} - {db_room.name} 已关联课程安排，无法删除", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="该教室已有课程安排，无法删除")
    
    db.delete(db_room)
    db.commit()
    log_operation(db, "教室管理", "删除", f"成功删除教室: {db_room.code} - {db_room.name}", current_user.username, "WARNING")
    return {"message": "删除成功"}