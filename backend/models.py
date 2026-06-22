# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Float, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

course_teacher = Table(
    'course_teacher',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('teacher_id', Integer, ForeignKey('teachers.id'), primary_key=True)
)

student_class = Table(
    'student_class',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),
    Column('class_id', Integer, ForeignKey('classes.id'), primary_key=True)
)

schedule_student = Table(
    'schedule_student',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('schedule_id', Integer, ForeignKey('schedules.id'), nullable=False, index=True),
    Column('student_id', Integer, ForeignKey('students.id'), nullable=False, index=True),
    Column('attendance_status', String(20), default='present', comment="出勤状态：present-出席, absent-缺席, leave-请假, makeup-补课"),
    Column('absence_reason', Text, nullable=True, comment="缺勤原因"),
    Column('makeup_status', String(20), nullable=True, comment="补课状态：pending-待补课, completed-已补课, declined-不补课"),
    Column('makeup_schedule_id', Integer, nullable=True, comment="补课课程ID（关联到schedules表的id）"),
    Column('declined_reason', Text, nullable=True, comment="不补课原因"),
    Column('created_at', DateTime, default=datetime.now, comment="记录创建时间")
)

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    priority = Column(Integer, default=0)
    teachers = relationship("Teacher", secondary=course_teacher, back_populates="courses")
    schedules = relationship("Schedule", back_populates="course")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    join_date = Column(Date, nullable=True, comment="进入机构日期")
    title = Column(String(50))
    department = Column(String(100))
    max_weekly_hours = Column(Integer, default=40)
    available_days = Column(Text, default="1,2,3,4,5,6,7")
    available_time_slots = Column(Text, default="08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30")
    allow_holiday_scheduling = Column(Boolean, default=False, comment="节假日可排课")
    # 添加：contact_phone = Column(String(20), comment="联系方式")
    contact_phone = Column(String(20), comment="联系电话")
    email = Column(String(100), comment="电子邮箱")
    is_active = Column(Boolean, default=True)
    end_date = Column(DateTime, nullable=True, comment="离职日期")
    courses = relationship("Course", secondary=course_teacher, back_populates="teachers")
    schedules = relationship("Schedule", back_populates="teacher")
    leaves = relationship("Leave", back_populates="teacher")
    no_feedback_required = Column(Boolean, default=False, comment="无需反馈")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 定义反向关系
    user_account = relationship("User", back_populates="teacher", uselist=False)

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, default=True)
    wechat_webhook = Column(String(500), comment="企业微信群Webhook地址")    
    # 删除 students = relationship("Student", back_populates="class_")
    # 添加：students = relationship("Student", secondary=student_class, back_populates="classes")
    students = relationship("Student", secondary=student_class, back_populates="classes")
    schedules = relationship("Schedule", back_populates="class_")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    school = Column(String(100))
    grade = Column(String(50))
    enrollment_date = Column(Date, nullable=True, comment="进入机构日期")
    # 删除 class_id = Column(Integer, ForeignKey("classes.id"))
    available_days = Column(Text, default="1,2,3,4,5,6,7")
    available_time_slots = Column(Text, default="08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30")
    allow_holiday_scheduling = Column(Boolean, default=False, comment="节假日可排课")
    is_active = Column(Boolean, default=True)
    end_date = Column(DateTime, nullable=True, comment="结束日期")
    # 删除 class_ = relationship("Class", back_populates="students")
    classes = relationship("Class", secondary=student_class, back_populates="students")
    leaves = relationship("Leave", back_populates="student")
    contact_person = Column(String(100), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    email = Column(String(100), comment="电子邮箱")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class StudentGrade(Base):
    """学生成绩记录表"""
    __tablename__ = "student_grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, comment="学生ID")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="科目ID")
    exam_date = Column(DateTime, nullable=False, comment="考试日期")
    grade_level = Column(String(50), nullable=False, comment="年级")
    exam_stage = Column(String(50), nullable=False, comment="考试阶段")
    score = Column(Float, nullable=False, comment="当次考试成绩")
    total_score = Column(Float, nullable=True, comment="当次科目总分")
    score_change = Column(Float, nullable=True, comment="较最近一次成绩的变化（正数表示增加，负数表示减少，0表示持平）")
    description = Column(Text, comment="备注")
    student = relationship("Student", backref="grades")
    course = relationship("Course", backref="student_grades")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    capacity = Column(Integer, default=30)
    facilities = Column(String(50), default="普通")
    facility_details = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    schedules = relationship("Schedule", back_populates="room")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    leave_type = Column(String(20), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text)
    teacher = relationship("Teacher", back_populates="leaves")
    student = relationship("Student", back_populates="leaves")
    created_at = Column(DateTime, default=datetime.now)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    has_conflict = Column(Boolean, default=False)
    conflict_reason = Column(Text)
    execution_status = Column(String(20), default="pending", comment="执行状态：pending-待执行, completed-完训, postponed-延期, cancelled-取消")
    content_feedback = Column(Text, default="", comment="课程反馈：内容|作业|注意|；格式说明：用|分隔，如：内容：我是谁？我来自哪里？我往那里去？|作业：今天布置的10道题|注意：注意第三题的解题思路")
    cancel_reason = Column(Text, default="", comment="取消原因")
    postpone_reason = Column(Text, default="", comment="延期原因")
    homework_regular = Column(Text, default="", comment="常规作业")
    homework_images = Column(Text, default="", comment="作业图片URL，用逗号分隔")
    room_type = Column(String(20), default="offline_physical", nullable=False, comment="教室类型：offline_physical-线下物理, online_virtual-线上虚拟")
    meeting_link = Column(Text, default=None, comment="会议室链接（线上虚拟课程必填）")
    schedule_type = Column(String(20), default="formal", nullable=False, comment="课程类型：formal-正式课, trial-试听课")
    course = relationship("Course", back_populates="schedules")
    teacher = relationship("Teacher", back_populates="schedules")
    class_ = relationship("Class", back_populates="schedules")
    room = relationship("Room", back_populates="schedules")
    scheduled_students = relationship("Student", secondary=schedule_student, backref="scheduled_schedules")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    condition_type = Column(String(50), nullable=False)
    description = Column(Text)
    is_hard_constraint = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='course_admin', nullable=False)  # 'super_admin', 'system_admin', 'course_admin', 'system_audit'
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    is_admin = Column(Boolean, default=False)  # 保留兼容性
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 定义反向关系，方便查询
    teacher = relationship("Teacher", back_populates="user_account")

