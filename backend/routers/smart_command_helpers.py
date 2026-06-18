# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
智能指令预览数据生成辅助函数
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models import Course, Teacher, Student, Class as ClassModel, Room, Schedule, StudentFee, Holiday, StudentGrade
from datetime import datetime

def generate_preview_data(parsed_result: dict, db: Session) -> dict:
    """
    根据解析结果生成预览数据
    
    Args:
        parsed_result: 解析后的意图数据
        db: 数据库会话
        
    Returns:
        预览数据字典
    """
    action = parsed_result.get('action', '')
    
    # 如果是导航操作，尝试从 query 中获取原始意图用于展示
    display_action = action
    if action == 'navigate' and parsed_result.get('query'):
        display_action = parsed_result['query'].get('action', action)
    
    # 预处理参数：如果存在 storage_data，将其合并到顶层以便预览函数读取
    processed_params = parsed_result.copy()
    if 'storage_data' in parsed_result:
        for key, value in parsed_result['storage_data'].items():
            # 对于 navigate 动作，直接使用 storage_data 的值（即使顶层已有空值）
            if action == 'navigate':
                processed_params[key] = value
            elif key not in processed_params:
                processed_params[key] = value
    
    # 添加字段名转换：将驼峰命名转换为下划线命名
    # 这样无论AI返回的是哪种命名方式，都能正确读取
    converted_params = {}
    for key, value in processed_params.items():
        # 将驼峰命名转换为下划线命名
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        converted_params[snake_key] = value
        
        # 同时保留原始键名，以防万一
        if key != snake_key:
            converted_params[key] = value
    
    # 添加字段别名映射，确保预览函数能正确读取字段
    # studentNames -> person_names (用于排课)
    if 'student_names' in converted_params and 'person_names' not in converted_params:
        converted_params['person_names'] = converted_params['student_names']
    
    # className -> class_name
    if 'class_name' not in converted_params and 'className' in converted_params:
        converted_params['class_name'] = converted_params['className']
    
    # courseName -> course_name
    if 'course_name' not in converted_params and 'courseName' in converted_params:
        converted_params['course_name'] = converted_params['courseName']
    
    # teacherName -> teacher_name
    if 'teacher_name' not in converted_params and 'teacherName' in converted_params:
        converted_params['teacher_name'] = converted_params['teacherName']
    
    # roomName -> room_name
    if 'room_name' not in converted_params and 'roomName' in converted_params:
        converted_params['room_name'] = converted_params['roomName']
    
    preview = {
        'action': action,
        'action_name': get_action_name(display_action),
        'fields': [],
        'warnings': [],
        'errors': [],
        'suggestions': [],
        'need_confirmation': True,
        'missing_fields': parsed_result.get('missing_fields', [])
    }
    
    # 使用转换后的参数
    if action == 'add_course':
        _preview_add_course(converted_params,db, preview)
    
    elif action == 'update_course':
        _preview_update_course(converted_params,db, preview)
    
    elif action == 'complete_schedule':
        _preview_complete_schedule(converted_params,db, preview)
    
    elif action == 'cancel_schedule':
        _preview_cancel_schedule(converted_params,db, preview)
    
    elif action == 'postpone_schedule':
        _preview_postpone_schedule(converted_params,db, preview)
    
    elif action == 'add_teacher':
        _preview_add_teacher(converted_params,db, preview)
    
    elif action == 'update_teacher':
        _preview_update_teacher(converted_params,db, preview)
    
    elif action == 'add_student':
        _preview_add_student(converted_params,db, preview)
    
    elif action == 'update_student':
        _preview_update_student(converted_params,db, preview)
    
    elif action == 'add_class':
        _preview_add_class(converted_params,db, preview)
    
    elif action == 'update_class':
        _preview_update_class(converted_params,db, preview)
    
    elif action == 'add_room':
        _preview_add_room(converted_params,db, preview)
    
    elif action == 'update_room':
        _preview_update_room(converted_params,db, preview)
    
    elif action == 'add_leave':
        _preview_add_leave(converted_params,db, preview)
    
    elif action == 'add_holiday':
        _preview_add_holiday(converted_params,db, preview)
    
    elif action == 'collect_fee':
        _preview_collect_fee(converted_params,db, preview)
    
    elif action == 'refund_fee':
        _preview_refund_fee(converted_params,db, preview)
    
    elif action == 'add_grade':
        _preview_add_grade(converted_params,db, preview)
    
    elif action == 'create_schedule':
        _preview_create_schedule(converted_params,db, preview)
    
    elif action == 'navigate':
        # 处理导航类型的动作，根据 query.action 调用相应的预览函数
        nav_action = parsed_result.get('query', {}).get('action', '')
        if nav_action == 'add':
            # 根据路径判断是添加什么
            path = parsed_result.get('path', '')
            if '/schedules' in path:
                _preview_create_schedule(converted_params, db, preview)
            elif '/teachers' in path:
                _preview_add_teacher(converted_params, db, preview)
            elif '/students' in path:
                _preview_add_student(converted_params, db, preview)
            elif '/classes' in path:
                _preview_add_class(converted_params, db, preview)
            elif '/rooms' in path:
                _preview_add_room(converted_params, db, preview)
            elif '/courses' in path:
                _preview_add_course(converted_params, db, preview)
        elif nav_action == 'edit' or nav_action == 'update':
            # 根据路径判断是更新什么
            path = parsed_result.get('path', '')
            if '/schedules' in path:
                # 编辑排课可以复用创建排课的预览逻辑
                _preview_create_schedule(converted_params, db, preview)
            elif '/teachers' in path:
                _preview_update_teacher(converted_params, db, preview)
            elif '/students' in path:
                _preview_update_student(converted_params, db, preview)
            elif '/classes' in path:
                _preview_update_class(converted_params, db, preview)
            elif '/rooms' in path:
                _preview_update_room(converted_params, db, preview)
            elif '/courses' in path:
                _preview_update_course(converted_params, db, preview)
        elif nav_action == 'complete':
            _preview_complete_schedule(converted_params, db, preview)
        elif nav_action == 'cancel':
            _preview_cancel_schedule(converted_params, db, preview)
        elif nav_action == 'postpone':
            _preview_postpone_schedule(converted_params, db, preview)
    
    return preview

