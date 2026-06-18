# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from typing import List, Optional, Dict
from datetime import datetime
from database import get_db
from models import StudentGrade, Student, Course, Settings
from schemas import StudentGradeCreate, StudentGradeUpdate, StudentGrade as StudentGradeSchema, GradeTrendData, PaginatedGradeResponse, BatchGradeCreate
from routers.auth import get_current_user, get_current_course_admin_user, User
from utils.logger import log_operation
import json

router = APIRouter()

def check_grade_manager_permission(db: Session, current_user: User):
    """检查用户是否有成绩管理权限（包含授权检查），不通过时直接抛出HTTPException"""
    from routers.license import _check_premium_feature
    if not _check_premium_feature('grade_trend', db):
        raise HTTPException(status_code=403, detail="成绩管理为授权功能，请在系统授权管理中激活")
    if current_user.role in ['super_admin', 'system_admin']:
        return True
    if current_user.teacher_id:
        settings = db.query(Settings).first()
        if settings and settings.grade_managers:
            try:
                grade_managers = json.loads(settings.grade_managers)
                if current_user.teacher_id in grade_managers:
                    return True
            except:
                pass
    raise HTTPException(status_code=403, detail="权限不足，需要管理员或成绩管理导师权限")

@router.get("", response_model=PaginatedGradeResponse)
def get_grades(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_grade_manager_permission(db, current_user)

    query = db.query(StudentGrade).options(
        joinedload(StudentGrade.student).joinedload(Student.classes),
        joinedload(StudentGrade.course).joinedload(Course.teachers)
    )
    
    if student_id is not None:
        query = query.filter(StudentGrade.student_id == student_id)
    if course_id is not None:
        query = query.filter(StudentGrade.course_id == course_id)
    if start_date is not None:
        query = query.filter(StudentGrade.exam_date >= start_date)
    if end_date is not None:
        query = query.filter(StudentGrade.exam_date <= end_date)
    
    total = query.count()
    grades = query.order_by(StudentGrade.exam_date.desc().nullslast()).offset(skip).limit(limit).all()
    
    result = []
    for i, grade in enumerate(grades):
        score_change = None
        if i < len(grades) - 1:
            next_grade = grades[i + 1]
            if next_grade.course_id == grade.course_id and grade.exam_date and next_grade.exam_date:
                score_change = grade.score - next_grade.score
        
        # 构建学生信息
        student_name = grade.student.name if grade.student else None
        student_school = grade.student.school if grade.student else None
        student_grade_info = grade.student.grade if grade.student else None
        student_contact_person = grade.student.contact_person if grade.student else None
        student_contact_phone = grade.student.contact_phone if grade.student else None
        student_is_active = grade.student.is_active if grade.student else None
        student_classes = []
        if grade.student and grade.student.classes:
            student_classes = [{"id": cls.id, "name": cls.name} for cls in grade.student.classes]
        
        # 构建课程信息
        course_name = grade.course.name if grade.course else None
        course_teachers = []
        if grade.course and grade.course.teachers:
            course_teachers = [
                {
                    "id": teacher.id,
                    "name": teacher.name,
                    "contact_phone": teacher.contact_phone,
                    "email": teacher.email
                } 
                for teacher in grade.course.teachers
            ]
        
        grade_dict = {
            "id": grade.id,
            "student_id": grade.student_id,
            "course_id": grade.course_id,
            "exam_date": grade.exam_date,
            "grade_level": grade.grade_level,
            "exam_stage": grade.exam_stage,
            "score": grade.score,
            "total_score": grade.total_score,
            "score_change": score_change,
            "description": grade.description,
            "student_name": student_name,
            "student_school": student_school,
            "student_grade_info": student_grade_info,
            "student_contact_person": student_contact_person,
            "student_contact_phone": student_contact_phone,
            "student_classes": student_classes,
            "student_is_active": student_is_active,
            "course_name": course_name,
            "course_teachers": course_teachers,
            "created_at": grade.created_at,
            "updated_at": grade.updated_at
        }
        result.append(StudentGradeSchema(**grade_dict))
    
    return {
        "items": result,
        "total": total
    }


@router.get("/{grade_id}", response_model=StudentGradeSchema)
def get_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_grade_manager_permission(db, current_user)

    grade = db.query(StudentGrade).options(
        joinedload(StudentGrade.student).joinedload(Student.classes),
        joinedload(StudentGrade.course).joinedload(Course.teachers)
    ).filter(StudentGrade.id == grade_id).first()
    
    if not grade:
        log_operation(db, "成绩管理", "获取成绩详情失败", f"成绩记录ID {grade_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="成绩记录不存在")
    
    score_change = None
    if grade.exam_date is not None:
        previous_grade = db.query(StudentGrade).filter(
            StudentGrade.student_id == grade.student_id,
            StudentGrade.course_id == grade.course_id,
            StudentGrade.exam_date < grade.exam_date
        ).order_by(desc(StudentGrade.exam_date)).first()
        
        if previous_grade:
            score_change = grade.score - previous_grade.score
    
    # 构建学生信息
    student_name = grade.student.name if grade.student else None
    student_school = grade.student.school if grade.student else None
    student_grade_info = grade.student.grade if grade.student else None
    student_contact_person = grade.student.contact_person if grade.student else None
    student_contact_phone = grade.student.contact_phone if grade.student else None
    student_is_active = grade.student.is_active if grade.student else None
    student_classes = []
    if grade.student and grade.student.classes:
        student_classes = [{"id": cls.id, "name": cls.name} for cls in grade.student.classes]
    
    # 构建课程信息
    course_name = grade.course.name if grade.course else None
    course_teachers = []
    if grade.course and grade.course.teachers:
        course_teachers = [
            {
                "id": teacher.id,
                "name": teacher.name,
                "contact_phone": teacher.contact_phone
            } 
            for teacher in grade.course.teachers
        ]
    
    return StudentGradeSchema(
        id=grade.id,
        student_id=grade.student_id,
        course_id=grade.course_id,
        exam_date=grade.exam_date,
        grade_level=grade.grade_level,
        exam_stage=grade.exam_stage,
        score=grade.score,
        total_score=grade.total_score,
        score_change=score_change,
        description=grade.description,
        student_name=student_name,
        student_school=student_school,
        student_grade_info=student_grade_info,
        student_contact_person=student_contact_person,
        student_contact_phone=student_contact_phone,
        student_classes=student_classes,
        student_is_active=student_is_active,
        course_name=course_name,
        course_teachers=course_teachers,
        created_at=grade.created_at,
        updated_at=grade.updated_at
    )

@router.get("/trend/{student_id}/{course_id}", response_model=List[GradeTrendData])
def get_grade_trend(
    student_id: int,
    course_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_grade_manager_permission(db, current_user)

    query = db.query(StudentGrade).filter(
        StudentGrade.student_id == student_id,
        StudentGrade.course_id == course_id
    )
    
    if start_date is not None:
        query = query.filter(StudentGrade.exam_date >= start_date)
    if end_date is not None:
        query = query.filter(StudentGrade.exam_date <= end_date)
    
    grades = query.order_by(StudentGrade.exam_date.asc().nullslast()).all()
    
    result = []
    for i, grade in enumerate(grades):
        score_change = None
        if i > 0:
            previous_grade = grades[i - 1]
            if grade.exam_date and previous_grade.exam_date:
                score_change = grade.score - previous_grade.score
        
        ratio = None
        if grade.total_score and grade.total_score > 0:
            ratio = (grade.score / grade.total_score) * 100
        
        date_str = grade.exam_date.strftime("%Y-%m-%d") if grade.exam_date else "未设置"
        
        result.append(GradeTrendData(
            date=date_str,
            score=grade.score,
            ratio=ratio,
            total_score=grade.total_score,
            score_change=score_change
        ))
    
    return result

@router.get("/student-trend/{student_id}")
def get_student_all_courses_trend(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_grade_manager_permission(db, current_user)
 
    """获取学生所有科目的成绩趋势数据"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    grades = db.query(StudentGrade).filter(
        StudentGrade.student_id == student_id
    ).options(
        joinedload(StudentGrade.course)
    ).order_by(StudentGrade.exam_date.asc().nullslast()).all()
    
    import json
    settings = db.query(Settings).first()
    default_grade_order = [
        '小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
        '初中一年级', '初中二年级', '初中三年级',
        '高中一年级', '高中二年级', '高中三年级',
        '大学一年级', '大学二年级', '大学三年级', '大学四年级',
        '研究生一年级', '研究生二年级', '研究生三年级'
    ]
    grade_order = default_grade_order

    default_exam_stage_order = [
        '秋季月考A', '秋季月考B', '秋季期中', '秋季月考C', '秋季月考D', '秋季期末',
        '春季月考A', '春季月考B', '春季期中', '春季月考C', '春季月考D', '春季期末', 
        '中考一模', '中考二模', '中考三模', '中考', '会考', 
        '高考特训A', '高考特训B', '高考特训C', '春季高考',
        '高考一模', '高考二模', '高考三模', '夏季高考'
    ]
    exam_stage_order = default_exam_stage_order
    if settings and settings.course_config:
        try:
            config = json.loads(settings.course_config)
            if 'grade_options' in config and config['grade_options']:
                grade_order = config['grade_options']
            if 'exam_stages' in config and config['exam_stages']:
                exam_stage_order = config['exam_stages']
        except (json.JSONDecodeError, TypeError):
            pass
    
    def get_grade_priority(grade_level):
        if grade_level in grade_order:
            return grade_order.index(grade_level)
        return 999
    
    def get_exam_stage_priority(exam_stage):
        if exam_stage in exam_stage_order:
            return exam_stage_order.index(exam_stage)
        return 999
    
    courses_data = {}
    all_exam_stages = set()
    
    for grade in grades:
        course_name = grade.course.name if grade.course else f"科目{grade.course_id}"
        
        if course_name not in courses_data:
            courses_data[course_name] = {
                "data": []
            }
        
        exam_date_str = grade.exam_date.strftime('%Y-%m-%d') if grade.exam_date else "未设置"
        exam_stage_key = f"{grade.exam_stage}_{exam_date_str}"
        all_exam_stages.add((grade.exam_stage, exam_date_str, grade.grade_level))
        
        # 计算比例：如果total_score存在且大于0，则计算比例；否则ratio为None
        ratio = None
        if grade.total_score and grade.total_score > 0:
            ratio = round((grade.score / grade.total_score) * 100, 1)
        
        courses_data[course_name]["data"].append({
            "exam_stage": grade.exam_stage,
            "exam_date": exam_date_str,
            "score": grade.score,
            "total_score": grade.total_score,
            "ratio": ratio,
            "grade_level": grade.grade_level,
            "description": grade.description
        })
    
    sorted_stages = sorted(all_exam_stages, key=lambda x: (
        get_grade_priority(x[2]),
        get_exam_stage_priority(x[0]),
        x[1]
    ))
    
    colors = [
        '#5470c6', '#91cc75', '#fac858', '#ee6666', 
        '#73c0de', '#3ba272', '#fc8452', '#9a60b4',
        '#ea7ccc', '#5ab1ef', '#ffb980', '#d87a80'
    ]
    
    result = {
        "student_name": student.name,
        "courses": [],
        "exam_stages": [{"stage": stage[0], "date": stage[1]} for stage in sorted_stages]
    }
    
    for idx, (course_name, course_info) in enumerate(courses_data.items()):
        color = colors[idx % len(colors)]
        
        stage_score_map = {}
        for data_point in course_info["data"]:
            key = f"{data_point['exam_stage']}_{data_point['exam_date']}"
            stage_score_map[key] = {
                "score": data_point["score"],
                "total_score": data_point["total_score"],
                "ratio": data_point["ratio"]
            }
        
        series_data = []
        for stage, date, _ in sorted_stages:
            key = f"{stage}_{date}"
            if key in stage_score_map:
                score_data = stage_score_map[key]
                series_data.append({
                    "value": score_data["ratio"] if score_data["ratio"] is not None else 0,
                    "score": score_data["score"],
                    "total_score": score_data["total_score"],
                    "ratio": score_data["ratio"],
                    "exam_stage": stage,
                    "exam_date": date,
                    "has_data": True
                })
            else:
                series_data.append({
                    "value": None,
                    "score": None,
                    "total_score": None,
                    "ratio": None,
                    "exam_stage": stage,
                    "exam_date": date,
                    "has_data": False
                })
        
        result["courses"].append({
            "course_name": course_name,
            "color": color,
            "data": series_data
        })
    
    return result

@router.post("", response_model=StudentGradeSchema)
def create_grade(
    grade: StudentGradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_grade_manager_permission(db, current_user)

    student = db.query(Student).filter(Student.id == grade.student_id).first()
    if not student:
        log_operation(db, "成绩管理", "创建成绩失败", f"学生ID {grade.student_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="学生不存在")
    
    course = db.query(Course).filter(Course.id == grade.course_id).first()
    if not course:
        log_operation(db, "成绩管理", "创建成绩失败", f"科目ID {grade.course_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="科目不存在")
    
    # 查找历史成绩：同一学生、同一科目、同一年级（不限考试阶段）
    # 按创建时间排序，取最近的一次
    previous_grade = db.query(StudentGrade).filter(
        StudentGrade.student_id == grade.student_id,
        StudentGrade.course_id == grade.course_id,
        StudentGrade.grade_level == grade.grade_level,
        StudentGrade.id != None
    ).order_by(desc(StudentGrade.created_at)).first()
    
    score_change = None
    if previous_grade:
        score_change = grade.score - previous_grade.score
    
    db_grade = StudentGrade(
        student_id=grade.student_id,
        course_id=grade.course_id,
        exam_date=grade.exam_date,
        grade_level=grade.grade_level,
        exam_stage=grade.exam_stage,
        score=grade.score,
        total_score=grade.total_score,
        score_change=score_change,
        description=grade.description
    )
    
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    
    log_operation(db, "成绩管理", "新建", f"学生 {student.name} (ID: {grade.student_id}) 科目 {course.name} 成绩 {grade.score} 被成功添加", current_user.username)
    
    # 构建学生信息
    student_classes = []
    if student.classes:
        student_classes = [{"id": cls.id, "name": cls.name} for cls in student.classes]
    
    # 构建课程信息
    course_teachers = []
    if course.teachers:
        course_teachers = [
            {
                "id": teacher.id,
                "name": teacher.name,
                "contact_phone": teacher.contact_phone
            }  
            for teacher in course.teachers
        ]
    
    return StudentGradeSchema(
        id=db_grade.id,
        student_id=db_grade.student_id,
        course_id=db_grade.course_id,
        exam_date=db_grade.exam_date,
        grade_level=db_grade.grade_level,
        exam_stage=db_grade.exam_stage,
        score=db_grade.score,
        total_score=db_grade.total_score,
        score_change=db_grade.score_change,
        description=db_grade.description,
        student_name=student.name,
        student_school=student.school,
        student_grade_info=student.grade,
        student_contact_person=student.contact_person,
        student_contact_phone=student.contact_phone,
        student_classes=student_classes,
        student_is_active=student.is_active,
        course_name=course.name,
        course_teachers=course_teachers,
        created_at=db_grade.created_at,
        updated_at=db_grade.updated_at
    )

@router.post("/batch", response_model=dict)
def batch_create_grades(
    batch_data: BatchGradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建成绩记录"""
    check_grade_manager_permission(db, current_user)

    if not batch_data.grades:
        raise HTTPException(status_code=400, detail="成绩列表不能为空")
    
    success_count = 0
    failed_count = 0
    errors = []
    
    for idx, grade_data in enumerate(batch_data.grades):
        try:
            student = db.query(Student).filter(Student.id == grade_data.student_id).first()
            if not student:
                errors.append(f"第{idx+1}条记录：学生ID {grade_data.student_id} 不存在")
                failed_count += 1
                continue
            
            course = db.query(Course).filter(Course.id == grade_data.course_id).first()
            if not course:
                errors.append(f"第{idx+1}条记录：科目ID {grade_data.course_id} 不存在")
                failed_count += 1
                continue
            
            previous_grade = None
            if grade_data.exam_date is not None:
                previous_grade = db.query(StudentGrade).filter(
                    StudentGrade.student_id == grade_data.student_id,
                    StudentGrade.course_id == grade_data.course_id,
                    StudentGrade.exam_date < grade_data.exam_date
                ).order_by(desc(StudentGrade.exam_date)).first()
            
            score_change = None
            if previous_grade:
                score_change = grade_data.score - previous_grade.score
            
            db_grade = StudentGrade(
                student_id=grade_data.student_id,
                course_id=grade_data.course_id,
                exam_date=grade_data.exam_date,
                grade_level=grade_data.grade_level,
                exam_stage=grade_data.exam_stage,
                score=grade_data.score,
                total_score=grade_data.total_score,
                score_change=score_change,
                description=grade_data.description
            )
            
            db.add(db_grade)
            success_count += 1
            
        except Exception as e:
            errors.append(f"第{idx+1}条记录：{str(e)}")
            failed_count += 1
    
    try:
        db.commit()
        
        log_operation(
            db, 
            "成绩管理", 
            "批量新建", 
            f"批量添加成绩：成功{success_count}条，失败{failed_count}条", 
            current_user.username
        )
        
        return {
            "message": "批量添加完成",
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量添加失败：{str(e)}")

@router.put("/{grade_id}", response_model=StudentGradeSchema)
def update_grade(
    grade_id: int,
    grade_update: StudentGradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_grade_manager_permission(db, current_user)

    db_grade = db.query(StudentGrade).filter(StudentGrade.id == grade_id).first()
    if not db_grade:
        log_operation(db, "成绩管理", "修改成绩失败", f"成绩记录ID {grade_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="成绩记录不存在")
    
    if grade_update.course_id is not None:
        db_grade.course_id = grade_update.course_id
    if grade_update.exam_date is not None:
        db_grade.exam_date = grade_update.exam_date
    if grade_update.grade_level is not None:
        db_grade.grade_level = grade_update.grade_level
    if grade_update.exam_stage is not None:
        db_grade.exam_stage = grade_update.exam_stage
    if grade_update.score is not None:
        db_grade.score = grade_update.score
    if grade_update.total_score is not None:
        db_grade.total_score = grade_update.total_score
    if grade_update.description is not None:
        db_grade.description = grade_update.description
    
    previous_grade = None
    if db_grade.exam_date is not None:
        previous_grade = db.query(StudentGrade).filter(
            StudentGrade.student_id == db_grade.student_id,
            StudentGrade.course_id == db_grade.course_id,
            StudentGrade.exam_date < db_grade.exam_date,
            StudentGrade.id != grade_id
        ).order_by(desc(StudentGrade.exam_date)).first()
    
    score_change = None
    if previous_grade:
        score_change = db_grade.score - previous_grade.score
    
    db_grade.score_change = score_change
    
    db.commit()
    db.refresh(db_grade)
    
    # 重新加载学生和课程信息
    student = db.query(Student).filter(Student.id == db_grade.student_id).first()
    course = db.query(Course).filter(Course.id == db_grade.course_id).first()
    
    log_operation(db, "成绩管理", "修改", f"成绩记录 (ID: {grade_id}) 被成功更新", current_user.username)
    
    # 构建学生信息
    student_classes = []
    if student and student.classes:
        student_classes = [{"id": cls.id, "name": cls.name} for cls in student.classes]
    
    # 构建课程信息
    course_teachers = []
    if course and course.teachers:
        course_teachers = [
            {
                "id": teacher.id,
                "name": teacher.name,
                "contact_phone": teacher.contact_phone
            } 
            for teacher in course.teachers
        ]
    
    return StudentGradeSchema(
        id=db_grade.id,
        student_id=db_grade.student_id,
        course_id=db_grade.course_id,
        exam_date=db_grade.exam_date,
        grade_level=db_grade.grade_level,
        exam_stage=db_grade.exam_stage,
        score=db_grade.score,
        total_score=db_grade.total_score,
        score_change=db_grade.score_change,
        description=db_grade.description,
        student_name=student.name if student else None,
        student_school=student.school if student else None,
        student_grade_info=student.grade if student else None,
        student_contact_person=student.contact_person if student else None,
        student_contact_phone=student.contact_phone if student else None,
        student_classes=student_classes,
        student_is_active=student.is_active if student else None,
        course_name=course.name if course else None,
        course_teachers=course_teachers,
        created_at=db_grade.created_at,
        updated_at=db_grade.updated_at
    )

@router.delete("/{grade_id}")
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_grade_manager_permission(db, current_user)

    db_grade = db.query(StudentGrade).filter(StudentGrade.id == grade_id).first()
    if not db_grade:
        log_operation(db, "成绩管理", "删除成绩失败", f"成绩记录ID {grade_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="成绩记录不存在")
    
    db.delete(db_grade)
    db.commit()
    
    log_operation(db, "成绩管理", "删除",  f"成绩记录 (ID: {grade_id}) 被成功删除", current_user.username)
    
    return {"message": "删除成功"}