class PasswordResetRequest(Base):
    __tablename__ = "password_reset_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(50), nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'completed', 'rejected'
    user = relationship("User")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    level = Column(String(10))
    message = Column(Text)
    user = Column(String(50))

class StudentFee(Base):
    """学生课时费记录表"""
    __tablename__ = "student_fees"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, comment="学生ID")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="科目ID")
    start_date = Column(DateTime, nullable=True, comment="起算日期")
    hourly_fee = Column(Float, nullable=False, comment="课时费/小时")
    total_receivable_amount = Column(Float, default=0.0, comment="总应收金额")
    total_actual_amount = Column(Float, default=0.0, comment="总实收金额")
    total_refund_amount = Column(Float, default=0.0, comment="总退费金额")
    total_lesson_count = Column(Float, default=0.0, comment="累计新增课节数")
    consumed_hours = Column(Float, default=0.0, comment="已消耗课时数（小时）")
    remaining_amount = Column(Float, default=0.0, comment="剩余费用")
    remaining_hours = Column(Float, default=0.0, comment="剩余课时（小时）")
    alert_threshold = Column(Float, default=5.0, comment="预警阈值（剩余课时低于此值时提醒）")
    is_active = Column(Boolean, default=True, comment="是否启用")
    payment_method = Column(String(50), default='', comment="收费途径")
    student = relationship("Student", backref="fees")
    course = relationship("Course", backref="student_fees")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class FeeLog(Base):
    """课时费日志表"""
    __tablename__ = "fee_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, comment="学生ID")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="科目ID")
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True, comment="课程安排ID（完训消耗时关联）")
    log_type = Column(String(20), nullable=False, comment="日志类型：payment-缴费, refund-退费, consume-消耗")
    amount = Column(Float, nullable=False, comment="金额（正数表示增加，负数表示减少）")
    receivable_amount = Column(Float, default=0.0, comment="应收金额（缴费时记录）")
    hours = Column(Float, default=0.0, comment="课时（消耗时记录）")
    remaining_amount = Column(Float, nullable=False, comment="剩余费用")
    remaining_hours = Column(Float, default=0.0, comment="剩余课时")
    payment_date = Column(Date, nullable=True, comment="缴费日期")
    refund_date = Column(Date, nullable=True, comment="退费日期")
    description = Column(Text, comment="描述")
    student = relationship("Student", backref="fee_logs")
    course = relationship("Course", backref="fee_logs")
    schedule = relationship("Schedule", backref="fee_logs")
    created_at = Column(DateTime, default=datetime.now)