def _preview_add_course(params: dict, db: Session, preview: dict):
    """预览添加科目"""
    course_name = params.get('course_name', '')
    teacher_name = params.get('teacher_name')
    priority = params.get('priority', 0)
    
    # 检查科目是否已存在
    existing_course = db.query(Course).filter(Course.name == course_name).first()
    
    preview['fields'] = [
        {'label': '科目名称', 'value': course_name, 'type': 'text'},
        {'label': '优先级', 'value': str(priority), 'type': 'number'},
    ]
    
    if existing_course:
        preview['errors'].append(f'科目"{course_name}"已存在（ID: {existing_course.id}）')
        preview['need_confirmation'] = False
    
    if teacher_name:
        teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
        if teacher:
            preview['fields'].append({
                'label': '关联导师',
                'value': f'{teacher.name} (ID: {teacher.id})',
                'type': 'text'
            })
        else:
            # 查找相似导师
            similar_teachers = _find_similar_items(db, Teacher, 'name', teacher_name)
            if similar_teachers:
                preview['warnings'].append(f'未找到导师"{teacher_name}"，建议从以下相似导师中选择：')
                preview['suggestions'] = [{'type': 'teacher', 'items': similar_teachers}]
            else:
                preview['warnings'].append(f'导师"{teacher_name}"不存在，将先创建该导师')
                preview['fields'].append({
                    'label': '新导师姓名',
                    'value': teacher_name,
                    'type': 'text',
                    'warning': '将自动创建'
                })
    
    # 生成预览编码
    code = _generate_code_preview(db, Course, "COURSE")
    preview['fields'].append({'label': '自动生成代码', 'value': code, 'type': 'code'})


def _preview_update_course(params: dict, db: Session, preview: dict):
    """预览更新科目"""
    course_identifier = params.get('course_identifier')
    updates = params.get('updates', {})
    
    # 查找科目
    course = None
    if course_identifier.isdigit():
        course = db.query(Course).filter(Course.id == int(course_identifier)).first()
    else:
        course = db.query(Course).filter(Course.name == course_identifier).first()
    
    if not course:
        similar_courses = _find_similar_items(db, Course, 'name', course_identifier)
        if similar_courses:
            preview['warnings'].append(f'未找到科目"{course_identifier}"，建议从以下相似科目中选择：')
            preview['suggestions'] = [{'type': 'course', 'items': similar_courses}]
        else:
            preview['errors'].append(f'科目"{course_identifier}"不存在')
        return
    
    preview['fields'] = [
        {'label': '科目标识', 'value': f'{course.name} (ID: {course.id})', 'type': 'text'},
        {'label': '当前名称', 'value': course.name, 'type': 'text'},
    ]
    
    if 'name' in updates:
        preview['fields'].append({'label': '新名称', 'value': updates['name'], 'type': 'text', 'changed': True})
    if 'priority' in updates:
        preview['fields'].append({
            'label': '新优先级', 
            'value': str(updates['priority']), 
            'type': 'number',
            'changed': True,
            'old_value': str(course.priority)
        })
    if 'teacher_name' in updates:
        teacher = db.query(Teacher).filter(Teacher.name == updates['teacher_name']).first()
        if teacher:
            preview['fields'].append({
                'label': '新关联导师',
                'value': f'{teacher.name} (ID: {teacher.id})',
                'type': 'text',
                'changed': True
            })
        else:
            preview['errors'].append(f'导师"{updates["teacher_name"]}"不存在')


def _preview_complete_schedule(params: dict, db: Session, preview: dict):
    """预览完成课程"""
    schedule_id = params.get('schedule_id')
    content_feedback = params.get('content_feedback')
    
    try:
        schedule_id_int = int(schedule_id)
    except ValueError:
        preview['errors'].append('排课ID必须是数字')
        return
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id_int).first()
    
    if not schedule:
        preview['errors'].append(f'未找到排课记录 ID: {schedule_id}')
        return
    
    # 获取相关信息
    course = db.query(Course).filter(Course.id == schedule.course_id).first()
    teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
    class_obj = db.query(ClassModel).filter(ClassModel.id == schedule.class_id).first()
    room = db.query(Room).filter(Room.id == schedule.room_id).first()
    
    weekday_names = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_name = weekday_names[schedule.day_of_week] if schedule.day_of_week <= 7 else ''
    
    preview['fields'] = [
        {'label': '排课ID', 'value': str(schedule.id), 'type': 'id'},
        {'label': '科目', 'value': course.name if course else '未知', 'type': 'text'},
        {'label': '导师', 'value': teacher.name if teacher else '未知', 'type': 'text'},
        {'label': '班级', 'value': class_obj.name if class_obj else '未知', 'type': 'text'},
        {'label': '教室', 'value': room.name if room else '未知', 'type': 'text'},
        {'label': '时间', 'value': f'{weekday_name} {schedule.start_time}-{schedule.end_time}', 'type': 'text'},
        {'label': '日期范围', 'value': f'{schedule.start_date} 至 {schedule.end_date}', 'type': 'text'},
    ]
    
    if content_feedback:
        # 解析反馈格式
        feedback_parts = content_feedback.split('|')
        if len(feedback_parts) >= 1:
            preview['fields'].append({'label': '课程内容', 'value': feedback_parts[0], 'type': 'textarea'})
        if len(feedback_parts) >= 2:
            preview['fields'].append({'label': '作业', 'value': feedback_parts[1], 'type': 'textarea'})
        if len(feedback_parts) >= 3:
            preview['fields'].append({'label': '注意事项', 'value': feedback_parts[2], 'type': 'textarea'})
    else:
        preview['warnings'].append('请提供课程内容反馈（格式：内容|作业|注意）')
        preview['missing_fields'].append('content_feedback')
    
    # 检查是否有冲突
    if schedule.has_conflict:
        preview['warnings'].append(f'该排课存在冲突：{schedule.conflict_reason}')


