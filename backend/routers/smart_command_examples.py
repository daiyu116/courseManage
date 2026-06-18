# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import SmartCommandExample
from schemas import (
    SmartCommandExampleCreate, 
    SmartCommandExampleUpdate, 
    SmartCommandExampleResponse,
    SmartCommandTestRequest,
    SmartCommandTestResult,
    SmartCommandBatchTestResult
)
from routers.auth import get_current_system_admin_user, User
from utils.logger import log_operation
from typing import List, Optional
from datetime import datetime
import json
import time

router = APIRouter()

# ==================== 辅助函数 ====================
def _require_smart_command_license(db: Session):
    from routers.license import _check_premium_feature
    if not _check_premium_feature('smart_command', db):
        raise HTTPException(status_code=403, detail="智能指令功能需要购买授权后才能使用")

def compare_fields(expected: dict, actual: dict) -> dict:
    """
    深度比较两个字典，返回匹配详情
    
    Returns:
        {
            "match_rate": 0.85,
            "matched_fields": ["field1", "field2"],
            "missing_fields": ["field3"],
            "extra_fields": ["field4"],
            "mismatched_fields": {"field5": {"expected": "val1", "actual": "val2"}}
        }
    """
    if not expected and not actual:
        return {
            "match_rate": 1.0,
            "matched_fields": [],
            "missing_fields": [],
            "extra_fields": [],
            "mismatched_fields": {}
        }
    
    expected_keys = set(expected.keys()) if expected else set()
    actual_keys = set(actual.keys()) if actual else set()
    
    matched_fields = []
    mismatched_fields = {}
    
    # 检查共同字段
    common_keys = expected_keys & actual_keys
    for key in common_keys:
        exp_val = expected[key]
        act_val = actual[key]
        
        # 简单比较（可以根据需要扩展为深度比较）
        if str(exp_val).lower() == str(act_val).lower():
            matched_fields.append(key)
        else:
            mismatched_fields[key] = {
                "expected": exp_val,
                "actual": act_val
            }
    
    missing_fields = list(expected_keys - actual_keys)
    extra_fields = list(actual_keys - expected_keys)
    
    # 计算匹配率
    total_expected = len(expected_keys)
    if total_expected == 0:
        match_rate = 1.0 if len(extra_fields) == 0 else 0.5
    else:
        match_rate = len(matched_fields) / total_expected
    
    return {
        "match_rate": round(match_rate, 2),
        "matched_fields": matched_fields,
        "missing_fields": missing_fields,
        "extra_fields": extra_fields,
        "mismatched_fields": mismatched_fields
    }

