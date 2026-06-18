# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
from models import Schedule, Teacher, Class, Room, Student, Settings
from utils.wechat_notifier import wechat_notifier
from utils.email_notifier import email_notifier
from datetime import date, datetime, timedelta
import json
from utils.logger import log_operation
import pytz
import os
import tempfile

# 使用北京时间时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

scheduler = BackgroundScheduler()
# 跨进程文件锁，防止多 uvicorn worker 同时执行定时任务
REMINDER_LOCK_FILE = os.path.join(tempfile.gettempdir(), 'course_arrange_reminder.lock')
def _acquire_reminder_lock():
    """尝试获取定时任务排他锁，返回 (lock_fd, acquired)。
    若锁已被其他 worker 持有则返回 (None, False)。
    """
    try:
        import fcntl
        lock_fd = open(REMINDER_LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd, True
    except (IOError, OSError):
        return None, False
    except ImportError:
        # Windows 平台回退：使用 msvcrt
        try:
            import msvcrt
            lock_fd = open(REMINDER_LOCK_FILE, 'w')
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
            return lock_fd, True
        except (IOError, OSError):
            return None, False
        
def _release_reminder_lock(lock_fd):
    """释放定时任务排他锁"""
    if lock_fd is None:
        return
    try:
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
    except (ImportError, IOError):
        pass
    try:
        lock_fd.close()
    except Exception:
        pass

def check_and_send_morning_reminder():
    """每天早上7点发送当天课程提醒"""
    from datetime import timezone
    import os, threading
    db = SessionLocal()
    # 获取跨进程锁，防止多 worker 重复执行
    lock_fd, acquired = _acquire_reminder_lock()
    if not acquired:
        log_operation(db, "系统配置", "定时任务执行", f"早上提醒任务触发 [PID={os.getpid()} TID={threading.current_thread().ident}] - 跳过", "system", "DEBUG")
        return
    
    db = SessionLocal()
    try:
        now_beijing = datetime.now(BEIJING_TZ)
        now_utc = datetime.now(timezone.utc)
        log_operation(db, "系统配置", "定时任务执行", f"早上提醒任务触发 [PID={os.getpid()} TID={threading.current_thread().ident}] - 北京时间: {now_beijing}, UTC时间: {now_utc}", "system", "DEBUG")
        
        settings = db.query(Settings).first()
        if not settings: 
            log_operation(db, "系统配置", "定时任务执行", "站点参数不存在，跳过提醒", "system", "WARNING")
            return
        
        notif_settings = json.loads(settings.notification_settings or "{}")
        email_notif_settings = json.loads(settings.email_notification_settings or "{}")
        
        wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
        wechat_notifier.load_promotion_info(
            website=settings.organization_website,
            wechat_qr=settings.wechat_qrcode,
            work_wechat_qr=settings.work_wechat_qrcode
        )
        need_wechat_reminder = notif_settings.get("morning_reminder", False)
        from routers.license import _check_premium_feature
        if need_wechat_reminder and not _check_premium_feature('wechat_notify', db):
            need_wechat_reminder = False
            log_operation(db, "系统配置", "定时任务执行", "微信通知功能未授权，跳过微信提醒", "system", "WARNING")
        need_email_reminder = email_notif_settings.get('enabled', False) and email_notif_settings.get("morning_reminder", False)
        
        log_operation(db, "系统配置", "定时任务执行", f"提醒配置 - 微信早上提醒: {need_wechat_reminder}, 邮件早上提醒: {need_email_reminder}", "system", "INFO")
        
        if not need_wechat_reminder and not need_email_reminder:
            log_operation(db, "系统配置", "定时任务执行", "未启用任何早上提醒，跳过", "system", "DEBUG")
            return

        today = date.today()
        schedules = db.query(Schedule).filter(
            Schedule.start_date == today,
            Schedule.execution_status == 'pending'
        ).all()
        
        log_operation(db, "系统配置", "定时任务执行", f"找到 {len(schedules)} 条今日待执行课程", "system", "DEBUG")
        
        if schedules:
            # 获取班级webhook地址
            class_webhooks = {}
            # 获取允许的班级列表
            enabled_classes = notif_settings.get('enabled_classes', [])
            for s in schedules:
                if s.class_id and s.class_.wechat_webhook:
                    class_webhooks[s.class_id] = s.class_.wechat_webhook
            
            schedule_list = [{
                "start_date": s.start_date.strftime('%Y-%m-%d'),
                "start_time": s.start_time,
                "end_time": s.end_time,
                "course_name": s.course.name if s.course else "未知科目",
                "teacher_name": s.teacher.name if s.teacher else "未知导师",
                "class_name": s.class_.name if s.class_ else "未知班级",
                "room_name": s.room.name if s.room else "未知教室",
                "teacher_id": s.teacher_id,
                "class_id": s.class_id,
                "student_list": [{"name": st.name, "is_active": st.is_active} for st in s.class_.students] if s.class_ else []
            } for s in schedules]
            
            # 发送微信提醒
            if need_wechat_reminder:
                try:
                    log_operation(db, "系统配置", "定时任务执行", f"已发送 {len(schedules)} 条今日课程微信提醒", "system", "DEBUG")
                    result = wechat_notifier.send_course_reminder(schedule_list, "📅 今日课程提醒", class_webhooks, enabled_classes)
                    success_count = sum(1 for v in result.values() if v)
                    log_operation(db, "系统配置", "发送微信提醒", f"已发送 {len(schedules)} 条今日课程微信提醒，成功 {success_count}/{len(result)} 个群", "system", "DEBUG")
                except Exception as e:
                    log_operation(db, "系统配置", "发送微信提醒失败", f"错误: {str(e)}", "system", "ERROR")
                    import traceback
                    log_operation(db, "系统配置", "发送微信提醒失败", f"堆栈跟踪: {traceback.format_exc()}", "system", "ERROR")
            
            # 发送邮件提醒（智能收件人）
            if need_email_reminder:
                try:
                    log_operation(db, "系统配置", "发送邮件提醒", f"开始处理邮件提醒，共 {len(schedules)} 条课程", "system", "DEBUG")
                    # 直接将原始字符串传递给load_config，不要解析后再传递
                    email_config = settings.email_config
                    log_operation(db, "系统配置", "发送邮件提醒", f"原始 email_config 类型: {type(email_config)}, 值: {email_config}", "system", "DEBUG")
                    #if isinstance(email_config, str):
                    #    email_config = json.loads(email_config or '{}')
                    #    log_operation(db, "系统配置", "发送邮件提醒", f"解析后的 email_config: {email_config}", "system", "DEBUG")
                    
                    from utils.email_notifier import EmailNotifier
                    email_notifier_instance = EmailNotifier()
                    email_notifier_instance.load_config(email_config, settings.site_name)
                    email_notifier_instance.load_promotion_info(
                        website=settings.organization_website,
                        wechat_qr=settings.wechat_qrcode,
                        work_wechat_qr=settings.work_wechat_qrcode
                    )
                    log_operation(db, "系统配置", "发送邮件提醒", f"邮件通知器配置加载完成", "system", "DEBUG")
                    
                    # 收集所有需要接收邮件的人员
                    all_recipients = set()
                    
                    for schedule in schedules:
                        log_operation(db, "系统配置", "发送邮件提醒", f"处理课程: class_id={schedule.class_id}, teacher_id={schedule.teacher_id}", "system", "DEBUG")
                        
                        # 1. 获取导师邮箱
                        if schedule.teacher_id:
                            teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
                            if teacher:
                                log_operation(db, "系统配置", "发送邮件提醒", f"找到导师: {teacher.name}, email={teacher.email}", "system", "DEBUG")
                                if teacher and teacher.email:
                                    all_recipients.add(teacher.email)
                                    log_operation(db, "系统配置", "发送邮件提醒", f"已添加导师邮箱: {teacher.name} - {teacher.email}", "system", "DEBUG")
                            else:
                                log_operation(db, "系统配置", "发送邮件提醒", f"未找到导师 ID={schedule.teacher_id}", "system", "WARNING")
                        
                        # 2. 获取班级中学员的邮箱
                        if schedule.class_id:
                            class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
                            if class_:
                                log_operation(db, "系统配置", "发送邮件提醒", f"找到班级: {class_.name}, 学生数量={len(class_.students)}", "system", "DEBUG")
                                # 通过班级的 students 关系获取学员
                                for student in class_.students:
                                    log_operation(db, "系统配置", "发送邮件提醒", f"检查学生: {student.name}, is_active={student.is_active}, email={student.email}", "system", "DEBUG")
                                    if student.is_active:
                                        if student.email:
                                            all_recipients.add(student.email)
                                            log_operation(db, "系统配置", "发送邮件提醒", f"已添加学员邮箱: {student.name} - {student.email}", "system", "DEBUG")
                                        else:
                                            log_operation(db, "系统配置", "发送邮件提醒", f"未找到学生 {student.name} 的邮箱", "system", "WARNING")
                                        
                                        # 如果学员有家长邮箱，也添加
                                        if hasattr(student, 'parent_email') and student.parent_email:
                                            all_recipients.add(student.parent_email)
                                            log_operation(db, "系统配置", "发送邮件提醒", f"已添加家长邮箱: {student.name}家长 - {student.parent_email}", "system", "DEBUG")
                            else:
                                log_operation(db, "系统配置", "发送邮件提醒", f"未找到班级 ID={schedule.class_id}", "system", "WARNING")
                    
                    recipients_list = list(all_recipients)
                    log_operation(db, "系统配置", "发送邮件提醒", f"最终收件人列表 ({len(recipients_list)}人)", "system", "DEBUG")
                    
                    if recipients_list:
                        email_notifier_instance.send_course_reminder(schedule_list, "今日课程提醒", recipients_list, db)
                        log_operation(db, "系统配置", "发送邮件提醒", f"已发送 {len(schedules)} 条今日课程邮件提醒给 {len(recipients_list)} 人", "system", "INFO")
                    else:
                        log_operation(db, "系统配置", "发送邮件提醒", "没有找到任何有效的邮箱收件人", "system", "WARNING")
                        
                except Exception as e:
                    log_operation(db, "系统配置", "发送邮件提醒失败", f"错误: {str(e)}", "system", "ERROR")
                    import traceback
                    error_trace = traceback.format_exc()
                    log_operation(db, "系统配置", "发送邮件提醒失败", f"堆栈跟踪: {error_trace}", "system", "ERROR")
        else:
            log_operation(db, "系统配置", "定时任务执行", "今日没有待执行的课程", "system", "INFO")
    
    except Exception as e:
        log_operation(db, "系统配置", "早间提醒任务出错", f"错误: {str(e)}", "system", "ERROR")
        import traceback
        log_operation(db, "系统配置", "早间提醒任务出错", f"堆栈跟踪: {traceback.format_exc()}", "system", "ERROR")
    finally:
        db.close()
        _release_reminder_lock(lock_fd)


def check_and_send_evening_reminder():
    """每天晚上7点发送明天课程提醒"""
    from datetime import timezone
    import os, threading    

    db = SessionLocal()
    # 获取跨进程锁，防止多 worker 重复执行
    lock_fd, acquired = _acquire_reminder_lock()
    if not acquired:
        log_operation(db, "系统配置", "定时任务执行", f"晚上提醒任务触发 [PID={os.getpid()} TID={threading.current_thread().ident}] - 另一个 worker 正在执行，跳过", "system", "DEBUG")
        return
    
    db = SessionLocal()
    try:
        now_beijing = datetime.now(BEIJING_TZ)
        now_utc = datetime.now(timezone.utc)
        log_operation(db, "系统配置", "定时任务执行", f"晚上提醒任务触发 [PID={os.getpid()} 线程ID={threading.current_thread().ident} 线程名: {threading.current_thread().name}] - 北京时间: {now_beijing}, UTC时间: {now_utc}", "system", "INFO")
        
        settings = db.query(Settings).first()
        if not settings: 
            log_operation(db, "系统配置", "定时任务执行", "站点参数不存在，跳过提醒", "system", "WARNING")
            return
        
        notif_settings = json.loads(settings.notification_settings or "{}")
        email_notif_settings = json.loads(settings.email_notification_settings or "{}")
        
        wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
        wechat_notifier.load_promotion_info(
            website=settings.organization_website,
            wechat_qr=settings.wechat_qrcode,
            work_wechat_qr=settings.work_wechat_qrcode
        )

        need_wechat_reminder = notif_settings.get("evening_reminder", False)
        from routers.license import _check_premium_feature
        if need_wechat_reminder and not _check_premium_feature('wechat_notify', db):
            need_wechat_reminder = False
            log_operation(db, "系统配置", "定时任务执行", "微信通知功能未授权，跳过微信提醒", "system", "WARNING")
        need_email_reminder = email_notif_settings.get('enabled', False) and email_notif_settings.get("evening_reminder", False)
        
        log_operation(db, "系统配置", "定时任务执行", f"提醒配置 - 微信晚上提醒: {need_wechat_reminder}, 邮件晚上提醒: {need_email_reminder}", "system", "INFO")
        
        if not need_wechat_reminder and not need_email_reminder:
            log_operation(db, "系统配置", "定时任务执行", "未启用任何晚上提醒，跳过", "system", "INFO")
            return

        tomorrow = date.today() + timedelta(days=1)
        schedules = db.query(Schedule).filter(
            Schedule.start_date == tomorrow,
            Schedule.execution_status == 'pending'
        ).all()
        
        log_operation(db, "系统配置", "定时任务执行", f"找到 {len(schedules)} 条明日待执行课程", "system", "INFO")
        
        if schedules:
            # 获取班级webhook地址
            class_webhooks = {}
            # 获取允许的班级列表
            enabled_classes = notif_settings.get('enabled_classes', [])
            for s in schedules:
                if s.class_id and s.class_.wechat_webhook:
                    class_webhooks[s.class_id] = s.class_.wechat_webhook
            
            schedule_list = [{
                "start_date": s.start_date.strftime('%Y-%m-%d'),
                "start_time": s.start_time,
                "end_time": s.end_time,
                "course_name": s.course.name if s.course else "未知科目",
                "teacher_name": s.teacher.name if s.teacher else "未知导师",
                "class_name": s.class_.name if s.class_ else "未知班级",
                "room_name": s.room.name if s.room else "未知教室",
                "teacher_id": s.teacher_id,
                "class_id": s.class_id,
                "student_list": [{"name": st.name, "is_active": st.is_active} for st in s.class_.students] if s.class_ else []
            } for s in schedules]
            
            # 发送微信提醒
            if need_wechat_reminder:
                try:
                    log_operation(db, "系统配置", "定时任务执行", f"准备发送微信提醒，课程数={len(schedule_list)}, 班级webhook数={len(class_webhooks)}", "system", "DEBUG")
                    result = wechat_notifier.send_course_reminder(schedule_list, "📅 明日课程预告", class_webhooks, enabled_classes)
                    success_count = sum(1 for v in result.values() if v)
                    log_operation(db, "系统配置", "发送微信提醒", f"已发送 {len(schedules)} 条明日课程微信提醒，成功 {success_count}/{len(result)} 个群", "system", "DEBUG")
                except Exception as e:
                    log_operation(db, "系统配置", "发送微信提醒失败", f"错误: {str(e)}", "system", "ERROR")
                    import traceback
                    log_operation(db, "系统配置", "发送微信提醒失败", f"堆栈跟踪: {traceback.format_exc()}", "system", "ERROR")
            
            # 发送邮件提醒（智能收件人）
            if need_email_reminder:
                try:
                    log_operation(db, "系统配置", "发送邮件提醒", f"开始处理邮件提醒，共 {len(schedules)} 条课程", "system", "DEBUG")
                    
                    # 直接将原始字符串传递给load_config，不要解析后再传递
                    email_config = settings.email_config
                    #if isinstance(email_config, str):
                    #    email_config = json.loads(email_config or '{}')
                    
                    from utils.email_notifier import EmailNotifier
                    email_notifier_instance = EmailNotifier()
                    email_notifier_instance.load_config(email_config, settings.site_name)
                    email_notifier_instance.load_promotion_info(
                        website=settings.organization_website,
                        wechat_qr=settings.wechat_qrcode,
                        work_wechat_qr=settings.work_wechat_qrcode
                    )
                    
                    # 收集所有需要接收邮件的人员
                    all_recipients = set()
                    
                    for schedule in schedules:
                        # 1. 获取导师邮箱
                        if schedule.teacher_id:
                            teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
                            if teacher and teacher.email:
                                all_recipients.add(teacher.email)
                                log_operation(db, "系统配置", "发送邮件提醒", f"添加导师邮箱: {teacher.name} - {teacher.email}", "system", "DEBUG")
                        
                        # 2. 获取班级中学员的邮箱（修复：使用正确的关联查询）
                        if schedule.class_id:
                            class_ = db.query(Class).filter(Class.id == schedule.class_id).first()
                            if class_:
                                # 通过班级的 students 关系获取学员
                                for student in class_.students:
                                    if student.is_active:
                                        if student.email:
                                            all_recipients.add(student.email)
                                            log_operation(db, "系统配置", "发送邮件提醒", f"添加学员邮箱: {student.name} - {student.email}", "system", "DEBUG")
                                        
                                        # 如果学员有家长邮箱，也添加
                                        if hasattr(student, 'parent_email') and student.parent_email:
                                            all_recipients.add(student.parent_email)
                                            log_operation(db, "系统配置", "发送邮件提醒", f"添加家长邮箱: {student.name}家长 - {student.parent_email}", "system", "DEBUG")
                    
                    recipients_list = list(all_recipients)
                    log_operation(db, "系统配置", "发送邮件提醒", f"最终收件人列表 ({len(recipients_list)}人: {recipients_list})", "system", "DEBUG")  
                    
                    if recipients_list:
                        email_notifier_instance.send_course_reminder(schedule_list, "明日课程提醒", recipients_list, db)
                        log_operation(db, "系统配置", "发送邮件提醒", f"已发送 {len(schedules)} 条明日课程邮件提醒给 {len(recipients_list)} 人", "system", "INFO")
                    else:
                        log_operation(db, "系统配置", "发送邮件提醒", "没有找到任何有效的邮箱收件人", "system", "WARNING")
                        
                except Exception as e:
                    log_operation(db, "系统配置", "发送邮件提醒失败", f"错误: {str(e)}", "system", "ERROR")
                    import traceback
                    log_operation(db, "系统配置", "发送邮件提醒失败", f"堆栈跟踪: {traceback.format_exc()}", "system", "ERROR")
        else:
            log_operation(db, "系统配置", "定时任务执行", "明日没有待执行的课程", "system", "INFO")
    
    except Exception as e:
        log_operation(db, "系统配置", "晚间提醒任务出错", f"错误: {str(e)}", "system", "ERROR")
        import traceback
        log_operation(db, "系统配置", "晚间提醒任务出错", f"堆栈跟踪: {traceback.format_exc()}", "system", "ERROR")
    finally:
        db.close()
        _release_reminder_lock(lock_fd)

def init_scheduler():
    """根据设置初始化定时任务"""
    db = SessionLocal()
    try:        
        settings = db.query(Settings).first()
        
        # 清除所有现有任务，确保不会有重复任务
        all_jobs = scheduler.get_jobs()
        log_operation(db, "系统配置", "初始化定时任务", f"当前共有 {len(all_jobs)} 个任务，将移除所有与课程提醒相关的任务", "system", "DEBUG")
        for job in all_jobs:
            # 移除我们管理的所有课程提醒任务
            if job.id in ['today_schedule_reminder', 'tomorrow_schedule_reminder'] or \
               (job.name and ('课程提醒' in job.name)):
                scheduler.remove_job(job.id)
                log_operation(db, "系统配置", "初始化定时任务", f"已移除任务: {job.id} ({job.name})", "system", "DEBUG")
        
        need_morning_reminder = False
        need_evening_reminder = False
        
        if settings:
            notif_settings = json.loads(settings.notification_settings or "{}")
            email_notif_settings = json.loads(settings.email_notification_settings or "{}")
            
            log_operation(db, "系统配置", "初始化定时任务", f"微信通知设置: {notif_settings} 邮件通知设置: {email_notif_settings}", "system", "DEBUG")
            
            # 检查是否需要添加早上提醒任务（只要有课程就会自动找收件人）
            need_morning_reminder = notif_settings.get('morning_reminder', False) or (
                email_notif_settings.get('enabled', False) and email_notif_settings.get('morning_reminder', False)
            )
            
            # 检查是否需要添加晚上提醒任务
            need_evening_reminder = notif_settings.get('evening_reminder', False) or (
                email_notif_settings.get('enabled', False) and email_notif_settings.get('evening_reminder', False)
            )
        else:
            log_operation(db, "系统配置", "初始化定时任务", "警告: 数据库中找不到站点设置", "system", "WARNING")
        
        log_operation(db, "系统配置", "初始化定时任务", f"已检查到课程提醒设置: 早上提醒: {need_morning_reminder} 晚上提醒: {need_evening_reminder}", "system", "DEBUG")
        
        # 根据设置添加相应的定时任务（使用北京时间）
        if need_morning_reminder:
            scheduler.add_job(
                check_and_send_morning_reminder,
                CronTrigger(hour=7, minute=0, timezone=BEIJING_TZ),
                id='today_schedule_reminder',
                name='今日课程提醒',
                replace_existing=True
            )
            log_operation(db, "系统配置", "初始化定时任务", "已添加早上7点今日课程提醒任务", "system", "INFO")
        
        if need_evening_reminder:
            scheduler.add_job(
                check_and_send_evening_reminder,
                CronTrigger(hour=19, minute=0, timezone=BEIJING_TZ),
                id='tomorrow_schedule_reminder',
                name='明日课程提醒',
                replace_existing=True
            )
            log_operation(db, "系统配置", "初始化定时任务", "已添加晚上7点明日课程提醒任务", "system", "INFO")
        
        # 确保调度器已启动
        if not scheduler.running:
            scheduler.start()
            log_operation(db, "系统配置", "初始化定时任务", "已启动定时任务调度器", "system", "INFO")
        else:
            log_operation(db, "系统配置", "初始化定时任务", "定时任务调度器已在运行", "system", "INFO")
            
        if not need_morning_reminder and not need_evening_reminder:
            log_operation(db, "系统配置", "初始化定时任务", "未启用任何提醒任务", "system", "INFO")
        
        # 打印所有当前任务
        jobs = scheduler.get_jobs()
        log_operation(db, "系统配置", "初始化定时任务", f"当前共有 {len(jobs)} 个定时任务", "system", "DEBUG")
        for job in jobs:
            log_operation(db, "系统配置", "初始化定时任务", f"已添加定时任务: {job.id} ({job.name}), 下次执行: {job.next_run_time}", "system", "INFO")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        log_operation(db, "系统配置", "初始化定时任务", f"初始化定时任务失败: {e}", "system", "ERROR")
    finally:
        db.close()

def shutdown_scheduler():
    """关闭定时任务调度器"""
    db = SessionLocal()
    try:
        scheduler.shutdown()
        log_operation(db, "系统配置", "初始化定时任务", "定时任务已关闭", "system", "INFO")
    except Exception as e:
        log_operation(db, "系统配置", "初始化定时任务", f"关闭定时任务调度器失败: {e}", "system", "ERROR")