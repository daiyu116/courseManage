// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="calendar-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('calendar.scheduleCalendar') }}</span>
          <div class="header-actions">
            <el-select v-model="searchType" :placeholder="t('calendar.searchType')" style="width: 100px; margin-right: 10px;" clearable @change="handleSearchTypeChange">
              <el-option :label="t('calendar.all')" value="all" />
              <el-option :label="t('calendar.teacher')" value="teacher" />
              <el-option :label="t('calendar.student')" value="student" />
            </el-select>
            <el-select
              v-if="searchType === 'teacher'"
              v-model="searchTeacherId"
              :placeholder="t('calendar.selectTeacher')"
              filterable
              clearable
              style="width: 150px; margin-right: 10px;"
              @change="handleSearchChange"
            >
              <el-option
                v-for="teacher in teachers"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
              />
            </el-select>
            <el-select
              v-if="searchType === 'student'"
              v-model="searchStudentId"
              :placeholder="t('calendar.selectStudent')"
              filterable
              clearable
              style="width: 150px; margin-right: 10px;"
              @change="handleSearchChange"
            >
              <el-option
                v-for="student in students"
                :key="student.id"
                :label="student.name"
                :value="student.id"
              />
            </el-select>
            <el-select v-model="viewType" @change="handleViewTypeChange" style="width: 120px; margin-right: 10px;">
              <el-option :label="t('calendar.teacherView')" value="teacher" />
              <el-option :label="t('calendar.classView')" value="class" />
              <el-option :label="t('calendar.roomView')" value="room" />
              <el-option :label="t('calendar.courseView')" value="course" />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              :range-separator="t('calendar.to')"
              :start-placeholder="t('calendar.startDate')"
              :end-placeholder="t('calendar.endDate')"
              value-format="YYYY-MM-DD"
              @change="handleDateRangeChange"
              style="width: 280px; margin-right: 10px;"
            />
            <el-button type="primary" @click="handlePrevWeek">{{ t('calendar.prevPeriod') }}</el-button>
            <el-button type="primary" @click="handleNextWeek">{{ t('calendar.nextPeriod') }}</el-button>
            <el-button type="primary" @click="handleToday">{{ t('calendar.today') }}</el-button>
          </div>
        </div>
      </template>

      <div class="calendar-container">
        <div class="time-column">
          <div class="time-header">{{ t('calendar.time') }}</div>
          <div v-for="time in timeSlots" :key="time" class="time-cell">
            {{ time }}
          </div>
        </div>

        <div class="dates-column">
          <div class="date-header-row">
            <div v-for="date in displayDates" :key="date.dateStr" class="date-header">
              <div class="date-name">{{ date.dayName }}</div>
              <div class="date-num" :class="{ 'is-today': date.isToday }">{{ date.dateNum }}</div>
              <div v-if="date.lunarDate" class="date-lunar">{{ date.lunarDate }}</div>
            </div>
          </div>

          <div v-for="time in timeSlots" :key="time" class="time-row">
            <div v-for="date in displayDates" :key="`${date.dateStr}-${time}`"
              class="schedule-cell"
              :class="{ 'empty-slot-clickable': currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin') && getSchedulesForSlot(date, time).length === 0 }"
              @click="getSchedulesForSlot(date, time).length === 0 && handleEmptySlotClick(date, time)"
            >
              <div
                v-for="schedule in getSchedulesForSlot(date, time)"
                :key="schedule.id"
                class="schedule-item"
                :class="{
                  'has-conflict': schedule.has_conflict,
                  'is-multi-row': schedule.isMultiRow
                }"
                :style="getScheduleStyle(schedule)"
                @click="showScheduleDetail(schedule)"
              >
                <div class="schedule-title">{{ getScheduleTitle(schedule) }}</div>
                <div class="schedule-time">{{ schedule.start_time }}-{{ schedule.end_time }}</div>
                <div v-if="schedule.content_feedback" class="schedule-feedback">
                  <el-icon><ChatDotRound /></el-icon>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="addDialogVisible" :title="t('calendar.addSchedule')" width="600px" draggable destroy-on-close>
      <el-form :model="addForm" :rules="addFormRules" ref="addFormRef" label-width="100px">
        <el-form-item :label="t('calendar.course')" prop="course_id">
          <el-select v-model="addForm.course_id" filterable :placeholder="t('calendar.selectCourse')" style="width: 100%">
            <el-option v-for="course in courses" :key="course.id" :label="course.name" :value="course.id">
              <el-tooltip placement="right" :show-after="200" v-if="getCourseTeachers(course.id).length > 0">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('calendar.course') }}：</strong>{{ course.name }}</div>
                    <div v-if="course.code"><strong>{{ t('calendar.code') }}：</strong>{{ course.code }}</div>
                    <div>
                      <div style="font-weight: bold; margin-top: 8px; margin-bottom: 4px;">{{ t('calendar.courseTeachers') }}</div>
                      <div v-for="teacher in getCourseTeachers(course.id)" :key="teacher.id" style="margin-left: 10px; margin-bottom: 4px;">
                        {{ teacher.name }}
                        <div v-if="teacher.contact_phone" style="font-size: 12px; color: #909399;">
                          📱 {{ teacher.contact_phone }}
                        </div>
                        <div v-if="teacher.email" style="font-size: 12px; color: #909399;">
                          📧 {{ teacher.email }}
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
                <span>{{ course.name }}</span>
              </el-tooltip>
              <span v-else>{{ course.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.courseType')" prop="schedule_type">
          <el-radio-group v-model="addForm.schedule_type">
            <el-radio value="formal">{{ t('calendar.formalClass') }}</el-radio>
            <el-radio value="trial">{{ t('calendar.trialClass') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('calendar.teacher')" prop="teacher_id">
          <el-select v-model="addForm.teacher_id" filterable :placeholder="t('calendar.selectTeacher')" style="width: 100%">
            <el-option v-for="teacher in teachers" :key="teacher.id" :label="teacher.name" :value="teacher.id">
              <el-tooltip placement="right" :show-after="200" v-if="teacher.contact_phone || teacher.email">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('calendar.teacher') }}：</strong>{{ teacher.name }}</div>
                    <div v-if="teacher.code"><strong>{{ t('calendar.code') }}：</strong>{{ teacher.code }}</div>
                    <div v-if="teacher.department"><strong>{{ t('calendar.department') }}：</strong>{{ teacher.department }}</div>
                    <div v-if="teacher.contact_phone">
                      <div style="margin-top: 8px;"><strong>{{ t('calendar.contactPhone') }}：</strong></div>
                      <div>{{ teacher.contact_phone }}</div>
                    </div>
                    <div v-if="teacher.email">
                      <div style="margin-top: 8px;"><strong>{{ t('calendar.email') }}：</strong></div>
                      <div>{{ teacher.email }}</div>
                    </div>
                  </div>
                </template>
                <span>{{ teacher.name }}</span>
              </el-tooltip>
              <span v-else>{{ teacher.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.class')" prop="class_id">
          <el-select v-model="addForm.class_id" filterable :placeholder="t('calendar.selectClass')" style="width: 100%">
            <el-option v-for="cls in classes" :key="cls.id" :label="cls.name" :value="cls.id">
              <el-tooltip placement="right" :show-after="200" v-if="getActiveClassStudents(cls.id).length > 0 || getInactiveClassStudents(cls.id).length > 0">
                <template #content>
                  <div v-if="getActiveClassStudents(cls.id).length > 0">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('calendar.activeStudents') }}：</div>
                    <div v-for="student in getActiveClassStudents(cls.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ student.name }}
                    </div>
                  </div>
                  <div v-if="getInactiveClassStudents(cls.id).length > 0">
                    <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('calendar.inactiveStudents') }}：</div>
                    <div v-for="student in getInactiveClassStudents(cls.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ student.name }}
                    </div>
                  </div>
                  <div v-if="getActiveClassStudents(cls.id).length === 0 && getInactiveClassStudents(cls.id).length === 0">
                    {{ t('calendar.noStudent') }}
                  </div>
                </template>
                <span>{{ cls.name }}</span>
              </el-tooltip>
              <span v-else>{{ cls.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.roomType')" prop="room_type">
          <el-select v-model="addForm.room_type" :placeholder="t('calendar.selectRoomType')" style="width: 100%" @change="handleAddRoomTypeChange">
            <el-option :label="t('calendar.offlinePhysical')" value="offline_physical" />
            <el-option :label="t('calendar.onlineVirtual')" value="online_virtual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="addForm.room_type === 'offline_physical'" :label="t('calendar.room')" prop="room_id">
          <el-select v-model="addForm.room_id" filterable :placeholder="t('calendar.selectRoom')" style="width: 100%">
            <el-option v-for="room in rooms" :key="room.id" :label="room.name" :value="room.id">
              <el-tooltip placement="right" :show-after="200" v-if="room.location || room.capacity || room.facilities">
                <template #content>
                  <div v-if="room.location">
                    <div style="font-weight: bold;">{{ t('calendar.location') }}:</div>
                    <div>{{ room.location }}</div>
                  </div>
                  <div v-if="room.capacity">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('calendar.capacity') }}:</div>
                    <div>{{ room.capacity }}{{ t('calendar.peopleUnit') }}</div>
                  </div>
                  <div v-if="room.facilities">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('calendar.facilities') }}:</div>
                    <div>{{ room.facilities }}</div>
                  </div>
                  <div v-if="!room.location && !room.capacity && !room.facilities">
                    {{ t('calendar.noDetailInfo') }}
                  </div>
                </template>
                <span>{{ room.name }}</span>
              </el-tooltip>
              <span v-else>{{ room.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item v-else :label="t('calendar.meetingLink')" prop="meeting_link">
          <el-input v-model="addForm.meeting_link" :placeholder="t('calendar.inputMeetingLink')" />
        </el-form-item>
        <el-form-item :label="t('calendar.startTime')" prop="start_time">
          <el-time-picker v-model="addStartTime" format="HH:mm" value-format="HH:mm" :placeholder="t('calendar.selectStartTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.endTime')" prop="end_time">
          <el-time-picker v-model="addEndTime" format="HH:mm" value-format="HH:mm" :placeholder="t('calendar.selectEndTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.startDate')" prop="start_date">
          <el-date-picker v-model="addForm.start_date" type="date" :placeholder="t('calendar.selectStartDate')" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.endDate')" prop="end_date">
          <el-date-picker v-model="addForm.end_date" type="date" :placeholder="t('calendar.selectEndDate')" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button @click="handleAddSubmit(false)">{{ t('calendar.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="handleAddSubmit(true)">{{ t('calendar.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" :title="t('calendar.scheduleDetailId', { id: currentSchedule?.id || '' })" width="600px" :style="{ marginTop: '5vh', marginLeft: '5vw' }" draggable>       
      <el-descriptions :column="2" border v-if="currentSchedule">
        <el-descriptions-item :label="t('calendar.date')">
          {{ formatDate(currentSchedule.start_date) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.time')">
          {{ currentSchedule.start_time }}-{{ currentSchedule.end_time }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.course')">
          {{ getCourseName(currentSchedule.course_id) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.teacher')">
          {{ getTeacherName(currentSchedule.teacher_id) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.class')">
            {{ getClassName(currentSchedule.class_id) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.room')">
          {{ getRoomName(currentSchedule.room_id) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.courseType')">
          <el-tag :type="currentSchedule.schedule_type === 'trial' ? 'warning' : 'success'" size="small">
            {{ currentSchedule.schedule_type === 'trial' ? t('calendar.trialClass') : t('calendar.formalClass') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.student')" :span="2">
          <div v-if="currentSchedule && currentSchedule.class_id">
            <div v-if="currentSchedule.scheduled_students && currentSchedule.scheduled_students.length > 0">
              <div style="margin-bottom: 10px; font-weight: bold;">{{ t('calendar.courseStudents') }}</div>
              <el-table :data="currentSchedule.scheduled_students" border size="small" max-height="300">
                <el-table-column prop="name" :label="t('calendar.name')" width="120">
                  <template #default="{ row }">
                    <el-tooltip placement="right" effect="light" popper-class="student-info-tooltip">
                      <template #content>
                        <div class="student-detail-info">
                          <div class="info-item"><strong>{{ t('calendar.studentCode') }}</strong>{{ getStudentCode(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.studentName') }}</strong>{{ row.name }}</div>
                          <div class="info-item"><strong>{{ t('calendar.school') }}</strong>{{ getStudentSchool(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.grade') }}</strong>{{ getStudentGrade(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.joinDate') }}</strong>{{ getStudentJoinDate(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.contact') }}</strong>{{ getStudentContact(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.contactPhone') }}</strong>{{ getStudentPhone(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.email') }}</strong>{{ getStudentEmail(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.belongClass') }}</strong>{{ getStudentClasses(row.id) }}</div>
                          <div class="info-item"><strong>{{ t('calendar.isActive') }}</strong>{{ getStudentIsActive(row.id) ? t('calendar.yes') : t('calendar.no') }}</div>
                        </div>
                      </template>
                      <span style="cursor: pointer; color: #409eff;">{{ row.name }}</span>
                    </el-tooltip>
                  </template>
                </el-table-column>
                <el-table-column :label="t('calendar.attendanceStatus')" width="100">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.attendance_status === 'present' ? 'success' : row.attendance_status === 'leave' ? 'warning' : 'danger'"
                      size="small"
                    >
                      {{ row.attendance_status === 'present' ? t('calendar.present') : row.attendance_status === 'leave' ? t('calendar.onLeave') : t('calendar.absent') }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div v-else>
              <div v-if="getActiveClassStudents(currentSchedule.class_id) && getActiveClassStudents(currentSchedule.class_id).length > 0">
                <div style="margin-bottom: 10px; color: #67c23a; font-weight: bold;">{{ t('calendar.activeStudents') }}</div>
                <div style="margin-bottom: 5px;">
                  {{ getActiveClassStudents(currentSchedule.class_id).map(s => s.name).join('、') }}
                </div>
              </div>
              <div v-else>
                <div style="margin-bottom: 10px; color: #67c23a; font-weight: bold;">{{ t('calendar.activeStudentsNone') }}</div>
              </div>
              <div v-if="getInactiveClassStudents(currentSchedule.class_id) && getInactiveClassStudents(currentSchedule.class_id).length > 0">
                <div style="margin-bottom: 10px; color: #909399; font-weight: bold;">{{ t('calendar.inactiveStudents') }}</div>
                <div style="margin-bottom: 5px;">
                  {{ getInactiveClassStudents(currentSchedule.class_id).map(s => s.name).join('、') }}
                </div>
              </div>
              <el-button type="primary" size="small" @click="showClassStudents(currentSchedule.class_id)">
                <el-icon><User /></el-icon>
                {{ t('calendar.classStudentList') }}
              </el-button>
            </div>
          </div>
          <span v-else style="color: #909399;">{{ t('calendar.noStudent') }}</span>
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.conflictStatus')">
          <el-button type="danger" size="small" @click="showConflictDetails" v-if="currentSchedule.has_conflict">
            {{ t('calendar.conflict') }}
          </el-button>
          <el-button type="success" size="small" @click="showConflictDetails" v-else>
            {{ t('calendar.noConflict') }}
          </el-button>
        </el-descriptions-item>
        <el-descriptions-item :label="t('calendar.executionStatus')">
          <el-button type="success" size="small" @click="showExecutionStatusDetails('completed')" v-if="currentSchedule.execution_status === 'completed'">
            {{ t('calendar.completed') }}
          </el-button>
          <el-button type="warning" size="small" @click="showExecutionStatusDetails('postponed')" v-else-if="currentSchedule.execution_status === 'postponed'">
            {{ t('calendar.postponed') }}
          </el-button>
          <el-button type="info" size="small" @click="showExecutionStatusDetails('cancelled')" v-else-if="currentSchedule.execution_status === 'cancelled'">
            {{ t('calendar.cancelled') }}
          </el-button>
          <el-button type="" size="small" @click="showExecutionStatusDetails('pending')" v-else>
            {{ t('calendar.pending') }}
          </el-button>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div style="display: flex; gap: 10px; justify-content: space-between;">
          <div>
            <el-button v-if="canEditCompletedSchedule" @click="showEditDialog">{{ t('calendar.edit') }}</el-button>
            <el-button v-if="currentSchedule && currentSchedule.execution_status === 'completed' && currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="primary" @click="showCopyDialog">{{ t('calendar.copy') }}</el-button>
            <el-button v-if="currentSchedule && currentSchedule.execution_status === 'completed' && currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="success" @click="showHomeworkDialog">{{ t('calendar.sendHomework') }}</el-button>
            <el-button v-if="currentSchedule && currentSchedule.execution_status === 'completed'" type="primary" @click="emit('word-check', currentSchedule)">{{ t('calendar.wordCheck') }}</el-button>
            <el-button v-if="currentSchedule && currentSchedule.execution_status === 'completed' && currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin') && hasStudentsNeedingMakeup(currentSchedule)" type="warning" @click="showMakeupDialog">{{ t('calendar.studentMakeup') }}</el-button>
            <el-button v-if="currentSchedule && currentSchedule.execution_status === 'pending' && currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" @click="showEditDialog">{{ t('calendar.edit') }}</el-button>
            <el-button v-if="currentSchedule && currentSchedule.execution_status === 'pending' && currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="primary" @click="showCopyDialog">{{ t('calendar.copy') }}</el-button>
            <el-button v-if="currentSchedule && currentSchedule.execution_status === 'pending' && currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="info" @click="showExtraStudentDialog">{{ t('calendar.extraStudent') }}</el-button>
            <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="warning" @click="handleNotifyNow">{{ t('calendar.notifyNow') }}</el-button>
          </div>
          <div>
            <el-button v-if="canEditCompletedSchedule" type="danger" @click="handleDeleteSchedule">{{ t('calendar.delete') }}</el-button>
            <el-button @click="detailDialogVisible = false">{{ t('calendar.close') }}</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
    <!-- 冲突详情弹窗 -->
    <el-dialog v-model="conflictDialogVisible" :title="t('calendar.conflictList')" width="800px" draggable>
      <el-table :data="conflictSchedules" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column :label="t('calendar.course')" width="120">
          <template #default="{ row }">
            {{ getCourseName(row.course_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('calendar.teacher')" width="120">
          <template #default="{ row }">
            {{ getTeacherName(row.teacher_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('calendar.class')" width="120">
          <template #default="{ row }">
            {{ getClassName(row.class_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('calendar.room')" width="120">
          <template #default="{ row }">
            {{ getRoomName(row.room_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('calendar.time')" width="160">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }} {{ row.start_time }}-{{ row.end_time }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="conflictDialogVisible = false">{{ t('calendar.close') }}</el-button>
      </template>
    </el-dialog>
    <!-- 执行状态详情弹窗 -->
    <el-dialog v-model="executionStatusDialogVisible" :title="t('calendar.executionStatusDetail')" width="600px" draggable>
      <div v-if="executionStatusType === 'postponed'">
        <el-descriptions :column="1" border>
          <el-descriptions-item :label="t('calendar.postponeReason')">
            {{ currentSchedule?.postpone_reason || t('calendar.noPostponeReason') }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else-if="executionStatusType === 'cancelled'">
        <el-descriptions :column="1" border>
          <el-descriptions-item :label="t('calendar.cancelReason')">
            {{ currentSchedule?.cancel_reason || t('calendar.noCancelReason') }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else-if="executionStatusType === 'completed'">
        <el-descriptions :column="1" border>
          <el-descriptions-item :label="t('calendar.contentFeedback')">
            <div v-if="currentSchedule?.content_feedback">
              <div v-for="(line, index) in parseContentFeedback(currentSchedule.content_feedback)" :key="index" style="margin-bottom: 8px;">
                <strong>{{ line.label }}:</strong> {{ line.content }}
              </div>
            </div>
            <div v-else>{{ t('calendar.noFeedback') }}</div>
          </el-descriptions-item>
          <el-descriptions-item :label="t('calendar.makeupInfo')" v-if="hasMakeupInfo(currentSchedule)">
            <div v-for="student in currentSchedule.scheduled_students.filter(s => s.makeup_status === 'completed' || s.makeup_status === 'declined')" :key="student.id" style="margin-bottom: 4px;">
              <strong>{{ student.name }}:</strong>
              <span v-if="student.makeup_status === 'completed'">{{ t('calendar.makeupCompleted') }} (ID: {{ student.makeup_schedule_id }})</span>
              <span v-else-if="student.makeup_status === 'declined'">{{ t('calendar.makeupDeclined') }} ({{ t('calendar.reason') }}: {{ student.declined_reason }})</span>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else-if="executionStatusType === 'pending'">
        <el-descriptions :column="1" border>
          <el-descriptions-item :label="t('calendar.statusLabel')">
            {{ t('calendar.pending') }}
          </el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 20px; text-align: center;">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="success" @click="handleCompleteSchedule">{{ t('calendar.completeTraining') }}</el-button>
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="warning" @click="handlePostponeSchedule">{{ t('calendar.postpone') }}</el-button>
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="info" @click="handleCancelSchedule">{{ t('calendar.cancelSchedule') }}</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="executionStatusDialogVisible = false">{{ t('calendar.close') }}</el-button>
      </template>
    </el-dialog>
    <!-- 班级学员弹窗 -->
    <el-dialog v-model="classStudentsDialogVisible" :title="t('calendar.classStudentList')" width="600px" :style="{ marginTop: '10vh', marginLeft: '10vw' }" draggable>
      <el-table :data="classStudents" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" :label="t('calendar.studentCode')" width="120" />
        <el-table-column prop="name" :label="t('calendar.studentName')" width="120" />
        <el-table-column prop="school" :label="t('calendar.school')" min-width="150" />
        <el-table-column prop="grade" :label="t('calendar.grade')" width="100" />
        <el-table-column :label="t('calendar.contact')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.contact_person" type="success">{{ row.contact_person }}</el-tag>
            <el-tag v-else type="info">{{ t('calendar.noContact') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('calendar.contactInfo')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.phone" type="success">{{ row.phone }}</el-tag>
            <el-tag v-else type="info">{{ t('calendar.noContactInfo') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('calendar.activeStatus')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? t('calendar.active') : t('calendar.inactive') }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="classStudentsDialogVisible = false">{{ t('calendar.close') }}</el-button>
      </template>
    </el-dialog>
    <!-- 完训对话框 -->
    <el-dialog v-model="completeDialogVisible" :title="t('calendar.fillFeedback')" width="800px" draggable>
      <el-form :model="completeForm" :rules="completeRules" ref="completeFormRef" label-width="80px">
        <el-form-item :label="t('calendar.content')" prop="content">
          <el-input v-model="completeForm.content" type="textarea" :rows="3" :placeholder="t('calendar.inputContent')" />
        </el-form-item>
        <el-form-item :label="t('calendar.homework')" prop="homework">
          <el-input v-model="completeForm.homework" type="textarea" :rows="3" :placeholder="t('calendar.inputHomework')" />
        </el-form-item>
        <el-form-item :label="t('calendar.note')" prop="note">
          <el-input v-model="completeForm.note" type="textarea" :rows="3" :placeholder="t('calendar.inputNote')" />
        </el-form-item>
        
        <el-divider>{{ t('calendar.studentAttendanceStatus') }}</el-divider>
        <el-table :data="completeForm.studentAttendance" border max-height="300">
          <el-table-column prop="name" :label="t('calendar.studentName')" width="150" />
          <el-table-column :label="t('calendar.attendanceStatus')" width="200">
            <template #default="{ row }">
              <el-radio-group v-model="row.status" :disabled="row.isLocked">
                <el-radio value="present">{{ t('calendar.present') }}</el-radio>
                <el-radio value="absent">{{ t('calendar.absent') }}</el-radio>
                <el-radio value="leave">{{ t('calendar.onLeave') }}</el-radio>
              </el-radio-group>
              <el-tag v-if="row.isLocked" type="info" size="small" style="margin-left: 8px;">{{ t('calendar.locked') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('calendar.absenceReason')">
            <template #default="{ row }">
              <el-input 
                v-if="row.status !== 'present'" 
                v-model="row.absenceReason" 
                :disabled="row.isLocked"
                :placeholder="t('calendar.inputAbsenceReason')"
                size="small"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="completeDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button @click="executeComplete(false)">{{ t('calendar.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="executeComplete(true)">{{ t('calendar.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 延期对话框 -->
    <el-dialog v-model="postponeDialogVisible" :title="t('calendar.adjustDateTime')" width="600px" draggable>
      <el-form :model="postponeForm" :rules="postponeRules" ref="postponeFormRef" label-width="100px">
        <el-form-item :label="t('calendar.startDate')" prop="startDate">
          <el-date-picker
            v-model="postponeForm.startDate"
            type="date"
            :placeholder="t('calendar.selectStartDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('calendar.endDate')" prop="endDate">
          <el-date-picker
            v-model="postponeForm.endDate"
            type="date"
            :placeholder="t('calendar.selectEndDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('calendar.startTime')" prop="startTime">
          <el-time-picker
            v-model="postponeForm.startTime"
            :placeholder="t('calendar.selectStartTime')"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('calendar.endTime')" prop="endTime">
          <el-time-picker
            v-model="postponeForm.endTime"
            :placeholder="t('calendar.selectEndTime')"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('calendar.postponeReason')" prop="postponeReason">
          <el-input v-model="postponeForm.postponeReason" type="textarea" :rows="3" :placeholder="t('calendar.inputPostponeReason')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="postponeDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button @click="executePostpone(false)">{{ t('calendar.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="executePostpone(true)">{{ t('calendar.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 取消排课对话框 -->
    <el-dialog v-model="cancelDialogVisible" :title="t('calendar.cancelSchedule')" width="600px" draggable>
      <el-form :model="cancelForm" :rules="cancelRules" ref="cancelFormRef" label-width="100px">
        <el-form-item :label="t('calendar.cancelReason')" prop="cancelReason">
          <el-input v-model="cancelForm.cancelReason" type="textarea" :rows="3" :placeholder="t('calendar.inputCancelReason')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button @click="executeCancel(false)">{{ t('calendar.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="executeCancel(true)">{{ t('calendar.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" :title="t('calendar.editSchedule')" width="600px" draggable>
      <el-form :model="editForm" label-width="100px">
        <el-form-item :label="t('calendar.course')">
          <el-select v-model="editForm.course_id" :placeholder="t('calendar.selectCourse')" style="width: 100%">
            <el-option v-for="course in courses" :key="course.id" :label="course.name" :value="course.id">
              <el-tooltip placement="right" effect="light" v-if="getCourseTeachers(course.id).length > 0">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('calendar.course') }}：</strong>{{ course.name }}</div>
                    <div v-if="course.code"><strong>{{ t('calendar.code') }}：</strong>{{ course.code }}</div>
                    <div v-if="getCourseTeachers(course.id).length > 0">
                      <div style="font-weight: bold; margin-top: 8px; margin-bottom: 4px;">{{ t('calendar.courseTeachers') }}</div>
                      <div v-for="teacher in getCourseTeachers(course.id)" :key="teacher.id" style="margin-left: 10px; margin-bottom: 4px;">
                        {{ teacher.name }}
                        <div v-if="teacher.contact_phone" style="font-size: 12px; color: #909399;">
                          📱 {{ teacher.contact_phone }}
                        </div>
                        <div v-if="teacher.email" style="font-size: 12px; color: #909399;">
                          📧 {{ teacher.email }}
                        </div>
                      </div>
                    </div>
                    <div v-else style="margin-top: 8px; color: #909399;">{{ t('calendar.noCourseTeacher') }}</div>
                  </div>
                </template>
                <span>{{ course.name }}</span>
              </el-tooltip>
              <span v-else>{{ course.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.courseType')">
          <el-radio-group v-model="editForm.schedule_type">
            <el-radio value="formal">{{ t('calendar.formalClass') }}</el-radio>
            <el-radio value="trial">{{ t('calendar.trialClass') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('calendar.teacher')">
          <el-select v-model="editForm.teacher_id" :placeholder="t('calendar.selectTeacher')" style="width: 100%">
            <el-option v-for="teacher in teachers" :key="teacher.id" :label="teacher.name" :value="teacher.id">
              <el-tooltip placement="right" effect="light" v-if="teacher.contact_phone || teacher.email">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('calendar.teacher') }}：</strong>{{ teacher.name }}</div>
                    <div v-if="teacher.code"><strong>{{ t('calendar.code') }}：</strong>{{ teacher.code }}</div>
                    <div v-if="teacher.department"><strong>{{ t('calendar.department') }}：</strong>{{ teacher.department }}</div>
                    <div v-if="teacher.contact_phone">
                      <div style="margin-top: 8px;"><strong>{{ t('calendar.contactPhone') }}：</strong></div>
                      <div>{{ teacher.contact_phone }}</div>
                    </div>
                    <div v-if="teacher.email">
                      <div style="margin-top: 8px;"><strong>{{ t('calendar.emailLabel') }}：</strong></div>
                      <div>{{ teacher.email }}</div>
                    </div>
                    <div v-if="!teacher.contact_phone && !teacher.email" style="margin-top: 8px; color: #909399;">
                      {{ t('calendar.noContactInfo') }}
                    </div>
                  </div>
                </template>
                <span>{{ teacher.name }}</span>
              </el-tooltip>
              <span v-else>{{ teacher.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.class')">
          <el-select v-model="editForm.class_id" :placeholder="t('calendar.selectClass')" style="width: 100%">
            <el-option v-for="class_ in classes" :key="class_.id" :label="class_.name" :value="class_.id">
              <el-tooltip placement="right" effect="light" v-if="getActiveClassStudents(class_.id).length > 0 || getInactiveClassStudents(class_.id).length > 0">
                <template #content>
                  <div v-if="getActiveClassStudents(class_.id).length > 0">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('calendar.activeStudents') }}:</div>
                    <div v-for="student in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ student.name }}
                    </div>
                  </div>
                  <div v-if="getInactiveClassStudents(class_.id).length > 0">
                    <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('calendar.inactiveStudents') }}:</div>
                    <div v-for="student in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ student.name }}
                    </div>
                  </div>
                  <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                    {{ t('calendar.noStudent') }}
                  </div>
                </template>
                <span>{{ class_.name }}</span>
              </el-tooltip>
              <span v-else>{{ class_.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.roomType')">
          <el-select v-model="editForm.room_type" :placeholder="t('calendar.selectRoomType')" style="width: 100%" @change="handleEditRoomTypeChange">
            <el-option :label="t('calendar.offlinePhysical')" value="offline_physical" />
            <el-option :label="t('calendar.onlineVirtual')" value="online_virtual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editForm.room_type === 'offline_physical'" :label="t('calendar.room')">
          <el-select v-model="editForm.room_id" :placeholder="t('calendar.selectRoom')" style="width: 100%">
            <el-option v-for="room in rooms" :key="room.id" :label="room.name" :value="room.id">
              <el-tooltip placement="right" effect="light" v-if="room.location || room.capacity || room.facilities">
                <template #content>
                  <div v-if="room.location">
                    <div style="font-weight: bold;">{{ t('calendar.location') }}:</div>
                    <div>{{ room.location }}</div>
                  </div>
                  <div v-if="room.capacity">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('calendar.capacity') }}:</div>
                    <div>{{ room.capacity }}{{ t('calendar.peopleUnit') }}</div>
                  </div>
                  <div v-if="room.facilities">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('calendar.facilities') }}:</div>
                    <div>{{ room.facilities }}</div>
                  </div>
                  <div v-if="!room.location && !room.capacity && !room.facilities">
                    {{ t('calendar.noDetailInfo') }}
                  </div>
                </template>
                <span>{{ room.name }}</span>
              </el-tooltip>
              <span v-else>{{ room.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item v-else :label="t('calendar.meetingLink')">
          <el-input v-model="editForm.meeting_link" :placeholder="t('calendar.inputMeetingLinkDesc')" />
        </el-form-item>
        <el-form-item :label="t('calendar.startTime')">
          <el-time-picker v-model="editStartTime" format="HH:mm" value-format="HH:mm" :placeholder="t('calendar.selectStartTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.endTime')">
          <el-time-picker v-model="editEndTime" format="HH:mm" value-format="HH:mm" :placeholder="t('calendar.selectEndTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.startDate')">
          <el-date-picker v-model="editForm.start_date" type="date" :placeholder="t('calendar.selectStartDate')" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.endDate')">
          <el-date-picker v-model="editForm.end_date" type="date" :placeholder="t('calendar.selectEndDate')" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button @click="executeEdit(false)">{{ t('calendar.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="executeEdit(true)">{{ t('calendar.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 复制对话框 -->
    <el-dialog v-model="copyDialogVisible" :title="t('calendar.copySchedule')" width="600px" draggable>
      <el-form :model="copyForm" label-width="100px">
        <el-form-item :label="t('calendar.course')">
          <el-select v-model="copyForm.course_id" :placeholder="t('calendar.selectCourse')" style="width: 100%">
            <el-option v-for="course in courses" :key="course.id" :label="course.name" :value="course.id">
              <el-tooltip placement="right" effect="light" v-if="getCourseTeachers(course.id).length > 0">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('calendar.course') }}：</strong>{{ course.name }}</div>
                    <div v-if="course.code"><strong>{{ t('calendar.code') }}：</strong>{{ course.code }}</div>
                    <div v-if="getCourseTeachers(course.id).length > 0">
                      <div style="font-weight: bold; margin-top: 8px; margin-bottom: 4px;">{{ t('calendar.courseTeachers') }}</div>
                      <div v-for="teacher in getCourseTeachers(course.id)" :key="teacher.id" style="margin-left: 10px; margin-bottom: 4px;">
                        {{ teacher.name }}
                        <div v-if="teacher.contact_phone" style="font-size: 12px; color: #909399;">
                          📱 {{ teacher.contact_phone }}
                        </div>
                        <div v-if="teacher.email" style="font-size: 12px; color: #909399;">
                          📧 {{ teacher.email }}
                        </div>
                      </div>
                    </div>
                    <div v-else style="margin-top: 8px; color: #909399;">{{ t('calendar.noCourseTeacher') }}</div>
                  </div>
                </template>
                <span>{{ course.name }}</span>
              </el-tooltip>
              <span v-else>{{ course.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.courseType')">
          <el-radio-group v-model="copyForm.schedule_type">
            <el-radio value="formal">{{ t('calendar.formalClass') }}</el-radio>
            <el-radio value="trial">{{ t('calendar.trialClass') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('calendar.teacher')">
          <el-select v-model="copyForm.teacher_id" :placeholder="t('calendar.selectTeacher')" style="width: 100%">
            <el-option v-for="teacher in teachers" :key="teacher.id" :label="teacher.name" :value="teacher.id">
              <el-tooltip placement="right" effect="light" v-if="teacher.contact_phone || teacher.email">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('calendar.teacher') }}：</strong>{{ teacher.name }}</div>
                    <div v-if="teacher.code"><strong>{{ t('calendar.code') }}：</strong>{{ teacher.code }}</div>
                    <div v-if="teacher.department"><strong>{{ t('calendar.department') }}：</strong>{{ teacher.department }}</div>
                    <div v-if="teacher.contact_phone">
                      <div style="margin-top: 8px;"><strong>{{ t('calendar.contactPhone') }}：</strong></div>
                      <div>{{ teacher.contact_phone }}</div>
                    </div>
                    <div v-if="teacher.email">
                      <div style="margin-top: 8px;"><strong>{{ t('calendar.emailLabel') }}：</strong></div>
                      <div>{{ teacher.email }}</div>
                    </div>
                    <div v-if="!teacher.contact_phone && !teacher.email" style="margin-top: 8px; color: #909399;">
                      {{ t('calendar.noContactInfo') }}
                    </div>
                  </div>
                </template>
                <span>{{ teacher.name }}</span>
              </el-tooltip>
              <span v-else>{{ teacher.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.class')">
          <el-select v-model="copyForm.class_id" :placeholder="t('calendar.selectClass')" style="width: 100%">
            <el-option v-for="class_ in classes" :key="class_.id" :label="class_.name" :value="class_.id">
              <el-tooltip placement="right" effect="light" v-if="getActiveClassStudents(class_.id).length > 0 || getInactiveClassStudents(class_.id).length > 0">
                <template #content>
                  <div v-if="getActiveClassStudents(class_.id).length > 0">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('calendar.activeStudents') }}:</div>
                    <div v-for="student in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ student.name }}
                    </div>
                  </div>
                  <div v-if="getInactiveClassStudents(class_.id).length > 0">
                    <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('calendar.inactiveStudents') }}:</div>
                    <div v-for="student in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ student.name }}
                    </div>
                  </div>
                  <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                    {{ t('calendar.noStudent') }}
                  </div>
                </template>
                <span>{{ class_.name }}</span>
              </el-tooltip>
              <span v-else>{{ class_.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('calendar.roomType')">
          <el-select v-model="copyForm.room_type" :placeholder="t('calendar.selectRoomType')" style="width: 100%" @change="handleCopyRoomTypeChange">
            <el-option :label="t('calendar.offlinePhysical')" value="offline_physical" />
            <el-option :label="t('calendar.onlineVirtual')" value="online_virtual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="copyForm.room_type === 'offline_physical'" :label="t('calendar.room')">
          <el-select v-model="copyForm.room_id" :placeholder="t('calendar.selectRoom')" style="width: 100%">
            <el-option v-for="room in rooms" :key="room.id" :label="room.name" :value="room.id">
              <el-tooltip placement="right" effect="light" v-if="room.location || room.capacity || room.facilities">
                <template #content>
                  <div v-if="room.location">
                    <div style="font-weight: bold;">{{ t('calendar.location') }}:</div>
                    <div>{{ room.location }}</div>
                  </div>
                  <div v-if="room.capacity">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('calendar.capacity') }}:</div>
                    <div>{{ room.capacity }}{{ t('calendar.peopleUnit') }}</div>
                  </div>
                  <div v-if="room.facilities">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('calendar.facilities') }}:</div>
                    <div>{{ room.facilities }}</div>
                  </div>
                  <div v-if="!room.location && !room.capacity && !room.facilities">
                    {{ t('calendar.noDetailInfo') }}
                  </div>
                </template>
                <span>{{ room.name }}</span>
              </el-tooltip>
              <span v-else>{{ room.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item v-else :label="t('calendar.meetingLink')">
          <el-input v-model="copyForm.meeting_link" :placeholder="t('calendar.inputMeetingLinkDesc')" />
        </el-form-item>
        <el-form-item :label="t('calendar.startTime')">
          <el-time-picker v-model="copyStartTime" format="HH:mm" value-format="HH:mm" :placeholder="t('calendar.selectStartTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.endTime')">
          <el-time-picker v-model="copyEndTime" format="HH:mm" value-format="HH:mm" :placeholder="t('calendar.selectEndTime')" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.startDate')">
          <el-date-picker v-model="copyForm.start_date" type="date" :placeholder="t('calendar.selectStartDate')" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('calendar.endDate')">
          <el-date-picker v-model="copyForm.end_date" type="date" :placeholder="t('calendar.selectEndDate')" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button @click="executeCopy(false)">{{ t('calendar.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="executeCopy(true)">{{ t('calendar.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 作业安排对话框 -->
    <el-dialog v-model="homeworkDialogVisible" :title="t('calendar.sendHomework')" width="700px" draggable>
      <el-form ref="homeworkFormRef" :model="homeworkForm" :rules="homeworkRules" label-width="100px">
        <el-form-item :label="t('calendar.classHomework')" prop="classHomework">
          <el-input v-model="homeworkForm.classHomework" type="textarea" :rows="3" :placeholder="t('calendar.inputClassHomework')" />
        </el-form-item>
        <el-form-item :label="t('calendar.regularHomework')" prop="regularHomework">
          <el-input v-model="homeworkForm.regularHomework" type="textarea" :rows="4" :placeholder="t('calendar.inputRegularHomework')" />
        </el-form-item>
        <el-form-item :label="t('calendar.homeworkImages')">
          <el-upload v-model:file-list="homeworkForm.images" action="/api/upload" list-type="picture-card" :limit="3" :on-preview="handlePicturePreview" :on-success="handleUploadSuccess" :on-remove="handleRemove" accept="image/*">
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="homeworkDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button @click="executeHomework(false)">{{ t('calendar.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="executeHomework(true)">{{ t('calendar.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 补课对话框 -->
    <el-dialog v-model="makeupDialogVisible" :title="t('calendar.studentMakeup')" width="600px" draggable>
      <el-form ref="makeupFormRef" :model="makeupForm" :rules="makeupRules" label-width="100px">
        <el-form-item :label="t('calendar.makeupOption')">
          <el-radio-group v-model="makeupForm.makeupType">
            <el-radio value="makeup">{{ t('calendar.makeup') }}</el-radio>
            <el-radio value="decline">{{ t('calendar.declineMakeup') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <template v-if="makeupForm.makeupType === 'makeup'">
          <el-form-item :label="t('calendar.selectStudent')" prop="studentIds">
            <el-select v-model="makeupForm.studentIds" :placeholder="t('calendar.selectStudent')" multiple style="width: 100%">
              <el-option v-for="student in classStudents" :key="student.id" :label="`${student.name} (${student.attendance_status === 'absent' ? t('calendar.absent') : t('calendar.onLeave')})`" :value="student.id" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('calendar.startDate')" prop="startDate">
            <el-date-picker v-model="makeupForm.startDate" type="date" :placeholder="t('calendar.selectStartDate')" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item :label="t('calendar.endDate')" prop="endDate">
            <el-date-picker v-model="makeupForm.endDate" type="date" :placeholder="t('calendar.selectEndDate')" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item :label="t('calendar.startTime')" prop="startTime">
            <el-time-picker v-model="makeupForm.startTime" :placeholder="t('calendar.selectStartTime')" format="HH:mm" value-format="HH:mm" style="width: 100%" />
          </el-form-item>
          <el-form-item :label="t('calendar.endTime')" prop="endTime">
            <el-time-picker v-model="makeupForm.endTime" :placeholder="t('calendar.selectEndTime')" format="HH:mm" value-format="HH:mm" style="width: 100%" />
          </el-form-item>
          <el-form-item :label="t('calendar.room')" prop="roomId">
            <el-select v-model="makeupForm.roomId" :placeholder="t('calendar.selectRoom')" style="width: 100%">
              <el-option v-for="room in rooms" :key="room.id" :label="room.name" :value="room.id" />
            </el-select>
          </el-form-item>
        </template>
        
        <template v-if="makeupForm.makeupType === 'decline'">
          <el-form-item :label="t('calendar.selectStudent')" prop="studentIds">
            <el-select v-model="makeupForm.studentIds" :placeholder="t('calendar.selectStudent')" multiple style="width: 100%">
              <el-option v-for="student in classStudents" :key="student.id" :label="`${student.name} (${student.attendance_status === 'absent' ? t('calendar.absent') : t('calendar.onLeave')})`" :value="student.id" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('calendar.declineReason')" prop="declinedReason">
            <el-input v-model="makeupForm.declinedReason" type="textarea" :rows="4" :placeholder="t('calendar.inputDeclineReason')" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="makeupDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button type="primary" @click="executeMakeup">{{ t('calendar.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 临时增员对话框 -->
    <el-dialog v-model="extraStudentDialogVisible" :title="t('calendar.extraStudentManage')" width="650px" draggable>
      <div v-if="currentSchedule" style="margin-bottom: 15px;">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item :label="t('calendar.course')">{{ getCourseName(currentSchedule.course_id) }}</el-descriptions-item>
          <el-descriptions-item :label="t('calendar.class')">{{ getClassName(currentSchedule.class_id) }}</el-descriptions-item>
          <el-descriptions-item :label="t('calendar.date')">{{ currentSchedule.start_date }} {{ currentSchedule.start_time }}-{{ currentSchedule.end_time }}</el-descriptions-item>
          <el-descriptions-item :label="t('calendar.teacher')">{{ getTeacherName(currentSchedule.teacher_id) }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider content-position="left">{{ t('calendar.currentExtraStudents') }}</el-divider>
      <div v-if="currentExtraStudents.length > 0" style="margin-bottom: 15px;">
        <el-tag v-for="student in currentExtraStudents" :key="student.id" closable type="warning" size="large" style="margin: 3px;" @close="removeExtraStudent(student.id)">
          {{ student.name }}
        </el-tag>
      </div>
      <div v-else style="color: #909399; margin-bottom: 15px;">{{ t('calendar.noExtraStudents') }}</div>

      <el-divider content-position="left">{{ t('calendar.addExtraStudents') }}</el-divider>
      <el-form label-width="80px">
        <el-form-item :label="t('calendar.selectStudents')">
          <el-select
            v-model="selectedExtraStudentIds"
            multiple
            filterable
            :placeholder="t('calendar.selectStudentsPlaceholder')"
            style="width: 100%;"
          >
            <el-option
              v-for="student in availableExtraStudents"
              :key="student.id"
              :label="`${student.name} (${student.code || 'N/A'})`"
              :value="student.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="extraStudentDialogVisible = false">{{ t('calendar.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddExtraStudents" :loading="extraStudentLoading" :disabled="selectedExtraStudentIds.length === 0">{{ t('calendar.confirmAddExtra') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, User, Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import dayjs from 'dayjs'
import weekday from 'dayjs/plugin/weekday'
import 'dayjs/locale/zh-cn'
import { Lunar, Solar } from 'lunar-javascript'
import { useI18n } from 'vue-i18n'

dayjs.extend(weekday)
dayjs.locale('zh-cn')

const { t } = useI18n()
const currentUser = ref(null)

const props = defineProps({
  dateRange: {
    type: Array,
    default: () => []
  },
  viewType: {
    type: String,
    default: 'teacher'
  }
})

const emit = defineEmits(['date-range-change', 'word-check'])
const conflictDialogVisible = ref(false)
const conflictSchedules = ref([])
const executionStatusDialogVisible = ref(false)
const executionStatusType = ref('')
const viewType = ref(props.viewType)
const dateRange = ref([])
const searchType = ref('all')
const searchTeacherId = ref(null)
const searchStudentId = ref(null)
const schedules = ref([])
const teachers = ref([])
const classes = ref([])
const students = ref([])
const classStudents = ref([])
const classStudentsDialogVisible = ref(false)
const rooms = ref([])
const courses = ref([])
const detailDialogVisible = ref(false)
const currentSchedule = ref(null)
const timeSlots = ['08:00', '10:00', '12:00', '13:30', '14:00', '14:30', '15:30', '16:00', '16:30', '17:30', '18:00', '18:30', '19:30', '20:00', '20:30', '21:30', '22:00', '22:30']
const homeworkFormRef = ref(null)
const makeupFormRef = ref(null)
const copyLoading = ref(false)
const editLoading = ref(false)

// 完训对话框
const completeDialogVisible = ref(false)
const completeFormRef = ref(null) 
const completeForm = ref({
  content: '',
  homework: '',
  note: ''
})
// 延期对话框
const postponeDialogVisible = ref(false)
const postponeFormRef = ref(null)
const postponeForm = ref({
  startDate: '',
  endDate: '',
  startTime: '',
  endTime: '',
  postponeReason: ''
})
// 取消排课对话框
const cancelDialogVisible = ref(false)
const cancelFormRef = ref(null)
const cancelForm = ref({
  cancelReason: ''
})
// 添加验证规则
const completeRules = computed(() => {
  // 获取导师信息
  const teacher = teachers.value.find(t => t.id === currentSchedule.value?.teacher_id)
  // 如果导师开启了"无需反馈"，则不需要验证
  if (teacher && teacher.no_feedback_required) {
    return {}
  }
  return {
    content: [{ required: true, message: t('calendar.validation.inputContent'), trigger: 'blur' }],
    homework: [{ required: true, message: t('calendar.validation.inputHomework'), trigger: 'blur' }],
    note: [{ required: true, message: t('calendar.validation.inputNote'), trigger: 'blur' }]
  }
})

const postponeRules = {
  startDate: [{ required: true, message: t('calendar.validation.selectStartDate'), trigger: 'change' }],
  endDate: [{ required: true, message: t('calendar.validation.selectEndDate'), trigger: 'change' }],
  startTime: [{ required: true, message: t('calendar.validation.selectStartTime'), trigger: 'change' }],
  endTime: [{ required: true, message: t('calendar.validation.selectEndTime'), trigger: 'change' }],
  postponeReason: [{ required: true, message: t('calendar.validation.inputPostponeReason'), trigger: 'blur' }]
}

const cancelRules = {
  cancelReason: [{ required: true, message: t('calendar.validation.inputCancelReason'), trigger: 'blur' }]
}

// 判断谁可以编辑已完训状态的排课
const canEditCompletedSchedule = computed(() => {
  if (!currentSchedule.value || !currentUser.value) return false
  if (currentSchedule.value.execution_status !== 'completed' && 
      currentSchedule.value.execution_status !== 'postponed' && 
      currentSchedule.value.execution_status !== 'cancelled') return false
  
  // 超级管理员可以编辑
  if (currentUser.value.role === 'super_admin') return true
  
  // 超级导师可以编辑
  if (currentUser.value.is_subject_teacher) {
    const scheduleEditRestricted = localStorage.getItem('schedule_edit_restricted')
    if (scheduleEditRestricted === null || scheduleEditRestricted === 'true') {
      return false
    }
    return true
  }
  
  // 系统管理员和系统审计员不能编辑
  if (currentUser.value.role === 'system_admin' || currentUser.value.role === 'system_audit') return false
  
  // 普通导师（course_admin，非超级导师）不能编辑
  return false
})
const editDialogVisible = ref(false)
const editStartTime = ref('')
const editEndTime = ref('')
const editForm = ref({
  id: null,
  course_id: null,
  teacher_id: null,
  class_id: null,
  room_id: null,
  room_type: 'offline_physical',
  meeting_link: '',
  day_of_week: null,
  start_time: '',
  end_time: '',
  start_date: '',
  end_date: '',
  schedule_type: 'formal'
})

const originalEditForm = ref({
  id: null,
  course_id: null,
  teacher_id: null,
  class_id: null,
  room_id: null,
  room_type: 'offline_physical',
  meeting_link: '',
  day_of_week: null,
  start_time: '',
  end_time: '',
  start_date: '',
  end_date: '',
  schedule_type: 'formal'
})
// 复制对话框
const copyDialogVisible = ref(false)
const copyStartTime = ref('')
const copyEndTime = ref('')
const copyForm = ref({
  id: null,
  course_id: null,
  teacher_id: null,
  class_id: null,
  room_id: null,
  room_type: 'offline_physical',
  meeting_link: '',
  day_of_week: null,
  start_time: '',
  end_time: '',
  start_date: '',
  end_date: '',
  schedule_type: 'formal'
})
// 作业安排对话框
const homeworkDialogVisible = ref(false)
const homeworkForm = ref({
  classHomework: '',
  regularHomework: '',
  images: []
})
const homeworkRules = {
  classHomework: [{ required: true, message: t('calendar.validation.inputClassHomework'), trigger: 'blur' }],
  regularHomework: [{ required: true, message: t('calendar.validation.inputRegularHomework'), trigger: 'blur' }]
}
const currentHomeworkSchedule = ref(null)
// 补课对话框
const makeupDialogVisible = ref(false)
const makeupForm = ref({
  studentIds: [],
  startDate: '',
  endDate: '',
  startTime: '',
  endTime: '',
  roomId: null
})
const makeupRules = computed(() => {
  if (makeupForm.value.makeupType === 'makeup') {
    return {
      studentIds: [{ required: true, message: t('calendar.validation.selectStudent'), trigger: 'change', type: 'array', min: 1 }],
      startDate: [{ required: true, message: t('calendar.validation.selectStartDate'), trigger: 'change' }],
      endDate: [{ required: true, message: t('calendar.validation.selectEndDate'), trigger: 'change' }],
      startTime: [{ required: true, message: t('calendar.validation.selectStartTime'), trigger: 'change' }],
      endTime: [{ required: true, message: t('calendar.validation.selectEndTime'), trigger: 'change' }],
      roomId: [{ required: true, message: t('calendar.validation.selectRoom'), trigger: 'change' }]
    }
  } else {
    return {
      studentIds: [{ required: true, message: t('calendar.validation.selectStudent'), trigger: 'change', type: 'array', min: 1 }],
      declinedReason: [{ required: true, message: t('calendar.validation.inputDeclineReason'), trigger: 'blur' }]
    }
  }
})
const currentMakeupSchedule = ref(null)

// 临时增员相关
const extraStudentDialogVisible = ref(false)
const extraStudentLoading = ref(false)
const selectedExtraStudentIds = ref([])
const currentExtraStudents = ref([])
const availableExtraStudents = ref([])
// 监听props变化
watch(() => props.dateRange, (newVal) => {
  if (newVal && newVal.length === 2) {
    dateRange.value = newVal
    fetchSchedules()
  }
}, { immediate: true })

watch(() => props.viewType, (newVal) => {
  viewType.value = newVal
})

// 农历转换函数（使用 lunar-javascript 库）
const getLunarDate = (year, month, day) => {
  try {
    const solar = Solar.fromYmd(year, month, day)
    const lunar = solar.getLunar()
    
    //window.logger.log('[getLunarDate] 输入:', year, month, day)
    //window.logger.log('[getLunarDate] solar:', solar)
    //window.logger.log('[getLunarDate] lunar:', lunar)
    
    // 获取农历日期
    const lunarMonth = lunar.getMonthInChinese()
    const lunarDay = lunar.getDayInChinese()
    
    //window.logger.log('[getLunarDate] lunarMonth:', lunarMonth)
    //window.logger.log('[getLunarDate] lunarDay:', lunarDay)
    
    const lunarDateStr = `${lunarMonth}月${lunarDay}`
    
    //window.logger.log('[getLunarDate] lunarDateStr:', lunarDateStr)
    
    // 获取农历节日
    const lunarFestivals = lunar.getFestivals()
    const lunarHoliday = lunarFestivals.length > 0 ? lunarFestivals[0] : ''
    
    // 获取公历节日
    const solarFestivals = solar.getFestivals()
    const solarHoliday = solarFestivals.length > 0 ? solarFestivals[0] : ''
    
    // 获取节气
    const jieQi = lunar.getJieQi()
    
    // 确定显示的节假日信息
    let displayStr = ''
    if (lunarHoliday) {
      displayStr = lunarHoliday
    } else if (solarHoliday) {
      displayStr = solarHoliday
    } else if (jieQi) {
      displayStr = jieQi
    } else {
      displayStr = lunarDateStr
    }
    
    window.logger.log('[getLunarDate] displayStr:', displayStr)
    
    return {
      lunarDate: lunarDateStr,
      holiday: lunarHoliday,
      solarHoliday: solarHoliday,
      term: jieQi,
      displayStr: displayStr
    }
  } catch (error) {
    window.logger.error('农历转换失败:', error)
    return {
      lunarDate: '',
      holiday: '',
      solarHoliday: '',
      term: '',
      displayStr: ''
    }
  }
}

// 获取节假日信息
const getHolidayInfo = (dateStr) => {
  const year = parseInt(dateStr.substring(0, 4))
  const month = parseInt(dateStr.substring(5, 7))
  const day = parseInt(dateStr.substring(8, 10))
  
  const lunarInfo = getLunarDate(year, month, day)
  
  return {
    lunarHoliday: lunarInfo.holiday,
    solarHoliday: lunarInfo.solarHoliday,
    term: lunarInfo.term
  }
}

const displayDates = computed(() => {
  if (dateRange.value.length !== 2) return []
  
  const [startDate, endDate] = dateRange.value
  //window.logger.log('[CalendarView] displayDates: startDate=', startDate, ', endDate=', endDate)
  const dates = []
  let current = dayjs(startDate)
  const end = dayjs(endDate)
  
  while (current.isBefore(end) || current.isSame(end)) {
    const dateStr = current.format('YYYY-MM-DD')
    const today = dayjs().format('YYYY-MM-DD')
    
    //window.logger.log(`[CalendarView] displayDates: dateStr=${dateStr}, dayName=${current.format('dddd')}, current.day()=${current.day()}`)
    
    // 获取农历日期和节假日信息
    const year = parseInt(dateStr.substring(0, 4))
    const month = parseInt(dateStr.substring(5, 7))
    const day = parseInt(dateStr.substring(8, 10))
    const lunarInfo = getLunarDate(year, month, day)
    
    dates.push({
      dateStr,
      dayName: current.format('dddd'),
      dateNum: current.format('MM-DD'),
      isToday: dateStr === today,
      lunarDate: lunarInfo.displayStr
    })
    
    current = current.add(1, 'day')
  }
  
  return dates
})

const fetchSchedules = async () => {
  try {
    const params = {}
    if (dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    // 日历视图需要获取所有数据，不分页
    params.skip = 0
    params.limit = 10000
    
    // 添加搜索参数
    if (searchType.value === 'teacher' && searchTeacherId.value) {
      params.teacher_id = searchTeacherId.value
    } else if (searchType.value === 'student' && searchStudentId.value) {
      params.student_ids = searchStudentId.value.toString()
    }
    window.logger.log('[CalendarView] 请求参数:', params)
    const response = await api.get('/schedules', { params })
    window.logger.log('[CalendarView] 获取到的排课数据:', response.data)
    schedules.value = response.data.items.map(schedule => ({
      ...schedule,
      isMultiRow: isMultiRowSchedule(schedule)
    }))
    window.logger.log('[CalendarView] 处理后的排课数据:', schedules.value)
  } catch (error) {
    window.logger.error('因未登录，获取课程安排失败:', error)
    ElMessage.error(t('calendar.getSchedulesFailedNotLogin'))
  }
}

const fetchResources = async () => {
  try {
    const [teachersRes, classesRes, studentsRes, roomsRes, coursesRes] = await Promise.all([
      api.get('/teachers', { params: { is_active: true, skip: 0, limit: 100000 } }),
      api.get('/classes', { params: { is_active: true, skip: 0, limit: 100000 } }),
      api.get('/students', { params: { skip: 0, limit: 100000 } }), 
      api.get('/rooms', { params: { skip: 0, limit: 100000 } }),
      api.get('/courses', { params: { skip: 0, limit: 100000 } })
    ])
    
    teachers.value = teachersRes.data.items || teachersRes.data
    classes.value = classesRes.data.items || classesRes.data
    students.value = studentsRes.data.items || studentsRes.data
    rooms.value = roomsRes.data.items || roomsRes.data
    courses.value = coursesRes.data.items || coursesRes.data
  } catch (error) {
    window.logger.error('获取资源失败:', error)
  }
}

const isMultiRowSchedule = (schedule) => {
  const startHour = parseInt(schedule.start_time.split(':')[0])
  const endHour = parseInt(schedule.end_time.split(':')[0])
  return (endHour - startHour) > 2
}

const getSchedulesForSlot = (date, time) => {
  const dayOfWeek = dayjs(date.dateStr).day() || 7
  // 转换为与 Python 一致的星期几表示方式（1=周一，7=周日）
  const pythonDayOfWeek = dayOfWeek === 0 ? 7 : dayOfWeek
  
  //window.logger.log(`[CalendarView] 查询日期: ${date.dateStr}, 时间: ${time}, 星期几: ${pythonDayOfWeek}`)
  
  return schedules.value.filter(schedule => {
    //window.logger.log(`[CalendarView] 检查排课: ID=${schedule.id}, 星期几=${schedule.day_of_week}, 开始日期=${schedule.start_date}, 结束日期=${schedule.end_date}, 开始时间=${schedule.start_time}, 结束时间=${schedule.end_time}`)
    
    // 检查星期几是否匹配
    if (schedule.day_of_week !== pythonDayOfWeek) {
      //window.logger.log(`[CalendarView] 星期几不匹配: ${schedule.day_of_week} !== ${pythonDayOfWeek}`)
      return false
    }
    
    // 检查日期是否在排课的有效期内
    const scheduleStartDate = dayjs(schedule.start_date).format('YYYY-MM-DD')
    const scheduleEndDate = dayjs(schedule.end_date).format('YYYY-MM-DD')
    if (date.dateStr < scheduleStartDate || date.dateStr > scheduleEndDate) {
      //window.logger.log(`[CalendarView] 当前日期不在该排课日期范围内: ${date.dateStr} < ${scheduleStartDate} 或 ${date.dateStr} > ${scheduleEndDate}`)
      return false
    }
    
    // 检查时间是否匹配
    const [scheduleStartHour, scheduleStartMinute] = schedule.start_time.split(':').map(Number)
    const [scheduleEndHour, scheduleEndMinute] = schedule.end_time.split(':').map(Number)
    const [slotHour, slotMinute] = time.split(':').map(Number)

    // 将时间转换为分钟数进行比较
    const scheduleStartMinutes = scheduleStartHour * 60 + scheduleStartMinute
    const scheduleEndMinutes = scheduleEndHour * 60 + scheduleEndMinute
    const slotMinutes = slotHour * 60 + slotMinute

    // 检查slot是否在课程时间范围内
    const timeMatch = scheduleStartMinutes <= slotMinutes && scheduleEndMinutes > slotMinutes
    //window.logger.log(`[CalendarView] 时间匹配: ${scheduleStartHour} <= ${slotHour} && ${scheduleEndHour} > ${slotHour} = ${timeMatch}`)
    
    return timeMatch
  })
}

const getScheduleStyle = (schedule) => {
  const startHour = parseInt(schedule.start_time.split(':')[0])
  const endHour = parseInt(schedule.end_time.split(':')[0])
  const duration = endHour - startHour
  
  //const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#C0C4CC']
  //const colorIndex = schedule.id % colors.length
  // 根据执行状态显示不同的颜色
  let backgroundColor
  window.logger.log('[CalendarView] 课程ID:', schedule.id, '执行状态:', schedule.execution_status)
  if (schedule.execution_status === 'completed') {
    backgroundColor = '#67C23A' // 绿色 - 完训
  } else if (schedule.execution_status === 'postponed') {
    backgroundColor = '#E6A23C' // 橙色 - 延期
  } else if (schedule.execution_status === 'cancelled') {
    backgroundColor = '#909399' // 灰色 - 取消
  } else {
    //const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#C0C4CC']
    //const colorIndex = schedule.id % colors.length
    //backgroundColor = colors[colorIndex]
    // 默认状态（pending）显示蓝色
    backgroundColor = '#409EFF' // 蓝色 - 待执行
  }
  
  return {
    backgroundColor
    //backgroundColor: colors[colorIndex],
    //backgroundColor,
    //height: schedule.isMultiRow ? `${duration * 50}px` : '50px',
    //gridRow: `span ${Math.max(1, duration / 2)}`
  }
}

const getScheduleTitle = (schedule) => {
  switch (viewType.value) {
    case 'teacher':
      return getTeacherName(schedule.teacher_id)
    case 'class':
      return getClassName(schedule.class_id)
    case 'room':
      return getRoomName(schedule.room_id)
    case 'course':
      return getCourseName(schedule.course_id)
    default:
      return getCourseName(schedule.course_id)
  }
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

const showClassStudents = async (classId) => {
  if (!classId) return
  
  try {
    const response = await api.get('/students', { params: { class_id: classId, skip: 0, limit: 100000 } })
    classStudents.value = response.data.items || response.data
    classStudentsDialogVisible.value = true
  } catch (error) {
    window.logger.error('获取班级学员失败:', error)
    ElMessage.error(t('calendar.getClassStudentsFailed'))
  }
}

const getClassTeachers = (classId) => {
  const classTeachers = []
  if (schedules.value && schedules.value.length > 0) {
    schedules.value.forEach(schedule => {
      if (schedule.class_id === classId && schedule.teacher) {
        const existing = classTeachers.find(t => t.id === schedule.teacher.id)
        if (!existing) {
          classTeachers.push(schedule.teacher)
        }
      }
    })
  }
  return classTeachers
}

const getCourseTeachers = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  if (course && course.teachers && Array.isArray(course.teachers)) {
    return course.teachers
  }
  return []
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

// 学员详细信息辅助函数
const getStudentDetail = (studentId) => {
  return students.value.find(s => s.id === studentId)
}

const getStudentCode = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? student.code : '-'
}

const getStudentSchool = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.school || '-') : '-'
}

const getStudentGrade = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.grade || '-') : '-'
}

const getStudentJoinDate = (studentId) => {
  const student = getStudentDetail(studentId)
  if (!student || !student.enrollment_date) return '-'
  const date = new Date(student.enrollment_date)
  return date.toLocaleDateString('zh-CN')
}

const getStudentContact = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.contact_person || '-') : '-'
}

const getStudentPhone = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.contact_phone || '-') : '-'
}

const getStudentEmail = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.email || '-') : '-'
}

const getStudentClasses = (studentId) => {
  const student = getStudentDetail(studentId)
  if (!student || !student.class_ids || !Array.isArray(student.class_ids) || student.class_ids.length === 0) {
    return '-'
  }
  const classNames = student.class_ids.map(classId => {
    const cls = classes.value.find(c => c.id === classId)
    return cls ? cls.name : `ID:${classId}`
  })
  return classNames.join('、')
}

const getStudentIsActive = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? student.is_active : false
}

const getRoomName = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.name : '-'
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD')
}

const parseContentFeedback = (feedback) => {
  if (!feedback) return []
  const lines = feedback.split('|').filter(line => line.trim())
  return lines.map(line => {
    const parts = line.split('：')
    if (parts.length >= 2) {
      return {
        label: parts[0].trim(),
        content: parts.slice(1).join('：').trim()
      }
    }
    return {
      label: t('calendar.feedback'),
      content: line.trim()
    }
  })
}

const getClassStudentCount = (classId) => {
  if (!Array.isArray(students.value)) {
    return 0
  }
  return students.value.filter(student => {
    const belongsToClass = student.class_ids && Array.isArray(student.class_ids) && student.class_ids.includes(classId)
    return belongsToClass
  }).length
}

const addForm = ref({
  course_id: null,
  teacher_id: null,
  class_id: null,
  room_id: null,
  room_type: 'offline_physical',
  meeting_link: '',
  day_of_week: null,
  start_time: '',
  end_time: '',
  start_date: '',
  end_date: '',
  content_feedback: '',
  schedule_type: 'formal',
})
const addStartTime = ref('')
const addEndTime = ref('')
const addDialogVisible = ref(false)
const addFormRef = ref(null)
const addFormRules = {
  course_id: [{ required: true, message: t('calendar.validation.selectCourse'), trigger: 'change' }],
  teacher_id: [{ required: true, message: t('calendar.validation.selectTeacher'), trigger: 'change' }],
  class_id: [{ required: true, message: t('calendar.validation.selectClass'), trigger: 'change' }],
  start_time: [{ required: true, message: t('calendar.validation.selectStartTime'), trigger: 'change' }],
  end_time: [{ required: true, message: t('calendar.validation.selectEndTime'), trigger: 'change' }],
  start_date: [{ required: true, message: t('calendar.validation.selectStartDate'), trigger: 'change' }],
  end_date: [{ required: true, message: t('calendar.validation.selectEndDate'), trigger: 'change' }],
}

const handleEmptySlotClick = (date, time) => {
  if (!currentUser.value || (currentUser.value.role !== 'super_admin' && currentUser.value.role !== 'course_admin')) {
    return
  }
  const dayOfWeek = dayjs(date.dateStr).day() || 7
  const pythonDayOfWeek = dayOfWeek === 0 ? 7 : dayOfWeek
  addForm.value = {
    course_id: null,
    teacher_id: null,
    class_id: null,
    room_id: null,
    room_type: 'offline_physical',
    meeting_link: '',
    day_of_week: pythonDayOfWeek,
    start_time: time,
    end_time: '',
    start_date: date.dateStr,
    end_date: date.dateStr,
    content_feedback: '',
    schedule_type: 'formal',
  }
  addStartTime.value = time
  addEndTime.value = ''
  addDialogVisible.value = true
}

const handleAddRoomTypeChange = () => {
  if (addForm.value.room_type === 'online_virtual') {
    addForm.value.room_id = null
  } else {
    addForm.value.meeting_link = ''
  }
}

const handleAddSubmit = async (sendNotification = true) => {
  if (!addFormRef.value) return
  addForm.value.start_time = addStartTime.value
  addForm.value.end_time = addEndTime.value
  if (!addForm.value.day_of_week && addForm.value.start_date) {
    const dow = dayjs(addForm.value.start_date).day() || 7
    addForm.value.day_of_week = dow === 0 ? 7 : dow
  }
  await addFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const scheduleData = {
        course_id: addForm.value.course_id,
        teacher_id: addForm.value.teacher_id,
        class_id: addForm.value.class_id,
        room_type: addForm.value.room_type || 'offline_physical',
        day_of_week: addForm.value.day_of_week,
        start_time: addForm.value.start_time,
        end_time: addForm.value.end_time,
        start_date: addForm.value.start_date,
        end_date: addForm.value.end_date,
        content_feedback: addForm.value.content_feedback || '',
        schedule_type: addForm.value.schedule_type || 'formal',
        send_notification: sendNotification,
      }
      if (addForm.value.room_type === 'offline_physical') {
        scheduleData.room_id = addForm.value.room_id
        scheduleData.meeting_link = null
      } else {
        scheduleData.room_id = null
        scheduleData.meeting_link = addForm.value.meeting_link || ''
      }
      await api.post('/schedules', scheduleData)
      ElMessage.success(sendNotification ? t('calendar.addSuccessNotified') : t('calendar.addSuccess'))
      addDialogVisible.value = false
      fetchSchedules()
    } catch (error) {
      window.logger.error('添加课程安排失败:', error)
      if (error.response?.data?.detail) {
        ElMessage.error(typeof error.response.data.detail === 'string' ? error.response.data.detail : JSON.stringify(error.response.data.detail))
      } else {
        ElMessage.error(t('calendar.addScheduleFailed'))
      }
    }
  })
}

const showScheduleDetail = async (schedule) => {
  try {
    // 重新获取完整的课程数据，确保所有字段都存在
    const response = await api.get(`/schedules/${schedule.id}`)
    window.logger.log('[CalendarView] 获取到的课程详情:', response.data)
    window.logger.log('[CalendarView] 课程详情字段:', {
      id: response.data.id,
      course_id: response.data.course_id,
      teacher_id: response.data.teacher_id,
      class_id: response.data.class_id,
      room_id: response.data.room_id,
      course: response.data.course,
      teacher: response.data.teacher,
      class_: response.data.class_,
      room: response.data.room
    })
    currentSchedule.value = response.data
    detailDialogVisible.value = true
    
    // 自动加载班级学员
    //if (schedule.class_id) {
    //  await showClassStudents(schedule.class_id)
    //}
  } catch (error) {
    window.logger.error('获取课程详情失败:', error)
    ElMessage.error(t('calendar.getScheduleDetailFailed'))
  }
}

const showConflictDetails = async () => {
  if (!currentSchedule.value) return
  
  try {
    const response = await api.get(`/schedules/${currentSchedule.value.id}/conflicts`)
    conflictSchedules.value = response.data
    conflictDialogVisible.value = true
  } catch (error) {
    window.logger.error('获取冲突课程失败:', error)
    ElMessage.error(t('calendar.getConflictFailed'))
  }
}

const showExecutionStatusDetails = (type) => {
  executionStatusType.value = type
  executionStatusDialogVisible.value = true
}

// 完训处理
const handleCompleteSchedule = async () => {
  if (!currentSchedule.value) return
  
  completeForm.value = {
    content: '',
    homework: '',
    note: '',
    studentAttendance: []
  }
  
  // 加载该课程安排的学员列表
  try {
    const response = await api.get(`/schedules/${currentSchedule.value.id}`)
    if (response.data && response.data.scheduled_students) {
      // 如果已有学员记录，使用现有数据
      completeForm.value.studentAttendance = response.data.scheduled_students.map(s => ({
        id: s.id,
        name: s.name,
        status: s.attendance_status || 'present',
        absenceReason: '',
        isLocked: false  // 添加锁定标记
      }))
    } else {
      // 否则从班级获取学员列表
      const classStudents = getActiveClassStudents(currentSchedule.value.class_id)
      completeForm.value.studentAttendance = classStudents.map(student => ({
        id: student.id,
        name: student.name,
        status: 'present',
        absenceReason: '',
        isLocked: false  // 添加锁定标记
      }))
    }
    
    // 检测学员是否有对应日期的请假记录
    const scheduleDate = currentSchedule.value.start_date
    const scheduleStartTime = currentSchedule.value.start_time
    const scheduleEndTime = currentSchedule.value.end_time
    
    window.logger.log(`开始检测请假记录 - 课程日期: ${scheduleDate}, 时间: ${scheduleStartTime}-${scheduleEndTime}`)
    
    for (let item of completeForm.value.studentAttendance) {
      try {
        const leaveResponse = await api.get('/leaves', {
          params: {
            leave_type: 'student',
            student_id: item.id,
            skip: 0,
            limit: 1000
          }
        })
        
        const leaves = leaveResponse.data.items || []
        window.logger.log(`学员 ${item.name} (ID: ${item.id}) 的请假记录数量: ${leaves.length}`)
        
        const matchedLeave = leaves.find(leave => {
          // 处理不同的日期格式
          let leaveStartDate, leaveEndDate
          
          if (typeof leave.start_date === 'string') {
            leaveStartDate = new Date(leave.start_date)
          } else {
            leaveStartDate = new Date(leave.start_date)
          }
          
          if (typeof leave.end_date === 'string') {
            leaveEndDate = new Date(leave.end_date)
          } else {
            leaveEndDate = new Date(leave.end_date)
          }
          
          const scheduleStart = new Date(scheduleDate)
          
          // 设置时间为当天开始和结束，以便正确比较
          leaveStartDate.setHours(0, 0, 0, 0)
          leaveEndDate.setHours(23, 59, 59, 999)
          scheduleStart.setHours(0, 0, 0, 0)
          
          const isDateInRange = scheduleStart >= leaveStartDate && scheduleStart <= leaveEndDate
          
          window.logger.log(`  请假记录: ${leave.start_date} 至 ${leave.end_date}, 原因: ${leave.reason}, 日期匹配: ${isDateInRange}`)
          
          return isDateInRange
        })
        
        if (matchedLeave) {
          window.logger.log(`✓ 学员 ${item.name} 匹配到请假记录，状态设置为leave，原因: ${matchedLeave.reason}`)
          item.status = 'leave'
          // 使用请假记录中的实际原因，如果没有则使用默认文本
          item.absenceReason = matchedLeave.reason || t('calendar.leaveRecordExists')
          item.isLocked = true  // 锁定该学员的出勤状态
        } else {
          window.logger.log(`✗ 学员 ${item.name} 未匹配到请假记录`)
        }
      } catch (error) {
        window.logger.error(`检查学员 ${item.name} 请假记录失败:`, error)
      }
    }
  } catch (error) {
    window.logger.error('加载学员列表失败:', error)
    // 降级方案：从班级获取学员
    const classStudents = getActiveClassStudents(currentSchedule.value.class_id)
    completeForm.value.studentAttendance = classStudents.map(student => ({
      id: student.id,
      name: student.name,
      status: 'present',
      absenceReason: '',
      isLocked: false
    }))
  }
  
  completeDialogVisible.value = true
}

// 延期处理
const handlePostponeSchedule = () => {
  postponeDialogVisible.value = true
  postponeForm.value = {
    startDate: currentSchedule.value ? formatDate(currentSchedule.value.start_date) : '',
    endDate: currentSchedule.value ? formatDate(currentSchedule.value.end_date) : '',
    startTime: currentSchedule.value ? currentSchedule.value.start_time : '',
    endTime: currentSchedule.value ? currentSchedule.value.end_time : '',
    postponeReason: ''
  }
}
// 取消排课处理
const handleCancelSchedule = () => {
  cancelDialogVisible.value = true
  cancelForm.value = {
    cancelReason: ''
  }
}
// 执行完训
const executeComplete = async (sendNotification = false) => {
  if (!currentSchedule.value) return
  if (!completeFormRef.value) return
  
  await completeFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const contentFeedback = `${t('calendar.contentLabel')}：${completeForm.value.content}|${t('calendar.homeworkLabel')}：${completeForm.value.homework}|${t('calendar.noteLabel')}：${completeForm.value.note}`
        
        // 构建学员出勤状态字典
        const studentAttendance = {}
        const absenceReasons = {}
        completeForm.value.studentAttendance.forEach(item => {
          studentAttendance[item.id] = item.status
          if (item.status !== 'present' && item.absenceReason) {
            absenceReasons[item.id] = item.absenceReason
          }
        })
        
        await api.post(`/schedules/${currentSchedule.value.id}/complete`, {
          content_feedback: contentFeedback,
          student_attendance: studentAttendance,
          absence_reasons: absenceReasons,
          send_notification: sendNotification
        })
        ElMessage.success(sendNotification ? t('calendar.completeSuccessNotified') : t('calendar.completeSuccess'))
        completeDialogVisible.value = false
        fetchSchedules()
        detailDialogVisible.value = false
      } catch (error) {
        window.logger.error('完训失败:', error)
        ElMessage.error(t('calendar.completeFailed'))
      }
    }
  })
}
// 执行延期
const executePostpone = async (sendNotification = false) => {
  if (!currentSchedule.value) return
  if (!postponeFormRef.value) return
  
  await postponeFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.post(`/schedules/${currentSchedule.value.id}/postpone`, {
          start_date: new Date(postponeForm.value.startDate).toISOString(),
          end_date: new Date(postponeForm.value.endDate).toISOString(),
          start_time: postponeForm.value.startTime,
          end_time: postponeForm.value.endTime,
          postpone_reason: postponeForm.value.postponeReason,
          send_notification: sendNotification
        })
        ElMessage.success(sendNotification ? t('calendar.postponeSuccessNotified') : t('calendar.postponeSuccess'))
        postponeDialogVisible.value = false
        fetchSchedules()
        detailDialogVisible.value = false
      } catch (error) {
        window.logger.error('延期失败:', error)
        ElMessage.error(t('calendar.postponeFailed'))
      }
    }
  })
}
// 执行取消排课
const executeCancel = async (sendNotification = false) => {
  if (!currentSchedule.value) return
  if (!cancelFormRef.value) return
  
  await cancelFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.post(`/schedules/${currentSchedule.value.id}/cancel`, {
          cancel_reason: cancelForm.value.cancelReason,
          send_notification: sendNotification
        })
        ElMessage.success(sendNotification ? t('calendar.cancelSuccessNotified') : t('calendar.cancelSuccess'))
        cancelDialogVisible.value = false
        fetchSchedules()
        detailDialogVisible.value = false
      } catch (error) {
        window.logger.error('取消排课失败:', error)
        ElMessage.error(t('calendar.cancelScheduleFailed'))
      }
    }
  })
}

const handleViewTypeChange = () => {
  fetchSchedules()
}

const handleSearchTypeChange = () => {
  searchTeacherId.value = null
  searchStudentId.value = null
  fetchSchedules()
}
const handleSearchChange = () => {
  fetchSchedules()
}

const handleDateRangeChange = () => {
  emit('date-range-change', dateRange.value)
  fetchSchedules()
}

const handlePrevWeek = () => {
  if (dateRange.value.length !== 2) return
  
  const startDate = dayjs(dateRange.value[0])
  const endDate = dayjs(dateRange.value[1])
  
  dateRange.value = [
    startDate.subtract(7, 'day').format('YYYY-MM-DD'),
    endDate.subtract(7, 'day').format('YYYY-MM-DD')
  ]
  
  handleDateRangeChange()
  fetchSchedules()
}

const handleNextWeek = () => {
  if (dateRange.value.length !== 2) return
  
  const startDate = dayjs(dateRange.value[0])
  const endDate = dayjs(dateRange.value[1])
  
  dateRange.value = [
    startDate.add(7, 'day').format('YYYY-MM-DD'),
    endDate.add(7, 'day').format('YYYY-MM-DD')
  ]
  
  handleDateRangeChange()
  fetchSchedules()
}

const handleToday = () => {
  const today = dayjs()
  // 获取本周日（使用 endOf('week')）
  const thisSunday = today.endOf('week')
  // 上周六 = 本周日 - 8天
  const lastSaturday = thisSunday.subtract(8, 'day')
  
  dateRange.value = [
    lastSaturday.format('YYYY-MM-DD'),
    thisSunday.format('YYYY-MM-DD')
  ]
  
  handleDateRangeChange()
  fetchSchedules()
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
  
  // 初始化日期范围后，获取课程安排
  fetchSchedules()
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  try {
    const response = await api.get('/settings')
    if (response.data) {
      localStorage.setItem('schedule_edit_restricted', response.data.schedule_edit_restricted !== undefined ? response.data.schedule_edit_restricted : true)
      localStorage.setItem('schedule_delete_restricted', response.data.schedule_delete_restricted !== undefined ? response.data.schedule_delete_restricted : true)
    }
  } catch (error) {
    window.logger.error('获取站点设置失败:', error)
  }
  await fetchResources()
  if (dateRange.value.length === 0) {
    initDateRange()
  } else {
    // 如果已有日期范围，直接获取课程安排
    fetchSchedules()
   }
})
 
const handleEditRoomTypeChange = () => {
  if (editForm.value.room_type === 'online_virtual') {
    editForm.value.room_id = null
  } else {
    editForm.value.meeting_link = ''
  }
}

const handleCopyRoomTypeChange = () => {
  if (copyForm.value.room_type === 'online_virtual') {
    copyForm.value.room_id = null
  } else {
    copyForm.value.meeting_link = ''
  }
}

// 编辑课程
const showEditDialog = () => {
  if (!currentSchedule.value) return
  editStartTime.value = currentSchedule.value.start_time
  editEndTime.value = currentSchedule.value.end_time
  const formData = {
    id: currentSchedule.value.id,
    course_id: currentSchedule.value.course_id,
    teacher_id: currentSchedule.value.teacher_id,
    class_id: currentSchedule.value.class_id,
    room_id: currentSchedule.value.room_id,
    room_type: currentSchedule.value.room_type || 'offline_physical',
    meeting_link: currentSchedule.value.meeting_link || '',
    // 使用统一的整数转换函数
    day_of_week: getDayOfWeekIntFromDate(currentSchedule.value.start_date),
    start_time: currentSchedule.value.start_time,
    end_time: currentSchedule.value.end_time,
    // 使用 dayjs 格式化，确保与其他 enrollment_date 逻辑一致
    start_date: currentSchedule.value.start_date ? dayjs(currentSchedule.value.start_date).format('YYYY-MM-DD') : null,
    end_date: currentSchedule.value.end_date ? dayjs(currentSchedule.value.end_date).format('YYYY-MM-DD') : null,
    schedule_type: currentSchedule.value.schedule_type || 'formal'
  }
  
  originalEditForm.value = { ...formData }
  editForm.value = formData
  editDialogVisible.value = true
}
 
const executeEdit = async (sendNotification = true) => {
  if (editLoading.value) return
  editLoading.value = true

  try {
    const { id, ...updateData } = editForm.value
    
    // 更新开始和结束时间
    updateData.start_time = editStartTime.value
    updateData.end_time = editEndTime.value
    
    // 检查内容是否改变
    const isChanged = 
      editForm.value.course_id !== originalEditForm.value.course_id ||
      editForm.value.teacher_id !== originalEditForm.value.teacher_id ||
      editForm.value.class_id !== originalEditForm.value.class_id ||
      editForm.value.room_id !== originalEditForm.value.room_id ||
      editForm.value.room_type !== originalEditForm.value.room_type ||
      editForm.value.meeting_link !== originalEditForm.value.meeting_link ||
      editForm.value.day_of_week !== originalEditForm.value.day_of_week ||
      editForm.value.schedule_type !== originalEditForm.value.schedule_type ||
      editStartTime.value !== originalEditForm.value.start_time ||
      editEndTime.value !== originalEditForm.value.end_time ||
      editForm.value.start_date !== originalEditForm.value.start_date ||
      editForm.value.end_date !== originalEditForm.value.end_date
    
    if (!isChanged) {
      ElMessage.warning(t('calendar.noChangeNoSave'))
      editLoading.value = false
      return
    }
    
    // 使用统一的整数转换函数，确保周日正确转换为 7
    const dayOfWeek = getDayOfWeekIntFromDate(updateData.start_date)
    
    const submitData = {
      ...updateData,
      day_of_week: dayOfWeek,
      // 直接发送日期字符串，因为 value-format 已经保证了格式是 YYYY-MM-DD
      start_date: updateData.start_date || null,
      end_date: updateData.end_date || null,
      room_type: updateData.room_type || 'offline_physical',
      meeting_link: updateData.room_type === 'online_virtual' ? updateData.meeting_link : null,
      send_notification: sendNotification
    }
    
    await api.put(`/schedules/${id}`, submitData)
    ElMessage.success(sendNotification ? t('calendar.editSuccessNotified') : t('calendar.editSuccess'))
    editDialogVisible.value = false
    await fetchSchedules()
    
  } catch (error) {
    window.logger.error('编辑失败:', error)
    handleScheduleError(error)
  } finally {
    editLoading.value = false
  }
}
 
// 复制课程
const showCopyDialog = () => {
  if (!currentSchedule.value) return
  copyStartTime.value = currentSchedule.value.start_time
  copyEndTime.value = currentSchedule.value.end_time
  copyForm.value = {
    id: null,
    course_id: currentSchedule.value.course_id,
    teacher_id: currentSchedule.value.teacher_id,
    class_id: currentSchedule.value.class_id,
    room_id: currentSchedule.value.room_id,
    room_type: currentSchedule.value.room_type || 'offline_physical',
    meeting_link: currentSchedule.value.meeting_link || '',
    // 使用统一的整数转换函数
    day_of_week: getDayOfWeekIntFromDate(currentSchedule.value.start_date),
    start_time: currentSchedule.value.start_time,
    end_time: currentSchedule.value.end_time,
    start_date: '',
    end_date: '',
    schedule_type: currentSchedule.value.schedule_type || 'formal'
  }
  copyDialogVisible.value = true
}
 
const executeCopy = async (sendNotification = true) => {
  if (!copyForm.value.start_date || !copyForm.value.end_date) {
    ElMessage.warning(t('calendar.selectStartEndDate'))
    return
  }
  
  if (copyLoading.value) return
  copyLoading.value = true
  
  try {
    copyForm.value.start_time = copyStartTime.value
    copyForm.value.end_time = copyEndTime.value
    
    // 使用统一的整数转换函数，确保周日正确转换为 7
    const dayOfWeek = getDayOfWeekIntFromDate(copyForm.value.start_date)
    
    const submitData = {
      ...copyForm.value,
      day_of_week: dayOfWeek,
      // 直接发送日期字符串
      start_date: copyForm.value.start_date || null,
      end_date: copyForm.value.end_date || null,
      room_type: copyForm.value.room_type || 'offline_physical',
      meeting_link: copyForm.value.room_type === 'online_virtual' ? copyForm.value.meeting_link : null,
      send_notification: sendNotification
    }
    
    await api.post('/schedules', submitData)
    ElMessage.success(sendNotification ? t('calendar.copySuccessNotified') : t('calendar.copySuccess'))
    copyDialogVisible.value = false
    await fetchSchedules()
    
  } catch (error) {
    window.logger.error('复制失败:', error)
    if (error.response?.data?.detail && error.response.data.detail.includes('已经存在')) {
      ElMessage.warning(t('calendar.scheduleExistsRefreshed'))
      copyDialogVisible.value = false
      await fetchSchedules()
    } else {
      handleScheduleError(error)
    }
  } finally {
    copyLoading.value = false
  }
}

// 统一的排课错误处理函数
const handleScheduleError = (error) => {
  const errorMsg = error.response?.data?.detail || t('calendar.operationFailed')
  
  if (errorMsg.includes('以下学员在该时间段不可用')) {
    ElMessageBox.alert(
      `<div style="line-height: 1.6;">
        <strong>⚠️ ${t('calendar.scheduleConflictWarning')}</strong><br/>
        ${errorMsg}<br/><br/>
        <span style="color: #e6a23c;">💡 ${t('calendar.suggestion')}：</span><br/>
        1. ${t('calendar.suggestionCheckTime')}<br/>
        2. ${t('calendar.suggestionHoliday')}
      </div>`,
      t('calendar.scheduleConflict'),
      {
        confirmButtonText: t('calendar.goCheck'),
        dangerouslyUseHTMLString: true,
        type: 'warning'
      }
    )
  } else if (errorMsg.includes('已经存在完全相同的排课')) {
    ElMessage.warning(t('calendar.schedulePeriodExistsRefreshed'))
    copyDialogVisible.value = false
    fetchSchedules()
  } else {
    ElMessage.error(errorMsg)
  }
}

// 作业安排
const showHomeworkDialog = () => {
  if (!currentSchedule.value) return
  currentHomeworkSchedule.value = currentSchedule.value
  
  if (currentSchedule.value.content_feedback) {
    const feedbackParts = parseContentFeedback(currentSchedule.value.content_feedback)
    const homeworkPart = feedbackParts.find(p => p.label === '作业')
    homeworkForm.value.classHomework = homeworkPart ? homeworkPart.content : ''
  } else {
    homeworkForm.value.classHomework = ''
  }
  
  homeworkForm.value.regularHomework = currentSchedule.value.homework_regular || ''
  
  if (currentSchedule.value.homework_images) {
    const imageUrls = currentSchedule.value.homework_images.split(',').filter(url => url)
    homeworkForm.value.images = imageUrls.map(url => ({
      name: url.split('/').pop(),
      url: url,
      response: { url: url }
    }))
  } else {
    homeworkForm.value.images = []
  }
  
  homeworkDialogVisible.value = true
}
 
const executeHomework = async (sendNotification = false) => {
  if (!homeworkFormRef.value) return
  
  try {
    await homeworkFormRef.value.validate()
  } catch (error) {
    return
  }
  
  try {
    const feedbackParts = parseContentFeedback(currentSchedule.value.content_feedback || '')
    const contentPart = feedbackParts.find(p => p.label === t('calendar.contentLabel'))
    const notePart = feedbackParts.find(p => p.label === t('calendar.noteLabel'))
    
    const newContentFeedback = `${t('calendar.contentLabel')}：${contentPart ? contentPart.content : ''}|${t('calendar.homeworkLabel')}：${homeworkForm.value.classHomework}|${t('calendar.noteLabel')}：${notePart ? notePart.content : ''}`
    
    await api.put(`/schedules/${currentSchedule.value.id}`, {
      content_feedback: newContentFeedback,
      homework_regular: homeworkForm.value.regularHomework,
      homework_images: homeworkForm.value.images && homeworkForm.value.images.length > 0 
        ? homeworkForm.value.images.map(img => img.response?.url || img.url).filter(url => url).join(',') 
        : ''
    })
    
    if (sendNotification) {
      const classInfo = classes.value.find(c => c.id === currentSchedule.value.class_id)
      
      let siteUrl = localStorage.getItem('site_url')
      if (!siteUrl) {
        try {
          const response = await api.get('/settings/site-info')
          if (response.data && response.data.site_url) {
            siteUrl = response.data.site_url
            localStorage.setItem('site_url', siteUrl)
          }
        } catch (error) {
          window.logger.error('获取站点URL失败:', error)
        }
      }
      if (!siteUrl) {
        siteUrl = window.location.origin
      }
      
      let imageUrls = []
      if (homeworkForm.value.images && homeworkForm.value.images.length > 0) {
        imageUrls = homeworkForm.value.images.map(img => {
          const url = img.response?.url || img.url
          return url.startsWith('http') ? url : siteUrl + url
        }).filter(url => url)
      }
      
      if (classInfo && classInfo.wechat_webhook) {
        const scheduleDate = currentSchedule.value.start_date
        const scheduleTime = `${currentSchedule.value.start_time}-${currentSchedule.value.end_time}`
        const classStudents = getActiveClassStudents(currentSchedule.value.class_id)
        const studentNames = classStudents.length > 0 ? classStudents.map(s => s.name).join('、') : t('calendar.none')
        
        let homeworkMessage = `${t('calendar.homeworkMsgTitle')}\n\n${t('calendar.course')}：${getCourseName(currentSchedule.value.course_id)}\n${t('calendar.dateTime')}：${scheduleDate} ${scheduleTime}\n${t('calendar.content')}：${contentPart ? contentPart.content : t('calendar.none')}\n${t('calendar.class')}：${getClassName(currentSchedule.value.class_id)}\n${t('calendar.student')}：${studentNames}\n\n${t('calendar.classHomework')}：${homeworkForm.value.classHomework}\n${t('calendar.regularHomework')}：${homeworkForm.value.regularHomework}\n\n${t('calendar.homeworkMsgReminder')} @所有人`
        
        try {
          await api.post('/wechat/send-message', {
            webhook_url: classInfo.wechat_webhook,
            message: homeworkMessage,
            images: imageUrls,
            class_id: classInfo.id
          })
        } catch (error) {
          window.logger.error('发送微信作业通知失败:', error)
        }
      }
      
      if (classInfo) {
        try {
          await api.post('/email/send-homework', {
            class_id: classInfo.id,
            course_name: getCourseName(currentSchedule.value.course_id),
            class_homework: homeworkForm.value.classHomework,
            regular_homework: homeworkForm.value.regularHomework,
            images: imageUrls
          })
        } catch (error) {
          window.logger.error('发送邮件作业通知失败:', error)
        }
      }
    }
    
    ElMessage.success(sendNotification ? t('calendar.homeworkSuccessNotified') : t('calendar.homeworkSaved'))
    homeworkDialogVisible.value = false
    fetchSchedules()
  } catch (error) {
    window.logger.error('作业安排失败:', error)
    ElMessage.error(t('calendar.homeworkFailed'))
  }
}
 
// 补课
const showMakeupDialog = async () => {
  if (!currentSchedule.value) return
  currentMakeupSchedule.value = currentSchedule.value
  makeupForm.value = {
    makeupType: 'makeup',
    studentIds: [],
    startDate: '',
    endDate: '',
    startTime: '',
    endTime: '',
    roomId: null,
    declinedReason: ''
  }
  
  try {
    // 只获取需要补课的学员（缺席或请假且未补课）
    const response = await api.get(`/schedules/${currentSchedule.value.id}/absent-students`)
    classStudents.value = response.data
    
    if (classStudents.value.length === 0) {
      ElMessage.info(t('calendar.noMakeupStudents'))
      makeupDialogVisible.value = false
      return
    }
  } catch (error) {
    window.logger.error('获取需要补课的学员失败:', error)
    ElMessage.error(t('calendar.getMakeupStudentsFailed'))
    return
  }
  
  makeupDialogVisible.value = true
}
 
const executeMakeup = async () => {
  if (!makeupFormRef.value) return
  
  try {
    await makeupFormRef.value.validate()
  } catch (error) {
    return
  }
  
  try {
    if (makeupForm.value.makeupType === 'makeup') {
      await api.post(`/schedules/${currentSchedule.value.id}/makeup`, {
        start_date: makeupForm.value.startDate,
        end_date: makeupForm.value.endDate,
        start_time: makeupForm.value.startTime,
        end_time: makeupForm.value.endTime,
        student_ids: makeupForm.value.studentIds,
        room_id: makeupForm.value.roomId
      })
      ElMessage.success(t('calendar.makeupSuccess'))
    } else {
      await api.post(`/schedules/${currentSchedule.value.id}/decline-makeup`, {
        student_ids: makeupForm.value.studentIds,
        declined_reason: makeupForm.value.declinedReason
      })
      ElMessage.success(t('calendar.declineMakeupSuccess'))
    }
    makeupDialogVisible.value = false
    fetchSchedules()
  } catch (error) {
    window.logger.error('操作失败:', error)
    ElMessage.error(t('calendar.operationFailed'))
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
      lines.push(`${student.name}: ${t('calendar.makeupCompleted')} (ID: ${student.makeup_schedule_id})`)
    } else if (student.makeup_status === 'declined') {
      lines.push(`${student.name}: ${t('calendar.makeupDeclined')} (${student.declined_reason})`)
    }
  })
  
  return lines.join('\n')
}

const hasStudentsNeedingMakeup = (schedule) => {
  if (!schedule.scheduled_students || schedule.scheduled_students.length === 0) return false
  return schedule.scheduled_students.some(student => 
    (student.attendance_status === 'absent' || student.attendance_status === 'leave') &&
    (!student.makeup_status || student.makeup_status === 'pending')
  )
}

// 删除课程
const handleDeleteSchedule = () => {
  if (!currentSchedule.value) return
  ElMessageBox.confirm(t('calendar.confirmDeleteSchedule'), t('calendar.tip'), {
    confirmButtonText: t('calendar.confirm'),
    cancelButtonText: t('calendar.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/schedules/${currentSchedule.value.id}`)
      ElMessage.success(t('calendar.deleteSuccess'))
      fetchSchedules()
      detailDialogVisible.value = false
    } catch (error) {
      window.logger.error('删除失败:', error)
      ElMessage.error(t('calendar.deleteFailed'))
    }
  }).catch(() => {})
}

const handleNotifyNow = () => {
  if (!currentSchedule.value) return
  ElMessageBox.confirm(t('calendar.notifyNowConfirm'), t('calendar.notifyNow'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.post(`/schedules/${currentSchedule.value.id}/notify`)
      ElMessage.success(t('calendar.notifyNowSuccess'))
    } catch (error) {
      window.logger.error('立即通知失败:', error)
      ElMessage.error(t('calendar.notifyNowFail'))
    }
  }).catch(() => {})
}
 
// 图片预览
const handlePicturePreview = async (uploadFile) => {
  const url = uploadFile.response?.url || uploadFile.url
  if (!url) return
  
  let siteUrl = localStorage.getItem('site_url')
  
  if (!siteUrl) {
    try {
      const response = await api.get('/settings/site-info')
      if (response.data && response.data.site_url) {
        siteUrl = response.data.site_url
        localStorage.setItem('site_url', siteUrl)
      }
    } catch (error) {
      window.logger.error('获取站点URL失败:', error)
    }
  }
  
  if (!siteUrl) {
    siteUrl = window.location.origin
  }
  
  const fullUrl = url.startsWith('http') ? url : siteUrl + url
  window.open(fullUrl, '_blank')
}
 
// 上传成功
const handleUploadSuccess = (response, uploadFile, uploadFiles) => {
  window.logger.log('上传成功:', response, uploadFile)
}
 
// 删除图片
const handleRemove = (uploadFile, uploadFiles) => {
  window.logger.log('删除图片:', uploadFile)
}
 
// 从日期获取星期几
const getDayOfWeekFromDate = (date) => {
  // 转换为与 Python 一致的星期几表示方式（1=周一，7=周日）
  const dayOfWeek = dayjs(date).day() || 7
  const pythonDayOfWeek = dayOfWeek === 0 ? 7 : dayOfWeek
  return pythonDayOfWeek
}

// 用于表单初始化的辅助函数（虽然上面的函数已经返回整数，但为了统一逻辑，我们保持一致）
const getDayOfWeekIntFromDate = (date) => {
  const dayOfWeek = dayjs(date).day() || 7
  return dayOfWeek === 0 ? 7 : dayOfWeek
}

// 临时增员相关函数
const showExtraStudentDialog = async () => {
  if (!currentSchedule.value) return
  selectedExtraStudentIds.value = []
  extraStudentLoading.value = false
  extraStudentDialogVisible.value = true

  const extraStudents = (currentSchedule.value.scheduled_students || []).filter(s => s.is_extra)
  currentExtraStudents.value = extraStudents

  try {
    const response = await api.get('/students')
    const allStudents = response.data.items || response.data
    const classStudentIds = new Set()
    if (currentSchedule.value.class_id) {
      const classResponse = await api.get(`/classes/${currentSchedule.value.class_id}`)
      if (classResponse.data && classResponse.data.students) {
        classResponse.data.students.forEach(s => classStudentIds.add(s.id))
      }
    }
    const scheduledStudentIds = new Set((currentSchedule.value.scheduled_students || []).map(s => s.id))
    availableExtraStudents.value = allStudents.filter(s =>
      !classStudentIds.has(s.id) && !scheduledStudentIds.has(s.id)
    )
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
    ElMessage.error(t('calendar.operationFailed'))
  }
}

const handleAddExtraStudents = async () => {
  if (selectedExtraStudentIds.value.length === 0) return
  extraStudentLoading.value = true
  try {
    const response = await api.post(`/schedules/${currentSchedule.value.id}/extra-students`, selectedExtraStudentIds.value)
    const result = response.data
    if (result.added_students && result.added_students.length > 0) {
      ElMessage.success(t('calendar.extraStudentAdded', { count: result.added_students.length }))
    }
    if (result.skipped_students && result.skipped_students.length > 0) {
      const skippedNames = result.skipped_students.map(s => `${s.name || s.student_id}(${s.reason})`).join(', ')
      ElMessage.warning(t('calendar.extraStudentSkipped', { names: skippedNames }))
    }
    selectedExtraStudentIds.value = []
    const scheduleResponse = await api.get(`/schedules/${currentSchedule.value.id}`)
    if (scheduleResponse.data) {
      currentSchedule.value = scheduleResponse.data
      const extraStudents = (scheduleResponse.data.scheduled_students || []).filter(s => s.is_extra)
      currentExtraStudents.value = extraStudents
      const scheduledStudentIds = new Set((scheduleResponse.data.scheduled_students || []).map(s => s.id))
      availableExtraStudents.value = availableExtraStudents.value.filter(s => !scheduledStudentIds.has(s.id))
    }
    fetchSchedules()
  } catch (error) {
    window.logger.error('添加临时增员学员失败:', error)
    ElMessage.error(t('calendar.operationFailed'))
  } finally {
    extraStudentLoading.value = false
  }
}

const removeExtraStudent = async (studentId) => {
  try {
    await api.delete(`/schedules/${currentSchedule.value.id}/extra-students/${studentId}`)
    ElMessage.success(t('calendar.extraStudentRemoved'))
    currentExtraStudents.value = currentExtraStudents.value.filter(s => s.id !== studentId)
    fetchSchedules()
  } catch (error) {
    window.logger.error('移除临时增员学员失败:', error)
    ElMessage.error(t('calendar.operationFailed'))
  }
}
</script>

<style scoped>
.calendar-view {
  padding: 6px;
  padding-left: 0px;
  padding-right: 0px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
@media (max-width: 768px) {
  .header-actions {
    gap: 6px;
    justify-content: center;
  }
  
  .header-actions .el-select {
    width: 100%;
    max-width: 150px;
  }
  
  .header-actions .el-date-picker {
    width: 100%;
    max-width: 200px;
    margin-right: 0;
  }
  
  .header-actions .el-button {
    font-size: 12px;
    padding: 6px 8px;
    flex: 0 0 auto;
  }
}

.calendar-container {
  display: flex;
  overflow-x: auto;
  border: 1px solid #EBEEF5;
}

.date-lunar {
  font-size: 12px;
  color: #EBEEF5;
  margin-top: 2px;
}

.date-holiday {
  font-size: 12px;
  color: #F56C6C;
  font-weight: bold;
  margin-top: 2px;
}

.time-column {
  display: flex;
  flex-direction: column;
  min-width: 80px;
  background-color: #F5F7FA;
  border-right: 1px solid #EBEEF5;
}

.time-header {
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border-bottom: 1px solid #EBEEF5;
  background-color: #409EFF;
  color: white;
}

.time-cell {
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #EBEEF5;
  font-size: 12px;
  color: #606266;
}

.dates-column {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.date-header-row {
  display: flex;
  height: 90px;
  background-color: #409EFF;
  color: white;
}

.date-header {
  min-width: 120px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-right: 1px solid #EBEEF5;
}

.date-name {
  font-size: 12px;
}

.date-num {
  font-size: 16px;
  font-weight: bold;
  margin-top: 4px;
}

.date-num.is-today {
  background-color: #F56C6C;
  padding: 2px 8px;
  border-radius: 4px;
}

.time-row {
  display: flex;
  height: 35px;
  border-bottom: 1px solid #EBEEF5;
}

.schedule-cell {
  min-width: 100px;
  flex: 1;
  border-right: 1px solid #EBEEF5;
  position: relative;
  padding: 2px;
  display: flex;
  flex-direction: row;
  gap: 2px;
  min-height: 40px;
  max-height: 120px;
  overflow-x: auto;
  overflow-y: hidden;
}

.schedule-cell.empty-slot-clickable {
  cursor: pointer;
  transition: background-color 0.2s;
}

.schedule-cell.empty-slot-clickable:hover {
  background-color: #ecf5ff;
}

.schedule-cell.empty-slot-clickable:hover::after {
  content: '+';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 18px;
  color: #409eff;
  opacity: 0.6;
  pointer-events: none;
}

.schedule-item {
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  left: 0;
  right: 0;
  top: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  flex-shrink: 0;
  min-width: 80px;
  max-width: 150px;
}

.schedule-item:hover {
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.schedule-item.has-conflict {
  border: 2px solid #F56C6C;
}

.schedule-item.is-multi-row {
  position: relative;
  left: 0;
  right: 0;
  top: 0;
}

.schedule-title {
  font-weight: bold;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.schedule-time {
  font-size: 11px;
  opacity: 0.9;
}

.schedule-feedback {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 12px;
}

/* 学员信息 Tooltip 样式 */
.student-info-tooltip {
  max-width: 400px !important;
}

.student-detail-info {
  padding: 8px 0;
  line-height: 1.8;
}

.student-detail-info .info-item {
  margin-bottom: 4px;
  font-size: 13px;
}

.student-detail-info .info-item strong {
  color: #606266;
  display: inline-block;
  min-width: 100px;
}
</style>