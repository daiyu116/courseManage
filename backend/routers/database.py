# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
from utils.logger import log_operation
from pydantic import BaseModel
from typing import Optional
import os
import json
import subprocess

router = APIRouter()

BACKUP_DIR = os.environ.get("BACKUP_DIR", "/app/backups")
BACKUP_CONFIG_KEY = "auto_backup_config"


def _get_backup_config(db) -> dict:
    from models import Settings
    settings = db.query(Settings).first()
    if not settings:
        return {"enabled": False, "frequency": "daily", "keep_count": 7}
    try:
        raw = getattr(settings, 'auto_backup_config', None)
        if raw:
            return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        pass
    return {"enabled": False, "frequency": "daily", "keep_count": 7}


def _set_backup_config(db, config: dict):
    from models import Settings
    settings = db.query(Settings).first()
    if not settings:
        raise HTTPException(status_code=500, detail="系统设置不存在")
    settings.auto_backup_config = json.dumps(config, ensure_ascii=False)
    db.commit()


def _perform_backup(db) -> str:
    """执行 pg_dump 备份，返回备份文件路径"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        db_user = os.environ.get("POSTGRES_USER", "cadbuser")
        db_pass = os.environ.get("POSTGRES_PASSWORD", "")
        db_host = os.environ.get("DB_HOST", "postgres")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DB", "cadb")
        if not db_pass:
            raise Exception("DATABASE_URL 或 POSTGRES_PASSWORD 环境变量未设置")
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    try:
        cmd = ["pg_dump", db_url, "--no-password", "--format=plain"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result.stdout)
    except FileNotFoundError:
        from io import StringIO
        import csv
        from sqlalchemy import text
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["-- Database Backup (fallback CSV)"])
        writer.writerow([f"-- Date: {datetime.now().isoformat()}"])
        writer.writerow([])
        tables_result = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = tables_result.fetchall()
        for table in tables:
            table_name = table[0]
            writer.writerow([f"-- Table: {table_name}"])
            columns_result = db.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"
            ))
            columns = columns_result.fetchall()
            column_names = [col[0] for col in columns]
            writer.writerow(column_names)
            rows_result = db.execute(text(f"SELECT * FROM {table_name}"))
            rows = rows_result.fetchall()
            for row in rows:
                writer.writerow([str(cell) if cell is not None else '' for cell in row])
            writer.writerow([])
        csv_path = filepath.replace(".sql", ".csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())
        filepath = csv_path

    config = _get_backup_config(db)
    keep_count = config.get("keep_count", 7)
    _cleanup_old_backups(keep_count)

    return filepath


def _cleanup_old_backups(keep_count: int):
    """清理旧备份文件，只保留最近 keep_count 个"""
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        files = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and (f.endswith(".sql") or f.endswith(".csv"))],
            reverse=True
        )
        for old_file in files[keep_count:]:
            old_path = os.path.join(BACKUP_DIR, old_file)
            try:
                os.remove(old_path)
            except Exception:
                pass
    except Exception:
        pass


class AutoBackupConfigRequest(BaseModel):
    enabled: bool = False
    frequency: str = "daily"
    keep_count: int = 7


@router.get("/backup")
async def backup_database(db: Session = Depends(get_db)):
    """手动备份数据库"""
    try:
        filepath = _perform_backup(db)
        filename = os.path.basename(filepath)
        from fastapi.responses import FileResponse
        log_operation(db, "数据库管理", "手动备份", f"数据库手动备份成功: {filename}")
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        log_operation(db, "数据库管理", "手动备份", f"数据库备份失败: {str(e)}", "system", "ERROR")
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")


@router.post("/restore")
async def restore_database(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """恢复数据库"""
    try:
        content = await file.read()
        import csv
        from io import StringIO

        csv_file = StringIO(content.decode('utf-8'))
        reader = csv.reader(csv_file)

        current_table = None
        columns = []

        for row in reader:
            if not row or row[0].startswith('--'):
                continue
            if row[0].startswith('Table:'):
                current_table = row[0].replace('Table: ', '')
                continue
            if current_table and row[0] not in ['id', 'created_at', 'updated_at']:
                columns = row
                continue
            if current_table and columns and len(row) == len(columns):
                try:
                    insert_query = f"INSERT INTO {current_table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
                    db.execute(insert_query, row)
                except Exception as e:
                    log_operation(db, "数据库管理", "恢复", f"插入数据到 {current_table} 失败: {str(e)}", "system", "ERROR")

        db.commit()
        log_operation(db, "数据库管理", "恢复", "数据库恢复成功", "system", "INFO")
        return {"message": "数据库恢复成功"}
    except Exception as e:
        db.rollback()
        log_operation(db, "数据库管理", "恢复", f"数据库恢复失败: {str(e)}", "system", "ERROR")
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")


@router.get("/auto-backup/config")
async def get_auto_backup_config(db: Session = Depends(get_db)):
    """获取自动备份配置"""
    config = _get_backup_config(db)
    return config


@router.post("/auto-backup/config")
async def set_auto_backup_config(request: AutoBackupConfigRequest, db: Session = Depends(get_db)):
    """设置自动备份配置"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('database_management', db):
        raise HTTPException(status_code=403, detail="数据库管理功能未授权，请先获取授权")

    if request.frequency not in ("daily", "every_6_hours", "every_12_hours", "weekly"):
        raise HTTPException(status_code=400, detail="不支持的备份频率")
    if request.keep_count < 1 or request.keep_count > 90:
        raise HTTPException(status_code=400, detail="保留数量需在1-90之间")

    config = {
        "enabled": request.enabled,
        "frequency": request.frequency,
        "keep_count": request.keep_count,
    }
    _set_backup_config(db, config)
    _sync_backup_scheduler()
    log_operation(db, "数据库管理", "自动备份配置", f"更新自动备份配置: enabled={config['enabled']}, frequency={config['frequency']}, keep_count={config['keep_count']}")
    return {"status": "success", "config": config}


