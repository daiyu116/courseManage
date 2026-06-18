# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from typing import List, Optional
from database import get_db
from models import (
    CourseEvaluationTemplate, StudentComprehensiveEvaluation,
    StudentSubjectEvaluation, Student, Course, Teacher, Settings
)
from schemas import (
    CourseEvaluationTemplateCreate, CourseEvaluationTemplateUpdate,
    CourseEvaluationTemplate as CourseEvaluationTemplateSchema,
    StudentComprehensiveEvaluationCreate, StudentComprehensiveEvaluationUpdate,
    StudentComprehensiveEvaluation as StudentComprehensiveEvaluationSchema,
    StudentSubjectEvaluationCreate, StudentSubjectEvaluationUpdate,
    StudentSubjectEvaluation as StudentSubjectEvaluationSchema,
    StudentEvaluationProfile,
    PaginatedComprehensiveEvaluationResponse,
    PaginatedSubjectEvaluationResponse,
    PaginatedEvaluationTemplateResponse,
)
from routers.auth import get_current_user, get_current_course_admin_user, User
from routers.license import _check_premium_feature
from utils.logger import log_operation
from datetime import datetime
import json

router = APIRouter()

SUBJECT_TYPE_PRESETS = {
    "language": {
        "name": "语言类",
        "dimensions": [
            {"name": "听力理解", "description": "听懂课堂指令、对话理解、信息提取", "weight": 1.0},
            {"name": "口语表达", "description": "朗读流利度、口头表达清晰度、课堂发言", "weight": 1.0},
            {"name": "阅读理解", "description": "文本理解、信息提取、推断分析", "weight": 1.0},
            {"name": "写作表达", "description": "结构组织、语言运用、逻辑表达", "weight": 1.0},
            {"name": "思维品质", "description": "批判性思维、逻辑推理、创造性思考", "weight": 1.0},
            {"name": "文化意识", "description": "文化理解、跨文化比较、文化认同", "weight": 1.0},
        ]
    },
    "math": {
        "name": "数学类",
        "dimensions": [
            {"name": "概念理解", "description": "数学概念、定理的理解与掌握", "weight": 1.0},
            {"name": "逻辑推理", "description": "演绎推理、归纳推理、证明能力", "weight": 1.0},
            {"name": "数学建模", "description": "问题抽象、模型构建、实际应用", "weight": 1.0},
            {"name": "运算能力", "description": "计算准确度、运算速度、技巧运用", "weight": 1.0},
            {"name": "数据分析", "description": "数据处理、图表解读、统计推断", "weight": 1.0},
            {"name": "直观想象", "description": "几何直观、空间想象、图形理解", "weight": 1.0},
        ]
    },
    "science": {
        "name": "理科类",
        "dimensions": [
            {"name": "概念理解", "description": "核心概念、原理的理解与掌握", "weight": 1.0},
            {"name": "实验探究", "description": "实验操作、观察能力、数据分析", "weight": 1.0},
            {"name": "逻辑推理", "description": "因果分析、假设验证、推理能力", "weight": 1.0},
            {"name": "应用能力", "description": "知识迁移、实际问题解决", "weight": 1.0},
            {"name": "科学态度", "description": "严谨求实、质疑精神、安全意识", "weight": 1.0},
        ]
    },
    "humanities": {
        "name": "文科类",
        "dimensions": [
            {"name": "知识理解", "description": "核心知识点的理解与记忆", "weight": 1.0},
            {"name": "分析论证", "description": "论据支撑、逻辑论证、多角度分析", "weight": 1.0},
            {"name": "综合表达", "description": "书面表达、观点阐述、材料组织", "weight": 1.0},
            {"name": "实践应用", "description": "联系实际、社会观察、学以致用", "weight": 1.0},
        ]
    },
    "art": {
        "name": "艺术类",
        "dimensions": [
            {"name": "审美感知", "description": "艺术感知、审美判断、鉴赏能力", "weight": 1.0},
            {"name": "技能表现", "description": "演唱/演奏/绘画等技能水平", "weight": 1.0},
            {"name": "创意实践", "description": "创作能力、想象力、个性表达", "weight": 1.0},
            {"name": "文化理解", "description": "艺术文化背景理解、风格辨识", "weight": 1.0},
        ]
    },
    "sports": {
        "name": "体育类",
        "dimensions": [
            {"name": "运动技能", "description": "动作规范、技术掌握、运动表现", "weight": 1.0},
            {"name": "健康行为", "description": "锻炼习惯、健康意识、自我保护", "weight": 1.0},
            {"name": "体育品德", "description": "规则意识、团队合作、意志品质", "weight": 1.0},
        ]
    },
}


