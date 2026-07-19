# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from typing import List, Optional
from datetime import date
from database import get_db
from models import Student, Class, Schedule, Course, Teacher
from schemas import StudentCreate, StudentUpdate, Student as StudentSchema, PaginatedStudentResponse
from routers.auth import get_teacher_visibility_filter, get_current_user,  get_current_course_admin_user, User
from utils.logger import log_operation

router = APIRouter()

@router.get("", response_model=PaginatedStudentResponse)
def get_students(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    class_id: Optional[int] = None,
    sort_field: Optional[str] = Query(None, description="排序字段，如：id, code, name"),
    sort_order: Optional[str] = Query("asc", description="排序顺序：asc 或 desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Student)

    #应用导师可见性过滤
    teacher_filter = get_teacher_visibility_filter(db, current_user)
    
    if teacher_filter is not None:
        if hasattr(teacher_filter, 'compile'):
            query = query.filter(teacher_filter)
        else:
            log_operation(db, "学员管理", "应用导师过滤", f"教师ID: {teacher_filter} - {current_user.username}", current_user.username, "DEBUG")
            
            # 逻辑链条：导师 -> 他的排课(Schedule) -> 涉及的班级(Class) -> 班级里的学生(Student)
            # 1. 先找到该导师排课的所有班级 ID（使用更高效的查询）
            allowed_class_ids_subquery = db.query(Schedule.class_id).filter(
                Schedule.teacher_id == teacher_filter,
                Schedule.class_id.isnot(None)  # 排除空值
            ).distinct()
            
            # 执行子查询获取班级ID列表
            allowed_class_ids_list = [row[0] for row in allowed_class_ids_subquery.all()]
            
            if allowed_class_ids_list:
                # 2. 过滤学生：只保留那些属于上述班级的学生
                query = query.join(Student.classes).filter(Class.id.in_(allowed_class_ids_list))
                
                # 如果前端还传了具体的 class_id，也要确保它在允许范围内（双重保险）
                if class_id is not None and class_id not in allowed_class_ids_list:
                    # 如果请求的class_id不在允许列表中，返回空结果
                    return {"items": [], "total": 0}
            else:
                # 如果导师没有任何排课，返回空结果
                return {"items": [], "total": 0}
                
            # 使用 distinct 防止一个学生在多个允许班级时重复出现
            query = query.distinct()
    else:
        log_operation(db, "学员管理", "导师可见性限制未启用", f"教师ID: {current_user.id} - {current_user.username}", current_user.username, "DEBUG")
        # 如果没有开启限制，但前端传了 class_id，正常过滤
        if class_id is not None:
            query = query.join(Student.classes).filter(Class.id == class_id)

    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) | 
            (Student.code.ilike(f'%{search}%')) |
            (Student.school.ilike(f'%{search}%'))|
            (Student.grade.ilike(f'%{search}%'))|
            (Student.contact_person.ilike(f'%{search}%'))|
            (Student.contact_phone.ilike(f'%{search}%'))|
            (Student.email.ilike(f'%{search}%'))
        )
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)
    # 注意：class_id 的过滤已经在上面的导师过滤逻辑中处理了

    # 应用排序
    if sort_field:
        sort_column = getattr(Student, sort_field, None)
        if sort_column:
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
    else:
        # 默认按ID降序排列
        query = query.order_by(desc(Student.id))

    # 添加eager loading加载classes关系
    query = query.options(joinedload(Student.classes))
    
    # 先获取总数（在分页之前）
    total = query.count()
    
    # 再获取分页数据
    students = query.offset(skip).limit(limit).all()

    # 手动构建返回数据，确保class_ids正确填充
    result = []
    for student in students:
        class_ids = [c.id for c in student.classes] if student.classes else []
        classes_list = [{"id": c.id, "name": c.name} for c in student.classes] if student.classes else []
        result.append(StudentSchema(
            id=student.id,
            code=student.code,
            name=student.name,
            school=student.school,
            grade=student.grade,
            enrollment_date=student.enrollment_date,
            class_ids=class_ids,
            classes=classes_list,
            available_days=student.available_days,
            available_time_slots=student.available_time_slots,
            allow_holiday_scheduling=student.allow_holiday_scheduling,
            contact_person=student.contact_person,
            contact_phone=student.contact_phone,
            email=student.email,
            is_active=student.is_active,
            end_date=student.end_date,
            created_at=student.created_at,
            updated_at=student.updated_at
        ))
    
    return {
        "items": result,
        "total": total
    }