def _preview_cancel_schedule(params: dict, db: Session, preview: dict):
    """预览取消课程"""
    schedule_id = params.get('schedule_id')
    cancel_reason = params.get('cancel_reason')
    
    try:
        schedule_id_int = int(schedule_id)
    except ValueError:
        preview['errors'].append('排课ID必须是数字')
        return
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id_int).first()
    
    if not schedule:
        preview['errors'].append(f'未找到排课记录 ID: {schedule_id}')
        return
    
    course = db.query(Course).filter(Course.id == schedule.course_id).first()
    teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
    class_obj = db.query(ClassModel).filter(ClassModel.id == schedule.class_id).first()
    
    preview['fields'] = [
        {'label': '排课ID', 'value': str(schedule.id), 'type': 'id'},
        {'label': '科目', 'value': course.name if course else '未知', 'type': 'text'},
        {'label': '导师', 'value': teacher.name if teacher else '未知', 'type': 'text'},
        {'label': '班级', 'value': class_obj.name if class_obj else '未知', 'type': 'text'},
        {'label': '取消原因', 'value': cancel_reason or '未提供', 'type': 'textarea'},
    ]
    
    if not cancel_reason:
        preview['warnings'].append('请提供取消原因')
        preview['missing_fields'].append('cancel_reason')


def _preview_postpone_schedule(params: dict, db: Session, preview: dict):
    """预览延期课程"""
    schedule_id = params.get('schedule_id')
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    start_time = params.get('start_time')
    end_time = params.get('end_time')
    postpone_reason = params.get('postpone_reason')
    
    try:
        schedule_id_int = int(schedule_id)
    except ValueError:
        preview['errors'].append('排课ID必须是数字')
        return
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id_int).first()
    
    if not schedule:
        preview['errors'].append(f'未找到排课记录 ID: {schedule_id}')
        return
    
    course = db.query(Course).filter(Course.id == schedule.course_id).first()
    teacher = db.query(Teacher).filter(Teacher.id == schedule.teacher_id).first()
    class_obj = db.query(ClassModel).filter(ClassModel.id == schedule.class_id).first()
    
    preview['fields'] = [
        {'label': '原排课ID', 'value': str(schedule.id), 'type': 'id'},
        {'label': '科目', 'value': course.name if course else '未知', 'type': 'text'},
        {'label': '导师', 'value': teacher.name if teacher else '未知', 'type': 'text'},
        {'label': '班级', 'value': class_obj.name if class_obj else '未知', 'type': 'text'},
        {'label': '新开始日期', 'value': start_date or '未提供', 'type': 'date'},
        {'label': '新结束日期', 'value': end_date or '未提供', 'type': 'date'},
        {'label': '新时间', 'value': f'{start_time or "??"}-{end_time or "??"}', 'type': 'time'},
        {'label': '延期原因', 'value': postpone_reason or '未提供', 'type': 'textarea'},
    ]
    
    missing = []
    if not start_date: missing.append('开始日期')
    if not end_date: missing.append('结束日期')
    if not start_time: missing.append('开始时间')
    if not end_time: missing.append('结束时间')
    if not postpone_reason: missing.append('延期原因')
    
    if missing:
        preview['warnings'].append(f'缺少信息：{", ".join(missing)}')
        preview['missing_fields'].extend([f for f in ['start_date', 'end_date', 'start_time', 'end_time', 'postpone_reason'] 
                                         if not params.get(f)])


def _preview_add_teacher(params: dict, db: Session, preview: dict):
    """预览添加导师"""
    # 兼容两种字段命名方式
    name = params.get('name') or params.get('teacher_name', '')
    phone = params.get('phone') or params.get('contact_phone')
    email = params.get('email')
    title = params.get('title')
    department = params.get('department')
    
    if not name:
        preview['errors'].append('缺少导师姓名')
        return
    
    existing_teacher = db.query(Teacher).filter(Teacher.name == name).first()
    
    preview['fields'] = [
        {'label': '导师姓名', 'value': name, 'type': 'text'},
    ]
    
    if existing_teacher:
        preview['warnings'].append(f'导师"{name}"已存在（ID: {existing_teacher.id}），将创建重复记录')
    
    if phone:
        preview['fields'].append({'label': '联系电话', 'value': phone, 'type': 'phone'})
    if email:
        preview['fields'].append({'label': '电子邮箱', 'value': email, 'type': 'email'})
    if title:
        preview['fields'].append({'label': '职称', 'value': title, 'type': 'text'})
    if department:
        preview['fields'].append({'label': '部门', 'value': department, 'type': 'text'})
    
    code = _generate_code_preview(db, Teacher, "TEACHER")
    preview['fields'].append({'label': '自动生成代码', 'value': code, 'type': 'code'})

def _preview_update_teacher(params: dict, db: Session, preview: dict):
    """预览更新导师"""
    teacher_identifier = params.get('teacher_identifier')
    updates = params.get('updates', {})
    
    teacher = None
    if teacher_identifier.isdigit():
        teacher = db.query(Teacher).filter(Teacher.id == int(teacher_identifier)).first()
    else:
        teacher = db.query(Teacher).filter(Teacher.name == teacher_identifier).first()
    
    if not teacher:
        similar_teachers = _find_similar_items(db, Teacher, 'name', teacher_identifier)
        if similar_teachers:
            preview['warnings'].append(f'未找到导师"{teacher_identifier}"，建议从以下相似导师中选择：')
            preview['suggestions'] = [{'type': 'teacher', 'items': similar_teachers}]
        else:
            preview['errors'].append(f'导师"{teacher_identifier}"不存在')
        return
    
    preview['fields'] = [
        {'label': '导师标识', 'value': f'{teacher.name} (ID: {teacher.id})', 'type': 'text'},
    ]
    
    field_labels = {
        'name': '姓名',
        'contact_phone': '联系电话',
        'email': '电子邮箱',
        'title': '职称',
        'department': '部门'
    }
    
    for field, value in updates.items():
        label = field_labels.get(field, field)
        old_value = getattr(teacher, field, None)
        preview['fields'].append({
            'label': f'新{label}',
            'value': str(value),
            'type': 'text',
            'changed': True,
            'old_value': str(old_value) if old_value else None
        })


