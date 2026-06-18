# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import FastAPI, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse
from sqlalchemy import inspect, text
from database import engine, Base, SessionLocal, get_pool_status
from routers import auth, logs, database, settings, wechat, email
from routers import courses, teachers, students, classes, rooms, leaves, conditions, holidays
from routers import fees, grades, schedules, statistics
from routers import smart_command, smart_command_examples
from routers import license
from routers import evaluations
from utils.logger import log_operation
from routers.auth import get_current_system_admin_user, User
from routers.license import _check_premium_feature
from utils.license import FEATURE_NAMES
import uuid
import os
from pathlib import Path
from utils.remainder import init_scheduler, shutdown_scheduler
from migrate_add_smart_command_examples import add_smart_command_examples
from migrate_add_operation_managers import add_operation_managers
from migrate_add_schedule_type import add_schedule_type
from migrate_add_dashboard_indexes import add_performance_indexes
from migrate_add_ldap_config import migrate_add_ldap_config
from migrate_add_makeup_fields import migrate_add_makeup_fields
from migrate_add_payment_method import migrate_add_payment_method
from migrate_add_course_config import migrate_add_course_config
from migrate_add_license import migrate_add_license_fields
from migrate_add_evaluation import migrate_evaluation_managers

import threading
import time
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Course Management API", version="2.0.0")

# 创建上传目录
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

def monitor_connection_pool_periodically():
    """定期监控连接池状态"""
    while True:
        try:
            status = get_pool_status()
            logger.info(
                f"DB Pool Status - "
                f"Size: {status['pool_size']}, "
                f"CheckedIn: {status['checked_in']}, "
                f"CheckedOut: {status['checked_out']}, "
                f"Overflow: {status['overflow']}"
            )
        except Exception as e:
            logger.error(f"Failed to monitor connection pool: {e}")
        
        time.sleep(300)

@app.on_event("startup")
async def startup_event():
    """应用启动时添加日志"""
    from utils.license import verify_compiled_modules
    integrity = verify_compiled_modules()
    if not integrity["valid"]:
        for mod_name, info in integrity["details"].items():
            if info.get("warning"):
                logger.warning(f"Module integrity: {mod_name} - {info['warning']}")
        logger.warning("Some critical modules are not compiled - running in development mode")
    else:
        logger.info("All critical modules verified as compiled binaries")

    db = SessionLocal()
    try:
        log_operation(db, "应用系统", "状态变化", "系统启动")
    finally:
        db.close()
    
    init_scheduler()
    
    from routers.database import _sync_backup_scheduler
    _sync_backup_scheduler()
    
    monitor_thread = threading.Thread(
        target=monitor_connection_pool_periodically,
        daemon=True,
        name="DBPoolMonitor"
    )
    monitor_thread.start()
    logger.info("Database pool monitor thread started")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    shutdown_scheduler()
    db = SessionLocal()
    try:
        log_operation(db, "应用系统", "状态变化", "系统关闭")
        
        final_status = get_pool_status()
        logger.info(f"Final DB Pool Status: {final_status}")
    finally:
        db.close()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:18080,http://127.0.0.1:18080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

PREMIUM_PATH_MAP = {
    "/api/grades": "grade_trend",
    "/api/fees": "fee_management",
    "/api/schedules/optimize": "smart_scheduling",
    "/api/wechat": "wechat_notify",
    "/api/smart-command": "smart_command",
    "/api/smart-command-examples": "smart_command",
    "/api/statistics/dashboard": "dashboard_view",
    "/api/database": "database_management",
    "/api/evaluations": "student_evaluation",
}

@app.middleware("http")
async def premium_feature_guard(request: Request, call_next):
    path = request.url.path
    for path_prefix, feature in PREMIUM_PATH_MAP.items():
        if path.startswith(path_prefix):
            db = SessionLocal()
            try:
                if not _check_premium_feature(feature, db):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"功能 '{FEATURE_NAMES.get(feature, feature)}' 需要授权，请在系统授权管理中激活"},
                    )
            finally:
                db.close()
            break
    return await call_next(request)

Base.metadata.create_all(bind=engine)
migrate_evaluation_managers()

