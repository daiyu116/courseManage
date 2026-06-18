# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
"""
智能指令API - 支持自然语言指令处理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user, User
from utils.smart_command import IntentParser, CommandExecutor
from pydantic import BaseModel
from typing import Optional
from models import Settings
import json

router = APIRouter(prefix="/smart-command", tags=["智能指令"])


class SmartCommandRequest(BaseModel):
    """智能指令请求模型"""
    text: Optional[str] = None
    use_ai: bool = False


class SmartCommandPreview(BaseModel):
    """智能指令预览响应模型"""
    success: bool
    message: str
    parsed_intent: Optional[dict] = None
    preview_data: Optional[dict] = None
    requires_confirmation: bool = True


class SmartCommandConfirmRequest(BaseModel):
    """智能指令确认执行请求模型"""
    parsed_intent: dict
    confirmed: bool = True


class SmartCommandResponse(BaseModel):
    """智能指令响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None
    parsed_intent: Optional[dict] = None


def get_ai_config(db: Session) -> dict:
    """获取AI配置"""
    settings = db.query(Settings).first()
    if settings and settings.ai_config:
        try:
            return json.loads(settings.ai_config)
        except:
            return {}
    return {}


@router.post("/preview", response_model=SmartCommandPreview)
async def preview_smart_command(
    request: SmartCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预览智能指令解析结果（不执行）
    
    返回解析后的参数供用户确认
    """
    from routers.license import _check_premium_feature
    if not _check_premium_feature('smart_command', db):
        raise HTTPException(status_code=403, detail="智能指令功能需要购买授权后才能使用")
    import time
    start_time = time.time()
    
    if not request.text:
        raise HTTPException(status_code=400, detail="请提供指令文本")
    
    # 获取AI配置
    ai_config = get_ai_config(db)
    
    # 创建解析器
    parser = IntentParser(use_ai=request.use_ai, ai_config=ai_config)
    
    parsed_result = parser.parse(request.text, db, current_user.id)
    
    if not parsed_result:
        return SmartCommandPreview(
            success=False,
            message="无法理解您的指令，请尝试更清晰的表达",
            parsed_intent=None,
            preview_data=None,
            requires_confirmation=False
        )
    
    # 处理 parsed_result：将 storage_data 中的字段提取到顶层，并转换字段名
    processed_parsed_result = parsed_result.copy()
    if 'storage_data' in parsed_result:
        for key, value in parsed_result['storage_data'].items():
            # 将驼峰命名转换为下划线命名
            snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
            processed_parsed_result[snake_key] = value
            
            # 同时保留一些常用的驼峰命名，以防前端直接使用
            if key in ['studentNames', 'className', 'courseName', 'teacherName', 'roomName', 
                       'dayOfWeek', 'startTime', 'endTime', 'startDate', 'endDate']:
                processed_parsed_result[key] = value
    
    # 生成预览数据（包含自动推断的班级和导师）
    from .smart_command_helpers import generate_preview_data
    preview_data = generate_preview_data(processed_parsed_result, db)
    
    # 将预览数据中推断的字段更新回 processed_parsed_result 的 storage_data
    # 这样前端在执行导航时，能获取到完整的推断结果
    if 'storage_data' not in processed_parsed_result:
        processed_parsed_result['storage_data'] = {}
    
    # 从 preview_data.fields 中提取推断的班级和导师信息
    for field in preview_data.get('fields', []):
        if field['label'] == '班级' and field['value'] != '未提供':
            processed_parsed_result['storage_data']['className'] = field['value']
            processed_parsed_result['storage_data']['class_name'] = field['value']
        elif field['label'] == '导师' and field['value'] != '未提供':
            processed_parsed_result['storage_data']['teacherName'] = field['value']
            processed_parsed_result['storage_data']['teacher_name'] = field['value']
    
    # 确保storage_data中包含所有必要字段，即使某些字段为空也要保留
    # 这样前端才能正确读取和转换
    if processed_parsed_result.get('action') == 'create_schedule' or \
       (processed_parsed_result.get('action') == 'navigate' and 
        '/schedules' in processed_parsed_result.get('path', '')):
        
        storage = processed_parsed_result['storage_data']
        
        # 对于navigate动作，字段已经在storage_data中了
        # 需要从storage_data内部进行字段名标准化（下划线转驼峰）
        if processed_parsed_result.get('action') == 'navigate':
            # 不仅检查字段是否存在，还要检查是否为有效值
            # 如果字段是null、空字符串或空列表，也需要补充
            
            # studentNames
            if not storage.get('studentNames'):
                storage['studentNames'] = storage.get('person_names') or storage.get('student_names') or []
            if not storage.get('student_names'):
                storage['student_names'] = storage.get('studentNames') or storage.get('person_names') or []
            
            # className
            if not storage.get('className'):
                storage['className'] = storage.get('class_name') or ''
            if not storage.get('class_name'):
                storage['class_name'] = storage.get('className') or ''
            
            # courseName
            if not storage.get('courseName'):
                storage['courseName'] = storage.get('course_name') or ''
            if not storage.get('course_name'):
                storage['course_name'] = storage.get('courseName') or ''
            
            # teacherName（可以为null，所以不强制补充）
            if 'teacherName' not in storage:
                storage['teacherName'] = storage.get('teacher_name')
            if 'teacher_name' not in storage:
                storage['teacher_name'] = storage.get('teacherName')
            
            # roomName（可以为null，所以不强制补充）
            if 'roomName' not in storage:
                storage['roomName'] = storage.get('room_name')
            if 'room_name' not in storage:
                storage['room_name'] = storage.get('roomName')
            
            # dayOfWeek
            if 'dayOfWeek' not in storage:
                storage['dayOfWeek'] = storage.get('day_of_week')
            if 'day_of_week' not in storage:
                storage['day_of_week'] = storage.get('dayOfWeek')
            
            # startTime
            if not storage.get('startTime'):
                storage['startTime'] = storage.get('start_time') or ''
            if not storage.get('start_time'):
                storage['start_time'] = storage.get('startTime') or ''
            
            # endTime
            if not storage.get('endTime'):
                storage['endTime'] = storage.get('end_time') or ''
            if not storage.get('end_time'):
                storage['end_time'] = storage.get('endTime') or ''
            
            # startDate
            if not storage.get('startDate'):
                storage['startDate'] = storage.get('start_date') or ''
            if not storage.get('start_date'):
                storage['start_date'] = storage.get('startDate') or ''
            
            # endDate
            if not storage.get('endDate'):
                storage['endDate'] = storage.get('end_date') or ''
            if not storage.get('end_date'):
                storage['end_date'] = storage.get('endDate') or ''
        else:
            # 对于create_schedule动作，字段在顶层，需要从顶层复制到storage_data
            if 'studentNames' not in storage and 'person_names' in processed_parsed_result:
                storage['studentNames'] = processed_parsed_result['person_names']
            if 'student_names' not in storage and 'person_names' in processed_parsed_result:
                storage['student_names'] = processed_parsed_result['person_names']
            
            if 'className' not in storage and 'class_name' in processed_parsed_result:
                storage['className'] = processed_parsed_result['class_name']
            if 'class_name' not in storage and 'class_name' in processed_parsed_result:
                storage['class_name'] = processed_parsed_result['class_name']
            
            if 'courseName' not in storage and 'course_name' in processed_parsed_result:
                storage['courseName'] = processed_parsed_result['course_name']
            if 'course_name' not in storage and 'course_name' in processed_parsed_result:
                storage['course_name'] = processed_parsed_result['course_name']
            
            if 'teacherName' not in storage and 'teacher_name' in processed_parsed_result:
                storage['teacherName'] = processed_parsed_result['teacher_name']
            if 'teacher_name' not in storage and 'teacher_name' in processed_parsed_result:
                storage['teacher_name'] = processed_parsed_result['teacher_name']
            
            if 'roomName' not in storage and 'room_name' in processed_parsed_result:
                storage['roomName'] = processed_parsed_result['room_name']
            if 'room_name' not in storage and 'room_name' in processed_parsed_result:
                storage['room_name'] = processed_parsed_result['room_name']
            
            if 'dayOfWeek' not in storage and 'day_of_week' in processed_parsed_result:
                storage['dayOfWeek'] = processed_parsed_result['day_of_week']
            if 'day_of_week' not in storage and 'day_of_week' in processed_parsed_result:
                storage['day_of_week'] = processed_parsed_result['day_of_week']
            
            if 'startTime' not in storage and 'start_time' in processed_parsed_result:
                storage['startTime'] = processed_parsed_result['start_time']
            if 'start_time' not in storage and 'start_time' in processed_parsed_result:
                storage['start_time'] = processed_parsed_result['start_time']
            
            if 'endTime' not in storage and 'end_time' in processed_parsed_result:
                storage['endTime'] = processed_parsed_result['end_time']
            if 'end_time' not in storage and 'end_time' in processed_parsed_result:
                storage['end_time'] = processed_parsed_result['end_time']
            
            if 'startDate' not in storage and 'start_date' in processed_parsed_result:
                storage['startDate'] = processed_parsed_result['start_date']
            if 'start_date' not in storage and 'start_date' in processed_parsed_result:
                storage['start_date'] = processed_parsed_result['start_date']
            
            if 'endDate' not in storage and 'end_date' in processed_parsed_result:
                storage['endDate'] = processed_parsed_result['end_date']
            if 'end_date' not in storage and 'end_date' in processed_parsed_result:
                storage['end_date'] = processed_parsed_result['end_date']
    
    return SmartCommandPreview(
        success=True,
        message="解析成功，请确认以下信息",
        parsed_intent=processed_parsed_result,
        preview_data=preview_data,
        requires_confirmation=True
    )

@router.post("/execute", response_model=SmartCommandResponse)
async def execute_smart_command(
    request: SmartCommandConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行已确认的智能指令
    
    需要传入之前预览时返回的parsed_intent
    """
    from routers.license import _check_premium_feature
    if not _check_premium_feature('smart_command', db):
        raise HTTPException(status_code=403, detail="智能指令功能需要购买授权后才能使用")
    if not request.confirmed:
        return SmartCommandResponse(
            success=False,
            message="用户取消执行",
            parsed_intent=request.parsed_intent
        )
    
    # 执行指令
    executor = CommandExecutor(db, current_user.id, current_user.username)
    execution_result = executor.execute(request.parsed_intent)
    
    return SmartCommandResponse(
        success=execution_result.get('success', False),
        message=execution_result.get('message', ''),
        data=execution_result.get('data'),
        parsed_intent=request.parsed_intent
    )

@router.get("/help")
async def get_command_help():
    """获取智能指令帮助信息（从数据库动态读取示例）"""
    from database import SessionLocal
    from models import SmartCommandExample
    import json
    
    db = SessionLocal()
    try:
        # 从数据库获取所有激活的示例
        examples = db.query(SmartCommandExample)\
                     .filter(SmartCommandExample.is_active == True)\
                     .order_by(SmartCommandExample.sort_order, SmartCommandExample.id)\
                     .all()
        
        # 按分类组织示例
        categories_dict = {}
        for example in examples:
            category = example.category
            
            if category not in categories_dict:
                categories_dict[category] = {
                    "category": "",
                    "commands": []
                }
            
            # 解析预期字段
            try:
                expected_fields = json.loads(example.expected_fields) if example.expected_fields else {}
            except:
                expected_fields = {}
            
            # 构建命令对象
            command_obj = {
                "action": example.action_name,
                "examples": [example.example_text],
                "description": example.description or ""
            }
            
            # 查找是否已有相同action的命令
            existing_command = None
            for cmd in categories_dict[category]["commands"]:
                if cmd["action"] == example.action_name:
                    existing_command = cmd
                    break
            
            if existing_command:
                # 如果已存在，追加示例
                existing_command["examples"].append(example.example_text)
            else:
                # 否则添加新命令
                categories_dict[category]["commands"].append(command_obj)
        
        # 转换为列表格式
        supported_commands = []
        for category_key, category_data in categories_dict.items():
            # 设置分类名称（可以根据category_key映射为中文）
            category_names = {
                "course_management": "科目管理",
                "teacher_management": "导师管理",
                "student_management": "学员管理",
                "class_management": "班级管理",
                "room_management": "教室管理",
                "schedule_management": "排课管理",
                "leave_management": "请假管理",
                "holiday_management": "假期管理",
                "fee_management": "课费管理",
                "grade_management": "成绩管理",
                "data_search": "数据查询"
            }
            category_data["category"] = category_names.get(category_key, category_key)
            supported_commands.append(category_data)
        
        return {
            "title": "智能指令帮助",
            "description": "支持通过自然语言或语音执行各种操作，系统会自动解析并生成预览供您确认",
            "usage_tips": [
                "尽量使用清晰、简洁的语言描述您的需求",
                "可以提供更多细节以提高准确性（如电话、邮箱、日期等）",
                "支持语音输入，点击麦克风按钮即可（需要Chrome或Edge浏览器）",
                "系统会先显示预览，确认后再执行写入数据库",
                "如果指令不明确或缺少信息，系统会提示您补充",
                "如果识别到相似项，会在预览中列出供您选择确认",
                "一次只执行一个操作，如需多个操作请分开输入并分开执行（例如：先说'添加班级1v1-senior03-004'，等执行上一条之后，再说'给张三安排明天上午10点到12点的英语课'）"
            ],
            "supported_commands": supported_commands if supported_commands else [
                {
                    "category": "暂无示例",
                    "commands": [
                        {
                            "action": "请先在'智能指令示例管理'中添加示例",
                            "examples": [],
                            "description": "管理员可以在站点参数-人工智能配置中管理智能指令示例"
                        }
                    ]
                }
            ],
            "feedback_format": {
                "description": "完成课程时的内容反馈格式说明",
                "format": "内容|作业|注意",
                "example": "内容：函数概念与性质|作业：课本第50页练习题1-10|注意：重点讲解定义域和值域",
                "note": "三个部分用竖线(|)分隔，可以只提供部分内容，如：内容：三角函数|作业：课后习题"
            },
            "date_format": {
                "description": "日期格式说明",
                "format": "YYYY-MM-DD",
                "example": "2024-01-15",
                "special_values": ["今天", "明天", "后天", "大后天"]
            },
            "time_format": {
                "description": "时间格式说明 - 支持多种表达方式",
                "formats": [
                    {
                        "type": "阿拉伯数字+点",
                        "example": "2点到4点、10点到12点",
                        "result": "02:00-04:00、10:00-12:00"
                    },
                    {
                        "type": "阿拉伯数字+点半",
                        "example": "2点半到4点半",
                        "result": "02:30-04:30（上午）或14:30-16:30（下午）"
                    },
                    {
                        "type": "中文数字+点",
                        "example": "两点到四点、两点半到四点半",
                        "result": "02:00-04:00或14:00-16:00（根据上下文判断）"
                    },
                    {
                        "type": "标准时间格式",
                        "example": "14:30-16:30、08:00-10:00",
                        "result": "14:30-16:30、08:00-10:00"
                    },
                    {
                        "type": "带分钟表达",
                        "example": "2点30分到4点30分",
                        "result": "02:30-04:30或14:30-16:30（根据上下文判断）"
                    }
                ],
                "note": "系统会根据'上午'、'下午'、'晚上'等关键词自动调整时间（下午/晚上的时间会自动+12小时）"
            },
            "weekday_format": {
                "description": "星期格式说明",
                "format": "周一、周二、周三、周四、周五、周六、周日",
                "example": "周一上午、周三下午"
            },
            "interaction_flow": {
                "step1": "用户输入自然语言指令",
                "step2": "系统解析指令并生成预览",
                "step3": "用户查看预览，确认信息是否正确",
                "step4": "如果有缺失信息或错误，系统会提示补充或修正",
                "step5": "用户确认后，系统执行操作并写入数据库",
                "step6": "系统返回执行结果"
            },
            "error_handling": {
                "similar_items": "如果未找到精确匹配的项目，系统会查找相似项并在预览中列出供您选择",
                "missing_info": "如果缺少必要信息，系统会明确提示需要补充的内容",
                "duplicate_check": "系统会自动检查是否存在重复记录，并在预览中标注",
                "validation": "所有数据在写入数据库前都会经过验证，确保数据完整性"
            }
        }
    finally:
        db.close()