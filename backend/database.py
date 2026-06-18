# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import urlparse
import time
import logging

logger = logging.getLogger(__name__)

# 从环境变量中获取 DATABASE信息，并设置连接池参数
DATABASE_URL = os.getenv("DATABASE_URL")
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '1800'))

# 如果没有设置 DATABASE_URL，则使用默认值
if not DATABASE_URL:
    raise ValueError("环境变量未设置DATABASE_URL参数，请检查docker-compose配置文件,设置该参数后重新部署应用")

# 解析 DATABASE_URL 获取各个部分
parsed = urlparse(DATABASE_URL)
DB_USER = parsed.username
DB_PASSWORD = parsed.password
DB_HOST = parsed.hostname
DB_PORT = parsed.port
DB_NAME = parsed.path.lstrip('/')

# 重新拼接 DATABASE_URL（确保格式正确）
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=True,
    echo=False
)

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """连接检出时记录 - 用于监控和泄漏检测"""
    connection_record._checkout_time = time.time()
    pool_status = {
        'size': engine.pool.size(),
        'checkedout': engine.pool.checkedout(),
        'overflow': engine.pool.overflow()
    }
    logger.debug(f"Connection checked out. Pool status: {pool_status}")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """连接归还时记录 - 检测长时间持有的连接"""
    checkout_time = getattr(connection_record, '_checkout_time', None)
    if checkout_time:
        duration = time.time() - checkout_time
        if duration > 10:
            logger.warning(f"Long running connection detected: {duration:.2f}s")
        else:
            logger.debug(f"Connection checked in after {duration:.2f}s")

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """新连接创建时记录"""
    logger.info(f"New database connection created. Total pool size: {engine.pool.size()}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_pool_status():
    """获取当前连接池状态（可用于API端点）"""
    return {
        'pool_size': engine.pool.size(),
        'checked_in': engine.pool.checkedin(),
        'checked_out': engine.pool.checkedout(),
        'overflow': engine.pool.overflow(),
        'total_connections': engine.pool.size() + engine.pool.overflow()
    }