def _preview_add_student(params: dict, db: Session, preview: dict):
    """预览添加学员"""
    # 兼容两种字段命名方式
    name = params.get('name') or params.get('student_name', '')
    phone = params.get('phone') or params.get('contact_phone')
    school = params.get('school')
    grade = params.get('grade')
    contact_person = params.get('contact_person')
    email = params.get('email')
    class_name = params.get('class_name')
    
    if not name:
        preview['errors'].append('缺少学员姓名')
        return
    
    existing_student = db.query(Student).filter(Student.name == name).first()
    
    preview['fields'] = [
        {'label': '学员姓名', 'value': name, 'type': 'text'},
    ]
    
    if existing_student:
        preview['warnings'].append(f'学员"{name}"已存在（ID: {existing_student.id}），将创建重复记录')
    
    if phone:
        preview['fields'].append({'label': '联系电话', 'value': phone, 'type': 'phone'})
    if school:
        preview['fields'].append({'label': '学校', 'value': school, 'type': 'text'})
    if grade:
        preview['fields'].append({'label': '年级', 'value': grade, 'type': 'text'})
    if contact_person:
        preview['fields'].append({'label': '联系人', 'value': contact_person, 'type': 'text'})
    if email:
        preview['fields'].append({'label': '电子邮箱', 'value': email, 'type': 'email'})
    
    if class_name:
        class_obj = db.query(ClassModel).filter(ClassModel.name == class_name).first()
        if class_obj:
            preview['fields'].append({
                'label': '关联班级',
                'value': f'{class_obj.name} (ID: {class_obj.id})',
                'type': 'text'
            })
        else:
            similar_classes = _find_similar_items(db, ClassModel, 'name', class_name)
            if similar_classes:
                preview['warnings'].append(f'未找到班级"{class_name}"，建议从以下相似班级中选择：')
                preview['suggestions'] = [{'type': 'class', 'items': similar_classes}]
            else:
                preview['warnings'].append(f'班级"{class_name}"不存在')
    
    code = _generate_code_preview(db, Student, "STUDENT")
    preview['fields'].append({'label': '自动生成代码', 'value': code, 'type': 'code'})


def _preview_update_student(params: dict, db: Session, preview: dict):
    """预览更新学员"""
    student_identifier = params.get('student_identifier')
    updates = params.get('updates', {})
    
    student = None
    if student_identifier.isdigit():
        student = db.query(Student).filter(Student.id == int(student_identifier)).first()
    else:
        student = db.query(Student).filter(Student.name == student_identifier).first()
    
    if not student:
        similar_students = _find_similar_items(db, Student, 'name', student_identifier)
        if similar_students:
            preview['warnings'].append(f'未找到学员"{student_identifier}"，建议从以下相似学员中选择：')
            preview['suggestions'] = [{'type': 'student', 'items': similar_students}]
        else:
            preview['errors'].append(f'学员"{student_identifier}"不存在')
        return
    
    preview['fields'] = [
        {'label': '学员标识', 'value': f'{student.name} (ID: {student.id})', 'type': 'text'},
    ]
    
    field_labels = {
        'name': '姓名',
        'contact_phone': '联系电话',
        'school': '学校',
        'grade': '年级',
        'contact_person': '联系人',
        'email': '电子邮箱'
    }
    
    for field, value in updates.items():
        label = field_labels.get(field, field)
        old_value = getattr(student, field, None)
        preview['fields'].append({
            'label': f'新{label}',
            'value': str(value),
            'type': 'text',
            'changed': True,
            'old_value': str(old_value) if old_value else None
        })


def _preview_add_class(params: dict, db: Session, preview: dict):
    """预览添加班级"""
    # 兼容两种字段命名方式
    name = params.get('name') or params.get('class_name', '')
    description = params.get('description')
    teacher_name = params.get('teacher_name')
    wechat_webhook = params.get('wechat_webhook')
    grade_level = params.get('grade_level')
    
    if not name:
        preview['errors'].append('缺少班级名称')
        return
    
    existing_class = db.query(ClassModel).filter(ClassModel.name == name).first()
    
    preview['fields'] = [
        {'label': '班级名称', 'value': name, 'type': 'text'},
    ]
    
    if existing_class:
        preview['warnings'].append(f'班级"{name}"已存在（ID: {existing_class.id}），将创建重复记录')
    
    if description:
        preview['fields'].append({'label': '描述', 'value': description, 'type': 'textarea'})
    if teacher_name:
        preview['fields'].append({'label': '班主任', 'value': teacher_name, 'type': 'text'})
    if grade_level:
        preview['fields'].append({'label': '年级', 'value': grade_level, 'type': 'text'})
    if wechat_webhook:
        preview['fields'].append({'label': 'Webhook', 'value': wechat_webhook, 'type': 'url'})
    
    code = _generate_code_preview(db, ClassModel, "CLASS")
    preview['fields'].append({'label': '自动生成代码', 'value': code, 'type': 'code'})