def _check_evaluation_permission(db: Session, current_user: User):
    if not _check_premium_feature('student_evaluation', db):
        raise HTTPException(status_code=403, detail="学员评价管理功能需要购买授权后才能使用")
    if current_user.role in ['super_admin', 'system_admin']:
        return True
    if current_user.teacher_id:
        settings = db.query(Settings).first()
        if settings and settings.evaluation_managers:
            try:
                evaluation_managers = json.loads(settings.evaluation_managers)
                if current_user.teacher_id in evaluation_managers:
                    return True
            except:
                pass
    raise HTTPException(status_code=403, detail="权限不足，需要管理员或评价管理导师权限")


# ==================== 评价模板 ====================

@router.get("/presets")
def get_subject_type_presets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_evaluation_permission(db, current_user)
    return SUBJECT_TYPE_PRESETS


@router.get("/templates", response_model=PaginatedEvaluationTemplateResponse)
def get_evaluation_templates(
    skip: int = 0,
    limit: int = 100,
    course_id: Optional[int] = None,
    subject_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_evaluation_permission(db, current_user)
    query = db.query(CourseEvaluationTemplate).options(
        joinedload(CourseEvaluationTemplate.course)
    )
    if course_id is not None:
        query = query.filter(CourseEvaluationTemplate.course_id == course_id)
    if subject_type:
        query = query.filter(CourseEvaluationTemplate.subject_type == subject_type)
    if search:
        query = query.filter(CourseEvaluationTemplate.template_name.ilike(f'%{search}%'))

    total = query.count()
    templates = query.order_by(desc(CourseEvaluationTemplate.id)).offset(skip).limit(limit).all()

    result = []
    for t in templates:
        result.append(CourseEvaluationTemplateSchema(
            id=t.id,
            course_id=t.course_id,
            template_name=t.template_name,
            subject_type=t.subject_type,
            dimensions=t.dimensions if t.dimensions else [],
            is_active=t.is_active,
            course_name=t.course.name if t.course else None,
            created_at=t.created_at,
            updated_at=t.updated_at,
        ))
    return {"items": result, "total": total}


@router.get("/templates/{template_id}", response_model=CourseEvaluationTemplateSchema)
def get_evaluation_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_evaluation_permission(db, current_user)
    t = db.query(CourseEvaluationTemplate).options(
        joinedload(CourseEvaluationTemplate.course)
    ).filter(CourseEvaluationTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="评价模板不存在")
    return CourseEvaluationTemplateSchema(
        id=t.id,
        course_id=t.course_id,
        template_name=t.template_name,
        subject_type=t.subject_type,
        dimensions=t.dimensions if t.dimensions else [],
        is_active=t.is_active,
        course_name=t.course.name if t.course else None,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.post("/templates", response_model=CourseEvaluationTemplateSchema)
def create_evaluation_template(
    data: CourseEvaluationTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    dims = [d.dict() for d in data.dimensions]
    t = CourseEvaluationTemplate(
        course_id=data.course_id,
        template_name=data.template_name,
        subject_type=data.subject_type,
        dimensions=dims,
        is_active=data.is_active,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    log_operation(db, "学员评价管理", "新增模板", f"模板: {t.template_name}", current_user.username)
    course_name = None
    if t.course_id:
        course = db.query(Course).filter(Course.id == t.course_id).first()
        course_name = course.name if course else None
    return CourseEvaluationTemplateSchema(
        id=t.id,
        course_id=t.course_id,
        template_name=t.template_name,
        subject_type=t.subject_type,
        dimensions=t.dimensions,
        is_active=t.is_active,
        course_name=course_name,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.put("/templates/{template_id}", response_model=CourseEvaluationTemplateSchema)
def update_evaluation_template(
    template_id: int,
    data: CourseEvaluationTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    t = db.query(CourseEvaluationTemplate).filter(CourseEvaluationTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="评价模板不存在")
    if data.template_name is not None:
        t.template_name = data.template_name
    if data.subject_type is not None:
        t.subject_type = data.subject_type
    if data.dimensions is not None:
        t.dimensions = [d.dict() for d in data.dimensions]
    if data.is_active is not None:
        t.is_active = data.is_active
    db.commit()
    db.refresh(t)
    log_operation(db, "学员评价管理", "修改模板", f"模板: {t.template_name}", current_user.username)
    course_name = None
    if t.course_id:
        course = db.query(Course).filter(Course.id == t.course_id).first()
        course_name = course.name if course else None
    return CourseEvaluationTemplateSchema(
        id=t.id,
        course_id=t.course_id,
        template_name=t.template_name,
        subject_type=t.subject_type,
        dimensions=t.dimensions,
        is_active=t.is_active,
        course_name=course_name,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.delete("/templates/{template_id}")
def delete_evaluation_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    t = db.query(CourseEvaluationTemplate).filter(CourseEvaluationTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="评价模板不存在")
    if t.evaluations:
        raise HTTPException(status_code=400, detail="该模板已有评价记录，无法删除")
    db.delete(t)
    db.commit()
    log_operation(db, "学员评价管理", "删除模板", f"模板: {t.template_name}", current_user.username)
    return {"message": "删除成功"}


# ==================== 综合能力评价 ====================

@router.get("/comprehensive", response_model=PaginatedComprehensiveEvaluationResponse)
def get_comprehensive_evaluations(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    profile_type: Optional[str] = None,
    eval_period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_evaluation_permission(db, current_user)
    query = db.query(StudentComprehensiveEvaluation).options(
        joinedload(StudentComprehensiveEvaluation.student),
        joinedload(StudentComprehensiveEvaluation.evaluator),
    )
    if student_id is not None:
        query = query.filter(StudentComprehensiveEvaluation.student_id == student_id)
    if profile_type:
        query = query.filter(StudentComprehensiveEvaluation.profile_type == profile_type)
    if eval_period:
        query = query.filter(StudentComprehensiveEvaluation.eval_period == eval_period)

    total = query.count()
    evals = query.order_by(desc(StudentComprehensiveEvaluation.eval_date).nullslast()).offset(skip).limit(limit).all()

    result = []
    for e in evals:
        result.append(StudentComprehensiveEvaluationSchema(
            id=e.id,
            student_id=e.student_id,
            eval_period=e.eval_period,
            profile_type=e.profile_type,
            attitude_score=e.attitude_score,
            knowledge_score=e.knowledge_score,
            practice_score=e.practice_score,
            innovation_score=e.innovation_score,
            collaboration_score=e.collaboration_score,
            overall_comment=e.overall_comment,
            evaluator_id=e.evaluator_id,
            eval_date=e.eval_date,
            student_name=e.student.name if e.student else None,
            evaluator_name=e.evaluator.name if e.evaluator else None,
            created_at=e.created_at,
            updated_at=e.updated_at,
        ))
    return {"items": result, "total": total}


@router.post("/comprehensive", response_model=StudentComprehensiveEvaluationSchema)
def create_comprehensive_evaluation(
    data: StudentComprehensiveEvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")
    e = StudentComprehensiveEvaluation(
        student_id=data.student_id,
        eval_period=data.eval_period,
        profile_type=data.profile_type,
        attitude_score=data.attitude_score,
        knowledge_score=data.knowledge_score,
        practice_score=data.practice_score,
        innovation_score=data.innovation_score,
        collaboration_score=data.collaboration_score,
        overall_comment=data.overall_comment,
        evaluator_id=data.evaluator_id,
        eval_date=data.eval_date or datetime.now(),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    evaluator_name = None
    if e.evaluator_id:
        teacher = db.query(Teacher).filter(Teacher.id == e.evaluator_id).first()
        evaluator_name = teacher.name if teacher else None
    log_operation(db, "学员评价管理", "新增综合评价", f"学员: {student.name}, 周期: {data.eval_period}", current_user.username)
    return StudentComprehensiveEvaluationSchema(
        id=e.id,
        student_id=e.student_id,
        eval_period=e.eval_period,
        profile_type=e.profile_type,
        attitude_score=e.attitude_score,
        knowledge_score=e.knowledge_score,
        practice_score=e.practice_score,
        innovation_score=e.innovation_score,
        collaboration_score=e.collaboration_score,
        overall_comment=e.overall_comment,
        evaluator_id=e.evaluator_id,
        eval_date=e.eval_date,
        student_name=student.name,
        evaluator_name=evaluator_name,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.put("/comprehensive/{eval_id}", response_model=StudentComprehensiveEvaluationSchema)
def update_comprehensive_evaluation(
    eval_id: int,
    data: StudentComprehensiveEvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    e = db.query(StudentComprehensiveEvaluation).filter(StudentComprehensiveEvaluation.id == eval_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="评价记录不存在")
    for field in ['eval_period', 'profile_type', 'attitude_score', 'knowledge_score',
                   'practice_score', 'innovation_score', 'collaboration_score',
                   'overall_comment', 'evaluator_id', 'eval_date']:
        val = getattr(data, field, None)
        if val is not None:
            setattr(e, field, val)
    db.commit()
    db.refresh(e)
    log_operation(db, "学员评价管理", "修改综合评价", f"评价ID: {eval_id}", current_user.username)
    evaluator_name = None
    if e.evaluator_id:
        teacher = db.query(Teacher).filter(Teacher.id == e.evaluator_id).first()
        evaluator_name = teacher.name if teacher else None
    return StudentComprehensiveEvaluationSchema(
        id=e.id,
        student_id=e.student_id,
        eval_period=e.eval_period,
        profile_type=e.profile_type,
        attitude_score=e.attitude_score,
        knowledge_score=e.knowledge_score,
        practice_score=e.practice_score,
        innovation_score=e.innovation_score,
        collaboration_score=e.collaboration_score,
        overall_comment=e.overall_comment,
        evaluator_id=e.evaluator_id,
        eval_date=e.eval_date,
        student_name=e.student.name if e.student else None,
        evaluator_name=evaluator_name,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.delete("/comprehensive/{eval_id}")
def delete_comprehensive_evaluation(
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    e = db.query(StudentComprehensiveEvaluation).filter(StudentComprehensiveEvaluation.id == eval_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="评价记录不存在")
    db.delete(e)
    db.commit()
    log_operation(db, "学员评价管理", "删除综合评价", f"评价ID: {eval_id}", current_user.username)
    return {"message": "删除成功"}


# ==================== 单科能力评价 ====================

@router.get("/subject", response_model=PaginatedSubjectEvaluationResponse)
def get_subject_evaluations(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    eval_period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_evaluation_permission(db, current_user)
    query = db.query(StudentSubjectEvaluation).options(
        joinedload(StudentSubjectEvaluation.student),
        joinedload(StudentSubjectEvaluation.course),
        joinedload(StudentSubjectEvaluation.evaluator),
        joinedload(StudentSubjectEvaluation.template),
    )
    if student_id is not None:
        query = query.filter(StudentSubjectEvaluation.student_id == student_id)
    if course_id is not None:
        query = query.filter(StudentSubjectEvaluation.course_id == course_id)
    if eval_period:
        query = query.filter(StudentSubjectEvaluation.eval_period == eval_period)

    total = query.count()
    evals = query.order_by(desc(StudentSubjectEvaluation.eval_date).nullslast()).offset(skip).limit(limit).all()

    result = []
    for e in evals:
        result.append(StudentSubjectEvaluationSchema(
            id=e.id,
            student_id=e.student_id,
            course_id=e.course_id,
            template_id=e.template_id,
            eval_period=e.eval_period,
            dimension_scores=e.dimension_scores if e.dimension_scores else {},
            average_score=e.average_score,
            comment=e.comment,
            strengths=e.strengths,
            improvements=e.improvements,
            evaluator_id=e.evaluator_id,
            eval_date=e.eval_date,
            student_name=e.student.name if e.student else None,
            course_name=e.course.name if e.course else None,
            evaluator_name=e.evaluator.name if e.evaluator else None,
            template_name=e.template.template_name if e.template else None,
            created_at=e.created_at,
            updated_at=e.updated_at,
        ))
    return {"items": result, "total": total}


@router.post("/subject", response_model=StudentSubjectEvaluationSchema)
def create_subject_evaluation(
    data: StudentSubjectEvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")
    course = db.query(Course).filter(Course.id == data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="科目不存在")
    if data.template_id:
        template = db.query(CourseEvaluationTemplate).filter(CourseEvaluationTemplate.id == data.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="评价模板不存在")

    scores = data.dimension_scores
    avg_score = round(sum(scores.values()) / len(scores), 2) if scores else None

    e = StudentSubjectEvaluation(
        student_id=data.student_id,
        course_id=data.course_id,
        template_id=data.template_id,
        eval_period=data.eval_period,
        dimension_scores=scores,
        average_score=avg_score,
        comment=data.comment,
        strengths=data.strengths,
        improvements=data.improvements,
        evaluator_id=data.evaluator_id,
        eval_date=data.eval_date or datetime.now(),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    evaluator_name = None
    if e.evaluator_id:
        teacher = db.query(Teacher).filter(Teacher.id == e.evaluator_id).first()
        evaluator_name = teacher.name if teacher else None
    template_name = None
    if e.template_id:
        t = db.query(CourseEvaluationTemplate).filter(CourseEvaluationTemplate.id == e.template_id).first()
        template_name = t.template_name if t else None
    log_operation(db, "学员评价管理", "新增单科评价", f"学员: {student.name}, 科目: {course.name}", current_user.username)
    return StudentSubjectEvaluationSchema(
        id=e.id,
        student_id=e.student_id,
        course_id=e.course_id,
        template_id=e.template_id,
        eval_period=e.eval_period,
        dimension_scores=e.dimension_scores,
        average_score=e.average_score,
        comment=e.comment,
        strengths=e.strengths,
        improvements=e.improvements,
        evaluator_id=e.evaluator_id,
        eval_date=e.eval_date,
        student_name=student.name,
        course_name=course.name,
        evaluator_name=evaluator_name,
        template_name=template_name,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.put("/subject/{eval_id}", response_model=StudentSubjectEvaluationSchema)
def update_subject_evaluation(
    eval_id: int,
    data: StudentSubjectEvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    e = db.query(StudentSubjectEvaluation).filter(StudentSubjectEvaluation.id == eval_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="评价记录不存在")
    if data.eval_period is not None:
        e.eval_period = data.eval_period
    if data.template_id is not None:
        e.template_id = data.template_id
    if data.dimension_scores is not None:
        e.dimension_scores = data.dimension_scores
        scores = data.dimension_scores
        e.average_score = round(sum(scores.values()) / len(scores), 2) if scores else None
    if data.comment is not None:
        e.comment = data.comment
    if data.strengths is not None:
        e.strengths = data.strengths
    if data.improvements is not None:
        e.improvements = data.improvements
    if data.evaluator_id is not None:
        e.evaluator_id = data.evaluator_id
    if data.eval_date is not None:
        e.eval_date = data.eval_date
    db.commit()
    db.refresh(e)
    log_operation(db, "学员评价管理", "修改单科评价", f"评价ID: {eval_id}", current_user.username)
    evaluator_name = None
    if e.evaluator_id:
        teacher = db.query(Teacher).filter(Teacher.id == e.evaluator_id).first()
        evaluator_name = teacher.name if teacher else None
    template_name = None
    if e.template_id:
        t = db.query(CourseEvaluationTemplate).filter(CourseEvaluationTemplate.id == e.template_id).first()
        template_name = t.template_name if t else None
    return StudentSubjectEvaluationSchema(
        id=e.id,
        student_id=e.student_id,
        course_id=e.course_id,
        template_id=e.template_id,
        eval_period=e.eval_period,
        dimension_scores=e.dimension_scores,
        average_score=e.average_score,
        comment=e.comment,
        strengths=e.strengths,
        improvements=e.improvements,
        evaluator_id=e.evaluator_id,
        eval_date=e.eval_date,
        student_name=e.student.name if e.student else None,
        course_name=e.course.name if e.course else None,
        evaluator_name=evaluator_name,
        template_name=template_name,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.delete("/subject/{eval_id}")
def delete_subject_evaluation(
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_course_admin_user),
):
    _check_evaluation_permission(db, current_user)
    e = db.query(StudentSubjectEvaluation).filter(StudentSubjectEvaluation.id == eval_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="评价记录不存在")
    db.delete(e)
    db.commit()
    log_operation(db, "学员评价管理", "删除单科评价", f"评价ID: {eval_id}", current_user.username)
    return {"message": "删除成功"}


# ==================== 学员画像 ====================

@router.get("/student/{student_id}/profile", response_model=StudentEvaluationProfile)
def get_student_evaluation_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_evaluation_permission(db, current_user)
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    comp_evals = db.query(StudentComprehensiveEvaluation).options(
        joinedload(StudentComprehensiveEvaluation.evaluator),
    ).filter(
        StudentComprehensiveEvaluation.student_id == student_id
    ).order_by(desc(StudentComprehensiveEvaluation.eval_date).nullslast()).all()

    comp_result = []
    for e in comp_evals:
        comp_result.append(StudentComprehensiveEvaluationSchema(
            id=e.id,
            student_id=e.student_id,
            eval_period=e.eval_period,
            profile_type=e.profile_type,
            attitude_score=e.attitude_score,
            knowledge_score=e.knowledge_score,
            practice_score=e.practice_score,
            innovation_score=e.innovation_score,
            collaboration_score=e.collaboration_score,
            overall_comment=e.overall_comment,
            evaluator_id=e.evaluator_id,
            eval_date=e.eval_date,
            student_name=student.name,
            evaluator_name=e.evaluator.name if e.evaluator else None,
            created_at=e.created_at,
            updated_at=e.updated_at,
        ))

    subj_evals = db.query(StudentSubjectEvaluation).options(
        joinedload(StudentSubjectEvaluation.course),
        joinedload(StudentSubjectEvaluation.evaluator),
        joinedload(StudentSubjectEvaluation.template),
    ).filter(
        StudentSubjectEvaluation.student_id == student_id
    ).order_by(desc(StudentSubjectEvaluation.eval_date).nullslast()).all()

    subj_result = []
    for e in subj_evals:
        subj_result.append(StudentSubjectEvaluationSchema(
            id=e.id,
            student_id=e.student_id,
            course_id=e.course_id,
            template_id=e.template_id,
            eval_period=e.eval_period,
            dimension_scores=e.dimension_scores if e.dimension_scores else {},
            average_score=e.average_score,
            comment=e.comment,
            strengths=e.strengths,
            improvements=e.improvements,
            evaluator_id=e.evaluator_id,
            eval_date=e.eval_date,
            student_name=student.name,
            course_name=e.course.name if e.course else None,
            evaluator_name=e.evaluator.name if e.evaluator else None,
            template_name=e.template.template_name if e.template else None,
            created_at=e.created_at,
            updated_at=e.updated_at,
        ))

    return StudentEvaluationProfile(
        student_id=student_id,
        student_name=student.name,
        comprehensive_evaluations=comp_result,
        subject_evaluations=subj_result,
    )