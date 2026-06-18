# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import List, Dict, Optional
import json
from database import SessionLocal
from utils.logger import log_operation

class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self):
        self.smtp_config = {}
        self.from_name = ""
        self.promotion_info = {
            "organization_website": "",
            "wechat_qrcode": "",
            "work_wechat_qrcode": ""
        }
    
    def load_config(self, config_json: str, from_name: str = ""):
        """
        加载SMTP配置
        :param config_json: JSON字符串，包含SMTP配置
        :param from_name: 发件人名称
        """
        db = SessionLocal()
        try:
            if config_json:
                self.smtp_config = json.loads(config_json)
            else:
                self.smtp_config = {}
            self.from_name = from_name
        except Exception as e:
            log_operation(db, "邮件通知", "解析邮件配置失败", f"解析邮件配置失败: {e}", "system", "ERROR")
            self.smtp_config = {}
            self.from_name = from_name
    
    def load_promotion_info(self, website: str = "", wechat_qr: str = "", work_wechat_qr: str = ""):
        """加载机构宣传信息"""
        self.promotion_info = {
            "organization_website": website or "",
            "wechat_qrcode": wechat_qr or "",
            "work_wechat_qrcode": work_wechat_qr or ""
        }

    def get_promotion_html(self) -> str:
        """获取宣传信息HTML"""
        html = '<div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">'
        if self.promotion_info.get("organization_website"):
            html += f'<p><a href="{self.promotion_info["organization_website"]}" target="_blank">🌐 访问机构官网</a></p>'
        if self.promotion_info.get("wechat_qrcode"):
            html += f'<p>关注公众号：<br/><img src="{self.promotion_info["wechat_qrcode"]}" alt="公众号二维码" style="max-width: 200px;"/></p>'
        if self.promotion_info.get("work_wechat_qrcode"):
            html += f'<p>添加企业微信：<br/><img src="{self.promotion_info["work_wechat_qrcode"]}" alt="企业微信二维码" style="max-width: 200px;"/></p>'
        html += '</div>'
        return html

    def send_email(self, to_emails: List[str], subject: str, html_content: str) -> Dict[str, bool]:
        """
        发送邮件
        :param to_emails: 收件人邮箱列表
        :param subject: 邮件主题
        :param html_content: HTML格式邮件内容
        :return: 发送结果字典 {email: success}
        """
        db = SessionLocal()
        if not to_emails:
            log_operation(db, "邮件通知", "邮件发送失败", "收件人列表为空，无法发送邮件", "system", "INFO")
            return {}
        
        if not self.smtp_config.get('smtp_host') or not self.smtp_config.get('smtp_user'):
            log_operation(db, "邮件通知", "邮件发送失败", "邮件配置不完整，无法发送邮件", "system", "ERROR")
            return {}
        
        log_operation(db, "邮件通知", "send_email 调用", f"准备发送邮件，收件人数量: {len(to_emails)}, SMTP配置: host={self.smtp_config.get('smtp_host')}, port={self.smtp_config.get('smtp_port')}, user={self.smtp_config.get('smtp_user')}", "system", "DEBUG")
        results = {}
        
        try:
            # 连接SMTP服务器
            smtp_host = self.smtp_config.get('smtp_host')
            smtp_port = self.smtp_config.get('smtp_port', 465)
            smtp_user = self.smtp_config.get('smtp_user')
            smtp_password = self.smtp_config.get('smtp_password')
            use_ssl = self.smtp_config.get('smtp_ssl', True)
            
            log_operation(db, "邮件通知", "send_email 调用", f"正在连接SMTP服务器: {smtp_host}:{smtp_port}, SSL: {use_ssl}", "system", "DEBUG")
            
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
            
            log_operation(db, "邮件通知", "send_email 调用", f"SMTP服务器连接成功，正在登录...", "system", "DEBUG")
            server.login(smtp_user, smtp_password)
            log_operation(db, "邮件通知", "send_email 调用", f"SMTP服务器登录成功", "system", "DEBUG")

            final_html = html_content + self.get_promotion_html()
            
            # 发送邮件（为每个收件人单独创建邮件对象）
            for email in to_emails:
                if not email:
                    continue
                try:
                    # 为每个收件人创建新的邮件对象
                    msg = MIMEMultipart()
                    msg['From'] = formataddr((self.from_name, self.smtp_config.get('smtp_user', '')))
                    msg['To'] = email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(final_html, 'html', 'utf-8'))
                    
                    server.sendmail(smtp_user, [email], msg.as_string())
                    results[email] = True
                    log_operation(db, "邮件通知", "邮件发送成功", f"邮件发送成功: {email}", "system", "INFO")
                except Exception as e:
                    results[email] = False
                    log_operation(db, "邮件通知", "邮件发送失败", f"邮件发送失败 {email}: {str(e)}", "system", "ERROR")
            
            server.quit()
            log_operation(db, "邮件通知", "send_email 调用", f"邮件发送完成，成功: {sum(1 for v in results.values() if v)}/{len(results)}", "system", "DEBUG")  
        
        except Exception as e:
            import traceback
            log_operation(db, "邮件通知", "邮件发送失败", f"邮件发送过程中出错: {str(e)}", "system", "ERROR")
            for email in to_emails:
                results[email] = False
        
        return results
    
    def send_course_reminder(self, schedule_list: List[Dict], title: str, to_emails: List[str], db) -> Dict[str, bool]:
        """
        发送课程提醒邮件
        :param schedule_list: 课程列表
        :param title: 提醒标题
        :param to_emails: 收件人邮箱列表
        :param db: 数据库会话
        :return: 发送结果
        """
        import os, threading
        db = SessionLocal()
        if not schedule_list or not to_emails:
            log_operation(db, "邮件通知", "send_course_reminder 调用", f"课程列表为空或收件人列表为空，跳过发送", "system", "INFO") 
            return {}
        
        log_operation(db, "邮件通知", "send_course_reminder 调用", f"函数被调用，进程ID: {os.getpid()}, 线程ID: {threading.current_thread().ident}, 线程名: {threading.current_thread().name}", "system", "DEBUG")
        log_operation(db, "邮件通知", "send_course_reminder 调用", f"课程列表: {[(s.get('class_name'), s.get('course_name'), s.get('class_id')) for s in schedule_list]}, 收件人: {to_emails}", "system", "DEBUG")
        
        # 构建邮件内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .schedule-item {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 5px; }}
                .time {{ color: #667eea; font-weight: bold; }}
                .course {{ color: #333; font-weight: bold; margin: 5px 0; }}
                .class {{ color: #666; }}
                .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{title}</h2>
                </div>
                <div class="content">
        """
        
        for schedule in schedule_list:
            # 获取学员列表
            student_list = schedule.get('student_list', [])
            active_students = [s['name'] for s in student_list if s.get('is_active', True)]
            inactive_students = [s['name'] for s in student_list if not s.get('is_active', True)]
            
            # 格式化学员列表
            student_text = ""
            if active_students:
                student_text += f"在读学员：{', '.join(active_students)}<br>"
            if inactive_students:
                student_text += f"非在读学员：{', '.join(inactive_students)}<br>"
            
            html_content += f"""
                    <div class="schedule-item">
                        <div class="time">📅 {schedule['start_date']}</div>
                        <div class="time">⏰ {schedule['start_time']} - {schedule['end_time']}</div>
                        <div class="course">📚 {schedule['course_name']}</div>
                        <div class="course">👨‍🏫 {schedule['teacher_name']}</div>
                        <div class="class">👥 {schedule['class_name']}</div>
                        <div class="class">🏫 {schedule['room_name']}</div>
                        {f'<div class="class">👥 学员：</div><div style="margin-left: 20px;">{student_text}</div>' if student_text else ''}
                    </div>
            """
        
        html_content += f"""
                </div>
                <div class="footer">
                    <p>此邮件由课程安排系统自动发送，请勿直接回复。</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_emails, title, html_content)


email_notifier = EmailNotifier()