def _preview_update_class(params: dict, db: Session, preview: dict):
    """预览更新班级"""
    class_identifier = params.get('class_identifier')
    updates = params.get('updates', {})
    
    class_obj = None
    if class_identifier.isdigit():
        class_obj = db.query(ClassModel).filter(ClassModel.id == int(class_identifier)).first()
    else:
        class_obj = db.query(ClassModel).filter(ClassModel.name == class_identifier).first()
    
    if not class_obj:
        similar_classes = _find_similar_items(db, ClassModel, 'name', class_identifier)
        if similar_classes:
            preview['warnings'].append(f'未找到班级"{class_identifier}"，建议从以下相似班级中选择：')
            preview['suggestions'] = [{'type': 'class', 'items': similar_classes}]
        else:
            preview['errors'].append(f'班级"{class_identifier}"不存在')
        return
    
    preview['fields'] = [
        {'label': '班级标识', 'value': f'{class_obj.name} (ID: {class_obj.id})', 'type': 'text'},
    ]
    
    field_labels = {
        'name': '名称',
        'description': '描述',
        'wechat_webhook': 'Webhook'
    }
    
    for field, value in updates.items():
        label = field_labels.get(field, field)
        old_value = getattr(class_obj, field, None)
        preview['fields'].append({
            'label': f'新{label}',
            'value': str(value),
            'type': 'text',
            'changed': True,
            'old_value': str(old_value) if old_value else None
        })


def _preview_add_room(params: dict, db: Session, preview: dict):
    """预览添加教室"""
    # 兼容两种字段命名方式
    name = params.get('name') or params.get('room_name', '')
    location = params.get('location')
    capacity = params.get('capacity', 30)
    facilities = params.get('facilities', "普通")
    facility_details = params.get('facility_details', "")
    
    if not name:
        preview['errors'].append('缺少教室名称')
        return
    
    existing_room = db.query(Room).filter(Room.name == name).first()
    
    preview['fields'] = [
        {'label': '教室名称', 'value': name, 'type': 'text'},
        {'label': '容量', 'value': f'{capacity}人', 'type': 'number'},
        {'label': '设施', 'value': facilities, 'type': 'text'},
    ]
    
    if existing_room:
        preview['warnings'].append(f'教室"{name}"已存在（ID: {existing_room.id}），将创建重复记录')
    
    if location:
        preview['fields'].append({'label': '位置', 'value': location, 'type': 'text'})
    if facility_details:
        preview['fields'].append({'label': '设施详情', 'value': facility_details, 'type': 'textarea'})
    
    code = _generate_code_preview(db, Room, "ROOM")
    preview['fields'].append({'label': '自动生成代码', 'value': code, 'type': 'code'})


def _preview_update_room(params: dict, db: Session, preview: dict):
    """预览更新教室"""
    room_identifier = params.get('room_identifier')
    updates = params.get('updates', {})
    
    room = None
    if room_identifier.isdigit():
        room = db.query(Room).filter(Room.id == int(room_identifier)).first()
    else:
        room = db.query(Room).filter(Room.name == room_identifier).first()
    
    if not room:
        similar_rooms = _find_similar_items(db, Room, 'name', room_identifier)
        if similar_rooms:
            preview['warnings'].append(f'未找到教室"{room_identifier}"，建议从以下相似教室中选择：')
            preview['suggestions'] = [{'type': 'room', 'items': similar_rooms}]
        else:
            preview['errors'].append(f'教室"{room_identifier}"不存在')
        return
    
    preview['fields'] = [
        {'label': '教室标识', 'value': f'{room.name} (ID: {room.id})', 'type': 'text'},
    ]
    
    field_labels = {
        'name': '名称',
        'location': '位置',
        'capacity': '容量',
        'facilities': '设施',
        'facility_details': '设施详情'
    }
    
    for field, value in updates.items():
        label = field_labels.get(field, field)
        old_value = getattr(room, field, None)
        preview['fields'].append({
            'label': f'新{label}',
            'value': str(value),
            'type': 'text',
            'changed': True,
            'old_value': str(old_value) if old_value else None
        })


def _preview_add_leave(params: dict, db: Session, preview: dict):
    """预览添加请假"""
    person_name = params.get('person_name', '')
    is_teacher = params.get('is_teacher', False)
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    reason = params.get('reason', '个人原因')
    
    preview['fields'] = [
        {'label': '人员类型', 'value': '导师' if is_teacher else '学员', 'type': 'text'},
        {'label': '人员姓名', 'value': person_name, 'type': 'text'},
        {'label': '开始日期', 'value': start_date or '未提供', 'type': 'date'},
        {'label': '结束日期', 'value': end_date or '未提供', 'type': 'date'},
        {'label': '请假原因', 'value': reason, 'type': 'textarea'},
    ]
    
    # 查找人员
    model_class = Teacher if is_teacher else Student
    person = db.query(model_class).filter(model_class.name == person_name).first()
    
    if not person:
        similar_persons = _find_similar_items(db, model_class, 'name', person_name)
        if similar_persons:
            preview['warnings'].append(f'未找到{"导师" if is_teacher else "学员"}"{person_name}"，建议从以下相似人员中选择：')
            preview['suggestions'] = [{'type': 'teacher' if is_teacher else 'student', 'items': similar_persons}]
        else:
            preview['errors'].append(f'{"导师" if is_teacher else "学员"}"{person_name}"不存在')
    
    if not start_date or not end_date:
        preview['warnings'].append('请提供开始日期和结束日期')


def _preview_add_holiday(params: dict, db: Session, preview: dict):
    """预览添加节假日"""
    date_str = params.get('date')
    name = params.get('name', '')
    description = params.get('description')
    
    preview['fields'] = [
        {'label': '节假日名称', 'value': name, 'type': 'text'},
        {'label': '日期', 'value': date_str or '未提供', 'type': 'date'},
    ]
    
    if description:
        preview['fields'].append({'label': '描述', 'value': description, 'type': 'textarea'})
    
    if date_str:
        from datetime import datetime as dt_datetime
        try:
            holiday_date = dt_datetime.strptime(date_str, '%Y-%m-%d').date()
            existing = db.query(Holiday).filter(Holiday.date == holiday_date).first()
            if existing:
                preview['errors'].append(f'日期 {date_str} 已设置为节假日: {existing.name}')
                preview['need_confirmation'] = False
        except ValueError:
            preview['errors'].append('日期格式错误，请使用 YYYY-MM-DD 格式')
    
    if not date_str:
        preview['warnings'].append('请提供节假日日期')