class Settings(Base):
    """站点参数表"""
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String(200), nullable=False, comment="机构名称")
    site_logo = Column(String(500), comment="机构LOGO")
    site_url = Column(String(500), comment="本站内网IP（用于构建文件访问地址，满足图片文件上传下载，必须填写真实准确有效的内网IP地址）")
    organization_website = Column(String(500), comment="机构宣传网站链接")
    wechat_qrcode = Column(String(500), comment="公众号二维码图片URL")
    work_wechat_qrcode = Column(String(500), comment="企业微信二维码图片URL")
    wechat_webhook_config = Column(Text, comment="微信通知配置(JSON格式)，存储不同类型消息对应的Webhook URL")
    notification_settings = Column(Text, nullable=True, default="{}")
    email_config = Column(Text, nullable=True, default="{}", comment="邮件配置(JSON格式)：SMTP服务器、端口、用户、密码等")
    email_notification_settings = Column(Text, nullable=True, default="{}", comment="邮件通知设置(JSON格式)：课程提醒、作业通知等")
    teacher_visibility_restricted = Column(Boolean, default=True, comment="课程管理员可见性限制开关：True-课程管理员只能看到自己相关的内容，False-课程管理员可以看到所有内容")
    subject_teachers = Column(Text, default="[]", comment="课程管理导师ID列表(逗号分隔)")
    fee_managers = Column(Text, default="[]", comment="费用管理导师ID列表(逗号分隔)")
    grade_managers = Column(Text, default="[]", comment="成绩管理导师ID列表(逗号分隔)")
    evaluation_managers = Column(Text, default="[]", comment="评价管理导师ID列表(逗号分隔)")
    operation_managers = Column(Text, default="[]", comment="运营管理导师ID列表(JSON格式)")
    schedule_edit_restricted = Column(Boolean, default=True, comment="课程安排编辑限制：True-仅超级管理员可编辑已完训/延期/取消的课程，False-课程管理导师也可编辑")
    schedule_delete_restricted = Column(Boolean, default=True, comment="课程安排删除限制：True-仅超级管理员可删除已完训/延期/取消的课程，False-课程管理导师也可删除")
    log_enabled = Column(Boolean, default=True, comment="是否启用日志记录")
    log_level = Column(String(10), default="INFO", comment="日志级别：DEBUG, INFO, WARNING, ERROR")
    log_debug_enabled = Column(Boolean, default=False, comment="是否启用DEBUG级别日志")
    frontend_log_enabled = Column(Boolean, default=True, comment="是否启用前端日志记录")
    ai_config = Column(Text, nullable=True, default="{}", comment="人工智能配置(JSON格式)：API提供商、API地址、API密钥等")
    ldap_enabled = Column(Boolean, default=False, comment="是否启用LDAP认证")
    ldap_config = Column(Text, nullable=True, default="{}", comment="LDAP配置(JSON格式)：服务器地址、端口、DN、密码等")
    open_registration_enabled = Column(Boolean, default=False, comment="是否启用开放注册")
    open_registration_expiry = Column(DateTime, nullable=True, comment="开放注册到期时间（开启3天后自动关闭）")
    hours_per_lesson = Column(Float, default=2.0, comment="每节课课时数（小时），默认2.0")
    course_config = Column(Text, nullable=True, default="{}", comment="课程配置(JSON格式)：考试阶段等")
    license_key = Column(Text, nullable=True, comment="授权License Key")
    premium_features = Column(Text, nullable=True, default="{}", comment="已激活的高级功能(JSON格式)")
    deactivated_licenses = Column(Text, nullable=True, default="[]", comment="已停用的License历史记录(JSON数组)")
    auto_backup_config = Column(Text, nullable=True, default="{}", comment="自动备份配置(JSON格式)：enabled、frequency、keep_count等")
    session_timeout_minutes = Column(Integer, default=1440, comment="登录超时时间（分钟），默认1440分钟即24小时")
    referral_code = Column(String(64), nullable=True, unique=True, comment="客户专属推荐码")
    referral_threshold = Column(Float, nullable=True, default=0, comment="推荐码激活门槛金额（元），实际花费超过此值才激活推荐码")
    referral_activated = Column(Boolean, default=False, comment="推荐码是否已激活")
    discount_percent = Column(Float, nullable=True, default=0, comment="第三方折扣百分比，如10表示10%")
    rebate_percent = Column(Float, nullable=True, default=0, comment="推荐人奖励百分比，如5表示5%")
    contact_person = Column(String(100), nullable=True, default='', comment="联系人")
    contact_phone = Column(String(20), nullable=True, default='', comment="联系电话")
    contact_email = Column(String(100), nullable=True, default='', comment="联系邮箱")
    contact_wechat = Column(String(100), nullable=True, default='', comment="联系微信")
    total_spending = Column(Float, default=0, comment="客户累计实际花费（元）")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Holiday(Base):
    """节假日表"""
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, comment="节假日日期")
    name = Column(String(100), nullable=False, comment="节假日名称")
    description = Column(Text, comment="节假日描述")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class CourseEvaluationTemplate(Base):
    """科目评价模板表"""
    __tablename__ = "course_evaluation_templates"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, comment="关联科目ID（NULL表示通用模板）")
    template_name = Column(String(100), nullable=False, comment="模板名称")
    subject_type = Column(String(50), nullable=False, comment="学科类型：language/math/science/humanities/art/sports/custom")
    dimensions = Column(JSONB, nullable=False, comment='评价维度配置 [{"name":"听力理解","description":"...","weight":1.0}, ...]')
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    course = relationship("Course", backref="evaluation_templates")

