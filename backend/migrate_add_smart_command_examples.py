# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
迁移脚本 - 添加智能指令示例数据（完整版）
此脚本在部署系统时自动执行，确保数据库中包含所有智能指令示例
包含完整的 expected_fields 数据用于测试和验证
"""
from database import SessionLocal
from sqlalchemy import text
import json


def add_smart_command_examples():
    """添加智能指令示例到数据库"""
    db = SessionLocal()
    
    try:
        # 第一步：检查并修改 expected_fields 字段类型为 JSONB（如果当前是 TEXT）
        print("检查 expected_fields 字段类型...")
        field_type = db.execute(text("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'smart_command_examples' 
            AND column_name = 'expected_fields'
        """)).scalar()
        
        if field_type == 'text':
            print("将 expected_fields 字段从 TEXT 转换为 JSONB...")
            db.execute(text("""
                ALTER TABLE smart_command_examples 
                ALTER COLUMN expected_fields TYPE JSONB 
                USING expected_fields::jsonb
            """))
            db.commit()
            print("✓ 字段类型转换成功")
        else:
            print(f"✓ expected_fields 字段类型已是 {field_type}")
        
        # 第二步：检查并添加唯一约束
        print("检查唯一约束...")
        constraint_exists = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE table_name = 'smart_command_examples' 
            AND constraint_name = 'uk_example_text_action_name'
            AND constraint_type = 'UNIQUE'
        """)).scalar()
        
        if not constraint_exists:
            print("添加唯一约束 uk_example_text_action_name...")
            db.execute(text("""
                ALTER TABLE smart_command_examples 
                ADD CONSTRAINT uk_example_text_action_name 
                UNIQUE (example_text, action_name)
            """))
            db.commit()
            print("✓ 唯一约束添加成功")
        else:
            print("✓ 唯一约束已存在")
        
        # 第三步：定义所有示例数据（包含完整的 expected_fields）
        examples = [
            # ========== 基础列表查询示例 ==========
            # 学员搜索
            {
                "category": "data_search",
                "action_name": "search_students",
                "example_text": "查询所有学员",
                "expected_intent": "search_students",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/students",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "students"
                    }
                },
                "description": "查看所有学员列表",
                "is_active": True,
                "sort_order": 1
            },
            {
                "category": "data_search",
                "action_name": "search_students",
                "example_text": "查看学员列表",
                "expected_intent": "search_students",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/students",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "students"
                    }
                },
                "description": "查看学员列表",
                "is_active": True,
                "sort_order": 2
            },
            
            # 导师搜索
            {
                "category": "data_search",
                "action_name": "search_teachers",
                "example_text": "查询所有导师",
                "expected_intent": "search_teachers",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/teachers",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "teachers"
                    }
                },
                "description": "查看所有导师列表",
                "is_active": True,
                "sort_order": 5
            },
            
            # 科目搜索
            {
                "category": "data_search",
                "action_name": "search_courses",
                "example_text": "查询所有科目",
                "expected_intent": "search_courses",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/courses",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "courses"
                    }
                },
                "description": "查看所有科目列表",
                "is_active": True,
                "sort_order": 9
            },
            
            # 教室搜索
            {
                "category": "data_search",
                "action_name": "search_rooms",
                "example_text": "查询所有教室",
                "expected_intent": "search_rooms",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/rooms",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "rooms"
                    }
                },
                "description": "查看所有教室列表",
                "is_active": True,
                "sort_order": 13
            },
            
            # 班级搜索
            {
                "category": "data_search",
                "action_name": "search_classes",
                "example_text": "查询所有班级",
                "expected_intent": "search_classes",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/classes",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "classes"
                    }
                },
                "description": "查看所有班级列表",
                "is_active": True,
                "sort_order": 17
            },
            
            # 排课搜索
            {
                "category": "data_search",
                "action_name": "search_schedules",
                "example_text": "查询所有排课",
                "expected_intent": "search_schedules",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/schedules",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "schedules"
                    }
                },
                "description": "查看所有排课列表",
                "is_active": True,
                "sort_order": 21
            },
            
            # 课费搜索
            {
                "category": "data_search",
                "action_name": "search_fees",
                "example_text": "查询所有课费",
                "expected_intent": "search_fees",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/fees",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "fees"
                    }
                },
                "description": "查看所有课费记录",
                "is_active": True,
                "sort_order": 26
            },
            
            # 成绩搜索
            {
                "category": "data_search",
                "action_name": "search_grades",
                "example_text": "查询所有成绩",
                "expected_intent": "search_grades",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/grades",
                    "query": {},
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "grades"
                    }
                },
                "description": "查看所有成绩列表",
                "is_active": True,
                "sort_order": 31
            },
            
            # ========== 高级关联查询示例 ==========
            {
                "category": "data_search",
                "action_name": "advanced_search",
                "example_text": "查询学员张三的班级",
                "expected_intent": "advanced_search",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/students",
                    "query": {
                        "search": "张三",
                        "related_to": "classes"
                    },
                    "storage_data": {
                        "search_mode": True,
                        "source_entity": "student",
                        "source_name": "张三",
                        "target_entity": "classes",
                        "target_path": "/admin/classes",
                        "target_label": "班级列表"
                    }
                },
                "description": "查询指定学员所属的班级",
                "is_active": True,
                "sort_order": 100
            },
            {
                "category": "data_search",
                "action_name": "advanced_search",
                "example_text": "查询学员张三在明天的排课",
                "expected_intent": "advanced_search",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/schedules",
                    "query": {
                        "filter_by": "student",
                        "filter_value": "张三",
                        "date": "明天"
                    },
                    "storage_data": {
                        "search_mode": True,
                        "entity_type": "student",
                        "entity_name": "张三",
                        "date_filter": "明天",
                        "target_entity": "schedules"
                    }
                },
                "description": "查询指定学员在特定日期的课程安排",
                "is_active": True,
                "sort_order": 140
            },
            
            # ========== 创建类指令示例 ==========
            # 添加科目
            {
                "category": "course_management",
                "action_name": "add_course",
                "example_text": "添加科目数学，优先级5",
                "expected_intent": "add_course",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/courses",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "name": "数学",
                            "priority": 5
                        },
                        "mode": "create"
                    }
                },
                "description": "添加新科目并设置优先级",
                "is_active": True,
                "sort_order": 200
            },
            {
                "category": "course_management",
                "action_name": "add_course",
                "example_text": "新增科目英语",
                "expected_intent": "add_course",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/courses",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "name": "英语"
                        },
                        "mode": "create"
                    }
                },
                "description": "添加新科目",
                "is_active": True,
                "sort_order": 201
            },
            
            # 添加导师
            {
                "category": "teacher_management",
                "action_name": "add_teacher",
                "example_text": "添加导师张老师，电话13800138000",
                "expected_intent": "add_teacher",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/teachers",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "name": "张老师",
                            "phone": "13800138000"
                        },
                        "mode": "create"
                    }
                },
                "description": "添加新导师并设置联系电话",
                "is_active": True,
                "sort_order": 210
            },
            
            # 添加学员
            {
                "category": "student_management",
                "action_name": "add_student",
                "example_text": "添加学员李四，手机号13900139000",
                "expected_intent": "add_student",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/students",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "name": "李四",
                            "phone": "13900139000"
                        },
                        "mode": "create"
                    }
                },
                "description": "添加新学员并设置手机号",
                "is_active": True,
                "sort_order": 220
            },
            
            # 添加班级
            {
                "category": "class_management",
                "action_name": "add_class",
                "example_text": "创建班级高三一班",
                "expected_intent": "add_class",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/classes",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "name": "高三一班"
                        },
                        "mode": "create"
                    }
                },
                "description": "创建新班级",
                "is_active": True,
                "sort_order": 230
            },
            
            # 添加教室
            {
                "category": "room_management",
                "action_name": "add_room",
                "example_text": "添加教室A101，容量30人",
                "expected_intent": "add_room",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/rooms",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "name": "A101",
                            "capacity": 30
                        },
                        "mode": "create"
                    }
                },
                "description": "添加新教室并设置容量",
                "is_active": True,
                "sort_order": 240
            },
            
            # ========== 更新类指令示例 ==========
            # 更新科目
            {
                "category": "course_management",
                "action_name": "update_course",
                "example_text": "修改科目数学的优先级为8",
                "expected_intent": "update_course",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/courses",
                    "query": {
                        "search": "数学"
                    },
                    "storage_data": {
                        "form_data": {
                            "priority": 8
                        },
                        "mode": "update",
                        "search_keyword": "数学"
                    }
                },
                "description": "修改指定科目的优先级",
                "is_active": True,
                "sort_order": 300
            },
            
            # 更新导师
            {
                "category": "teacher_management",
                "action_name": "update_teacher",
                "example_text": "更新张老师的电话为13800138001",
                "expected_intent": "update_teacher",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/teachers",
                    "query": {
                        "search": "张老师"
                    },
                    "storage_data": {
                        "form_data": {
                            "phone": "13800138001"
                        },
                        "mode": "update",
                        "search_keyword": "张老师"
                    }
                },
                "description": "更新指定导师的联系电话",
                "is_active": True,
                "sort_order": 310
            },
            
            # ========== 排课类指令示例 ==========
            # 创建排课
            {
                "category": "schedule_management",
                "action_name": "create_schedule",
                "example_text": "给叶一鸣安排5月17号16:30到18:30的初一英语课",
                "expected_intent": "create_schedule",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/schedules",
                    "query": {},
                    "storage_data": {
                        "student_name": "叶一鸣",
                        "date": "2026-05-17",
                        "start_time": "16:30",
                        "end_time": "18:30",
                        "course_name": "初一英语",
                        "mode": "create"
                    }
                },
                "description": "为指定学员创建排课",
                "is_active": True,
                "sort_order": 400
            },
            {
                "category": "schedule_management",
                "action_name": "create_schedule",
                "example_text": "为张三安排明天上午9点到10点的数学课",
                "expected_intent": "create_schedule",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/schedules",
                    "query": {},
                    "storage_data": {
                        "student_name": "张三",
                        "date": "明天",
                        "start_time": "09:00",
                        "end_time": "10:00",
                        "course_name": "数学",
                        "mode": "create"
                    }
                },
                "description": "为指定学员创建排课（使用相对日期）",
                "is_active": True,
                "sort_order": 401
            },
            
            # 完成排课
            {
                "category": "schedule_management",
                "action_name": "complete_schedule",
                "example_text": "完成张三今天的数学课",
                "expected_intent": "complete_schedule",
                "expected_fields": {
                    "action": "confirm",
                    "operation": "complete_schedule",
                    "storage_data": {
                        "student_name": "张三",
                        "date": "今天",
                        "course_name": "数学"
                    }
                },
                "description": "标记指定课程为已完成",
                "is_active": True,
                "sort_order": 410
            },
            
            # 取消排课
            {
                "category": "schedule_management",
                "action_name": "cancel_schedule",
                "example_text": "取消李四明天的英语课",
                "expected_intent": "cancel_schedule",
                "expected_fields": {
                    "action": "confirm",
                    "operation": "cancel_schedule",
                    "storage_data": {
                        "student_name": "李四",
                        "date": "明天",
                        "course_name": "英语"
                    }
                },
                "description": "取消指定的课程安排",
                "is_active": True,
                "sort_order": 420
            },
            
            # 延期排课
            {
                "category": "schedule_management",
                "action_name": "postpone_schedule",
                "example_text": "将王五今天的课程推迟到后天",
                "expected_intent": "postpone_schedule",
                "expected_fields": {
                    "action": "confirm",
                    "operation": "postpone_schedule",
                    "storage_data": {
                        "student_name": "王五",
                        "original_date": "今天",
                        "new_date": "后天"
                    }
                },
                "description": "延期指定的课程安排",
                "is_active": True,
                "sort_order": 430
            },
            
            # ========== 请假管理示例 ==========
            {
                "category": "leave_management",
                "action_name": "add_leave",
                "example_text": "张三从5月20日到5月22日请假，原因是生病",
                "expected_intent": "add_leave",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/leaves",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "student_name": "张三",
                            "start_date": "2026-05-20",
                            "end_date": "2026-05-22",
                            "reason": "生病"
                        },
                        "mode": "create"
                    }
                },
                "description": "为学员添加请假记录",
                "is_active": True,
                "sort_order": 500
            },
            
            # ========== 假期管理示例 ==========
            {
                "category": "holiday_management",
                "action_name": "add_holiday",
                "example_text": "添加假期国庆节，从10月1日到10月7日",
                "expected_intent": "add_holiday",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/holidays",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "name": "国庆节",
                            "start_date": "2026-10-01",
                            "end_date": "2026-10-07"
                        },
                        "mode": "create"
                    }
                },
                "description": "添加节假日设置",
                "is_active": True,
                "sort_order": 510
            },
            
            # ========== 课费管理示例 ==========
            {
                "category": "fee_management",
                "action_name": "collect_fee",
                "example_text": "收取张三学费500元",
                "expected_intent": "collect_fee",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/fees",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "student_name": "张三",
                            "amount": 500,
                            "type": "collect"
                        },
                        "mode": "create"
                    }
                },
                "description": "收取学员学费",
                "is_active": True,
                "sort_order": 520
            },
            {
                "category": "fee_management",
                "action_name": "refund_fee",
                "example_text": "退还李四学费200元",
                "expected_intent": "refund_fee",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/fees",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "student_name": "李四",
                            "amount": 200,
                            "type": "refund"
                        },
                        "mode": "create"
                    }
                },
                "description": "退还学员学费",
                "is_active": True,
                "sort_order": 521
            },
            
            # ========== 成绩管理示例 ==========
            {
                "category": "grade_management",
                "action_name": "add_grade",
                "example_text": "录入张三数学期中考试成绩95分",
                "expected_intent": "add_grade",
                "expected_fields": {
                    "action": "navigate",
                    "path": "/admin/grades",
                    "query": {},
                    "storage_data": {
                        "form_data": {
                            "student_name": "张三",
                            "course_name": "数学",
                            "score": 95,
                            "exam_type": "期中考试"
                        },
                        "mode": "create"
                    }
                },
                "description": "录入学员考试成绩",
                "is_active": True,
                "sort_order": 530
            }
        ]
        
        # 第三步：导入模型
        from models import SmartCommandExample
        
        # 第四步：插入数据（使用 ON CONFLICT 避免重复）
        inserted_count = 0
        skipped_count = 0
        updated_count = 0
        
        for example_data in examples:
            # 检查是否已存在
            existing = db.query(SmartCommandExample).filter(
                SmartCommandExample.example_text == example_data["example_text"],
                SmartCommandExample.action_name == example_data["action_name"]
            ).first()
            
            if not existing:
                new_example = SmartCommandExample(
                    category=example_data["category"],
                    action_name=example_data["action_name"],
                    example_text=example_data["example_text"],
                    expected_intent=example_data["expected_intent"],
                    expected_fields=example_data["expected_fields"],
                    description=example_data["description"],
                    is_active=example_data["is_active"],
                    sort_order=example_data["sort_order"]
                )
                db.add(new_example)
                inserted_count += 1
                print(f"  ✓ 添加示例: {example_data['example_text']}")
            else:
                # 如果已存在，更新 expected_fields
                existing.expected_fields = example_data["expected_fields"]
                existing.description = example_data["description"]
                existing.is_active = example_data["is_active"]
                existing.sort_order = example_data["sort_order"]
                updated_count += 1
                print(f"  ↻ 更新示例: {example_data['example_text']}")
        
        db.commit()
        print(f"\n迁移完成！")
        print(f"  - 新增示例: {inserted_count} 条")
        print(f"  - 更新示例: {updated_count} 条")
        print(f"  - 跳过已有: {skipped_count} 条")
        print(f"  - 总计处理: {len(examples)} 条")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("开始执行智能指令示例数据迁移...")
    print("=" * 60)
    add_smart_command_examples()
    print("=" * 60)
    print("迁移执行完毕！")
    print("=" * 60)