def _preview_collect_fee(params: dict, db: Session, preview: dict):
    """预览收费"""
    person_name = params.get('person_name', '')
    course_name = params.get('course_name')
    amount = params.get('amount')
    receivable_amount = params.get('receivable_amount')
    payment_date = params.get('payment_date')
    
    preview['fields'] = [
        {'label': '学员姓名', 'value': person_name, 'type': 'text'},
        {'label': '缴费金额', 'value': f'{amount}元' if amount else '未提供', 'type': 'money'},
    ]
    
    if course_name:
        preview['fields'].append({'label': '科目', 'value': course_name, 'type': 'text'})
    if receivable_amount:
        preview['fields'].append({'label': '应收金额', 'value': f'{receivable_amount}元', 'type': 'money'})
    if payment_date:
        preview['fields'].append({'label': '缴费日期', 'value': payment_date, 'type': 'date'})
    
    # 查找学员
    student = db.query(Student).filter(Student.name == person_name).first()
    if not student:
        similar_students = _find_similar_items(db, Student, 'name', person_name)
        if similar_students:
            preview['warnings'].append(f'未找到学员"{person_name}"，建议从以下相似学员中选择：')
            preview['suggestions'] = [{'type': 'student', 'items': similar_students}]
        else:
            preview['errors'].append(f'学员"{person_name}"不存在')
    else:
        # 查找StudentFee
        if course_name:
            course = db.query(Course).filter(Course.name == course_name).first()
            if course:
                student_fee = db.query(StudentFee).filter(
                    StudentFee.student_id == student.id,
                    StudentFee.course_id == course.id
                ).first()
                
                if student_fee:
                    preview['fields'].append({
                        'label': '当前剩余金额',
                        'value': f'{student_fee.remaining_amount}元',
                        'type': 'money'
                    })
                    preview['fields'].append({
                        'label': '缴费后剩余',
                        'value': f'{student_fee.remaining_amount + (amount or 0)}元',
                        'type': 'money',
                        'highlight': True
                    })
                else:
                    preview['warnings'].append(f'学员"{person_name}"在科目"{course_name}"下没有课时费记录，需要先设置课时费标准')
    
    if not course_name:
        preview['warnings'].append('请提供科目名称')
    if not amount:
        preview['warnings'].append('请提供缴费金额')


def _preview_refund_fee(params: dict, db: Session, preview: dict):
    """预览退费"""
    person_name = params.get('person_name', '')
    course_name = params.get('course_name')
    amount = params.get('amount')
    refund_date = params.get('refund_date')
    
    preview['fields'] = [
        {'label': '学员姓名', 'value': person_name, 'type': 'text'},
        {'label': '退费金额', 'value': f'{amount}元' if amount else '未提供', 'type': 'money'},
    ]
    
    if course_name:
        preview['fields'].append({'label': '科目', 'value': course_name, 'type': 'text'})
    if refund_date:
        preview['fields'].append({'label': '退费日期', 'value': refund_date, 'type': 'date'})
    
    # 查找学员和课时费记录
    student = db.query(Student).filter(Student.name == person_name).first()
    if student and course_name:
        course = db.query(Course).filter(Course.name == course_name).first()
        if course:
            student_fee = db.query(StudentFee).filter(
                StudentFee.student_id == student.id,
                StudentFee.course_id == course.id
            ).first()
            
            if student_fee:
                preview['fields'].append({
                    'label': '当前剩余金额',
                    'value': f'{student_fee.remaining_amount}元',
                    'type': 'money'
                })
                preview['fields'].append({
                    'label': '退费后剩余',
                    'value': f'{student_fee.remaining_amount - (amount or 0)}元',
                    'type': 'money',
                    'highlight': True
                })
            else:
                preview['errors'].append(f'学员"{person_name}"在科目"{course_name}"下没有课时费记录')


def _preview_add_grade(params: dict, db: Session, preview: dict):
    """预览添加成绩"""
    student_name = params.get('student_name', '')
    course_name = params.get('course_name')
    score = params.get('score')
    total_score = params.get('total_score')
    exam_date = params.get('exam_date')
    grade_level = params.get('grade_level')
    exam_stage = params.get('exam_stage')
    description = params.get('description')
    
    preview['fields'] = [
        {'label': '学员姓名', 'value': student_name, 'type': 'text'},
        {'label': '科目', 'value': course_name or '未提供', 'type': 'text'},
        {'label': '成绩', 'value': f'{score}/{total_score}' if score and total_score else '未提供', 'type': 'text'},
        {'label': '考试日期', 'value': exam_date or '今天', 'type': 'date'},
        {'label': '年级', 'value': grade_level or '未提供', 'type': 'text'},
        {'label': '考试阶段', 'value': exam_stage or '未提供', 'type': 'text'},
    ]
    
    if description:
        preview['fields'].append({'label': '备注', 'value': description, 'type': 'textarea'})
    
    # 查找学员和科目
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        similar_students = _find_similar_items(db, Student, 'name', student_name)
        if similar_students:
            preview['warnings'].append(f'未找到学员"{student_name}"，建议从以下相似学员中选择：')
            preview['suggestions'] = [{'type': 'student', 'items': similar_students}]
        else:
            preview['errors'].append(f'学员"{student_name}"不存在')
    
    if course_name:
        course = db.query(Course).filter(Course.name == course_name).first()
        if not course:
            similar_courses = _find_similar_items(db, Course, 'name', course_name)
            if similar_courses:
                preview['warnings'].append(f'未找到科目"{course_name}"，建议从以下相似科目中选择：')
                preview['suggestions'].append({'type': 'course', 'items': similar_courses})
            else:
                preview['errors'].append(f'科目"{course_name}"不存在')
        elif student:
            # 计算成绩变化
            previous_grade = db.query(StudentGrade).filter(
                StudentGrade.student_id == student.id,
                StudentGrade.course_id == course.id
            ).order_by(StudentGrade.exam_date.desc()).first()
            
            if previous_grade and score:
                change = score - previous_grade.score
                if change > 0:
                    preview['fields'].append({
                        'label': '成绩变化',
                        'value': f'较上次提高 {change} 分',
                        'type': 'text',
                        'highlight': True
                    })
                elif change < 0:
                    preview['fields'].append({
                        'label': '成绩变化',
                        'value': f'较上次降低 {abs(change)} 分',
                        'type': 'text'
                    })
                else:
                    preview['fields'].append({
                        'label': '成绩变化',
                        'value': '与上次持平',
                        'type': 'text'
                    })


