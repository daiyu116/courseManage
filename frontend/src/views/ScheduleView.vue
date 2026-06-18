// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="schedule-view">
    <!-- 视图切换 -->
    <el-card class="view-switch-card" style="margin-bottom: 20px;">
      <el-radio-group v-model="viewType" @change="handleViewTypeChange">
        <el-radio-button value="calendar">日历视图</el-radio-button>
        <el-radio-button value="table">表格视图</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- 表格视图 -->
    <el-card v-if="viewType === 'table'" class="schedule-card">
      <!-- 筛选条件 -->
      <el-card class="filter-card" style="margin-bottom: 20px;">
        <el-form :model="filters" class="filter-form">
          <el-row :gutter="10">
            <el-col :span="4.8">
              <el-form-item label="科目" label-width="50px">
                <el-select v-model="filters.courseIds" placeholder="选择科目" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="course in courses"
                      :key="course.id"
                      :label="course.name"
                      :value="course.id"
                    >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="getCourseTeachers(course.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px;">导师:</div>
                          <div v-for="teacher in getCourseTeachers(course.id)" :key="teacher.id" style="margin-bottom: 4px;">
                            {{ teacher.name }}
                          </div>
                        </div>
                        <div v-else>暂无导师</div>
                      </template>
                      <span>{{ course.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item label="导师" label-width="50px">
                <el-select v-model="filters.teacherIds" placeholder="选择导师" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="teacher in teachers"
                      :key="teacher.id"
                      :label="teacher.name"
                      :value="teacher.id"
                    >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="teacher.contact_phone">
                          <div style="font-weight: bold;">联系方式:</div>
                          <div>{{ teacher.contact_phone }}</div>
                        </div>
                        <div v-if="teacher.is_active !== undefined">
                          <div style="font-weight: bold; margin-top: 8px;">在职状态:</div>
                          <div>{{ teacher.is_active ? '在职' : '非在职' }}</div>
                        </div>
                        <div v-if="!teacher.contact_phone && teacher.is_active === undefined">暂无详细信息</div>
                      </template>
                      <span>{{ teacher.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item label="班级" label-width="50px">
                <el-select v-model="filters.classIds" placeholder="选择班级" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="class_ in classes"
                      :key="class_.id"
                      :label="class_.name"
                      :value="class_.id"
                    >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="getActiveClassStudents(class_.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">在读学员:</div>
                          <div v-for="student in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getInactiveClassStudents(class_.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">非在读学员:</div>
                          <div v-for="student in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                          暂无学员
                        </div>
                      </template>
                      <span>{{ class_.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item label="学员" label-width="50px">
                <el-select v-model="filters.studentIds" placeholder="选择学员" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="student in students"
                      :key="student.id"
                      :label="student.name"
                      :value="student.id"
                  >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="student.school">
                          <div style="font-weight: bold;">就读学校:</div>
                          <div>{{ student.school }}</div>
                        </div>
                        <div v-if="student.grade">
                          <div style="font-weight: bold; margin-top: 8px;">年级:</div>
                          <div>{{ student.grade }}</div>
                        </div>
                        <div v-if="student.contact_person">
                          <div style="font-weight: bold; margin-top: 8px;">联系人:</div>
                          <div>{{ student.contact_person }}</div>
                        </div>
                        <div v-if="student.contact_phone">
                          <div style="font-weight: bold; margin-top: 8px;">联系方式:</div>
                          <div>{{ student.contact_phone }}</div>
                        </div>
                        <div v-if="student.is_active !== undefined">
                          <div style="font-weight: bold; margin-top: 8px;">本机构在读状态:</div>
                          <div>{{ student.is_active ? '在读' : '非在读' }}</div>
                        </div>
                        <div v-if="!student.school && !student.grade && !student.contact_person && !student.contact_phone && student.is_active === undefined">
                          暂无详细信息
                        </div>
                      </template>
                      <span>{{ student.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item label="教室" label-width="50px">
                <el-select v-model="filters.roomIds" placeholder="选择教室" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="room in rooms"
                      :key="room.id"
                      :label="room.name"
                      :value="room.id"
                  >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="room.location">
                          <div style="font-weight: bold;">位置:</div>
                          <div>{{ room.location }}</div>
                        </div>
                        <div v-if="room.capacity">
                          <div style="font-weight: bold; margin-top: 8px;">容量:</div>
                          <div>{{ room.capacity }}人</div>
                        </div>
                        <div v-if="room.facilities">
                          <div style="font-weight: bold; margin-top: 8px;">设施:</div>
                          <div>{{ room.facilities }}</div>
                        </div>
                        <div v-if="!room.location && !room.capacity && !room.facilities">
                          暂无详细信息
                        </div>
                      </template>
                      <span>{{ room.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="10">
            <el-col :xs="12" :sm="7" :md="7" :lg="7" :xl="7">
              <el-form-item label="开始日期" label-width="80px">
                  <el-date-picker
                  v-model="filters.startDate"
                  type="date"
                  placeholder="选择开始日期"
                  value-format="YYYY-MM-DD"
                        style="width: 100%"
                  />
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="7" :md="7" :lg="7" :xl="7">
              <el-form-item label="结束日期" label-width="80px">
                  <el-date-picker
                  v-model="filters.endDate"
                  type="date"
                  placeholder="选择结束日期"
                  value-format="YYYY-MM-DD"
                        style="width: 100%"
                  />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="10" :md="10" :lg="10" :xl="10">
              <el-form-item label="星期" label-width="35px">
                  <el-select v-model="filters.daysOfWeek" placeholder="选择星期" clearable multiple collapse-tags collapse-tags-tooltip style="width: 100%">
                  <el-option label="周一" :value="1" />
                  <el-option label="周二" :value="2" />
                  <el-option label="周三" :value="3" />
                  <el-option label="周四" :value="4" />
                  <el-option label="周五" :value="5" />
                  <el-option label="周六" :value="6" />
                  <el-option label="周日" :value="7" />
                  </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="10">
            <el-col :xs="12" :sm="5" :md="5" :lg="5" :xl="5">
              <el-form-item label="冲突状态" label-width="70px">
                  <el-select v-model="filters.hasConflict" placeholder="选择冲突状态" clearable style="width: 100%">
                  <el-option label="有冲突" :value="true" />
                  <el-option label="无冲突" :value="false" />
                  </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="5" :md="5" :lg="5" :xl="5">
              <el-form-item label="执行状态" label-width="70px">
                  <el-select v-model="filters.executionStatus" placeholder="选择执行状态" clearable style="width: 100%">
                  <el-option label="待执行" value="pending" />
                  <el-option label="完训" value="completed" />
                  <el-option label="延期" value="postponed" />
                  <el-option label="取消" value="cancelled" />
                  </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="7" :md="7" :lg="7" :xl="7">
              <el-form-item label-width="0">
                <el-button type="primary" @click="searchSchedules" style="width: 100%">
                  <el-icon><Search /></el-icon>
                  查询
                </el-button>
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="7" :md="7" :lg="7" :xl="7">
              <el-form-item label-width="0">
                  <el-button @click="resetFilters" style="width: 100%">重置</el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
      <template #header>
        <div class="card-header">
          <span>课程安排</span>
          <el-tag v-if="conflictCount > 0" type="danger" size="large">
            发现 {{ conflictCount }} 个冲突
          </el-tag>
        </div>
      </template>
      <el-table :data="schedules" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="科目" width="120">
          <template #default="{ row }">
            {{ getCourseName(row.course_id) }}
          </template>
        </el-table-column>
        <el-table-column label="课程类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.schedule_type === 'trial' ? 'warning' : 'success'" size="small">
              {{ row.schedule_type === 'trial' ? '试听课' : '正式课' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="导师" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light" v-if="getTeacherContact(row.teacher_id)">
              <template #content>
                <div><strong>联系方式：</strong>{{ getTeacherContact(row.teacher_id) }}</div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ getTeacherName(row.teacher_id) }}</span>
            </el-tooltip>
            <span v-else>{{ getTeacherName(row.teacher_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="班级" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light" v-if="getActiveClassStudents(row.class_id).length > 0 || getInactiveClassStudents(row.class_id).length > 0">
              <template #content>
                <div v-if="getActiveClassStudents(row.class_id).length > 0">
                  <div style="color: #67c23a; font-weight: bold; margin-bottom: 5px;">在读学员：</div>
                  <div v-for="student in getActiveClassStudents(row.class_id)" :key="student.id" style="margin-bottom: 3px;">
                    {{ student.name }}
                  </div>
                </div>
                <div v-if="getInactiveClassStudents(row.class_id).length > 0" style="margin-top: 8px;">
                  <div style="color: #909399; font-weight: bold; margin-bottom: 5px;">非在读学员：</div>
                  <div v-for="student in getInactiveClassStudents(row.class_id)" :key="student.id" style="margin-bottom: 3px;">
                    {{ student.name }}
                  </div>
                </div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ getClassName(row.class_id) }}</span>
            </el-tooltip>
            <span v-else>{{ getClassName(row.class_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="教室" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light" v-if="getRoomLocation(row.room_id) || getRoomCapacity(row.room_id) || getRoomFacilities(row.room_id)">
              <template #content>
                <div v-if="getRoomLocation(row.room_id)"><strong>位置：</strong>{{ getRoomLocation(row.room_id) }}</div>
                <div v-if="getRoomCapacity(row.room_id)"><strong>容量：</strong>{{ getRoomCapacity(row.room_id) }}人</div>
                <div v-if="getRoomFacilities(row.room_id)"><strong>设施：</strong>{{ getRoomFacilities(row.room_id) }}</div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ getRoomName(row.room_id) }}</span>
            </el-tooltip>
            <span v-else>{{ getRoomName(row.room_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="星期" width="80">
          <template #default="{ row }">
            {{ getDayOfWeekFromDate(row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">
            {{ row.start_time }} - {{ row.end_time }}
          </template>
        </el-table-column>
        <el-table-column label="开始日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column label="结束日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column label="冲突状态" width="100">
          <template #default="{ row }">
            <el-popover v-if="row.has_conflict" placement="top" :width="800" trigger="hover" @show="loadConflictSchedules(row)">
              <template #reference>
                <el-tag type="danger" style="cursor: pointer;">冲突</el-tag>
              </template>
              <div v-loading="conflictLoading">
                <div v-if="conflictSchedules.length > 0">
                  <el-table :data="conflictSchedules" stripe style="width: 100%">
                    <el-table-column prop="id" label="ID" width="80" />
                    <el-table-column label="科目" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getCourseName(conflictRow.course_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="导师" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getTeacherName(conflictRow.teacher_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="班级" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getClassName(conflictRow.class_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="教室" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getRoomName(conflictRow.room_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="时间" width="160">
                      <template #default="{ row: conflictRow }">
                        {{ formatDate(conflictRow.start_date) }} {{ conflictRow.start_time }}-{{ conflictRow.end_time }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <div v-else>暂无冲突课程</div>
              </div>
            </el-popover>
            <el-tag v-else type="success">无冲突</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行状态" width="100">
          <template #default="{ row }">
            <el-popover placement="top" :width="400" trigger="hover">
              <template #reference>
                <el-tag v-if="row.execution_status === 'completed'" type="success" style="cursor: pointer;">完训</el-tag>
                <el-tag v-else-if="row.execution_status === 'postponed'" type="warning" style="cursor: pointer;">延期</el-tag>
                <el-tag v-else-if="row.execution_status === 'cancelled'" type="info" style="cursor: pointer;">取消</el-tag>
                <el-tag v-else style="cursor: pointer;">待执行</el-tag>
              </template>
              <div v-if="row.execution_status === 'completed'">
                <div v-if="row.content_feedback">
                  <div v-for="(line, index) in parseContentFeedback(row.content_feedback)" :key="index" style="margin-bottom: 8px;">
                    <strong>{{ line.label }}:</strong> {{ line.content }}
                  </div>
                </div>
                <div v-else>暂无反馈</div>
                
                <el-divider v-if="row.scheduled_students && row.scheduled_students.length > 0" />
                
                <div v-if="row.scheduled_students && row.scheduled_students.length > 0">
                  <div style="font-weight: bold; margin-bottom: 8px;">学员出勤情况：</div>
                  <div v-for="student in row.scheduled_students" :key="student.id" style="margin-bottom: 4px; display: flex; align-items: center;">
                    <span style="flex: 1;">{{ student.name }}</span>
                    <el-tag 
                      :type="student.attendance_status === 'present' ? 'success' : student.attendance_status === 'leave' ? 'warning' : 'danger'"
                      size="small"
                    >
                      {{ student.attendance_status === 'present' ? '出席' : student.attendance_status === 'leave' ? '请假' : '缺席' }}
                    </el-tag>
                    <el-tag v-if="student.makeup_status === 'completed'" type="success" size="small" style="margin-left: 4px;">已补课</el-tag>
                    <el-tag v-else-if="student.makeup_status === 'declined'" type="info" size="small" style="margin-left: 4px;">不补课</el-tag>
                  </div>
                </div>
                <el-divider v-if="hasMakeupInfo(row)" />
                <div v-if="hasMakeupInfo(row)">
                  <div style="font-weight: bold; margin-bottom: 8px;">补课信息：</div>
                  <div v-for="student in row.scheduled_students.filter(s => s.makeup_status === 'completed' || s.makeup_status === 'declined')" :key="student.id" style="margin-bottom: 4px;">
                    <strong>{{ student.name }}:</strong>
                    <span v-if="student.makeup_status === 'completed'">已补课 (补课课程ID: {{ student.makeup_schedule_id }})</span>
                    <span v-else-if="student.makeup_status === 'declined'">不补课 (原因: {{ student.declined_reason }})</span>
                  </div>
                </div>
              </div>
              <div v-else-if="row.execution_status === 'postponed'">
                <div v-if="row.postpone_reason">
                  <strong>延期原因:</strong> {{ row.postpone_reason }}
                </div>
                <div v-else>暂无延期原因</div>
              </div>
              <div v-else-if="row.execution_status === 'cancelled'">
                <div v-if="row.cancel_reason">
                  <strong>取消原因:</strong> {{ row.cancel_reason }}
                </div>
                <div v-else>暂无取消原因</div>
              </div>
              <div v-else>
                <strong>状态:</strong> 待执行
              </div>
            </el-popover>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 25, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-card>
    <!-- 班级学员弹窗 -->
    <el-dialog v-model="classStudentsDialogVisible" title="班级学员列表" width="600px">
      <el-table :data="classStudents" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="学员代码" width="120" />
        <el-table-column prop="name" label="学员姓名" width="120" />
        <el-table-column prop="school" label="就读学校" min-width="150" />
        <el-table-column prop="grade" label="就读年级" width="100" />
        <el-table-column label="冲突状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '在读' : '非在读' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="classStudentsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <!-- 日历视图 -->
    <CalendarView v-if="viewType === 'calendar'" :date-range="dateRange" :view-type="calendarViewType" @date-range-change="handleDateRangeChange" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import CalendarView from '@/components/CalendarView.vue'
import api from '@/utils/api'
import dayjs from 'dayjs'

const loading = ref(false)
const schedules = ref([])
const teachers = ref([])
const classes = ref([])
const students = ref([])
const classStudents = ref([])
const classStudentsDialogVisible = ref(false)
const courses = ref([])
const rooms = ref([])
const conflictCount = ref(0)
const viewType = ref('calendar')
const calendarViewType = ref('teacher')
const dateRange = ref([])
const conflictLoading = ref(false)
const conflictSchedules = ref([])

const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

const filters = ref({
  startDate: '',
  endDate: '',
  teacherIds: [],
  classIds: [],
  studentIds: [],
  courseIds: [],
  roomIds: [],
  daysOfWeek: [],
  hasConflict: null,
  executionStatus: null
})

const fetchTeachers = async () => {
  try {
    const response = await api.get('/teachers', { params: { skip: 0, limit: 100000 } })
    teachers.value = Array.isArray(response.data.items) ? response.data.items : (Array.isArray(response.data) ? response.data : [])
  } catch (error) {
    window.logger.error('获取导师列表失败:', error)
    teachers.value = []
  }
}

const fetchClasses = async () => {
  try {
    const response = await api.get('/classes', { params: { skip: 0, limit: 100000 } })
    classes.value = Array.isArray(response.data.items) ? response.data.items : (Array.isArray(response.data) ? response.data : [])
  } catch (error) {
    window.logger.error('获取班级列表失败:', error)
    classes.value = []
  }
}

const fetchStudents = async () => {
  try {
    const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    students.value = Array.isArray(response.data.items) ? response.data.items : (Array.isArray(response.data) ? response.data : [])
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
    students.value = []
  }
}

const showClassStudents = async (classId) => {
  if (!classId) return
  
  try {
    const response = await api.get('/students', { params: { class_id: classId, skip: 0, limit: 100000 } })
    classStudents.value = Array.isArray(response.data.items) ? response.data.items : (Array.isArray(response.data) ? response.data : [])
    classStudentsDialogVisible.value = true
  } catch (error) {
    window.logger.error('获取班级学员失败:', error)
    ElMessage.error('获取班级学员失败')
    classStudents.value = []
  }
}

// 获取导师联系方式
const getTeacherContact = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.contact_phone +" | "+ teacher.email : null
}

// 获取教室位置
const getRoomLocation = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.location : null
}

// 获取教室容量
const getRoomCapacity = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.capacity : null
}

// 获取教室设施
const getRoomFacilities = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.facilities : null
}

const fetchCourses = async () => {
  try {
    const response = await api.get('/courses', { params: { skip: 0, limit: 100000 } })
    courses.value = Array.isArray(response.data.items) ? response.data.items : (Array.isArray(response.data) ? response.data : [])
  } catch (error) {
    window.logger.error('获取科目列表失败:', error)
    courses.value = []
  }
}

const fetchRooms = async () => {
  try {
    const response = await api.get('/rooms', { params: { skip: 0, limit: 100000 } })
    rooms.value = Array.isArray(response.data.items) ? response.data.items : (Array.isArray(response.data) ? response.data : [])
  } catch (error) {
    window.logger.error('获取教室列表失败:', error)
    rooms.value = []
  }
}

const fetchSchedules = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.startDate) params.start_date = filters.value.startDate
    if (filters.value.endDate) params.end_date = filters.value.endDate
    if (filters.value.teacherIds && filters.value.teacherIds.length > 0) params.teacher_ids = filters.value.teacherIds.join(',')
    if (filters.value.classIds && filters.value.classIds.length > 0) params.class_ids = filters.value.classIds.join(',')
    if (filters.value.studentIds && filters.value.studentIds.length > 0) params.student_ids = filters.value.studentIds.join(',')
    if (filters.value.courseIds && filters.value.courseIds.length > 0) params.course_ids = filters.value.courseIds.join(',')
    if (filters.value.roomIds && filters.value.roomIds.length > 0) params.room_ids = filters.value.roomIds.join(',')
    if (filters.value.daysOfWeek && filters.value.daysOfWeek.length > 0) params.days_of_week = filters.value.daysOfWeek.join(',')
    if (filters.value.hasConflict !== null) params.has_conflict = filters.value.hasConflict
    if (filters.value.executionStatus) params.execution_status = filters.value.executionStatus
    params.skip = (pagination.value.currentPage - 1) * pagination.value.pageSize
    params.limit = pagination.value.pageSize

    window.logger.log('[ScheduleView] 请求参数:', params)
    const response = await api.get('/schedules', { params })
    window.logger.log('[ScheduleView] 获取到的排课数据:', response.data)
    schedules.value = response.data.items || []
    pagination.value.total = response.data.total || 0
    window.logger.log('[ScheduleView] schedules.value:', schedules.value)
    conflictCount.value = (response.data.items || []).filter(s => s.has_conflict).length
    window.logger.log('[ScheduleView] conflictCount.value:', conflictCount.value)
  } catch (error) {
    window.logger.error('获取课程安排失败:', error)
    schedules.value = []
    pagination.value.total = 0
    conflictCount.value = 0
  } finally {
    loading.value = false
  }
}

const hasMakeupInfo = (schedule) => {
  if (!schedule.scheduled_students || schedule.scheduled_students.length === 0) return false
  return schedule.scheduled_students.some(student => 
    student.makeup_status === 'completed' || student.makeup_status === 'declined'
  )
}

const getMakeupInfoText = (schedule) => {
  if (!schedule.scheduled_students || schedule.scheduled_students.length === 0) return ''  
  
  const makeupStudents = schedule.scheduled_students.filter(student =>  
    student.makeup_status === 'completed' || student.makeup_status === 'declined'
  )
  
  if (makeupStudents.length === 0) return ''
  
  const lines = []
  makeupStudents.forEach(student => {
    if (student.makeup_status === 'completed') {
      lines.push(`${student.name}: 已补课 (补课课程ID: ${student.makeup_schedule_id})`)
    } else if (student.makeup_status === 'declined') {
      lines.push(`${student.name}: 不补课 (${student.declined_reason})`)
    }
  })
  
  return lines.join('\n')
}

const loadConflictSchedules = async (schedule) => {
  if (!schedule || !schedule.id) return
  
  conflictLoading.value = true
  try {
    const response = await api.get(`/schedules/${schedule.id}/conflicts`)
    conflictSchedules.value = response.data || []
  } catch (error) {
    window.logger.error('获取冲突课程失败:', error)
    ElMessage.error('获取冲突课程失败')
    conflictSchedules.value = []
  } finally {
    conflictLoading.value = false
  }
}

const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchSchedules()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchSchedules()
}

const searchSchedules = () => {
  fetchSchedules()
}

const resetFilters = () => {
  filters.value = {
    startDate: '',
    endDate: '',
    teacherIds: [],
    classIds: [],
    studentIds: [],
    courseIds: [],
    roomIds: [],
    daysOfWeek: [],
    hasConflict: null,
    executionStatus: null
  }
  fetchSchedules()
}

const getCourseName = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? course.name : '-'
}

const getTeacherName = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.name : '-'
}

const getClassName = (classId) => {
  const class_ = classes.value.find(c => c.id === classId)
  return class_ ? class_.name : '-'
}

const getStudentName = (studentId) => {
  const student = students.value.find(s => s.id === studentId)
  return student ? student.name : '-'
}

const getRoomName = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.name : '-'
}

const getDayOfWeekFromDate = (date) => {
  // 转换为与 Python 一致的星期几表示方式（1=周一，7=周日）
  const dayOfWeek = dayjs(date).day() || 7
  const pythonDayOfWeek = dayOfWeek === 0 ? 7 : dayOfWeek
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return days[pythonDayOfWeek - 1] || '-'
}

const getCourseTeachers = (courseId) => {
  if (!Array.isArray(teachers.value)) {
    return []
  }
  return teachers.value.filter(teacher => {
    return teacher.course_ids && Array.isArray(teacher.course_ids) && teacher.course_ids.includes(courseId)
  })
}
const getActiveClassStudents = (classId) => {
  if (!Array.isArray(students.value)) {
    return []
  }
  return students.value.filter(student => {
    const belongsToClass = student.class_ids && Array.isArray(student.class_ids) && student.class_ids.includes(classId)
    const isActive = student.is_active
    return belongsToClass && isActive
  })
}
const getInactiveClassStudents = (classId) => {
  if (!Array.isArray(students.value)) {
    return []
  }
  return students.value.filter(student => {
    const belongsToClass = student.class_ids && Array.isArray(student.class_ids) && student.class_ids.includes(classId)
    const isInactive = !student.is_active
    return belongsToClass && isInactive
  })
}

const getDayOfWeek = (day) => {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return days[day - 1] || '-'
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD')
}

const parseContentFeedback = (feedback) => {
  if (!feedback) return []
  const lines = feedback.split('|').filter(line => line.trim())
  return lines.map(line => {
    const parts = line.split('：')
    if (parts && parts.length >= 2) {
      return {
        label: parts[0].trim(),
        content: parts.slice(1).join('：').trim()
      }
    }
    return {
      label: '反馈',
      content: line.trim()
    }
  })
}

const handleViewTypeChange = () => {
  if (viewType.value === 'calendar') {
    initDateRange()
  } else if (viewType.value === 'table') {
    fetchSchedules()
  }
}

const handleDateRangeChange = (newDateRange) => {
  dateRange.value = newDateRange || []
  if (newDateRange && Array.isArray(newDateRange) && newDateRange.length === 2) {
    filters.value.startDate = newDateRange[0]
    filters.value.endDate = newDateRange[1]
  }
}

const initDateRange = () => {
  const today = dayjs()
  // 获取本周日（使用 endOf('week')）
  const thisSunday = today.endOf('week')
  // 上周六 = 本周日 - 8天（上周日是-7，上周六是-8）
  const lastSaturday = thisSunday.subtract(8, 'day')
  
  dateRange.value = [
    lastSaturday.format('YYYY-MM-DD'),
    thisSunday.format('YYYY-MM-DD')
  ]
  
  // 初始化日期范围后，触发日期变化事件并获取课程安排
  handleDateRangeChange()
  fetchSchedules()
}

onMounted(() => {
  fetchTeachers()
  fetchClasses()
  fetchStudents()
  fetchCourses()
  fetchRooms()
  if (dateRange.value.length === 0) {
    initDateRange()
  } else {
    // 如果已有日期范围，直接获取课程安排
    fetchSchedules()
  }
})
</script>

<style scoped>
.schedule-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 6px;
}

.filter-card {
  margin-bottom: 20px;
}

.view-switch-card {
  text-align: center;
}

.schedule-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 768px) {
  .filter-form :deep(.el-form-item) {
    margin-bottom: 10px;
  }
  
  .filter-form :deep(.el-form-item__label) {
    font-size: 12px;
    padding-right: 5px;
  }
  
  .filter-form :deep(.el-select) {
    width: 100% !important;
  }
  
  .filter-form :deep(.el-date-editor) {
    width: 100% !important;
  }
  
  .filter-form :deep(.el-row) {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  
  .filter-form :deep(.el-col) {
    padding-left: 5px !important;
    padding-right: 5px !important;
  }
  
  .schedule-card :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center !important;
  }
  
  .schedule-card :deep(.el-pagination .el-pagination__total),
  .schedule-card :deep(.el-pagination .el-pagination__sizes),
  .schedule-card :deep(.el-pagination .el-pagination__jump) {
    margin: 5px 0;
  }
  
  .schedule-card :deep(.el-pagination .btn-prev),
  .schedule-card :deep(.el-pagination .btn-next),
  .schedule-card :deep(.el-pagination .el-pager li) {
    min-width: 28px;
    height: 28px;
    line-height: 28px;
    font-size: 12px;
  }
}
</style>