# 测试Ai对指令的解析
def test_single_command(command_text: str, db: Session, ai_config: dict = None, current_user_id: int = None) -> SmartCommandTestResult:
    """
    测试单个智能指令
    
    Args:
        command_text: 要测试的指令文本
        db: 数据库会话
        ai_config: AI配置（如果为None则使用系统默认配置）
        current_user_id: 当前用户ID（可选）
    
    Returns:
        测试结果
    """
    start_time = time.time()
    
    try:
        from utils.smart_command import IntentParser
        
        # 创建解析器
        use_ai = ai_config.get('enabled', False) if ai_config else False
        parser = IntentParser(use_ai=use_ai, ai_config=ai_config)
        
        # 解析指令（传入current_user_id，如果为None则传0或跳过）
        parsed_result = parser.parse(command_text, db, current_user_id or 0)
        
        parse_time_ms = (time.time() - start_time) * 1000
        
        if not parsed_result:
            return SmartCommandTestResult(
                success=False,
                command_text=command_text,
                message="指令解析失败，无法识别意图",
                parse_time_ms=round(parse_time_ms, 2)
            )
        
        # 提取解析结果，兼容不同的返回结构
        # 对于navigate动作，数据在storage_data中
        # 对于其他动作，可能在顶层
        action = parsed_result.get('action', '')
        
        if action == 'navigate' and 'storage_data' in parsed_result:
            # navigate动作：使用storage_data作为parsed_fields
            storage_data = parsed_result['storage_data'].copy()  # 复制一份，避免修改原始数据
            
            # 同时提取一些顶层字段用于显示
            parsed_intent = action
            
            # 如果是排课相关的导航，需要确保包含所有必要字段
            path = parsed_result.get('path', '')
            if '/schedules' in path:
                # 不仅检查字段是否存在，还要检查是否为有效值
                # studentNames
                if not storage_data.get('studentNames'):
                    storage_data['studentNames'] = storage_data.get('person_names') or storage_data.get('student_names') or []
                
                # className
                if not storage_data.get('className'):
                    storage_data['className'] = storage_data.get('class_name') or ''
                
                # courseName
                if not storage_data.get('courseName'):
                    storage_data['courseName'] = storage_data.get('course_name') or ''
                
                # teacherName（可以为null）
                if 'teacherName' not in storage_data:
                    storage_data['teacherName'] = storage_data.get('teacher_name')
                
                # roomName（可以为null）
                if 'roomName' not in storage_data:
                    storage_data['roomName'] = storage_data.get('room_name')
                
                # dayOfWeek
                if 'dayOfWeek' not in storage_data:
                    storage_data['dayOfWeek'] = storage_data.get('day_of_week')
                
                # startTime
                if not storage_data.get('startTime'):
                    storage_data['startTime'] = storage_data.get('start_time') or ''
                
                # endTime
                if not storage_data.get('endTime'):
                    storage_data['endTime'] = storage_data.get('end_time') or ''
                
                # startDate
                if not storage_data.get('startDate'):
                    storage_data['startDate'] = storage_data.get('start_date') or ''
                
                # endDate
                if not storage_data.get('endDate'):
                    storage_data['endDate'] = storage_data.get('end_date') or ''
                
                log_operation(db, "智能指令测试", "解析结果调整", f"针对navigate动作调整解析结果字段，最终storage_data: {storage_data}", "system", "DEBUG")
        else:
            # 其他动作：使用传统的提取方式
            parsed_intent = parsed_result.get('intent', action)
            storage_data = parsed_result.get('storage_data', parsed_result)
        
        return SmartCommandTestResult(
            success=True,
            command_text=command_text,
            parsed_intent=parsed_intent,
            parsed_fields=storage_data,
            message=f"解析成功（耗时: {parse_time_ms:.2f}ms）",
            parse_time_ms=round(parse_time_ms, 2)
        )
        
    except Exception as e:
        parse_time_ms = (time.time() - start_time) * 1000
        import traceback
        traceback.print_exc()
        return SmartCommandTestResult(
            success=False,
            command_text=command_text,
            message=f"解析异常: {str(e)}",
            parse_time_ms=round(parse_time_ms, 2)
        )