def _preview_create_schedule(params: dict, db: Session, preview: dict):
    """预览创建排课"""
    person_names = params.get('person_names', [])
    class_name = params.get('class_name')
    course_name = params.get('course_name')
    teacher_name = params.get('teacher_name')
    room_name = params.get('room_name')
    day_of_week = params.get('day_of_week')
    start_time = params.get('start_time')
    end_time = params.get('end_time')
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    grade_level = params.get('grade_level')
    
    weekday_names = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_name = weekday_names[day_of_week] if day_of_week and day_of_week <= 7 else '未知'
    
    # 如果有学生姓名但没有班级，尝试自动推断班级
    inferred_class_name = None
    if person_names and not class_name:
        student_classes_map = {}
        for student_name in person_names:
            student = db.query(Student).filter(Student.name == student_name).first()
            if student:
                classes = [c for c in student.classes]
                student_classes_map[student_name] = classes
        
        # 如果只有一个学生，直接使用他的第一个班级
        if len(student_classes_map) == 1:
            student_name = list(student_classes_map.keys())[0]
            classes = student_classes_map[student_name]
            if classes:
                inferred_class_name = classes[0].name
        
        # 如果有多个学生，找到共同班级
        elif len(student_classes_map) > 1:
            all_classes_sets = [set(c.id for c in classes) for classes in student_classes_map.values()]
            if all_classes_sets:
                common_class_ids = all_classes_sets[0]
                for class_set in all_classes_sets[1:]:
                    common_class_ids = common_class_ids.intersection(class_set)
                
                if common_class_ids:
                    # 取第一个共同班级
                    common_class = db.query(ClassModel).filter(ClassModel.id.in_(common_class_ids)).first()
                    if common_class:
                        inferred_class_name = common_class.name
    
    display_class_name = class_name or inferred_class_name
    
    inferred_teacher_name = None
    if display_class_name and course_name and not teacher_name:
        target_class = db.query(ClassModel).filter(ClassModel.name == display_class_name).first()
        if target_class:
            from models import Schedule as ScheduleModel
            schedules = db.query(ScheduleModel).join(
                Course, ScheduleModel.course_id == Course.id
            ).join(
                Teacher, ScheduleModel.teacher_id == Teacher.id
            ).filter(
                ScheduleModel.class_id == target_class.id,
                Course.name == course_name
            ).order_by(ScheduleModel.start_date.desc()).limit(5).all()
            
            if schedules:
                teacher_count = {}
                for schedule in schedules:
                    if schedule.teacher and schedule.teacher.name:
                        teacher_count[schedule.teacher.name] = teacher_count.get(schedule.teacher.name, 0) + 1
                
                if teacher_count:
                    inferred_teacher_name = max(teacher_count, key=teacher_count.get)
                    preview['suggestions'].append({
                        'type': 'info',
                        'message': f'根据历史排课记录，{inferred_teacher_name} 经常教授 {display_class_name} 的 {course_name} 课程'
                    })
            else:
                recent_schedules = db.query(ScheduleModel).join(
                    Teacher, ScheduleModel.teacher_id == Teacher.id
                ).filter(
                    ScheduleModel.class_id == target_class.id,
                    Teacher.is_active == True
                ).order_by(ScheduleModel.start_date.desc()).limit(10).all()
                
                if recent_schedules:
                    teacher_count = {}
                    for schedule in recent_schedules:
                        if schedule.teacher and schedule.teacher.name:
                            teacher_count[schedule.teacher.name] = teacher_count.get(schedule.teacher.name, 0) + 1
                    
                    if teacher_count:
                        inferred_teacher_name = max(teacher_count, key=teacher_count.get)
                        preview['suggestions'].append({
                            'type': 'warning',
                            'message': f'未找到 {course_name} 的历史记录，但 {inferred_teacher_name} 是该班级最近的授课导师'
                        })
                else:
                    preview['suggestions'].append({
                        'type': 'warning',
                        'message': f'未找到 {display_class_name} 的历史排课记录，请手动选择导师'
                    })
    
    display_teacher_name = teacher_name or inferred_teacher_name
    
    # 如果有学生姓名，显示学生列表
    if person_names:
        student_info_list = []
        for student_name in person_names:
            student = db.query(Student).filter(Student.name == student_name).first()
            if student:
                student_classes = [c.name for c in student.classes]
                student_info_list.append({
                    'name': student_name,
                    'id': student.id,
                    'classes': student_classes
                })
        
        preview['fields'].append({
            'label': '学员列表',
            'value': ', '.join(person_names),
            'type': 'text',
            'detail': student_info_list
        })
        
        # 如果找到共同班级或推断出班级，显示提示
        if display_class_name:
            preview['fields'].append({
                'label': '班级',
                'value': display_class_name,
                'type': 'text',
                'highlight': True
            })
            if inferred_class_name and not class_name:
                preview['suggestions'].append({
                    'type': 'info',
                    'message': f'已根据学员"{person_names[0]}"自动推断班级为"{display_class_name}"'
                })
    
    preview['fields'].extend([
        {'label': '科目', 'value': course_name or '未提供', 'type': 'text'},
        {'label': '导师', 'value': display_teacher_name or '未提供', 'type': 'text'},
        {'label': '教室', 'value': room_name or '未提供', 'type': 'text'},
        {'label': '星期', 'value': weekday_name, 'type': 'text'},
        {'label': '时间', 'value': f'{start_time or "??"}-{end_time or "??"}', 'type': 'time'},
        {'label': '开始日期', 'value': start_date or '未提供', 'type': 'date'},
        {'label': '结束日期', 'value': end_date or '未提供', 'type': 'date'},
    ])
    
    if grade_level:
        preview['fields'].append({'label': '年级', 'value': grade_level, 'type': 'text'})
    
    # 标记为需要手动确认
    preview['needs_manual_confirmation'] = True
    preview['has_warning'] = False
    
    # 验证各项是否存在并给出建议
    missing_items = []
    
    if not display_class_name and not person_names:
        missing_items.append('班级或学员')
    
    if course_name:
        course = db.query(Course).filter(Course.name == course_name).first()
        if not course:
            similar_courses = _find_similar_items(db, Course, 'name', course_name)
            if similar_courses:
                preview['warnings'].append(f'未找到科目"{course_name}"，建议从以下相似科目中选择：')
                preview['suggestions'].append({'type': 'course', 'items': similar_courses})
            else:
                preview['errors'].append(f'科目"{course_name}"不存在')
    
    if display_teacher_name:
        teacher = db.query(Teacher).filter(Teacher.name == display_teacher_name).first()
        if not teacher:
            similar_teachers = _find_similar_items(db, Teacher, 'name', display_teacher_name)
            if similar_teachers:
                preview['warnings'].append(f'未找到导师"{display_teacher_name}"，建议从以下相似导师中选择：')
                preview['suggestions'].append({'type': 'teacher', 'items': similar_teachers})
            else:
                preview['errors'].append(f'导师"{display_teacher_name}"不存在')
    
    if room_name:
        room = db.query(Room).filter(Room.name == room_name).first()
        if not room:
            similar_rooms = _find_similar_items(db, Room, 'name', room_name)
            if similar_rooms:
                preview['warnings'].append(f'未找到教室"{room_name}"，建议从以下相似教室中选择：')
                preview['suggestions'].append({'type': 'room', 'items': similar_rooms})
            else:
                preview['errors'].append(f'教室"{room_name}"不存在')
    
    if missing_items:
        preview['warnings'].append(f'以下信息需要在排课界面补充：{", ".join(missing_items)}')

