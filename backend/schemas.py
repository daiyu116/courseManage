# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date,datetime

class CourseBase(BaseModel):
    code: str = Field(..., description="科目代码")
    name: str = Field(..., description="科目名称")
    priority: int = Field(default=0, description="优先级")

class CourseCreate(CourseBase):
    teacher_ids: List[int] = Field(default=[], description="授课导师ID列表")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    teacher_ids: Optional[List[int]] = None

class Course(CourseBase):
    id: int
    teacher_ids: List[int] = []
    teachers: List[dict] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailConfigRequest(BaseModel):
    smtp_host: str = Field(..., description="SMTP服务器")
    smtp_port: int = Field(465, description="SMTP端口")
    smtp_user: str = Field(..., description="发送邮箱")
    smtp_password: str = Field(..., description="邮箱密码/授权码")
    smtp_from_name: str = Field(..., description="发件人名称")
    smtp_ssl: bool = Field(True, description="使用SSL")

class SendEmailHomeworkRequest(BaseModel):
    class_id: int = Field(..., description="班级ID")
    course_name: str = Field(..., description="课程名称")
    class_homework: str = Field(..., description="随堂作业")
    regular_homework: str = Field(..., description="常规作业")
    images: Optional[List[str]] = Field(None, description="作业图片URL列表")

class TeacherBase(BaseModel):
    code: str = Field(..., description="导师代码")
    name: str = Field(..., description="导师姓名")
    join_date: Optional[date] = Field(None, description="进入机构日期")
    title: Optional[str] = Field(None, description="职称")
    department: Optional[str] = Field(None, description="部门")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="电子邮箱")
    max_weekly_hours: int = Field(40, description="最大周课时")
    available_days: str = Field("1,2,3,4,5,6,7", description="日常可排课日")
    available_time_slots: str = Field("08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30", description="可排课时间段")
    allow_holiday_scheduling: bool = Field(False, description="节假日可排课")
    no_feedback_required: bool = Field(False, description="无需反馈")
    is_active: bool = Field(True, description="是否本机构在职")
    end_date: Optional[date] = Field(None, description="离职日期")

