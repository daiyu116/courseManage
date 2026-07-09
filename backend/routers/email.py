# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
import requests
import smtplib
import json

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.utils import formataddr

from database import get_db
from models import Settings, Student, Class
from utils.logger import log_operation
from routers.auth import get_current_system_admin_user, get_current_teaching_assistant_user, User
from schemas import SendEmailHomeworkRequest

router = APIRouter()

@router.post("/send-homework")
def send_email_homework(
    request: SendEmailHomeworkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teaching_assistant_user)
):
    """发送作业安排邮件（同时发送给学员和家长）"""
    settings = db.query(Settings).first()
    if not settings:
        log_operation(db, "邮件通知", "发送作业邮件失败", "尝试发送作业邮件但站点参数不存在", current_user.username, "ERROR")
        raise HTTPException(status_code=404, detail="站点参数不存在")
    
    try:
        email_config = json.loads(settings.email_config or '{}')
    except json.JSONDecodeError:
        log_operation(db, "邮件通知", "发送作业邮件失败", "邮件配置格式错误，无法解析为JSON", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail="邮件配置格式错误")
    
    class_info = db.query(Class).filter(Class.id == request.class_id).first()
    if not class_info:
        log_operation(db, "邮件通知", "发送作业邮件失败", f"尝试发送作业邮件但班级ID {request.class_id} 不存在", current_user.username, "ERROR")
        raise HTTPException(status_code=404, detail="班级不存在")
    
    students = db.query(Student).join(Student.classes).filter(
        Class.id == request.class_id,
        Student.is_active == True
    ).all()
    
    if not students:
        return {"message": "班级中没有在读学员"}
    
    students_with_email = [s for s in students if s.email]
    if not students_with_email:
        return {"message": "班级中没有配置邮箱的学员"}
    
    msg = MIMEMultipart()
    msg['From'] = formataddr((email_config.get('smtp_from_name', settings.site_name), email_config.get('smtp_user', '')))
    msg['Subject'] = f"【{settings.site_name}】作业安排通知 - {request.course_name}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
            .homework-item {{ margin: 15px 0; padding: 15px; background: white; border-left: 4px solid #409eff; }}
            .footer {{ margin-top: 20px; text-align: center; color: #909399; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📚 作业安排通知</h2>
            </div>
            <div class="content">
                <div class="homework-item">
                    <h3 style="color: #409EFF; margin-top: 0;">课程：{request.course_name}</h3>
                </div>
                {f'<div class="homework-item"><strong>随堂作业：</strong><br>{request.class_homework}</div>' if request.class_homework else ''}
                {f'<div class="homework-item"><strong>常规作业：</strong><br>{request.regular_homework}</div>' if request.regular_homework else ''}
                {f'<div class="homework-item"><strong>作业图片：</strong></div>' if request.images else ''}
                <p style="margin-top: 20px; color: #909399;">
                    温馨提示：请同学们按时完成作业，如有疑问请及时联系老师。
                </p>
            </div>
            <div class="footer">
                <p>{settings.site_name} · 课程安排系统</p>
            </div>
            {f'''
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                {f'<p><a href="{settings.organization_website}" target="_blank" style="color: #409eff; text-decoration: none;">🌐 访问机构官网</a></p>' if settings.organization_website else ''}
                {f'<p style="text-align: center;">关注公众号：<br/><img src="{settings.wechat_qrcode}" alt="公众号二维码" style="max-width: 200px;"/></p>' if settings.wechat_qrcode else ''}
                {f'<p style="text-align: center;">添加企业微信：<br/><img src="{settings.work_wechat_qrcode}" alt="企业微信二维码" style="max-width: 200px;"/></p>' if settings.work_wechat_qrcode else ''}
            </div>
            ''' if (settings.organization_website or settings.wechat_qrcode or settings.work_wechat_qrcode) else ''}
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    
    if request.images:
        for i, img_url in enumerate(request.images, 1):
            try:
                response = requests.get(img_url, timeout=10)
                img_data = response.content
                img = MIMEImage(img_data)
                img.add_header('Content-ID', f'<image{i}>')
                msg.attach(img)
            except Exception as e:
                log_operation(db, "邮件通知", "下载图片失败", f"尝试下载作业图片但失败: {img_url}, error: {str(e)}", current_user.username, "WARNING")
    
    success_count = 0
    for student in students_with_email:
        try:
            msg['To'] = student.email
            
            if email_config.get('smtp_ssl', True):
                smtp = smtplib.SMTP_SSL(email_config.get('smtp_host', ''), email_config.get('smtp_port', 465))
            else:
                smtp = smtplib.SMTP(email_config.get('smtp_host', ''), email_config.get('smtp_port', 465))
            
            smtp.login(email_config.get('smtp_user', ''), email_config.get('smtp_password', ''))
            smtp.send_message(msg)
            smtp.quit()
            success_count += 1
        except Exception as e:
            log_operation(db, "邮件通知", "发送邮件失败", f"尝试发送作业邮件给 {student.email} 但失败: {str(e)}", current_user.username, "ERROR")
    
    log_operation(db, "邮件通知", "发送作业邮件", f"作业邮件发送完成: 成功{success_count}/{len(students_with_email)}", current_user.username, "INFO")
    return {"message": f"作业邮件发送完成，成功{success_count}/{len(students_with_email)}"}