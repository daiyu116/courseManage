# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Optional
from database import get_db
from models import Log
from utils.logger import log_operation
import csv
import os
import io

router = APIRouter()

LOG_BACKUP_DIR = os.environ.get("BACKUP_DIR", "/app/backups")


@router.get("")
async def get_logs(
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    user: Optional[str] = Query(None, description="用户名"),
    level: Optional[str] = Query(None, description="日志级别（DEBUG, INFO, WARNING, ERROR）"),
    search: Optional[str] = Query(None, description="内容模糊查询"),
    db: Session = Depends(get_db)
):
    """获取系统日志"""
    query = db.query(Log)
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Log.timestamp >= start_datetime)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            end_datetime = end_datetime + timedelta(days=1)
            query = query.filter(Log.timestamp < end_datetime)
        except ValueError:
            pass
    
    if user:
        query = query.filter(Log.user.ilike(f"%{user}%"))
    
    if level:
        query = query.filter(Log.level.ilike(level))
    
    if search:
        query = query.filter(Log.message.like(f"%{search}%"))
    
    total = query.count()
    logs = query.order_by(Log.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "user": log.user
            }
            for log in logs
        ],
        "total": total
    }


def _build_log_query(db, start_date=None, end_date=None, user=None, level=None, search=None):
    query = db.query(Log)
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Log.timestamp >= start_datetime)
        except ValueError:
            pass
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            end_datetime = end_datetime + timedelta(days=1)
            query = query.filter(Log.timestamp < end_datetime)
        except ValueError:
            pass
    if user:
        query = query.filter(Log.user.ilike(f"%{user}%"))
    if level:
        query = query.filter(Log.level.ilike(level))
    if search:
        query = query.filter(Log.message.like(f"%{search}%"))
    return query


def _export_logs_to_csv(db, start_date=None, end_date=None, user=None, level=None, search=None) -> str:
    query = _build_log_query(db, start_date, end_date, user, level, search)
    logs = query.order_by(Log.timestamp.desc()).all()

    os.makedirs(LOG_BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs_backup_{timestamp}.csv"
    filepath = os.path.join(LOG_BACKUP_DIR, filename)

    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "时间", "级别", "内容", "操作用户"])
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.isoformat() if log.timestamp else "",
                log.level or "",
                log.message or "",
                log.user or "",
            ])
    return filepath


@router.post("/backup")
async def backup_logs(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    user: Optional[str] = Query(None, description="用户名"),
    level: Optional[str] = Query(None, description="日志级别"),
    search: Optional[str] = Query(None, description="内容模糊查询"),
    db: Session = Depends(get_db)
):
    """备份日志（导出为CSV），支持按筛选条件备份"""
    query = _build_log_query(db, start_date, end_date, user, level, search)
    count = query.count()
    if count == 0:
        return {"status": "success", "message": "没有符合条件的日志需要备份", "count": 0}

    filepath = _export_logs_to_csv(db, start_date, end_date, user, level, search)
    filename = os.path.basename(filepath)
    log_operation(db, "系统日志", "日志备份", f"备份日志 {count} 条，文件: {filename}")
    return {
        "status": "success",
        "message": f"成功备份 {count} 条日志",
        "count": count,
        "filename": filename,
    }


@router.get("/backup/download/{filename}")
async def download_log_backup(filename: str, db: Session = Depends(get_db)):
    """下载日志备份文件"""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    filepath = os.path.join(LOG_BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv"
    )


@router.get("/backup/list")
async def list_log_backups(db: Session = Depends(get_db)):
    """获取日志备份文件列表"""
    backups = []
    if os.path.exists(LOG_BACKUP_DIR):
        for f in sorted(os.listdir(LOG_BACKUP_DIR), reverse=True):
            if f.startswith("logs_backup_") and f.endswith(".csv"):
                filepath = os.path.join(LOG_BACKUP_DIR, f)
                try:
                    stat = os.stat(filepath)
                    backups.append({
                        "filename": f,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    })
                except Exception:
                    pass
    return {"backups": backups}


@router.get("/backup/view/{filename}")
async def view_log_backup(
    filename: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    search: Optional[str] = Query(None, description="内容模糊查询"),
    db: Session = Depends(get_db)
):
    """查看归档日志文件内容（分页）"""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    filepath = os.path.join(LOG_BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    rows = []
    try:
        with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if level and row.get("级别", "") != level:
                    continue
                if search and search.lower() not in row.get("内容", "").lower():
                    continue
                rows.append({
                    "id": row.get("ID", ""),
                    "timestamp": row.get("时间", ""),
                    "level": row.get("级别", ""),
                    "message": row.get("内容", ""),
                    "user": row.get("操作用户", ""),
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取归档文件失败: {str(e)}")

    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": rows[start:end],
        "total": total,
        "filename": filename,
    }


@router.delete("/backup/{filename}")
async def delete_log_backup(filename: str, db: Session = Depends(get_db)):
    """删除日志备份文件"""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    filepath = os.path.join(LOG_BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    os.remove(filepath)
    log_operation(db, "系统日志", "删除日志备份", f"删除备份文件: {filename}")
    return {"status": "success", "message": "备份文件已删除"}


@router.delete("/clear")
async def clear_logs(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    user: Optional[str] = Query(None, description="用户名"),
    level: Optional[str] = Query(None, description="日志级别"),
    search: Optional[str] = Query(None, description="内容模糊查询"),
    db: Session = Depends(get_db)
):
    """清除日志（清除前自动备份）"""
    query = _build_log_query(db, start_date, end_date, user, level, search)
    count = query.count()
    if count == 0:
        return {"status": "success", "message": "没有符合条件的日志需要清除", "count": 0}

    filepath = _export_logs_to_csv(db, start_date, end_date, user, level, search)
    backup_filename = os.path.basename(filepath)

    try:
        query.delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清除日志失败: {str(e)}")

    log_operation(db, "系统日志", "日志清除", f"清除日志 {count} 条，自动备份至: {backup_filename}")
    return {
        "status": "success",
        "message": f"已清除 {count} 条日志，自动备份至 {backup_filename}",
        "count": count,
        "backup_filename": backup_filename,
    }


@router.get("/stats")
async def get_log_stats(db: Session = Depends(get_db)):
    """获取日志统计信息"""
    total = db.query(Log).count()
    from sqlalchemy import func
    level_stats = db.query(Log.level, func.count(Log.id)).group_by(Log.level).all()
    stats = {level: count for level, count in level_stats}
    return {"total": total, "level_stats": stats}