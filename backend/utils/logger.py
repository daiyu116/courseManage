# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from sqlalchemy.orm import Session
from datetime import datetime
from models import Log, Settings

def add_log(db: Session, level: str, message: str, user: str = None, send_wechat: bool = False):
    """添加日志记录"""
    try:
        # 获取日志配置
        settings = db.query(Settings).first()
        
        # 检查是否启用日志
        if settings and not settings.log_enabled:
            return
        
        # 检查日志级别
        if settings:
            min_level = settings.log_level
            log_levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            
            # 检查日志级别是否满足要求
            if log_levels.get(level, 1) < log_levels.get(min_level, 1):
                return
            
        log = Log(
            timestamp=datetime.now(),
            level=level,
            message=message,
            user=user or "system"
        )
        db.add(log)
        db.commit()
        
        # 如果需要发送微信通知
        if send_wechat:
            from utils.wechat_notifier import wechat_notifier
            settings = db.query(Settings).first()
            if settings and settings.wechat_webhook_url:
                wechat_notifier.webhook_url = settings.wechat_webhook_url
                wechat_notifier.send_text_message(f"【{level}】{message}")
                
    except Exception as e:
        print(f"Failed to add log: {e}")
        db.rollback()

def log_operation(db: Session, module: str, operation: str, details: str, user: str = None, level: str = "INFO"):
    """记录操作日志"""
    message = f"{module} - {operation}: {details}"
    add_log(db, level, message, user)

def log_debug(db: Session, message: str, user: str = None):
    """记录 DEBUG 日志"""
    add_log(db, "DEBUG", message, user)

def log_info(db: Session, message: str, user: str = None):
    """记录 INFO 日志"""
    add_log(db, "INFO", message, user)

def log_warning(db: Session, message: str, user: str = None):
    """记录 WARNING 日志"""
    add_log(db, "WARNING", message, user)

def log_error(db: Session, message: str, user: str = None):
    """记录 ERROR 日志"""
    add_log(db, "ERROR", message, user)