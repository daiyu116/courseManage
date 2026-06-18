# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from database import get_db
from models import Holiday
from schemas import HolidayCreate, HolidayUpdate, Holiday as HolidaySchema, PaginatedHolidayResponse
from routers.auth import get_current_course_admin_user, User
from utils.logger import log_operation

router = APIRouter()

@router.get("/holidays", response_model=PaginatedHolidayResponse)
def get_holidays(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """获取节假日列表"""
    query = db.query(Holiday).order_by(Holiday.date.asc())
    total = query.count()
    holidays = query.offset(skip).limit(limit).all()
    
    # 转换日期格式为字符串
    result = []
    for holiday in holidays:
        result.append(HolidaySchema(
            id=holiday.id,
            date=holiday.date.strftime("%Y-%m-%d") if isinstance(holiday.date, date) else str(holiday.date),
            name=holiday.name,
            description=holiday.description,
            created_at=holiday.created_at,
            updated_at=holiday.updated_at
        ))
    
    return {
        "items": result,
        "total": total
    }

@router.post("/holidays", response_model=HolidaySchema)
def create_holiday(
    holiday: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """创建节假日"""
    try:
        # 将字符串日期转换为 date 对象
        if isinstance(holiday.date, str):
            date_obj = datetime.strptime(holiday.date, "%Y-%m-%d").date()
        else:
            date_obj = holiday.date
        
        # 检查日期是否已存在
        existing = db.query(Holiday).filter(Holiday.date == date_obj).first()
        if existing:
            log_operation(db,"假期管理","创建",f"尝试创建已存在的节假日：{existing.name} ({existing.date})",current_user.username,"WARNING")
            raise HTTPException(status_code=400, detail="该日期已设置为节假日")
        
        db_holiday = Holiday(
            date=date_obj,
            name=holiday.name,
            description=holiday.description
        )
        db.add(db_holiday)
        db.commit()
        db.refresh(db_holiday)
        
        log_operation(db,"假期管理","创建",f"成功创建节假日：{db_holiday.name} ({db_holiday.date})",current_user.username)
        
        return HolidaySchema(
            id=db_holiday.id,
            date=db_holiday.date.strftime("%Y-%m-%d"),
            name=db_holiday.name,
            description=db_holiday.description,
            created_at=db_holiday.created_at,
            updated_at=db_holiday.updated_at
        )
    except ValueError as e:
        log_operation(db,"假期管理","创建",f"日期格式错误：{str(e)}",current_user.username,"WARNING")
        raise HTTPException(status_code=400, detail=f"日期格式错误：{str(e)}")
    except Exception as e:
        db.rollback()
        log_operation(db,"假期管理","创建",f"创建节假日失败：{str(e)}",current_user.username,"ERROR")
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")

@router.put("/holidays/{holiday_id}", response_model=HolidaySchema)
def update_holiday(
    holiday_id: int,
    holiday: HolidayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """更新节假日"""
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not db_holiday:
        log_operation(db,"假期管理","更新",f"节假日ID: {holiday_id} 不存在",current_user.username,"WARNING")
        raise HTTPException(status_code=404, detail="节假日不存在")
    
    if holiday.name is not None:
        db_holiday.name = holiday.name
    if holiday.description is not None:
        db_holiday.description = holiday.description
    
    db.commit()
    db.refresh(db_holiday)
    
    log_operation(db,"假期管理","更新",f"成功更新节假日：{db_holiday.name} ({db_holiday.date})",current_user.username)
    
    return HolidaySchema(
        id=db_holiday.id,
        date=db_holiday.date.strftime("%Y-%m-%d"),
        name=db_holiday.name,
        description=db_holiday.description,
        created_at=db_holiday.created_at,
        updated_at=db_holiday.updated_at
    )

@router.delete("/holidays/{holiday_id}")
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """删除节假日"""
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not db_holiday:
        log_operation(db,"假期管理","删除",f"节假日ID: {holiday_id} 不存在",current_user.username,"WARNING")
        raise HTTPException(status_code=404, detail="节假日不存在")
    
    db.delete(db_holiday)
    db.commit()
    
    log_operation(db,"假期管理","删除",f"成功删除节假日：{db_holiday.name} ({db_holiday.date})",current_user.username,"WARNING")
    
    return {"message": "删除成功"}