@router.get("/{student_id}", response_model=StudentSchema)
def get_student(student_id: int, db: Session = Depends(get_db)):
    # 使用joinedload加载classes关系，确保编辑时能正确获取班级信息
    student = db.query(Student).options(joinedload(Student.classes)).filter(Student.id == student_id).first()
    if not student:
        log_operation(db, "学员管理", "获取学员详情失败", f"学员ID {student_id} 不存在", get_current_user(db).username, "WARNING")
        raise HTTPException(status_code=404, detail="学员不存在")
    
    # 手动构建返回数据，确保class_ids正确填充
    class_ids = [c.id for c in student.classes] if student.classes else []
    classes_list = [{"id": c.id, "name": c.name} for c in student.classes] if student.classes else []
    return StudentSchema(
        id=student.id,
        code=student.code,
        name=student.name,
        school=student.school,
        grade=student.grade,
        enrollment_date=student.enrollment_date,
        class_ids=class_ids,
        classes=classes_list,
        available_days=student.available_days,
        available_time_slots=student.available_time_slots,
        allow_holiday_scheduling=student.allow_holiday_scheduling,
        contact_person=student.contact_person,
        contact_phone=student.contact_phone,
        email=student.email,
        is_active=student.is_active,
        end_date=student.end_date,
        created_at=student.created_at,
        updated_at=student.updated_at
    )