@router.get("/auto-backup/list")
async def list_auto_backups(db: Session = Depends(get_db)):
    """获取自动备份文件列表"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('database_management', db):
        raise HTTPException(status_code=403, detail="数据库管理功能未授权，请先获取授权")

    backups = []
    if os.path.exists(BACKUP_DIR):
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if f.startswith("backup_") and (f.endswith(".sql") or f.endswith(".csv")):
                filepath = os.path.join(BACKUP_DIR, f)
                try:
                    stat = os.stat(filepath)
                    backups.append({
                        "filename": f,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "type": "sql" if f.endswith(".sql") else "csv",
                    })
                except Exception:
                    pass
    return {"backups": backups, "backup_dir": BACKUP_DIR}


@router.get("/auto-backup/download/{filename}")
async def download_backup(filename: str, db: Session = Depends(get_db)):
    """下载指定备份文件"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('database_management', db):
        raise HTTPException(status_code=403, detail="数据库管理功能未授权，请先获取授权")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    from fastapi.responses import FileResponse
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.delete("/auto-backup/{filename}")
async def delete_backup(filename: str, db: Session = Depends(get_db)):
    """删除指定备份文件"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('database_management', db):
        raise HTTPException(status_code=403, detail="数据库管理功能未授权，请先获取授权")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    os.remove(filepath)
    log_operation(db, "数据库管理", "删除备份", f"已删除备份文件: {filename}")
    return {"status": "success"}


@router.post("/auto-backup/trigger")
async def trigger_manual_auto_backup(db: Session = Depends(get_db)):
    """手动触发一次自动备份（存到备份目录而非下载）"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('database_management', db):
        raise HTTPException(status_code=403, detail="数据库管理功能未授权，请先获取授权")

    try:
        filepath = _perform_backup(db)
        filename = os.path.basename(filepath)
        log_operation(db, "数据库管理", "手动触发备份", f"备份成功: {filename}")
        return {"status": "success", "filename": filename}
    except Exception as e:
        import traceback
        traceback.print_exc()
        log_operation(db, "数据库管理", "手动触发备份", f"备份失败: {str(e)}", "system", "ERROR")
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")


def _sync_backup_scheduler():
    """同步自动备份定时任务（从配置读取并注册/移除 APScheduler 任务）"""
    try:
        from utils.remainder import scheduler, BEIJING_TZ
        from apscheduler.triggers.cron import CronTrigger

        db = SessionLocal()
        try:
            config = _get_backup_config(db)
            job_id = "auto_database_backup"

            existing = scheduler.get_job(job_id)
            if existing:
                scheduler.remove_job(job_id)

            if config.get("enabled"):
                freq = config.get("frequency", "daily")
                if freq == "every_6_hours":
                    trigger = CronTrigger(hour="0,6,12,18", minute=0, timezone=BEIJING_TZ)
                elif freq == "every_12_hours":
                    trigger = CronTrigger(hour="0,12", minute=0, timezone=BEIJING_TZ)
                elif freq == "weekly":
                    trigger = CronTrigger(day_of_week="mon", hour=2, minute=0, timezone=BEIJING_TZ)
                else:
                    trigger = CronTrigger(hour=2, minute=0, timezone=BEIJING_TZ)

                scheduler.add_job(
                    _scheduled_backup_job,
                    trigger,
                    id=job_id,
                    name="自动数据库备份",
                    replace_existing=True,
                )
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger("auto_backup").error(f"同步备份定时任务失败: {e}")


def _scheduled_backup_job():
    """APScheduler 定时执行的备份任务"""
    lock_fd = None
    acquired = False
    try:
        lock_fd, acquired = _acquire_backup_lock()
        if not acquired:
            return
        db = SessionLocal()
        try:
            config = _get_backup_config(db)
            if not config.get("enabled"):
                return
            filepath = _perform_backup(db)
            filename = os.path.basename(filepath)
            log_operation(db, "数据库管理", "自动备份", f"自动备份成功: {filename}")
        finally:
            db.close()
    except Exception as e:
        import logging
        import traceback
        traceback.print_exc()
        logging.getLogger("auto_backup").error(f"自动备份失败: {e}")
    finally:
        if lock_fd:
            try:
                lock_fd.close()
            except Exception:
                pass


def _acquire_backup_lock():
    """跨进程文件锁，防止多 worker 同时执行备份"""
    import tempfile
    lock_file = os.path.join(tempfile.gettempdir(), 'course_arrange_backup.lock')
    try:
        import fcntl
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd, True
    except (IOError, OSError, ImportError):
        try:
            import msvcrt
            lock_fd = open(lock_file, 'w')
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
            return lock_fd, True
        except (IOError, OSError):
            return None, False


from database import SessionLocal