class StudentComprehensiveEvaluation(Base):
    """学员综合能力评价表"""
    __tablename__ = "student_comprehensive_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, comment="学员ID")
    eval_period = Column(String(50), nullable=False, comment="评价周期，如：2026年春季")
    profile_type = Column(String(50), default="academic", comment="画像类型：academic-学习态度/知识掌握/实践能力/创新思维/协作素养，virtue-德智体美劳")
    attitude_score = Column(Float, nullable=True, comment="学习态度/德 (1-5)")
    knowledge_score = Column(Float, nullable=True, comment="知识掌握/智 (1-5)")
    practice_score = Column(Float, nullable=True, comment="实践能力/体 (1-5)")
    innovation_score = Column(Float, nullable=True, comment="创新思维/美 (1-5)")
    collaboration_score = Column(Float, nullable=True, comment="协作素养/劳 (1-5)")
    overall_comment = Column(Text, comment="综合评语")
    evaluator_id = Column(Integer, ForeignKey("teachers.id"), nullable=True, comment="评价导师ID")
    eval_date = Column(DateTime, nullable=True, comment="评价日期")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    student = relationship("Student", backref="comprehensive_evaluations")
    evaluator = relationship("Teacher", backref="given_comprehensive_evaluations")

class StudentSubjectEvaluation(Base):
    """学员单科能力评价表"""
    __tablename__ = "student_subject_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, comment="学员ID")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="科目ID")
    template_id = Column(Integer, ForeignKey("course_evaluation_templates.id"), nullable=True, comment="评价模板ID")
    eval_period = Column(String(50), nullable=False, comment="评价周期")
    dimension_scores = Column(JSONB, nullable=False, comment='各维度得分 {"听力理解":4,"口语表达":3,...}')
    average_score = Column(Float, nullable=True, comment="维度均分")
    comment = Column(Text, comment="单科评语")
    strengths = Column(Text, comment="优势/亮点")
    improvements = Column(Text, comment="待提升方面")
    evaluator_id = Column(Integer, ForeignKey("teachers.id"), nullable=True, comment="评价导师ID")
    eval_date = Column(DateTime, nullable=True, comment="评价日期")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    student = relationship("Student", backref="subject_evaluations")
    course = relationship("Course", backref="student_evaluations")
    template = relationship("CourseEvaluationTemplate", backref="evaluations")
    evaluator = relationship("Teacher", backref="given_subject_evaluations")

class SmartCommandExample(Base):
    __tablename__ = "smart_command_examples"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, comment="分类：course_management/teacher_management/student_management等")
    action_name = Column(String(100), nullable=False, comment="动作名称：添加科目、创建排课等")
    example_text = Column(Text, nullable=False, comment="示例指令文本")
    expected_intent = Column(String(50), nullable=True, comment="预期意图标识")
    expected_fields = Column(JSONB, default=lambda: {}, comment="预期字段(JSON格式)")
    description = Column(Text, nullable=True, comment="描述说明")
    is_active = Column(Boolean, default=True, comment="是否激活")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class RegistrationToken(Base):
    __tablename__ = "registration_tokens"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, index=True, comment="注册邮箱")
    username = Column(String(50), nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    token = Column(String(255), nullable=False, unique=True, index=True, comment="确认令牌")
    is_used = Column(Boolean, default=False, comment="是否已使用")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    created_at = Column(DateTime, default=datetime.now)