class TeacherCreate(TeacherBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    join_date: Optional[date] = None
    title: Optional[str] = None
    department: Optional[str] = None
    max_weekly_hours: Optional[int] = None
    available_days: Optional[str] = None
    available_time_slots: Optional[str] = None
    allow_holiday_scheduling: Optional[bool] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    no_feedback_required: Optional[bool] = None
    is_active: Optional[bool] = None
    end_date: Optional[date] = None

class Teacher(TeacherBase):
    id: int
    course_ids: List[int] = []
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    join_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    end_date: Optional[date] = None
    no_feedback_required: Optional[bool] = None

    class Config:
        from_attributes = True

class ClassBase(BaseModel):
    code: str = Field(..., description="班级代码")
    name: str = Field(..., description="班级名称")
    description: Optional[str] = Field(None, description="班级描述")
    is_active: bool = Field(default=True, description="是否启用")

class ClassCreate(ClassBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    wechat_webhook: Optional[str] = None

class Class(ClassBase):
    id: int
    wechat_webhook: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    code: str = Field(..., description="学员代码")
    name: str = Field(..., description="学员姓名")
    school: Optional[str] = Field(None, description="学校")
    grade: Optional[str] = Field(None, description="年级")
    enrollment_date: Optional[date] = Field(None, description="进入机构日期")
    # 删除 class_id: Optional[int] = Field(None, description="班级ID")
    # 添加：class_ids: List[int] = Field(default=[], description="班级ID列表")
    class_ids: List[int] = Field(default=[], description="班级ID列表")
    available_days: str = Field("1,2,3,4,5,6,7", description="日常可排课日")
    available_time_slots: str = Field("08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30", description="可排课时间段")
    allow_holiday_scheduling: bool = Field(False, description="节假日可排课")
    contact_person: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系方式")
    email: Optional[str] = Field(None, description="电子邮箱")
    is_active: bool = Field(True, description="是否本机构在读")
    end_date: Optional[date] = Field(None, description="结束日期")

class StudentCreate(StudentBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
    enrollment_date: Optional[date] = None
    # 删除 class_id: Optional[int] = None
    # 添加：class_ids: Optional[List[int]] = None
    class_ids: Optional[List[int]] = None
    available_days: Optional[str] = None
    available_time_slots: Optional[str] = None
    allow_holiday_scheduling: Optional[bool] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    end_date: Optional[date] = None

class Student(StudentBase):
    id: int
    class_ids: List[int] = []
    classes: List[dict] = []
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    end_date: Optional[date] = None

    class Config:
        from_attributes = True

class StudentGradeBase(BaseModel):
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="科目ID")
    exam_date: Optional[datetime] = Field(None, description="考试日期")
    grade_level: str = Field(..., description="年级")
    exam_stage: str = Field(..., description="考试阶段")
    score: float = Field(..., description="当次考试成绩")
    total_score: float = Field(..., gt=0, description="当次科目总分（必填，必须大于0）")
    description: Optional[str] = Field(None, description="备注")

class StudentGradeCreate(StudentGradeBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class StudentGradeUpdate(BaseModel):
    course_id: Optional[int] = None
    exam_date: Optional[datetime] = None
    grade_level: Optional[str] = None
    exam_stage: Optional[str] = None
    score: Optional[float] = None
    total_score: Optional[float] = Field(None, gt=0, description="当次科目总分（如填写则必须大于0）")
    description: Optional[str] = None

class BatchGradeCreate(BaseModel):
    grades: List[StudentGradeCreate] = Field(..., min_items=1, description="成绩列表，至少包含一条记录")

class StudentGrade(StudentGradeBase):
    id: int
    score_change: Optional[float] = None
    # 学生相关信息（扁平化）
    student_name: Optional[str] = None
    student_school: Optional[str] = None
    student_grade_info: Optional[str] = None
    student_contact_person: Optional[str] = None
    student_contact_phone: Optional[str] = None
    student_classes: Optional[List[dict]] = []
    student_is_active: Optional[bool] = None
    # 课程相关信息（扁平化）
    course_name: Optional[str] = None
    course_teachers: Optional[List[dict]] = []
    # 保留原有字段以兼容
    student: Optional[Student] = None
    course: Optional[Course] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class GradeTrendData(BaseModel):
    date: str
    score: float
    ratio: Optional[float] = None
    total_score: Optional[float] = None
    score_change: Optional[float] = None

class RoomBase(BaseModel):
    code: str = Field(..., description="教室代码")
    name: str = Field(..., description="教室名称")
    location: Optional[str] = Field(None, description="教室位置")
    capacity: int = Field(default=30, description="容量")
    facilities: str = Field(default="普通", description="设施")
    facility_details: str = Field(default="", description="设施内容")
    is_active: bool = Field(default=True, description="是否启用")

class RoomCreate(RoomBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    facilities: Optional[str] = None
    facility_details: Optional[str] = None
    is_active: Optional[bool] = None

class Room(RoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LeaveBase(BaseModel):
    leave_type: str = Field(..., description="请假类型")
    teacher_id: Optional[int] = Field(None, description="导师ID")
    student_id: Optional[int] = Field(None, description="学员ID")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    reason: Optional[str] = Field(None, description="请假原因")

class LeaveCreate(LeaveBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class LeaveUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    reason: Optional[str] = None

class Leave(LeaveBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CourseInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class TeacherInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class ClassInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class RoomInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class ScheduleBase(BaseModel):
    course_id: int = Field(..., description="科目ID")
    teacher_id: int = Field(..., description="导师ID")
    class_id: int = Field(..., description="班级ID")
    room_type: str = Field(default="offline_physical", description="教室类型：offline_physical-线下物理, online_virtual-线上虚拟")
    meeting_link: Optional[str] = Field(None, description="会议室链接（线上虚拟课程必填）")
    room_id: Optional[int] = Field(None, description="教室ID（线下物理课程必填）")
    day_of_week: int = Field(..., ge=1, le=7, description="星期几(1-7)")
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间")
    start_date: date = Field(..., description="课程开始日期")
    end_date: date = Field(..., description="课程结束日期")
    execution_status: str = Field(default="pending", description="执行状态：pending-待执行, completed-完训, postponed-延期, cancelled-取消")
    content_feedback: str = Field(default="", description="内容反馈")
    cancel_reason: str = Field(default="", description="取消原因")
    schedule_type: str = Field(default="formal", description="课程类型：formal-正式课, trial-试听课")

class ScheduleCreate(ScheduleBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    send_notification: bool = Field(default=True, description="是否发送通知")

class ScheduleUpdate(BaseModel):
    course_id: Optional[int] = None
    teacher_id: Optional[int] = None
    class_id: Optional[int] = None
    room_type: Optional[str] = None
    meeting_link: Optional[str] = None
    room_id: Optional[int] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    execution_status: Optional[str] = None
    homework_regular: Optional[str] = None
    homework_images: Optional[str] = None
    content_feedback: Optional[str] = None
    cancel_reason: Optional[str] = None
    postpone_reason: Optional[str] = None
    schedule_type: Optional[str] = None
    send_notification: bool = Field(default=False, description="是否发送通知")

class StudentAttendanceInfo(BaseModel):
    id: int
    name: str
    attendance_status: str

class Schedule(ScheduleBase):
    id: int
    course: Optional[CourseInfo] = None
    teacher: Optional[TeacherInfo] = None
    class_: Optional[ClassInfo] = None
    room_type: str
    meeting_link: Optional[str] = None
    room: Optional[RoomInfo] = None
    has_conflict: bool
    conflict_reason: Optional[str]
    execution_status: str
    homework_regular: Optional[str] = None
    homework_images: Optional[str] = None
    scheduled_students: Optional[List[StudentAttendanceInfo]] = Field(None, description="参与课程的学员列表及出勤状态")
    schedule_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScheduleCompleteFeedback(BaseModel):
    content_feedback: str = Field(..., description="课程反馈：内容|作业|注意|；格式说明：用|分隔，如：内容：我是谁？我来自哪里？我往那里去？|作业：今天布置的10道题|注意：注意第三题的解题思路")
    student_attendance: Optional[Dict[int, str]] = Field(None, description="学员出勤状态字典，key为学员ID，value为出勤状态(present/absent/leave)")
    absence_reasons: Optional[Dict[int, str]] = Field(None, description="缺勤原因字典，key为学员ID，value为缺勤原因")
    send_notification: bool = Field(default=False, description="是否发送通知")

class ScheduleAttendanceUpdate(BaseModel):
    student_attendance: Dict[int, str] = Field(..., description="学员出勤状态字典，key为学员ID，value为出勤状态(present/absent/leave)")
    absence_reasons: Optional[Dict[int, str]] = Field(None, description="缺勤原因字典，key为学员ID，value为缺勤原因")

class SchedulePostpone(BaseModel):
    start_date: datetime = Field(..., description="新的开始日期")
    end_date: datetime = Field(..., description="新的结束日期")
    start_time: str = Field(..., description="新的开始时间")
    end_time: str = Field(..., description="新的结束时间")
    postpone_reason: str = Field(..., description="延期原因")
    send_notification: bool = Field(default=False, description="是否发送通知")

class ScheduleMakeup(BaseModel):
    start_date: datetime = Field(..., description="补课开始日期")
    end_date: datetime = Field(..., description="补课结束日期")
    start_time: str = Field(..., description="补课开始时间")
    end_time: str = Field(..., description="补课结束时间")
    student_ids: List[int] = Field(..., description="补课学员ID列表")
    room_id: int = Field(..., description="补课教室ID")

class ScheduleDeclineMakeup(BaseModel):
    student_ids: List[int] = Field(..., description="不补课学员ID列表")
    declined_reason: str = Field(..., description="不补课原因")

class ScheduleCancel(BaseModel):
    cancel_reason: str = Field(..., description="取消原因")
    send_notification: bool = Field(default=False, description="是否发送通知")

class ScheduleFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    teacher_id: Optional[int] = None
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    room_id: Optional[int] = None
    day_of_week: Optional[int] = None

class ConditionBase(BaseModel):
    name: str = Field(..., description="条件名称")
    condition_type: str = Field(..., description="条件类型")
    description: Optional[str] = Field(None, description="条件描述")
    is_hard_constraint: bool = Field(default=True, description="是否为硬性约束")
    is_active: bool = Field(default=True, description="是否启用")

class ConditionCreate(ConditionBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class ConditionUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Condition(ConditionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HomeworkAssignment(BaseModel):
    class_homework: str = Field(..., description="随堂作业")
    regular_homework: str = Field(..., description="常规作业")

class WeChatMessage(BaseModel):
    webhook_url: str = Field(..., description="企业微信群Webhook地址")
    message: str = Field(..., description="消息内容")

class UserBase(BaseModel):
    username: str = Field(..., description="用户名")
    role: str = Field(default='course_admin', description="角色：super_admin(超级管理员), system_admin(系统管理员), course_admin(课程管理员), system_audit(系统审计员)")

class UserCreate(UserBase):
    password: str = Field(..., description="密码")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class User(UserBase):
    id: int
    role: str
    teacher_id: Optional[int] = None
    is_admin: bool
    must_change_password: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class PasswordResetRequestBase(BaseModel):
    username: str = Field(..., description="用户名")

class PasswordResetRequestCreate(PasswordResetRequestBase):
    pass

class PasswordResetRequestUpdate(BaseModel):
    status: str = Field(..., description="状态：pending, completed, rejected")

class PasswordResetRequest(PasswordResetRequestBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    new_password: str = Field(..., description="新密码")

class Token(BaseModel):
    access_token: str
    token_type: str
    user: 'User'
    is_admin: bool
    is_subject_teacher: bool = False

class UserManagementCreate(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="初始密码")
    role: str = Field(default='course_admin', description="角色：super_admin, system_admin, course_admin, system_audit")
    teacher_id: Optional[int] = None

class UserManagementUpdate(BaseModel):
    password: Optional[str] = Field(None, description="输入新密码")
    role: Optional[str] = Field(None, description="角色：super_admin, system_admin, course_admin, system_audit")
    teacher_id: Optional[int] = None

class PasswordChange(BaseModel):
    old_password: str = Field(..., description="输入旧密码")
    new_password: str = Field(..., description="输入新密码")
    confirm_password: str = Field(..., description="确认新密码")

class PasswordVerify(BaseModel):
    password: str = Field(..., description="待验证的密码")

class ConflictInfo(BaseModel):
    schedule_id: int
    conflict_type: str
    conflict_description: str
    related_schedules: List[int] = []

class StudentFeeBase(BaseModel):
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="科目ID")
    start_date: Optional[datetime] = Field(None, description="起算日期")
    hourly_fee: float = Field(..., ge=0, description="课时费/小时")
    total_receivable_amount: float = Field(0.0, ge=0, description="累计应收金额")
    total_actual_amount: float = Field(0.0, ge=0, description="累计实收金额")
    total_refund_amount: float = Field(0.0, ge=0, description="累计退费金额")
    total_lesson_count: float = Field(0.0, ge=0, description="累计新增课节数")
    consumed_hours: float = Field(0.0, ge=0, description="已消耗课时数（小时）")
    remaining_hours: float = Field(0.0, description="剩余课时（小时），负数表示欠课时")
    alert_threshold: float = Field(6.0, ge=0, description="预警阈值（剩余课时低于此值时提醒）")
    is_active: bool = Field(True, description="是否启用")
    payment_method: str = Field('', description="收费途径")

class StudentFeeCreate(BaseModel):
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="科目ID")
    start_date: Optional[datetime] = Field(None, description="起算日期")
    hourly_fee: float = Field(..., ge=0, description="课时费/小时")
    lesson_count: float = Field(..., ge=0, description="本次新增课节数")
    discount_amount: float = Field(0.0, ge=0, description="本次优惠金额")
    payment_date: Optional[date] = Field(None, description="收费日期")
    payment_method: str = Field('', description="收费途径")
    alert_threshold: float = Field(6.0, ge=0, description="预警阈值（剩余课时低于此值时提醒）")
    is_active: bool = Field(True, description="是否启用")

class StudentFeeUpdate(BaseModel):
    start_date: Optional[datetime] = None
    hourly_fee: Optional[float] = None
    alert_threshold: Optional[float] = None
    is_active: Optional[bool] = None

class StudentFee(StudentFeeBase):
    id: int
    student_name: str = ""
    course_name: str = ""
    student_school: str = ""
    student_grade: str = ""
    student_contact_person: str = ""
    student_contact_phone: str = ""
    student_classes: List[dict] = []
    student_is_active: bool = True
    course_teachers: List[dict] = []
    total_actual_amount: float = 0.0
    total_refund_amount: float = 0.0
    consumed_hours: float = 0.0
    consumed_schedules: List[dict] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FeeLogBase(BaseModel):
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="科目ID")
    schedule_id: Optional[int] = None
    log_type: str = Field(..., description="日志类型：payment-收费, refund-退费, consume-消耗")
    amount: float = Field(..., description="金额")
    receivable_amount: float = Field(0.0, description="应收金额")
    hours: float = Field(0.0, description="课时")
    remaining_amount: float = Field(..., description="剩余费用")
    remaining_hours: float = Field(..., description="剩余课时")
    description: Optional[str] = None


class FeeLogCreate(FeeLogBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class FeeLog(FeeLogBase):
    id: int
    student_name: str = ""
    course_name: str = ""
    schedule_date: Optional[str] = None
    schedule_time: Optional[str] = None
    teacher_name: Optional[str] = None
    class_name: Optional[str] = ""
    room_name: Optional[str] = ""
    content_feedback: Optional[str] = ""
    is_makeup: bool = False
    is_postponed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="科目ID")
    lesson_count: float = Field(..., ge=0, description="本次新增课节数")
    discount_amount: float = Field(0.0, ge=0, description="本次优惠金额")
    payment_date: Optional[date] = Field(None, description="收费日期")
    payment_method: str = Field('', description="收费途径")
    description: Optional[str] = None

class RefundRequest(BaseModel):
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="科目ID")
    amount: float = Field(..., gt=0, description="退费金额")
    refund_date: Optional[date] = Field(None, description="退费日期")
    refund_reason: Optional[str] = Field(None, description="退费说明")
    description: Optional[str] = None

class AlertThresholdUpdate(BaseModel):
    alert_threshold: float = Field(..., gt=0, description="预警阈值")

class SettingsBase(BaseModel):
    site_name: str = Field(..., description="机构名称")
    site_logo: Optional[str] = Field(None, description="机构LOGO")
    site_url: str = Field(..., description="本站内网真实IP地址（用于构建文件访问地址，如：10.11.12.99，必须准确填写否则文件无法上传和访问）")
    organization_website: Optional[str] = Field(None, description="机构宣传网站链接")
    wechat_qrcode: Optional[str] = Field(None, description="公众号二维码图片URL")
    work_wechat_qrcode: Optional[str] = Field(None, description="企业微信二维码图片URL")
    wechat_webhook_config: Optional[str] = Field(None, description="微信通知配置(JSON字符串)")
    notification_settings: Optional[str] = Field(None, description="通知提醒配置(JSON字符串)")
    email_config: Optional[str] = Field(None, description="邮件配置(JSON字符串)")
    email_notification_settings: Optional[str] = Field(None, description="邮件通知设置(JSON字符串)")
    teacher_visibility_restricted: Optional[bool] = Field(True, description="课程管理员可见性限制开关")
    subject_teachers: Optional[List[int]] = Field(None, description="课程管理导师ID列表(逗号分隔)")
    fee_managers: Optional[List[int]] = Field(None, description="费用管理导师ID列表(逗号分隔)")
    grade_managers: Optional[List[int]] = Field(None, description="成绩管理导师ID列表(逗号分隔)")
    evaluation_managers: Optional[List[int]] = Field(None, description="评价管理导师ID列表(逗号分隔)")
    operation_managers: Optional[List[int]] = Field(None, description="运营管理导师ID列表")
    schedule_edit_restricted: Optional[bool] = Field(True, description="课程安排编辑限制：True-仅超级管理员可编辑已完训/延期/取消的课程，False-课程管理导师也可编辑")
    schedule_delete_restricted: Optional[bool] = Field(True, description="课程安排删除限制：True-仅超级管理员可删除已完训/延期/取消的课程，False-课程管理导师也可删除")
    log_enabled: Optional[bool] = Field(True, description="是否启用日志记录")
    log_level: Optional[str] = Field("INFO", description="日志级别：DEBUG, INFO, WARNING, ERROR")
    log_debug_enabled: Optional[bool] = Field(False, description="是否启用DEBUG级别日志")
    frontend_log_enabled: Optional[bool] = Field(True, description="是否启用前端日志记录")
    ai_config: Optional[str] = Field(None, description="人工智能配置(JSON字符串)")
    ldap_enabled: Optional[bool] = Field(False, description="是否启用LDAP认证")
    ldap_config: Optional[str] = Field(None, description="LDAP配置(JSON字符串)")
    hours_per_lesson: Optional[float] = Field(2.0, description="每节课课时数（小时），默认2.0")
    course_config: Optional[str] = Field(None, description="课程配置(JSON字符串)：考试阶段等")
    open_registration_enabled: Optional[bool] = Field(False, description="是否启用开放注册")
    open_registration_expiry: Optional[datetime] = Field(None, description="开放注册到期时间")
    session_timeout_minutes: Optional[int] = Field(1440, description="登录超时时间（分钟），默认1440分钟即24小时")
    license_key: Optional[str] = Field(None, description="授权License Key")
    premium_features: Optional[str] = Field(None, description="已激活的高级功能(JSON字符串)")
    contact_person: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    contact_wechat: Optional[str] = Field(None, description="联系微信")

class SettingsCreate(SettingsBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class SettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    site_logo: Optional[str] = None
    site_url: Optional[str] = None
    organization_website: Optional[str] = None
    wechat_qrcode: Optional[str] = None
    work_wechat_qrcode: Optional[str] = None
    wechat_webhook_config: Optional[str] = None
    notification_settings: Optional[str] = None
    email_config: Optional[str] = None
    email_notification_settings: Optional[str] = None
    teacher_visibility_restricted: Optional[bool] = None
    subject_teachers: Optional[List[int]] = []
    fee_managers: Optional[List[int]] = []
    grade_managers: Optional[List[int]] = []
    evaluation_managers: Optional[List[int]] = []
    operation_managers: Optional[List[int]] = []
    schedule_edit_restricted: Optional[bool] = None
    schedule_delete_restricted: Optional[bool] = None
    log_enabled: Optional[bool] = None  # 添加日志启用字段
    log_level: Optional[str] = None  # 添加日志级别字段
    log_debug_enabled: Optional[bool] = None  # 添加DEBUG日志启用字段
    frontend_log_enabled: Optional[bool] = None  # 添加前端日志启用字段
    ai_config: Optional[str] = None
    ldap_enabled: Optional[bool] = None
    ldap_config: Optional[str] = None
    hours_per_lesson: Optional[float] = None
    course_config: Optional[str] = None
    open_registration_enabled: Optional[bool] = None
    open_registration_expiry: Optional[datetime] = None
    license_key: Optional[str] = None
    premium_features: Optional[str] = None
    session_timeout_minutes: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_wechat: Optional[str] = None

class Settings(SettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class HolidayBase(BaseModel):
    date: str = Field(..., description="节假日日期（格式：YYYY-MM-DD）")
    name: str = Field(..., description="节假日名称")
    description: Optional[str] = Field(None, description="节假日描述")

class HolidayCreate(HolidayBase):
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Holiday(HolidayBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedCourseResponse(BaseModel):
    items: List[Course]
    total: int

class PaginatedTeacherResponse(BaseModel):
    items: List[Teacher]
    total: int

class PaginatedClassResponse(BaseModel):
    items: List[Class]
    total: int

class PaginatedStudentResponse(BaseModel):
    items: List[Student]
    total: int

class PaginatedFeeResponse(BaseModel):
    items: List[StudentFee]
    total: int

class PaginatedGradeResponse(BaseModel):
    items: List[StudentGrade]
    total: int

class PaginatedRoomResponse(BaseModel):
    items: List[Room]
    total: int

class PaginatedLeaveResponse(BaseModel):
    items: List[Leave]
    total: int

class PaginatedHolidayResponse(BaseModel):
    items: List[Holiday]
    total: int

class PaginatedConditionResponse(BaseModel):
    items: List[Condition]
    total: int

class PaginatedScheduleResponse(BaseModel):
    items: List[Schedule]
    total: int

# ==================== 智能指令示例相关Schema ====================

class SmartCommandExampleBase(BaseModel):
    category: str
    action_name: str
    example_text: str
    expected_intent: Optional[str] = None
    expected_fields: Optional[dict] = {}
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class SmartCommandExampleCreate(SmartCommandExampleBase):
    pass

class SmartCommandExampleUpdate(BaseModel):
    category: Optional[str] = None
    action_name: Optional[str] = None
    example_text: Optional[str] = None
    expected_intent: Optional[str] = None
    expected_fields: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class SmartCommandExampleResponse(SmartCommandExampleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SmartCommandTestRequest(BaseModel):
    """测试单个指令的请求"""
    command_text: str
    use_ai: Optional[bool] = None  # 如果为None则使用系统配置

class SmartCommandTestResult(BaseModel):
    """测试结果"""
    success: bool
    command_text: str
    parsed_intent: Optional[str] = None
    expected_intent: Optional[str] = None
    intent_match: bool = False
    parsed_fields: Optional[dict] = None
    expected_fields: Optional[dict] = None
    field_comparison: Optional[dict] = None
    message: str
    parse_time_ms: Optional[float] = None

class SmartCommandBatchTestResult(BaseModel):
    """批量测试结果"""
    total: int
    success_count: int
    failed_count: int
    results: List[SmartCommandTestResult]
    test_duration_ms: float

# ==================== 学员评价管理相关Schema ====================

class EvaluationDimensionConfig(BaseModel):
    name: str = Field(..., description="维度名称")
    description: str = Field("", description="维度说明")
    weight: float = Field(1.0, description="权重")

class CourseEvaluationTemplateBase(BaseModel):
    course_id: Optional[int] = Field(None, description="关联科目ID（NULL表示通用模板）")
    template_name: str = Field(..., description="模板名称")
    subject_type: str = Field(..., description="学科类型：language/math/science/humanities/art/sports/custom")
    dimensions: List[EvaluationDimensionConfig] = Field(..., description="评价维度配置")
    is_active: bool = Field(True, description="是否启用")

class CourseEvaluationTemplateCreate(CourseEvaluationTemplateBase):
    pass

class CourseEvaluationTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    subject_type: Optional[str] = None
    dimensions: Optional[List[EvaluationDimensionConfig]] = None
    is_active: Optional[bool] = None

class CourseEvaluationTemplate(CourseEvaluationTemplateBase):
    id: int
    course_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentComprehensiveEvaluationBase(BaseModel):
    student_id: int = Field(..., description="学员ID")
    eval_period: str = Field(..., description="评价周期")
    profile_type: str = Field("academic", description="画像类型：academic-学习态度/知识掌握/实践能力/创新思维/协作素养，virtue-德智体美劳")
    attitude_score: float = Field(..., ge=1, le=5, description="学习态度/德 (1-5)")
    knowledge_score: float = Field(..., ge=1, le=5, description="知识掌握/智 (1-5)")
    practice_score: float = Field(..., ge=1, le=5, description="实践能力/体 (1-5)")
    innovation_score: float = Field(..., ge=1, le=5, description="创新思维/美 (1-5)")
    collaboration_score: float = Field(..., ge=1, le=5, description="协作素养/劳 (1-5)")
    overall_comment: Optional[str] = Field(None, description="综合评语")
    evaluator_id: Optional[int] = Field(None, description="评价导师ID")
    eval_date: Optional[datetime] = Field(None, description="评价日期")

class StudentComprehensiveEvaluationCreate(StudentComprehensiveEvaluationBase):
    pass

class StudentComprehensiveEvaluationUpdate(BaseModel):
    eval_period: Optional[str] = None
    profile_type: Optional[str] = None
    attitude_score: Optional[float] = Field(None, ge=1, le=5)
    knowledge_score: Optional[float] = Field(None, ge=1, le=5)
    practice_score: Optional[float] = Field(None, ge=1, le=5)
    innovation_score: Optional[float] = Field(None, ge=1, le=5)
    collaboration_score: Optional[float] = Field(None, ge=1, le=5)
    overall_comment: Optional[str] = None
    evaluator_id: Optional[int] = None
    eval_date: Optional[datetime] = None

class StudentComprehensiveEvaluation(StudentComprehensiveEvaluationBase):
    id: int
    student_name: Optional[str] = None
    evaluator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentSubjectEvaluationBase(BaseModel):
    student_id: int = Field(..., description="学员ID")
    course_id: int = Field(..., description="科目ID")
    template_id: Optional[int] = Field(None, description="评价模板ID")
    eval_period: str = Field(..., description="评价周期")
    dimension_scores: Dict[str, float] = Field(..., description="各维度得分")
    comment: Optional[str] = Field(None, description="单科评语")
    strengths: Optional[str] = Field(None, description="优势/亮点")
    improvements: Optional[str] = Field(None, description="待提升方面")
    evaluator_id: Optional[int] = Field(None, description="评价导师ID")
    eval_date: Optional[datetime] = Field(None, description="评价日期")

class StudentSubjectEvaluationCreate(StudentSubjectEvaluationBase):
    pass

class StudentSubjectEvaluationUpdate(BaseModel):
    template_id: Optional[int] = None
    eval_period: Optional[str] = None
    dimension_scores: Optional[Dict[str, float]] = None
    comment: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    evaluator_id: Optional[int] = None
    eval_date: Optional[datetime] = None

class StudentSubjectEvaluation(StudentSubjectEvaluationBase):
    id: int
    average_score: Optional[float] = None
    student_name: Optional[str] = None
    course_name: Optional[str] = None
    evaluator_name: Optional[str] = None
    template_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudentEvaluationProfile(BaseModel):
    student_id: int
    student_name: str
    comprehensive_evaluations: List[StudentComprehensiveEvaluation] = []
    subject_evaluations: List[StudentSubjectEvaluation] = []

class PaginatedComprehensiveEvaluationResponse(BaseModel):
    items: List[StudentComprehensiveEvaluation]
    total: int

class PaginatedSubjectEvaluationResponse(BaseModel):
    items: List[StudentSubjectEvaluation]
    total: int

class PaginatedEvaluationTemplateResponse(BaseModel):
    items: List[CourseEvaluationTemplate]
    total: int