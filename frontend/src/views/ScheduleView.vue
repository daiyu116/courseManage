// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="schedule-view">
    <!-- 视图切换 -->
    <el-card class="view-switch-card" style="margin-bottom: 20px;">
      <el-radio-group v-model="viewType" @change="handleViewTypeChange">
        <el-radio-button value="calendar">{{ t('scheduleView.calendarView') }}</el-radio-button>
        <el-radio-button value="table">{{ t('scheduleView.tableView') }}</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- 表格视图 -->
    <el-card v-if="viewType === 'table'" class="schedule-card">
      <!-- 筛选条件 -->
      <el-card class="filter-card" style="margin-bottom: 20px;">
        <el-form :model="filters" class="filter-form">
          <el-row :gutter="10">
            <el-col :span="4.8">
              <el-form-item :label="t('scheduleView.course')" label-width="50px">
                <el-select v-model="filters.courseIds" filterable :placeholder="t('scheduleView.selectCourse')" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="course in courses"
                      :key="course.id"
                      :label="course.name"
                      :value="course.id"
                    >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="getCourseTeachers(course.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px;">{{ t('scheduleView.teacherInfo') }}</div>
                          <div v-for="teacher in getCourseTeachers(course.id)" :key="teacher.id" style="margin-bottom: 4px;">
                            {{ teacher.name }}
                          </div>
                        </div>
                        <div v-else>{{ t('scheduleView.noTeacher') }}</div>
                      </template>
                      <span>{{ course.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item :label="t('scheduleView.teacher')" label-width="50px">
                <el-select v-model="filters.teacherIds" filterable :placeholder="t('scheduleView.selectTeacher')" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="teacher in teachers"
                      :key="teacher.id"
                      :label="teacher.name"
                      :value="teacher.id"
                    >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="teacher.contact_phone">
                          <div style="font-weight: bold;">{{ t('scheduleView.contactInfo') }}</div>
                          <div>{{ teacher.contact_phone }}</div>
                        </div>
                        <div v-if="teacher.is_active !== undefined">
                          <div style="font-weight: bold; margin-top: 8px;">{{ t('scheduleView.activeStatus') }}</div>
                          <div>{{ teacher.is_active ? t('scheduleView.active') : t('scheduleView.notActive') }}</div>
                        </div>
                        <div v-if="!teacher.contact_phone && teacher.is_active === undefined">{{ t('scheduleView.noDetail') }}</div>
                      </template>
                      <span>{{ teacher.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item :label="t('scheduleView.class')" label-width="50px">
                <el-select v-model="filters.classIds" filterable :placeholder="t('scheduleView.selectClass')" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="class_ in classes"
                      :key="class_.id"
                      :label="class_.name"
                      :value="class_.id"
                    >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="getActiveClassStudents(class_.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('scheduleView.activeStudent') }}</div>
                          <div v-for="student in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getInactiveClassStudents(class_.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('scheduleView.inactiveStudent') }}</div>
                          <div v-for="student in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                          {{ t('scheduleView.noStudent') }}
                        </div>
                      </template>
                      <span>{{ class_.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item :label="t('scheduleView.student')" label-width="50px">
                <el-select v-model="filters.studentIds" filterable :placeholder="t('scheduleView.selectStudent')" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="student in students"
                      :key="student.id"
                      :label="student.name"
                      :value="student.id"
                  >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="student.school">
                          <div style="font-weight: bold;">{{ t('scheduleView.school') }}</div>
                          <div>{{ student.school }}</div>
                        </div>
                        <div v-if="student.grade">
                          <div style="font-weight: bold; margin-top: 8px;">{{ t('scheduleView.grade') }}</div>
                          <div>{{ student.grade }}</div>
                        </div>
                        <div v-if="student.contact_person">
                          <div style="font-weight: bold; margin-top: 8px;">{{ t('scheduleView.contactPerson') }}</div>
                          <div>{{ student.contact_person }}</div>
                        </div>
                        <div v-if="student.contact_phone">
                          <div style="font-weight: bold; margin-top: 8px;">{{ t('scheduleView.contactWay') }}</div>
                          <div>{{ student.contact_phone }}</div>
                        </div>
                        <div v-if="student.is_active !== undefined">
                          <div style="font-weight: bold; margin-top: 8px;">{{ t('scheduleView.isActiveStatus') }}</div>
                          <div>{{ student.is_active ? t('scheduleView.studentActive') : t('scheduleView.studentInactive') }}</div>
                        </div>
                        <div v-if="!student.school && !student.grade && !student.contact_person && !student.contact_phone && student.is_active === undefined">
                          {{ t('scheduleView.noDetail') }}
                        </div>
                      </template>
                      <span>{{ student.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4.8">
              <el-form-item :label="t('scheduleView.room')" label-width="50px">
                <el-select v-model="filters.roomIds" filterable :placeholder="t('scheduleView.selectRoom')" clearable multiple collapse-tags collapse-tags-tooltip style="width: 180px">
                  <el-option
                      v-for="room in rooms"
                      :key="room.id"
                      :label="room.name"
                      :value="room.id"
                  >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="room.location">
                          <div style="font-weight: bold;">{{ t('scheduleView.locationLabel') }}</div>
                          <div>{{ room.location }}</div>
                        </div>
                        <div v-if="room.capacity">
                          <div style="font-weight: bold; margin-top: 8px;">{{ t('scheduleView.capacityLabel') }}</div>
                          <div>{{ t('scheduleView.capacityUnit', { n: room.capacity }) }}</div>
                        </div>
                        <div v-if="room.facilities">
                          <div style="font-weight: bold; margin-top: 8px;">{{ t('scheduleView.facilitiesLabel') }}</div>
                          <div>{{ room.facilities }}</div>
                        </div>
                        <div v-if="!room.location && !room.capacity && !room.facilities">
                          {{ t('scheduleView.noDetail') }}
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
              <el-form-item :label="t('scheduleView.startDate')" label-width="80px">
                  <el-date-picker
                  v-model="filters.startDate"
                  type="date"
                  :placeholder="t('scheduleView.selectStartDate')"
                  value-format="YYYY-MM-DD"
                        style="width: 100%"
                  />
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="7" :md="7" :lg="7" :xl="7">
              <el-form-item :label="t('scheduleView.endDate')" label-width="80px">
                  <el-date-picker
                  v-model="filters.endDate"
                  type="date"
                  :placeholder="t('scheduleView.selectEndDate')"
                  value-format="YYYY-MM-DD"
                        style="width: 100%"
                  />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="10" :md="10" :lg="10" :xl="10">
              <el-form-item :label="t('scheduleView.dayOfWeek')" label-width="35px">
                  <el-select v-model="filters.daysOfWeek" :placeholder="t('scheduleView.selectDayOfWeek')" clearable multiple collapse-tags collapse-tags-tooltip style="width: 100%">
                  <el-option :label="t('scheduleView.mon')" :value="1" />
                  <el-option :label="t('scheduleView.tue')" :value="2" />
                  <el-option :label="t('scheduleView.wed')" :value="3" />
                  <el-option :label="t('scheduleView.thu')" :value="4" />
                  <el-option :label="t('scheduleView.fri')" :value="5" />
                  <el-option :label="t('scheduleView.sat')" :value="6" />
                  <el-option :label="t('scheduleView.sun')" :value="7" />
                  </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="10">
            <el-col :xs="12" :sm="5" :md="5" :lg="5" :xl="5">
              <el-form-item :label="t('scheduleView.conflictStatus')" label-width="70px">
                  <el-select v-model="filters.hasConflict" :placeholder="t('scheduleView.selectConflictStatus')" clearable style="width: 100%">
                  <el-option :label="t('scheduleView.hasConflict')" :value="true" />
                  <el-option :label="t('scheduleView.noConflict')" :value="false" />
                  </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="5" :md="5" :lg="5" :xl="5">
              <el-form-item :label="t('scheduleView.executionStatus')" label-width="70px">
                  <el-select v-model="filters.executionStatus" :placeholder="t('scheduleView.selectExecutionStatus')" clearable style="width: 100%">
                  <el-option :label="t('scheduleView.pending')" value="pending" />
                  <el-option :label="t('scheduleView.completed')" value="completed" />
                  <el-option :label="t('scheduleView.postponed')" value="postponed" />
                  <el-option :label="t('scheduleView.cancelled')" value="cancelled" />
                  </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="7" :md="7" :lg="7" :xl="7">
              <el-form-item label-width="0">
                <el-button type="primary" @click="searchSchedules" style="width: 100%">
                  <el-icon><Search /></el-icon>
                  {{ t('scheduleView.query') }}
                </el-button>
              </el-form-item>
            </el-col>
            <el-col :xs="12" :sm="7" :md="7" :lg="7" :xl="7">
              <el-form-item label-width="0">
                  <el-button @click="resetFilters" style="width: 100%">{{ t('scheduleView.reset') }}</el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('scheduleView.scheduleTitle') }}</span>
          <el-tag v-if="conflictCount > 0" type="danger" size="large">
            {{ t('scheduleView.conflictCount', { n: conflictCount }) }}
          </el-tag>
        </div>
      </template>
      <el-table :data="schedules" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column :label="t('scheduleView.course')" width="120">
          <template #default="{ row }">
            {{ getCourseName(row.course_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.courseType')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.schedule_type === 'trial' ? 'warning' : 'success'" size="small">
              {{ row.schedule_type === 'trial' ? t('scheduleView.trialClass') : t('scheduleView.formalClass') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.teacher')" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light" v-if="getTeacherContact(row.teacher_id)">
              <template #content>
                <div><strong>{{ t('scheduleView.contactLabel') }}</strong>{{ getTeacherContact(row.teacher_id) }}</div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ getTeacherName(row.teacher_id) }}</span>
            </el-tooltip>
            <span v-else>{{ getTeacherName(row.teacher_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.class')" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light" v-if="getActiveClassStudents(row.class_id).length > 0 || getInactiveClassStudents(row.class_id).length > 0">
              <template #content>
                <div v-if="getActiveClassStudents(row.class_id).length > 0">
                  <div style="color: #67c23a; font-weight: bold; margin-bottom: 5px;">{{ t('scheduleView.activeStudentLabel') }}</div>
                  <div v-for="student in getActiveClassStudents(row.class_id)" :key="student.id" style="margin-bottom: 3px;">
                    {{ student.name }}
                  </div>
                </div>
                <div v-if="getInactiveClassStudents(row.class_id).length > 0" style="margin-top: 8px;">
                  <div style="color: #909399; font-weight: bold; margin-bottom: 5px;">{{ t('scheduleView.inactiveStudentLabel') }}</div>
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
        <el-table-column :label="t('scheduleView.room')" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light" v-if="getRoomLocation(row.room_id) || getRoomCapacity(row.room_id) || getRoomFacilities(row.room_id)">
              <template #content>
                <div v-if="getRoomLocation(row.room_id)"><strong>{{ t('scheduleView.locationLabel') }}</strong>{{ getRoomLocation(row.room_id) }}</div>
                <div v-if="getRoomCapacity(row.room_id)"><strong>{{ t('scheduleView.capacityLabel') }}</strong>{{ t('scheduleView.capacityUnit', { n: getRoomCapacity(row.room_id) }) }}</div>
                <div v-if="getRoomFacilities(row.room_id)"><strong>{{ t('scheduleView.facilitiesLabel') }}</strong>{{ getRoomFacilities(row.room_id) }}</div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ getRoomName(row.room_id) }}</span>
            </el-tooltip>
            <span v-else>{{ getRoomName(row.room_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.dayOfWeek')" width="80">
          <template #default="{ row }">
            {{ getDayOfWeekFromDate(row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.timeSlot')" width="160">
          <template #default="{ row }">
            {{ row.start_time }} - {{ row.end_time }}
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.startDate')" width="120">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.endDate')" width="120">
          <template #default="{ row }">
            {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.conflictStatus')" width="100">
          <template #default="{ row }">
            <el-popover v-if="row.has_conflict" placement="top" :width="800" trigger="hover" @show="loadConflictSchedules(row)">
              <template #reference>
                <el-tag type="danger" style="cursor: pointer;">{{ t('scheduleView.conflict') }}</el-tag>
              </template>
              <div v-loading="conflictLoading">
                <div v-if="conflictSchedules.length > 0">
                  <el-table :data="conflictSchedules" stripe style="width: 100%">
                    <el-table-column prop="id" label="ID" width="80" />
                    <el-table-column :label="t('scheduleView.course')" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getCourseName(conflictRow.course_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column :label="t('scheduleView.teacher')" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getTeacherName(conflictRow.teacher_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column :label="t('scheduleView.class')" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getClassName(conflictRow.class_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column :label="t('scheduleView.room')" width="120">
                      <template #default="{ row: conflictRow }">
                        {{ getRoomName(conflictRow.room_id) }}
                      </template>
                    </el-table-column>
                    <el-table-column :label="t('scheduleView.timeSlot')" width="160">
                      <template #default="{ row: conflictRow }">
                        {{ formatDate(conflictRow.start_date) }} {{ conflictRow.start_time }}-{{ conflictRow.end_time }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <div v-else>{{ t('scheduleView.noConflictCourse') }}</div>
              </div>
            </el-popover>
            <el-tag v-else type="success">{{ t('scheduleView.noConflict') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.studentAttendanceStatus')" min-width="200">
          <template #default="{ row }">
            <div v-if="row.scheduled_students && row.scheduled_students.length > 0">
              <el-popover placement="top" :width="360" trigger="hover">
                <template #reference>
                  <div style="cursor: pointer;">
                    <div v-for="student in row.scheduled_students.slice(0, 3)" :key="student.id" style="margin-bottom: 2px; display: flex; align-items: center; gap: 4px;">
                      <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ student.name }}</span>
                      <el-tag :type="getAttendanceTagType(student.attendance_status)" size="small">{{ getAttendanceStatusText(student.attendance_status) }}</el-tag>
                    </div>
                    <div v-if="row.scheduled_students.length > 3" style="color: #909399; font-size: 12px;">
                      {{ t('scheduleView.moreStudents', { n: row.scheduled_students.length - 3 }) }}
                    </div>
                  </div>
                </template>
                <div>
                  <div style="font-weight: bold; margin-bottom: 8px;">{{ t('scheduleView.studentAttendanceStatus') }}</div>
                  <div v-for="student in row.scheduled_students" :key="student.id" style="margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span style="flex: 1;">{{ student.name }}</span>
                    <el-tag :type="getAttendanceTagType(student.attendance_status)" size="small">{{ getAttendanceStatusText(student.attendance_status) }}</el-tag>
                    <el-tag v-if="student.makeup_status === 'completed'" type="success" size="small">{{ t('scheduleView.makeupCompleted') }}</el-tag>
                    <el-tag v-else-if="student.makeup_status === 'pending'" type="warning" size="small">{{ t('scheduleView.makeupPending') }}</el-tag>
                    <el-tag v-else-if="student.makeup_status === 'declined'" type="info" size="small">{{ t('scheduleView.makeupDeclined') }}</el-tag>
                  </div>
                </div>
              </el-popover>
            </div>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.executionStatus')" width="100">
          <template #default="{ row }">
            <el-popover placement="top" :width="400" trigger="hover">
              <template #reference>
                <el-tag v-if="row.execution_status === 'completed'" type="success" style="cursor: pointer;">{{ t('scheduleView.completed') }}</el-tag>
                <el-tag v-else-if="row.execution_status === 'postponed'" type="warning" style="cursor: pointer;">{{ t('scheduleView.postponed') }}</el-tag>
                <el-tag v-else-if="row.execution_status === 'cancelled'" type="info" style="cursor: pointer;">{{ t('scheduleView.cancelled') }}</el-tag>
                <el-tag v-else style="cursor: pointer;">{{ t('scheduleView.pending') }}</el-tag>
              </template>
              <div v-if="row.execution_status === 'completed'">
                <div v-if="row.content_feedback">
                  <div v-for="(line, index) in parseContentFeedback(row.content_feedback)" :key="index" style="margin-bottom: 8px;">
                    <strong>{{ line.label }}:</strong> {{ line.content }}
                  </div>
                </div>
                <div v-else>{{ t('scheduleView.noFeedback') }}</div>
                
                <el-divider v-if="row.scheduled_students && row.scheduled_students.length > 0" />
                
                <div v-if="row.scheduled_students && row.scheduled_students.length > 0">
                  <div style="font-weight: bold; margin-bottom: 8px;">{{ t('scheduleView.studentAttendance') }}</div>
                  <div v-for="student in row.scheduled_students" :key="student.id" style="margin-bottom: 4px; display: flex; align-items: center;">
                    <span style="flex: 1;">{{ student.name }}</span>
                    <el-tag 
                      :type="student.attendance_status === 'present' ? 'success' : student.attendance_status === 'leave' ? 'warning' : 'danger'"
                      size="small"
                    >
                      {{ student.attendance_status === 'present' ? t('scheduleView.present') : student.attendance_status === 'leave' ? t('scheduleView.onLeave') : t('scheduleView.absent') }}
                    </el-tag>
                    <el-tag v-if="student.makeup_status === 'completed'" type="success" size="small" style="margin-left: 4px;">{{ t('scheduleView.makeupCompleted') }}</el-tag>
                    <el-tag v-else-if="student.makeup_status === 'declined'" type="info" size="small" style="margin-left: 4px;">{{ t('scheduleView.makeupDeclined') }}</el-tag>
                  </div>
                </div>
                <el-divider v-if="hasMakeupInfo(row)" />
                <div v-if="hasMakeupInfo(row)">
                  <div style="font-weight: bold; margin-bottom: 8px;">{{ t('scheduleView.makeupInfo') }}</div>
                  <div v-for="student in row.scheduled_students.filter(s => s.makeup_status === 'completed' || s.makeup_status === 'declined')" :key="student.id" style="margin-bottom: 4px;">
                    <strong>{{ student.name }}:</strong>
                    <span v-if="student.makeup_status === 'completed'">{{ t('scheduleView.makeupCompleted') }} ({{ t('scheduleView.makeupScheduleId') }}: {{ student.makeup_schedule_id }})</span>
                    <span v-else-if="student.makeup_status === 'declined'">{{ t('scheduleView.makeupDeclined') }} ({{ t('scheduleView.declinedReason') }}: {{ student.declined_reason }})</span>
                  </div>
                </div>
              </div>
              <div v-else-if="row.execution_status === 'postponed'">
                <div v-if="row.postpone_reason">
                  <strong>{{ t('scheduleView.postponeReason') }}</strong> {{ row.postpone_reason }}
                </div>
                <div v-else>{{ t('scheduleView.noPostponeReason') }}</div>
              </div>
              <div v-else-if="row.execution_status === 'cancelled'">
                <div v-if="row.cancel_reason">
                  <strong>{{ t('scheduleView.cancelReason') }}</strong> {{ row.cancel_reason }}
                </div>
                <div v-else>{{ t('scheduleView.noCancelReason') }}</div>
              </div>
              <div v-else>
                <strong>{{ t('scheduleView.statusLabel') }}</strong> {{ t('scheduleView.pending') }}
              </div>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column :label="t('scheduleView.notifyNow')" width="110" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click="handleNotifyNow(row)">{{ t('scheduleView.notifyNow') }}</el-button>
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
    <el-dialog v-model="classStudentsDialogVisible" :title="t('scheduleView.classStudentList')" width="600px">
      <el-table :data="classStudents" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" :label="t('scheduleView.studentCode')" width="120" />
        <el-table-column prop="name" :label="t('scheduleView.studentName')" width="120" />
        <el-table-column prop="school" :label="t('scheduleView.school')" min-width="150" />
        <el-table-column prop="grade" :label="t('scheduleView.grade')" width="100" />
        <el-table-column :label="t('scheduleView.conflictStatus')" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? t('scheduleView.studentActive') : t('scheduleView.studentInactive') }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="classStudentsDialogVisible = false">{{ t('scheduleView.close') }}</el-button>
      </template>
    </el-dialog>
    <!-- 日历视图 -->
    <CalendarView v-if="viewType === 'calendar'" :date-range="dateRange" :view-type="calendarViewType" @date-range-change="handleDateRangeChange" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import CalendarView from '@/components/CalendarView.vue'
import api from '@/utils/api'
import dayjs from 'dayjs'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
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
    ElMessage.error(t('scheduleView.getClassStudentsFailed'))
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
      lines.push(`${student.name}: ${t('scheduleView.makeupCompleted')} (${t('scheduleView.makeupScheduleId')}: ${student.makeup_schedule_id})`)
    } else if (student.makeup_status === 'declined') {
      lines.push(`${student.name}: ${t('scheduleView.makeupDeclined')} (${student.declined_reason})`)
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
    ElMessage.error(t('scheduleView.getConflictFailed'))
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

const getAttendanceTagType = (status) => {
  switch (status) {
    case 'present': return 'success'
    case 'absent': return 'danger'
    case 'leave': return 'warning'
    default: return 'info'
  }
}

const getAttendanceStatusText = (status) => {
  switch (status) {
    case 'present': return t('scheduleView.present')
    case 'absent': return t('scheduleView.absent')
    case 'leave': return t('scheduleView.onLeave')
    default: return t('scheduleView.pending')
  }
}

const getRoomName = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.name : '-'
}

const getDayOfWeekFromDate = (date) => {
  const dayOfWeek = dayjs(date).day() || 7
  const pythonDayOfWeek = dayOfWeek === 0 ? 7 : dayOfWeek
  const days = [t('scheduleView.mon'), t('scheduleView.tue'), t('scheduleView.wed'), t('scheduleView.thu'), t('scheduleView.fri'), t('scheduleView.sat'), t('scheduleView.sun')]
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
  const days = [t('scheduleView.mon'), t('scheduleView.tue'), t('scheduleView.wed'), t('scheduleView.thu'), t('scheduleView.fri'), t('scheduleView.sat'), t('scheduleView.sun')]
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
      label: t('scheduleView.feedback'),
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

const handleNotifyNow = (row) => {
  ElMessageBox.confirm(t('scheduleView.notifyNowConfirm'), t('scheduleView.notifyNow'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.post(`/schedules/${row.id}/notify`)
      ElMessage.success(t('scheduleView.notifyNowSuccess'))
    } catch (error) {
      window.logger.error('立即通知失败:', error)
      ElMessage.error(t('scheduleView.notifyNowFail'))
    }
  }).catch(() => {})
}
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