def run_migrations():
    from sqlalchemy import text
    insp = inspect(engine)
    if 'users' in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns('users')]
        if 'must_change_password' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE'))
                conn.commit()
    if 'settings' in insp.get_table_names():
        columns = [col['name'] for col in insp.get_columns('settings')]
        if 'open_registration_enabled' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN open_registration_enabled BOOLEAN DEFAULT FALSE'))
                conn.execute(text('ALTER TABLE settings ADD COLUMN open_registration_expiry TIMESTAMP NULL'))
                conn.commit()
        if 'session_timeout_minutes' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN session_timeout_minutes INTEGER DEFAULT 1440'))
                conn.commit()
        if 'referral_code' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN referral_code VARCHAR(64) NULL UNIQUE'))
                conn.commit()
        if 'referral_threshold' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN referral_threshold FLOAT DEFAULT 0'))
                conn.commit()
        if 'referral_activated' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN referral_activated BOOLEAN DEFAULT FALSE'))
                conn.commit()
        if 'total_spending' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN total_spending FLOAT DEFAULT 0'))
                conn.commit()
        if 'discount_percent' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN discount_percent FLOAT DEFAULT 0'))
                conn.commit()
        if 'rebate_percent' not in columns:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE settings ADD COLUMN rebate_percent FLOAT DEFAULT 0'))
                conn.commit()
        else:
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_name='settings' AND column_name='rebate_percent'"
                ))
                row = result.fetchone()
                if row and row[0] != 'double precision':
                    conn.execute(text('ALTER TABLE settings ALTER COLUMN rebate_percent DROP DEFAULT'))
                    conn.execute(text("ALTER TABLE settings ALTER COLUMN rebate_percent TYPE FLOAT USING CASE WHEN rebate_percent='' OR rebate_percent IS NULL THEN 0 ELSE rebate_percent::FLOAT END"))
                    conn.execute(text('ALTER TABLE settings ALTER COLUMN rebate_percent SET DEFAULT 0'))
                    conn.commit()
        if 'contact_person' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE settings ADD COLUMN contact_person VARCHAR(100) DEFAULT ''"))
                conn.execute(text("ALTER TABLE settings ADD COLUMN contact_phone VARCHAR(20) DEFAULT ''"))
                conn.execute(text("ALTER TABLE settings ADD COLUMN contact_email VARCHAR(100) DEFAULT ''"))
                conn.execute(text("ALTER TABLE settings ADD COLUMN contact_wechat VARCHAR(100) DEFAULT ''"))
                conn.commit()

run_migrations()