# 辅助函数
def _find_similar_items(db: Session, model_class, name_field: str, search_name: str, threshold: float = 0.6) -> List:
    """查找相似的项目"""
    all_items = db.query(model_class).all()
    similar_items = []
    
    for item in all_items:
        item_name = getattr(item, name_field, '')
        similarity = _calculate_similarity(search_name, item_name)
        if similarity >= threshold:
            similar_items.append({
                'id': item.id,
                'name': item_name,
                'similarity': round(similarity, 2)
            })
    
    similar_items.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_items[:5]


def _calculate_similarity(str1: str, str2: str) -> float:
    """计算两个字符串的相似度"""
    if not str1 or not str2:
        return 0.0
    
    str1_lower = str1.lower()
    str2_lower = str2.lower()
    
    if str1_lower == str2_lower:
        return 1.0
    
    if str1_lower in str2_lower or str2_lower in str1_lower:
        return 0.8
    
    set1 = set(str1_lower)
    set2 = set(str2_lower)
    intersection = set1 & set2
    union = set1 | set2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def _generate_code_preview(db: Session, model_class, prefix: str) -> str:
    """生成预览编码 - 查询数据库当前最大代码并+1"""
    import re
    
    # 获取所有非空代码
    all_codes = db.query(model_class.code).filter(
        model_class.code.isnot(None),
        model_class.code != ''
    ).all()
    
    if not all_codes or not any(code[0] for code in all_codes):
        # 如果没有代码，返回提示
        return "请手动输入代码"
    
    # 提取所有代码
    codes = [code_tuple[0] for code_tuple in all_codes if code_tuple[0]]
    
    # 尝试从每个代码中提取数字部分，找到最大的
    max_code = None
    max_num = -1
    
    for code in codes:
        # 使用正则表达式提取代码中的数字部分
        match = re.search(r'(\d+)$', code)
        if match:
            try:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
                    max_code = code
            except ValueError:
                continue
    
    if max_code is None:
        # 如果无法提取数字，按字符串排序取最后一个
        codes.sort()
        return f"建议在 {codes[-1]} 基础上+1"
    
    # 提取前缀和数字格式
    match = re.match(r'(.*?)(\d+)$', max_code)
    if match:
        prefix_part = match.group(1)
        num_part = match.group(2)
        # 新数字 = 最大数字 + 1
        new_num = max_num + 1
        # 保持原有的数字位数（如 001 -> 002, 010 -> 011）
        new_code = f"{prefix_part}{new_num:0{len(num_part)}d}"
        return new_code
    else:
        # 如果无法解析，按字符串排序取最后一个并提示
        codes.sort()
        return f"建议在 {codes[-1]} 基础上+1"

def get_action_name(action: str) -> str:
    """获取操作的中文名称"""
    action_names = {
        'add_course': '添加科目',
        'update_course': '更新科目',
        'complete_schedule': '完成课程',
        'cancel_schedule': '取消课程',
        'postpone_schedule': '延期课程',
        'add_teacher': '添加导师',
        'update_teacher': '更新导师',
        'add_student': '添加学员',
        'update_student': '更新学员',
        'add_class': '添加班级',
        'update_class': '更新班级',
        'add_room': '添加教室',
        'update_room': '更新教室',
        'add_leave': '添加请假',
        'add_holiday': '添加节假日',
        'collect_fee': '收取费用',
        'refund_fee': '退费',
        'add_grade': '添加成绩',
        'create_schedule': '创建排课',
    }
    return action_names.get(action, action)