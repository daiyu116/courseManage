# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import requests
import json

from database import get_db
from models import Settings, Class
from utils.logger import log_operation
from utils.wechat_notifier import wechat_notifier
from routers.auth import get_current_system_admin_user, get_current_teaching_assistant_user, User
from routers.license import _check_premium_feature

router = APIRouter()

class SendWechatRequest(BaseModel):
    webhook_url: str
    message: str
    images: Optional[List[str]] = None
    class_id: Optional[int] = None

@router.post("/send-message")
def send_wechat_message(
    request: SendWechatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teaching_assistant_user)
):
    """发送微信消息到指定的Webhook地址（同时发送到班级webhook和导师信息群）"""
    if not _check_premium_feature('wechat_notify', db):
        raise HTTPException(status_code=403, detail="微信通知功能需要购买授权后才能使用")
    url = request.webhook_url
    message = request.message
    images = request.images or []
    class_id = request.class_id
    
    if not url:
        log_operation(db, "微信通知", "发送消息失败", "尝试发送微信消息但未提供Webhook URL", current_user.username, "ERROR")
        raise HTTPException(status_code=400, detail="Webhook URL 不能为空")
    
    if not message:
        log_operation(db, "微信通知",   "发送消息失败", "尝试发送微信消息但未提供消息内容", current_user.username, "ERROR")
        raise HTTPException(status_code=400, detail="消息内容不能为空")
    
    try:
        # 构建消息内容
        if images:
            markdown_content = message
            markdown_content += "\n\n**作业图片：**\n"
            for i, img_url in enumerate(images, 1):
                markdown_content += f"\n{i}. [图片 {i}]({img_url})"
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": markdown_content
                }
            }
        else:
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
        
        # 获取配置
        settings = db.query(Settings).first()
        enabled_classes = []
        if settings and settings.notification_settings:
            try:
                notif_config = json.loads(settings.notification_settings)
                enabled_classes = notif_config.get('enabled_classes', [])
            except:
                pass
        
        # 确定要发送的URL列表
        urls = []
        
        # 1. 添加班级webhook（如果班级在允许列表中）
        if class_id and enabled_classes is not None:
            if class_id in enabled_classes:
                urls.append(url)
                log_operation(db, "微信通知", "发送消息", f"班级ID {class_id} 在允许列表中，添加班级webhook", current_user.username, "DEBUG")
            else:
                log_operation(db, "微信通知", "发送消息", f"班级ID {class_id} 不在允许列表中，不发送到班级webhook", current_user.username, "DEBUG")
        else:
            # 没有班级ID或没有配置允许列表，发送到班级webhook
            urls.append(url)
            log_operation(db, "微信通知", "发送消息", f"添加班级webhook", current_user.username, "DEBUG")
        
        # 2. 添加导师信息群（default）
        if settings and settings.wechat_webhook_config:
            try:
                wechat_notifier.load_config(settings.wechat_webhook_config or "{}")
                config_item = wechat_notifier.webhook_config.get('schedule_arrange', {})
                if isinstance(config_item, dict) and "default" in config_item:
                    urls.extend(config_item["default"])
                    log_operation(db, "微信通知", "发送消息", f"添加导师信息群Webhook URL: {config_item['default']}", current_user.username, "DEBUG")
            except Exception as e:
                log_operation(db, "微信通知", "发送消息失败", f"加载导师信息群失败: {e}", current_user.username, "ERROR")
        
        if not urls:
            log_operation(db, "微信通知", "发送消息失败", "未配置任何微信通知地址", current_user.username, "ERROR")
            raise HTTPException(status_code=400, detail="未配置任何微信通知地址")
        
        # 发送到所有URL
        success_count = 0
        for url in urls:
            if not url: continue
            try:
                resp = requests.post(url, json=data, timeout=5)
                res_json = resp.json()
                
                if res_json.get('errcode') == 0:
                    success_count += 1
                    log_operation(db, "微信通知", "发送消息", f"发送微信消息成功: {url}", current_user.username, "DEBUG")
                else:
                    log_operation(db, "微信通知", "发送消息失败", f"发送微信消息失败，企业微信返回错误: {res_json.get('errmsg')}", current_user.username, "ERROR")
            except Exception as e:
                log_operation(db, "微信通知",   "发送消息失败", f"发送微信消息失败，网络请求错误: {str(e)}", current_user.username, "ERROR")
        
        if success_count > 0:
            return {"message": f"发送成功 {success_count}/{len(urls)}"}
        else:
            raise HTTPException(status_code=500, detail="所有发送都失败")
            
    except HTTPException:
        raise    
    except Exception as e:
        log_operation(db, "微信通知",   "发送消息失败", f"发送微信消息失败，网络请求错误: {str(e)}", current_user.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"网络请求失败: {str(e)}")