# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from datetime import datetime, date
from database import SessionLocal
from models import Holiday
from utils.logger import log_operation

def is_holiday(date_obj: datetime) -> bool:
    """判断给定日期是否为节假日（包括系统定义的节假日和自定义节假日）"""
    db = None
    try:
        from lunar_python import Solar
        
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
        
        # 首先检查自定义节假日
        db = SessionLocal()
        try:
            # 将 datetime 转换为 date 对象进行比较
            target_date = date_obj.date() if isinstance(date_obj, datetime) else date_obj
            custom_holiday = db.query(Holiday).filter(
                Holiday.date == target_date
            ).first()
            if custom_holiday:
                return True
        finally:
            db.close()
            db = None
        
        # 创建Solar对象
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        
        # 检查农历节日
        lunar_festivals = lunar.getFestivals()
        if lunar_festivals:
            return True
        
        # 检查公历节日
        solar_festivals = solar.getFestivals()
        if solar_festivals:
            return True
        
        return False
    except ImportError as e:
        # 如果lunar模块不存在，只检查自定义节假日
        print(f"[WARNING] lunar_python模块未安装，仅检查自定义节假日: {e}")
        try:
            if db is None:
                db = SessionLocal()
            target_date = date_obj.date() if isinstance(date_obj, datetime) else date_obj
            custom_holiday = db.query(Holiday).filter(
                Holiday.date == target_date
            ).first()
            if custom_holiday:
                return True
            return False
        except Exception as inner_e:
            print(f"[ERROR] 检查自定义节假日失败: {inner_e}")
            return False
        finally:
            if db:
                db.close()
    except Exception as e:
        print(f"[ERROR] 判断节假日失败: {str(e)}")
        if db:
            try:
                log_operation(db,"假期管理","判断节假日",f"判断节假日失败: {str(e)}","system","ERROR")
            except:
                pass
            finally:
                db.close()
        return False

def can_schedule_on_holiday(teacher_allow: bool, student_allow: bool) -> bool:
    """判断是否可以在节假日排课"""
    # 导师和学员都必须允许节假日排课
    return teacher_allow and student_allow