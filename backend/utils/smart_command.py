# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
"""
智能指令解析器 - 支持自然语言处理课程安排系统的各种操作
支持两种模式：
1. 基于规则的解析（快速、免费）
2. 基于AI大模型的解析（灵活、准确）
"""
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from models import Course, Teacher, Student, Class as ClassModel, Room, Schedule, Leave, StudentFee, FeeLog, StudentGrade, Holiday
from utils.logger import log_operation
from database import SessionLocal

class IntentParser:
    """意图解析器 - 将自然语言转换为结构化指令"""
    
    def __init__(self, use_ai: bool = False, ai_config: dict = None):
        self.use_ai = use_ai
        self.ai_config = ai_config or {}
        
    # 主解析方法
    def parse(self, text: str, db: Session, user_id: int = None) -> Optional[Dict[str, Any]]:
        """
        解析用户输入的自然语言指令
        
        Args:
            text: 用户输入的文本
            db: 数据库会话
            user_id: 当前用户ID
            
        Returns:
            包含意图类型和参数的字典
        """
        # 如果启用了AI，直接使用AI解析
        if self.use_ai and self.ai_config.get('enabled'):
            result = self._ai_based_parse(text, db)
            # 如果AI解析成功，直接返回
            if result:
                return result
        
        # 否则使用基于规则的解析
        result = self._rule_based_parse(text, db)
            
        return result
    
    def _rule_based_parse(self, text: str, db: Session) -> Optional[Dict[str, Any]]:
        """基于规则的解析"""
        # 先清理文本，去除语气词和无关词汇
        cleaned_text = self._clean_text(text)
        text_lower = cleaned_text.lower().strip()
        
        # 定义意图模式 - 按优先级排序，更具体的模式放在前面
        patterns = [
            {
                'name': 'complete_schedule',
                'patterns': [
                    r'(?:完成|完训|结束).*(?:课程|排课|安排)',
                    r'(?:课程|排课|安排).*(?:完成|完训|结束)',
                    r'(?:把|将).*(?:完成|完训|结束)',
                ],
                'handler': self._parse_complete_schedule,
                'priority': 12
            },
            {
                'name': 'cancel_schedule',
                'patterns': [
                    r'(?:取消|消除).*(?:课程|排课|安排)',
                    r'(?:课程|排课|安排).*(?:取消|消除)',
                    r'(?:把|将).*(?:取消|消除)',
                ],
                'handler': self._parse_cancel_schedule,
                'priority': 12
            },
            {
                'name': 'postpone_schedule',
                'patterns': [
                    r'(?:延期|推迟|延迟).*(?:课程|排课|安排)',
                    r'(?:课程|排课|安排).*(?:延期|推迟|延迟)',
                    r'(?:把|将).*(?:延期|推迟|延迟)',
                ],
                'handler': self._parse_postpone_schedule,
                'priority': 12
            },
            {
                'name': 'create_schedule',
                'patterns': [
                    # ========== 模式1-6: "为|给 SSS VVV DDD的..." 或 "VVV SSS DDD的..." ==========
                    # 模式1-2: 为|给 SSS VVV DDD的课程/CCC课程
                    r'(?:为|给)\s*\S+(?:\s*\S+)*\s*(?:新增|新建|创建|安排|添加|增加|增添)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后]).*(?:课程|课|排课|课程安排)',
                    
                    # 模式3-4: DDD为|给 SSS VVV课程/CCC课程
                    r'(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:为|给)\s*\S+(?:\s*\S+)*\s*(?:新增|新建|创建|安排|添加|增加|增添).*(?:课程|课|排课|课程安排)',
                    
                    # 模式5-6: VVV SSS DDD的课程/CCC课程
                    r'(?:新增|新建|创建|安排|添加|增加|增添)\s*\S+(?:\s*\S+)*\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后]).*(?:课程|课|排课|课程安排)',
                    
                    # ========== 模式7-15: 包含"在|于"的复杂语序 ==========
                    # 模式7-8: 为|给 SSS 在|于 DDD VVV...
                    r'(?:为|给)\s*\S+(?:\s*\S+)*\s*(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:新增|新建|创建|安排|添加|增加|增添).*(?:课程|课|排课|课程安排)',
                    
                    # 模式9-10: 在|于 DDD 为|给 SSS VVV...
                    r'(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:为|给)\s*\S+(?:\s*\S+)*\s*(?:新增|新建|创建|安排|添加|增加|增添).*(?:课程|课|排课|课程安排)',
                    
                    # 模式11-12: 为|给 SSS VVV 在|于 DDD...
                    r'(?:为|给)\s*\S+(?:\s*\S+)*\s*(?:新增|新建|创建|安排|添加|增加|增添)\s*(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后]).*(?:课程|课|排课|课程安排)',
                    
                    # 模式13: 为|给 SSS VVV TTT 在|于 DDD...
                    r'(?:为|给)\s*\S+(?:\s*\S+)*\s*(?:新增|新建|创建|安排|添加|增加|增添)\s*\S+\s*(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后]).*(?:课程|课|排课|课程安排)',
                    
                    # 模式14-15: VVV 为|给 SSS 在|于 DDD...
                    r'(?:新增|新建|创建|安排|添加|增加|增添)\s*(?:为|给)\s*\S+(?:\s*\S+)*\s*(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后]).*(?:课程|课|排课|课程安排)',
                    
                    # 模式16-19: "将|把"句式
                    # 模式16: 在|于DDD 将|把TTT的CCC课程 VVV给SSS
                    r'(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:将|把)\s*.+?(?:新增|新建|创建|安排|添加|增加|增添)\s*给\s*\S+',
                    
                    # 模式17: 在|于DDD 将|把CCC课程 VVV给SSS，导师是TTT
                    r'(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:将|把).+?(?:新增|新建|创建|安排|添加|增加|增添)\s*给\s*\S+',
                    
                    # 模式18: 将|把TTT的CCC课程 在|于DDD VVV给SSS
                    r'(?:将|把)\s*.+?(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:新增|新建|创建|安排|添加|增加|增添)\s*给\s*\S+',
                    
                    # 模式19: 将|把CCC课程 在|于DDD VVV给SSS，导师是TTT
                    r'(?:将|把).+?(?:在|于)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:新增|新建|创建|安排|添加|增加|增添)\s*给\s*\S+',
                    
                    # 模式20-21: "SSS DDD VVV..." 和 "SSS VVV DDD..." 句式
                    # 模式20: SSS DDD VVV TTT的CCC的课程安排 或 SSS DDD VVV CCC的课程安排，导师是TTT
                    r'\S+(?:\s*\S+)*\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后])\s*(?:新增|新建|创建|安排|添加|增加|增添).*(?:课程|课|排课|课程安排)',
                    
                    # 模式21: SSS VVV DDD TTT的CCC的课程安排 或 SSS VVV DDD CCC的课程安排，导师是TTT
                    r'\S+(?:\s*\S+)*\s*(?:新增|新建|创建|安排|添加|增加|增添)\s*(?:\d{4}-\d{2}-\d{2}|今天|明天|后天|大后天|\d+[天后]).*(?:课程|课|排课|课程安排)',
                    
                    # ========== 通用兜底匹配 ==========
                    # 包含动作词和课程词的任意组合
                    r'.*(?:新增|新建|创建|安排|添加|增加|增添).*(?:课程|课|排课|课程安排).*',
                    r'.*(?:课程|课|排课|课程安排).*(?:新增|新建|创建|安排|添加|增加|增添).*'
                ],
                'handler': self._parse_create_schedule,
                'priority': 10
            },
            {
                'name': 'add_student',
                'patterns': [
                    r'(?:增加|添加|新增|创建|新建|增添)(?:一个|一位)?(?:学员|学生)\s*[:：]?\s*(.+)',
                    r'(?:学员|学生)\s*[:：]?\s*(.+?)(?:增加|添加|新增|创建|新建|增添)'
                ],
                'handler': self._parse_add_student,
                'priority': 8
            },
            {
                'name': 'update_student',
                'patterns': [
                    r'(?:修改|更新|编辑|改变)(?:学员|学生)\s*[:：]?\s*(.+)',
                ],
                'handler': self._parse_update_student,
                'priority': 8
            },
            {
                'name': 'add_class',
                'patterns': [
                    r'(?:增加|添加|新增|创建|新建|增添)(?:一个)?(?:班级)\s*[:：]?\s*(.+)',
                    r'(?:班级)\s*[:：]?\s*(.+?)(?:添加|新增|创建)'
                ],
                'handler': self._parse_add_class,
                'priority': 8
            },
            {
                'name': 'update_class',
                'patterns': [
                    r'(?:修改|更新|编辑|改变)(?:班级)\s*[:：]?\s*(.+)',
                ],
                'handler': self._parse_update_class,
                'priority': 8
            },
            {
                'name': 'add_leave',
                'patterns': [
                    r'(?:为|给)\s*(.+?)\s*(?:请假|请个假)',
                    r'(.+?)\s*(?:请假|请个假)',
                ],
                'handler': self._parse_add_leave,
                'priority': 5
            },
            {
                'name': 'add_holiday',
                'patterns': [
                    r'(?:增加|添加|新增|创建|新建|增添|设置)(?:节假日|假日|假期)\s*[:：]?\s*(.+)',
                ],
                'handler': self._parse_add_holiday,
                'priority': 8
            },
            {
                'name': 'collect_fee',
                'patterns': [
                    r'(?:收取|缴费|收费)\s*(.+?)\s*(?:科目|课程)\s*(.+?)\s*(?:费用|学费)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?(?:，|,)?(?:应收\s*(\d+(?:\.\d+)?)\s*(?:元)?)?(?:，|,)?(?:日期\s*(\d{4}-\d{2}-\d{2}))?',
                    r'(?:追加|追缴|收取|缴费)\s*(.+?)\s*(?:费用|学费)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?(?:，|,)?(?:科目\s*(.+?))?(?:，|,)?(?:应收\s*(\d+(?:\.\d+)?)\s*(?:元)?)?(?:，|,)?(?:日期\s*(\d{4}-\d{2}-\d{2}))?'
                ],
                'handler': self._parse_collect_fee,
                'priority': 8
            },
            {
                'name': 'refund_fee',
                'patterns': [
                    r'(?:退费|退款|退回)\s*(.+?)\s*(?:科目|课程)\s*(.+?)\s*(?:费用|学费)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?(?:，|,)?(?:日期\s*(\d{4}-\d{2}-\d{2}))?',
                ],
                'handler': self._parse_refund_fee,
                'priority': 8
            },
            {
                'name': 'add_grade',
                'patterns': [
                    r'(?:增加|添加|新增|创建|新建|增添|录入|记录)(?:成绩|分数)\s*[:：]?\s*(.+)',
                ],
                'handler': self._parse_add_grade,
                'priority': 8
            },
            {
                'name': 'add_course',
                'patterns': [
                    r'(?:增加|添加|新增|创建|新建|增添)(?:一个)?(?:科目|课程)\s*[:：]?\s*(.+)',
                    r'(?:科目|课程)\s*[:：]?\s*(.+?)(?:添加|新增|创建)'
                ],
                'handler': self._parse_add_course,
                'priority': 8
            },
            {
                'name': 'update_course',
                'patterns': [
                    r'(?:修改|更新|编辑|改变)(?:科目|课程)\s*[:：]?\s*(.+)',
                ],
                'handler': self._parse_update_course,
                'priority': 8
            },
            {
                'name': 'add_teacher',
                'patterns': [
                    r'(?:增加|添加|新增|创建|新建|增添)(?:一个)?(?:导师|老师|教师)\s*[:：]?\s*(.+)',
                    r'(?:导师|老师|教师)\s*[:：]?\s*(.+?)(?:添加|新增|创建)'
                ],
                'handler': self._parse_add_teacher,
                'priority': 8
            },
            {
                'name': 'update_teacher',
                'patterns': [
                    r'(?:修改|更新|编辑|改变)(?:导师|老师|教师)\s*[:：]?\s*(.+)',
                ],
                'handler': self._parse_update_teacher,
                'priority': 8
            },
            {
                'name': 'add_room',
                'patterns': [
                    r'(?:增加|添加|新增|创建|新建|增添)(?:一个)?(?:教室|房间)\s*[:：]?\s*(.+)',
                    r'(?:教室|房间)\s*[:：]?\s*(.+?)(?:添加|新增|创建)'
                ],
                'handler': self._parse_add_room,
                'priority': 8
            },
            {
                'name': 'update_room',
                'patterns': [
                    r'(?:修改|更新|编辑|改变)(?:教室|房间)\s*[:：]?\s*(.+)',
                ],
                'handler': self._parse_update_room,
                'priority': 8
            },
            {
                'name': 'search_courses',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:科目|课程)',
                    r'(?:科目|课程)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:科目|课程)',
                    r'(?:科目|课程)列表',
                ],
                'handler': self._parse_search_courses,
                'priority': 9
            },
            {
                'name': 'search_teachers',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:导师|老师|教师)',
                    r'(?:导师|老师|教师)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:导师|老师|教师)',
                    r'(?:导师|老师|教师)列表',
                ],
                'handler': self._parse_search_teachers,
                'priority': 9
            },
            {
                'name': 'search_students',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:学员|学生)',
                    r'(?:学员|学生)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:学员|学生)',
                    r'(?:学员|学生)列表',
                ],
                'handler': self._parse_search_students,
                'priority': 9
            },
            {
                'name': 'search_classes',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:班级)',
                    r'(?:班级)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:班级)',
                    r'(?:班级)列表',
                ],
                'handler': self._parse_search_classes,
                'priority': 9
            },
            {
                'name': 'search_rooms',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:教室|房间)',
                    r'(?:教室|房间)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:教室|房间)',
                    r'(?:教室|房间)列表',
                ],
                'handler': self._parse_search_rooms,
                'priority': 9
            },
            {
                'name': 'search_schedules',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:课程安排|排课|课表)',
                    r'(?:课程安排|排课|课表)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:课程安排|排课|课表)',
                    r'(?:课程安排|排课|课表)列表',
                ],
                'handler': self._parse_search_schedules,
                'priority': 9
            },
            {
                'name': 'search_holidays',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:节假日|假日|假期)',
                    r'(?:节假日|假日|假期)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:节假日|假日|假期)',
                    r'(?:节假日|假日|假期)列表',
                ],
                'handler': self._parse_search_holidays,
                'priority': 9
            },
            {
                'name': 'search_fees',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:课费|费用|缴费|学费)',
                    r'(?:课费|费用|缴费|学费)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:课费|费用|缴费记录)',
                    r'(?:课费|费用)列表',
                ],
                'handler': self._parse_search_fees,
                'priority': 9
            },
            {
                'name': 'search_grades',
                'patterns': [
                    r'(?:查询|搜索|查找|检索)(?:成绩|分数)',
                    r'(?:成绩|分数)(?:查询|搜索|查找|检索)',
                    r'查看(?:所有)?(?:成绩|分数)',
                    r'(?:成绩|分数)列表',
                ],
                'handler': self._parse_search_grades,
                'priority': 9
            },
            {
                'name': 'advanced_search',
                'patterns': [
                    # 学员相关复杂查询
                    r'(?:查询|搜索|查找|检索)(?:学员|学生)\s*(.+?)(?:相关的|关联的|的|所属)(?:班级)',
                    r'(?:查询|搜索|查找|检索)(?:学员|学生)\s*(.+?)(?:相关的|关联的|的|所属)(?:科目|课程)',
                    r'(?:查询|搜索|查找|检索)(?:学员|学生)\s*(.+?)(?:相关的|关联的|的|所属)(?:导师|老师)',
                    r'(?:查询|搜索|查找|检索)(?:学员|学生)\s*(.+?)(?:相关的|关联的|的|所属)(?:课费|费用|缴费)',
                    r'(?:查询|搜索|查找|检索)(?:学员|学生)\s*(.+?)(?:相关的|关联的|的|所属)(?:成绩|分数)',
                    r'(?:查询|搜索|查找|检索)(?:学员|学生)\s*(.+?)(?:相关的|关联的|的|所属)(?:排课|课程安排|课表)',
                    
                    # 导师相关复杂查询
                    r'(?:查询|搜索|查找|检索)(?:导师|老师|教师)\s*(.+?)(?:相关的|关联的|的|所教)(?:科目|课程)',
                    r'(?:查询|搜索|查找|检索)(?:导师|老师|教师)\s*(.+?)(?:相关的|关联的|的|所教)(?:班级)',
                    r'(?:查询|搜索|查找|检索)(?:导师|老师|教师)\s*(.+?)(?:相关的|关联的|的|所教)(?:学员|学生)',
                    r'(?:查询|搜索|查找|检索)(?:导师|老师|教师)\s*(.+?)(?:相关的|关联的|的|所教)(?:排课|课程安排|课表)',
                    
                    # 班级相关复杂查询
                    r'(?:查询|搜索|查找|检索)(?:班级)\s*(.+?)(?:相关的|关联的|的|所属)(?:学员|学生)',
                    r'(?:查询|搜索|查找|检索)(?:班级)\s*(.+?)(?:相关的|关联的|的|所属)(?:导师|老师)',
                    r'(?:查询|搜索|查找|检索)(?:班级)\s*(.+?)(?:相关的|关联的|的|所属)(?:科目|课程)',
                    r'(?:查询|搜索|查找|检索)(?:班级)\s*(.+?)(?:相关的|关联的|的|所属)(?:排课|课程安排|课表)',
                    
                    # 科目相关复杂查询
                    r'(?:查询|搜索|查找|检索)(?:科目|课程)\s*(.+?)(?:相关的|关联的|的|所属)(?:导师|老师)',
                    r'(?:查询|搜索|查找|检索)(?:科目|课程)\s*(.+?)(?:相关的|关联的|的|所属)(?:学员|学生)',
                    r'(?:查询|搜索|查找|检索)(?:科目|课程)\s*(.+?)(?:相关的|关联的|的|所属)(?:班级)',
                    r'(?:查询|搜索|查找|检索)(?:科目|课程)\s*(.+?)(?:相关的|关联的|的|所属)(?:排课|课程安排|课表)',
                    
                    # 教室相关复杂查询
                    r'(?:查询|搜索|查找|检索)(?:教室|房间)\s*(.+?)(?:相关的|关联的|的|所属)(?:排课|课程安排|课表)',
                    
                    # 通用带条件搜索
                    r'(?:查询|搜索|查找|检索)(.+?)(?:在|于)\s*(.+?)\s*(?:相关的|关联的|的)(?:排课|课程安排|课表)',
                    r'(?:查询|搜索|查找|检索)(.+?)\s*(.+?)\s*(?:相关的|关联的|的)(?:信息|详情|资料)',
                ],
                'handler': self._parse_advanced_search,
                'priority': 15
            }
        ]
        
        # 尝试匹配每个模式，按优先级排序
        matched_patterns = []
        for pattern_config in patterns:
            for pattern in pattern_config['patterns']:
                match = re.search(pattern, text_lower)
                if match:
                    matched_patterns.append({
                        'config': pattern_config,
                        'match': match,
                        'priority': pattern_config.get('priority', 0)
                    })
                    break
        
        # 如果没有匹配到任何模式，返回None
        if not matched_patterns:
            return None
        
        # 按优先级排序，选择最高优先级的匹配
        matched_patterns.sort(key=lambda x: x['priority'], reverse=True)
        best_match = matched_patterns[0]
        
        try:
            # 使用清理后的文本进行handler处理，但保留原始文本用于日志
            result = best_match['config']['handler'](best_match['match'], cleaned_text, db)
            if result:
                result['intent'] = best_match['config']['name']
                result['original_text'] = text  # 保留原始文本
                result['cleaned_text'] = cleaned_text  # 也保存清理后的文本
                return result
        except Exception as e:
            log_operation(db, "智能指令解析", "错误", f"解析指令时发生错误: {str(e)}", "SYSTEM", "DEBUG")
            
        return None
    
    def _parse_add_course(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加科目指令 - 返回导航信息"""
        course_info = self._clean_text(match.group(1).strip())
        
        # 优化：尝试多种方式提取科目名称
        name_match = re.search(r'(?:名字|姓名|叫|名为)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = re.search(r'(?:科目|课程)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = type('obj', (object,), {'group': lambda x: course_info})()
        
        course_name = self._clean_text(name_match.group(1).strip())
        
        # 提取可能的导师信息
        teacher_match = re.search(r'(?:导师|老师|教师)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        teacher_name = teacher_match.group(1).strip() if teacher_match else None
        
        # 查询导师ID（如果提供了导师名称）
        teacher_id = None
        if teacher_name and db:
            teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
            if teacher:
                teacher_id = teacher.id
        
        # 提取优先级
        priority_match = re.search(r'(?:优先级|priority)\s*(?:是|为|叫|乃)?[:：]?\s*(\d+)', text)
        priority = int(priority_match.group(1)) if priority_match else 0
        
        return {
            'action': 'navigate',
            'path': '/admin/courses',
            'query': {
                'action': 'add'
            },
            'storage_data': {
                'course_name': course_name,
                'teacher_name': teacher_name,
                'teacher_id': teacher_id,
                'priority': priority
            },
            'message': '已为您打开添加科目页面，请确认信息后提交'
        }
    
    def _parse_update_course(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析更新科目指令 - 返回导航信息"""
        course_info = self._clean_text(match.group(1).strip())
        
        # 提取科目名称或ID
        course_match = re.search(r'(?:科目|课程)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:的|，|,|$)', text)
        course_name_or_id = course_match.group(1).strip() if course_match else course_info
        
        # 尝试查找科目ID
        course_id = None
        if course_name_or_id.isdigit():
            course_id = int(course_name_or_id)
        elif db:
            course = db.query(Course).filter(Course.name == course_name_or_id).first()
            if course:
                course_id = course.id
        
        if not course_id:
            return {
                'action': 'error',
                'message': f'未找到科目"{course_name_or_id}"，请确认科目名称或ID是否正确'
            }
        
        # 提取要更新的字段
        updates = {}
        
        name_match = re.search(r'(?:名称|名字)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if name_match:
            updates['name'] = name_match.group(1).strip()
        
        priority_match = re.search(r'(?:优先级|priority)\s*(?:改为|改成|变更为)?[:：]?\s*(\d+)', text)
        if priority_match:
            updates['priority'] = int(priority_match.group(1))
        
        teacher_match = re.search(r'(?:导师|老师)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if teacher_match:
            updates['teacher_name'] = teacher_match.group(1).strip()
        
        return {
            'action': 'navigate',
            'path': '/admin/courses',
            'query': {
                'action': 'edit',
                'id': str(course_id)
            },
            'storage_data': {
                'course_id': course_id,
                'updates': updates
            },
            'message': '已为您打开科目编辑页面，请确认修改内容后提交'
        }
    
    def _parse_complete_schedule(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析完成课程指令 - 返回导航信息"""
        
        # 二次验证：确保文本中确实包含"完成/完训/结束"的意图
        # 如果文本中包含"创建"、"新增"等词，说明可能是创建排课而非完成
        #if re.search(r'(?:创建|新增|新建|添加)', text):
        #    return None
        
        #schedule_info = self._clean_text(match.group(1).strip())
        
        # 尝试提取排课ID - 支持多种格式：ID为3、ID 3、#3、id=3等
        id_match = re.search(r'(?:id|ID|#|编号)[=:：为是乃]?\s*(\d+)', text)
        schedule_id = None
        if id_match:
            schedule_id = int(id_match.group(1))
        #elif schedule_info.isdigit():
        #    schedule_id = int(schedule_info)
        
        # 如果没有提供ID，尝试通过其他信息查找
        if not schedule_id and db:
            # 提取学生姓名
            person_names = self._extract_person_names(text)
            # 提取科目
            course_match = re.search(r'(?:科目|课程)[:：]?\s*(.+?)(?:，|,|$)', text)
            course_name = course_match.group(1).strip() if course_match else None
            # 提取日期
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            schedule_date = date_match.group(1) if date_match else None
                
            # 尝试查找匹配的排课
            if person_names and course_name and schedule_date:
                student = db.query(Student).filter(Student.name == person_names[0]).first()
                course = db.query(Course).filter(Course.name == course_name).first()
                if student and course:
                    schedule = db.query(Schedule).filter(
                        Schedule.student_id == student.id,
                        Schedule.course_id == course.id,
                        Schedule.date == schedule_date
                    ).first()
                    if schedule:
                        schedule_id = schedule.id
        
        if not schedule_id:
            return {
                'action': 'error',
                'message': '无法识别要完成的课程，请提供排课ID或使用格式：完成课程ID 123，反馈：内容|作业|注意'
            }
        
        # 提取内容反馈（格式：内容|作业|注意）
        feedback_match = re.search(r'(?:反馈|内容)[:：]?\s*(.+?)(?:$)', text)
        content_feedback = feedback_match.group(1).strip() if feedback_match else None
        
        return {
            'action': 'navigate',
            'path': '/admin/schedules',
            'query': {
                'action': 'complete',
                'id': str(schedule_id)
            },
            'storage_data': {
                'schedule_id': schedule_id,
                'content_feedback': content_feedback
            },
            'message': '已为您打开课程完成确认页面，请确认信息后提交'
        }
    
    def _parse_cancel_schedule(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析取消课程指令 - 返回导航信息"""
        
        # 二次验证：确保文本中确实包含"取消"的意图
        #if re.search(r'(?:创建|新增|新建|添加)', text):
        #    return None
        
        #schedule_info = self._clean_text(match.group(1).strip())
        
        # 尝试提取排课ID - 支持多种格式：ID为3、ID 3、#3、id=3等
        id_match = re.search(r'(?:id|ID|#|编号)[=:：为是乃]?\s*(\d+)', text)
        schedule_id = None
        if id_match:
            schedule_id = int(id_match.group(1))
        #elif schedule_info.isdigit():
        #    schedule_id = int(schedule_info)
        
        # 如果没有提供ID，尝试通过其他信息查找
        if not schedule_id and db:
            person_names = self._extract_person_names(text)
            course_match = re.search(r'(?:科目|课程)[:：]?\s*(.+?)(?:，|,|$)', text)
            course_name = course_match.group(1).strip() if course_match else None
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            schedule_date = date_match.group(1) if date_match else None
            
            if person_names and course_name and schedule_date:
                student = db.query(Student).filter(Student.name == person_names[0]).first()
                course = db.query(Course).filter(Course.name == course_name).first()
                if student and course:
                    schedule = db.query(Schedule).filter(
                        Schedule.student_id == student.id,
                        Schedule.course_id == course.id,
                        Schedule.date == schedule_date
                    ).first()
                    if schedule:
                        schedule_id = schedule.id
        
        if not schedule_id:
            return {
                'action': 'error',
                'message': '无法识别要取消的课程，请提供排课ID或使用格式：取消课程ID 123，原因：学生请假'
            }
        
        # 提取取消原因
        reason_match = re.search(r'(?:原因|因为)[:：]?\s*(.+)', text)
        cancel_reason = reason_match.group(1).strip() if reason_match else None
        
        # 提取是否发送通知
        send_notification = '通知' in text or '提醒' in text
        
        return {
            'action': 'navigate',
            'path': '/admin/schedules',
            'query': {
                'action': 'cancel',
                'id': str(schedule_id)
            },
            'storage_data': {
                'schedule_id': schedule_id,
                'cancel_reason': cancel_reason,
                'send_notification': send_notification
            },
            'message': '已为您打开课程取消确认页面，请确认信息后提交'
        }
    
    def _parse_postpone_schedule(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析延期课程指令 - 返回导航信息"""
        
        # 二次验证：确保文本中确实包含"延期/推迟"的意图
        #if re.search(r'(?:创建|新增|新建|添加)', text):
        #    return None
        
        #schedule_info = self._clean_text(match.group(1).strip())
        
        # 尝试提取排课ID - 支持多种格式：ID为3、ID 3、#3、id=3等
        id_match = re.search(r'(?:id|ID|#|编号)[=:：为是乃]?\s*(\d+)', text)
        schedule_id = None
        if id_match:
            schedule_id = int(id_match.group(1))
        #elif schedule_info.isdigit():
        #    schedule_id = int(schedule_info)
        
        # 如果没有提供ID，尝试通过其他信息查找
        if not schedule_id and db:
            person_names = self._extract_person_names(text)
            course_match = re.search(r'(?:科目|课程)[:：]?\s*(.+?)(?:，|,|$)', text)
            course_name = course_match.group(1).strip() if course_match else None
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
            schedule_date = date_match.group(1) if date_match else None
            
            if person_names and course_name and schedule_date:
                student = db.query(Student).filter(Student.name == person_names[0]).first()
                course = db.query(Course).filter(Course.name == course_name).first()
                if student and course:
                    schedule = db.query(Schedule).filter(
                        Schedule.student_id == student.id,
                        Schedule.course_id == course.id,
                        Schedule.date == schedule_date
                    ).first()
                    if schedule:
                        schedule_id = schedule.id
        
        if not schedule_id:
            return {
                'action': 'error',
                'message': '无法识别要延期的课程，请提供排课ID或使用格式：延期课程ID 123，从2024-01-15到2024-01-20，原因：教师出差'
            }
        
        # 提取新的日期和时间
        start_date_match = re.search(r'(?:开始|从|改为)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        end_date_match = re.search(r'(?:结束|到|至)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        start_time_match = re.search(r'(?:开始时间|从)\s*(\d{1,2}[:：]\d{2})', text)
        end_time_match = re.search(r'(?:结束时间|到)\s*(\d{1,2}[:：]\d{2})', text)
        
        # 提取延期原因
        reason_match = re.search(r'(?:原因|因为)[:：]?\s*(.+)', text)
        postpone_reason = reason_match.group(1).strip() if reason_match else None
        
        return {
            'action': 'navigate',
            'path': '/admin/schedules',
            'query': {
                'action': 'postpone',
                'id': str(schedule_id)
            },
            'storage_data': {
                'schedule_id': schedule_id,
                'start_date': start_date_match.group(1) if start_date_match else None,
                'end_date': end_date_match.group(1) if end_date_match else None,
                'start_time': start_time_match.group(1).replace('：', ':') if start_time_match else None,
                'end_time': end_time_match.group(1).replace('：', ':') if end_time_match else None,
                'postpone_reason': postpone_reason
            },
            'message': '已为您打开课程延期确认页面，请确认信息后提交'
        }
    
    def _parse_add_teacher(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加导师指令 - 返回导航信息"""
        teacher_info = self._clean_text(match.group(1).strip())
        
        # 优化：尝试多种方式提取导师姓名
        # 1. 尝试提取"名字叫XXX"或"名为XXX"格式
        name_match = re.search(r'(?:名字|姓名|叫|名为)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            # 2. 尝试提取"导师XXX"格式
            name_match = re.search(r'(?:导师|老师|教师)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            # 3. 使用原始匹配内容
            name_match = type('obj', (object,), {'group': lambda x: teacher_info})()
        
        teacher_name = self._clean_text(name_match.group(1).strip())
        
        # 提取电话
        phone_match = re.search(r'(?:电话|手机|联系方式)[:：]?\s*(\d{11}|\d{3,4}-\d{7,8})', text)
        phone = phone_match.group(1) if phone_match else None
        
        # 提取邮箱
        email_match = re.search(r'(?:邮箱|email)[:：]?\s*([\w.-]+@[\w.-]+\.\w+)', text)
        email = email_match.group(1) if email_match else None
        
        # 提取职称
        title_match = re.search(r'(?:职称|职务)[:：]?\s*(.+?)(?:，|,|$)', text)
        title = title_match.group(1).strip() if title_match else None
        
        # 提取部门
        dept_match = re.search(r'(?:部门|系)[:：]?\s*(.+?)(?:，|,|$)', text)
        department = dept_match.group(1).strip() if dept_match else None
        
        return {
            'action': 'navigate',
            'path': '/admin/teachers',
            'query': {
                'action': 'add'
            },
            'storage_data': {
                'teacher_name': teacher_name,
                'contact_phone': phone,
                'email': email,
                'title': title,
                'department': department
            },
            'message': '已为您打开添加导师页面，请确认信息后提交'
        }
    
    def _parse_update_teacher(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析更新导师指令 - 返回导航信息"""
        teacher_info = self._clean_text(match.group(1).strip())
        
        # 提取导师名称或ID
        teacher_match = re.search(r'(?:导师|老师|教师)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:的|，|,|$)', text)
        teacher_name_or_id = teacher_match.group(1).strip() if teacher_match else teacher_info
        
        # 尝试查找导师ID
        teacher_id = None
        if teacher_name_or_id.isdigit():
            teacher_id = int(teacher_name_or_id)
        elif db:
            teacher = db.query(Teacher).filter(Teacher.name == teacher_name_or_id).first()
            if teacher:
                teacher_id = teacher.id
        
        if not teacher_id:
            return {
                'action': 'error',
                'message': f'未找到导师"{teacher_name_or_id}"，请确认导师名称或ID是否正确'
            }
        
        # 提取要更新的字段
        updates = {}
        
        name_match = re.search(r'(?:名称|名字)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if name_match:
            updates['name'] = name_match.group(1).strip()
        
        phone_match = re.search(r'(?:电话|手机)\s*(?:改为|改成|变更为)?[:：]?\s*(\d{11}|\d{3,4}-\d{7,8})', text)
        if phone_match:
            updates['contact_phone'] = phone_match.group(1)
        
        email_match = re.search(r'(?:邮箱|email)\s*(?:改为|改成|变更为)?[:：]?\s*([\w.-]+@[\w.-]+\.\w+)', text)
        if email_match:
            updates['email'] = email_match.group(1)
        
        title_match = re.search(r'(?:职称|职务)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if title_match:
            updates['title'] = title_match.group(1).strip()
        
        dept_match = re.search(r'(?:部门|系)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if dept_match:
            updates['department'] = dept_match.group(1).strip()
        
        return {
            'action': 'navigate',
            'path': '/admin/teachers',
            'query': {
                'action': 'edit',
                'id': str(teacher_id)
            },
            'storage_data': {
                'teacher_id': teacher_id,
                'updates': updates
            },
            'message': '已为您打开导师编辑页面，请确认修改内容后提交'
        }
    
    def _parse_add_student(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加学员指令 - 返回导航信息"""
        student_info = self._clean_text(match.group(1).strip())
        
        # 优化：尝试多种方式提取学员姓名
        name_match = re.search(r'(?:名字|姓名|叫|名为)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = re.search(r'(?:学员|学生)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = type('obj', (object,), {'group': lambda x: student_info})()
        
        student_name = self._clean_text(name_match.group(1).strip())
        
        # 提取电话
        phone_match = re.search(r'(?:电话|手机|联系方式)[:：]?\s*(\d{11}|\d{3,4}-\d{7,8})', text)
        phone = phone_match.group(1) if phone_match else None
        
        # 提取邮箱
        email_match = re.search(r'(?:邮箱|email)[:：]?\s*([\w.-]+@[\w.-]+\.\w+)', text)
        email = email_match.group(1) if email_match else None
        
        # 提取班级
        class_match = re.search(r'(?:班级|班)[:：]?\s*(.+?)(?:，|,|$)', text)
        class_name = class_match.group(1).strip() if class_match else None
        
        # 查询班级ID
        class_id = None
        if class_name and db:
            class_obj = db.query(ClassModel).filter(ClassModel.name == class_name).first()
            if class_obj:
                class_id = class_obj.id
        
        return {
            'action': 'navigate',
            'path': '/admin/students',
            'query': {
                'action': 'add'
            },
            'storage_data': {
                'student_name': student_name,
                'contact_phone': phone,
                'email': email,
                'class_name': class_name,
                'class_id': class_id
            },
            'message': '已为您打开添加学员页面，请确认信息后提交'
        }
    
    def _parse_update_student(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析更新学员指令 - 返回导航信息"""
        student_info = self._clean_text(match.group(1).strip())
        
        # 提取学员名称或ID
        student_match = re.search(r'(?:学员|学生)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:的|，|,|$)', text)
        student_name_or_id = student_match.group(1).strip() if student_match else student_info
        
        # 尝试查找学员ID
        student_id = None
        if student_name_or_id.isdigit():
            student_id = int(student_name_or_id)
        elif db:
            student = db.query(Student).filter(Student.name == student_name_or_id).first()
            if student:
                student_id = student.id
        
        if not student_id:
            return {
                'action': 'error',
                'message': f'未找到学员"{student_name_or_id}"，请确认学员名称或ID是否正确'
            }
        
        # 提取要更新的字段
        updates = {}
        
        name_match = re.search(r'(?:名称|名字)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if name_match:
            updates['name'] = name_match.group(1).strip()
        
        phone_match = re.search(r'(?:电话|手机)\s*(?:改为|改成|变更为)?[:：]?\s*(\d{11}|\d{3,4}-\d{7,8})', text)
        if phone_match:
            updates['contact_phone'] = phone_match.group(1)
        
        email_match = re.search(r'(?:邮箱|email)\s*(?:改为|改成|变更为)?[:：]?\s*([\w.-]+@[\w.-]+\.\w+)', text)
        if email_match:
            updates['email'] = email_match.group(1)
        
        class_match = re.search(r'(?:班级|班)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if class_match:
            class_name = class_match.group(1).strip()
            class_obj = db.query(ClassModel).filter(ClassModel.name == class_name).first()
            if class_obj:
                updates['class_id'] = class_obj.id
        
        return {
            'action': 'navigate',
            'path': '/admin/students',
            'query': {
                'action': 'edit',
                'id': str(student_id)
            },
            'storage_data': {
                'student_id': student_id,
                'updates': updates
            },
            'message': '已为您打开学员编辑页面，请确认修改内容后提交'
        }
    
    def _parse_add_class(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加班级指令 - 返回导航信息"""
        class_info = self._clean_text(match.group(1).strip())
        
        # 优化：尝试多种方式提取班级名称
        name_match = re.search(r'(?:名字|名称|叫|名为)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = re.search(r'(?:班级)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = type('obj', (object,), {'group': lambda x: class_info})()
        
        class_name = self._clean_text(name_match.group(1).strip())
        
        # 提取年级
        grade_match = re.search(r'(?:年级)[:：]?\s*(.+?)(?:，|,|$)', text)
        grade_level = grade_match.group(1).strip() if grade_match else None
        
        return {
            'action': 'navigate',
            'path': '/admin/classes',
            'query': {
                'action': 'add'
            },
            'storage_data': {
                'class_name': class_name,
                'grade_level': grade_level
            },
            'message': '已为您打开添加班级页面，请确认信息后提交'
        }
    
    def _parse_update_class(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析更新班级指令 - 返回导航信息"""
        class_info = self._clean_text(match.group(1).strip())
        
        # 提取班级名称或ID
        class_match = re.search(r'(?:班级)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:的|，|,|$)', text)
        class_name_or_id = class_match.group(1).strip() if class_match else class_info
        
        # 尝试查找班级ID
        class_id = None
        if class_name_or_id.isdigit():
            class_id = int(class_name_or_id)
        elif db:
            class_obj = db.query(ClassModel).filter(ClassModel.name == class_name_or_id).first()
            if class_obj:
                class_id = class_obj.id
        
        if not class_id:
            return {
                'action': 'error',
                'message': f'未找到班级"{class_name_or_id}"，请确认班级名称或ID是否正确'
            }
        
        # 提取要更新的字段
        updates = {}
        
        name_match = re.search(r'(?:名称|名字)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if name_match:
            updates['name'] = name_match.group(1).strip()
        
        grade_match = re.search(r'(?:年级)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if grade_match:
            updates['grade_level'] = grade_match.group(1).strip()
        
        return {
            'action': 'navigate',
            'path': '/admin/classes',
            'query': {
                'action': 'edit',
                'id': str(class_id)
            },
            'storage_data': {
                'class_id': class_id,
                'updates': updates
            },
            'message': '已为您打开班级编辑页面，请确认修改内容后提交'
        }
    
    def _parse_add_room(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加教室指令 - 返回导航信息"""
        room_info = self._clean_text(match.group(1).strip())
        
        # 优化：尝试多种方式提取教室名称
        name_match = re.search(r'(?:名字|名称|叫|名为)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = re.search(r'(?:教室|房间)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if not name_match:
            name_match = type('obj', (object,), {'group': lambda x: room_info})()
        
        room_name = self._clean_text(name_match.group(1).strip())
        
        # 提取位置
        location_match = re.search(r'(?:位置|地点)[:：]?\s*(.+?)(?:，|,|$)', text)
        location = location_match.group(1).strip() if location_match else None
        
        # 提取容量
        capacity_match = re.search(r'(?:容量|座位数)[:：]?\s*(\d+)', text)
        capacity = int(capacity_match.group(1)) if capacity_match else None
        
        return {
            'action': 'navigate',
            'path': '/admin/rooms',
            'query': {
                'action': 'add'
            },
            'storage_data': {
                'room_name': room_name,
                'location': location,
                'capacity': capacity
            },
            'message': '已为您打开添加教室页面，请确认信息后提交'
        }
    
    def _parse_update_room(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析更新教室指令 - 返回导航信息"""
        room_info = self._clean_text(match.group(1).strip())
        
        # 提取教室名称或ID
        room_match = re.search(r'(?:教室|房间)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:的|，|,|$)', text)
        room_name_or_id = room_match.group(1).strip() if room_match else room_info
        
        # 尝试查找教室ID
        room_id = None
        if room_name_or_id.isdigit():
            room_id = int(room_name_or_id)
        elif db:
            room = db.query(Room).filter(Room.name == room_name_or_id).first()
            if room:
                room_id = room.id
        
        if not room_id:
            return {
                'action': 'error',
                'message': f'未找到教室"{room_name_or_id}"，请确认教室名称或ID是否正确'
            }
        
        # 提取要更新的字段
        updates = {}
        
        name_match = re.search(r'(?:名称|名字)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if name_match:
            updates['name'] = name_match.group(1).strip()
        
        location_match = re.search(r'(?:位置|地点)\s*(?:改为|改成|变更为)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if location_match:
            updates['location'] = location_match.group(1).strip()
        
        capacity_match = re.search(r'(?:容量|座位数)\s*(?:改为|改成|变更为)?[:：]?\s*(\d+)', text)
        if capacity_match:
            updates['capacity'] = int(capacity_match.group(1))
        
        return {
            'action': 'navigate',
            'path': '/admin/rooms',
            'query': {
                'action': 'edit',
                'id': str(room_id)
            },
            'storage_data': {
                'room_id': room_id,
                'updates': updates
            },
            'message': '已为您打开教室编辑页面，请确认修改内容后提交'
        }

    def _parse_add_leave(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加请假指令 - 返回导航信息"""
        # 提取人员名称（可能是导师或学员）
        person_match = re.search(r'(?:为|给)\s*(.+?)\s*(?:请假|请个假)', text)
        if not person_match:
            person_match = re.search(r'(.+?)\s*(?:请假|请个假)', text)
        
        if not person_match:
            return {
                'action': 'error',
                'message': '无法识别请假人员，请使用格式：为张三请假 或 张三请假'
            }
        
        person_name = person_match.group(1).strip()
        
        # 尝试查找是导师还是学员
        teacher_id = None
        student_id = None
        person_type = None
        
        if db:
            teacher = db.query(Teacher).filter(Teacher.name == person_name).first()
            if teacher:
                teacher_id = teacher.id
                person_type = 'teacher'
            else:
                student = db.query(Student).filter(Student.name == person_name).first()
                if student:
                    student_id = student.id
                    person_type = 'student'
        
        if not teacher_id and not student_id:
            return {
                'action': 'error',
                'message': f'未找到"{person_name}"，请确认是导师还是学员'
            }
        
        # 提取请假日期
        date_match = re.search(r'(?:日期|时间|从)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        start_date = date_match.group(1) if date_match else None
        
        # 提取结束日期
        end_date_match = re.search(r'(?:到|至|结束)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        end_date = end_date_match.group(1) if end_date_match else start_date
        
        # 提取请假原因
        reason_match = re.search(r'(?:原因|事由)[:：]?\s*(.+?)(?:，|,|$)', text)
        reason = reason_match.group(1).strip() if reason_match else None
        
        return {
            'action': 'navigate',
            'path': '/admin/leaves',
            'query': {
                'action': 'add'
            },
            'storage_data': {
                'person_name': person_name,
                'person_type': person_type,
                'teacher_id': teacher_id,
                'student_id': student_id,
                'start_date': start_date,
                'end_date': end_date,
                'reason': reason
            },
            'message': '已为您打开添加请假页面，请确认信息后提交'
        }
    
    def _parse_add_holiday(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加节假日指令 - 返回导航信息"""
        holiday_info = self._clean_text(match.group(1).strip())
        
        # 提取节假日名称
        name_match = re.search(r'(?:节假日|假日|假期|节日)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        holiday_name = name_match.group(1).strip() if name_match else holiday_info
        
        # 提取开始日期
        start_date_match = re.search(r'(?:开始|从|日期)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        start_date = start_date_match.group(1) if start_date_match else None
        
        # 提取结束日期
        end_date_match = re.search(r'(?:结束|到|至)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        end_date = end_date_match.group(1) if end_date_match else start_date
        
        if not start_date:
            return {
                'action': 'error',
                'message': '缺少节假日日期，请使用格式：添加节假日元旦，日期2024-01-01'
            }
        
        return {
            'action': 'navigate',
            'path': '/admin/holidays',
            'query': {
                'action': 'add'
            },
            'storage_data': {
                'holiday_name': holiday_name,
                'start_date': start_date,
                'end_date': end_date
            },
            'message': '已为您打开添加节假日页面，请确认信息后提交'
        }
    
    def _parse_collect_fee(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析收取费用指令 - 返回导航信息"""
        # 尝试匹配不同的格式
        # 格式1: 收取张三科目数学费用500元
        pattern1 = re.search(r'(?:收取|缴费|收费)\s*(.+?)\s*(?:科目|课程)\s*(.+?)\s*(?:费用|学费)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?', text)
        # 格式2: 收取张三费用500元，科目数学
        pattern2 = re.search(r'(?:收取|缴费|收费)\s*(.+?)\s*(?:费用|学费)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?(?:，|,)?(?:科目\s*(.+?))?', text)
        
        student_name = None
        course_name = None
        amount = None
        receivable_amount = None
        fee_date = None
        
        if pattern1:
            student_name = pattern1.group(1).strip()
            course_name = pattern1.group(2).strip()
            amount = float(pattern1.group(3))
        elif pattern2:
            student_name = pattern2.group(1).strip()
            amount = float(pattern2.group(2))
            course_name = pattern2.group(3).strip() if pattern2.group(3) else None
        
        # 提取应收金额
        receivable_match = re.search(r'(?:应收)\s*(\d+(?:\.\d+)?)\s*(?:元)?', text)
        if receivable_match:
            receivable_amount = float(receivable_match.group(1))
        
        # 提取日期
        date_match = re.search(r'(?:日期|时间)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            fee_date = date_match.group(1)
        
        if not student_name or not amount:
            return {
                'action': 'error',
                'message': '缺少学员姓名或金额，请使用格式：收取张三科目数学费用500元'
            }
        
        # 查询学员ID
        student_id = None
        if db:
            student = db.query(Student).filter(Student.name == student_name).first()
            if student:
                student_id = student.id
        
        if not student_id:
            return {
                'action': 'error',
                'message': f'未找到学员"{student_name}"，请确认学员姓名是否正确'
            }
        
        # 查询科目ID
        course_id = None
        if course_name and db:
            course = db.query(Course).filter(Course.name == course_name).first()
            if course:
                course_id = course.id
        
        return {
            'action': 'navigate',
            'path': '/admin/feemanagement',
            'query': {
                'action': 'collect'
            },
            'storage_data': {
                'student_id': student_id,
                'student_name': student_name,
                'course_id': course_id,
                'course_name': course_name,
                'amount': amount,
                'receivable_amount': receivable_amount,
                'fee_date': fee_date
            },
            'message': '已为您打开收费页面，请确认信息后提交'
        }
    
    def _parse_refund_fee(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析退费指令 - 返回导航信息"""
        # 提取学员姓名
        student_match = re.search(r'(?:退费|退款)\s*(.+?)\s*(?:科目|课程)?\s*(.+?)?\s*(?:费用|学费)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元)?', text)
        
        if not student_match:
            return {
                'action': 'error',
                'message': '无法识别退费信息，请使用格式：退费张三科目数学费用200元'
            }
        
        student_name = student_match.group(1).strip()
        course_name = student_match.group(2).strip() if student_match.group(2) else None
        amount = float(student_match.group(3))
        
        # 提取日期
        date_match = re.search(r'(?:日期|时间)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        refund_date = date_match.group(1) if date_match else None
        
        # 查询学员ID
        student_id = None
        if db:
            student = db.query(Student).filter(Student.name == student_name).first()
            if student:
                student_id = student.id
        
        if not student_id:
            return {
                'action': 'error',
                'message': f'未找到学员"{student_name}"，请确认学员姓名是否正确'
            }
        
        # 查询科目ID
        course_id = None
        if course_name and db:
            course = db.query(Course).filter(Course.name == course_name).first()
            if course:
                course_id = course.id
        
        return {
            'action': 'navigate',
            'path': '/admin/feemanagement',
            'query': {
                'action': 'refund'
            },
            'storage_data': {
                'student_id': student_id,
                'student_name': student_name,
                'course_id': course_id,
                'course_name': course_name,
                'amount': amount,
                'refund_date': refund_date
            },
            'message': '已为您打开退费页面，请确认信息后提交'
        }
    
    def _parse_add_grade(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析添加成绩指令 - 返回导航信息"""
        grade_info = self._clean_text(match.group(1).strip())
        
        # 提取学员姓名
        student_match = re.search(r'(?:学员|学生)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:的|，|,|$)', text)
        student_name = student_match.group(1).strip() if student_match else None
        
        # 提取科目名称
        course_match = re.search(r'(?:科目|课程)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:的|，|,|$)', text)
        course_name = course_match.group(1).strip() if course_match else None
        
        # 提取成绩
        score_match = re.search(r'(?:成绩|分数|得分)\s*(?:是|为|叫|乃)?[:：]?\s*(\d+(?:\.\d+)?)', text)
        score = float(score_match.group(1)) if score_match else None
        
        # 提取总分
        total_score_match = re.search(r'(?:总分|满分)\s*(?:是|为|叫|乃)?[:：]?\s*(\d+(?:\.\d+)?)', text)
        total_score = float(total_score_match.group(1)) if total_score_match else None
        
        # 提取考试日期
        date_match = re.search(r'(?:日期|时间|考试日期)[:：]?\s*(\d{4}-\d{2}-\d{2})', text)
        exam_date = date_match.group(1) if date_match else None
        
        # 提取年级
        grade_level_match = re.search(r'(?:年级)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        grade_level = grade_level_match.group(1).strip() if grade_level_match else None
        
        # 提取考试阶段
        stage_match = re.search(r'(?:阶段|考试阶段|类型)\s*(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        exam_stage = stage_match.group(1).strip() if stage_match else None
        
        if not student_name or not course_name or not score:
            return {
                'action': 'error',
                'message': '缺少必要信息，请使用格式：添加成绩，学员张三，科目数学，成绩95分'
            }
        
        # 查询学员ID
        student_id = None
        if db:
            student = db.query(Student).filter(Student.name == student_name).first()
            if student:
                student_id = student.id
        
        if not student_id:
            return {
                'action': 'error',
                'message': f'未找到学员"{student_name}"，请确认学员姓名是否正确'
            }
        
        # 查询科目ID
        course_id = None
        if db:
            course = db.query(Course).filter(Course.name == course_name).first()
            if course:
                course_id = course.id
        
        if not course_id:
            return {
                'action': 'error',
                'message': f'未找到科目"{course_name}"，请确认科目名称是否正确'
            }
        
        return {
            'action': 'navigate',
            'path': '/admin/grades',
            'query': {
                'action': 'add',
                'student_id': str(student_id)
            },
            'storage_data': {
                'student_id': student_id,
                'student_name': student_name,
                'course_id': course_id,
                'course_name': course_name,
                'score': score,
                'total_score': total_score,
                'exam_date': exam_date,
                'grade_level': grade_level,
                'exam_stage': exam_stage
            },
            'message': '已为您打开添加成绩页面，请确认信息后提交'
        }
    
    def _extract_person_names(self, text: str) -> List[str]:
        """
        从文本中提取人名列表，支持多种分隔符和语序
                '是', '为', '叫', '叫做', '名为', '姓名'
        Args:
            text: 输入文本
            
        Returns:
            人名列表
        """
        person_names = []
        db = SessionLocal()
        
        # 策略1: 尝试提取"给XXX和YYY添加/安排..."格式的多个人名
        give_match = re.search(r'(?:为|给|把|将)\s*(.+?)\s*(?:添加|安排|排|新增|新建|创建|增加)', text)
        if give_match:
            names_str = give_match.group(1).strip()
            log_operation(self.db, "智能指令解析", "提取人名", f"[DEBUG] 策略1提取到人名字符串: {names_str}",  "SYSTEM", "DEBUG")
            
            # 如果包含"的"，只取"的"之前的部分
            if '的' in names_str:
                names_str = names_str.split('的')[0].strip()
            
            # 拆分多个人名（支持"和"、"与"、"及"、"、"、","、"，"分隔）
            name_parts = re.split(r'[和与及同、,，]', names_str)
            for name_part in name_parts:
                name_part = name_part.strip()
                if name_part and 2 <= len(name_part) <= 4:
                    if not re.search(r'\d', name_part):
                        invalid_words = ['添加', '安排', '排课', '课程', '导师', '老师', '学生', '学员', 
                                       '明天', '今天', '后天', '上午', '下午', '晚上', '点', '分', '时',
                                       '周一', '周二', '周三', '周四', '周五', '周六', '周日', '星期',
                                       '初三', '高一', '高二', '英语', '数学', '语文']
                        is_invalid = False
                        for word in invalid_words:
                            if word in name_part:
                                is_invalid = True
                                break
                        
                        if not is_invalid:
                            person_names.append(name_part)
            
            log_operation(self.db, "智能指令解析", "提取人名", f"[DEBUG] 策略1提取到人名列表: {person_names}",  "SYSTEM", "DEBUG")
            if person_names:
                return person_names
        
        # 策略2: 尝试提取"XXX和YYY安排/添加..."格式（无"为|给"前缀）
        # 匹配模式：人名 + 动作词
        action_match = re.search(r'(.+?)\s*(?:安排|添加|排|新增|新建|创建|增加)', text)
        if action_match and not person_names:
            names_str = action_match.group(1).strip()
            log_operation(self.db, "智能指令解析", "提取人名", f"[DEBUG] 策略2提取到人名字符串: {names_str}",  "SYSTEM", "DEBUG")
            
            # 清理可能的前缀词
            names_str = re.sub(r'^(为|给|把|将)\s*', '', names_str).strip()
            
            # 如果包含"的"，只取"的"之前的部分
            if '的' in names_str:
                names_str = names_str.split('的')[0].strip()
            
            # 拆分多个人名
            name_parts = re.split(r'[和与及同、,，]', names_str)
            for name_part in name_parts:
                name_part = name_part.strip()
                if name_part and 2 <= len(name_part) <= 4:
                    if not re.search(r'\d', name_part):
                        invalid_words = ['添加', '安排', '排课', '课程', '导师', '老师', '学生', '学员',
                                       '明天', '今天', '后天', '上午', '下午', '晚上', '点', '分', '时',
                                       '周一', '周二', '周三', '周四', '周五', '周六', '周日', '星期',
                                       '初三', '高一', '高二', '英语', '数学', '语文']
                        is_invalid = False
                        for word in invalid_words:
                            if word in name_part:
                                is_invalid = True
                                break
                        
                        if not is_invalid:
                            person_names.append(name_part)
            
            log_operation(self.db, "智能指令解析", "提取人名", f"[DEBUG] 策略2提取到人名列表: {person_names}",  "SYSTEM", "DEBUG")
            if person_names:
                return person_names
        
        # 策略3: 如果没有从上述方式中提取到人名，尝试其他方式
        give_match2 = re.search(r'(?:为|给|把|将)\s*(.+?)(?:的|，|,|$)', text)
        if give_match2 and not person_names:
            names_str = give_match2.group(1).strip()
            # 只取"添加"之前的部分
            add_pos = names_str.find('添加')
            if add_pos > 0:
                names_str = names_str[:add_pos].strip()
            
            # 如果包含"的"，只取"的"之前的部分
            if '的' in names_str:
                names_str = names_str.split('的')[0].strip()
            
            name_parts = re.split(r'[和与及同、,，]', names_str)
            for name_part in name_parts:
                name_part = name_part.strip()
                if name_part and 2 <= len(name_part) <= 4:
                    if not re.search(r'\d', name_part):
                        invalid_words = ['添加', '安排', '排课', '课程', '导师', '老师', '学生', '学员',
                                       '明天', '今天', '后天', '上午', '下午', '晚上', '点', '分', '时',
                                       '周一', '周二', '周三', '周四', '周五', '周六', '周日', '星期',
                                       '初三', '高一', '高二', '英语', '数学', '语文']
                        is_invalid = False
                        for word in invalid_words:
                            if word in name_part:
                                is_invalid = True
                                break
                        
                        if not is_invalid:
                            person_names.append(name_part)
            
            if person_names:
                return person_names
        
        # 策略4: 如果还是没有找到人名，尝试提取"XXX的排课"格式
        possessive_match = re.search(r'(.+?)的(?:排课|课程)', text)
        if possessive_match and not person_names:
            names_str = possessive_match.group(1).strip()
            name_parts = re.split(r'[和与及同、,，]', names_str)
            for name_part in name_parts:
                name_part = name_part.strip()
                if name_part and 2 <= len(name_part) <= 4:
                    if not re.search(r'\d', name_part):
                        invalid_words = ['添加', '安排', '排课', '课程', '导师', '老师', '学生', '学员',
                                       '明天', '今天', '后天', '上午', '下午', '晚上', '点', '分', '时',
                                       '周一', '周二', '周三', '周四', '周五', '周六', '周日', '星期',
                                       '初三', '高一', '高二', '英语', '数学', '语文']
                        is_invalid = False
                        for word in invalid_words:
                            if word in name_part:
                                is_invalid = True
                                break
                        
                        if not is_invalid:
                            person_names.append(name_part)
        
        return person_names

    def _clean_text(self, text: str) -> str:
        """
        清理文本，去除前后空格和无关词汇
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ''
        
        text = text.strip()
        
        # 去除常见的前缀词
        prefixes = ['听好了', '注意了', '请注意', '请听好', '请听好了', '请听清楚', '请听清楚了', '请听清楚啊', '听清楚']
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        # 去除常见的后缀词
        suffixes = ['就这样', '就这些', '这样', '这些', '大体就这样', '大体就这些', 
                    '大概就这样', '大概就这些', '大约就这样', '大约就这些', '大体上', 
                    '等等', '等', '之类的', '什么的', '之类', '等一下', '等等的', 
                    '好吧', '可以吗', '行吗', '怎么样', '怎么样啊', '怎么样呢', '怎么样吧'
                    ]
        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()

        # 去除常见的语气词
        mood_words = ['嗯', '吧', '了', '啊', '呢', '嘛', '呀', '哦', '哈', '嘿', '哇', '咦', '哎', '哟', '呃', '呕', '呗', '呜', '咳', '咚', '咩', '咕', '咒', '咯', '咿', '咻', '咳咳', '咕咕', '咕噜', '咕叽', '咕哝', '咕哝哝', '咕哝哝哝', '咕哝哝哝哝']
        for mood in mood_words:
            if text.endswith(mood):
                text = text[:-len(mood)].strip()
        
        # 去除形容词
        adjectives = ['新的', '旧的', '老的', '原来的', '新', '旧', '老']
        
        # 去除多余的标点符号
        text = re.sub(r'[，,。.!！?？；;：:\s]+', ' ', text)
        
        return text
    
    def _chinese_number_to_int(self, chinese_num: str) -> int:
        """
        将中文数字转换为整数
        
        Args:
            chinese_num: 中文数字字符串（如一、二、三、两等）
            
        Returns:
            对应的整数
        """
        chinese_map = {
            '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
            '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
            '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24
        }
        return chinese_map.get(chinese_num, 0)
    
    def _parse_time_expression(self, time_str: str, time_period: str = None) -> str:
        """
        解析时间表达式，支持多种格式
        
        Args:
            time_str: 时间字符串（如"2点半"、"两点半"、"14:30"等）
            time_period: 时间段（morning/afternoon/evening），用于判断是否需要+12小时
            
        Returns:
            标准化时间字符串（HH:MM格式）
        """
        if not time_str:
            return None
        
        time_str = time_str.strip()
        
        # 格式1: HH:MM 或 HH：MM
        colon_match = re.match(r'(\d{1,2})[:：](\d{2})', time_str)
        if colon_match:
            hour = int(colon_match.group(1))
            minute = int(colon_match.group(2))
            return f"{hour:02d}:{minute:02d}"
        
        # 格式2: X点Y分 / X点Y / X点半
        # 匹配中文数字或阿拉伯数字
        chinese_time_match = re.match(r'([一二两三四五六七八九十]+|\d+)点(?:([一二两三四五六七八九十]+|\d+)分|半)?', time_str)
        if chinese_time_match:
            hour_str = chinese_time_match.group(1)
            minute_str = chinese_time_match.group(2)
            
            # 转换小时
            if hour_str.isdigit():
                hour = int(hour_str)
            else:
                hour = self._chinese_number_to_int(hour_str)
            
            # 转换分钟
            if minute_str:
                if minute_str == '半':
                    minute = 30
                elif minute_str.isdigit():
                    minute = int(minute_str)
                else:
                    minute = self._chinese_number_to_int(minute_str)
            else:
                minute = 0
            
            # 根据时间段调整小时（下午/晚上需要+12）
            if time_period == 'afternoon' and hour < 12:
                hour += 12
            elif time_period == 'evening' and hour < 12:
                hour += 12
            
            return f"{hour:02d}:{minute:02d}"
        
        # 格式3: X点（整点）
        simple_hour_match = re.match(r'([一二两三四五六七八九十]+|\d+)点$', time_str)
        if simple_hour_match:
            hour_str = simple_hour_match.group(1)
            if hour_str.isdigit():
                hour = int(hour_str)
            else:
                hour = self._chinese_number_to_int(hour_str)
            
            # 根据时间段调整小时
            if time_period == 'afternoon' and hour < 12:
                hour += 12
            elif time_period == 'evening' and hour < 12:
                hour += 12
            
            return f"{hour:02d}:00"
        
        return None

    def _parse_create_schedule(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析创建排课指令 - 支持19种语序模式的智能提取
        
        支持的19种模式：
        1. 为|给 SSS VVV DDD的课程，科目是TTT的CCC
        2. 为|给 SSS VVV DDD的CCC课程，导师是TTT
        3. DDD为|给 SSS VVV课程，科目是TTT的CCC
        4. DDD为|给 SSS VVV CCC课程，导师是TTT
        5. VVV SSS DDD的课程，科目是TTT的CCC
        6. VVV SSS DDD的CCC课程，导师是TTT
        7. 为|给 SSS 在/于 DDD VVV TTT 的 CCC 课程
        8. 为|给 SSS 在|于DDD VVV CCC 课程，导师是 TTT
        9. 在|于 DDD 为|给 SSS VVV TTT 的 CCC 课程
        10. 在|于 DDD 为|给 SSS VVV CCC 课程，导师是 TTT
        11. 为|给 SSS VVV 在|于 DDD TTT 的 CCC 课程
        12. 为|给 SSS VVV 在|于 DDD 的 CCC 课程，导师是 TTT
        13. 为|给 SSS VVV TTT 在|于 DDD 的 CCC 课程
        14. VVV 为|给 SSS 在|于 DDD TTT 的 CCC 课程
        15. VVV 为|给 SSS 在|于 DDD 的 CCC 课程，导师是 TTT
        16. 在|于DDD 将|把TTT 的 CCC 课程 VVV给SSS
        17. 在/于DDD 将|把 CCC 课程 VVV给SSS，导师是 TTT
        18. 将|把TTT 的 CCC 课程 在|于DDD VVV给SSS
        19. 将|把 CCC 课程 在|于DDD VVV给SSS，导师是 TTT
        """
        
        log_operation(self.db, "智能指令解析", "解析排课指令", f"[DEBUG] 解析排课指令: {text}",  "SYSTEM", "DEBUG")
        
        # ========== 第一步：提取日期和时间段（DDD）==========
        start_date = None
        end_date = None
        start_time = None
        end_time = None
        time_period = None
        
        # 1. 提取具体日期（YYYY-MM-DD格式）
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            try:
                parsed_date = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                start_date = parsed_date
                end_date = parsed_date
            except ValueError:
                pass
        
        # 2. 提取相对日期（今天、明天、后天等）
        today = date.today()
        if not start_date:
            if '明天' in text:
                start_date = today + timedelta(days=1)
                end_date = start_date
            elif '今天' in text:
                start_date = today
                end_date = today
            elif '后天' in text or '两天后' in text:
                start_date = today + timedelta(days=2)
                end_date = start_date
            elif '大后天' in text or '三天后' in text:
                start_date = today + timedelta(days=3)
                end_date = start_date
        
        # 2.5 提取"X月X号"或"X月X日"格式的日期（默认为今年）
        if not start_date:
            month_day_match = re.search(r'(\d{1,2})月(\d{1,2})[号日]', text)
            if month_day_match:
                try:
                    month = int(month_day_match.group(1))
                    day = int(month_day_match.group(2))
                    year = today.year  # 使用当前年份
                    
                    # 验证月份和日期的有效性
                    import calendar
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        max_day = calendar.monthrange(year, month)[1]
                        if day <= max_day:
                            start_date = date(year, month, day)
                            end_date = start_date
                            log_operation(self.db, "智能指令解析", "DEBUG", f"从'{month}月{day}号'提取到日期: {start_date}", level="DEBUG")
                        else:
                            log_operation(self.db, "智能指令解析", "DEBUG", f"日期无效: {year}-{month}-{day} (当月最大天数: {max_day})", level="WARNING")
                    else:
                        log_operation(self.db, "智能指令解析", "DEBUG", f"月份或日期超出范围: {month}-{day}", level="WARNING")
                except Exception as e:
                    log_operation(self.db, "智能指令解析", "DEBUG", f"解析月日格式失败: {e}", level="WARNING")
        
        # 3. 提取时间段描述（上午/下午/晚上）
        if '上午' in text:
            time_period = 'morning'
        elif '下午' in text:
            time_period = 'afternoon'
        elif '晚上' in text or '晚间' in text:
            time_period = 'evening'
        
        # 4. 提取具体时间范围
        # 优先匹配带分钟的时间格式（如"2点半到4点半"、"两点半到四点半"、"10点一刻到12点一刻"）
        time_with_minute_match = re.search(r'([一二两三四五六七八九十]+|\d{1,2})点((?:[一二两三四五六七八九十]+|\d{1,2})分|半|一刻)?(?:到|-|~|至)\s*([一二两三四五六七八九十]+|\d{1,2})点((?:[一二两三四五六七八九十]+|\d{1,2})分|半|一刻)?', text)
        if time_with_minute_match:
            start_hour_str = time_with_minute_match.group(1)
            start_minute_str = time_with_minute_match.group(2)
            end_hour_str = time_with_minute_match.group(3)
            end_minute_str = time_with_minute_match.group(4)
            
            # 转换开始时间
            if start_hour_str.isdigit():
                start_hour = int(start_hour_str)
            else:
                start_hour = self._chinese_number_to_int(start_hour_str)
            
            if start_minute_str:
                if start_minute_str == '半':
                    start_minute = 30
                elif start_minute_str == '一刻':
                    start_minute = 15
                elif start_minute_str.endswith('分'):
                    minute_num = start_minute_str[:-1]
                    if minute_num.isdigit():
                        start_minute = int(minute_num)
                    else:
                        start_minute = self._chinese_number_to_int(minute_num)
                else:
                    start_minute = 0
            else:
                start_minute = 0
            
            # 转换结束时间
            if end_hour_str.isdigit():
                end_hour = int(end_hour_str)
            else:
                end_hour = self._chinese_number_to_int(end_hour_str)
            
            if end_minute_str:
                if end_minute_str == '半':
                    end_minute = 30
                elif end_minute_str == '一刻':
                    end_minute = 15
                elif end_minute_str.endswith('分'):
                    minute_num = end_minute_str[:-1]
                    if minute_num.isdigit():
                        end_minute = int(minute_num)
                    else:
                        end_minute = self._chinese_number_to_int(minute_num)
                else:
                    end_minute = 0
            else:
                end_minute = 0
            
            # 根据时间段调整小时（下午/晚上需要+12）
            if time_period == 'afternoon':
                if start_hour < 12:
                    start_hour += 12
                if end_hour < 12:
                    end_hour += 12
            elif time_period == 'evening':
                if start_hour < 12:
                    start_hour += 12
                if end_hour < 12:
                    end_hour += 12
            
            start_time = f"{start_hour:02d}:{start_minute:02d}"
            end_time = f"{end_hour:02d}:{end_minute:02d}"
        else:
            # 匹配整点格式（如"10点到12点"）
            time_match = re.search(r'(\d{1,2})点(?:到|-|~|至|to)\s*(\d{1,2})点', text)
            if time_match:
                start_hour = int(time_match.group(1))
                end_hour = int(time_match.group(2))
                start_time = f"{start_hour:02d}:00"
                end_time = f"{end_hour:02d}:00"
            else:
                # 匹配HH:MM格式
                time_match = re.search(r'(\d{1,2}[:：]\d{2})\s*[-至~to到]\s*(\d{1,2}[:：]\d{2})', text)
                if time_match:
                    start_time = time_match.group(1).replace('：', ':')
                    end_time = time_match.group(2).replace('：', ':')
        
        log_operation(self.db, "智能指令解析", "DEBUG", f"提取到日期: {start_date} - {end_date}, 时间: {start_time} - {end_time}", level="DEBUG")
        
        # ========== 第二步：提取学员姓名（SSS）==========
        person_names = self._extract_person_names(text)
        
        # 特殊处理："VVV给SSS"句式（模式16-19）
        if not person_names:
            give_match = re.search(r'(?:新增|新建|创建|安排|添加|增加|增添)\s*给\s*(.+?)(?:，|,|$)', text)
            if give_match:
                names_str = give_match.group(1).strip()
                # 分割多个学员
                name_parts = re.split(r'[和与及同、,，]', names_str)
                for name_part in name_parts:
                    name_part = name_part.strip()
                    if name_part and 2 <= len(name_part) <= 4 and not re.search(r'\d', name_part):
                        person_names.append(name_part)
        
        log_operation(self.db, "智能指令解析", "DEBUG", f"提取到学员: {person_names}", level="DEBUG")
        
        # ========== 第三步：提取导师姓名（TTT）==========
        teacher_name = None
        
        # 策略1: 匹配"XXX老师"或"XXX导师"格式（优先级最高，如"张老师"、"李老师"）
        teacher_suffix_pattern = re.finditer(r'([^\s，,。\n]{1,3})(?:老师|导师)', text)
        for match in teacher_suffix_pattern:
            candidate = match.group(1).strip()
            # 验证是否为有效人名（1-3个字符，不包含数字和标点）
            if 1 <= len(candidate) <= 3 and not re.search(r'[\d，,。\s]', candidate):
                invalid_words = ['添加', '安排', '排课', '课程', '学生', '学员', '明天', '今天', 
                               '后天', '上午', '下午', '晚上', '周一', '周二', '周三', '周四', 
                               '周五', '周六', '周日', '星期', '英语', '数学', '语文', '物理', '化学',
                               '点', '分', '时', '到', '至', '半', '一个', '刻']
                # 只保留纯文字部分（排除单独的无效词）
                if candidate and candidate not in ['老', '师', '导', '的老', '的导', '程', '程，', '，导']:
                    teacher_name = candidate + '老师'
                    log_operation(self.db, "智能指令解析", "DEBUG", f"策略1提取到导师: {teacher_name}", level="DEBUG")
                    break
        
        # 策略2: 直接匹配"导师是XXX"或"老师是XXX"
        if not teacher_name:
            teacher_is_pattern = re.search(r'(?:导师|老师)(?:是|为|乃|叫|叫做)[:：]?\s*(.+?)(?:，|,|$)', text)
            if teacher_is_pattern:
                candidate = teacher_is_pattern.group(1).strip()
                if 2 <= len(candidate) <= 4 and not re.search(r'\d', candidate):
                    invalid_words = ['添加', '安排', '排课', '课程', '学生', '学员', '明天', '今天', 
                                   '后天', '上午', '下午', '晚上', '周一', '周二', '周三', '周四', 
                                   '周五', '周六', '周日', '星期', '英语', '数学', '语文', '物理', '化学',
                                   '点', '分', '时', '到', '至', '半']
                    if not any(word in candidate for word in invalid_words):
                        teacher_name = candidate
                        log_operation(self.db, "智能指令解析", "DEBUG", f"策略2提取到导师: {teacher_name}", level="DEBUG")
        
        # 策略3: 处理"代怀凯的英语课程"这种"XXX的YYY课程"结构
        if not teacher_name:
            possessive_matches = re.finditer(r'([^，,。\s]{2,4})的(\S+)', text)
            for poss_match in possessive_matches:
                candidate = poss_match.group(1).strip()
                followed_word = poss_match.group(2).strip()
                
                # 验证candidate是否为人名
                if 2 <= len(candidate) <= 4 and not re.search(r'\d', candidate):
                    # 排除包含时间相关词汇的候选
                    time_words = ['点', '分', '时', '到', '至', '上午', '下午', '晚上', '早上', '中午', '傍晚', '半', '刻']
                    has_time_word = any(word in candidate for word in time_words)
                    
                    if not has_time_word:
                        invalid_words = ['添加', '安排', '排课', '课程', '学生', '学员', '明天', '今天', 
                                       '后天', '周一', '周二', '周三', '周四', '周五', '周六', '周日', '星期']
                        if not any(word in candidate for word in invalid_words):
                            # 关键判断：如果后面跟的是常见科目名，则candidate很可能是导师
                            common_courses = ['英语', '数学', '语文', '物理', '化学', '生物', '历史', '地理', '政治', 
                                            '体育', '音乐', '美术', '编程', '科学']
                            if any(course in followed_word for course in common_courses):
                                teacher_name = candidate
                                log_operation(self.db, "智能指令解析", "DEBUG", f"策略3提取到导师: {teacher_name} (后面跟着: {followed_word})", level="DEBUG")
                                break
        
        # 策略4: 从"科目是XXX的"结构中提取
        if not teacher_name:
            course_is_pattern = re.search(r'(?:科目|课程)是(.{2,4})的', text)
            if course_is_pattern:
                candidate = course_is_pattern.group(1).strip()
                if 2 <= len(candidate) <= 4 and not re.search(r'\d', candidate):
                    invalid_words = ['添加', '安排', '排课', '课程', '学生', '学员', '明天', '今天', 
                                   '后天', '上午', '下午', '晚上', '周一', '周二', '周三', '周四', 
                                   '周五', '周六', '周日', '星期', '英语', '数学', '语文', '点', '分', '时', '半']
                    if not any(word in candidate for word in invalid_words):
                        teacher_name = candidate
                        log_operation(self.db, "智能指令解析", "DEBUG", f"策略4提取到导师: {teacher_name}", level="DEBUG")
        
        # 策略5: 处理"将|把TTT的CCC课程"句式（模式16、18）
        if not teacher_name:
            ba_pattern = re.search(r'(?:将|把)\s*([^，,。\s]{2,4})的', text)
            if ba_pattern:
                candidate = ba_pattern.group(1).strip()
                if 2 <= len(candidate) <= 4 and not re.search(r'\d', candidate):
                    time_words = ['点', '分', '时', '到', '至', '上午', '下午', '晚上', '早上', '中午', '傍晚', '半', '刻']
                    has_time_word = any(word in candidate for word in time_words)
                    
                    if not has_time_word:
                        invalid_words = ['添加', '安排', '排课', '课程', '学生', '学员', '明天', '今天', 
                                       '后天', '上午', '下午', '晚上', '周一', '周二', '周三', '周四', 
                                       '周五', '周六', '周日', '星期', '英语', '数学', '语文']
                        if not any(word in candidate for word in invalid_words):
                            teacher_name = candidate
                            log_operation(self.db, "智能指令解析", "DEBUG", f"策略5提取到导师: {teacher_name}", level="DEBUG")
        
        log_operation(self.db, "智能指令解析", "DEBUG", f"最终提取到导师: {teacher_name}", level="DEBUG")
        
        # ========== 第四步：提取科目名称（CCC）==========
        course_name = None
        
        # 策略1: 直接匹配"科目是XXX"或"课程是XXX"
        course_direct = re.search(r'(?:科目|课程|学科)(?:是|为|叫|乃)?[:：]?\s*(.+?)(?:，|,|$)', text)
        if course_direct:
            course_name = course_direct.group(1).strip()
            course_name = re.sub(r'(课程|课|排课)$', '', course_name).strip()
            log_operation(self.db, "智能指令解析", "DEBUG", f"策略1提取到科目: {course_name}", level="DEBUG")
        
        # 策略2: 从"XXX的YYY"结构中提取YYY作为科目（如"代怀凯的数学"中数学是科目）
        if not course_name:
            # 寻找"导师名 + 的 + 科目名"的模式
            possessive_course = re.search(r'(?:导师|老师|.{2,4})的\s*(.{1,10}?)(?:课程|课|排课)?(?:，|,|$)', text)
            if possessive_course:
                candidate = possessive_course.group(1).strip()
                candidate = re.sub(r'(课程|课|排课|课程安排)$', '', candidate).strip()
                
                # 验证：不能是导师名、不能是常见非科目词
                if candidate and 1 <= len(candidate) <= 10 and candidate != teacher_name:
                    invalid_course_words = ['添加', '安排', '排课', '课程', '学生', '学员', '明天', '今天',
                                          '后天', '上午', '下午', '晚上']
                    if not any(word in candidate for word in invalid_course_words):
                        course_name = candidate
                        log_operation(self.db, "智能指令解析", "DEBUG", f"策略2提取到科目: {course_name}", level="DEBUG")
        
        # 策略3: 处理"将|把TTT的CCC课程"句式（模式16、18）
        if not course_name:
            ba_course_pattern = re.search(r'(?:将|把)\s*(?:.{2,4}的)?\s*(.{1,10}?)(?:课程|课|排课)', text)
            if ba_course_pattern:
                candidate = ba_course_pattern.group(1).strip()
                if candidate and 1 <= len(candidate) <= 10 and candidate != teacher_name:
                    course_name = candidate
                    log_operation(self.db, "智能指令解析", "DEBUG", f"策略3提取到科目: {course_name}", level="DEBUG")
        
        # 策略4: 匹配常见科目名称
        if not course_name:
            common_courses = ['数学', '英语', '语文', '物理', '化学', '生物', '历史', '地理', '政治', '体育', '音乐', '美术', 
                              '信息技术', '编程', '机器人', '奥数', '英语口语', '写作', '阅读', '科学', '综合实践', '心理辅导', 
                              '兴趣班', '艺术', '经济学', '哲学', '社会学', '法学', '医学', '工程学', '计算机科学', '环境科学', 
                              '体育运动', '音乐艺术', '舞蹈', '戏剧', '电影', '摄影', '设计', '编程语言', '数据科学', '人工智能', 
                              '机器学习', '深度学习', '自然语言处理', '计算机视觉', '大数据', '云计算', '网络安全', '区块链', '金融学', 
                              '会计学', '市场营销', '管理学', '人力资源', '心理学', '教育学', '法律', '政治学', '历史学', '地理学', 
                              '软件工程', '软件测试', '算法', '数据结构', '操作系统', '数据库', '计算机网络', '编译原理', 
                              '计算机组成原理', '数字逻辑', '微机原理', '电路', '电子学', '通信原理', '信号与系统', '控制系统', '自动化', 
                              '机械设计', '机械制造', '机械原理', '机械电子工程', '机械自动化', '机械工程', '土木工程', '建筑学', '环境设计', 
                              '城市规划', '交通工程', '水利工程', '电气工程', '电子工程', '通信工程', '计算机工程', '材料工程', '自动化工程',
                              '生物工程', '化学工程', '环境工程', '能源工程', '核工程', '航空航天工程', '船舶与海洋工程', '农业工程', 
                              '食品科学与工程', '纺织工程', '轻工技术与工程', '安全工程', '质量管理工程', '物流工程', '工程管理', '项目管理',
                              '工商管理', '财务管理', '人力资源管理', '信息管理与信息系统', '电子商务', '旅游管理', '公共事业管理',
                              '公共管理', '行政管理', '图书馆学', '档案学', '新闻学', '传播学', '广告学', '广播电视编导', '播音与主持艺术',
                              '表演', '戏剧影视文学', '电影学', '美术学', '设计学', '动画', '音乐学', '作曲与作曲技术理论',
                              '音乐表演', '舞蹈学', '舞蹈表演', '戏剧影视导演', '戏剧影视表演', '戏剧影视美术设计',
                              '口才', '演讲', '辩论', '收纳', '整理', '时间管理', '效率工具', '学习方法', '考试技巧', '职业规划', '兴趣培养', 
                              '素质拓展', '户外活动', '运动', '健康管理', '营养学', '心理健康', '情绪管理', '人际关系', '沟通技巧', '领导力', 
                              '团队合作', '创新思维', '创业指导']
            for course in common_courses:
                if course in text:
                    # 确保科目名不在导师位置
                    if teacher_name != course:
                        course_name = course
                        log_operation(self.db, "智能指令解析", "DEBUG", f"策略4提取到科目: {course_name}", level="DEBUG")
                        break
        
        log_operation(self.db, "智能指令解析", "DEBUG", f"最终提取到科目: {course_name}", level="DEBUG")
        
        # ========== 第五步：提取其他信息 ==========
        # 提取年级
        grade_level = None
        grade_match = re.search(r'(小学[一二三四五六]|初[一二三]|高[一二三]|一年级|二年级|三年级|四年级|五年级|六年级|七年级|八年级|九年级|专[一二三]|大[一二三四]|研[一二三]|博[一二三])', text)
        if grade_match:
            grade_level = grade_match.group(1)
        
        # 提取星期几
        weekday_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7, '天': 7}
        weekday_match = re.search(r'周([一二三四五六日天])', text)
        day_of_week = weekday_map.get(weekday_match.group(1)) if weekday_match else None
        
        # 提取教室
        room_name = None
        room_match = re.search(r'(?:教室|房间|会议室|教研室)[:：]?\s*(.+?)(?:，|,|$)', text)
        if room_match:
            room_name = room_match.group(1).strip()
        
        # 提取班级
        class_name = None
        class_match = re.search(r'(?:班级|班)[:：]?\s*(.+?)(?:的|，|,|$)', text)
        if class_match:
            class_name = class_match.group(1).strip()
        
        # 如果没有班级但有学生，尝试查找共同班级
        if person_names and not class_name and db:
            student_classes = []
            for student_name in person_names:
                student = db.query(Student).filter(Student.name == student_name).first()
                if student:
                    student_classes.append({
                        'student_id': student.id,
                        'student_name': student.name,
                        'classes': [(c.id, c.name) for c in student.classes]
                    })
            
            if student_classes:
                common_classes = self._find_common_classes(student_classes)
                if common_classes:
                    class_name = common_classes[0]['name']
        
        # 计算星期几
        if not day_of_week and start_date:
            day_of_week = start_date.weekday() + 1 if start_date.weekday() != 6 else 7
        
        # ========== 第六步：检查缺失字段并返回结果 ==========
        missing_fields = []
        if not person_names:
            missing_fields.append('person_names')
        if not course_name:
            missing_fields.append('course_name')
        if not teacher_name:
            missing_fields.append('teacher_name')
        if not start_time:
            missing_fields.append('start_time')
        if not end_time:
            missing_fields.append('end_time')
        if not start_date:
            missing_fields.append('start_date')
        if not end_date:
            missing_fields.append('end_date')
        
        result = {
            'action': 'create_schedule',
            'person_names': person_names,
            'class_name': class_name,
            'course_name': course_name,
            'teacher_name': teacher_name,
            'room_name': room_name,
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
            'time_period': time_period,
            'grade_level': grade_level,
            'missing_fields': missing_fields if missing_fields else None,
            'needs_manual_confirmation': True
        }
        
        log_operation(self.db, "智能指令解析", "DEBUG", f"解析结果: {result}", level="DEBUG")
        return result
    
    def _find_common_classes(self, student_classes: List[Dict]) -> List[Dict]:
        """查找多个学生的共同班级"""
        if not student_classes:
            return []
        
        # 获取第一个学生的所有班级
        first_student_classes = {cid: cname for cid, cname in student_classes[0]['classes']}
        
        # 与其他学生的班级取交集
        for student_info in student_classes[1:]:
            current_classes = {cid: cname for cid, cname in student_info['classes']}
            common_ids = set(first_student_classes.keys()) & set(current_classes.keys())
            first_student_classes = {cid: first_student_classes[cid] for cid in common_ids}
        
        # 转换为列表格式
        return [{'id': cid, 'name': cname} for cid, cname in first_student_classes.items()]

    # 基于AI大模型的解析（需要配置API密钥）
    def _ai_based_parse(self, text: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        基于AI大模型的解析（需要配置API密钥）
        
        注意：此方法必须返回与_rule_based_parse兼容的数据结构
        支持DeepSeek、通义千问等OpenAI兼容格式的API
        """
        import time
        from datetime import date
        start_time = time.time()

        # 获取当前年份，用于日期解析
        current_year = date.today().year
         
        try:
            import requests
            from models import SmartCommandExample
            
            provider = self.ai_config.get('provider', 'qwen')
            api_url = self.ai_config.get('api_url', '')
            api_key = self.ai_config.get('api_key', '')
            model = self.ai_config.get('model', 'deepseek-v4-flash')
            timeout = self.ai_config.get('timeout', 60)  # 增加默认超时到60秒
            
            log_operation(db, "智能指令", "DEBUG", f"开始AI解析，use_ai={self.use_ai}, enabled={self.ai_config.get('enabled')}", level="DEBUG")
            
            if not api_url or not api_key:
                log_operation(db, "智能指令", "DEBUG", "API配置不完整，跳过AI解析", level="WARNING")
                return None
            
            # 从数据库获取一些上下文信息，帮助AI更准确地解析
            # 优化：只获取少量记录，减少数据传输量和Prompt长度
            log_operation(db, "智能指令", "DEBUG", "开始查询数据库...", level="DEBUG")
            db_query_start = time.time()
            
            all_teachers = [t.name for t in db.query(Teacher).limit(25).all()] if db else []
            all_courses = [c.name for c in db.query(Course).limit(25).all()] if db else []
            all_students = [s.name for s in db.query(Student).limit(25).all()] if db else []
            all_classes = [c.name for c in db.query(ClassModel).limit(25).all()] if db else []
            all_rooms = [r.name for r in db.query(Room).limit(25).all()] if db else []
            
            # 从数据库获取智能指令示例（最多取20条，避免提示词过长导致超时）
            examples = db.query(SmartCommandExample)\
                        .filter(SmartCommandExample.is_active == True)\
                        .order_by(SmartCommandExample.sort_order, SmartCommandExample.id)\
                        .limit(20)\
                        .all()
            
            db_query_elapsed = time.time() - db_query_start
            log_operation(db, "智能指令", "DEBUG", f"数据库查询完成，耗时: {db_query_elapsed:.2f}秒", level="DEBUG")
            log_operation(db, "智能指令", "DEBUG", f"查询结果: teachers={len(all_teachers)}, courses={len(all_courses)}, students={len(all_students)}, classes={len(all_classes)}, rooms={len(all_rooms)}, examples={len(examples)}", level="DEBUG")
            
            # 构建示例文本
            examples_text = ""
            if examples:
                examples_text = "\n【参考示例】\n以下是用户可能使用的自然语言表达方式，请参考这些示例理解用户意图：\n"
                for i, example in enumerate(examples[:20], 1):
                    # 只取前100个字符作为示例，防止单条示例过长
                    short_text = example.example_text[:100] + "..." if len(example.example_text) > 100 else example.example_text
                    examples_text += f"{i}. [{example.category}] {example.action_name}: \"{short_text}\"\n"
                examples_text += "\n请根据上述示例的模式来理解用户的新指令。\n"
            
            prompt = f"""你是一个智能指令解析助手，负责将用户的自然语言指令转换为课程安排系统的结构化操作。

{examples_text}

【支持的操作类型及返回格式】
注意：无论用户使用的是"添加"、"增加"、"创建"、"新建"、"新增"、"录入"、"更新"、"更改"、"修改"、"改正"、"改变"、"取消"，只要意图明确，都必须返回对应的 navigate 动作，严禁返回 error，除非完全无法理解意图。

1. 添加科目 (add_course)
   返回: {{"action": "navigate", "path": "/admin/courses", "query": {{"action": "add"}}, "storage_data": {{"course_name": "科目名称", "teacher_name": "导师姓名(可选)", "teacher_id": 导师ID(可选), "priority": 优先级数字(可选)}}, "message": "已为您打开添加科目页面，请确认信息后提交"}}

2. 更新科目 (update_course)
   返回: {{"action": "navigate", "path": "/admin/courses", "query": {{"action": "edit", "id": "科目ID"}}, "storage_data": {{"course_id": 科目ID, "updates": {{"name": "新名称(可选)", "priority": 新优先级(可选)}}}}, "message": "已为您打开科目编辑页面，请确认修改内容后提交"}}

3. 创建排课 (create_schedule)
   返回: {{"action": "navigate", "path": "/admin/schedules", "query": {{"action": "add"}}, "storage_data": {{"studentNames": ["学生姓名列表"], "className": "班级名称", "courseName": "科目名称", "teacherName": "导师姓名", "roomName": "教室名称", "dayOfWeek": 星期几(1-7, 可选), "startTime": "开始时间(HH:MM)", "endTime": "结束时间(HH:MM)", "startDate": "开始日期(YYYY-MM-DD)", "endDate": "结束日期(YYYY-MM-DD)"}}, "message": "已为您打开添加排课页面，请确认信息后提交"}}

4. 完成课程 (complete_schedule)
   返回: {{"action": "navigate", "path": "/admin/schedules", "query": {{"action": "complete", "id": "排课ID"}}, "storage_data": {{"schedule_id": 排课ID, "content_feedback": "反馈内容(可选)"}}, "message": "已为您打开课程完成确认页面，请确认信息后提交"}}

5. 取消课程 (cancel_schedule)
   返回: {{"action": "navigate", "path": "/admin/schedules", "query": {{"action": "cancel", "id": "排课ID"}}, "storage_data": {{"schedule_id": 排课ID, "cancel_reason": "取消原因(可选)", "send_notification": true/false}}, "message": "已为您打开课程取消确认页面，请确认信息后提交"}}

6. 延期课程 (postpone_schedule)
   返回: {{"action": "navigate", "path": "/admin/schedules", "query": {{"action": "postpone", "id": "排课ID"}}, "storage_data": {{"schedule_id": 排课ID, "start_date": "新开始日期", "end_date": "新结束日期", "start_time": "新开始时间", "end_time": "新结束时间", "postpone_reason": "延期原因"}}, "message": "已为您打开课程延期确认页面，请确认信息后提交"}}

7. 添加导师 (add_teacher)
   返回: {{"action": "navigate", "path": "/admin/teachers", "query": {{"action": "add"}}, "storage_data": {{"teacher_name": "导师姓名", "phone": "电话(可选)", "email": "邮箱(可选)", "title": "职称(可选)", "department": "部门(可选)"}}, "message": "已为您打开添加导师页面，请确认信息后提交"}}

8. 更新导师 (update_teacher)
   返回: {{"action": "navigate", "path": "/admin/teachers", "query": {{"action": "edit", "id": "导师ID"}}, "storage_data": {{"teacher_id": 导师ID, "updates": {{"name": "新姓名(可选)", "phone": "新电话(可选)", "email": "新邮箱(可选)"}}}}, "message": "已为您打开导师编辑页面，请确认修改内容后提交"}}

9. 添加学员 (add_student)
   返回: {{"action": "navigate", "path": "/admin/students", "query": {{"action": "add"}}, "storage_data": {{"student_name": "学员姓名", "phone": "电话(可选)", "email": "邮箱(可选)", "class_ids": [班级ID列表]}}, "message": "已为您打开添加学员页面，请确认信息后提交"}}

10. 更新学员 (update_student)
    返回: {{"action": "navigate", "path": "/admin/students", "query": {{"action": "edit", "id": "学员ID"}}, "storage_data": {{"student_id": 学员ID, "updates": {{"name": "新姓名(可选)", "phone": "新电话(可选)", "email": "新邮箱(可选)"}}}}, "message": "已为您打开学员编辑页面，请确认修改内容后提交"}}

11. 添加班级 (add_class)
    返回: {{"action": "navigate", "path": "/admin/classes", "query": {{"action": "add"}}, "storage_data": {{"class_name": "班级名称", "grade_level": "年级(可选)"}}, "message": "已为您打开添加班级页面，请确认信息后提交"}}

12. 更新班级 (update_class)
    返回: {{"action": "navigate", "path": "/admin/classes", "query": {{"action": "edit", "id": "班级ID"}}, "storage_data": {{"class_id": 班级ID, "updates": {{"name": "新名称(可选)"}}}}, "message": "已为您打开班级编辑页面，请确认修改内容后提交"}}

13. 添加教室 (add_room)
    返回: {{"action": "navigate", "path": "/admin/rooms", "query": {{"action": "add"}}, "storage_data": {{"room_name": "教室名称", "capacity": 容量(可选), "type": "类型(可选)"}}, "message": "已为您打开添加教室页面，请确认信息后提交"}}

14. 更新教室 (update_room)
    返回: {{"action": "navigate", "path": "/admin/rooms", "query": {{"action": "edit", "id": "教室ID"}}, "storage_data": {{"room_id": 教室ID, "updates": {{"name": "新名称(可选)", "capacity": 新容量(可选)}}}}, "message": "已为您打开教室编辑页面，请确认修改内容后提交"}}

15. 添加请假 (add_leave)
    返回: {{"action": "navigate", "path": "/admin/leaves", "query": {{"action": "add"}}, "storage_data": {{"person_name": "人员姓名", "leave_type": "请假类型", "start_date": "开始日期", "end_date": "结束日期", "reason": "请假原因"}}, "message": "已为您打开添加请假页面，请确认信息后提交"}}

16. 添加节假日 (add_holiday)
    返回: {{"action": "navigate", "path": "/admin/holidays", "query": {{"action": "add"}}, "storage_data": {{"holiday_name": "节假日名称", "start_date": "开始日期", "end_date": "结束日期"}}, "message": "已为您打开添加节假日页面，请确认信息后提交"}}

17. 收取费用 (collect_fee)
    返回: {{"action": "navigate", "path": "/admin/feemanagement", "query": {{"action": "collect"}}, "storage_data": {{"student_id": 学员ID, "student_name": "学员姓名", "course_id": 科目ID, "course_name": "科目名称", "amount": 金额, "receivable_amount": 应收金额(可选), "fee_date": "收费日期"}}, "message": "已为您打开收费页面，请确认信息后提交"}}

18. 退费 (refund_fee)
    返回: {{"action": "navigate", "path": "/admin/feemanagement", "query": {{"action": "refund"}}, "storage_data": {{"student_id": 学员ID, "student_name": "学员姓名", "course_id": 科目ID, "course_name": "科目名称", "amount": 金额, "refund_date": "退费日期"}}, "message": "已为您打开退费页面，请确认信息后提交"}}

19. 添加成绩 (add_grade)
    返回: {{"action": "navigate", "path": "/admin/grades", "query": {{"action": "add"}}, "storage_data": {{"student_id": 学员ID, "student_name": "学员姓名", "course_id": 科目ID, "course_name": "科目名称", "score": 分数, "total_score": 总分(可选), "exam_date": "考试日期(可选)", "grade_level": "年级(可选)", "exam_stage": "考试阶段(可选)"}}, "message": "已为您打开添加成绩页面，请确认信息后提交"}}

20. 查询科目列表 (search_courses)
    返回: {{"action": "navigate", "path": "/admin/courses", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "courses"}}, "message": "已为您打开科目列表页面，您可以查看所有科目信息"}}

21. 查询导师列表 (search_teachers)
    返回: {{"action": "navigate", "path": "/admin/teachers", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "teachers"}}, "message": "已为您打开导师列表页面，您可以查看所有导师信息"}}

22. 查询学员列表 (search_students)
    返回: {{"action": "navigate", "path": "/admin/students", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "students"}}, "message": "已为您开学员列表页面，您可以查看所有学员信息"}}

23. 查询班级列表 (search_classes)
    返回: {{"action": "navigate", "path": "/admin/classes", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "classes"}}, "message": "已为您打开班级列表页面，您可以查看所有班级信息"}}

24. 查询教室列表 (search_rooms)
    返回: {{"action": "navigate", "path": "/admin/rooms", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "rooms"}}, "message": "已为您打开教室列表页面，您可以查看所有教室信息"}}

25. 查询课程安排列表 (search_schedules)
    返回: {{"action": "navigate", "path": "/admin/schedules", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "schedules"}}, "message": "已为您打开课程安排列表页面，您可以查看所有排课信息"}}

26. 查询节假日列表 (search_holidays)
    返回: {{"action": "navigate", "path": "/admin/holidays", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "holidays"}}, "message": "已为您打开节假日列表页面，您可以查看所有假日信息"}}

27. 查询课费记录 (search_fees)
    返回: {{"action": "navigate", "path": "/admin/feemanagement", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "fees"}}, "message": "已为您打开课费管理页面，您可以查看所有缴费记录"}}

28. 查询成绩列表 (search_grades)
    返回: {{"action": "navigate", "path": "/admin/grades", "query": {{}}, "storage_data": {{"search_mode": true, "entity_type": "grades"}}, "message": "已为您打开成绩管理页面，您可以查看所有成绩信息"}}

29. 高级关联查询 (advanced_search)
    当用户想要查询某个实体的关联信息时，例如"学员张三的班级"、"导师李四的科目"等
    返回格式根据具体情况而定：
    
    a) 查询学员的班级：
    {{"action": "navigate", "path": "/admin/students", "query": {{"search": "张三", "related_to": "classes"}}, "storage_data": {{"search_mode": true, "source_entity": "student", "source_name": "张三", "target_entity": "classes", "target_path": "/admin/classes", "target_label": "班级列表"}}, "message": "正在查询学员张三的班级列表..."}}
    
    b) 查询导师的科目：
    {{"action": "navigate", "path": "/admin/teachers", "query": {{"search": "李四", "related_to": "courses"}}, "storage_data": {{"search_mode": true, "source_entity": "teacher", "source_name": "李四", "target_entity": "courses", "target_path": "/admin/courses", "target_label": "科目列表"}}, "message": "正在查询导师李四的科目列表..."}}
    
    c) 查询某人在特定日期的排课：
    {{"action": "navigate", "path": "/admin/schedules", "query": {{"filter_by": "student", "filter_value": "张三", "date": "明天"}}, "storage_data": {{"search_mode": true, "entity_type": "student", "entity_name": "张三", "date_filter": "明天", "target_entity": "schedules"}}, "message": "正在查询学员张三在明天的课程安排..."}}
    
    d) 查询实体的详细信息：
    {{"action": "navigate", "path": "/admin/students", "query": {{"search": "张三", "view_detail": "true"}}, "storage_data": {{"search_mode": true, "entity_type": "student", "entity_name": "张三", "auto_view_detail": true}}, "message": "正在查询学员张三的详细信息..."}}

【支持的关联查询类型】
- 学员的：班级、科目、导师、课费、成绩、排课
- 导师的：科目、班级、学员、排课
- 班级的：学员、导师、科目、排课
- 科目的：导师、学员、班级、排课
- 教室的：排课
    
【错误处理】
如果仅仅是缺少可选字段（如电话、邮箱等），请不要返回 error，而是正常返回 navigate 动作，缺失的字段在 storage_data 中留空或设为 null。
只有在以下情况才返回 error：
1. 用户输入完全无意义或与系统功能无关。
2. 用户意图极度模糊，无法从上述29种操作中找到任何匹配项。
3. 缺少最核心的实体信息（用户的指令中包含了"新增"、"修改"、"更改"、"查找"等词汇，但没有提供足够的信息来确定修改的对象和内容。例如：只说了"添加"，没说添加什么）。
4. 用户的指令中包含了矛盾信息（如同时提到"添加"和"删除"同一实体）。
5. 用户的指令中包含了无法识别的专有名词，且无法通过上下文推断其含义。
6. 用户的指令中包含了"删除"，要给出明确提示用户通过智能指令不支持删除操作；如果指令包含删除课程则引导其使用"取消课程"等更合适的操作。

返回格式示例（错误情况）：
{{"action": "error", "message": "我无法理解您的指令，请尝试更清晰的表达，例如：'添加科目数学'"}}

【当前系统中的实体】
- 导师列表: {all_teachers[:100]}
- 科目列表: {all_courses[:100]}
- 学员列表: {all_students[:200]}
- 班级列表: {all_classes[:200]}
- 教室列表: {all_rooms[:50]}

【重要规则】
1. 必须严格按照上述格式返回JSON，不要添加任何额外说明
2. action字段只能是"navigate"或"error"
3. 如果涉及ID但用户未提供，尝试从名称推断，如果无法确定则设为null
4. 日期格式必须是YYYY-MM-DD，时间格式必须是HH:MM
5. 优先参考【参考示例】中的表达方式理解用户意图
6. **对于"添加成绩"等操作，即使缺少总分、日期等非核心字段，只要有了学员、科目和分数，就必须返回 navigate 动作，不要返回 error**
7. **日期处理规则：如果用户只说了"X月X号"而没有说年份，必须使用当前年份（{current_year}年）。例如：今天是{current_year}年，用户说"5月17号"，应该返回"{current_year}-05-17"，而不是其他年份！**

用户输入：{text}

请直接返回JSON（不要包含markdown代码块标记）：
"""
            
            prompt_build_elapsed = time.time() - start_time
            log_operation(db, "智能指令", "DEBUG", f"Prompt构建完成，耗时: {prompt_build_elapsed:.2f}秒, Prompt长度: {len(prompt)}字符", level="DEBUG")
            
            # 严格按照DeepSeek官方文档格式
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            data = {
                'model': model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'stream': False
            }
            
            log_operation(db, "智能指令", "DEBUG", f"开始调用AI API: url={api_url}, model={model}, timeout={timeout}", level="DEBUG")
            api_call_start = time.time()
            
            response = requests.post(api_url, headers=headers, json=data, timeout=timeout)
            
            api_call_elapsed = time.time() - api_call_start
            log_operation(db, "智能指令", "DEBUG", f"AI API响应状态码: {response.status_code}, 耗时: {api_call_elapsed:.2f}秒", level="DEBUG")
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    text_result = result['choices'][0]['message']['content'].strip()
                    
                    # 移除可能的markdown代码块标记
                    if text_result.startswith('```json'):
                        text_result = text_result[7:]
                    if text_result.startswith('```'):
                        text_result = text_result[3:]
                    if text_result.endswith('```'):
                        text_result = text_result[:-3]
                    text_result = text_result.strip()
                    
                    try:
                        parsed = json.loads(text_result)
                        
                        # 验证返回的数据结构是否有效
                        if not isinstance(parsed, dict):
                            log_operation(db, "智能指令", "DEBUG", f"AI返回的不是有效的字典: {parsed}", level="WARNING")
                            return None
                        
                        if 'action' not in parsed:
                            log_operation(db, "智能指令", "DEBUG", f"AI返回的数据缺少action字段: {parsed}", level="WARNING")
                            return None
                        
                        # 如果是navigate操作，确保有必要的字段
                        if parsed['action'] == 'navigate':
                            if 'path' not in parsed or 'storage_data' not in parsed:
                                log_operation(db, "智能指令", "DEBUG", f"AI返回的navigate操作缺少必要字段: {parsed}", level="WARNING")
                                return None
                            
                            # 如果storage_data中有startDate但没有dayOfWeek，自动计算星期几
                            storage_data = parsed.get('storage_data', {})
                            if storage_data and 'startDate' in storage_data and not storage_data.get('dayOfWeek'):
                                try:
                                    from datetime import datetime as dt_datetime
                                    start_date = dt_datetime.strptime(storage_data['startDate'], '%Y-%m-%d').date()
                                    # Python weekday(): 0=周一, 6=周日
                                    # 我们需要: 1=周一, 7=周日
                                    day_of_week = start_date.weekday() + 1
                                    storage_data['dayOfWeek'] = day_of_week
                                    storage_data['day_of_week'] = day_of_week
                                    log_operation(db, "智能指令", "DEBUG", f"根据startDate {storage_data['startDate']} 自动计算星期几: {day_of_week}", level="DEBUG")
                                except Exception as e:
                                    log_operation(db, "智能指令", "DEBUG", f"计算星期几失败: {e}", level="WARNING")

                        total_elapsed = time.time() - start_time
                        log_operation(db, "智能指令", "INFO", f"AI解析成功，总耗时: {total_elapsed:.2f}秒")
                        return parsed
                        
                    except json.JSONDecodeError as e:
                        log_operation(db, "智能指令", "WARNING", f"JSON解析失败: {e}, 原始内容: {text_result[:200]}")
                        # 尝试从文本中提取JSON
                        json_match = re.search(r'\{.*\}', text_result, re.DOTALL)
                        if json_match:
                            try:
                                return json.loads(json_match.group())
                            except:
                                pass
                        return None
                else:
                    log_operation(db, "智能指令", "WARNING", f"AI响应中没有choices: {result}")
                    return None
            else:
                log_operation(db, "智能指令", "ERROR", f"AI API请求失败，状态码: {response.status_code}, 响应: {response.text[:200]}")
                return None
                
        except Exception as e:
            total_elapsed = time.time() - start_time
            log_operation(db, "智能指令", "ERROR", f"AI解析异常: {e}, 总耗时: {total_elapsed:.2f}秒")
            import traceback
            traceback.print_exc()
            return None

    def _parse_search_courses(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询科目指令"""
        return {
            'action': 'navigate',
            'path': '/admin/courses',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'courses'
            },
            'message': '已为您打开科目列表页面，您可以查看所有科目信息'
        }
    
    def _parse_search_teachers(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询导师指令"""
        return {
            'action': 'navigate',
            'path': '/admin/teachers',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'teachers'
            },
            'message': '已为您打开导师列表页面，您可以查看所有导师信息'
        }
    
    def _parse_search_students(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询学员指令"""
        return {
            'action': 'navigate',
            'path': '/admin/students',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'students'
            },
            'message': '已为您开学员列表页面，您可以查看所有学员信息'
        }
    
    def _parse_search_classes(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询班级指令"""
        return {
            'action': 'navigate',
            'path': '/admin/classes',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'classes'
            },
            'message': '已为您打开班级列表页面，您可以查看所有班级信息'
        }
    
    def _parse_search_rooms(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询教室指令"""
        return {
            'action': 'navigate',
            'path': '/admin/rooms',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'rooms'
            },
            'message': '已为您打开教室列表页面，您可以查看所有教室信息'
        }
    
    def _parse_search_schedules(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询课程安排指令"""
        return {
            'action': 'navigate',
            'path': '/admin/schedules',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'schedules'
            },
            'message': '已为您打开课程安排列表页面，您可以查看所有排课信息'
        }
    
    def _parse_search_holidays(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询假日指令"""
        return {
            'action': 'navigate',
            'path': '/admin/holidays',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'holidays'
            },
            'message': '已为您打开节假日列表页面，您可以查看所有假日信息'
        }
    
    def _parse_search_fees(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询课费指令"""
        return {
            'action': 'navigate',
            'path': '/admin/fees',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'fees'
            },
            'message': '已为您打开课费管理页面，您可以查看所有缴费记录'
        }
    
    def _parse_search_grades(self, match, text, db) -> Optional[Dict[str, Any]]:
        """解析查询成绩指令"""
        return {
            'action': 'navigate',
            'path': '/admin/grades',
            'query': {},
            'storage_data': {
                'search_mode': True,
                'entity_type': 'grades'
            },
            'message': '已为您打开成绩管理页面，您可以查看所有成绩信息'
        }
    
    def _parse_advanced_search(self, match, text, db) -> Optional[Dict[str, Any]]:
        """
        解析高级搜索指令 - 支持复杂的自然语言关联查询
        
        支持的查询模式：
        1. 学员张三的班级 → 查询学员张三，并显示其所属班级
        2. 导师李四的科目 → 查询导师李四教的科目
        3. 班级1v1的学员 → 查询班级1v1的所有学员
        4. 科目数学的排课 → 查询科目数学的所有排课
        5. 学员张三在明天的排课 → 查询学员张三明天的课程安排
        """
        text_lower = text.lower()
        
        # ========== 模式1：查询X的Y（关联查询）==========
        # 提取实体名称和关联类型
        entity_patterns = [
            # 学员相关
            (r'(?:学员|学生)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(班级)', 'student', 'classes'),
            (r'(?:学员|学生)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:科目|课程)', 'student', 'courses'),
            (r'(?:学员|学生)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:导师|老师)', 'student', 'teachers'),
            (r'(?:学员|学生)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:课费|费用|缴费)', 'student', 'fees'),
            (r'(?:学员|学生)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:成绩|分数)', 'student', 'grades'),
            (r'(?:学员|学生)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:排课|课程安排|课表)', 'student', 'schedules'),
            
            # 导师相关
            (r'(?:导师|老师|教师)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所教)\s*(?:科目|课程)', 'teacher', 'courses'),
            (r'(?:导师|老师|教师)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所教)\s*(班级)', 'teacher', 'classes'),
            (r'(?:导师|老师|教师)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所教)\s*(?:学员|学生)', 'teacher', 'students'),
            (r'(?:导师|老师|教师)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所教)\s*(?:排课|课程安排|课表)', 'teacher', 'schedules'),
            
            # 班级相关
            (r'(?:班级)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:学员|学生)', 'class', 'students'),
            (r'(?:班级)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:导师|老师)', 'class', 'teachers'),
            (r'(?:班级)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:科目|课程)', 'class', 'courses'),
            (r'(?:班级)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:排课|课程安排|课表)', 'class', 'schedules'),
            
            # 科目相关
            (r'(?:科目|课程)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:导师|老师)', 'course', 'teachers'),
            (r'(?:科目|课程)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:学员|学生)', 'course', 'students'),
            (r'(?:科目|课程)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(班级)', 'course', 'classes'),
            (r'(?:科目|课程)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:排课|课程安排|课表)', 'course', 'schedules'),
            
            # 教室相关
            (r'(?:教室|房间)\s*([^\s的，,]+)\s*(?:相关的|关联的|的|所属)\s*(?:排课|课程安排|课表)', 'room', 'schedules'),
        ]
        
        for pattern, source_entity, target_entity in entity_patterns:
            match_result = re.search(pattern, text)
            if match_result:
                entity_name = match_result.group(1).strip()
                
                # 构建导航数据
                navigation_map = {
                    'student': {'path': '/admin/students', 'label': '学员'},
                    'teacher': {'path': '/admin/teachers', 'label': '导师'},
                    'class': {'path': '/admin/classes', 'label': '班级'},
                    'course': {'path': '/admin/courses', 'label': '科目'},
                    'room': {'path': '/admin/rooms', 'label': '教室'}
                }
                
                target_map = {
                    'students': {'path': '/admin/students', 'label': '学员列表'},
                    'teachers': {'path': '/admin/teachers', 'label': '导师列表'},
                    'classes': {'path': '/admin/classes', 'label': '班级列表'},
                    'courses': {'path': '/admin/courses', 'label': '科目列表'},
                    'schedules': {'path': '/admin/schedules', 'label': '课程安排列表'},
                    'fees': {'path': '/admin/feemanagement', 'label': '课费记录'},
                    'grades': {'path': '/admin/grades', 'label': '成绩列表'}
                }
                
                source_info = navigation_map.get(source_entity, {})
                target_info = target_map.get(target_entity, {})
                
                return {
                    'action': 'navigate',
                    'path': source_info['path'],
                    'query': {
                        'search': entity_name,
                        'related_to': target_entity
                    },
                    'storage_data': {
                        'search_mode': True,
                        'source_entity': source_entity,
                        'source_name': entity_name,
                        'target_entity': target_entity,
                        'target_path': target_info['path'],
                        'target_label': target_info['label']
                    },
                    'message': f'正在查询{source_info["label"]}"{entity_name}"的{target_info["label"]}...'
                }
        
        # ========== 模式2：带时间条件的查询 ==========
        time_pattern = r'(?:查询|搜索|查找|检索)(.+?)(?:在|于)\s*(今天|明天|后天|\d{4}-\d{2}-\d{2}|\d+[天后])\s*(?:的|的)(?:排课|课程安排|课表)'
        time_match = re.search(time_pattern, text)
        if time_match:
            person_or_class = time_match.group(1).strip()
            date_str = time_match.group(2).strip()
            
            # 判断是学员、导师还是班级
            entity_type = 'student'
            if '导师' in text or '老师' in text:
                entity_type = 'teacher'
            elif '班级' in text:
                entity_type = 'class'
            
            return {
                'action': 'navigate',
                'path': '/admin/schedules',
                'query': {
                    'filter_by': entity_type,
                    'filter_value': person_or_class,
                    'date': date_str
                },
                'storage_data': {
                    'search_mode': True,
                    'entity_type': entity_type,
                    'entity_name': person_or_class,
                    'date_filter': date_str,
                    'target_entity': 'schedules'
                },
                'message': f'正在查询"{person_or_class}"在{date_str}的课程安排...'
            }
        
        # ========== 模式3：通用信息查询 ==========
        info_pattern = r'(?:查询|搜索|查找|检索)(?:学员|学生|导师|老师|教师|班级|科目|课程|教室|房间)\s*(.+?)(?:的|的)(?:信息|详情|资料)'
        info_match = re.search(info_pattern, text)
        if info_match:
            entity_name = info_match.group(1).strip()
            
            # 判断实体类型
            entity_type = 'student'
            path = '/admin/students'
            label = '学员'
            
            if '导师' in text or '老师' in text or '教师' in text:
                entity_type = 'teacher'
                path = '/admin/teachers'
                label = '导师'
            elif '班级' in text:
                entity_type = 'class'
                path = '/admin/classes'
                label = '班级'
            elif '科目' in text or '课程' in text:
                entity_type = 'course'
                path = '/admin/courses'
                label = '科目'
            elif '教室' in text or '房间' in text:
                entity_type = 'room'
                path = '/admin/rooms'
                label = '教室'
            
            return {
                'action': 'navigate',
                'path': path,
                'query': {
                    'search': entity_name,
                    'view_detail': 'true'
                },
                'storage_data': {
                    'search_mode': True,
                    'entity_type': entity_type,
                    'entity_name': entity_name,
                    'auto_view_detail': True
                },
                'message': f'正在查询{label}"{entity_name}"的详细信息...'
            }
        
        # 如果以上模式都不匹配，尝试通用搜索
        return {
            'action': 'navigate',
            'path': '/admin/students',
            'query': {
                'search': text.replace('查询', '').replace('搜索', '').replace('查找', '').replace('检索', '').strip()
            },
            'storage_data': {
                'search_mode': True,
                'entity_type': 'students',
                'raw_query': text
            },
            'message': '正在执行智能搜索...'
        }

# 4. 命令执行器 - 执行解析后的指令        
class CommandExecutor:
    """命令执行器 - 执行解析后的指令"""
    
    def __init__(self, db: Session, user_id: int = None, username: str = "system"):
        self.db = db
        self.user_id = user_id
        self.username = username
    
    def execute(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行解析后的指令
        
        Args:
            parsed_result: 解析结果
            
        Returns:
            执行结果
        """
        action = parsed_result.get('action')
        
        if not action:
            return {'success': False, 'message': '无法识别操作类型'}
        
        # 特殊处理：导航操作不需要后端执行，直接返回成功
        if action == 'navigate':
            return {
                'success': True,
                'message': parsed_result.get('message', '正在打开页面...'),
                'data': parsed_result
            }
        
        # 特殊处理：错误信息也不需要执行
        if action == 'error':
            return {
                'success': False,
                'message': parsed_result.get('message', '解析失败')
            }
        
        # 检查是否有缺失字段
        missing_fields = parsed_result.get('missing_fields')
        if missing_fields:
            field_names = {
                'content_feedback': '课程内容反馈（格式：内容|作业|注意）',
                'cancel_reason': '取消原因',
                'postpone_reason': '延期原因',
                'start_date': '开始日期',
                'end_date': '结束日期',
                'start_time': '开始时间',
                'end_time': '结束时间',
                'person_name': '人员姓名',
                'course_name': '科目名称',
                'amount': '金额',
                'receivable_amount': '应收金额',
                'student_name': '学员姓名',
                'score': '成绩',
                'total_score': '总分',
                'grade_level': '年级',
                'exam_stage': '考试阶段',
                'class_name': '班级名称',
                'teacher_name': '导师姓名',
                'room_name': '教室名称',
                'day_of_week': '星期几',
                'date': '日期'
            }
            missing_desc = [field_names.get(f, f) for f in missing_fields]
            return {
                'success': False, 
                'message': f'缺少必要信息：{", ".join(missing_desc)}',
                'missing_fields': missing_fields
            }
        
        # 根据action分发到不同的执行方法
        executor_map = {
            'add_course': self._execute_add_course,
            'update_course': self._execute_update_course,
            'complete_schedule': self._execute_complete_schedule,
            'cancel_schedule': self._execute_cancel_schedule,
            'postpone_schedule': self._execute_postpone_schedule,
            'add_teacher': self._execute_add_teacher,
            'update_teacher': self._execute_update_teacher,
            'add_student': self._execute_add_student,
            'update_student': self._execute_update_student,
            'add_class': self._execute_add_class,
            'update_class': self._execute_update_class,
            'add_room': self._execute_add_room,
            'update_room': self._execute_update_room,
            'add_leave': self._execute_add_leave,
            'add_holiday': self._execute_add_holiday,
            'collect_fee': self._execute_collect_fee,
            'refund_fee': self._execute_refund_fee,
            'add_grade': self._execute_add_grade,
            'create_schedule': self._execute_create_schedule,
        }
        
        executor = executor_map.get(action)
        if executor:
            try:
                return executor(parsed_result)
            except Exception as e:
                self.db.rollback()
                return {'success': False, 'message': f'执行失败: {str(e)}'}
        else:
            return {'success': False, 'message': f'不支持的操作类型: {action}'}
    
    def _generate_code(self, model_class, prefix: str) -> str:
        """自动生成编码 - 查询数据库当前最大代码并+1"""
        import re
        
        # 获取所有非空代码
        all_codes = self.db.query(model_class.code).filter(
            model_class.code.isnot(None),
            model_class.code != ''
        ).all()
        
        if not all_codes or not any(code[0] for code in all_codes):
            # 如果没有代码，使用默认格式
            return f"{prefix}001"
        
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
            # 如果无法提取数字，使用默认格式
            return f"{prefix}001"
        
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
            # 如果无法解析，使用默认格式
            return f"{prefix}001"
    
    def _find_similar_items(self, model_class, name_field: str, search_name: str, threshold: float = 0.6) -> List:
        """查找相似的项目"""
        all_items = self.db.query(model_class).all()
        similar_items = []
        
        for item in all_items:
            item_name = getattr(item, name_field, '')
            if self._calculate_similarity(search_name, item_name) >= threshold:
                similar_items.append({
                    'id': item.id,
                    'name': item_name,
                    'similarity': self._calculate_similarity(search_name, item_name)
                })
        
        # 按相似度排序
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_items[:5]  # 返回最相似的5个
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度（简单实现）"""
        if not str1 or not str2:
            return 0.0
        
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        # 如果完全匹配
        if str1_lower == str2_lower:
            return 1.0
        
        # 如果包含关系
        if str1_lower in str2_lower or str2_lower in str1_lower:
            return 0.8
        
        # 简单的字符重叠度
        set1 = set(str1_lower)
        set2 = set(str2_lower)
        intersection = set1 & set2
        union = set1 | set2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _execute_add_course(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加科目"""
        course_name = params.get('course_name')
        teacher_name = params.get('teacher_name')
        priority = params.get('priority', 0)
        
        if not course_name:
            return {'success': False, 'message': '缺少科目名称'}
        
        # 检查科目是否已存在
        existing = self.db.query(Course).filter(Course.name == course_name).first()
        if existing:
            return {'success': False, 'message': f'科目"{course_name}"已存在'}
        
        # 生成编码
        code = self._generate_code(Course, "COURSE")
        
        # 创建科目
        new_course = Course(
            code=code,
            name=course_name,
            priority=priority
        )
        
        # 如果指定了导师，查找或创建导师
        created_teachers = []
        if teacher_name:
            teacher = self.db.query(Teacher).filter(Teacher.name == teacher_name).first()
            if not teacher:
                # 导师不存在，查找相似导师
                similar_teachers = self._find_similar_items(Teacher, 'name', teacher_name)
                if similar_teachers:
                    return {
                        'success': False,
                        'message': f'未找到导师"{teacher_name}"，但找到以下相似导师：{", ".join([t["name"] for t in similar_teachers])}，请确认是否正确',
                        'similar_items': similar_teachers,
                        'need_confirmation': True
                    }
                else:
                    # 没有相似导师，询问是否创建
                    return {
                        'success': False,
                        'message': f'导师"{teacher_name}"不存在，是否需要先创建该导师？',
                        'need_create_teacher': True,
                        'teacher_name': teacher_name
                    }
            new_course.teachers.append(teacher)
        
        self.db.add(new_course)
        self.db.commit()
        self.db.refresh(new_course)
        
        log_operation(self.db, "科目管理", "添加科目", f"通过智能指令添加科目: {course_name}", user=self.username)
        
        result_msg = f'成功添加科目: {course_name}'
        if created_teachers:
            result_msg += f'，并创建了导师: {", ".join(created_teachers)}'
        
        return {
            'success': True,
            'message': result_msg,
            'data': {'id': new_course.id, 'name': new_course.name, 'code': new_course.code}
        }
    
    def _execute_update_course(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新科目"""
        course_identifier = params.get('course_identifier')
        updates = params.get('updates', {})
        
        if not course_identifier:
            return {'success': False, 'message': '缺少科目标识'}
        
        # 尝试查找科目
        course = None
        if course_identifier.isdigit():
            course = self.db.query(Course).filter(Course.id == int(course_identifier)).first()
        else:
            course = self.db.query(Course).filter(Course.name == course_identifier).first()
        
        if not course:
            # 查找相似科目
            similar_courses = self._find_similar_items(Course, 'name', course_identifier)
            if similar_courses:
                return {
                    'success': False,
                    'message': f'未找到科目"{course_identifier}"，但找到以下相似科目：{", ".join([c["name"] for c in similar_courses])}',
                    'similar_items': similar_courses,
                    'need_confirmation': True
                }
            else:
                return {'success': False, 'message': f'科目"{course_identifier}"不存在'}
        
        # 执行更新
        update_fields = []
        if 'name' in updates:
            course.name = updates['name']
            update_fields.append('名称')
        if 'priority' in updates:
            course.priority = updates['priority']
            update_fields.append('优先级')
        if 'teacher_name' in updates:
            teacher = self.db.query(Teacher).filter(Teacher.name == updates['teacher_name']).first()
            if teacher:
                course.teachers = [teacher]
                update_fields.append('导师')
            else:
                return {'success': False, 'message': f'导师"{updates["teacher_name"]}"不存在'}
        
        self.db.commit()
        
        log_operation(self.db, "科目管理", "更新科目", f"更新科目: {course.name} ({', '.join(update_fields)})", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功更新科目: {course.name}',
            'data': {'id': course.id, 'name': course.name}
        }
    
    def _execute_complete_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行完成课程"""
        schedule_id = params.get('schedule_id')
        content_feedback = params.get('content_feedback')
        
        if not schedule_id:
            return {'success': False, 'message': '缺少排课ID'}
        
        try:
            schedule_id_int = int(schedule_id)
        except ValueError:
            return {'success': False, 'message': '排课ID必须是数字'}
        
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id_int).first()
        
        if not schedule:
            return {'success': False, 'message': f'未找到排课记录: {schedule_id}'}
        
        if not content_feedback:
            return {
                'success': False,
                'message': '请提供课程内容反馈（格式：内容|作业|注意）',
                'missing_fields': ['content_feedback']
            }
        
        # 更新状态和反馈
        schedule.execution_status = 'completed'
        schedule.content_feedback = content_feedback
        
        # 获取班级的活跃学员并设置默认出勤状态
        from routers.schedules import get_students_by_class
        active_students = get_students_by_class(self.db, schedule.class_id, is_active=True)
        
        for student in active_students:
            # 检查是否有请假记录
            from datetime import datetime as dt_datetime
            start_datetime = dt_datetime.combine(schedule.start_date, dt_datetime.min.time())
            end_datetime = dt_datetime.combine(schedule.end_date, dt_datetime.max.time())
            
            student_leave = self.db.query(Leave).filter(
                Leave.leave_type == "student",
                Leave.student_id == student.id,
                Leave.start_date <= end_datetime,
                Leave.end_date >= start_datetime
            ).first()
            
            default_status = 'leave' if student_leave else 'present'
            
            # 更新或创建学员出勤记录
            from sqlalchemy import update as sql_update
            from models import schedule_student
            stmt = sql_update(schedule_student).where(
                (schedule_student.c.schedule_id == schedule_id_int) & 
                (schedule_student.c.student_id == student.id)
            ).values(
                attendance_status=default_status,
                absence_reason='已有请假记录' if student_leave else None
            )
            result = self.db.execute(stmt)
            
            if result.rowcount == 0:
                association = schedule_student.insert().values(
                    schedule_id=schedule_id_int,
                    student_id=student.id,
                    attendance_status=default_status,
                    absence_reason='已有请假记录' if student_leave else None
                )
                self.db.execute(association)
        
        self.db.commit()
        
        # 消耗课时
        try:
            from routers.fees import consume_hours_with_attendance
            from routers.auth import User
            # 创建一个临时用户对象用于权限检查
            temp_user = User(id=self.user_id, username="system", role="system_admin")
            consume_hours_with_attendance(schedule_id_int, self.db, temp_user)
        except Exception as e:
            log_operation(self.db, "课程安排", "完训", f"消耗课时失败: {str(e)}", user="system", level="ERROR")
        
        log_operation(self.db, "课程安排", "完成课程", f"完成排课ID: {schedule_id}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'已完成排课: {schedule_id}'
        }
    
    def _execute_cancel_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行取消课程"""
        schedule_id = params.get('schedule_id')
        cancel_reason = params.get('cancel_reason')
        
        if not schedule_id:
            return {'success': False, 'message': '缺少排课ID'}
        
        if not cancel_reason:
            return {
                'success': False,
                'message': '请提供取消原因',
                'missing_fields': ['cancel_reason']
            }
        
        try:
            schedule_id_int = int(schedule_id)
        except ValueError:
            return {'success': False, 'message': '排课ID必须是数字'}
        
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id_int).first()
        
        if not schedule:
            return {'success': False, 'message': f'未找到排课记录: {schedule_id}'}
        
        schedule.execution_status = 'cancelled'
        schedule.cancel_reason = cancel_reason
        self.db.commit()
        
        log_operation(self.db, "课程安排", "取消课程", f"取消排课ID: {schedule_id}, 原因: {cancel_reason}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'已取消排课: {schedule_id}'
        }
    
    def _execute_postpone_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行延期课程"""
        schedule_id = params.get('schedule_id')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        start_time = params.get('start_time')
        end_time = params.get('end_time')
        postpone_reason = params.get('postpone_reason')
        
        if not schedule_id:
            return {'success': False, 'message': '缺少排课ID'}
        
        try:
            schedule_id_int = int(schedule_id)
        except ValueError:
            return {'success': False, 'message': '排课ID必须是数字'}
        
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id_int).first()
        
        if not schedule:
            return {'success': False, 'message': f'未找到排课记录: {schedule_id}'}
        
        # 解析日期
        from datetime import datetime as dt_datetime
        try:
            start_date_obj = dt_datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = dt_datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'message': '日期格式错误，请使用 YYYY-MM-DD 格式'}
        
        # 更新原课程状态
        schedule.execution_status = 'postponed'
        schedule.postpone_reason = postpone_reason
        
        # 计算星期几
        day_of_week = start_date_obj.weekday() + 1 if start_date_obj.weekday() != 6 else 7
        
        # 创建新的排课
        new_schedule = Schedule(
            course_id=schedule.course_id,
            teacher_id=schedule.teacher_id,
            class_id=schedule.class_id,
            room_id=schedule.room_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            start_date=start_date_obj,
            end_date=end_date_obj,
            content_feedback=schedule.content_feedback,
            schedule_type=schedule.schedule_type  # 继承原课程的类型
        )
        self.db.add(new_schedule)
        self.db.flush()  # 先flush获取new_schedule.id
        
        # 复制原课程的学员关联到新排课
        for student in schedule.scheduled_students:
            new_schedule.scheduled_students.append(student)
        
        self.db.commit()
        self.db.refresh(new_schedule)
        
        log_operation(self.db, "课程安排", "延期课程", f"延期排课ID: {schedule_id} 到新日期 {start_date}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'已延期排课: {schedule_id}，新排课ID: {new_schedule.id}',
            'data': {'original_schedule_id': schedule.id, 'new_schedule_id': new_schedule.id}
        }
    
    def _execute_add_teacher(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加导师"""
        name = params.get('name')
        phone = params.get('phone')
        email = params.get('email')
        title = params.get('title')
        department = params.get('department')
        
        if not name:
            return {'success': False, 'message': '缺少导师姓名'}
        
        # 检查导师是否已存在
        existing = self.db.query(Teacher).filter(Teacher.name == name).first()
        if existing:
            return {'success': False, 'message': f'导师"{name}"已存在'}
        
        # 生成编码
        code = self._generate_code(Teacher, "TEACHER")
        
        new_teacher = Teacher(
            code=code,
            name=name,
            contact_phone=phone,
            email=email,
            title=title,
            department=department,
            is_active=True
        )
        
        self.db.add(new_teacher)
        self.db.commit()
        self.db.refresh(new_teacher)
        
        log_operation(self.db, "导师管理", "添加导师", f"通过智能指令添加导师: {name}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功添加导师: {name}',
            'data': {'id': new_teacher.id, 'name': new_teacher.name, 'code': new_teacher.code}
        }
    
    def _execute_update_teacher(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新导师"""
        teacher_identifier = params.get('teacher_identifier')
        updates = params.get('updates', {})
        
        if not teacher_identifier:
            return {'success': False, 'message': '缺少导师标识'}
        
        # 尝试查找导师
        teacher = None
        if teacher_identifier.isdigit():
            teacher = self.db.query(Teacher).filter(Teacher.id == int(teacher_identifier)).first()
        else:
            teacher = self.db.query(Teacher).filter(Teacher.name == teacher_identifier).first()
        
        if not teacher:
            similar_teachers = self._find_similar_items(Teacher, 'name', teacher_identifier)
            if similar_teachers:
                return {
                    'success': False,
                    'message': f'未找到导师"{teacher_identifier}"，但找到以下相似导师：{", ".join([t["name"] for t in similar_teachers])}',
                    'similar_items': similar_teachers,
                    'need_confirmation': True
                }
            else:
                return {'success': False, 'message': f'导师"{teacher_identifier}"不存在'}
        
        # 执行更新
        update_fields = []
        for field, value in updates.items():
            if hasattr(teacher, field):
                setattr(teacher, field, value)
                update_fields.append(field)
        
        self.db.commit()
        
        log_operation(self.db, "导师管理", "更新导师", f"更新导师: {teacher.name} ({', '.join(update_fields)})", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功更新导师: {teacher.name}',
            'data': {'id': teacher.id, 'name': teacher.name}
        }
    
    def _execute_add_student(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加学员"""
        name = params.get('name')
        phone = params.get('phone')
        school = params.get('school')
        grade = params.get('grade')
        contact_person = params.get('contact_person')
        email = params.get('email')
        class_name = params.get('class_name')
        
        if not name:
            return {'success': False, 'message': '缺少学员姓名'}
        
        # 检查学员是否已存在
        existing = self.db.query(Student).filter(Student.name == name).first()
        if existing:
            return {'success': False, 'message': f'学员"{name}"已存在'}
        
        # 生成编码
        code = self._generate_code(Student, "STUDENT")
        
        new_student = Student(
            code=code,
            name=name,
            contact_phone=phone,
            school=school,
            grade=grade,
            contact_person=contact_person,
            email=email,
            is_active=True
        )
        
        # 如果指定了班级，查找并关联
        if class_name:
            class_obj = self.db.query(ClassModel).filter(ClassModel.name == class_name).first()
            if class_obj:
                new_student.classes.append(class_obj)
            else:
                # 班级不存在，查找相似班级
                similar_classes = self._find_similar_items(ClassModel, 'name', class_name)
                if similar_classes:
                    return {
                        'success': False,
                        'message': f'未找到班级"{class_name}"，但找到以下相似班级：{", ".join([c["name"] for c in similar_classes])}',
                        'similar_items': similar_classes,
                        'need_confirmation': True
                    }
                else:
                    return {
                        'success': False,
                        'message': f'班级"{class_name}"不存在，是否需要先创建该班级？',
                        'need_create_class': True,
                        'class_name': class_name
                    }
        
        self.db.add(new_student)
        self.db.commit()
        self.db.refresh(new_student)
        
        log_operation(self.db, "学员管理", "添加学员", f"通过智能指令添加学员: {name}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功添加学员: {name}',
            'data': {'id': new_student.id, 'name': new_student.name, 'code': new_student.code}
        }
    
    def _execute_update_student(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新学员"""
        student_identifier = params.get('student_identifier')
        updates = params.get('updates', {})
        
        if not student_identifier:
            return {'success': False, 'message': '缺少学员标识'}
        
        # 尝试查找学员
        student = None
        if student_identifier.isdigit():
            student = self.db.query(Student).filter(Student.id == int(student_identifier)).first()
        else:
            student = self.db.query(Student).filter(Student.name == student_identifier).first()
        
        if not student:
            similar_students = self._find_similar_items(Student, 'name', student_identifier)
            if similar_students:
                return {
                    'success': False,
                    'message': f'未找到学员"{student_identifier}"，但找到以下相似学员：{", ".join([s["name"] for s in similar_students])}',
                    'similar_items': similar_students,
                    'need_confirmation': True
                }
            else:
                return {'success': False, 'message': f'学员"{student_identifier}"不存在'}
        
        # 执行更新
        update_fields = []
        for field, value in updates.items():
            if hasattr(student, field):
                setattr(student, field, value)
                update_fields.append(field)
        
        self.db.commit()
        
        log_operation(self.db, "学员管理", "更新学员", f"更新学员: {student.name} ({', '.join(update_fields)})", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功更新学员: {student.name}',
            'data': {'id': student.id, 'name': student.name}
        }
    
    def _execute_add_class(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加班级"""
        name = params.get('name')
        description = params.get('description')
        teacher_name = params.get('teacher_name')
        wechat_webhook = params.get('wechat_webhook')
        
        if not name:
            return {'success': False, 'message': '缺少班级名称'}
        
        # 检查班级是否已存在
        existing = self.db.query(ClassModel).filter(ClassModel.name == name).first()
        if existing:
            return {'success': False, 'message': f'班级"{name}"已存在'}
        
        # 生成编码
        code = self._generate_code(ClassModel, "CLASS")
        
        new_class = ClassModel(
            code=code,
            name=name,
            description=description,
            wechat_webhook=wechat_webhook,
            is_active=True
        )
        
        self.db.add(new_class)
        self.db.commit()
        self.db.refresh(new_class)
        
        log_operation(self.db, "班级管理", "添加班级", f"通过智能指令添加班级: {name}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功添加班级: {name}',
            'data': {'id': new_class.id, 'name': new_class.name, 'code': new_class.code}
        }
    
    def _execute_update_class(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新班级"""
        class_identifier = params.get('class_identifier')
        updates = params.get('updates', {})
        
        if not class_identifier:
            return {'success': False, 'message': '缺少班级标识'}
        
        # 尝试查找班级
        class_obj = None
        if class_identifier.isdigit():
            class_obj = self.db.query(ClassModel).filter(ClassModel.id == int(class_identifier)).first()
        else:
            class_obj = self.db.query(ClassModel).filter(ClassModel.name == class_identifier).first()
        
        if not class_obj:
            similar_classes = self._find_similar_items(ClassModel, 'name', class_identifier)
            if similar_classes:
                return {
                    'success': False,
                    'message': f'未找到班级"{class_identifier}"，但找到以下相似班级：{", ".join([c["name"] for c in similar_classes])}',
                    'similar_items': similar_classes,
                    'need_confirmation': True
                }
            else:
                return {'success': False, 'message': f'班级"{class_identifier}"不存在'}
        
        # 执行更新
        update_fields = []
        for field, value in updates.items():
            if hasattr(class_obj, field):
                setattr(class_obj, field, value)
                update_fields.append(field)
        
        self.db.commit()
        
        log_operation(self.db, "班级管理", "更新班级", f"更新班级: {class_obj.name} ({', '.join(update_fields)})", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功更新班级: {class_obj.name}',
            'data': {'id': class_obj.id, 'name': class_obj.name}
        }
    
    def _execute_add_room(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加教室"""
        name = params.get('name')
        location = params.get('location')
        capacity = params.get('capacity', 30)
        facilities = params.get('facilities', "普通")
        facility_details = params.get('facility_details', "")
        
        if not name:
            return {'success': False, 'message': '缺少教室名称'}
        
        # 检查教室是否已存在
        existing = self.db.query(Room).filter(Room.name == name).first()
        if existing:
            return {'success': False, 'message': f'教室"{name}"已存在'}
        
        # 生成编码
        code = self._generate_code(Room, "ROOM")
        
        new_room = Room(
            code=code,
            name=name,
            location=location,
            capacity=capacity,
            facilities=facilities,
            facility_details=facility_details,
            is_active=True
        )
        
        self.db.add(new_room)
        self.db.commit()
        self.db.refresh(new_room)
        
        log_operation(self.db, "教室管理", "添加教室", f"通过智能指令添加教室: {name}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功添加教室: {name}',
            'data': {'id': new_room.id, 'name': new_room.name, 'code': new_room.code}
        }
    
    def _execute_update_room(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行更新教室"""
        room_identifier = params.get('room_identifier')
        updates = params.get('updates', {})
        
        if not room_identifier:
            return {'success': False, 'message': '缺少教室标识'}
        
        # 尝试查找教室
        room = None
        if room_identifier.isdigit():
            room = self.db.query(Room).filter(Room.id == int(room_identifier)).first()
        else:
            room = self.db.query(Room).filter(Room.name == room_identifier).first()
        
        if not room:
            similar_rooms = self._find_similar_items(Room, 'name', room_identifier)
            if similar_rooms:
                return {
                    'success': False,
                    'message': f'未找到教室"{room_identifier}"，但找到以下相似教室：{", ".join([r["name"] for r in similar_rooms])}',
                    'similar_items': similar_rooms,
                    'need_confirmation': True
                }
            else:
                return {'success': False, 'message': f'教室"{room_identifier}"不存在'}
        
        # 执行更新
        update_fields = []
        for field, value in updates.items():
            if hasattr(room, field):
                setattr(room, field, value)
                update_fields.append(field)
        
        self.db.commit()
        
        log_operation(self.db, "教室管理", "更新教室", f"更新教室: {room.name} ({', '.join(update_fields)})", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功更新教室: {room.name}',
            'data': {'id': room.id, 'name': room.name}
        }
    
    def _execute_add_leave(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加请假"""
        person_name = params.get('person_name')
        is_teacher = params.get('is_teacher', False)
        start_date_str = params.get('start_date')
        end_date_str = params.get('end_date')
        reason = params.get('reason', '个人原因')
        
        if not person_name:
            return {'success': False, 'message': '缺少人员姓名'}
        
        if not start_date_str or not end_date_str:
            return {
                'success': False,
                'message': '请提供开始日期和结束日期',
                'missing_fields': ['start_date', 'end_date']
            }
        
        # 查找人员
        if is_teacher:
            person = self.db.query(Teacher).filter(Teacher.name == person_name).first()
        else:
            person = self.db.query(Student).filter(Student.name == person_name).first()
        
        if not person:
            # 查找相似人员
            model_class = Teacher if is_teacher else Student
            similar_persons = self._find_similar_items(model_class, 'name', person_name)
            if similar_persons:
                return {
                    'success': False,
                    'message': f'未找到{"导师" if is_teacher else "学员"}"{person_name}"，但找到以下相似人员：{", ".join([p["name"] for p in similar_persons])}',
                    'similar_items': similar_persons,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'{"导师" if is_teacher else "学员"}"{person_name}"不存在，是否需要先创建？',
                    'need_create_person': True,
                    'person_name': person_name,
                    'is_teacher': is_teacher
                }
        
        # 解析日期
        from datetime import datetime as dt_datetime
        today = dt_datetime.now().date()
        
        def parse_date(date_str):
            if date_str == '今天':
                return today
            elif date_str == '明天':
                return today + timedelta(days=1)
            else:
                try:
                    return dt_datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    return today
        
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        
        # 创建请假记录
        new_leave = Leave(
            leave_type='teacher' if is_teacher else 'student',
            teacher_id=person.id if is_teacher else None,
            student_id=person.id if not is_teacher else None,
            start_date=dt_datetime.combine(start_date, dt_datetime.min.time()),
            end_date=dt_datetime.combine(end_date, dt_datetime.max.time()),
            reason=reason
        )
        
        self.db.add(new_leave)
        self.db.commit()
        self.db.refresh(new_leave)
        
        log_operation(self.db, "请假管理", "添加请假", 
                     f"为{'导师' if is_teacher else '学员'} {person_name} 添加请假: {reason}", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功为{person_name}添加请假',
            'data': {'id': new_leave.id}
        }
    
    def _execute_add_holiday(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加节假日"""
        date_str = params.get('date')
        name = params.get('name')
        description = params.get('description')
        
        if not date_str:
            return {
                'success': False,
                'message': '请提供节假日日期',
                'missing_fields': ['date']
            }
        
        if not name:
            return {'success': False, 'message': '缺少节假日名称'}
        
        # 解析日期
        from datetime import datetime as dt_datetime
        try:
            holiday_date = dt_datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'message': '日期格式错误，请使用 YYYY-MM-DD 格式'}
        
        # 检查日期是否已存在
        existing = self.db.query(Holiday).filter(Holiday.date == holiday_date).first()
        if existing:
            return {'success': False, 'message': f'日期 {date_str} 已设置为节假日: {existing.name}'}
        
        # 创建节假日
        new_holiday = Holiday(
            date=holiday_date,
            name=name,
            description=description
        )
        
        self.db.add(new_holiday)
        self.db.commit()
        self.db.refresh(new_holiday)
        
        log_operation(self.db, "假期管理", "添加节假日", f"添加节假日: {name} ({date_str})", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功添加节假日: {name} ({date_str})',
            'data': {'id': new_holiday.id, 'name': new_holiday.name, 'date': date_str}
        }
    
    def _execute_collect_fee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行收费"""
        person_name = params.get('person_name')
        course_name = params.get('course_name')
        amount = params.get('amount')
        receivable_amount = params.get('receivable_amount')
        payment_date_str = params.get('payment_date')
        
        if not person_name:
            return {'success': False, 'message': '缺少学员姓名'}
        
        if not course_name:
            return {
                'success': False,
                'message': '请提供科目名称',
                'missing_fields': ['course_name']
            }
        
        if not amount:
            return {
                'success': False,
                'message': '请提供缴费金额',
                'missing_fields': ['amount']
            }
        
        # 查找学员
        student = self.db.query(Student).filter(Student.name == person_name).first()
        if not student:
            similar_students = self._find_similar_items(Student, 'name', person_name)
            if similar_students:
                return {
                    'success': False,
                    'message': f'未找到学员"{person_name}"，但找到以下相似学员：{", ".join([s["name"] for s in similar_students])}',
                    'similar_items': similar_students,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'学员"{person_name}"不存在，是否需要先创建？',
                    'need_create_student': True,
                    'student_name': person_name
                }
        
        # 查找科目
        course = self.db.query(Course).filter(Course.name == course_name).first()
        if not course:
            similar_courses = self._find_similar_items(Course, 'name', course_name)
            if similar_courses:
                return {
                    'success': False,
                    'message': f'未找到科目"{course_name}"，但找到以下相似科目：{", ".join([c["name"] for c in similar_courses])}',
                    'similar_items': similar_courses,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'科目"{course_name}"不存在，是否需要先创建？',
                    'need_create_course': True,
                    'course_name': course_name
                }
        
        # 检查StudentFee是否存在，不存在则创建
        student_fee = self.db.query(StudentFee).filter(
            StudentFee.student_id == student.id,
            StudentFee.course_id == course.id
        ).first()
        
        created_fee_record = False
        if not student_fee:
            # 需要用户提供课时费标准
            return {
                'success': False,
                'message': f'学员"{person_name}"在科目"{course_name}"下没有课时费记录，请先设置课时费标准（元/小时）',
                'need_set_hourly_fee': True,
                'student_id': student.id,
                'course_id': course.id,
                'student_name': person_name,
                'course_name': course_name
            }
        
        # 解析缴费日期
        from datetime import datetime as dt_datetime
        try:
            payment_date = dt_datetime.strptime(payment_date_str, '%Y-%m-%d').date() if payment_date_str else dt_datetime.now().date()
        except ValueError:
            payment_date = dt_datetime.now().date()
        
        # 更新StudentFee
        student_fee.total_receivable_amount = (student_fee.total_receivable_amount or 0) + (receivable_amount or amount)
        student_fee.total_actual_amount = (student_fee.total_actual_amount or 0) + amount
        student_fee.remaining_amount = (student_fee.remaining_amount or 0) + amount
        
        # 然后用更新后的值创建缴费日志
        fee_log = FeeLog(
            student_id=student.id,
            course_id=course.id,
            log_type='payment',
            amount=amount,
            receivable_amount=receivable_amount or amount,
            remaining_amount=student_fee.remaining_amount,
            remaining_hours=student_fee.remaining_hours,
            payment_date=payment_date,
            description=f'智能指令缴费'
        )
        
        self.db.add(fee_log)
        self.db.commit()
        
        log_operation(self.db, "课费管理", "收取费用", f"向学员 {person_name} 收取科目 {course_name} 费用 {amount} 元", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功收取学员 {person_name} 科目 {course_name} 费用 {amount} 元',
            'data': {'fee_log_id': fee_log.id, 'remaining_amount': student_fee.remaining_amount}
        }
    
    def _execute_refund_fee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行退费"""
        person_name = params.get('person_name')
        course_name = params.get('course_name')
        amount = params.get('amount')
        refund_date_str = params.get('refund_date')
        
        if not person_name or not course_name or not amount:
            return {
                'success': False,
                'message': '缺少必要信息：学员姓名、科目名称、退费金额',
                'missing_fields': [f for f in ['person_name', 'course_name', 'amount'] 
                                  if not locals().get(f)]
            }
        
        # 查找学员
        student = self.db.query(Student).filter(Student.name == person_name).first()
        if not student:
            return {'success': False, 'message': f'学员"{person_name}"不存在'}
        
        # 查找科目
        course = self.db.query(Course).filter(Course.name == course_name).first()
        if not course:
            return {'success': False, 'message': f'科目"{course_name}"不存在'}
        
        # 查找StudentFee
        student_fee = self.db.query(StudentFee).filter(
            StudentFee.student_id == student.id,
            StudentFee.course_id == course.id
        ).first()
        
        if not student_fee:
            return {'success': False, 'message': f'学员"{person_name}"在科目"{course_name}"下没有课时费记录'}
        
        # 解析退费日期
        from datetime import datetime as dt_datetime
        try:
            refund_date = dt_datetime.strptime(refund_date_str, '%Y-%m-%d').date() if refund_date_str else dt_datetime.now().date()
        except ValueError:
            refund_date = dt_datetime.now().date()
        
        # 先更新StudentFee
        student_fee.total_refund_amount = (student_fee.total_refund_amount or 0) + amount
        student_fee.remaining_amount = (student_fee.remaining_amount or 0) - amount
        
        # 然后用更新后的值创建退费日志
        fee_log = FeeLog(
            student_id=student.id,
            course_id=course.id,
            log_type='refund',
            amount=-amount,  # 负数表示退费
            remaining_amount=student_fee.remaining_amount,
            remaining_hours=student_fee.remaining_hours,
            refund_date=refund_date,
            description=f'智能指令退费'
        )
        
        self.db.add(fee_log)
        self.db.commit()
        
        log_operation(self.db, "课费管理", "退费", f"退给学员 {person_name} 科目 {course_name} 费用 {amount} 元", 
                     user=self.username)
        
        return {
            'success': True,
            'message': f'成功退给学员 {person_name} 科目 {course_name} 费用 {amount} 元',
            'data': {'fee_log_id': fee_log.id, 'remaining_amount': student_fee.remaining_amount}
        }
    
    def _execute_add_grade(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加成绩"""
        student_name = params.get('student_name')
        course_name = params.get('course_name')
        score = params.get('score')
        total_score = params.get('total_score')
        exam_date_str = params.get('exam_date')
        grade_level = params.get('grade_level')
        exam_stage = params.get('exam_stage')
        description = params.get('description')
        
        if not student_name or not course_name or not score or not total_score or not grade_level or not exam_stage:
            missing = []
            if not student_name: missing.append('学员姓名')
            if not course_name: missing.append('科目名称')
            if not score: missing.append('成绩')
            if not total_score: missing.append('总分')
            if not grade_level: missing.append('年级')
            if not exam_stage: missing.append('考试阶段')
            return {
                'success': False,
                'message': f'缺少必要信息：{", ".join(missing)}',
                'missing_fields': [f for f in ['student_name', 'course_name', 'score', 'total_score', 'grade_level', 'exam_stage'] 
                                  if not params.get(f)]
            }
        
        # 查找学员
        student = self.db.query(Student).filter(Student.name == student_name).first()
        if not student:
            similar_students = self._find_similar_items(Student, 'name', student_name)
            if similar_students:
                return {
                    'success': False,
                    'message': f'未找到学员"{student_name}"，但找到以下相似学员：{", ".join([s["name"] for s in similar_students])}',
                    'similar_items': similar_students,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'学员"{student_name}"不存在，是否需要先创建？',
                    'need_create_student': True,
                    'student_name': student_name
                }
        
        # 查找科目
        course = self.db.query(Course).filter(Course.name == course_name).first()
        if not course:
            similar_courses = self._find_similar_items(Course, 'name', course_name)
            if similar_courses:
                return {
                    'success': False,
                    'message': f'未找到科目"{course_name}"，但找到以下相似科目：{", ".join([c["name"] for c in similar_courses])}',
                    'similar_items': similar_courses,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'科目"{course_name}"不存在，是否需要先创建？',
                    'need_create_course': True,
                    'course_name': course_name
                }
        
        # 解析考试日期
        from datetime import datetime as dt_datetime
        try:
            exam_date = dt_datetime.strptime(exam_date_str, '%Y-%m-%d') if exam_date_str else dt_datetime.now()
        except ValueError:
            exam_date = dt_datetime.now()
        
        # 计算成绩变化
        previous_grade = self.db.query(StudentGrade).filter(
            StudentGrade.student_id == student.id,
            StudentGrade.course_id == course.id
        ).order_by(StudentGrade.exam_date.desc()).first()
        
        score_change = None
        if previous_grade:
            score_change = score - previous_grade.score
        
        # 创建成绩记录
        new_grade = StudentGrade(
            student_id=student.id,
            course_id=course.id,
            exam_date=exam_date,
            grade_level=grade_level,
            exam_stage=exam_stage,
            score=score,
            total_score=total_score,
            score_change=score_change,
            description=description
        )
        
        self.db.add(new_grade)
        self.db.commit()
        self.db.refresh(new_grade)
        
        log_operation(self.db, "成绩管理", "添加成绩", f"录入学员 {student_name} 科目 {course_name} 成绩 {score}/{total_score}", 
                     user=self.username)
        
        change_msg = ""
        if score_change is not None:
            if score_change > 0:
                change_msg = f"（较上次提高 {score_change} 分）"
            elif score_change < 0:
                change_msg = f"（较上次降低 {abs(score_change)} 分）"
            else:
                change_msg = "（与上次持平）"
        
        return {
            'success': True,
            'message': f'成功录入学员 {student_name} 科目 {course_name} 成绩 {score}/{total_score}{change_msg}',
            'data': {'id': new_grade.id, 'score_change': score_change}
        }
    
    def _execute_create_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行创建排课"""
        class_name = params.get('class_name')
        course_name = params.get('course_name')
        teacher_name = params.get('teacher_name')
        room_name = params.get('room_name')
        day_of_week = params.get('day_of_week')
        start_time = params.get('start_time')
        end_time = params.get('end_time')
        start_date_str = params.get('start_date')
        end_date_str = params.get('end_date')
        
        missing = []
        if not class_name: missing.append('班级名称')
        if not course_name: missing.append('科目名称')
        if not teacher_name: missing.append('导师姓名')
        if not room_name: missing.append('教室名称')
        if not day_of_week: missing.append('星期几')
        if not start_time: missing.append('开始时间')
        if not end_time: missing.append('结束时间')
        if not start_date_str: missing.append('开始日期')
        if not end_date_str: missing.append('结束日期')
        
        if missing:
            return {
                'success': False,
                'message': f'缺少必要信息：{", ".join(missing)}',
                'missing_fields': [f for f in ['class_name', 'course_name', 'teacher_name', 'room_name', 
                                              'day_of_week', 'start_time', 'end_time', 'start_date', 'end_date']
                                  if not params.get(f)]
            }
        
        # 查找班级
        class_obj = self.db.query(ClassModel).filter(ClassModel.name == class_name).first()
        if not class_obj:
            similar_classes = self._find_similar_items(ClassModel, 'name', class_name)
            if similar_classes:
                return {
                    'success': False,
                    'message': f'未找到班级"{class_name}"，但找到以下相似班级：{", ".join([c["name"] for c in similar_classes])}',
                    'similar_items': similar_classes,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'班级"{class_name}"不存在，是否需要先创建？',
                    'need_create_class': True,
                    'class_name': class_name
                }
        
        # 查找科目
        course = self.db.query(Course).filter(Course.name == course_name).first()
        if not course:
            similar_courses = self._find_similar_items(Course, 'name', course_name)
            if similar_courses:
                return {
                    'success': False,
                    'message': f'未找到科目"{course_name}"，但找到以下相似科目：{", ".join([c["name"] for c in similar_courses])}',
                    'similar_items': similar_courses,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'科目"{course_name}"不存在，是否需要先创建？',
                    'need_create_course': True,
                    'course_name': course_name
                }
        
        # 查找导师
        teacher = self.db.query(Teacher).filter(Teacher.name == teacher_name).first()
        if not teacher:
            similar_teachers = self._find_similar_items(Teacher, 'name', teacher_name)
            if similar_teachers:
                return {
                    'success': False,
                    'message': f'未找到导师"{teacher_name}"，但找到以下相似导师：{", ".join([t["name"] for t in similar_teachers])}',
                    'similar_items': similar_teachers,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'导师"{teacher_name}"不存在，是否需要先创建？',
                    'need_create_teacher': True,
                    'teacher_name': teacher_name
                }
        
        # 查找教室
        room = self.db.query(Room).filter(Room.name == room_name).first()
        if not room:
            similar_rooms = self._find_similar_items(Room, 'name', room_name)
            if similar_rooms:
                return {
                    'success': False,
                    'message': f'未找到教室"{room_name}"，但找到以下相似教室：{", ".join([r["name"] for r in similar_rooms])}',
                    'similar_items': similar_rooms,
                    'need_confirmation': True
                }
            else:
                return {
                    'success': False,
                    'message': f'教室"{room_name}"不存在，是否需要先创建？',
                    'need_create_room': True,
                    'room_name': room_name
                }
        
        # 解析日期
        from datetime import datetime as dt_datetime
        try:
            start_date = dt_datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = dt_datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'message': '日期格式错误，请使用 YYYY-MM-DD 格式'}
        
        # 创建排课
        new_schedule = Schedule(
            course_id=course.id,
            teacher_id=teacher.id,
            class_id=class_obj.id,
            room_id=room.id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            start_date=start_date,
            end_date=end_date,
            execution_status='pending',
            schedule_type='formal'  # 默认创建为正式课
        )
        
        self.db.add(new_schedule)
        self.db.flush()  # 先flush获取new_schedule.id
        
        # 自动关联班级中的活跃学员
        from routers.schedules import get_students_by_class
        from models import schedule_student
        active_students = get_students_by_class(self.db, class_obj.id, is_active=True)
        for student in active_students:
            association = schedule_student.insert().values(
                schedule_id=new_schedule.id,
                student_id=student.id,
                attendance_status='pending'
            )
            self.db.execute(association)
        
        self.db.commit()
        self.db.refresh(new_schedule)
        
        # 检查冲突
        from routers.schedules import check_conflicts, check_leave_conflicts
        conflicts = check_conflicts(self.db, new_schedule)
        leave_conflicts = check_leave_conflicts(self.db, new_schedule)
        
        if conflicts or leave_conflicts:
            new_schedule.has_conflict = True
            all_conflicts = [c.conflict_description for c in conflicts] + leave_conflicts
            new_schedule.conflict_reason = "; ".join(all_conflicts)
            self.db.commit()
            
            conflict_msg = f"（存在冲突：{'; '.join(all_conflicts[:2])}）" if len(all_conflicts) > 2 else f"（存在冲突：{all_conflicts[0]}）"
        else:
            conflict_msg = ""
        
        log_operation(self.db, "排课管理", "创建排课", 
                     f"为班级 {class_name} 安排 {course_name} 课程，导师 {teacher_name}，教室 {room_name}", 
                     user=self.username)
        
        weekday_names = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_name = weekday_names[day_of_week] if day_of_week <= 7 else ''
        
        return {
            'success': True,
            'message': f'成功创建排课：{class_name} {course_name} {weekday_name} {start_time}-{end_time}{conflict_msg}',
            'data': {
                'id': new_schedule.id, 
                'has_conflict': new_schedule.has_conflict,
                'conflict_reason': new_schedule.conflict_reason if new_schedule.has_conflict else None
            }
        }