# 创建节假日表
def create_holidays_table():
    """创建节假日表"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if 'holidays' not in tables:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE holidays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        
        print("已创建 holidays 表")
    else:
        print("holidays 表已存在")

# 检查并添加 execution_status 字段到 schedules 表
def add_execution_status_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('schedules')]
    if 'execution_status' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS execution_status VARCHAR(20) DEFAULT 'pending'"))            
            conn.commit()
        print("已添加字段 execution_status 到表 schedules")
    else:
        print("字段 execution_status 已存在于表 schedules")

# 检查并添加 cancel_reason 字段到 schedules 表
def add_cancel_reason_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('schedules')]
    if 'cancel_reason' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS cancel_reason TEXT DEFAULT ''"))
            conn.commit()
        print("已添加字段 cancel_reason 到表 schedules")
    else:
        print("字段 cancel_reason 已存在于表 schedules")
 
# 检查并添加 postpone_reason 字段到 schedules 表
def add_postpone_reason_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('schedules')]
    if 'postpone_reason' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS postpone_reason TEXT DEFAULT ''"))
            conn.commit()
        print("已添加字段 postpone_reason 到表 schedules")
    else:
        print("字段 postpone_reason 已存在于表 schedules")

# 检查并添加 refund_date 字段到 fee_logs 表
def add_refund_date_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('fee_logs')]
    if 'refund_date' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE fee_logs ADD COLUMN IF NOT EXISTS refund_date TIMESTAMP"))
            conn.commit()
        print("已添加字段 refund_date 到表 fee_logs")
    else:
        print("字段 refund_date 已存在于表 fee_logs")

# 迁移退费记录的payment_date到refund_date
def migrate_refund_dates():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('fee_logs')]
    if 'refund_date' in columns:
        with engine.connect() as conn:
            # 将退费记录的payment_date复制到refund_date
            conn.execute(text("UPDATE fee_logs SET refund_date = payment_date WHERE log_type = 'refund' AND payment_date IS NOT NULL AND refund_date IS NULL"))
            conn.commit()
            # 查看更新了多少条记录
            result = conn.execute(text("SELECT COUNT(*) FROM fee_logs WHERE log_type = 'refund' AND refund_date IS NOT NULL"))
            count = result.fetchone()[0]
            print(f"已迁移 {count} 条退费记录的日期")

# 检查并添加微信配置字段到 settings 表
def add_wechat_config_columns():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('settings')]
    
    if 'wechat_webhook_config' not in columns:
        with engine.connect() as conn:
            # PostgreSQL 使用 TEXT 类型存储 JSON 字符串
            conn.execute(text("ALTER TABLE settings ADD COLUMN wechat_webhook_config TEXT"))
            conn.commit()
        print("已添加字段 wechat_webhook_config 到表 settings")
    else:
        print("字段 wechat_webhook_config 已存在于表 settings")

    if 'site_url' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE settings ADD COLUMN site_url VARCHAR(500)"))
            conn.commit()
        print("已添加字段 site_url 到表 settings")
    else:
        print("字段 site_url 已存在于表 settings")

# 检查并添加作业安排字段到 schedules 表
def add_homework_columns():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('schedules')]
    
    if 'homework_regular' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE schedules ADD COLUMN homework_regular TEXT DEFAULT ''"))
            conn.commit()
        print("已添加字段 homework_regular 到表 schedules")
    else:
        print("字段 homework_regular 已存在于表 schedules")
    
    if 'homework_images' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE schedules ADD COLUMN homework_images TEXT DEFAULT ''"))
            conn.commit()
        print("已添加字段 homework_images 到表 schedules")
    else:
        print("字段 homework_images 已存在于表 schedules")

# 在应用启动时执行迁移
add_execution_status_column()
add_cancel_reason_column()
add_postpone_reason_column()
add_refund_date_column()
migrate_refund_dates()
create_holidays_table()
add_wechat_config_columns()
add_homework_columns()
add_smart_command_examples()
add_operation_managers()
add_schedule_type()
add_performance_indexes()
migrate_add_ldap_config()
migrate_add_makeup_fields()
migrate_add_payment_method()
migrate_add_course_config()
migrate_add_license_fields()

def add_auto_backup_config_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('settings')]
    if 'auto_backup_config' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE settings ADD COLUMN auto_backup_config TEXT DEFAULT '{}'"))
            conn.commit()
        print("已添加字段 auto_backup_config 到表 settings")
    else:
        print("字段 auto_backup_config 已存在于表 settings")

add_auto_backup_config_column()

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(courses.router, prefix="/api/courses", tags=["科目管理"])
app.include_router(teachers.router, prefix="/api/teachers", tags=["导师管理"])
app.include_router(classes.router, prefix="/api/classes", tags=["班级管理"])
app.include_router(students.router, prefix="/api/students", tags=["学员管理"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["教室管理"])
app.include_router(leaves.router, prefix="/api/leaves", tags=["请假管理"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["排课管理"])
app.include_router(conditions.router, prefix="/api/conditions", tags=["条件管理"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(database.router, prefix="/api/database", tags=["database"])
app.include_router(fees.router, prefix="/api/fees", tags=["课费管理"])
app.include_router(settings.router, prefix="/api/settings", tags=["站点参数"])
app.include_router(grades.router, prefix="/api/grades", tags=["成绩管理"])
app.include_router(holidays.router, prefix="/api/holidays", tags=["节假日管理"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["运营统计"])
app.include_router(smart_command.router, prefix="/api", tags=["智能指令"])
app.include_router(smart_command_examples.router, prefix="/api/smart-command-examples", tags=["智能指令示例管理"])
app.include_router(wechat.router, prefix="/api/wechat", tags=["微信通知"])
app.include_router(email.router, prefix="/api/email", tags=["邮件通知"])
app.include_router(license.router, prefix="/api", tags=["系统授权"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["学员评价管理"])


# 静态文件服务
#print(f"DEBUG: 静态文件服务 - 上传目录: {UPLOAD_DIR.absolute()}")
#print(f"DEBUG: 静态文件服务 - 目录存在: {UPLOAD_DIR.exists()}")
#print(f"DEBUG: 静态文件服务 - 挂载路径: /uploads")
#print(f"DEBUG: 静态文件服务 - 实际目录: {str(UPLOAD_DIR)}")
#print(f"DEBUG: ============================================")
# 手动处理静态文件请求
@app.get("/uploads/{filename}")
async def serve_static_file(filename: str):
    """手动处理静态文件请求"""
    try:
        safe_name = Path(filename).name
        if safe_name != filename:
            return JSONResponse(content={"error": "非法文件名"}, status_code=400)
        file_path = (UPLOAD_DIR / safe_name).resolve()
        if not str(file_path).startswith(str(UPLOAD_DIR.resolve())):
            return JSONResponse(content={"error": "非法路径"}, status_code=400)
        
        if not file_path.exists():
            return JSONResponse(content={"error": f"文件不存在"}, status_code=404)
        
        return FileResponse(path=str(file_path), filename=safe_name)
    except Exception as e:
        return JSONResponse(content={"error": "文件访问失败"}, status_code=500)

@app.get("/")
def read_root():
    return {"message": "Course Management API is running"}

@app.get("/api/system-info")
def get_system_info():
    """获取系统配置信息（端口等）"""
    import os
    return {
        "backend_port": int(os.getenv("BACKEND_PORT", "35000")),
        "frontend_port": int(os.getenv("FRONTEND_PORT", "18080")),
    }

@app.get("/api/public/open-registration-status")
def get_public_open_registration_status():
    from models import Settings
    from datetime import datetime
    db = SessionLocal()
    try:
        settings = db.query(Settings).first()
        if not settings:
            return {"enabled": False}
        enabled = getattr(settings, 'open_registration_enabled', False)
        expiry = getattr(settings, 'open_registration_expiry', None)
        if not enabled:
            return {"enabled": False}
        if expiry and datetime.now() > expiry:
            settings.open_registration_enabled = False
            settings.open_registration_expiry = None
            db.commit()
            return {"enabled": False}
        remaining = None
        if expiry:
            remaining = int((expiry - datetime.now()).total_seconds())
        return {
            "enabled": True,
            "expiry": expiry.isoformat() if expiry else None,
            "remaining_seconds": remaining
        }
    except Exception as e:
        import logging
        logging.getLogger("open_registration").error(f"检查开放注册状态失败: {e}")
        return {"enabled": False}
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "healthy"}
 
@app.get("/api/uploads/test")
def test_uploads():
    """测试上传目录是否可访问"""
    try:
        files = list(UPLOAD_DIR.glob("*"))
        file_details = []
        for f in files[:10]:
            file_details.append({
                "name": f.name,
                "size": f.stat().st_size if f.exists() else 0
            })
        return {
            "exists": UPLOAD_DIR.exists(),
            "file_count": len(files),
            "files": file_details
        }
    except Exception as e:
        return {"error": "目录访问失败"}
 
@app.get("/api/uploads/test/{filename}")
def test_file_access(filename: str):
    """测试特定文件是否可访问"""
    try:
        safe_name = Path(filename).name
        if safe_name != filename:
            return {"error": "非法文件名"}
        file_path = (UPLOAD_DIR / safe_name).resolve()
        if not str(file_path).startswith(str(UPLOAD_DIR.resolve())):
            return {"error": "非法路径"}
        if not file_path.exists():
            return {"error": "文件不存在"}
        return {
            "filename": safe_name,
            "exists": True,
            "size": file_path.stat().st_size,
            "url": f"/uploads/{safe_name}"
        }
    except Exception as e:
        return {"error": "文件访问失败"}
 
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_system_admin_user)):
    """上传文件接口"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'}
    MAX_FILE_SIZE = 50 * 1024 * 1024
    try:
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if not file_extension or file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{file_extension}")
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超过限制(50MB)")
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        file_url = f"/uploads/{unique_filename}"
        return JSONResponse(content={"url": file_url})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件上传失败")