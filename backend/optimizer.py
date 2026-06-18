# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 CourseArrange Contributors
import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Schedule, Course, Teacher, Student, Room, Leave, Class
from utils.holiday_utils import is_holiday
from utils.logger import log_operation

class ScheduleOptimizer:
    def __init__(self, db: Session):
        self.db = db
        self.time_slots = []
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8

    def _compare_time(self, time1: str, time2: str) -> int:
        """比较两个时间字符串，返回 -1, 0, 1"""
        h1, m1 = map(int, time1.split(':'))
        h2, m2 = map(int, time2.split(':'))
        total1 = h1 * 60 + m1
        total2 = h2 * 60 + m2
        if total1 < total2:
            return -1
        elif total1 > total2:
            return 1
        else:
            return 0

    def _generate_time_slots(self, resources: Dict = None) -> List[Dict]:
        """
        根据导师和学生的可用时间段动态生成时间槽
        """
        if resources is None:
            resources = self._get_available_resources(datetime.now(), datetime.now() + timedelta(days=7))
        
        teachers = resources.get('teachers', [])
        students = resources.get('students', [])
        
        # 收集所有导师的可用时间段
        teacher_time_slots = set()
        for teacher in teachers:
            if teacher.available_time_slots:
                slots = teacher.available_time_slots.split(',')
                for slot in slots:
                    slot = slot.strip()
                    if slot:
                        teacher_time_slots.add(slot)
        
        # 收集所有学生的可用时间段
        student_time_slots = set()
        for student in students:
            if student.available_time_slots:
                slots = student.available_time_slots.split(',')
                for slot in slots:
                    slot = slot.strip()
                    if slot:
                        student_time_slots.add(slot)
        
        # 如果导师没有设置可用时间段，使用默认时间段
        if not teacher_time_slots:
            teacher_time_slots = {
                '08:00-10:00', '10:00-12:00',
                '13:30-15:30', '15:30-17:30', '17:30-19:30', '19:30-21:30',
                '14:00-16:00', '16:00-18:00', '18:00-20:00', '20:00-22:00',
                '14:30-16:30', '16:30-18:30', '18:30-20:30', '20:30-22:30'
            }
        # 如果学生没有设置可用时间段，使用默认时间段
        if not student_time_slots:
            student_time_slots = {
                '08:00-10:00', '10:00-12:00',
                '13:30-15:30', '15:30-17:30', '17:30-19:30', '19:30-21:30',
                '14:00-16:00', '16:00-18:00', '18:00-20:00', '20:00-22:00',
                '14:30-16:30', '16:30-18:30', '18:30-20:30', '20:30-22:30'
            }
        
        # 计算导师和学生可用时间段的交集
        common_time_slots = teacher_time_slots & student_time_slots
        
        # 如果交集为空，使用导师的可用时间段
        if not common_time_slots:
            common_time_slots = teacher_time_slots
        
        # 按时间排序
        sorted_time_slots = sorted(common_time_slots, key=lambda x: x.split('-')[0])
        
        # 生成时间槽
        slots = []
        days = [1, 2, 3, 4, 5, 6, 7]  # 周一到周日
        
        for day in days:
            for time_slot in sorted_time_slots:
                start, end = time_slot.split('-')
                slots.append({
                    'day_of_week': day,
                    'start_time': start.strip(),
                    'end_time': end.strip()
                })
        
        log_operation(self.db, "排课算法", "DEBUG", f"生成的时间槽数量: {len(slots)}")
        log_operation(self.db, "排课算法", "DEBUG", f"可用时间段: {sorted_time_slots}")
        
        return slots

    def _get_available_resources(self, start_date: datetime, end_date: datetime, class_ids: List[int] = None) -> Dict:
        # 获取在职导师
        teachers = self.db.query(Teacher).filter(Teacher.is_active == True).all()
        
        # 获取包含有效学生的班级
        if class_ids and len(class_ids) > 0:
            # 如果指定了班级ID，只获取这些班级
            all_classes = self.db.query(Class).filter(
                Class.id.in_(class_ids),
                Class.is_active == True
            ).all()
            log_operation(self.db, "排课筛选", "INFO", f"指定班级IDs: {class_ids}, 匹配到 {len(all_classes)} 个班级: {[c.name for c in all_classes]}")
        else:
            # 否则获取所有班级
            all_classes = self.db.query(Class).filter(Class.is_active == True).all()
            log_operation(self.db, "排课筛选", "INFO", f"未指定班级，使用所有 {len(all_classes)} 个班级")
        
        classes = []
        class_students_cache = {}  # 班级学生缓存
        
        for class_ in all_classes:
            active_students = [s for s in class_.students if s.is_active]
            if active_students:
                classes.append(class_)
                # 缓存班级的学生ID集合
                class_students_cache[class_.id] = {s.id for s in active_students}
        
        log_operation(self.db, "排课筛选", "INFO", f"最终用于排课的班级({len(classes)}个): {[(c.id, c.name) for c in classes]}")
        
        # 获取有效教室
        rooms = self.db.query(Room).filter(Room.is_active == True).all()
        
        # 只获取关联了在职教师的科目
        all_courses = self.db.query(Course).all()
        courses = []
        for course in all_courses:
            active_teachers = [t for t in course.teachers if t.is_active]
            if active_teachers:
                courses.append(course)
        
        # 获取请假记录
        leaves = self.db.query(Leave).all()
        
        # 获取有效学生（如果指定了班级，只获取这些班级的学生）
        if class_ids and len(class_ids) > 0:
            # 通过班级关系获取学生
            students_query = self.db.query(Student).join(Student.classes).filter(
                Student.is_active == True,
                Class.id.in_(class_ids)
            ).distinct()
            students = students_query.all()
            log_operation(self.db, "排课筛选", "INFO", f"指定班级的学生数量: {len(students)}")
        else:
            students = self.db.query(Student).filter(Student.is_active == True).all()
        
        return {
            'teachers': teachers,
            'classes': classes,
            'rooms': rooms,
            'courses': courses,
            'leaves': leaves,
            'students': students,
            'class_students_cache': class_students_cache
        }

    def _check_conflicts(self, schedule: Schedule, existing_schedules: List[Schedule], class_students_cache: Dict[int, Set[int]] = None) -> List[str]:
        conflicts = []
        
        for existing in existing_schedules:
            if schedule.day_of_week == existing.day_of_week:
                time_overlap = (
                    schedule.start_time < existing.end_time and
                    schedule.end_time > existing.start_time and
                    schedule.start_date <= existing.end_date and
                    schedule.end_date >= existing.start_date
                )
                
                if time_overlap:
                    # 硬性约束：导师时间冲突（HC_TEACHER_TIME）
                    if schedule.teacher_id == existing.teacher_id:
                        conflicts.append(f"导师时间冲突: {schedule.teacher_id}")
                    
                    # 硬性约束：班级时间冲突（HC_CLASS_TIME）
                    if schedule.class_id == existing.class_id:
                        conflicts.append(f"班级时间冲突: {schedule.class_id}")
                    
                    # 硬性约束：教室时间冲突（HC_ROOM_TIME）
                    if schedule.room_id == existing.room_id:
                        conflicts.append(f"教室时间冲突: {schedule.room_id}")
                    
                    # 硬性约束：学员时间冲突（HC_STUDENT_TIME）
                    # 检查两个班级是否有共同的学生
                    if class_students_cache is None:
                        # 如果没有缓存，查询数据库（使用多对多关系）
                        class1 = self.db.query(Class).filter(Class.id == schedule.class_id).first()
                        class2 = self.db.query(Class).filter(Class.id == existing.class_id).first()
                        
                        class1_students = [s for s in class1.students if s.is_active] if class1 else []
                        class2_students = [s for s in class2.students if s.is_active] if class2 else []
                        
                        class1_student_ids = {s.id for s in class1_students}
                        class2_student_ids = {s.id for s in class2_students}
                    else:
                        # 使用缓存
                        class1_student_ids = class_students_cache.get(schedule.class_id, set())
                        class2_student_ids = class_students_cache.get(existing.class_id, set())
                    
                    common_students = class1_student_ids & class2_student_ids
                    if common_students:
                        conflicts.append(f"学员时间冲突: 班级 {schedule.class_id} 和班级 {existing.class_id} 有共同学生")
        
        return conflicts

    def _check_leave_conflicts(self, schedule: Schedule, leaves: List[Leave]) -> List[str]:
        conflicts = []
        
        for leave in leaves:
            if leave.start_date <= schedule.end_date and leave.end_date >= schedule.start_date:
                if leave.leave_type == "teacher" and leave.teacher_id == schedule.teacher_id:
                    conflicts.append(f"导师请假: {leave.reason}")
                elif leave.leave_type == "student":
                    # 检查学员请假（使用多对多关系）
                    class_ = self.db.query(Class).filter(Class.id == schedule.class_id).first()
                    if class_:
                        students = [s for s in class_.students if s.is_active]
                        for student in students:
                            if student.id == leave.student_id:
                                conflicts.append(f"学员请假: {leave.reason}")
                                break
        
        return conflicts

    def _check_teacher_availability(self, teacher: Teacher, day_of_week: int, start_time: str = None, end_time: str = None) -> bool:
        try:
            log_operation(self.db, "排课算法", "DEBUG", f"检查导师可用性: teacher={teacher}, teacher.name={teacher.name}, teacher.available_days={teacher.available_days}, teacher.available_time_slots={teacher.available_time_slots}")
            
            if not teacher.available_days:
                log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 没有设置可安排日期")
                return False
            
            available_days = [int(d.strip()) for d in teacher.available_days.split(",")]
            if day_of_week not in available_days:
                log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 星期 {day_of_week} 不可用")
                return False
            
            if start_time and end_time:
                if not teacher.available_time_slots:
                    log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 没有设置可安排课时段")
                    return False
                
                available_time_slots = [t.strip() for t in teacher.available_time_slots.split(",")]
                time_slot = f"{start_time}-{end_time}"
                
                found = False
                for available_slot in available_time_slots:
                    available_start, available_end = available_slot.split('-')
                    
                    if time_slot == available_slot:
                        log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 时间段 {time_slot} 完全匹配")
                        found = True
                        break
                    
                    if (self._compare_time(start_time, available_start) >= 0 and 
                        self._compare_time(end_time, available_end) <= 0):
                        log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 时间段 {time_slot} 在可用时间段 {available_slot} 内")
                        found = True
                        break
                
                if not found:
                    log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 没有可用时间段 {time_slot}")
                    return False
            
            log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 可用")
            return True
        except Exception as e:
            log_operation(self.db, "排课算法", "ERROR", f"检查导师可用性时出错: {e}")
            return False

    def _check_class_availability(self, class_: Class, day_of_week: int, start_time: str = None, end_time: str = None) -> bool:
        try:
            # 获取班级的所有学员（使用多对多关系）
            students = class_.students
            
            if not students:
                return False
            
            # 检查所有学员是否都可用
            for student in students:
                # 检查日期
                if not student.available_days:
                    return False
                
                available_days = [int(d.strip()) for d in student.available_days.split(",")]
                if day_of_week not in available_days:
                    return False
                
                # 如果指定了时间段，检查时间段
                if start_time and end_time:
                    if not student.available_time_slots:
                        return False
                    
                    available_time_slots = [t.strip() for t in student.available_time_slots.split(",")]
                    time_slot = f"{start_time}-{end_time}"
                    
                    # 检查是否有包含或被包含的时间段
                    found = False
                    for available_slot in available_time_slots:
                        available_start, available_end = available_slot.split('-')
                        
                        # 检查是否完全匹配
                        if time_slot == available_slot:
                            found = True
                            break
                        
                        # 检查是否在可用时间段内
                        if (self._compare_time(start_time, available_start) >= 0 and 
                            self._compare_time(end_time, available_end) <= 0):
                            found = True
                            break
                    
                    if not found:
                        return False
            
            return True
        except Exception as e:
            return False

    def _check_class_availability_optimized(self, class_: Class, day_of_week: int, start_time: str = None, end_time: str = None, class_students: Dict[int, Student] = None) -> bool:
        """优化版本的班级可用性检查，使用缓存的学生信息"""
        try:
            # 使用传入的缓存，如果没有则查询（使用多对多关系）
            if class_students is None:
                students = class_.students
            else:
                students = list(class_students.values())
            
            if not students:
                return False
            
            # 检查所有学员是否都可用
            for student in students:
                # 检查日期
                if not student.available_days:
                    return False
                
                available_days = [int(d.strip()) for d in student.available_days.split(",")]
                if day_of_week not in available_days:
                    return False
                
                # 如果指定了时间段，检查时间段
                if start_time and end_time:
                    if not student.available_time_slots:
                        return False
                    
                    available_time_slots = [t.strip() for t in student.available_time_slots.split(",")]
                    time_slot = f"{start_time}-{end_time}"
                    
                    # 检查是否有包含或被包含的时间段
                    found = False
                    for available_slot in available_time_slots:
                        available_start, available_end = available_slot.split('-')
                        
                        # 检查是否完全匹配
                        if time_slot == available_slot:
                            found = True
                            break
                        
                        # 检查是否在可用时间段内
                        if (self._compare_time(start_time, available_start) >= 0 and 
                            self._compare_time(end_time, available_end) <= 0):
                            found = True
                            break
                    
                    if not found:
                        return False
            
            return True
        except Exception as e:
            return False

    def _check_room_availability(self, room: Room, day_of_week: int, start_time: str, end_time: str) -> bool:
        try:
            # 教室默认所有时间段都可用
            log_operation(self.db, "排课算法", "DEBUG", f"教室 {room.name} 可用")
            return True
        except Exception as e:
            log_operation(self.db, "排课算法", "ERROR", f"检查教室可用性时出错: {e}")
            return False

    def _calculate_fitness(self, individual: List[Schedule], resources: Dict) -> float:
        fitness = 0.0
        conflicts = 0
        valid_schedules = 0
        
        # 获取班级学生缓存
        class_students_cache = resources.get('class_students_cache', {})
        
        for schedule in individual:
            schedule_conflicts = self._check_conflicts(schedule, individual, class_students_cache)
            leave_conflicts = self._check_leave_conflicts(schedule, resources['leaves'])
            
            if not schedule_conflicts and not leave_conflicts:
                valid_schedules += 1
                fitness += 10.0
                
                course = next((c for c in resources['courses'] if c.id == schedule.course_id), None)
                if course:
                    fitness += course.priority * 0.1
            else:
                conflicts += len(schedule_conflicts) + len(leave_conflicts)
        
        fitness -= conflicts * 5.0
        fitness += valid_schedules * 2.0
        
        return max(fitness, 0.0)

    def _generate_initial_population(self, resources: Dict, start_date: datetime, end_date: datetime) -> List[Schedule]:
        individual = []
        
        try:
            log_operation(self.db, "排课算法", "INFO", "开始生成初始个体")
            log_operation(self.db, "排课算法", "DEBUG", f"可用资源: {len(resources['courses'])} 课程, {len(resources['teachers'])} 导师, {len(resources['classes'])} 班级, {len(resources['rooms'])} 教室")
            
            # 计算日期范围内的所有日期
            dates = []
            current = start_date
            while current <= end_date:
                dates.append(current)
                current += timedelta(days=1)
            
            log_operation(self.db, "排课算法", "DEBUG", f"日期范围: {start_date.date()} 到 {end_date.date()}，共 {len(dates)} 天")
            
            # 为每个班级生成排课
            for class_ in resources['classes']:
                # 获取班级的所有学员（使用多对多关系）
                students = [s for s in class_.students if s.is_active]
                
                if not students:
                    continue
                
                # 缓存班级学生信息
                class_students = {s.id: s for s in students}
                
                # 为每个日期生成排课
                for date in dates:
                    # 计算该日期的星期几（1-7，1=周一，7=周日）
                    day_of_week = date.weekday() + 1
                    
                    # 检查是否为节假日
                    is_date_holiday = is_holiday(date)
                    if is_date_holiday:
                        # 检查所有学生是否允许节假日排课
                        all_students_allow = all(s.allow_holiday_scheduling for s in students)
                        
                        if not all_students_allow:
                            continue
                    
                    # 检查班级的所有学员是否在该日期可用
                    if not self._check_class_availability_optimized(class_, day_of_week, None, None, class_students):
                        continue
                    
                    # 获取学员的可用时间段（只匹配当前日期的星期几）
                    available_slots = []
                    for slot in self.time_slots:
                        if slot['day_of_week'] == day_of_week:
                            if self._check_class_availability_optimized(class_, day_of_week, slot['start_time'], slot['end_time'], class_students):
                                available_slots.append(slot)
                    
                    if not available_slots:
                        continue
                    
                    if available_slots:
                        slot = random.choice(available_slots)
                        
                        # 对于每个科目，获取可以教授该科目的导师
                        available_course_teacher_pairs = []
                        for course in resources['courses']:
                            # 获取可以教授该科目的导师
                            course_teachers = []
                            for teacher in resources['teachers']:
                                # 如果是节假日，检查导师是否允许节假日排课
                                if is_date_holiday:
                                    if not teacher.allow_holiday_scheduling:
                                        log_operation(self.db, "排课算法", "DEBUG", f"导师 {teacher.name} 不允许节假日排课，跳过")
                                        continue
                                # 检查导师是否可以教授该科目
                                if teacher.courses:
                                    teacher_course_ids = [c.id for c in teacher.courses]
                                    if course.id in teacher_course_ids:
                                        # 检查导师的可安排日期和可安排课时段
                                        if self._check_teacher_availability(teacher, day_of_week, slot['start_time'], slot['end_time']):
                                            course_teachers.append(teacher)
                            
                            if course_teachers:
                                available_course_teacher_pairs.append({
                                    'course': course,
                                    'teachers': course_teachers
                                })
                        
                        if not available_course_teacher_pairs:
                            log_operation(self.db, "排课算法", "DEBUG", f"班级 {class_.name} 在 {date.date()} 星期{day_of_week} 没有可用的科目-导师组合")
                            continue
                        
                        # 随机选择一个科目-导师组合
                        selected_pair = random.choice(available_course_teacher_pairs)
                        selected_course = selected_pair['course']
                        selected_teacher = random.choice(selected_pair['teachers'])
                        
                        # 获取可用的教室
                        available_rooms = []
                        for room in resources['rooms']:
                            if self._check_room_availability(room, day_of_week, slot['start_time'], slot['end_time']):
                                available_rooms.append(room)
                        
                        if not available_rooms:
                            log_operation(self.db, "排课算法", "DEBUG", f"班级 {class_.name} 在 {date.date()} 星期{day_of_week} 没有可用教室")
                            continue
                        
                        selected_room = random.choice(available_rooms)
                        
                        schedule = Schedule(
                            course_id=selected_course.id,
                            teacher_id=selected_teacher.id,
                            class_id=class_.id,
                            room_id=selected_room.id,
                            day_of_week=day_of_week,
                            start_time=slot['start_time'],
                            end_time=slot['end_time'],
                            start_date=date,
                            end_date=date,
                            schedule_type='formal'  # 自动排课默认为正式课
                        )
                        individual.append(schedule)
                        log_operation(self.db, "排课算法", "INFO", f"创建排课成功: 班级 {class_.name} - 科目 {selected_course.name} - 导师 {selected_teacher.name} - 教室 {selected_room.name} - {date.date()} 星期{day_of_week} {slot['start_time']}")
                    else:
                        log_operation(self.db, "排课算法", "DEBUG", f"班级 {class_.name} 在 {date.date()} 星期{day_of_week} 没有可用时间段")
        except Exception as e:
            log_operation(self.db, "排课算法", "ERROR", f"生成初始个体时出错: {e}")
        
        log_operation(self.db, "排课算法", "INFO", f"初始个体生成完成，共 {len(individual)} 个排课")
        return individual

    def _crossover(self, parent1: List[Schedule], parent2: List[Schedule]) -> Tuple[List[Schedule], List[Schedule]]:
        if random.random() > self.crossover_rate:
            return parent1[:], parent2[:]
        
        if not parent1 or not parent2:
            return parent1[:], parent2[:]
        
        min_len = min(len(parent1), len(parent2))
        if min_len <= 1:
            return parent1[:], parent2[:]
        
        crossover_point = random.randint(1, min_len - 1)
        
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return child1, child2

    def _mutate(self, individual: List[Schedule], resources: Dict, start_date: datetime, end_date: datetime) -> List[Schedule]:
        if not individual:
            return individual[:]
        
        mutated = individual[:]
        
        for schedule in mutated:
            if random.random() < self.mutation_rate:
                # 获取班级
                class_ = next((c for c in resources['classes'] if c.id == schedule.class_id), None)
                if not class_:
                    continue
                
                # 根据 schedule.start_date 计算正确的星期几
                day_of_week = schedule.start_date.weekday() + 1
                
                # 获取可用时间段（只匹配当前日期的星期几）
                available_slots = []
                for slot in self.time_slots:
                    if slot['day_of_week'] == day_of_week:
                        if self._check_class_availability(class_, day_of_week, slot['start_time'], slot['end_time']):
                            available_slots.append(slot)
                
                if available_slots:
                    new_slot = random.choice(available_slots)
                    
                    # 对于每个科目，获取可以教授该科目的导师
                    available_course_teacher_pairs = []
                    for course in resources['courses']:
                        # 获取可以教授该科目的导师
                        course_teachers = []
                        for teacher in resources['teachers']:
                            # 检查导师是否可以教授该科目
                            if teacher.courses:
                                teacher_course_ids = [c.id for c in teacher.courses]
                                if course.id in teacher_course_ids:
                                    # 检查导师的可安排日期和可安排课时段
                                    if self._check_teacher_availability(teacher, day_of_week, new_slot['start_time'], new_slot['end_time']):
                                        course_teachers.append(teacher)
                        
                        if course_teachers:
                            available_course_teacher_pairs.append({
                                'course': course,
                                'teachers': course_teachers
                            })
                    
                    if available_course_teacher_pairs:
                        # 随机选择一个科目-导师组合
                        selected_pair = random.choice(available_course_teacher_pairs)
                        selected_course = selected_pair['course']
                        selected_teacher = random.choice(selected_pair['teachers'])
                        
                        # 获取可用的教室
                        available_rooms = []
                        for room in resources['rooms']:
                            if self._check_room_availability(room, day_of_week, new_slot['start_time'], new_slot['end_time']):
                                available_rooms.append(room)
                        
                        if available_rooms:
                            selected_room = random.choice(available_rooms)
                            
                            schedule.day_of_week = day_of_week
                            schedule.course_id = selected_course.id
                            schedule.teacher_id = selected_teacher.id
                            schedule.room_id = selected_room.id
                            schedule.start_time = new_slot['start_time']
                            schedule.end_time = new_slot['end_time']
        
        return mutated

    def _selection(self, population: List[List[Schedule]], fitness_scores: List[float]) -> List[Schedule]:
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            return random.choice(population)
        
        pick = random.uniform(0, total_fitness)
        current = 0
        
        for i, fitness in enumerate(fitness_scores):
            current += fitness
            if current > pick:
                return population[i]
        
        return population[-1]

    #  遗传算法主函数
    def genetic_algorithm(self, start_date: datetime, end_date: datetime, class_ids: List[int] = None) -> List[Schedule]:
        resources = self._get_available_resources(start_date, end_date, class_ids)
        
        initial_solution = self.backtracking_search(resources, start_date, end_date, class_ids)
        
        if not initial_solution:
            log_operation(self.db, "排课算法", "WARNING", "回溯算法无法生成初始解")
            return []
        
        log_operation(self.db, "排课算法", "INFO", f"回溯算法生成初始解，共 {len(initial_solution)} 个排课")
        
        population = [initial_solution]
        
        for _ in range(self.population_size - 1):
            individual = self._mutate(initial_solution[:], resources, start_date, end_date)
            population.append(individual)
        
        log_operation(self.db, "排课算法", "DEBUG", f"初始种群大小: {len(population)}")
        
        best_individual = initial_solution
        best_fitness = self._calculate_fitness(best_individual, resources)
        log_operation(self.db, "排课算法", "DEBUG", f"初始最佳适应度: {best_fitness}")
        
        for generation in range(self.generations):
            fitness_scores = [self._calculate_fitness(ind, resources) for ind in population]
            
            max_fitness = max(fitness_scores)
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_individual = population[fitness_scores.index(max_fitness)]
                log_operation(self.db, "排课算法", "DEBUG", f"代数 {generation + 1}: 新的最佳适应度 {best_fitness}")
            
            new_population = []
            
            # 保留精英
            elite_size = int(self.population_size * 0.1)
            elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
            for idx in elite_indices:
                new_population.append(population[idx][:])
            
            # 生成新个体
            while len(new_population) < self.population_size:
                parent1 = self._selection(population, fitness_scores)
                parent2 = self._selection(population, fitness_scores)
                
                child1, child2 = self._crossover(parent1, parent2)
                
                child1 = self._mutate(child1, resources, start_date, end_date)
                child2 = self._mutate(child2, resources, start_date, end_date)
                
                new_population.extend([child1, child2])
            
            population = new_population[:self.population_size]
        
        log_operation(self.db, "排课算法", "INFO", f"遗传算法完成，最佳适应度: {best_fitness}, 排课数量: {len(best_individual)}")
        return best_individual if best_individual else []

    def backtracking_search(self, resources: Dict, start_date: datetime, end_date: datetime, class_ids: List[int] = None) -> List[Schedule]:
        result = []
        
        try:
            log_operation(self.db, "排课算法", "INFO", f"开始回溯搜索，处理 {len(resources['classes'])} 个班级")
            
            # 计算日期范围内的所有日期
            dates = []
            current = start_date
            while current <= end_date:
                dates.append(current)
                current += timedelta(days=1)
            
            # 为每个班级生成排课
            for class_ in resources['classes']:
                log_operation(self.db, "排课算法", "DEBUG", f"正在为班级 '{class_.name}' (ID:{class_.id}) 生成排课")
                
                # 获取班级的所有学员（使用多对多关系）
                students = [s for s in class_.students if s.is_active]
                
                if not students:
                    log_operation(self.db, "排课算法", "DEBUG", f"班级 {class_.name} 没有有效学生，跳过")
                    continue
                
                # 缓存班级学生信息
                class_students = {s.id: s for s in students}
                
                # 为每个日期生成排课
                for date in dates:
                    # 计算该日期的星期几（1-7，1=周一，7=周日）
                    day_of_week = date.weekday() + 1
                    
                    # 检查是否为节假日
                    is_date_holiday = is_holiday(date)
                    if is_date_holiday:
                        # 检查所有学生是否允许节假日排课
                        all_students_allow = all(s.allow_holiday_scheduling for s in students)
                        
                        if not all_students_allow:
                            continue
                    
                    # 检查班级的所有学员是否在该日期可用
                    if not self._check_class_availability_optimized(class_, day_of_week, None, None, class_students):
                        continue
                    
                    # 获取学员的可用时间段（只匹配当前日期的星期几）
                    available_slots = []
                    for slot in self.time_slots:
                        if slot['day_of_week'] == day_of_week:
                            if self._check_class_availability_optimized(class_, day_of_week, slot['start_time'], slot['end_time'], class_students):
                                available_slots.append(slot)
                    
                    if not available_slots:
                        continue
                    
                    if available_slots:
                        slot = random.choice(available_slots)
                        
                        # 对于每个科目，获取可以教授该科目的导师
                        available_course_teacher_pairs = []
                        for course in resources['courses']:
                            # 获取可以教授该科目的导师
                            course_teachers = []
                            for teacher in resources['teachers']:
                                # 如果是节假日，检查导师是否允许节假日排课
                                if is_date_holiday:
                                    if not teacher.allow_holiday_scheduling:
                                        continue
                                # 检查导师是否可以教授该科目
                                if teacher.courses:
                                    teacher_course_ids = [c.id for c in teacher.courses]
                                    if course.id in teacher_course_ids:
                                        # 检查导师的可安排日期和可安排课时段
                                        if self._check_teacher_availability(teacher, day_of_week, slot['start_time'], slot['end_time']):
                                            course_teachers.append(teacher)
                            
                            if course_teachers:
                                available_course_teacher_pairs.append({
                                    'course': course,
                                    'teachers': course_teachers
                                })
                        
                        if not available_course_teacher_pairs:
                            continue
                        
                        # 随机选择一个科目-导师组合
                        selected_pair = random.choice(available_course_teacher_pairs)
                        selected_course = selected_pair['course']
                        selected_teacher = random.choice(selected_pair['teachers'])
                        
                        # 获取可用的教室
                        available_rooms = []
                        for room in resources['rooms']:
                            if self._check_room_availability(room, day_of_week, slot['start_time'], slot['end_time']):
                                available_rooms.append(room)
                        
                        if not available_rooms:
                            continue
                        
                        selected_room = random.choice(available_rooms)
                        
                        schedule = Schedule(
                            course_id=selected_course.id,
                            teacher_id=selected_teacher.id,
                            class_id=class_.id,
                            room_id=selected_room.id,
                            day_of_week=day_of_week,
                            start_time=slot['start_time'],
                            end_time=slot['end_time'],
                            start_date=date,
                            end_date=date,
                            schedule_type='formal'  # 自动排课默认为正式课
                        )
                        result.append(schedule)
            
            log_operation(self.db, "排课算法", "INFO", f"回溯搜索完成，共生成 {len(result)} 个排课")
            return result
        except Exception as e:
            log_operation(self.db, "排课算法", "ERROR", f"回溯搜索出错: {e}")
            traceback.print_exc()
            return []

    def hybrid_algorithm(self, start_date: datetime, end_date: datetime, class_ids: List[int] = None) -> List[Schedule]:
        resources = self._get_available_resources(start_date, end_date, class_ids)
        
        log_operation(self.db, "排课算法", "INFO", "开始混合算法")
        
        initial_solution = self.backtracking_search(resources, start_date, end_date, class_ids)
        
        if not initial_solution:
            log_operation(self.db, "排课算法", "WARNING", "回溯算法无法生成初始解")
            return []
        
        log_operation(self.db, "排课算法", "INFO", f"回溯算法生成初始解，共 {len(initial_solution)} 个排课")
        
        population = [initial_solution]
        
        for _ in range(self.population_size - 1):
            individual = self._mutate(initial_solution[:], resources, start_date, end_date)
            population.append(individual)
        
        log_operation(self.db, "排课算法", "DEBUG", f"初始种群大小: {len(population)}")
        
        best_individual = initial_solution
        best_fitness = self._calculate_fitness(best_individual, resources)
        log_operation(self.db, "排课算法", "DEBUG", f"初始最佳适应度: {best_fitness}")
        
        for generation in range(self.generations):
            fitness_scores = [self._calculate_fitness(ind, resources) for ind in population]
            
            max_fitness = max(fitness_scores)
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_individual = population[fitness_scores.index(max_fitness)]
                log_operation(self.db, "排课算法", "DEBUG", f"代数 {generation + 1}: 新的最佳适应度 {best_fitness}")
            
            new_population = []
            
            elite_size = int(self.population_size * 0.1)
            elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
            for idx in elite_indices:
                new_population.append(population[idx][:])
            
            while len(new_population) < self.population_size:
                parent1 = self._selection(population, fitness_scores)
                parent2 = self._selection(population, fitness_scores)
                
                child1, child2 = self._crossover(parent1, parent2)
                
                child1 = self._mutate(child1, resources, start_date, end_date)
                child2 = self._mutate(child2, resources, start_date, end_date)
                
                new_population.append(child1)
                new_population.append(child2)
            
            population = new_population
        
        log_operation(self.db, "排课算法", "INFO", f"混合算法完成，最佳适应度: {best_fitness}")
        return best_individual

    def _genetic_optimize(self, initial_solution: List[Schedule], resources: Dict, 
                      start_date: datetime, end_date: datetime) -> List[Schedule]:
        """使用遗传算法优化初始解"""
        if not initial_solution:
            return []
        
        # 使用初始解作为初始种群
        population = [initial_solution]
        
        # 生成变异个体
        for _ in range(self.population_size - 1):
            individual = self._mutate(initial_solution[:], resources, start_date, end_date)
            population.append(individual)
        
        best_individual = initial_solution
        best_fitness = self._calculate_fitness(best_individual, resources)
        
        for generation in range(self.generations):
            fitness_scores = [self._calculate_fitness(ind, resources) for ind in population]
            
            max_fitness = max(fitness_scores)
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_individual = population[fitness_scores.index(max_fitness)]
            
            new_population = []
            
            # 保留精英
            elite_size = int(self.population_size * 0.1)
            elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
            for idx in elite_indices:
                new_population.append(population[idx][:])
            
            # 生成新个体
            while len(new_population) < self.population_size:
                parent1 = self._selection(population, fitness_scores)
                parent2 = self._selection(population, fitness_scores)
                
                child1, child2 = self._crossover(parent1, parent2)
                
                child1 = self._mutate(child1, resources, start_date, end_date)
                child2 = self._mutate(child2, resources, start_date, end_date)
                
                new_population.extend([child1, child2])
            
            population = new_population[:self.population_size]
        
        return best_individual if best_individual else []

    def optimize_schedules(self, start_date: datetime, end_date: datetime, 
                      algorithm: str = "hybrid", class_ids: List[int] = None) -> List[Schedule]:
        # 获取资源，传入班级ID筛选
        resources = self._get_available_resources(start_date, end_date, class_ids)
        
        # 根据资源动态生成时间槽
        self.time_slots = self._generate_time_slots(resources)
        
        if algorithm == "genetic":
            return self.genetic_algorithm(start_date, end_date, class_ids)
        elif algorithm == "backtracking":
            return self.backtracking_search(resources, start_date, end_date, class_ids) or []
        else:
            return self.hybrid_algorithm(start_date, end_date, class_ids)