@router.post("", response_model=StudentSchema)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_student = db.query(Student).filter(Student.code == student.code).first()
    if db_student:
        log_operation(db, "学员管理", "创建学员失败", f"学员代码 {student.code} 已存在", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="学员代码已存在")
    
    db_student = Student(
        code=student.code,
        name=student.name,
        school=student.school,
        grade=student.grade,
        enrollment_date=student.enrollment_date,
        available_days=student.available_days,
        available_time_slots=student.available_time_slots,
        allow_holiday_scheduling=student.allow_holiday_scheduling,
        contact_person=student.contact_person,
        contact_phone=student.contact_phone,
        email=student.email,
        is_active=student.is_active, 
        end_date=student.end_date, 
        created_at=student.created_at, 
        updated_at=student.updated_at
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    # 关联班级
    if student.class_ids:
        classes = db.query(Class).filter(Class.id.in_(student.class_ids)).all()
        db_student.classes = classes
        db.commit()
        db.refresh(db_student)

    # 手动构建返回数据，确保class_ids正确填充
    class_ids = [c.id for c in db_student.classes] if db_student.classes else []
    log_operation(db, "学员管理", "新增",  f"成功创建学员: {db_student.code} - {db_student.name}", current_user.username)
    return StudentSchema(
        id=db_student.id,
        code=db_student.code,
        name=db_student.name,
        school=db_student.school,
        grade=db_student.grade,
        enrollment_date=db_student.enrollment_date,
        class_ids=class_ids,
        available_days=db_student.available_days,
        available_time_slots=db_student.available_time_slots,
        allow_holiday_scheduling=db_student.allow_holiday_scheduling,
        contact_person=db_student.contact_person,
        contact_phone=db_student.contact_phone,
        is_active=db_student.is_active,
        end_date=db_student.end_date,
        created_at=db_student.created_at,
        updated_at=db_student.updated_at
    )

@router.put("/{student_id}", response_model=StudentSchema)
def update_student(
    student_id: int,
    student: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        log_operation(db, "学员管理", "修改学员失败", f"学员ID {student_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="学员不存在")
    
    # 检查is_active是否从True变为False
    is_becoming_inactive = (db_student.is_active == True and student.is_active == False)
    
    if student.name is not None:
        db_student.name = student.name
    if student.school is not None:
        db_student.school = student.school
    if student.grade is not None:
        db_student.grade = student.grade
    if student.enrollment_date is not None:
        db_student.enrollment_date = student.enrollment_date
    if student.class_ids is not None:
        # 更新多对多关系
        db_student.classes = []
        for class_id in student.class_ids:
            class_ = db.query(Class).filter(Class.id == class_id).first()
            if class_:
                db_student.classes.append(class_)
    else:
        # 明确设置为空列表（清空班级关系）
        db_student.classes = []
        db.commit()
    if student.available_days is not None:
        db_student.available_days = student.available_days
    if student.available_time_slots is not None:
        db_student.available_time_slots = student.available_time_slots
    if student.allow_holiday_scheduling is not None:
        db_student.allow_holiday_scheduling = student.allow_holiday_scheduling
    if student.contact_person is not None:
        db_student.contact_person = student.contact_person
    if student.contact_phone is not None:
        db_student.contact_phone = student.contact_phone
    if student.email is not None:
        db_student.email = student.email
    if student.is_active is not None:
        db_student.is_active = student.is_active
    if student.end_date is not None:
        db_student.end_date = student.end_date
    
    # 如果从在读变为非在读，检查是否填写了结束日期
    if is_becoming_inactive and db_student.end_date is None:
        log_operation(db, "学员管理", "修改学员失败", f"学员 {db_student.name} (ID: {db_student.id}) 非在读但未填写结束日期", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="学员非在读时必须填写结束日期")
    
    db.commit()
    log_operation(db, "学员管理", "修改", f"学员 {db_student.name} (ID: {db_student.id}) 信息成功更新", current_user.username)
    db.refresh(db_student)
    
    # 如果从在读变为非在读，写入日志
    if is_becoming_inactive:
        log_operation(db, "学员管理", "修改", f"学员 {db_student.name} (ID: {db_student.id}) 在读状态更新为非在读，结束日期: {db_student.end_date}")
    
    # 获取班级ID列表
    class_ids = [c.id for c in db_student.classes]
    return StudentSchema(
        id=db_student.id,
        code=db_student.code,
        name=db_student.name,
        school=db_student.school,
        grade=db_student.grade,
        enrollment_date=db_student.enrollment_date,
        class_ids=class_ids,
        available_days=db_student.available_days,
        available_time_slots=db_student.available_time_slots,
        allow_holiday_scheduling=db_student.allow_holiday_scheduling,
        contact_person=db_student.contact_person,
        contact_phone=db_student.contact_phone,
        is_active=db_student.is_active,
        end_date=db_student.end_date,
        created_at=db_student.created_at,
        updated_at=db_student.updated_at
    )

@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    log_operation(db, "学员管理", "删除学员", f"尝试删除学员ID {student_id}", current_user.username, "DEBUG")
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        log_operation(db, "学员管理", "删除学员失败", f"学员ID {student_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="学员不存在")
    
    if db_student.schedules:
        log_operation(db, "学员管理", "删除学员失败", f"学员 {db_student.code} - {db_student.name} 已有课程安排，无法删除", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="该学员已有课程安排，无法删除")
    
    db.delete(db_student)
    db.commit()
    log_operation(db, "学员管理", "删除", f"成功删除学员: {db_student.code} - {db_student.name}", current_user.username, "WARNING")
    return {"message": "删除成功"}

# 年级升级映射表
GRADE_UPGRADE_MAP = {
    "小学1年级": "小学2年级", "小学2年级": "小学3年级", "小学3年级": "小学4年级",
    "小学4年级": "小学5年级", "小学5年级": "小学6年级", "小学6年级": "初中1年级",
    "初中1年级": "初中2年级", "初中2年级": "初中3年级", "初中3年级": "高中1年级",
    "高中1年级": "高中2年级", "高中2年级": "高中3年级", "高中3年级": "大学1年级",
    "大学1年级": "大学2年级", "大学2年级": "大学3年级", "大学3年级": "大学4年级",
    "大学4年级": "大学5年级", "大学5年级": "研究生1年级",
    "研究生1年级": "研究生2年级", "研究生2年级": "研究生3年级", "研究生3年级": "博士1年级",
    "博士1年级": "博士2年级", "博士2年级": "博士3年级",
}

@router.post("/upgrade-grades")
def upgrade_grades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user)
):
    """每年9月1日后手动触发年级升级，将所有活跃学员升级到下一级"""
    today = date.today()
    current_year = today.year

    if today < date(current_year, 9, 1):
        raise HTTPException(status_code=400, detail="年级升级仅在每年9月1日后可用")

    active_students = db.query(Student).filter(
        Student.is_active == True,
        (Student.grade_updated_year != current_year) | (Student.grade_updated_year == None)
    ).all()

    upgraded = []
    skipped = []

    for student in active_students:
        if student.grade in GRADE_UPGRADE_MAP:
            new_grade = GRADE_UPGRADE_MAP[student.grade]
            old_grade = student.grade
            student.grade = new_grade
            student.grade_updated_year = current_year
            upgraded.append({
                "id": student.id,
                "name": student.name,
                "old_grade": old_grade,
                "new_grade": new_grade
            })
        else:
            skipped.append({
                "id": student.id,
                "name": student.name,
                "grade": student.grade,
                "reason": "已为终态年级或不在升级映射表中"
            })

    if upgraded:
        db.commit()
        log_operation(db, "学员管理", "年级升级", f"成功升级 {len(upgraded)} 名学员的年级，跳过 {len(skipped)} 名", current_user.username)

    return {
        "upgraded_count": len(upgraded),
        "skipped_count": len(skipped),
        "upgraded": upgraded,
        "skipped": skipped
    }