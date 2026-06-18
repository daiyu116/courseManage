# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.wechat_notifier import wechat_notifier
from database import get_db
from models import Settings, Schedule
from schemas import SettingsCreate, SettingsUpdate, Settings as SettingsSchema, EmailConfigRequest
from routers.auth import  get_current_system_admin_user, User
from utils.logger import log_operation
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date, timedelta
import requests
import json
import re
import os

router = APIRouter()

class TestWebhookRequest(BaseModel):
    webhook_url: str

class TestAIRequest(BaseModel):
    api_url: str
    api_key: str
    provider: str
    model: str
    timeout: int = 10

class TestLDAPRequest(BaseModel):
    server: str
    port: int = 389
    use_ssl: bool = False
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    user_search_base: str
    user_search_filter: str = '(uid={username})'
    user_dn_template: Optional[str] = None

def validate_api_url(url: str) -> bool:
    """验证API地址格式"""
    if not url:
        return False
    # 检查是否以http://或https://开头
    if not re.match(r'^https?://', url, re.IGNORECASE):
        return False
    # 检查是否包含有效的域名或IP
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
        return True
    except:
        return False

@router.post("/test-morning-reminder")
def test_morning_reminder(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试早上提醒功能"""
    from utils.remainder import check_and_send_morning_reminder
    
    log_operation(db, "系统配置", "手动测试", "管理员手动触发早上提醒测试", current_user.username, "INFO")
    
    try:
        # 手动触发早上提醒
        check_and_send_morning_reminder()
        return {"message": "早上提醒已触发，请查看日志确认发送结果"}
    except Exception as e:
        log_operation(db, "系统配置", "手动测试失败", f"错误: {str(e)}", current_user.username, "ERROR")
        import traceback
        log_operation(db, "系统配置", "手动测试失败", f"堆栈跟踪: {traceback.format_exc()}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")

@router.post("/test-evening-reminder")
def test_evening_reminder(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试晚上提醒功能"""
    from utils.remainder import check_and_send_evening_reminder
    
    log_operation(db, "系统配置", "手动测试", "管理员手动触发晚上提醒测试", current_user.username, "INFO")
    
    try:
        # 手动触发晚上提醒
        check_and_send_evening_reminder()
        return {"message": "晚上提醒已触发，请查看日志确认发送结果"}
    except Exception as e:
        log_operation(db, "系统配置", "手动测试失败", f"错误: {str(e)}", current_user.username, "ERROR")
        import traceback
        log_operation(db, "系统配置", "手动测试失败", f"堆栈跟踪: {traceback.format_exc()}", "system", "ERROR")
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")

@router.get("/today-schedules")
def get_today_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """获取今天的课程安排（用于调试）"""
    today = date.today()
    schedules = db.query(Schedule).filter(
        Schedule.start_date == today,
        Schedule.execution_status == 'pending'
    ).all()
    
    schedule_list = [{
        "id": s.id,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "course_name": s.course.name if s.course else "未知科目",
        "class_name": s.class_.name if s.class_ else "未知班级",
        "teacher_id": s.teacher_id,
        "class_id": s.class_id,
        "execution_status": s.execution_status
    } for s in schedules]
    
    log_operation(db, "系统配置", "查询", f"查询今日课程: 找到 {len(schedule_list)} 条", current_user.username, "INFO")
    
    return {
        "date": str(today),
        "count": len(schedule_list),
        "schedules": schedule_list
    }

@router.get("/tomorrow-schedules")
def get_tomorrow_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """获取明天的课程安排（用于调试）"""
    from datetime import timedelta
    tomorrow = date.today() + timedelta(days=1)
    schedules = db.query(Schedule).filter(
        Schedule.start_date == tomorrow,
        Schedule.execution_status == 'pending'
    ).all()
    
    schedule_list = [{
        "id": s.id,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "course_name": s.course.name if s.course else "未知科目",
        "class_name": s.class_.name if s.class_ else "未知班级",
        "teacher_id": s.teacher_id,
        "class_id": s.class_id,
        "execution_status": s.execution_status
    } for s in schedules]
    
    log_operation(db, "系统配置", "查询", f"查询明日课程: 找到 {len(schedule_list)} 条", current_user.username, "INFO")
    
    return {
        "date": str(tomorrow),
        "count": len(schedule_list),
        "schedules": schedule_list
    }

@router.get("", response_model=SettingsSchema)
def get_settings(db: Session = Depends(get_db)):
    """获取站点参数"""
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings(
            site_name="默认机构",
            site_logo="",
            site_url="",
            organization_website="",
            wechat_qrcode="",
            work_wechat_qrcode="",
            wechat_webhook_config="{}",
            notification_settings="{}",
            email_config="{}",
            email_notification_settings="{}",
            teacher_visibility_restricted=True,
            subject_teachers=[],
            fee_managers=[],
            grade_managers=[],
            evaluation_managers=[],
            operation_managers=[],
            schedule_edit_restricted=True,
            schedule_delete_restricted=True,
            log_enabled=True,
            log_level="INFO",
            log_debug_enabled=False,
            frontend_log_enabled=True,
            ai_config="{}",
            ldap_enabled=False,
            ldap_config="{}",
            hours_per_lesson=2.0,
            course_config="{}"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # 解析subject_teachers
    try:
        subject_teachers_list = json.loads(settings.subject_teachers) if settings.subject_teachers else []
        if not isinstance(subject_teachers_list, list):
            subject_teachers_list = []
    except (json.JSONDecodeError, TypeError):
        subject_teachers_list = []
    settings.subject_teachers = subject_teachers_list
    
    # 解析fee_managers
    try:
        fee_managers_list = json.loads(settings.fee_managers) if settings.fee_managers else []
        if not isinstance(fee_managers_list, list):
            fee_managers_list = []
    except (json.JSONDecodeError, TypeError):
        fee_managers_list = []
    settings.fee_managers = fee_managers_list

    # 解析grade_managers
    try:
        grade_managers_list = json.loads(settings.grade_managers) if settings.grade_managers else []
        if not isinstance(grade_managers_list, list):
            grade_managers_list = []
    except (json.JSONDecodeError, TypeError):
        grade_managers_list = []
    settings.grade_managers = grade_managers_list

    # 解析evaluation_managers
    try:
        evaluation_managers_list = json.loads(settings.evaluation_managers) if settings.evaluation_managers else []
        if not isinstance(evaluation_managers_list, list):
            evaluation_managers_list = []
    except (json.JSONDecodeError, TypeError):
        evaluation_managers_list = []
    settings.evaluation_managers = evaluation_managers_list

    settings.log_enabled = settings.log_enabled if settings.log_enabled is not None else True
    settings.log_level = settings.log_level or "INFO"

    if settings.open_registration_enabled and settings.open_registration_expiry and datetime.now() > settings.open_registration_expiry:
        settings.open_registration_enabled = False
        settings.open_registration_expiry = None
        db.commit()
        db.refresh(settings)
        log_operation(db, "系统配置", "自动关闭", "开放注册已过期，自动关闭", "system", "WARNING")

    # 解析operation_managers
    try:
        operation_managers_list = json.loads(settings.operation_managers) if settings.operation_managers else []
        if not isinstance(operation_managers_list, list):
            operation_managers_list = []
    except (json.JSONDecodeError, TypeError):
        operation_managers_list = []
    settings.operation_managers = operation_managers_list

    # 同步配置到全局通知器
    from utils.wechat_notifier import wechat_notifier
    wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
    return settings

@router.get("/check-scheduler-status")
def check_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """检查定时任务状态"""
    from utils.remainder import scheduler
    
    jobs = scheduler.get_jobs()
    job_list = []
    for job in jobs:
        job_list.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    log_operation(db, "系统配置", "查询", f"查询定时任务状态: 共 {len(job_list)} 个任务", current_user.username, "INFO")
    
    return {
        "scheduler_running": scheduler.running,
        "jobs_count": len(job_list),
        "jobs": job_list
    }

@router.put("", response_model=SettingsSchema)
def update_settings(
    settings_data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """更新站点参数"""
    settings = db.query(Settings).first()
    if not settings:
        log_operation(db, "系统配置", "修改失败", "尝试修改站点参数但未找到现有配置", current_user.username, "ERROR")
        raise HTTPException(status_code=404, detail="站点参数不存在")
    
    if settings_data.site_name is not None:
        if not settings_data.site_name or not settings_data.site_name.strip():
            raise HTTPException(status_code=400, detail="机构名称不能为空")
        settings.site_name = settings_data.site_name
    
    if settings_data.site_url is not None:
        # 验证并处理 site_url（内网IP）
        raw_ip = settings_data.site_url.strip()
        if not raw_ip:
            raise HTTPException(status_code=400, detail="本站内网IP不能为空")
        
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        if not (re.match(ip_pattern, raw_ip) or re.match(domain_pattern, raw_ip)):
            raise HTTPException(status_code=400, detail="请输入有效的内网IP地址或域名")
        
        # 获取后端端口（从环境变量）
        backend_port = int(os.getenv("BACKEND_PORT", "35000"))
        
        # 自动拼接完整的 URL
        settings.site_url = f"http://{raw_ip}:{backend_port}"
    
    if settings_data.site_logo is not None:
        settings.site_logo = settings_data.site_logo
    if settings_data.organization_website is not None:
        settings.organization_website = settings_data.organization_website
    if settings_data.wechat_qrcode is not None:
        settings.wechat_qrcode = settings_data.wechat_qrcode
    if settings_data.work_wechat_qrcode is not None:
        settings.work_wechat_qrcode = settings_data.work_wechat_qrcode
    if settings_data.wechat_webhook_config is not None:
        settings.wechat_webhook_config = settings_data.wechat_webhook_config
    if settings_data.log_enabled is not None:
        settings.log_enabled = settings_data.log_enabled
    if settings_data.log_level is not None:
        settings.log_level = settings_data.log_level
    if settings_data.teacher_visibility_restricted is not None:
        settings.teacher_visibility_restricted = settings_data.teacher_visibility_restricted
    if settings_data.subject_teachers is not None:
        settings.subject_teachers = json.dumps(settings_data.subject_teachers)
    if settings_data.fee_managers is not None:
        settings.fee_managers = json.dumps(settings_data.fee_managers)
    if settings_data.grade_managers is not None:
        settings.grade_managers = json.dumps(settings_data.grade_managers)
    if settings_data.evaluation_managers is not None:
        settings.evaluation_managers = json.dumps(settings_data.evaluation_managers)
    if settings_data.operation_managers is not None:
        settings.operation_managers = json.dumps(settings_data.operation_managers)
    if settings_data.schedule_edit_restricted is not None:
        settings.schedule_edit_restricted = settings_data.schedule_edit_restricted
    if settings_data.schedule_delete_restricted is not None:
        settings.schedule_delete_restricted = settings_data.schedule_delete_restricted
    if settings_data.ai_config is not None:
        current_ai = settings.ai_config or '{}'
        try:
            current_ai_parsed = json.loads(current_ai) if current_ai else {}
            new_ai_parsed = json.loads(settings_data.ai_config) if settings_data.ai_config else {}
        except (json.JSONDecodeError, TypeError):
            current_ai_parsed = {}
            new_ai_parsed = {}
        if new_ai_parsed.get('enabled') and not current_ai_parsed.get('enabled'):
            from routers.license import _check_premium_feature
            if not _check_premium_feature('smart_command', db):
                raise HTTPException(status_code=403, detail="智能指令功能需要购买授权后才能使用")
        settings.ai_config = settings_data.ai_config
        log_operation(db, "系统配置", "修改", f"更新人工智能配置", current_user.username, "INFO")
    if settings_data.wechat_webhook_config is not None:
        current_wc = settings.wechat_webhook_config or '{}'
        try:
            current_wc_parsed = json.loads(current_wc) if current_wc else {}
            new_wc_parsed = json.loads(settings_data.wechat_webhook_config) if settings_data.wechat_webhook_config else {}
        except (json.JSONDecodeError, TypeError):
            current_wc_parsed = {}
            new_wc_parsed = {}
        if new_wc_parsed.get('enabled') and not current_wc_parsed.get('enabled'):
            from routers.license import _check_premium_feature
            if not _check_premium_feature('wechat_notify', db):
                raise HTTPException(status_code=403, detail="微信通知功能需要购买授权后才能使用")
        settings.wechat_webhook_config = settings_data.wechat_webhook_config
    if settings_data.open_registration_enabled is not None:
        if settings_data.open_registration_enabled:
            if not settings.open_registration_enabled:
                settings.open_registration_enabled = True
                settings.open_registration_expiry = datetime.now() + timedelta(days=3)
                log_operation(db, "系统配置", "修改", f"启用开放注册，3天后自动关闭", current_user.username, "INFO")
            else:
                if settings.open_registration_expiry and datetime.now() > settings.open_registration_expiry:
                    settings.open_registration_expiry = datetime.now() + timedelta(days=3)
                    log_operation(db, "系统配置", "修改", f"开放注册已过期，重新启用并设置3天后自动关闭", current_user.username, "INFO")
        else:
            if settings.open_registration_enabled:
                settings.open_registration_enabled = False
                settings.open_registration_expiry = None
                log_operation(db, "系统配置", "修改", f"关闭开放注册", current_user.username, "INFO")
    
    if settings_data.contact_person is not None:
        settings.contact_person = settings_data.contact_person
    if settings_data.contact_phone is not None:
        settings.contact_phone = settings_data.contact_phone
    if settings_data.contact_email is not None:
        settings.contact_email = settings_data.contact_email
    if settings_data.contact_wechat is not None:
        settings.contact_wechat = settings_data.contact_wechat
    
    db.commit()
    db.refresh(settings)
    
    # 更新后立即同步
    from utils.wechat_notifier import wechat_notifier
    wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
    # 返回前解析 JSON 字符串为列表，以符合 Schema 定义
    try:
        settings.subject_teachers = json.loads(settings.subject_teachers) if settings.subject_teachers else []
    except:
        settings.subject_teachers = []
    
    try:
        settings.fee_managers = json.loads(settings.fee_managers) if settings.fee_managers else []
    except:
        settings.fee_managers = []

    try:
        settings.grade_managers = json.loads(settings.grade_managers) if settings.grade_managers else []
    except:
        settings.grade_managers = []

    try:
        settings.evaluation_managers = json.loads(settings.evaluation_managers) if settings.evaluation_managers else []
    except:
        settings.evaluation_managers = []

    try:
        settings.operation_managers = json.loads(settings.operation_managers) if settings.operation_managers else []
    except:
        settings.operation_managers = []

    log_operation(db, "系统配置", "修改", f"更新系统配置及微信通知映射", current_user.username)
    return settings

@router.post("", response_model=SettingsSchema)
def create_or_update_settings(
    settings_data: SettingsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """创建或更新站点参数"""
    settings = db.query(Settings).first()

    # 验证并处理 site_url（内网IP）
    if not settings_data.site_url or not settings_data.site_url.strip():
        raise HTTPException(status_code=400, detail="本站内网IP不能为空")
    
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    raw_ip = settings_data.site_url.strip()
    if not (re.match(ip_pattern, raw_ip) or re.match(domain_pattern, raw_ip)):
        raise HTTPException(status_code=400, detail="请输入有效的内网IP地址或域名")
    
    # 获取后端端口（从环境变量）
    backend_port = int(os.getenv("BACKEND_PORT", "35000"))
    
    # 自动拼接完整的 URL
    full_site_url = f"http://{raw_ip}:{backend_port}"

    # 如果配置为空字符串，则初始化为空对象 JSON
    config_str = settings_data.wechat_webhook_config
    if not config_str or config_str.strip() == '':
        config_str = '{}'
    notif_str = settings_data.notification_settings or '{}'
    email_config_str = settings_data.email_config or '{}'
    email_notif_str = settings_data.email_notification_settings or '{}'
    teacher_restricted = settings_data.teacher_visibility_restricted if settings_data.teacher_visibility_restricted is not None else True
    # 处理 subject_teachers，将其转为 JSON 字符串
    subject_teachers_json = json.dumps(settings_data.subject_teachers or [])
    # 处理 fee_managers，将其转为 JSON 字符串
    fee_managers_json = json.dumps(settings_data.fee_managers or [])
    # 处理 grade_managers，将其转为 JSON 字符串
    grade_managers_json = json.dumps(settings_data.grade_managers or [])
    # 处理 evaluation_managers，将其转为 JSON 字符串
    evaluation_managers_json = json.dumps(settings_data.evaluation_managers or [])
    # 处理 operation_managers，将其转为 JSON 字符串
    operation_managers_json = json.dumps(settings_data.operation_managers or [])

    schedule_edit_restricted = settings_data.schedule_edit_restricted if settings_data.schedule_edit_restricted is not None else True
    schedule_delete_restricted = settings_data.schedule_delete_restricted if settings_data.schedule_delete_restricted is not None else True

    # 处理 ai_config，确保不为空
    ai_config_str = settings_data.ai_config or '{}'

    # 处理 ldap_config，确保不为空
    ldap_config_str = settings_data.ldap_config or '{}'
    
    # License 检查（仅在功能被启用时检查，避免格式差异误触发）
    from routers.license import _check_premium_feature
    old_ai = (settings.ai_config or '{}') if settings else '{}'
    old_wc = (settings.wechat_webhook_config or '{}') if settings else '{}'
    try:
        old_ai_parsed = json.loads(old_ai) if old_ai else {}
        new_ai_parsed = json.loads(ai_config_str) if ai_config_str else {}
    except (json.JSONDecodeError, TypeError):
        old_ai_parsed = {}
        new_ai_parsed = {}
    try:
        old_wc_parsed = json.loads(old_wc) if old_wc else {}
        new_wc_parsed = json.loads(config_str) if config_str else {}
    except (json.JSONDecodeError, TypeError):
        old_wc_parsed = {}
        new_wc_parsed = {}
    if new_ai_parsed.get('enabled') and not old_ai_parsed.get('enabled') and not _check_premium_feature('smart_command', db):
        raise HTTPException(status_code=403, detail="智能指令功能需要购买授权后才能使用")
    if new_wc_parsed.get('enabled') and not old_wc_parsed.get('enabled') and not _check_premium_feature('wechat_notify', db):
        raise HTTPException(status_code=403, detail="微信通知功能需要购买授权后才能使用")
    
    if settings:
        # 更新现有站点参数
        settings.site_name = settings_data.site_name
        settings.site_logo = settings_data.site_logo or ""
        settings.site_url = full_site_url  # 使用拼接后的完整URL
        settings.organization_website = settings_data.organization_website or ""
        settings.wechat_qrcode = settings_data.wechat_qrcode or ""
        settings.work_wechat_qrcode = settings_data.work_wechat_qrcode or ""
        settings.wechat_webhook_config = config_str
        settings.notification_settings = notif_str
        settings.email_config = email_config_str
        settings.email_notification_settings = email_notif_str
        settings.teacher_visibility_restricted = teacher_restricted
        settings.subject_teachers = subject_teachers_json
        settings.fee_managers = fee_managers_json
        settings.grade_managers = grade_managers_json
        settings.evaluation_managers = evaluation_managers_json
        settings.operation_managers = operation_managers_json
        settings.schedule_edit_restricted = schedule_edit_restricted
        settings.schedule_delete_restricted = schedule_delete_restricted
        # 添加日志字段处理
        settings.log_enabled = settings_data.log_enabled if settings_data.log_enabled is not None else True
        settings.log_level = settings_data.log_level if settings_data.log_level is not None else "INFO"
        settings.log_debug_enabled = settings_data.log_debug_enabled if settings_data.log_debug_enabled is not None else False
        settings.frontend_log_enabled = settings_data.frontend_log_enabled if settings_data.frontend_log_enabled is not None else True
        # 添加AI字段处理
        settings.ai_config = ai_config_str
        # 添加LDAP字段处理
        settings.ldap_enabled = settings_data.ldap_enabled if settings_data.ldap_enabled is not None else False
        settings.ldap_config = ldap_config_str
        # 添加课程字段处理
        settings.hours_per_lesson = settings_data.hours_per_lesson if settings_data.hours_per_lesson is not None else 2.0
        settings.course_config = settings_data.course_config or '{}'
        # 添加开放注册字段处理
        if settings_data.open_registration_enabled is not None:
            if settings_data.open_registration_enabled:
                if not settings.open_registration_enabled:
                    settings.open_registration_enabled = True
                    settings.open_registration_expiry = datetime.now() + timedelta(days=3)
                    log_operation(db, "系统配置", "修改", f"启用开放注册，3天后自动关闭", current_user.username, "INFO")
                else:
                    if settings.open_registration_expiry and datetime.now() > settings.open_registration_expiry:
                        settings.open_registration_expiry = datetime.now() + timedelta(days=3)
                        log_operation(db, "系统配置", "修改", f"开放注册已过期，重新启用并设置3天后自动关闭", current_user.username, "INFO")
            else:
                if settings.open_registration_enabled:
                    settings.open_registration_enabled = False
                    settings.open_registration_expiry = None
                    log_operation(db, "系统配置", "修改", f"关闭开放注册", current_user.username, "INFO")
        
        if settings_data.session_timeout_minutes is not None:
            new_timeout = max(5, min(settings_data.session_timeout_minutes, 43200))
            if settings.session_timeout_minutes != new_timeout:
                settings.session_timeout_minutes = new_timeout
                log_operation(db, "系统配置", "修改", f"登录超时时间修改为 {new_timeout} 分钟", current_user.username, "INFO")
        
        if settings_data.contact_person is not None:
            settings.contact_person = settings_data.contact_person
        if settings_data.contact_phone is not None:
            settings.contact_phone = settings_data.contact_phone
        if settings_data.contact_email is not None:
            settings.contact_email = settings_data.contact_email
        if settings_data.contact_wechat is not None:
            settings.contact_wechat = settings_data.contact_wechat
        
        db.commit()
        log_operation(db, "系统配置", "修改", f"更新站点参数: {settings_data.site_name}", current_user.username)
        db.refresh(settings)
    else:
        # 创建新的站点参数
        settings = Settings(
            site_name=settings_data.site_name,
            site_logo=settings_data.site_logo or "",
            site_url=full_site_url,  # 使用拼接后的完整URL
            organization_website=settings_data.organization_website or "",
            wechat_qrcode=settings_data.wechat_qrcode or "",
            work_wechat_qrcode=settings_data.work_wechat_qrcode or "",
            wechat_webhook_config=config_str,
            notification_settings=notif_str,
            email_config=email_config_str,
            email_notification_settings=email_notif_str,
            teacher_visibility_restricted=teacher_restricted,
            subject_teachers=subject_teachers_json,
            fee_managers=fee_managers_json,
            grade_managers=grade_managers_json,
            evaluation_managers=evaluation_managers_json,
            operation_managers=operation_managers_json,
            schedule_edit_restricted=schedule_edit_restricted,
            schedule_delete_restricted=schedule_delete_restricted,
            log_enabled=settings_data.log_enabled if settings_data.log_enabled is not None else True,
            log_level=settings_data.log_level if settings_data.log_level is not None else "INFO",
            log_debug_enabled=settings_data.log_debug_enabled if settings_data.log_debug_enabled is not None else False,
            frontend_log_enabled=settings_data.frontend_log_enabled if settings_data.frontend_log_enabled is not None else True,
            ai_config=ai_config_str,
            ldap_enabled=settings_data.ldap_enabled if settings_data.ldap_enabled is not None else False,
            ldap_config=ldap_config_str,
            hours_per_lesson=settings_data.hours_per_lesson if settings_data.hours_per_lesson is not None else 2.0,
            course_config=settings_data.course_config or '{}',
            open_registration_enabled=settings_data.open_registration_enabled if settings_data.open_registration_enabled is not None else False,
            open_registration_expiry=settings_data.open_registration_expiry,
            session_timeout_minutes=settings_data.session_timeout_minutes if settings_data.session_timeout_minutes is not None else 1440,
            contact_person=settings_data.contact_person or "",
            contact_phone=settings_data.contact_phone or "",
            contact_email=settings_data.contact_email or "",
            contact_wechat=settings_data.contact_wechat or "",
        )

        db.add(settings)
        db.commit()
        log_operation(db, "系统配置", "创建", f"创建站点参数: {settings_data.site_name}", current_user.username)
        db.refresh(settings)
    
    # 同步到全局通知器
    from utils.wechat_notifier import wechat_notifier
    wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
    wechat_notifier.load_notification_settings(settings.notification_settings or "{}")
    
    # 返回时同样需要解析一下，确保响应格式一致
    try:
        settings.subject_teachers = json.loads(settings.subject_teachers)
    except:
        settings.subject_teachers = []

    try:
        settings.fee_managers = json.loads(settings.fee_managers)
    except:
        settings.fee_managers = []

    try:
        settings.grade_managers = json.loads(settings.grade_managers)
    except:
        settings.grade_managers = []

    try:
        settings.evaluation_managers = json.loads(settings.evaluation_managers)
    except:
        settings.evaluation_managers = []

    try:
        settings.operation_managers = json.loads(settings.operation_managers)
    except:
        settings.operation_managers = []

    # 重新初始化定时任务调度器
    from utils.remainder import init_scheduler
    init_scheduler()
    return settings

@router.post("/test-wechat-url")
def test_specific_webhook(
    request: TestWebhookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试指定的 Webhook URL"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('wechat_notify', db):
        raise HTTPException(status_code=403, detail="微信通知功能需要购买授权后才能使用")
    
    from datetime import datetime
    
    url = request.webhook_url
    if not url:
        log_operation(db, "系统配置", "测试失败", "尝试测试微信Webhook但未提供URL", current_user.username, "ERROR")
        raise HTTPException(status_code=400, detail="Webhook URL 不能为空")
    
    settings = db.query(Settings).first()
    site_name = settings.site_name if settings else "未知机构"
    
    try:
        data = {
            "msgtype": "text",
            "text": {
                "content": f"🎉 **系统通知测试**\n\n机构：{site_name}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n如果您收到此消息，说明该 Webhook 配置有效！"
            }
        }
        resp = requests.post(url, json=data, timeout=5)
        res_json = resp.json()
        
        if res_json.get('errcode') == 0:
            return {"message": "测试成功"}
        else:
            log_operation(db, "系统配置", "测试失败", f"测试微信Webhook失败，企业微信返回错误: {res_json.get('errmsg')}", current_user.username, "ERROR")
            raise HTTPException(status_code=500, detail=f"企业微信返回错误: {res_json.get('errmsg')}")
            
    except Exception as e:
        log_operation(db, "系统配置", "测试失败", f"测试微信Webhook失败，网络请求错误: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"网络请求失败: {str(e)}")

@router.post("/test-wechat")
def test_wechat_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试微信通知（保留作为备用，尝试发送默认配置）"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('wechat_notify', db):
        raise HTTPException(status_code=403, detail="微信通知功能需要购买授权后才能使用")
    
    from utils.wechat_notifier import wechat_notifier
    import json
    
    settings = db.query(Settings).first()
    if not settings or not settings.wechat_webhook_config:
        log_operation(db, "系统配置", "测试失败", "尝试测试微信通知但未配置Webhook URL", current_user.username, "ERROR")
        raise HTTPException(status_code=400, detail="未配置任何企业微信Webhook URL")
    
    try:
        config = json.loads(settings.wechat_webhook_config)
        test_url = None
        if isinstance(config.get('fee_alert'), list) and len(config['fee_alert']) > 0:
            test_url = config['fee_alert'][0]
        elif isinstance(config.get('schedule_change'), dict) and isinstance(config['schedule_change'].get('default'), list) and len(config['schedule_change']['default']) > 0:
            test_url = config['schedule_change']['default'][0]
            
        if not test_url:
            log_operation(db, "系统配置", "测试失败", "配置中没有有效的Webhook URL用于测试", current_user.username, "ERROR")
            raise HTTPException(status_code=400, detail="配置中没有有效的Webhook URL用于测试")
            
        original_config = wechat_notifier.webhook_config
        wechat_notifier.webhook_config = {"test": [test_url]}
        success = wechat_notifier.send_message_by_type("test", "🎉 微信通知配置测试成功！")
        wechat_notifier.webhook_config = original_config
        
        if not success.get(test_url, False):
            log_operation(db, "系统配置", "测试失败", f"测试微信通知失败，企业微信返回错误或网络请求失败", current_user.username, "ERROR")
            raise HTTPException(status_code=500, detail="发送失败，请检查Webhook URL是否正确")
        return {"message": "测试消息已发送"}
    except json.JSONDecodeError:
        log_operation(db, "系统配置",   "测试失败", "微信配置格式错误，无法解析为JSON", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail="微信配置格式错误")
    except Exception as e:
        log_operation(db, "系统配置",  "测试失败", f"测试微信通知过程中发生错误: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"测试过程中发生错误: {str(e)}")
    
@router.post("/test-email")
def test_email(
    request: EmailConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试邮件发送"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    from email.utils import formataddr
    
    settings = db.query(Settings).first()
    if not settings:
        log_operation(db, "系统配置", "测试失败", "尝试测试邮件发送但站点参数不存在", current_user.username, "ERROR")
        raise HTTPException(status_code=404, detail="站点参数不存在")
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = formataddr((request.smtp_from_name, request.smtp_user))
        msg['To'] = request.smtp_user
        msg['Subject'] = '课程安排系统 - 邮件配置测试'
        
        # 添加邮件正文
        body = f"""
        <h2>邮件配置测试</h2>
        <p>您好！</p>
        <p>这是来自<strong>{settings.site_name}</strong>课程安排系统的测试邮件。</p>
        <p>如果您收到此邮件，说明您的SMTP配置正确！</p>
        <p>配置信息：</p>
        <ul>
            <li>SMTP服务器：{request.smtp_host}</li>
            <li>SMTP端口：{request.smtp_port}</li>
            <li>发送邮箱：{request.smtp_user}</li>
            <li>使用SSL：{request.smtp_ssl}</li>
        </ul>
        <p>测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # 发送邮件
        if request.smtp_ssl:
            smtp = smtplib.SMTP_SSL(request.smtp_host, request.smtp_port)
        else:
            smtp = smtplib.SMTP(request.smtp_host, request.smtp_port)
        
        smtp.login(request.smtp_user, request.smtp_password)
        smtp.send_message(msg)
        smtp.quit()
        
        log_operation(db, "系统配置", "测试", f"测试邮件发送成功: {request.smtp_user}", current_user.username)
        return {"message": "测试邮件发送成功，请检查收件箱"}
        
    except smtplib.SMTPAuthenticationError as e:
        log_operation(db, "系统配置", "测试失败", f"SMTP认证失败: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"SMTP认证失败: {str(e)}")
    except smtplib.SMTPException as e:
        log_operation(db, "系统配置", "测试失败", f"SMTP发送失败: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"SMTP发送失败: {str(e)}")
    except Exception as e:
        log_operation(db, "系统配置", "测试失败", f"邮件发送失败: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"邮件发送失败: {str(e)}")

@router.post("/test-ai")
def test_ai_connection(
    request: TestAIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试AI API连接"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('smart_command', db):
        raise HTTPException(status_code=403, detail="智能指令功能需要购买授权后才能使用")
    
    try:
        # 验证API地址格式
        if not validate_api_url(request.api_url):
            try:
                log_operation(db, "系统配置", "AI测试失败", f"API地址格式不正确: {request.api_url}", current_user.username if current_user else "unknown", "ERROR")
            except:
                pass
            raise HTTPException(status_code=400, detail="API地址格式不正确，必须以 http:// 或 https:// 开头")
        
        # 验证必填字段
        if not request.api_key:
            try:
                log_operation(db, "系统配置", "AI测试失败", "API密钥不能为空", current_user.username if current_user else "unknown", "ERROR")
            except:
                pass
            raise HTTPException(status_code=400, detail="API密钥不能为空")
        
        if not request.model:
            try:
                log_operation(db, "系统配置", "AI测试失败", "模型名称不能为空", current_user.username if current_user else "unknown", "ERROR")
            except:
                pass
            raise HTTPException(status_code=400, detail="模型名称不能为空")
        
        username = current_user.username if current_user else "unknown"
        log_operation(db, "系统配置", "AI测试", f"开始测试AI连接: provider={request.provider}, model={request.model}, url={request.api_url}", username, "INFO")
        
        # 构建请求头 - 严格按照DeepSeek官方文档
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {request.api_key}"
        }
        
        # 构建测试消息 - 严格按照DeepSeek官方文档格式
        test_payload = {
            "model": request.model,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ],
            "stream": False
        }
        
        response = requests.post(
            request.api_url,
            json=test_payload,
            headers=headers,
            timeout=request.timeout
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                # 检查是否有错误
                if "error" in result:
                    error_msg = result["error"].get("message", "未知错误")
                    try:
                        log_operation(db, "系统配置", "AI测试失败", f"API返回错误: {error_msg}", username, "ERROR")
                    except:
                        pass
                    raise HTTPException(status_code=500, detail=f"API返回错误: {error_msg}")
                
                # 检查是否有choices
                if "choices" not in result or len(result["choices"]) == 0:
                    try:
                        log_operation(db, "系统配置", "AI测试失败", "API响应中没有choices字段", username, "ERROR")
                    except:
                        pass
                    raise HTTPException(status_code=500, detail="API响应格式错误：缺少choices字段")
                
                try:
                    log_operation(db, "系统配置", "AI测试成功", f"AI连接测试成功: provider={request.provider}, model={request.model}", username, "INFO")
                except:
                    pass
                return {"message": "AI连接测试成功！配置已保存"}
            except json.JSONDecodeError:
                try:
                    log_operation(db, "系统配置", "AI测试失败", "API响应不是有效的JSON格式", username, "ERROR")
                except:
                    pass
                raise HTTPException(status_code=500, detail="API响应格式错误")
        else:
            error_detail = f"HTTP {response.status_code}"
            try:
                error_resp = response.json()
                if "error" in error_resp:
                    error_detail = error_resp["error"].get("message", error_detail)
            except:
                error_detail = response.text[:200] if response.text else error_detail
            
            try:
                log_operation(db, "系统配置", "AI测试失败", f"API返回错误: {error_detail}", username, "ERROR")
            except:
                pass
            raise HTTPException(status_code=response.status_code, detail=f"API连接失败: {error_detail}")
            
    except requests.exceptions.Timeout:
        username = current_user.username if current_user else "unknown"
        try:
            log_operation(db, "系统配置", "AI测试失败", f"请求超时（{request.timeout}秒）", username, "ERROR")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"请求超时，请检查网络连接或增加超时时间")
    except requests.exceptions.ConnectionError as e:
        username = current_user.username if current_user else "unknown"
        try:
            log_operation(db, "系统配置", "AI测试失败", f"连接错误: {str(e)}", username, "ERROR")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"无法连接到API服务器，请检查API地址是否正确")
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        username = current_user.username if current_user else "unknown"
        import traceback
        error_traceback = traceback.format_exc()

        log_operation(db, "系统配置", "AI测试失败", f"测试过程中发生未预期错误: {str(e)} 堆栈跟踪:\n{error_traceback}", username, "ERROR")
        try:
            log_operation(db, "系统配置", "AI测试失败", f"测试过程中发生错误: {str(e)}\n{error_traceback}", username, "ERROR")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")
    
@router.post("/test-ldap")
def test_ldap_connection(
    request: TestLDAPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试LDAP连接"""
    try:
        if not request.server:
            raise HTTPException(status_code=400, detail="LDAP服务器地址不能为空")
        
        if not request.user_search_base:
            raise HTTPException(status_code=400, detail="用户搜索基础DN不能为空")
        
        try:
            import ldap3
        except ImportError:
            raise HTTPException(status_code=500, detail="ldap3库未安装，请运行: pip install ldap3")
        
        server_uri = f"{'ldaps' if request.use_ssl else 'ldap'}://{request.server}:{request.port}"
        server_obj = ldap3.Server(server_uri)
        
        if request.bind_dn and request.bind_password:
            try:
                conn = ldap3.Connection(server_obj, user=request.bind_dn, password=request.bind_password, auto_bind=True)
                conn.unbind()
            except Exception as e:
                log_operation(db, "系统配置", "LDAP测试失败", f"LDAP管理员绑定失败: {str(e)}", current_user.username, "ERROR")
                raise HTTPException(status_code=400, detail=f"LDAP管理员绑定失败: {str(e)}")
        else:
            conn = ldap3.Connection(server_obj)
            if not conn.bind():
                log_operation(db, "系统配置", "LDAP测试失败", "LDAP匿名绑定失败", current_user.username, "ERROR")
                raise HTTPException(status_code=400, detail="LDAP匿名绑定失败")
            conn.unbind()
        
        log_operation(db, "系统配置", "LDAP测试成功", f"LDAP连接测试成功: {server_uri}", current_user.username, "INFO")
        return {"message": "LDAP连接测试成功！"}
    except HTTPException:
        raise
    except Exception as e:
        log_operation(db, "系统配置", "LDAP测试失败", f"测试过程中发生错误: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")