# 测试正则表达式对指令的解析
@router.post("/test-regex", response_model=SmartCommandTestResult)
def test_regex_command(
    request: SmartCommandTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试单个指令的正则表达式解析（不使用AI）"""
    # 强制关闭AI，仅使用规则解析
    ai_config = {'enabled': False}
    
    result = test_single_command(request.command_text, db, ai_config, current_user.id)
    
    log_operation(db, "智能指令测试", "正则测试", f"正则测试指令: {request.command_text[:50]}...", current_user.username, "INFO")
    
    return result

# ==================== CRUD 接口 ====================

@router.get("/list")
def get_examples(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: Optional[str] = Query(None, description="排序字段：category, action_name, expected_intent, is_active, sort_order"),
    sort_order: Optional[str] = Query("asc", description="排序顺序：asc 或 desc"),
    search: Optional[str] = Query(None, description="模糊搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """获取智能指令示例列表（支持分页、筛选、排序和搜索）"""
    query = db.query(SmartCommandExample)
    
    if category:
        query = query.filter(SmartCommandExample.category == category)
    
    if is_active is not None:
        query = query.filter(SmartCommandExample.is_active == is_active)
    
    # 处理模糊搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (SmartCommandExample.category.ilike(search_pattern)) |
            (SmartCommandExample.action_name.ilike(search_pattern)) |
            (SmartCommandExample.example_text.ilike(search_pattern)) |
            (SmartCommandExample.expected_intent.ilike(search_pattern)) |
            (SmartCommandExample.description.ilike(search_pattern))
        )
    
    # 获取总数
    total = query.count()
    
    # 处理排序
    valid_sort_fields = {
        'category': SmartCommandExample.category,
        'action_name': SmartCommandExample.action_name,
        'expected_intent': SmartCommandExample.expected_intent,
        'is_active': SmartCommandExample.is_active,
        'sort_order': SmartCommandExample.sort_order
    }
    
    if sort_by and sort_by in valid_sort_fields:
        sort_column = valid_sort_fields[sort_by]
        if sort_order and sort_order.lower() == 'desc':
            query = query.order_by(sort_column.desc(), SmartCommandExample.id)
        else:
            query = query.order_by(sort_column.asc(), SmartCommandExample.id)
    else:
        # 默认排序：按优先级升序，然后按ID
        query = query.order_by(SmartCommandExample.sort_order.asc(), SmartCommandExample.id)
    
    examples = query.offset(skip).limit(limit).all()
    
    # 转换 expected_fields（JSONB类型从数据库读取时已经是dict）
    result = []
    for ex in examples:
        ex_dict = SmartCommandExampleResponse.from_orm(ex).dict()
        # 检查是否为字符串类型（兼容TEXT和JSONB）
        if isinstance(ex.expected_fields, str):
            try:
                ex_dict['expected_fields'] = json.loads(ex.expected_fields) if ex.expected_fields else {}
            except:
                ex_dict['expected_fields'] = {}
        else:
            # JSONB类型已经是dict，直接使用
            ex_dict['expected_fields'] = ex.expected_fields if ex.expected_fields else {}
        result.append(ex_dict)
    
    return {
        "items": result,
        "total": total
    }

@router.post("/create", response_model=SmartCommandExampleResponse)
def create_example(
    example: SmartCommandExampleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """创建新的智能指令示例"""
    _require_smart_command_license(db)
    # JSONB类型可以直接存储字典，无需转换为JSON字符串
    expected_fields_value = example.expected_fields
    
    db_example = SmartCommandExample(
        category=example.category,
        action_name=example.action_name,
        example_text=example.example_text,
        expected_intent=example.expected_intent,
        expected_fields=expected_fields_value,
        description=example.description,
        is_active=example.is_active,
        sort_order=example.sort_order
    )
    
    db.add(db_example)
    db.commit()
    db.refresh(db_example)
    
    log_operation(db, "智能指令示例", "创建", f"创建示例: {example.action_name}", current_user.username, "INFO")
    
    # 返回时直接使用expected_fields（JSONB类型已经是dict）
    result = SmartCommandExampleResponse.from_orm(db_example).dict()
    result['expected_fields'] = db_example.expected_fields if db_example.expected_fields else {}
    
    return result

@router.put("/update/{example_id}", response_model=SmartCommandExampleResponse)
def update_example(
    example_id: int,
    example_update: SmartCommandExampleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """更新智能指令示例"""
    _require_smart_command_license(db)
    db_example = db.query(SmartCommandExample).filter(SmartCommandExample.id == example_id).first()
    
    if not db_example:
        raise HTTPException(status_code=404, detail="示例不存在")
    
    update_data = example_update.dict(exclude_unset=True)
    
    # JSONB类型直接更新，无需JSON转换
    
    for field, value in update_data.items():
        setattr(db_example, field, value)
    
    db_example.updated_at = datetime.now()
    db.commit()
    db.refresh(db_example)
    
    log_operation(db, "智能指令示例", "更新", f"更新示例ID: {example_id}", current_user.username, "INFO")
    
    # 返回时直接使用expected_fields（JSONB类型已经是dict）
    result = SmartCommandExampleResponse.from_orm(db_example).dict()
    result['expected_fields'] = db_example.expected_fields if db_example.expected_fields else {}
    
    return result

@router.delete("/delete/{example_id}")
def delete_example(
    example_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """删除智能指令示例"""
    _require_smart_command_license(db)
    db_example = db.query(SmartCommandExample).filter(SmartCommandExample.id == example_id).first()
    
    if not db_example:
        raise HTTPException(status_code=404, detail="示例不存在")
    
    db.delete(db_example)
    db.commit()
    
    log_operation(db, "智能指令示例", "删除", f"删除示例ID: {example_id}", current_user.username, "INFO")
    
    return {"message": "删除成功"}


# ==================== 测试接口 ====================

@router.post("/test-one", response_model=SmartCommandTestResult)
def test_one_command(
    request: SmartCommandTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试单个自定义指令"""
    # 获取AI配置
    from models import Settings
    settings = db.query(Settings).first()
    ai_config = {}
    if settings and settings.ai_config:
        try:
            ai_config = json.loads(settings.ai_config)
        except:
            ai_config = {}
    
    # 如果请求中指定了use_ai，则覆盖配置
    if request.use_ai is not None:
        ai_config['enabled'] = request.use_ai
    
    result = test_single_command(request.command_text, db, ai_config, current_user.id)
    
    log_operation(db, "智能指令测试", "单条测试", f"测试指令: {request.command_text[:50]}...", current_user.username, "INFO")
    
    return result


@router.post("/test-all", response_model=SmartCommandBatchTestResult)
def test_all_examples(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """测试所有激活的智能指令示例"""
    start_time = time.time()
    
    # 获取所有激活的示例
    examples = db.query(SmartCommandExample)\
                 .filter(SmartCommandExample.is_active == True)\
                 .order_by(SmartCommandExample.sort_order, SmartCommandExample.id)\
                 .all()
    
    if not examples:
        return SmartCommandBatchTestResult(
            total=0,
            success_count=0,
            failed_count=0,
            results=[],
            test_duration_ms=0.0
        )
    
    # 获取AI配置
    from models import Settings
    settings = db.query(Settings).first()
    ai_config = {}
    if settings and settings.ai_config:
        try:
            ai_config = json.loads(settings.ai_config)
        except:
            ai_config = {}
    
    # 逐个测试
    results = []
    success_count = 0
    failed_count = 0
    
    for example in examples:
        # 解析预期字段（JSONB类型从数据库读取时已经是dict）
        if isinstance(example.expected_fields, str):
            try:
                expected_fields = json.loads(example.expected_fields) if example.expected_fields else {}
            except:
                expected_fields = {}
        else:
            # JSONB类型已经是dict，直接使用
            expected_fields = example.expected_fields if example.expected_fields else {}
        
        # 执行测试（传入current_user.id）
        test_result = test_single_command(example.example_text, db, ai_config, current_user.id)
        
        # 对比预期结果
        if test_result.success and example.expected_intent:
            intent_match = test_result.parsed_intent == example.expected_intent
            
            # 字段对比
            field_comparison = compare_fields(expected_fields, test_result.parsed_fields or {})
            
            # 判断整体是否成功
            overall_success = intent_match and field_comparison['match_rate'] >= 0.8
            
            if overall_success:
                success_count += 1
            else:
                failed_count += 1
            
            # 构建详细结果
            detailed_result = SmartCommandTestResult(
                success=overall_success,
                command_text=example.example_text,
                parsed_intent=test_result.parsed_intent,
                expected_intent=example.expected_intent,
                intent_match=intent_match,
                parsed_fields=test_result.parsed_fields,
                expected_fields=expected_fields,
                field_comparison=field_comparison,
                message="通过" if overall_success else "失败",
                parse_time_ms=test_result.parse_time_ms
            )
        else:
            failed_count += 1
            detailed_result = test_result
        
        results.append(detailed_result)
    
    test_duration_ms = (time.time() - start_time) * 1000
    
    log_operation(db, "智能指令测试", "批量测试", f"测试{len(examples)}条示例，成功{success_count}条，失败{failed_count}条", current_user.username, "INFO")
    
    return SmartCommandBatchTestResult(
        total=len(examples),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
        test_duration_ms=round(test_duration_ms, 2)
    )

@router.post("/auto-generate")
def auto_generate_expected_fields(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """
    根据示例文本和预期意图自动生成预期字段
    
    Args:
        request: 包含 example_text 和 expected_intent 的字典
    
    Returns:
        自动生成的预期字段
    """
    try:
        example_text = request.get('example_text', '')
        expected_intent = request.get('expected_intent', '')
        
        if not example_text or not expected_intent:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 根据意图类型生成预期的字段结构
        generated_fields = generate_expected_fields_by_intent(example_text, expected_intent)
        
        log_operation(db, "智能指令示例", "自动生成", f"为意图 {expected_intent} 生成预期字段", current_user.username, "INFO")
        
        return {
            "success": True,
            "expected_fields": generated_fields,
            "message": "自动生成成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


def generate_expected_fields_by_intent(example_text: str, intent: str) -> dict:
    """
    根据意图类型生成预期字段结构
    
    Args:
        example_text: 示例文本
        intent: 意图类型
    
    Returns:
        预期字段字典
    """
    import re
    import copy
    
    # 基础导航结构
    base_navigate = {
        "action": "navigate",
        "path": "",
        "query": {},
        "storage_data": {}
    }
    
    # 基础确认结构
    base_confirm = {
        "action": "confirm",
        "operation": "",
        "storage_data": {}
    }
    
    # 根据意图生成不同的结构
    if intent in ['search_students', 'search_teachers', 'search_courses', 
                  'search_rooms', 'search_classes', 'search_schedules',
                  'search_fees', 'search_grades']:
        # 查询类指令
        entity_map = {
            'search_students': ('students', '/admin/students'),
            'search_teachers': ('teachers', '/admin/teachers'),
            'search_courses': ('courses', '/admin/courses'),
            'search_rooms': ('rooms', '/admin/rooms'),
            'search_classes': ('classes', '/admin/classes'),
            'search_schedules': ('schedules', '/admin/schedules'),
            'search_fees': ('fees', '/admin/fees'),
            'search_grades': ('grades', '/admin/grades')
        }
        
        entity_type, path = entity_map.get(intent, ('students', '/admin/students'))
        
        result = copy.deepcopy(base_navigate)
        result['path'] = path
        result['storage_data'] = {
            "search_mode": True,
            "entity_type": entity_type
        }
        return result
    
    elif intent == 'advanced_search':
        # 高级搜索 - 尝试从文本中提取信息
        result = copy.deepcopy(base_navigate)
        result['path'] = '/admin/students'  # 默认路径
        
        # 尝试提取实体名称和类型
        storage_data = {}
        
        # 检查是否是关联查询（X的Y）
        relation_match = re.search(r'(学员|学生|导师|老师|班级|科目|课程)\s*(\S+?)\s*的\s*(班级|科目|课程|导师|老师|学员|学生|排课|课费|成绩)', example_text)
        if relation_match:
            source_type_map = {
                '学员': 'student', '学生': 'student',
                '导师': 'teacher', '老师': 'teacher',
                '班级': 'class',
                '科目': 'course', '课程': 'course'
            }
            target_type_map = {
                '班级': 'classes',
                '科目': 'courses', '课程': 'courses',
                '导师': 'teachers', '老师': 'teachers',
                '学员': 'students', '学生': 'students',
                '排课': 'schedules',
                '课费': 'fees',
                '成绩': 'grades'
            }
            
            source_type = source_type_map.get(relation_match.group(1), 'student')
            source_name = relation_match.group(2)
            target_type = target_type_map.get(relation_match.group(3), 'classes')
            
            path_map = {
                'student': '/admin/students',
                'teacher': '/admin/teachers',
                'class': '/admin/classes',
                'course': '/admin/courses'
            }
            
            result['path'] = path_map.get(source_type, '/admin/students')
            result['query'] = {
                "search": source_name,
                "related_to": target_type
            }
            result['storage_data'] = {
                "search_mode": True,
                "source_entity": source_type,
                "source_name": source_name,
                "target_entity": target_type
            }
            return result
        
        # 检查是否带时间条件
        time_match = re.search(r'(学员|学生|导师|老师|班级)?\s*(\S+?)\s*在\s*(今天|明天|后天|\d{4}-\d{2}-\d{2})', example_text)
        if time_match:
            entity_type = 'student'
            if '导师' in example_text or '老师' in example_text:
                entity_type = 'teacher'
            elif '班级' in example_text:
                entity_type = 'class'
            
            entity_name = time_match.group(2)
            date_str = time_match.group(3)
            
            result['path'] = '/admin/schedules'
            result['query'] = {
                "filter_by": entity_type,
                "filter_value": entity_name,
                "date": date_str
            }
            result['storage_data'] = {
                "search_mode": True,
                "entity_type": entity_type,
                "entity_name": entity_name,
                "date_filter": date_str,
                "target_entity": "schedules"
            }
            return result
        
        # 默认高级搜索结构
        result['storage_data'] = {
            "search_mode": True,
            "entity_type": "student"
        }
        return result
    
    elif intent in ['add_course', 'add_teacher', 'add_student', 'add_class', 'add_room']:
        # 添加类指令
        entity_map = {
            'add_course': ('courses', '/admin/courses'),
            'add_teacher': ('teachers', '/admin/teachers'),
            'add_student': ('students', '/admin/students'),
            'add_class': ('classes', '/admin/classes'),
            'add_room': ('rooms', '/admin/rooms')
        }
        
        entity_type, path = entity_map.get(intent, ('courses', '/admin/courses'))
        
        result = copy.deepcopy(base_navigate)
        result['path'] = path
        result['storage_data'] = {
            "form_data": {},
            "mode": "create"
        }
        
        # 尝试从文本中提取字段
        form_data = {}
        
        # 提取名称
        name_match = re.search(r'(?:科目|课程|导师|老师|学员|学生|班级|教室)\s*(\S+?)(?:，|,|$)', example_text)
        if name_match:
            form_data['name'] = name_match.group(1)
        
        # 提取电话/手机
        phone_match = re.search(r'(?:电话|手机|联系方式)[:：]?\s*(\d{11})', example_text)
        if phone_match:
            form_data['phone'] = phone_match.group(1)
        
        # 提取优先级
        priority_match = re.search(r'优先级[:：]?\s*(\d+)', example_text)
        if priority_match:
            form_data['priority'] = int(priority_match.group(1))
        
        # 提取容量
        capacity_match = re.search(r'容量[:：]?\s*(\d+)', example_text)
        if capacity_match:
            form_data['capacity'] = int(capacity_match.group(1))
        
        result['storage_data']['form_data'] = form_data
        return result
    
    elif intent in ['update_course', 'update_teacher', 'update_student', 'update_class', 'update_room']:
        # 更新类指令
        entity_map = {
            'update_course': ('courses', '/admin/courses'),
            'update_teacher': ('teachers', '/admin/teachers'),
            'update_student': ('students', '/admin/students'),
            'update_class': ('classes', '/admin/classes'),
            'update_room': ('rooms', '/admin/rooms')
        }
        
        entity_type, path = entity_map.get(intent, ('courses', '/admin/courses'))
        
        # 提取搜索关键词
        keyword = ''
        keyword_match = re.search(r'(?:科目|课程|导师|老师|学员|学生|班级|教室)\s*(\S+?)(?:的|,|，|$)', example_text)
        if keyword_match:
            keyword = keyword_match.group(1)
        
        result = copy.deepcopy(base_navigate)
        result['path'] = path
        result['query'] = {
            "search": keyword
        }
        result['storage_data'] = {
            "form_data": {},
            "mode": "update",
            "search_keyword": keyword
        }
        return result
    
    elif intent == 'create_schedule':
        # 创建排课
        result = copy.deepcopy(base_navigate)
        result['path'] = '/admin/schedules'
        
        storage_data = {
            "mode": "create"
        }
        
        # 提取学员姓名
        student_match = re.search(r'(?:为|给)\s*(\S+?)\s*(?:安排|创建|添加)', example_text)
        if not student_match:
            student_match = re.search(r'(?:安排|创建|添加)\s*(\S+?)\s*(?:的|在)', example_text)
        if student_match:
            storage_data['student_name'] = student_match.group(1)
        
        # 提取日期
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|今天|明天|后天|\d+月\d+号|\d+月\d+日)', example_text)
        if date_match:
            storage_data['date'] = date_match.group(1)
        
        # 提取时间
        time_match = re.search(r'(\d{1,2}:\d{2})\s*到\s*(\d{1,2}:\d{2})', example_text)
        if time_match:
            storage_data['start_time'] = time_match.group(1)
            storage_data['end_time'] = time_match.group(2)
        
        # 提取课程名称
        course_match = re.search(r'的\s*(.+?)(?:课|课程)', example_text)
        if course_match:
            storage_data['course_name'] = course_match.group(1)
        
        result['storage_data'] = storage_data
        return result
    
    elif intent in ['complete_schedule', 'cancel_schedule', 'postpone_schedule']:
        # 确认类操作
        operation_map = {
            'complete_schedule': 'complete_schedule',
            'cancel_schedule': 'cancel_schedule',
            'postpone_schedule': 'postpone_schedule'
        }
        
        result = copy.deepcopy(base_confirm)
        result['operation'] = operation_map.get(intent, intent)
        
        storage_data = {}
        
        # 提取学员姓名
        student_match = re.search(r'(?:完成|取消|推迟|延期)\s*(\S+?)(?:的|今天|明天)', example_text)
        if student_match:
            storage_data['student_name'] = student_match.group(1)
        
        # 提取日期
        date_match = re.search(r'(今天|明天|后天|\d{4}-\d{2}-\d{2})', example_text)
        if date_match:
            if intent == 'postpone_schedule':
                storage_data['original_date'] = date_match.group(1)
                # 尝试提取新日期
                new_date_match = re.search(r'(?:到|至|改为)\s*(今天|明天|后天|\d{4}-\d{2}-\d{2})', example_text)
                if new_date_match:
                    storage_data['new_date'] = new_date_match.group(1)
            else:
                storage_data['date'] = date_match.group(1)
        
        # 提取课程名称
        course_match = re.search(r'(?:的|的)(.+?)(?:课|课程)', example_text)
        if course_match:
            storage_data['course_name'] = course_match.group(1)
        
        result['storage_data'] = storage_data
        return result
    
    elif intent == 'add_leave':
        # 添加请假
        result = copy.deepcopy(base_navigate)
        result['path'] = '/admin/leaves'
        
        storage_data = {
            "form_data": {},
            "mode": "create"
        }
        
        # 提取学员姓名
        student_match = re.search(r'(\S+?)\s*(?:从|于)', example_text)
        if student_match:
            storage_data['form_data']['student_name'] = student_match.group(1)
        
        # 提取日期范围
        date_range_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d+月\d+号?)\s*(?:到|至)\s*(\d{4}-\d{2}-\d{2}|\d+月\d+号?)', example_text)
        if date_range_match:
            storage_data['form_data']['start_date'] = date_range_match.group(1)
            storage_data['form_data']['end_date'] = date_range_match.group(2)
        
        # 提取原因
        reason_match = re.search(r'(?:原因|事由)[:：]?\s*(.+?)(?:。|$)', example_text)
        if reason_match:
            storage_data['form_data']['reason'] = reason_match.group(1)
        
        result['storage_data'] = storage_data
        return result
    
    elif intent == 'add_holiday':
        # 添加假期
        result = copy.deepcopy(base_navigate)
        result['path'] = '/admin/holidays'
        
        storage_data = {
            "form_data": {},
            "mode": "create"
        }
        
        # 提取假期名称
        name_match = re.search(r'(?:假期|假日)\s*(\S+?)(?:，|,|从)', example_text)
        if name_match:
            storage_data['form_data']['name'] = name_match.group(1)
        
        # 提取日期范围
        date_range_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d+月\d+号?)\s*(?:到|至)\s*(\d{4}-\d{2}-\d{2}|\d+月\d+号?)', example_text)
        if date_range_match:
            storage_data['form_data']['start_date'] = date_range_match.group(1)
            storage_data['form_data']['end_date'] = date_range_match.group(2)
        
        result['storage_data'] = storage_data
        return result
    
    elif intent in ['collect_fee', 'refund_fee']:
        # 课费操作
        result = copy.deepcopy(base_navigate)
        result['path'] = '/admin/fees'
        
        storage_data = {
            "form_data": {
                "type": "collect" if intent == 'collect_fee' else "refund"
            },
            "mode": "create"
        }
        
        # 提取学员姓名
        student_match = re.search(r'(?:收取|退还)\s*(\S+?)(?:学费|课费|费用)', example_text)
        if student_match:
            storage_data['form_data']['student_name'] = student_match.group(1)
        
        # 提取金额
        amount_match = re.search(r'(\d+)\s*元', example_text)
        if amount_match:
            storage_data['form_data']['amount'] = int(amount_match.group(1))
        
        result['storage_data'] = storage_data
        return result
    
    elif intent == 'add_grade':
        # 添加成绩
        result = copy.deepcopy(base_navigate)
        result['path'] = '/admin/grades'
        
        storage_data = {
            "form_data": {},
            "mode": "create"
        }
        
        # 提取学员姓名
        student_match = re.search(r'(\S+?)\s*(?:的| )(?:数学|语文|英语|物理|化学|生物|历史|地理|政治)', example_text)
        if student_match:
            storage_data['form_data']['student_name'] = student_match.group(1)
        
        # 提取科目
        course_match = re.search(r'(数学|语文|英语|物理|化学|生物|历史|地理|政治)', example_text)
        if course_match:
            storage_data['form_data']['course_name'] = course_match.group(1)
        
        # 提取分数
        score_match = re.search(r'(\d+)\s*(?:分|分数|成绩)', example_text)
        if score_match:
            storage_data['form_data']['score'] = int(score_match.group(1))
        
        # 提取考试类型
        exam_match = re.search(r'(期中|期末|月考|模拟|测验)', example_text)
        if exam_match:
            storage_data['form_data']['exam_type'] = exam_match.group(1) + "考试"
        
        result['storage_data'] = storage_data
        return result
    
    else:
        # 未知意图，返回空结构
        return {
            "action": "navigate",
            "path": "/admin/students",
            "query": {},
            "storage_data": {}
        }