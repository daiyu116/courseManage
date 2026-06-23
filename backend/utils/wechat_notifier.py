# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
import requests
import json
from typing import Optional, List, Dict
import os
from database import SessionLocal
from utils.logger import log_operation

class WeChatNotifier:
    """企业微信机器人通知器 - 支持多群动态配置"""
    
    def __init__(self):
        self.webhook_config = {}
        self.notification_settings = {"morning_reminder": False, "evening_reminder": False}
        self.promotion_info = {
            "organization_website": "",
            "wechat_qrcode": "",
            "work_wechat_qrcode": ""
        }

    def load_config(self, config_json: str):
        """
        加载配置
        :param config_json: JSON字符串，格式如：
        {
            "schedule_arrange": {"default": ["url1"], "class_1": ["url2"]},
            "fee_alert": ["url3"]
        }
        """
        db = SessionLocal()
        log_operation(db, "系统配置", "load_config 调用", f"传入的 config_json: {config_json}", "system", "DEBUG")  

        try:
            if config_json:
                self.webhook_config = json.loads(config_json)
                migrated = self._migrate_legacy_keys()
                if migrated:
                    self._persist_migrated_config()
                log_operation(db, "系统配置", "load_config 调用", f"解析后的 webhook_config: {self.webhook_config}", "system", "DEBUG")
            else:
                self.webhook_config = {}
                log_operation(db, "系统配置", "load_config 调用", f"使用空配置", "system", "DEBUG")
        except Exception as e:
            log_operation(db, "系统配置", "load_config 调用", f"解析微信配置失败: {e}", "system", "ERROR")
            self.webhook_config = {}

    def _migrate_legacy_keys(self) -> bool:
        """将旧key名 schedule_change/schedule_create 迁移为 schedule_arrange，返回是否有变更"""
        migrated = False

        if "schedule_change" in self.webhook_config:
            self.webhook_config["schedule_arrange"] = self.webhook_config.pop("schedule_change")
            migrated = True

        if "schedule_create" in self.webhook_config:
            create_config = self.webhook_config.pop("schedule_create")
            if "schedule_arrange" not in self.webhook_config:
                self.webhook_config["schedule_arrange"] = create_config
            elif isinstance(create_config, dict) and isinstance(self.webhook_config["schedule_arrange"], dict):
                for key, value in create_config.items():
                    if key not in self.webhook_config["schedule_arrange"]:
                        self.webhook_config["schedule_arrange"][key] = value
                    elif key == "default":
                        merged = list(dict.fromkeys(self.webhook_config["schedule_arrange"]["default"] + value))
                        self.webhook_config["schedule_arrange"]["default"] = merged
            migrated = True

        return migrated

    def _persist_migrated_config(self):
        """将迁移后的配置回写到数据库"""
        db = None
        try:
            db = SessionLocal()
            from models import Settings
            settings = db.query(Settings).first()
            if settings:
                settings.wechat_webhook_config = json.dumps(self.webhook_config, ensure_ascii=False)
                db.commit()
                log_operation(db, "系统配置", "自动迁移", "已将 schedule_change/schedule_create 迁移为 schedule_arrange 并回写数据库", "system", "INFO")
        except Exception as e:
            if db:
                try:
                    log_operation(db, "系统配置", "自动迁移", f"回写迁移配置失败: {e}", "system", "WARNING")
                except:
                    pass

    def load_promotion_info(self, website: str = "", wechat_qr: str = "", work_wechat_qr: str = ""):
        """加载机构宣传信息"""
        self.promotion_info = {
            "organization_website": website or "",
            "wechat_qrcode": wechat_qr or "",
            "work_wechat_qrcode": work_wechat_qr or ""
        }
    
    def get_promotion_footer(self) -> str:
        """获取宣传信息footer"""
        footer = "\n\n---\n"
        if self.promotion_info.get("organization_website"):
            footer += f"[🌐 机构官网]({self.promotion_info['organization_website']})\n"
        if self.promotion_info.get("wechat_qrcode"):
            footer += f"![公众号二维码]({self.promotion_info['wechat_qrcode']})\n"
        if self.promotion_info.get("work_wechat_qrcode"):
            footer += f"![企业微信二维码]({self.promotion_info['work_wechat_qrcode']})\n"
        return footer
    
    def load_notification_settings(self, settings_json: str):
        try:
            self.notification_settings = json.loads(settings_json) if settings_json else {}
        except:
            self.notification_settings = {}

    def send_message_by_type(self, msg_type: str, content: str, class_id: int = None, class_webhook: str = None, is_markdown: bool = False, enabled_classes: list = None) -> Dict[str, bool]:
        """
        根据消息类型发送通知
        :param msg_type: 消息类型 (e.g., 'schedule_arrange', 'fee_alert')
        :param class_id: 班级ID，用于匹配特定班级的群
        :param class_webhook: 班级webhook地址（优先使用）
        :param content: 消息内容
        :param is_markdown: 是否为Markdown格式
        :param enabled_classes: 允许发送通知的班级ID列表
        :return: 返回发送结果字典，包含 success（是否成功）和 message（错误信息）
        """
        db = SessionLocal()
        urls = []
        config_item = self.webhook_config.get(msg_type, {})
        log_operation(db, "微信通知", "send_message_by_type 调用", f"消息类型: {msg_type}, 班级ID: {class_id}, 允许的班级列表: {enabled_classes}, 配置项: {config_item}", "system", "DEBUG")
        
        # 检查班级是否在允许列表中
        class_allowed = True
        log_operation(db, "微信通知", "send_message_by_type 调用", f"检查班级ID {class_id} 是否在允许列表 {enabled_classes} 中", "system", "DEBUG")
        if class_id is not None and enabled_classes is not None:
            # 如果enabled_classes为空列表，按照业务逻辑应允许所有班级
            # 因为定时任务能正常工作，说明配置是存在的
            if len(enabled_classes) == 0:
                log_operation(db, "微信通知", "send_message_by_type 调用", f"enabled_classes为空列表，允许所有班级发送通知（可能是未设置特定班级限制）", "system", "DEBUG") 
                class_allowed = True
            else:
                # enabled_classes不为空，检查班级是否在列表中
                if class_id in enabled_classes:
                    log_operation(db, "微信通知", "send_message_by_type 调用", f"班级ID {class_id} 在允许列表中", "system", "DEBUG")
                    class_allowed = True
                else:
                    log_operation(db, "微信通知", "send_message_by_type 调用", f"班级ID {class_id} 不在允许的班级列表中: {enabled_classes}", "system", "DEBUG")
                    class_allowed = False
        else:
            log_operation(db, "微信通知", "send_message_by_type 调用", f"班级ID或enabled_classes为None，无法检查，允许发送", "system", "DEBUG")
            class_allowed = True

        # 1. 使用班级表中的webhook地址（仅当班级在允许列表中）
        if class_allowed and class_webhook:       
            urls.append(class_webhook)
            log_operation(db, "微信通知", "send_message_by_type 调用", f"使用班级表中的webhook: {class_webhook}", "system", "DEBUG")
        # 2. 从全局配置中查找导师信息群webhook地址（不管班级webhook是否存在，都要检查）
        if isinstance(config_item, dict):
            # 先添加班级群（如果存在且班级在允许列表中）
            if class_allowed and class_id and f"class_{class_id}" in config_item:
                urls.extend(config_item[f"class_{class_id}"])
                log_operation(db, "微信通知", "send_message_by_type 调用", f"使用全局配置中的班级webhook: class_{class_id}", "system", "DEBUG")
            # 再添加导师信息群（default）
            if "default" in config_item:
                urls.extend(config_item["default"])
                log_operation(db, "微信通知", "send_message_by_type 调用", f"使用全局配置中的默认webhook: default", "system", "DEBUG")
            else:
                # 回退：如果当前消息类型没有default配置，尝试从schedule_arrange中获取教师群webhook
                fallback_config = self.webhook_config.get("schedule_arrange", {})
                if isinstance(fallback_config, dict) and "default" in fallback_config:
                    urls.extend(fallback_config["default"])
                    log_operation(db, "微信通知", "send_message_by_type 调用", f"当前消息类型 {msg_type} 无default配置，回退使用schedule_arrange的默认webhook", "system", "DEBUG")
        # 3. 如果是列表结构（针对通用提醒，如缴费）
        elif isinstance(config_item, list):
            urls.extend(config_item)

        if not urls:
            error_message = "未配置微信通知地址"
            if class_id and not class_allowed:
                error_message = f"该班级不属于允许微信通知的班级中，且未配置导师信息群，如需向该班级发送微信通知，请联系系统管理员修改'课程安排提醒-班级信息群'班级列表，同时保证该班级webhook地址准确。"
            log_operation(db, "微信通知", "send_message_by_type 调用", error_message, "system", "ERROR")
            return {
                "success": False,
                "message": error_message
            }

        results = {}
        for url in urls:
            if not url: continue
            final_content = content + self.get_promotion_footer()
            data = {
                "msgtype": "markdown" if is_markdown else "text",
                ("markdown" if is_markdown else "text"): {"content": final_content}
            }
            try:
                resp = requests.post(url, json=data, timeout=5)
                res_json = resp.json()
                results[url] = (res_json.get('errcode') == 0)
            except Exception as e:
                log_operation(db, "微信通知", "send_message_by_type 调用", f"发送到 {url} 失败: {str(e)}", "system", "ERROR")
                results[url] = False
        
        # 如果有URL列表，返回成功状态
        if urls:
            success_count = sum(1 for v in results.values() if v)
            return {
                "success": success_count > 0,
                "message": f"微信通知发送成功 {success_count}/{len(results)}" if success_count > 0 else "微信通知发送失败",
                "results": results
            }
        else:
            return {
                "success": False,
                "message": "未配置微信通知地址",
                "results": results
            }

    def _build_course_content(self, schedule_list: List[Dict], title: str) -> str:
        """构建课程提醒消息内容"""
        content = f"## {title}\n\n"
        for schedule in schedule_list:
            student_list = schedule.get('student_list', [])
            active_students = [s['name'] for s in student_list if s.get('is_active', True)]
            inactive_students = [s['name'] for s in student_list if not s.get('is_active', True)]

            student_text = ""
            if active_students:
                student_text += f"在读学员：{', '.join(active_students)}\n"
            if inactive_students:
                student_text += f"非在读学员：{', '.join(inactive_students)}\n"

            content += f"- **日期**: {schedule['start_date']}\n"
            content += f"  **时间**: {schedule['start_time']}-{schedule['end_time']}\n"
            content += f"  **科目**: {schedule['course_name']}\n"
            content += f"  **导师**: {schedule['teacher_name']}\n"
            content += f"  **班级**: {schedule['class_name']}\n"
            if student_text:
                content += f"  **学员**:\n"
                for line in student_text.split('\n'):
                    if line:
                        content += f"    {line}\n"
            content += f"  **教室**: {schedule['room_name']}\n\n"
        return content

    def send_course_reminder(self, schedule_list: List[Dict], title: str, class_webhooks: Dict[int, str] = None, enabled_classes: list = None) -> Dict[str, bool]:
        """
        发送课程提醒（教师群发送所有课程汇总，班级群发送本班级课程）
        :param schedule_list: 课程列表
        :param title: 提醒标题
        :param class_webhooks: 班级webhook地址字典 {class_id: webhook_url}
        :param enabled_classes: 允许发送通知的班级ID列表
        """
        import os, threading
        if not schedule_list:
            return {}
        db = SessionLocal()
        log_operation(db, "微信通知", "send_course_reminder 调用", f"进程ID: {os.getpid()}, 线程ID: {threading.current_thread().ident}, 线程名: {threading.current_thread().name}", "system", "DEBUG")
        log_operation(db, "微信通知", "send_course_reminder 调用", f"标题: {title}, 课程数: {len(schedule_list)}, 课程列表: {[(s.get('class_name'), s.get('course_name'), s.get('class_id')) for s in schedule_list]}, enabled_classes: {enabled_classes}", "system", "DEBUG")
        all_results = {}

        # === 第一步：向教师群（导师信息群）发送所有课程的汇总消息 ===
        teacher_urls = []
        if isinstance(self.webhook_config.get('schedule_arrange'), dict):
            teacher_urls = self.webhook_config['schedule_arrange'].get('default', [])

        if teacher_urls:
            teacher_content = self._build_course_content(schedule_list, title)
            final_content = teacher_content + self.get_promotion_footer()
            log_operation(db, "微信通知", "send_course_reminder 调用", f"向导师信息群发送汇总消息，课程数: {len(schedule_list)}, URL数: {len(teacher_urls)}", "system", "DEBUG")
            for url in teacher_urls:
                if not url:
                    continue
                try:
                    response = requests.post(
                        url,
                        json={"msgtype": "markdown", "markdown": {"content": final_content}},
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    all_results[url] = response.status_code == 200
                    log_operation(db, "微信通知", "send_course_reminder 调用", f"导师信息群发送到 {url[:80]}...结果: {'成功' if response.status_code == 200 else '失败'}, 状态码: {response.status_code}", "system", "DEBUG")
                except Exception as e:
                    log_operation(db, "微信通知", "send_course_reminder 调用", f"导师信息群发送到 {url[:80]}...异常: {str(e)}", "system", "ERROR")
                    all_results[url] = False
        else:
            log_operation(db, "微信通知", "send_course_reminder 调用", "未配置导师信息群webhook，跳过教师群发送", "system", "DEBUG")

        # === 第二步：按班级分组，向各班级群发送本班级课程消息 ===
        class_groups = {}
        for schedule in schedule_list:
            class_id = schedule.get('class_id')
            if class_id not in class_groups:
                class_groups[class_id] = []
            class_groups[class_id].append(schedule)

        for class_id, class_schedules in class_groups.items():
            class_allowed = True
            if enabled_classes is not None and len(enabled_classes) > 0 and class_id not in enabled_classes:
                log_operation(db, "微信通知", "send_course_reminder 调用", f"班级ID {class_id} 不在允许的班级列表中: {enabled_classes}，跳过班级群发送", "system", "DEBUG")
                class_allowed = False

            if not class_allowed:
                continue

            class_url = None
            if class_webhooks and class_id in class_webhooks:
                class_url = class_webhooks[class_id]
                log_operation(db, "微信通知", "send_course_reminder 调用", f"使用班级表中的webhook: {class_url}", "system", "DEBUG")
            else:
                class_key = f"class_{class_id}"
                if isinstance(self.webhook_config.get('schedule_arrange'), dict):
                    fallback_urls = self.webhook_config['schedule_arrange'].get(class_key, [])
                    if fallback_urls:
                        class_url = fallback_urls[0]
                        log_operation(db, "微信通知", "send_course_reminder 调用", f"使用全局配置中的班级webhook: {class_key}", "system", "DEBUG")

            if not class_url:
                log_operation(db, "微信通知", "send_course_reminder 调用", f"班级ID {class_id} 未配置班级群webhook地址，跳过班级群发送", "system", "DEBUG")
                continue

            class_content = self._build_course_content(class_schedules, title)
            final_content = class_content + self.get_promotion_footer()
            log_operation(db, "微信通知", "send_course_reminder 调用", f"向班级群发送消息，班级ID: {class_id}, 班级名: {class_schedules[0].get('class_name')}, 课程数: {len(class_schedules)}", "system", "DEBUG")
            try:
                response = requests.post(
                    class_url,
                    json={"msgtype": "markdown", "markdown": {"content": final_content}},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                all_results[class_url] = response.status_code == 200
                log_operation(db, "微信通知", "send_course_reminder 调用", f"班级群 {class_schedules[0].get('class_name')} 发送到 {class_url[:80]}...结果: {'成功' if response.status_code == 200 else '失败'}, 状态码: {response.status_code}", "system", "DEBUG")
            except Exception as e:
                log_operation(db, "微信通知", "send_course_reminder 调用", f"班级群 {class_schedules[0].get('class_name')} 发送到 {class_url[:80]}...异常: {str(e)}", "system", "ERROR")
                all_results[class_url] = False

        return all_results

wechat_notifier = WeChatNotifier()