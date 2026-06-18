# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
"""
数据库迁移：添加学员评价管理相关表
- course_evaluation_templates: 科目评价模板表
- student_comprehensive_evaluations: 学员综合能力评价表
- student_subject_evaluations: 学员单科能力评价表
"""
from sqlalchemy import inspect, text
from database import engine, SessionLocal
from models import Base, CourseEvaluationTemplate, Course
import json


def _add_evaluation_managers_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('settings')]
    if 'evaluation_managers' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE settings ADD COLUMN evaluation_managers TEXT DEFAULT '[]'"))
            conn.commit()
        print("已添加 evaluation_managers 字段到 settings 表")
    else:
        print("evaluation_managers 字段已存在，跳过")


def migrate_evaluation_managers():
    print("开始迁移：添加学员评价管理相关表...")
    _add_evaluation_managers_column()
    Base.metadata.create_all(bind=engine)
    print("表结构创建完成")

    db = SessionLocal()
    try:
        existing = db.query(CourseEvaluationTemplate).first()
        if existing:
            print("评价模板已存在，跳过初始化")
            return

        courses = db.query(Course).all()
        course_name_map = {}
        for c in courses:
            name_lower = c.name.lower()
            if any(k in name_lower for k in ['语文', '英语', '日语', '法语', '德语', '韩语', '语言']):
                course_name_map[c.id] = 'language'
            elif any(k in name_lower for k in ['数学']):
                course_name_map[c.id] = 'math'
            elif any(k in name_lower for k in ['物理', '化学', '生物']):
                course_name_map[c.id] = 'science'
            elif any(k in name_lower for k in ['历史', '地理', '政治']):
                course_name_map[c.id] = 'humanities'
            elif any(k in name_lower for k in ['音乐', '美术', '书法', '绘画', '舞蹈', '戏剧']):
                course_name_map[c.id] = 'art'
            elif any(k in name_lower for k in ['体育', '运动']):
                course_name_map[c.id] = 'sports'

        for course_id, subject_type in course_name_map.items():
            presets = {
                "language": {
                    "name": f"语言类评价模板",
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
                    "name": f"数学类评价模板",
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
                    "name": f"理科类评价模板",
                    "dimensions": [
                        {"name": "概念理解", "description": "核心概念、原理的理解与掌握", "weight": 1.0},
                        {"name": "实验探究", "description": "实验操作、观察能力、数据分析", "weight": 1.0},
                        {"name": "逻辑推理", "description": "因果分析、假设验证、推理能力", "weight": 1.0},
                        {"name": "应用能力", "description": "知识迁移、实际问题解决", "weight": 1.0},
                        {"name": "科学态度", "description": "严谨求实、质疑精神、安全意识", "weight": 1.0},
                    ]
                },
                "humanities": {
                    "name": f"文科类评价模板",
                    "dimensions": [
                        {"name": "知识理解", "description": "核心知识点的理解与记忆", "weight": 1.0},
                        {"name": "分析论证", "description": "论据支撑、逻辑论证、多角度分析", "weight": 1.0},
                        {"name": "综合表达", "description": "书面表达、观点阐述、材料组织", "weight": 1.0},
                        {"name": "实践应用", "description": "联系实际、社会观察、学以致用", "weight": 1.0},
                    ]
                },
                "art": {
                    "name": f"艺术类评价模板",
                    "dimensions": [
                        {"name": "审美感知", "description": "艺术感知、审美判断、鉴赏能力", "weight": 1.0},
                        {"name": "技能表现", "description": "演唱/演奏/绘画等技能水平", "weight": 1.0},
                        {"name": "创意实践", "description": "创作能力、想象力、个性表达", "weight": 1.0},
                        {"name": "文化理解", "description": "艺术文化背景理解、风格辨识", "weight": 1.0},
                    ]
                },
                "sports": {
                    "name": f"体育类评价模板",
                    "dimensions": [
                        {"name": "运动技能", "description": "动作规范、技术掌握、运动表现", "weight": 1.0},
                        {"name": "健康行为", "description": "锻炼习惯、健康意识、自我保护", "weight": 1.0},
                        {"name": "体育品德", "description": "规则意识、团队合作、意志品质", "weight": 1.0},
                    ]
                },
            }
            preset = presets.get(subject_type)
            if preset:
                course = db.query(Course).filter(Course.id == course_id).first()
                template = CourseEvaluationTemplate(
                    course_id=course_id,
                    template_name=f"{course.name}评价模板" if course else preset["name"],
                    subject_type=subject_type,
                    dimensions=preset["dimensions"],
                )
                db.add(template)

        db.commit()
        print(f"已为 {len(course_name_map)} 个科目自动创建评价模板")
    except Exception as e:
        print(f"迁移出错: {e}")
        db.rollback()
    finally:
        db.close()

    print("学员评价管理迁移完成")


if __name__ == "__main__":
    migrate_evaluation_managers()