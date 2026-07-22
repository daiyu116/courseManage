// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="schedules-page">
    <!-- 导航栏 -->
    <el-card class="nav-card" style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/dashboard')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('schedules.dashboard') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/courses')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('schedules.courseManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="success" @click="goToPage('/admin/teachers')" style="width: 100%;height: 100%;">
            <el-icon><User /></el-icon>
            {{ t('schedules.teacherManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
            <el-button type="warning" @click="goToPage('/admin/classes')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
            {{ t('schedules.classManagement') }}
            </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="warning" @click="goToPage('/admin/students')" style="width: 100%;height: 100%;">
            <el-icon><UserFilled /></el-icon>
            {{ t('schedules.studentManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="info" @click="goToPage('/admin/rooms')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
            {{ t('schedules.roomManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="danger" @click="goToPage('/admin/leaves')" style="width: 100%;height: 100%;">
            <el-icon><Calendar /></el-icon>
            {{ t('schedules.holidayManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/conditions')" style="width: 100%;height: 100%;">
            <el-icon><Setting /></el-icon>
            {{ t('schedules.conditionManagement') }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('schedules.scheduleManagement') }}</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('schedules.goBack') }}
            </el-button>
            <el-button type="warning" @click="goToPage('/admin/daily-words')">
              <el-icon><Reading /></el-icon>
              {{ t('schedules.dailyWords') }}
            </el-button>
            <el-button v-if="hasFeature(licenseFeatures.SMART_SCHEDULING) && currentUser && currentUser.role !== 'teaching_assistant'" type="success" @click="showAutoScheduleDialog">
              <el-icon><MagicStick /></el-icon>
              {{ t('schedules.smartScheduling') }}
            </el-button>
            <el-tooltip v-else-if="currentUser && currentUser.role !== 'teaching_assistant'" :content="t('schedules.smartSchedulingLicense')" placement="bottom">
              <el-button type="success" disabled>
                <el-icon><Lock /></el-icon>
                {{ t('schedules.smartScheduling') }}
              </el-button>
            </el-tooltip>
            <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('schedules.manualSchedule') }}
            </el-button>
            <el-button v-if="currentUser && (currentUser.role === 'super_admin' || (currentUser.role === 'course_admin' && currentUser.is_subject_teacher))" type="danger" @click="batchDeleteSchedules" :disabled="selectedSchedules.length === 0">
              <el-icon><Delete /></el-icon>
              {{ t('schedules.batchDelete') }} ({{ selectedSchedules.length }})
            </el-button>
            <el-button v-if="currentUser && currentUser.role === 'super_admin'" type="danger" @click="clearAllSchedules">
              <el-icon><Delete /></el-icon>
              {{ t('schedules.clearAll') }}
            </el-button>
            <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" type="info" @click="downloadImportTemplate">
              <el-icon><Download /></el-icon>
              {{ t('schedules.downloadTemplate') }}
            </el-button>
            <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" type="primary" @click="showImportDialog">
              <el-icon><Upload /></el-icon>
              {{ t('schedules.import') }}
            </el-button>
            <el-button type="warning" @click="handleScreenshot" :loading="isScreenshotting">
              <el-icon><Camera /></el-icon>
              {{ t('schedules.screenshot') }}
            </el-button>
            <el-dropdown @command="handleExport" split-button type="success">
              <el-icon><Download /></el-icon>
              {{ t('schedules.export') }}
              <template #dropdown>
                <el-dropdown-item command="excel">{{ t('schedules.exportExcel') }}</el-dropdown-item>
                <el-dropdown-item command="csv">{{ t('schedules.exportCSV') }}</el-dropdown-item>
                <el-dropdown-item command="pdf">{{ t('schedules.exportPDF') }}</el-dropdown-item>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane :label="t('schedules.allCourses')" name="all">
          <div class="filter-bar">
            <el-date-picker
              v-model="filterStartDate"
              type="date"
              :placeholder="t('schedules.startDate')"
              value-format="YYYY-MM-DD"
                @change="fetchSchedules"
            />
            <el-date-picker
              v-model="filterEndDate"
              type="date"
              :placeholder="t('schedules.endDate')"
              value-format="YYYY-MM-DD"
                @change="fetchSchedules"
            />
            <el-col :span="2">
              <el-form-item label-width="0">
                <el-button @click="resetFilters" style="width: 100%">{{ t('common.reset') }}</el-button>
              </el-form-item>
            </el-col>
            <el-select v-model="filterCourseIds" filterable :placeholder="t('schedules.course')" multiple collapse-tags clearable @change="fetchSchedules">
              <el-option
                v-for="course in courses"
                :key="course.id"
                :label="course.name"
                :value="course.id"
              >
                <el-tooltip placement="right" :show-after="200">
                  <template #content>
                    <div v-if="getCourseTeachers(course.id).length > 0">
                      <div style="font-weight: bold; margin-bottom: 8px;">{{ t('schedules.teacherLabel') }}</div>
                      <div v-for="teacher in getCourseTeachers(course.id)" :key="teacher.id" style="margin-bottom: 4px;">
                        {{ teacher.name }}
                      </div>
                    </div>
                    <div v-else>{{ t('schedules.noTeacher') }}</div>
                  </template>
                  <span>{{ course.name }}</span>
                </el-tooltip>
              </el-option>
            </el-select>
            <el-select v-model="filterScheduleType" :placeholder="t('schedules.courseType')" clearable @change="fetchSchedules">
              <el-option :label="t('schedules.formalClass')" value="formal" />
              <el-option :label="t('schedules.trialClass')" value="trial" />
            </el-select>
            <el-select v-model="filterTeacherIds" filterable :placeholder="t('schedules.teacher')" multiple collapse-tags clearable @change="fetchSchedules">
              <el-option
                v-for="teacher in teachers"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
              >
                <el-tooltip placement="right" :show-after="200">
                  <template #content>
                    <div v-if="teacher.contact_phone">
                      <div style="font-weight: bold;">{{ t('schedules.contactInfo') }}</div>
                      <div>{{ teacher.contact_phone }}</div>
                    </div>
                    <div v-if="teacher.is_active !== undefined">
                      <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.employmentStatus') }}</div>
                      <div>{{ teacher.is_active ? t('schedules.employed') : t('schedules.notEmployed') }}</div>
                    </div>
                    <div v-if="!teacher.contact_phone && teacher.is_active === undefined">{{ t('schedules.noDetailInfo') }}</div>
                  </template>
                  <span>{{ teacher.name }}</span>
                </el-tooltip>
              </el-option>
            </el-select>
            <el-select v-model="filterClassIds" filterable :placeholder="t('schedules.class')" multiple collapse-tags clearable @change="fetchSchedules">
              <el-option
                v-for="class_ in classes"
                :key="class_.id"
                :label="class_.name"
                :value="class_.id"
              >
                <el-tooltip placement="right" :show-after="200">
                  <template #content>
                    <div v-if="getActiveClassStudents(class_.id).length > 0">
                      <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('schedules.activeStudents') }}</div>
                      <div v-for="student in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                        {{ student.name }}
                      </div>
                    </div>
                    <div v-if="getInactiveClassStudents(class_.id).length > 0">
                      <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('schedules.inactiveStudents') }}</div>
                      <div v-for="student in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                        {{ student.name }}
                      </div>
                    </div>
                    <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                      {{ t('schedules.noStudent') }}
                    </div>
                  </template>
                  <span>{{ class_.name }}</span>
                </el-tooltip>
              </el-option>
            </el-select>
            <el-select v-model="filterStudentIds" filterable :placeholder="t('schedules.student')" multiple collapse-tags clearable @change="fetchSchedules">
              <el-option
                v-for="student in students"
                :key="student.id"
                :label="student.name"
                :value="student.id"
              >
                <el-tooltip placement="right" :show-after="200">
                  <template #content>
                    <div v-if="student.school">
                      <div style="font-weight: bold;">{{ t('schedules.school') }}</div>
                      <div>{{ student.school }}</div>
                    </div>
                    <div v-if="student.grade">
                      <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.grade') }}</div>
                      <div>{{ student.grade }}</div>
                    </div>
                    <div v-if="student.contact_person">
                      <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.contact') }}</div>
                      <div>{{ student.contact_person }}</div>
                    </div>
                    <div v-if="student.contact_phone">
                      <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.contactInfo') }}</div>
                      <div>{{ student.contact_phone }}</div>
                    </div>
                    <div v-if="student.is_active !== undefined">
                      <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.activeStatus') }}</div>
                      <div>{{ student.is_active ? t('schedules.active') : t('schedules.inactive') }}</div>
                    </div>
                    <div v-if="!student.school && !student.grade && !student.contact_person && !student.contact_phone && student.is_active === undefined">
                      {{ t('schedules.noDetailInfo') }}
                    </div>
                  </template>
                  <span>{{ student.name }}</span>
                </el-tooltip>
              </el-option>
            </el-select>
            <el-select v-model="filterRoomIds" filterable :placeholder="t('schedules.room')" multiple collapse-tags clearable @change="fetchSchedules">
              <el-option
                v-for="room in rooms"
                :key="room.id"
                :label="room.name"
                :value="room.id"
              >
                <el-tooltip placement="right" :show-after="200">
                  <template #content>
                    <div v-if="room.location">
                      <div style="font-weight: bold;">{{ t('schedules.location') }}</div>
                      <div>{{ room.location }}</div>
                    </div>
                    <div v-if="room.capacity">
                      <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.capacity') }}</div>
                      <div>{{ room.capacity }}{{ t('schedules.peopleUnit') }}</div>
                    </div>
                    <div v-if="room.facilities">
                      <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.facilities') }}</div>
                      <div>{{ room.facilities }}</div>
                    </div>
                    <div v-if="!room.location && !room.capacity && !room.facilities">
                      {{ t('schedules.noDetailInfo') }}
                    </div>
                  </template>
                  <span>{{ room.name }}</span>
                </el-tooltip>
              </el-option>
            </el-select>
            <el-select v-model="filterDaysOfWeek" filterable :placeholder="t('schedules.dayOfWeek')" multiple collapse-tags clearable @change="fetchSchedules">
              <el-option :label="t('schedules.monday')" :value="1" />
              <el-option :label="t('schedules.tuesday')" :value="2" />
              <el-option :label="t('schedules.wednesday')" :value="3" />
              <el-option :label="t('schedules.thursday')" :value="4" />
              <el-option :label="t('schedules.friday')" :value="5" />
              <el-option :label="t('schedules.saturday')" :value="6" />
              <el-option :label="t('schedules.sunday')" :value="7" />
            </el-select>
            <el-select v-model="filterHasConflict" :placeholder="t('schedules.conflictStatus')" clearable @change="fetchSchedules">
              <el-option :label="t('schedules.hasConflict')" :value="true" />
              <el-option :label="t('schedules.noConflict')" :value="false" />
            </el-select>
            <el-select v-model="filterExecutionStatus" :placeholder="t('schedules.executionStatus')" clearable @change="fetchSchedules">
              <el-option :label="t('schedules.pending')" value="pending" />
              <el-option :label="t('schedules.completed')" value="completed" />
              <el-option :label="t('schedules.postponed')" value="postponed" />
              <el-option :label="t('schedules.cancelled')" value="cancelled" />
            </el-select>
          </div>

          <div class="fake-scrollbar" ref="topScrollbarRef">
            <div class="scrollbar-inner" :style="{ width: scrollbarWidth + 'px' }"></div>
          </div>
          <el-table :data="schedules" stripe v-loading="loading" style="margin-top: 0" @selection-change="handleSelectionChange" :default-sort="{ prop: 'id', order: 'descending' }" @sort-change="handleSortChange" ref="mainTableRef">
                <el-table-column v-if="currentUser && currentUser.role !== 'teaching_assistant'" type="selection" width="55" />
                <el-table-column prop="id" label="ID" width="70" sortable />
                <el-table-column :label="t('schedules.course')" width="135" sortable prop="course">
                  <template #default="{ row }">
                    {{ getCourseName(row.course_id) }}
                  </template>
                </el-table-column>
                <el-table-column :label="t('schedules.courseType')" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.schedule_type === 'trial' ? 'warning' : 'success'" size="small">
                      {{ row.schedule_type === 'trial' ? t('schedules.trialClass') : t('schedules.formalClass') }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="t('schedules.teacher')" width="100" sortable prop="teacher">
                  <template #default="{ row }">
                    <el-popover placement="top" :width="300" trigger="hover">
                      <template #reference>
                        <span style="cursor: pointer;">{{ getTeacherName(row.teacher_id) }}</span>
                      </template>
                      <div>
                        <div v-if="getTeacherContact(row.teacher_id)">
                          <div style="font-weight: bold; margin-bottom: 8px;">{{ t('schedules.contactPhone') }}</div>
                          <div>{{ getTeacherContact(row.teacher_id) }}</div>
                        </div>
                        <div v-if="getTeacherEmail(row.teacher_id)">
                          <div style="font-weight: bold; margin-bottom: 8px;">{{ t('schedules.email') }}</div>
                          <div>{{ getTeacherEmail(row.teacher_id) }}</div>
                        </div>
                        <div v-if="!getTeacherContact(row.teacher_id) && !getTeacherEmail(row.teacher_id)">{{ t('schedules.noContactInfo') }}</div>
                      </div>
                    </el-popover>
                  </template>
                </el-table-column>
                <el-table-column :label="t('schedules.class')" width="250" sortable prop="class">
                    <template #default="{ row }">
                        <el-popover placement="top" :width="300" trigger="hover">
                            <template #reference>
                                <span style="cursor: pointer;">{{ getClassName(row.class_id) }}</span>
                            </template>
                            <div>
                                <div v-if="getActiveClassStudents(row.class_id).length > 0">
                                    <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('schedules.activeStudents') }}</div>
                                    <div v-for="student in getActiveClassStudents(row.class_id)" :key="student.id" style="margin-bottom: 4px;">
                                        {{ student.name }}
                                    </div>
                                </div>
                                <div v-if="getInactiveClassStudents(row.class_id).length > 0">
                                    <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('schedules.inactiveStudents') }}</div>
                                    <div v-for="student in getInactiveClassStudents(row.class_id)" :key="student.id" style="margin-bottom: 4px;">
                                        {{ student.name }}
                                    </div>
                                </div>
                                <div v-if="getActiveClassStudents(row.class_id).length === 0 && getInactiveClassStudents(row.class_id).length === 0">
                                    {{ t('schedules.noStudent') }}
                                </div>
                            </div>
                        </el-popover>
                    </template>
                </el-table-column>
                <el-table-column :label="t('schedules.studentAttendance')" width="255">
                  <template #default="{ row }">
                    <div v-if="row.scheduled_students && row.scheduled_students.length > 0">
                      <div v-for="student in row.scheduled_students" :key="student.id" style="margin-bottom: 5px; display: flex; align-items: center; gap: 8px;">
                        <el-tooltip placement="top" effect="light" popper-class="student-info-tooltip">
                          <template #content>
                            <div class="student-detail-info">
                              <div class="info-item"><strong>{{ t('schedules.studentCodeLabel') }}</strong>{{ getStudentCode(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.studentNameLabel') }}</strong>{{ student.name }}</div>
                              <div class="info-item"><strong>{{ t('schedules.schoolLabel') }}</strong>{{ getStudentSchool(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.gradeLabel') }}</strong>{{ getStudentGrade(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.enrollmentDateLabel') }}</strong>{{ getStudentEnrollmentDate(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.contactLabel') }}</strong>{{ getStudentContactPerson(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.contactPhoneLabel') }}</strong>{{ getStudentContactPhone(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.emailLabel') }}</strong>{{ getStudentEmail(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.belongClassLabel') }}</strong>{{ getStudentClasses(student.id) }}</div>
                              <div class="info-item"><strong>{{ t('schedules.isActiveLabel') }}</strong>{{ getStudentIsActive(student.id) ? t('schedules.yes') : t('schedules.no') }}</div>
                            </div>
                          </template>
                          <span style="cursor: pointer; color: #409eff; flex: 1;">{{ student.name }}</span>
                        </el-tooltip>
                        <el-tag v-if="student.is_extra" type="warning" size="small" effect="dark">{{ t('schedules.extraStudent') }}</el-tag>
                        <el-tag 
                          :type="student.attendance_status === 'present' ? 'success' : student.attendance_status === 'leave' ? 'warning' : 'danger'"
                          size="small"
                        >
                          {{ student.attendance_status === 'present' ? t('schedules.present') : student.attendance_status === 'leave' ? t('schedules.onLeave') : t('schedules.absent') }}
                        </el-tag>
                      </div>
                    </div>
                    <div v-else-if="row.class_id" style="color: #909399;">
                      <div v-if="getActiveClassStudents(row.class_id).length > 0 || getInactiveClassStudents(row.class_id).length > 0">
                        <div style="margin-bottom: 5px; font-size: 12px;">{{ t('schedules.noAttendanceRecord') }}</div>
                        <div v-if="getActiveClassStudents(row.class_id).length > 0" style="margin-bottom: 3px;">
                          <span style="color: #67c23a;">{{ t('schedules.activeStudentsLabel') }}</span>
                          {{ getActiveClassStudents(row.class_id).map(s => s.name).join('、') }}
                        </div>
                        <div v-if="getInactiveClassStudents(row.class_id).length > 0">
                          <span style="color: #909399;">{{ t('schedules.inactiveStudentsLabel') }}</span>
                          {{ getInactiveClassStudents(row.class_id).map(s => s.name).join('、') }}
                        </div>
                      </div>
                      <div v-else>
                        {{ t('schedules.noStudentInClass') }}
                      </div>
                    </div>
                    <div v-else style="color: #909399;">
                      {{ t('schedules.noClassInfo') }}
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column :label="t('schedules.date')" width="120" sortable prop="start_date">
                  <template #default="{ row }">
                    {{ formatDate(row.start_date) }}
                  </template>
                </el-table-column>
                <!--
                <el-table-column :label="t('schedules.endDate')" width="120" sortable prop="end_date">
                  <template #default="{ row }">
                    {{ formatDate(row.end_date) }}
                  </template>
                </el-table-column>
                -->
                <el-table-column :label="t('schedules.dayOfWeek')" width="80" sortable>
                    <template #default="{ row }">
                        {{ getDayOfWeekFromDate(row.start_date) }}
                    </template>
                </el-table-column>
                <el-table-column :label="t('schedules.time')" width="150">
                  <template #default="{ row }">
                    {{ row.start_time }} - {{ row.end_time }}
                  </template>
                </el-table-column>
                <el-table-column :label="t('schedules.executionStatus')" width="150" sortable prop="execution_status">
                  <template #default="{ row }">
                    <el-popover placement="top" :width="400" trigger="hover">
                      <template #reference>
                        <el-tag v-if="row.execution_status === 'completed'" type="success" style="cursor: pointer;" @click="showEditFeedbackDialog(row, 'complete')">{{ t('schedules.completed') }}</el-tag>
                        <el-tag v-else-if="row.execution_status === 'postponed'" type="warning" style="cursor: pointer;" @click="showEditFeedbackDialog(row, 'postpone')">{{ t('schedules.postponed') }}</el-tag>
                        <el-tag v-else-if="row.execution_status === 'cancelled'" type="info" style="cursor: pointer;" @click="showEditFeedbackDialog(row, 'cancel')">{{ t('schedules.cancelSchedule') }}</el-tag>
                        <el-tag v-else style="cursor: pointer;">{{ t('schedules.pending') }}</el-tag>
                      </template>
                      <div v-if="row.execution_status === 'completed'">
                        <div v-if="row.content_feedback">
                          <div v-for="(line, index) in parseContentFeedback(row.content_feedback)" :key="index" style="margin-bottom: 8px;">
                            <strong>{{ line.label }}:</strong> {{ line.content }}
                          </div>
                        </div>
                        <div v-else>{{ t('schedules.noFeedback') }}</div>
                        
                        <el-divider v-if="row.scheduled_students && row.scheduled_students.length > 0" />
                        
                        <div v-if="row.scheduled_students && row.scheduled_students.length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px;">{{ t('schedules.studentAttendance') }}</div>
                          <div v-for="student in row.scheduled_students" :key="student.id" style="margin-bottom: 4px; display: flex; align-items: center;">
                            <span style="flex: 1;">{{ student.name }}</span>
                            <el-tag 
                              :type="student.attendance_status === 'present' ? 'success' : student.attendance_status === 'leave' ? 'warning' : 'danger'"
                              size="small"
                            >
                              {{ student.attendance_status === 'present' ? t('schedules.present') : student.attendance_status === 'leave' ? t('schedules.onLeave') : t('schedules.absent') }}
                            </el-tag>
                            <el-tag v-if="student.makeup_status === 'completed'" type="success" size="small" style="margin-left: 4px;">{{ t('schedules.makeupCompleted') }}</el-tag>
                            <el-tag v-else-if="student.makeup_status === 'declined'" type="info" size="small" style="margin-left: 4px;">{{ t('schedules.makeupDeclined') }}</el-tag>
                          </div>
                        </div>
                        <el-divider v-if="hasMakeupInfo(row)" />
                        <div v-if="hasMakeupInfo(row)">
                          <div style="font-weight: bold; margin-bottom: 8px;">{{ t('schedules.makeupInfo') }}</div>
                          <div v-for="student in row.scheduled_students.filter(s => s.makeup_status === 'completed' || s.makeup_status === 'declined')" :key="student.id" style="margin-bottom: 4px;">
                            <strong>{{ student.name }}:</strong>
                            <span v-if="student.makeup_status === 'completed'">{{ t('schedules.makeupCompleted') }} (ID: {{ student.makeup_schedule_id }})</span>
                            <span v-else-if="student.makeup_status === 'declined'">{{ t('schedules.makeupDeclined') }} ({{ t('schedules.reason') }}: {{ student.declined_reason }})</span>
                          </div>
                        </div>
                      </div>
                      <div v-else-if="row.execution_status === 'postponed'">
                        <div v-if="row.postpone_reason">
                          <strong>{{ t('schedules.postponeReason') }}</strong> {{ row.postpone_reason }}
                        </div>
                        <div v-else>{{ t('schedules.noPostponeReason') }}</div>
                      </div>
                      <div v-else-if="row.execution_status === 'cancelled'">
                        <div v-if="row.cancel_reason">
                          <strong>{{ t('schedules.cancelReason') }}</strong> {{ row.cancel_reason }}
                        </div>
                        <div v-else>{{ t('schedules.noCancelReason') }}</div>
                      </div>
                      <div v-else>
                        <strong>{{ t('schedules.statusLabel') }}</strong> {{ t('schedules.pending') }}
                      </div>
                    </el-popover>
                  </template>
                </el-table-column>
                <el-table-column :label="t('schedules.room')" width="180" sortable prop="room">
                  <template #default="{ row }">
                    <div v-if="row.room_type === 'offline_physical'">
                      <el-popover placement="top" :width="300" trigger="hover">
                        <template #reference>
                          <span style="cursor: pointer;">{{ getRoomName(row.room_id) }}</span>
                        </template>
                        <div>
                          <div v-if="getRoomLocation(row.room_id)">
                            <div style="font-weight: bold;">{{ t('schedules.location') }}</div>
                            <div>{{ getRoomLocation(row.room_id) }}</div>
                          </div>
                          <div v-if="getRoomCapacity(row.room_id)">
                            <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.capacity') }}</div>
                            <div>{{ getRoomCapacity(row.room_id) }}{{ t('schedules.peopleUnit') }}</div>
                          </div>
                          <div v-if="getRoomFacilities(row.room_id)">
                            <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.facilities') }}</div>
                            <div>{{ getRoomFacilities(row.room_id) }}</div>
                          </div>
                          <div v-if="!getRoomLocation(row.room_id) && !getRoomCapacity(row.room_id) && !getRoomFacilities(row.room_id)">
                            {{ t('schedules.noDetailInfo') }}
                          </div>
                        </div>
                      </el-popover>
                    </div>
                    <div v-else-if="row.room_type === 'online_virtual'">
                      <el-tooltip v-if="row.meeting_link" placement="top" :content="row.meeting_link">
                        <el-link type="primary" :href="row.meeting_link" target="_blank">
                          <el-icon><Link /></el-icon>
                          {{ t('schedules.clickToJoin') }}
                        </el-link>
                      </el-tooltip>
                      <span v-else style="color: #f56c6c;">{{ t('schedules.toBeAdded') }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column :label="t('schedules.conflictStatus')" width="120" sortable prop="has_conflict">
                    <template #default="{ row }">
                        <el-popover v-if="row.has_conflict" placement="top" :width="800" trigger="hover" @show="loadConflictSchedules(row)">
                            <template #reference>
                                <el-tag type="danger" style="cursor: pointer;">{{ t('schedules.conflict') }}</el-tag>
                            </template>
                            <div v-loading="conflictLoading">
                                <div v-if="popoverConflictSchedules.length > 0">
                                    <div style="margin-bottom: 8px; color: #f56c6c; font-weight: bold;">
                                        ⚠️ {{ t('schedules.conflictWithFollowing') }}
                                    </div>
                                    <el-table :data="popoverConflictSchedules" stripe style="width: 100%">
                                        <el-table-column prop="id" label="ID" width="80" />
                                        <el-table-column :label="t('schedules.course')" width="120">
                                            <template #default="{ row: conflictRow }">
                                                {{ getCourseName(conflictRow.course_id) }}
                                            </template>
                                        </el-table-column>
                                        <el-table-column :label="t('schedules.teacher')" width="120">
                                            <template #default="{ row: conflictRow }">
                                                {{ getTeacherName(conflictRow.teacher_id) }}
                                            </template>
                                        </el-table-column>
                                        <el-table-column :label="t('schedules.class')" width="120">
                                            <template #default="{ row: conflictRow }">
                                                {{ getClassName(conflictRow.class_id) }}
                                            </template>
                                        </el-table-column>
                                        <el-table-column :label="t('schedules.room')" width="120">
                                            <template #default="{ row: conflictRow }">
                                                {{ getRoomName(conflictRow.room_id) }}
                                            </template>
                                        </el-table-column>
                                        <el-table-column :label="t('schedules.time')" width="160">
                                            <template #default="{ row: conflictRow }">
                                                {{ formatDate(conflictRow.start_date) }} {{ conflictRow.start_time }}-{{ conflictRow.end_time }}
                                            </template>
                                        </el-table-column>
                                        <el-table-column :label="t('schedules.conflictReason')" min-width="200">
                                            <template #default="{ row: conflictRow }">
                                                <el-tag v-if="conflictRow.conflict_type === 'teacher'" type="warning" size="small">{{ t('schedules.teacherConflict') }}</el-tag>
                                                <el-tag v-if="conflictRow.conflict_type === 'room'" type="danger" size="small">{{ t('schedules.roomConflict') }}</el-tag>
                                                <el-tag v-if="conflictRow.conflict_type === 'class'" type="info" size="small">{{ t('schedules.classConflict') }}</el-tag>
                                                <span style="color: #f56c6c; font-size: 12px; margin-left: 4px;">{{ conflictRow.conflict_detail }}</span>
                                            </template>
                                        </el-table-column>
                                    </el-table>
                                </div>
                                <div v-else>{{ t('schedules.noConflictCourse') }}</div>
                            </div>
                        </el-popover>
                        <el-tag v-else type="success">{{ t('schedules.noConflict') }}</el-tag>
                    </template>
                </el-table-column>
                
                <el-table-column v-if="!isScreenshotting" :label="t('common.operation')" width="150" fixed="right">
                  <template #default="{ row }">
                    <div style="display: flex; gap: 3px; flex-wrap: wrap;">
                      <el-button v-if="canEditSchedule(row)" size="small" @click="showEditDialog(row)">{{ t('schedules.edit') }}</el-button>
                      <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" size="small" type="primary" @click="showCopyDialog(row)">{{ t('schedules.copy') }}</el-button>
                      <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" size="small" type="success" @click="showCompleteDialog(row)" :disabled="row.has_conflict || row.execution_status !== 'pending'">{{ t('schedules.completed') }}</el-button>
                      <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" size="small" type="warning" @click="showPostponeDialog(row)" :disabled="row.has_conflict || row.execution_status !== 'pending'">{{ t('schedules.postponed') }}</el-button>
                      <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" size="small" type="info" @click="showExtraStudentDialog(row)" :disabled="row.execution_status !== 'pending'">{{ t('schedules.extraStudent') }}</el-button>
                      <el-button size="small" type="success" @click="showHomeworkDialog(row)" :disabled="row.execution_status !== 'completed'">{{ t('schedules.homeworkNotify') }}</el-button>
                      <el-button size="small" type="primary" @click="showWordCheckDialog(row)" :disabled="row.execution_status !== 'completed'">{{ t('schedules.wordCheck') }}</el-button>
                      <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" size="small" type="primary" @click="showMakeupDialog(row)" :disabled="row.execution_status !== 'completed' || !hasStudentsNeedingMakeup(row)">{{ t('schedules.studentMakeup') }}</el-button>
                      <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" size="small" type="info" @click="showCancelDialog(row)" :disabled="row.has_conflict || row.execution_status !== 'pending'">{{ t('schedules.cancelSchedule') }}</el-button>
                      <el-button size="small" type="warning" @click="handleNotifyNow(row)">{{ t('schedules.notifyNow') }}</el-button>
                      <el-button v-if="canDeleteSchedule(row)" size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[15, 25, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
            style="margin-top: 20px; justify-content: center; display: flex;"
          />
        </el-tab-pane>

        <el-tab-pane :label="t('schedules.conflictCourses')" name="conflicts">
          <el-table :data="conflictSchedules" stripe v-loading="loading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column :label="t('schedules.course')" width="120">
              <template #default="{ row }">
                {{ getCourseName(row.course_id) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('schedules.teacher')" width="120">
              <template #default="{ row }">
                {{ getTeacherName(row.teacher_id) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('schedules.class')" width="120">
                <template #default="{ row }">
                    {{ getClassName(row.class_id) }}
                </template>
            </el-table-column>

            <el-table-column :label="t('schedules.room')" width="120">
              <template #default="{ row }">
                {{ getRoomName(row.room_id) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('schedules.dayOfWeek')" width="80">
                <template #default="{ row }">
                    {{ getDayOfWeekFromDate(row.start_date) }}
                </template>
            </el-table-column>
            <el-table-column :label="t('schedules.time')" width="160">
              <template #default="{ row }">
                {{ row.start_time }} - {{ row.end_time }}
              </template>
            </el-table-column>
            <el-table-column :label="t('schedules.conflictReason')" min-width="300">
              <template #default="{ row }">
                <span style="color: #f56c6c;">{{ row.conflict_reason }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.operation')" width="135" fixed="right">
              <template #default="{ row }">
                <el-button v-if="canEditSchedule(row)" size="small" @click="showEditDialog(row)">{{ t('schedules.edit') }}</el-button>
                <el-button v-if="canDeleteSchedule(row)" size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <!-- 手动排课对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable destroy-on-close>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item :label="t('schedules.course')" prop="course_id">
          <el-select v-model="form.course_id" filterable :placeholder="t('schedules.selectCourse')" style="width: 100%">
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('schedules.course') }}：</strong>{{ course.name }}</div>
                    <div v-if="course.code"><strong>{{ t('schedules.code') }}：</strong>{{ course.code }}</div>
                    <div v-if="getCourseTeachers(course.id).length > 0">
                      <div style="font-weight: bold; margin-top: 8px; margin-bottom: 4px;">{{ t('schedules.teachingTeacher') }}：</div>
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
                    <div v-else style="margin-top: 8px; color: #909399;">{{ t('schedules.noTeacher') }}</div>
                  </div>
                </template>
                <span>{{ course.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.courseType')" prop="schedule_type">
          <el-radio-group v-model="form.schedule_type">
            <el-radio value="formal">{{ t('schedules.formalClass') }}</el-radio>
            <el-radio value="trial">{{ t('schedules.trialClass') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('schedules.teacher')" prop="teacher_id">
          <el-select v-model="form.teacher_id" filterable :placeholder="t('schedules.selectTeacher')" style="width: 100%">
            <el-option
                v-for="teacher in availableTeachers"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('schedules.teacherLabel') }}：</strong>{{ teacher.name }}</div>
                    <div v-if="teacher.code"><strong>{{ t('schedules.code') }}：</strong>{{ teacher.code }}</div>
                    <div v-if="teacher.department"><strong>{{ t('schedules.department') }}：</strong>{{ teacher.department }}</div>
                    <div v-if="teacher.contact_phone">
                      <div style="margin-top: 8px;"><strong>{{ t('schedules.contactPhone') }}：</strong></div>
                      <div>{{ teacher.contact_phone }}</div>
                    </div>
                    <div v-if="teacher.email">
                      <div style="margin-top: 8px;"><strong>{{ t('schedules.email') }}：</strong></div>
                      <div>{{ teacher.email }}</div>
                    </div>
                    <div v-if="!teacher.contact_phone && !teacher.email" style="margin-top: 8px; color: #909399;">
                      {{ t('schedules.noContactInfo') }}
                    </div>
                  </div>
                </template>
                <span>{{ teacher.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.class')" prop="class_id">
            <el-select v-model="form.class_id" filterable :placeholder="t('schedules.selectClass')" style="width: 100%">
                <el-option
                v-for="class_ in classes"
                :key="class_.id"
                :label="class_.name"
                :value="class_.id"
                >
                <el-tooltip placement="right" :show-after="200">
                    <template #content>
                        <div v-if="getActiveClassStudents(class_.id).length > 0">
                            <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('schedules.activeStudentsLabel') }}</div>
                            <div v-for="student in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                                {{ student.name }}
                            </div>
                        </div>
                        <div v-if="getInactiveClassStudents(class_.id).length > 0">
                            <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('schedules.inactiveStudentsLabel') }}</div>
                            <div v-for="student in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                                {{ student.name }}
                            </div>
                        </div>
                        <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                            {{ t('schedules.noStudent') }}
                        </div>
                    </template>
                    <span>{{ class_.name }}</span>
                </el-tooltip>
                </el-option>
            </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.roomType')" prop="room_type">
          <el-select v-model="form.room_type" :placeholder="t('schedules.selectRoomType')" style="width: 100%" @change="handleRoomTypeChange">
            <el-option :label="t('schedules.offlinePhysical')" value="offline_physical" />
            <el-option :label="t('schedules.onlineVirtual')" value="online_virtual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.room_type === 'offline_physical'" :label="t('schedules.room')" prop="room_id">
          <el-select v-model="form.room_id" filterable :placeholder="t('schedules.selectRoom')" style="width: 100%">
            <el-option
                v-for="room in rooms"
                :key="room.id"
                :label="room.name"
                :value="room.id"
              >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div v-if="room.location">
                    <div style="font-weight: bold;">{{ t('schedules.location') }}:</div>
                    <div>{{ room.location }}</div>
                  </div>
                  <div v-if="room.capacity">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.capacity') }}:</div>
                    <div>{{ room.capacity }}{{ t('schedules.peopleUnit') }}</div>
                  </div>
                  <div v-if="room.facilities">
                    <div style="font-weight: bold; margin-top: 8px;">{{ t('schedules.facilities') }}:</div>
                    <div>{{ room.facilities }}</div>
                  </div>
                  <div v-if="!room.location && !room.capacity && !room.facilities">
                    {{ t('schedules.noDetailInfo') }}
                  </div>
                </template>
                <span>{{ room.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item v-else :label="t('schedules.meetingLink')" prop="meeting_link">
          <el-input v-model="form.meeting_link" :placeholder="t('schedules.meetingLinkPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('schedules.startTime')" prop="start_time">
          <el-time-picker
            v-model="startTime"
            format="HH:mm"
            value-format="HH:mm"
            :placeholder="t('schedules.selectStartTime')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.endTime')" prop="end_time">
          <el-time-picker
            v-model="endTime"
            format="HH:mm"
            value-format="HH:mm"
            :placeholder="t('schedules.selectEndTime')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.startDate')" prop="start_date">
            <el-date-picker
                v-model="form.start_date"
                type="date"
                :placeholder="t('schedules.selectStartDate')"
                value-format="YYYY-MM-DD"
                    style="width: 100%"
            />
        </el-form-item>
        <el-form-item :label="t('schedules.endDate')" prop="end_date">
            <el-date-picker
                v-model="form.end_date"
                type="date"
                :placeholder="t('schedules.selectEndDate')"
                value-format="YYYY-MM-DD"
                    style="width: 100%"
            />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button @click="handleSubmit(false)">{{ t('schedules.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="handleSubmit(true)">{{ t('schedules.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>

    <!-- 智能算法排课对话框 -->
    <el-dialog v-model="autoScheduleDialogVisible" :title="t('schedules.smartScheduling')" width="500px" draggable>
      <el-form :model="autoScheduleForm" :rules="autoScheduleRules" ref="autoScheduleFormRef" label-width="120px">
        <el-form-item :label="t('schedules.scheduleAlgorithm')" prop="algorithm">
          <el-select v-model="autoScheduleForm.algorithm" :placeholder="t('schedules.selectAlgorithm')" style="width: 100%">
            <el-option :label="t('schedules.hybridAlgorithm')" value="hybrid" />
            <el-option :label="t('schedules.geneticAlgorithm')" value="genetic" />
            <el-option :label="t('schedules.backtrackingAlgorithm')" value="backtracking" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.specifyClass')" prop="classIds">
          <el-select 
            v-model="autoScheduleForm.classIds" 
            :placeholder="t('schedules.selectClassPlaceholder')" 
            clearable 
            multiple 
            collapse-tags 
            collapse-tags-tooltip
            style="width: 100%"
          >
            <el-option
              v-for="class_ in classes"
              :key="class_.id"
              :label="class_.name"
              :value="class_.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div v-if="getActiveClassStudents(class_.id).length > 0">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">📚 {{ t('schedules.activeStudentsLabel') }}</div>
                    <div v-for="(student, index) in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ index + 1 }}. {{ student.name }} ({{ student.code }})
                      <div v-if="student.contact_phone" style="font-size: 12px; color: #909399; margin-top: 2px;">
                        📱 {{ student.contact_phone }}
                      </div>
                    </div>
                  </div>
                  <div v-if="getInactiveClassStudents(class_.id).length > 0" style="margin-top: 8px;">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #909399;">{{ t('schedules.inactiveStudentsLabel') }}</div>
                    <div v-for="(student, index) in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                      {{ index + 1 }}. {{ student.name }} ({{ student.code }})
                    </div>
                  </div>
                  <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                    {{ t('schedules.noStudent') }}
                  </div>
                </template>
                <span>{{ class_.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
          <div style="margin-top: 5px; font-size: 12px; color: #909399;">
            <el-icon><InfoFilled /></el-icon> {{ t('schedules.selectClassTip') }}
          </div>
        </el-form-item>
        <el-form-item :label="t('schedules.roomType')" prop="room_type">
          <el-select v-model="autoScheduleForm.room_type" :placeholder="t('schedules.selectRoomType')" style="width: 100%">
            <el-option :label="t('schedules.offlinePhysical')" value="offline_physical" />
            <el-option :label="t('schedules.onlineVirtual')" value="online_virtual" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.startDate')" prop="start_date">
            <el-date-picker
                v-model="autoScheduleForm.start_date"
                type="date"
                :placeholder="t('schedules.selectStartDate')"
                value-format="YYYY-MM-DD"
                style="width: 100%"
            />
            </el-form-item>
            <el-form-item :label="t('schedules.endDate')" prop="end_date">
            <el-date-picker
                v-model="autoScheduleForm.end_date"
                type="date"
                :placeholder="t('schedules.selectEndDate')"
                value-format="YYYY-MM-DD"
                style="width: 100%"
            />
        </el-form-item>
      </el-form>
      <el-alert
        :title="t('schedules.autoScheduleWarning')"
        type="warning"
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-alert
        :title="t('schedules.algorithmDescription')"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />
      <template #footer>
        <el-button @click="autoScheduleDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAutoSchedule" :loading="autoScheduleLoading">{{ t('schedules.startScheduling') }}</el-button>
      </template>
    </el-dialog>

    <!-- 智能算法排课预览对话框 -->
    <el-dialog v-model="previewDialogVisible" :title="t('schedules.smartSchedulingPreview')" width="90%" top="5vh" draggable>
      <el-alert
        :title="t('schedules.previewSelectTip')"
        type="warning"
        :closable="false"
        style="margin-bottom: 20px"
      />
      
      <!-- 视图切换 -->
      <el-card class="view-switch-card" style="margin-bottom: 20px;">
        <el-radio-group v-model="previewViewType" @change="handlePreviewViewTypeChange">
          <el-radio-button value="table">{{ t('schedules.tableView') }}</el-radio-button>
          <el-radio-button value="calendar">{{ t('schedules.calendarView') }}</el-radio-button>
        </el-radio-group>
        <span style="margin-left: 20px; color: #606266;">
          {{ t('schedules.selected') }}: {{ selectedPreviewSchedules.length }} / {{ previewSchedules.length }}
        </span>
      </el-card>
      
      <!-- 表格视图 -->
      <div v-if="previewViewType === 'table'">
        <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
          <el-checkbox v-model="selectAll" @change="handleSelectAll">{{ t('schedules.selectAll') }}</el-checkbox>
          <el-button type="danger" @click="handleSelectConflicts">{{ t('schedules.selectConflictsOnly') }}</el-button>
          <el-button type="success" @click="handleSelectNoConflicts">{{ t('schedules.selectNoConflictsOnly') }}</el-button>
        </div>
        <el-table
          :data="previewSchedules"
          stripe
          v-loading="previewLoading"
          style="margin-top: 20px"
          @selection-change="handlePreviewSelectionChange"
          max-height="500px"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="course_name" :label="t('schedules.course')" width="240" />
          <el-table-column prop="teacher_name" :label="t('schedules.teacher')" width="100">
            <template #default="{ row }">
              <el-tooltip placement="top" effect="light" v-if="row.teacher_phone || row.teacher_email">
                <template #content>
                  <div v-if="row.teacher_phone"><strong>{{ t('schedules.contactPhone') }}：</strong>{{ row.teacher_phone }}</div>
                  <div v-if="row.teacher_email"><strong>{{ t('schedules.email') }}：</strong>{{ row.teacher_email }}</div>
                </template>
                <span style="cursor: help; color: #409EFF;">{{ row.teacher_name }}</span>
              </el-tooltip>
              <span v-else>{{ row.teacher_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="class_name" :label="t('schedules.class')" width="240">
            <template #default="{ row }">
              <el-tooltip placement="top" effect="light" v-if="row.class_students && row.class_students.length > 0">
                <template #content>
                  <div><strong>{{ t('schedules.studentList') }}：</strong></div>
                  <div v-for="(student, index) in row.class_students" :key="index" style="margin-top: 5px;">
                    <div>{{ index + 1 }}. {{ student.name }} ({{ student.code }})</div>
                    <div v-if="student.phone">{{ t('schedules.contactPhone') }}：{{ student.phone }}</div>
                    <div v-if="student.parent_phone">{{ t('schedules.parentPhone') }}：{{ student.parent_phone }}</div>
                  </div>
                </template>
                <span style="cursor: help; color: #409EFF;">{{ row.class_name }}</span>
              </el-tooltip>
              <span v-else>{{ row.class_name }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('schedules.roomOrMeetingLink')" width="200">
            <template #default="{ row }">
              <div v-if="row.room_type === 'offline_physical'">
                <el-tooltip placement="top" effect="light" v-if="row.room_location || row.room_capacity || row.room_facilities">
                  <template #content>
                    <div v-if="row.room_location"><strong>{{ t('schedules.location') }}：</strong>{{ row.room_location }}</div>
                    <div v-if="row.room_capacity"><strong>{{ t('schedules.capacity') }}：</strong>{{ row.room_capacity }}{{ t('schedules.peopleUnit') }}</div>
                    <div v-if="row.room_facilities"><strong>{{ t('schedules.facilities') }}：</strong>{{ row.room_facilities }}</div>
                  </template>
                  <span style="cursor: help; color: #409EFF;">{{ row.room_name }}</span>
                </el-tooltip>
                <span v-else>{{ row.room_name }}</span>
              </div>
              <div v-else-if="row.room_type === 'online_virtual'">
                <el-tooltip v-if="row.meeting_link" placement="top" :content="row.meeting_link">
                  <el-link type="primary" :href="row.meeting_link" target="_blank">
                    <el-icon><Link /></el-icon>
                    {{ row.meeting_link.substring(0, 20) }}...
                  </el-link>
                </el-tooltip>
                <span v-else style="color: #f56c6c;">{{ t('schedules.toBeAdded') }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="t('schedules.date')" width="120">
            <template #default="{ row }">
              {{ formatDate(row.start_date) }}
            </template>
          </el-table-column>
          <el-table-column :label="t('schedules.time')" width="100">
            <template #default="{ row }">
              {{ row.start_time }}-{{ row.end_time }}
            </template>
          </el-table-column>
          <el-table-column :label="t('schedules.dayOfWeek')" width="80">
            <template #default="{ row }">
              {{ getDayOfWeekName(row.day_of_week) }}
            </template>
          </el-table-column>
          <el-table-column :label="t('schedules.conflictStatus')" width="100">
            <template #default="{ row }">
              <el-tag :type="row.has_conflict ? 'danger' : 'success'">
                {{ row.has_conflict ? t('schedules.hasConflict') : t('schedules.noConflict') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="conflict_reason" :label="t('schedules.conflictReason')" min-width="200" show-overflow-tooltip />
          <el-table-column :label="t('common.operation')" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" plain @click="handleEditPreviewSchedule(row)">
                {{ t('schedules.edit') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 日历视图 -->
      <div v-else-if="previewViewType === 'calendar'" v-loading="previewLoading">
        <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
          <el-checkbox v-model="selectAllCalendar" @change="handleSelectAllCalendar">{{ t('schedules.selectAll') }}</el-checkbox>
          <el-button type="danger" @click="handleSelectConflictsCalendar">{{ t('schedules.selectConflictsOnly') }}</el-button>
          <el-button type="success" @click="handleSelectNoConflictsCalendar">{{ t('schedules.selectNoConflictsOnly') }}</el-button>
          <el-button @click="handleClearSelectionCalendar">{{ t('schedules.clearSelection') }}</el-button>
        </div>
        
        <div class="preview-calendar-container">
          <div class="time-column">
            <div class="time-header">{{ t('schedules.time') }}</div>
            <div v-for="time in previewTimeSlots" :key="time" class="time-cell">
              {{ time }}
            </div>
          </div>
          
          <div class="dates-column">
            <div class="date-header-row">
              <div v-for="date in previewDisplayDates" :key="date.dateStr" class="date-header">
                <div class="date-name">{{ date.dayName }}</div>
                <div class="date-num" :class="{ 'is-today': date.isToday }">{{ date.dateNum }}</div>
              </div>
            </div>
            
            <div v-for="time in previewTimeSlots" :key="time" class="time-row">
              <div v-for="date in previewDisplayDates" :key="`${date.dateStr}-${time}`" class="schedule-cell">
                <el-tooltip 
                  v-for="schedule in getPreviewSchedulesForSlot(date, time)"
                  :key="schedule.temp_id"
                  placement="top"
                  effect="light"
                  :disabled="!schedule.class_students || schedule.class_students.length === 0"
                >
                  <template #content>
                    <div v-if="schedule.class_students && schedule.class_students.length > 0">
                      <div style="font-weight: bold; margin-bottom: 8px;">📚 {{ t('schedules.classStudentList') }}：</div>
                      <div v-for="(student, index) in schedule.class_students" :key="index" style="margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px solid #eee;">
                        <div style="font-weight: 500;">{{ index + 1 }}. {{ student.name }} ({{ student.code }})</div>
                        <div v-if="student.phone" style="font-size: 12px; color: #606266; margin-top: 2px;">
                          📱 {{ student.phone }}
                        </div>
                        <div v-if="student.parent_phone" style="font-size: 12px; color: #606266; margin-top: 2px;">
                          👨‍👩‍👧 {{ t('schedules.parentPhone') }}：{{ student.parent_phone }}
                        </div>
                      </div>
                    </div>
                  </template>
                  <div
                    class="preview-schedule-item"
                    :class="{
                      'has-conflict': schedule.has_conflict,
                      'is-selected': isPreviewScheduleSelected(schedule)
                    }"
                    @click="togglePreviewScheduleSelection(schedule)"
                  >
                    <div class="schedule-checkbox">
                      <el-checkbox 
                        :model-value="isPreviewScheduleSelected(schedule)"
                        @click.stop
                        @change="togglePreviewScheduleSelection(schedule)"
                      />
                    </div>
                    <div class="schedule-title">{{ schedule.course_name }}</div>
                    <div class="schedule-info">{{ t('schedules.teacher') }}:{{ schedule.teacher_name }}@{{ t('schedules.location') }}:{{ schedule.room_name }}</div>
                    <div class="schedule-info">{{ t('schedules.class') }}:{{ schedule.class_name }}  </div>
                    <div class="schedule-info"></div>
                    <div class="schedule-time">{{ schedule.start_time }}-{{ schedule.end_time }}</div>
                    <div v-if="schedule.has_conflict" class="conflict-badge">
                      <el-icon><Warning /></el-icon>
                    </div>
                    <div class="schedule-edit-btn" @click.stop="handleEditPreviewSchedule(schedule)">
                      <el-button type="primary" size="small" plain>{{ t('common.edit') }}</el-button>
                    </div>
                  </div>
                </el-tooltip>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="previewDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveSelectedSchedules" :loading="saveLoading" :disabled="selectedPreviewSchedules.length === 0">
          {{ t('schedules.saveSelectedSchedules') }} ({{ selectedPreviewSchedules.length }})
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 预览排课编辑对话框 -->
    <el-dialog v-model="previewEditDialogVisible" :title="t('schedules.editPreviewSchedule')" width="600px" draggable destroy-on-close>
      <el-form :model="previewEditForm" :rules="previewEditRules" ref="previewEditFormRef" label-width="120px">
        <el-form-item :label="t('schedules.course')" prop="course_id">
          <el-select v-model="previewEditForm.course_id" filterable :placeholder="t('schedules.selectCourse')" style="width: 100%">
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.teacher')" prop="teacher_id">
          <el-select v-model="previewEditForm.teacher_id" filterable :placeholder="t('schedules.selectTeacher')" style="width: 100%">
            <el-option
              v-for="teacher in previewEditAvailableTeachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.class')" prop="class_id">
          <el-select v-model="previewEditForm.class_id" filterable :placeholder="t('schedules.selectClass')" style="width: 100%">
            <el-option
              v-for="class_ in classes"
              :key="class_.id"
              :label="class_.name"
              :value="class_.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('schedules.roomType')" prop="room_type">
          <el-select v-model="previewEditForm.room_type" :placeholder="t('schedules.selectRoomType')" style="width: 100%" @change="handlePreviewEditRoomTypeChange">
            <el-option :label="t('schedules.offlinePhysical')" value="offline_physical" />
            <el-option :label="t('schedules.onlineVirtual')" value="online_virtual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="previewEditForm.room_type === 'offline_physical'" :label="t('schedules.room')" prop="room_id">
          <el-select v-model="previewEditForm.room_id" filterable :placeholder="t('schedules.selectRoom')" style="width: 100%">
            <el-option
              v-for="room in rooms"
              :key="room.id"
              :label="room.name"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-else :label="t('schedules.meetingLink')" prop="meeting_link">
          <el-input v-model="previewEditForm.meeting_link" :placeholder="t('schedules.meetingLinkPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('schedules.startTime')" prop="start_time">
          <el-time-picker
            v-model="previewEditStartTime"
            format="HH:mm"
            value-format="HH:mm"
            :placeholder="t('schedules.selectStartTime')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.endTime')" prop="end_time">
          <el-time-picker
            v-model="previewEditEndTime"
            format="HH:mm"
            value-format="HH:mm"
            :placeholder="t('schedules.selectEndTime')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.startDate')" prop="start_date">
            <el-date-picker
                v-model="previewEditForm.start_date"
                type="date"
                :placeholder="t('schedules.selectStartDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.endDate')" prop="end_date">
            <el-date-picker
                v-model="previewEditForm.end_date"
                type="date"
                :placeholder="t('schedules.selectEndDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="previewEditDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handlePreviewEditConfirm" :loading="previewEditLoading">{{ t('schedules.confirmEdit') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" :title="t('schedules.importSchedule')" width="500px" draggable>
      <el-alert
        :title="t('schedules.importInstructions')"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <p>{{ t('schedules.importStep1') }}</p>
        <p>{{ t('schedules.importStep2') }}</p>
        <p>{{ t('schedules.importStep3') }}</p>
        <p>{{ t('schedules.importStep4') }}</p>
        <p>{{ t('schedules.importStep5') }}</p>
        <p>{{ t('schedules.importStep6') }}</p>
      </el-alert>
      
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".xlsx,.xls"
      >
        <el-button type="primary">{{ t('schedules.selectFile') }}</el-button>
        <template #tip>
          <div class="el-upload__tip">{{ t('schedules.excelOnly') }}</div>
        </template>
      </el-upload>
      
      <template #footer>
        <el-button @click="importDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleImport" :loading="importUploading">
          {{ t('schedules.importButton') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 完训对话框 -->
    <el-dialog v-model="completeDialogVisible" :title="t('schedules.completeFeedback')" width="800px" draggable>
      <el-alert
        v-if="currentCompleteSchedule && currentCompleteSchedule.schedule_type === 'trial'"
        :title="t('schedules.trialNoFeedback')"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-alert
        v-else-if="currentCompleteSchedule && teachers.find(t => t.id === currentCompleteSchedule.teacher_id)?.no_feedback_required"
        :title="t('schedules.noFeedbackRequired')"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="completeForm" :rules="completeRules" ref="completeFormRef" label-width="80px">
        <el-form-item :label="t('schedules.content')" prop="content">
          <el-input v-model="completeForm.content" type="textarea" :rows="3" :placeholder="t('schedules.inputCourseContent')" />
        </el-form-item>
        <el-form-item :label="t('schedules.homework')" prop="homework">
          <el-input v-model="completeForm.homework" type="textarea" :rows="3" :placeholder="t('schedules.inputHomeworkContent')" />
        </el-form-item>
        <el-form-item :label="t('schedules.note')" prop="note">
          <el-input v-model="completeForm.note" type="textarea" :rows="3" :placeholder="t('schedules.inputNoteContent')" />
        </el-form-item>
        
        <el-divider>{{ t('schedules.studentAttendanceStatus') }}</el-divider>
        <el-table :data="completeForm.studentAttendance" border max-height="300">
          <el-table-column prop="name" :label="t('schedules.studentName')" width="150" />
          <el-table-column :label="t('schedules.attendanceStatus')" width="200">
            <template #default="{ row }">
              <el-radio-group v-model="row.status" :disabled="row.isLocked">
                <el-radio value="present">{{ t('schedules.present') }}</el-radio>
                <el-radio value="absent">{{ t('schedules.absent') }}</el-radio>
                <el-radio value="leave">{{ t('schedules.leave') }}</el-radio>
              </el-radio-group>
              <el-tag v-if="row.isLocked" type="info" size="small" style="margin-left: 8px;">{{ t('schedules.locked') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('schedules.absenceReason')">
            <template #default="{ row }">
              <el-input 
                v-if="row.status !== 'present'" 
                v-model="row.absenceReason" 
                :disabled="row.isLocked"
                :placeholder="t('schedules.inputAbsenceReason')"
                size="small"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="completeDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button @click="handleComplete(false)">{{ t('schedules.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="handleComplete(true)">{{ t('schedules.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- 修改反馈对话框 -->
    <el-dialog v-model="editFeedbackDialogVisible" :title="editFeedbackDialogTitle" width="600px" draggable>
      <el-alert
        v-if="currentEditFeedbackSchedule && teachers.find(t => t.id === currentEditFeedbackSchedule.teacher_id)?.no_feedback_required && editFeedbackType === 'complete'"
        :title="t('schedules.noFeedbackRequired')"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="editFeedbackForm" :rules="editFeedbackRules" ref="editFeedbackFormRef" label-width="100px">
        <template v-if="editFeedbackType === 'complete'">
          <el-form-item :label="t('schedules.content')" prop="content">
            <el-input v-model="editFeedbackForm.content" type="textarea" :rows="3" :placeholder="t('schedules.inputCourseContent')" />
          </el-form-item>
          <el-form-item :label="t('schedules.homework')" prop="homework">
            <el-input v-model="editFeedbackForm.homework" type="textarea" :rows="3" :placeholder="t('schedules.inputHomeworkContent')" />
          </el-form-item>
          <el-form-item :label="t('schedules.note')" prop="note">
            <el-input v-model="editFeedbackForm.note" type="textarea" :rows="3" :placeholder="t('schedules.inputNoteContent')" />
          </el-form-item>
          
          <el-divider>{{ t('schedules.studentAttendanceStatus') }}</el-divider>
          <el-table :data="editFeedbackForm.studentAttendance" border max-height="300">
            <el-table-column prop="name" :label="t('schedules.studentName')" width="150" />
            <el-table-column :label="t('schedules.attendanceStatus')" width="200">
              <template #default="{ row }">
                <el-radio-group v-model="row.status">
                  <el-radio value="present">{{ t('schedules.present') }}</el-radio>
                  <el-radio value="absent">{{ t('schedules.absent') }}</el-radio>
                  <el-radio value="leave">{{ t('schedules.leave') }}</el-radio>
                </el-radio-group>
              </template>
            </el-table-column>
            <el-table-column :label="t('schedules.absenceReason')">
              <template #default="{ row }">
                <el-input 
                  v-if="row.status !== 'present'" 
                  v-model="row.absenceReason" 
                  :placeholder="t('schedules.inputAbsenceReason')"
                  size="small"
                />
              </template>
            </el-table-column>
          </el-table>
        </template>
        <template v-if="editFeedbackType === 'postpone'">
          <el-form-item :label="t('schedules.postponeReason')" prop="postpone_reason">
            <el-input v-model="editFeedbackForm.postpone_reason" type="textarea" :rows="5" :placeholder="t('schedules.inputPostponeReason')" />
          </el-form-item>
        </template>
        <template v-if="editFeedbackType === 'cancel'">
          <el-form-item :label="t('schedules.cancelReasonLabel')" prop="cancel_reason">
            <el-input v-model="editFeedbackForm.cancel_reason" type="textarea" :rows="5" :placeholder="t('schedules.inputCancelReason')" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="editFeedbackDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleEditFeedback">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 延期课程安排对话框 -->
    <el-dialog v-model="postponeDialogVisible" :title="t('schedules.adjustDateTime')" width="600px" draggable>
      <el-form :model="postponeForm" :rules="postponeRules" ref="postponeFormRef" label-width="100px">
        <el-form-item :label="t('schedules.startDate')" prop="startDate">
          <el-date-picker
            v-model="postponeForm.startDate"
            type="date"
            :placeholder="t('schedules.selectStartDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.endDate')" prop="endDate">
          <el-date-picker
            v-model="postponeForm.endDate"
            type="date"
            :placeholder="t('schedules.selectEndDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.startTime')" prop="startTime">
          <el-time-picker
            v-model="postponeForm.startTime"
            :placeholder="t('schedules.selectStartTime')"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.endTime')" prop="endTime">
          <el-time-picker
            v-model="postponeForm.endTime"
            :placeholder="t('schedules.selectEndTime')"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.postponeReason')" prop="postponeReason">
          <el-input
            v-model="postponeForm.postponeReason"
            type="textarea"
            :rows="4"
            :placeholder="t('schedules.inputPostponeReason')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="postponeDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button @click="handlePostpone(false)">{{ t('schedules.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="handlePostpone(true)">{{ t('schedules.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 取消课程安排对话框 -->
    <el-dialog v-model="cancelDialogVisible" :title="t('schedules.confirmCancelTitle')" width="500px" draggable>
      <el-form :model="cancelForm" :rules="cancelRules" ref="cancelFormRef" label-width="100px">
        <el-form-item :label="t('schedules.cancelReasonLabel')" prop="cancelReason">
          <el-input
            v-model="cancelForm.cancelReason"
            type="textarea"
            :rows="4"
            :placeholder="t('schedules.inputCancelReason')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button @click="handleCancel(false)">{{ t('schedules.saveAndScheduleNotify') }}</el-button>
        <el-button type="danger" @click="handleCancel(true)">{{ t('schedules.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>
    <!-- 学员补课对话框 -->
    <el-dialog v-model="makeupDialogVisible" :title="t('schedules.studentMakeup')" width="600px" draggable>
      <el-form :model="makeupForm" :rules="makeupRules" ref="makeupFormRef" label-width="100px">
        <el-form-item :label="t('schedules.makeupOptions')">
          <el-radio-group v-model="makeupForm.makeupType">
            <el-radio value="makeup">{{ t('schedules.makeup') }}</el-radio>
            <el-radio value="decline">{{ t('schedules.declineMakeup') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item :label="t('schedules.selectStudents')" prop="studentIds">
          <el-select 
            v-model="makeupForm.studentIds" 
            :placeholder="t('schedules.selectStudentPlaceholder')" 
            multiple 
            collapse-tags 
            collapse-tags-tooltip 
            style="width: 100%"
          >
            <el-option
              v-for="student in classStudents"
              :key="student.id"
              :label="`${student.name} (${student.attendance_status === 'absent' ? t('schedules.absent') : t('schedules.onLeave')})`"
              :value="student.id"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ student.name }}</span>
                <el-tag 
                  :type="student.attendance_status === 'absent' ? 'danger' : 'warning'" 
                  size="small"
                >
                  {{ student.attendance_status === 'absent' ? t('schedules.absent') : t('schedules.onLeave') }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div v-if="classStudents.length > 0" style="margin-top: 8px; font-size: 12px; color: #909399;">
            {{ t('schedules.studentsNeedMakeup', { count: classStudents.length }) }}
          </div>
        </el-form-item>
        
        <template v-if="makeupForm.makeupType === 'makeup'">
          <el-form-item :label="t('schedules.startDate')" prop="startDate">
            <el-date-picker
              v-model="makeupForm.startDate"
              type="date"
              :placeholder="t('schedules.selectStartDate')"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item :label="t('schedules.endDate')" prop="endDate">
            <el-date-picker
              v-model="makeupForm.endDate"
              type="date"
              :placeholder="t('schedules.selectEndDate')"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item :label="t('schedules.startTime')" prop="startTime">
            <el-time-picker
              v-model="makeupForm.startTime"
              :placeholder="t('schedules.selectStartTime')"
              format="HH:mm"
              value-format="HH:mm"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item :label="t('schedules.endTime')" prop="endTime">
            <el-time-picker
              v-model="makeupForm.endTime"
              :placeholder="t('schedules.selectEndTime')"
              format="HH:mm"
              value-format="HH:mm"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item :label="t('schedules.room')" prop="roomId">
            <el-select v-model="makeupForm.roomId" :placeholder="t('schedules.selectRoom')" style="width: 100%">
              <el-option v-for="room in rooms" :key="room.id" :label="room.name" :value="room.id" />
            </el-select>
          </el-form-item>
        </template>
        
        <template v-if="makeupForm.makeupType === 'decline'">
          <el-form-item :label="t('schedules.declinedReasonLabel')" prop="declinedReason">
            <el-input 
              v-model="makeupForm.declinedReason" 
              type="textarea" 
              :rows="4" 
              :placeholder="t('schedules.inputDeclinedReason')"
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="makeupDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleMakeup">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 发送作业安排对话框 -->
    <el-dialog v-model="homeworkDialogVisible" :title="t('schedules.sendHomework')" width="700px" draggable>
      <el-alert
        :title="t('schedules.homeworkInstructions')"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #default>
          <div>{{ t('schedules.classHomeworkDesc') }}</div>
          <div>{{ t('schedules.regularHomeworkDesc') }}</div>
          <div>{{ t('schedules.homeworkImageDesc') }}</div>
          <div>{{ t('schedules.sendToWechatGroup') }}</div>
        </template>
      </el-alert>
      <el-form :model="homeworkForm" :rules="homeworkRules" ref="homeworkFormRef" label-width="120px">
        <el-form-item :label="t('schedules.classHomework')" prop="classHomework">
          <el-input
            v-model="homeworkForm.classHomework"
            type="textarea"
            :rows="4"
            :placeholder="t('schedules.inputClassHomework')"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.regularHomework')" prop="regularHomework">
          <el-input
            v-model="homeworkForm.regularHomework"
            type="textarea"
            :rows="4"
            :placeholder="t('schedules.inputRegularHomework')"
          />
        </el-form-item>
        <el-form-item :label="t('schedules.homeworkImage')">
          <el-upload
            v-model:file-list="homeworkForm.images"
            action="/api/upload"
            :headers="uploadHeaders"
            list-type="picture-card"
            :limit="3"
            :on-preview="handlePicturePreview"
            :on-success="handleUploadSuccess"
            :on-remove="handleRemove"
            :before-upload="beforeUpload"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div style="margin-top: 5px; font-size: 12px; color: #909399;">
            <el-icon><InfoFilled /></el-icon> {{ t('schedules.maxImagesTip') }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="homeworkDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button @click="handleHomeworkSubmit(false)" :loading="homeworkLoading">{{ t('schedules.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="handleHomeworkSubmit(true)" :loading="homeworkLoading">{{ t('schedules.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>

    <!-- 单词检查对话框 -->
    <el-dialog v-model="wordCheckDialogVisible" :title="t('schedules.wordCheckTitle')" width="900px" draggable>
      <div v-if="wordCheckData" style="margin-bottom: 15px;">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item :label="t('schedules.course')">{{ wordCheckData.course_name }}</el-descriptions-item>
          <el-descriptions-item :label="t('schedules.class')">{{ wordCheckData.class_name }}</el-descriptions-item>
          <el-descriptions-item :label="t('schedules.date')">{{ wordCheckData.start_date }} {{ wordCheckData.start_time }}-{{ wordCheckData.end_time }}</el-descriptions-item>
        </el-descriptions>
        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
          <el-button type="warning" size="small" @click="printWordCheck">
            <el-icon><Printer /></el-icon>
            {{ t('schedules.wordCheckPrint') }}
          </el-button>
          <el-button type="success" size="small" @click="screenshotWordCheck">
            <el-icon><Camera /></el-icon>
            {{ t('schedules.wordCheckScreenshot') }}
          </el-button>
        </div>
      </div>

      <div v-if="wordCheckCommonWords && wordCheckCommonWords.length > 0" style="margin-bottom: 15px;">
        <div style="font-weight: bold; margin-bottom: 8px;">{{ t('schedules.wordList') }}</div>
        <el-table :data="wordCheckCommonWords" border size="small">
          <el-table-column type="index" :label="t('schedules.indexLabel')" width="50" />
          <el-table-column prop="word" :label="t('schedules.wordLabel')" />
          <el-table-column prop="part_of_speech" :label="t('schedules.partOfSpeechLabel')" width="70">
            <template #default="{ row }">
              {{ formatPartOfSpeech(row.part_of_speech) }}
            </template>
          </el-table-column>
          <el-table-column prop="uk_phonetic" :label="t('schedules.ukPhoneticLabel')" />
          <el-table-column prop="us_phonetic" :label="t('schedules.usPhoneticLabel')" />
          <el-table-column prop="meaning" :label="t('schedules.meaningLabel')" />
          <el-table-column :label="t('schedules.masteryRequirementLabel')" width="70">
            <template #default="{ row }">
              {{ formatMasteryRequirement(row.mastery_requirement) }}
            </template>
          </el-table-column>
          <el-table-column prop="remark" :label="t('schedules.remarkLabel')" />
        </el-table>
        <div v-if="wordCheckCommonPhrases && wordCheckCommonPhrases.length > 0" style="margin-top: 10px;">
          <div style="font-weight: bold; margin-bottom: 8px;">{{ t('schedules.phraseListLabel') }}</div>
          <el-table :data="wordCheckCommonPhrases" border size="small">
            <el-table-column type="index" :label="t('schedules.indexLabel')" width="50" />
            <el-table-column prop="phrase" :label="t('schedules.phraseContentLabel')" />
            <el-table-column :label="t('schedules.phraseTypeLabel')" width="80">
              <template #default="{ row }">
                {{ formatPhraseType(row.phrase_type) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('schedules.syntacticRoleLabel')" width="80">
              <template #default="{ row }">
                {{ formatSyntacticRole(row.syntactic_role) }}
              </template>
            </el-table-column>
            <el-table-column prop="meaning" :label="t('schedules.meaningLabel')" />
            <el-table-column :label="t('schedules.masteryRequirementLabel')" width="70">
              <template #default="{ row }">
                {{ formatMasteryRequirement(row.mastery_requirement) }}
              </template>
            </el-table-column>
            <el-table-column prop="remark" :label="t('schedules.remarkLabel')" />
          </el-table>
        </div>
      </div>

      <div v-if="wordCheckNoWords" style="margin-bottom: 15px;">
        <el-alert :title="t('schedules.noDailyWordsForGrade')" type="warning" :closable="false" show-icon>
          <template #default>
            <div>{{ t('schedules.noDailyWordsTip') }}</div>
            <el-button type="primary" size="small" style="margin-top: 8px;" @click="goToDailyWords">{{ t('schedules.goToAddDailyWords') }}</el-button>
          </template>
        </el-alert>
      </div>

      <el-table :data="wordCheckData?.checks || []" border style="width: 100%;">
        <el-table-column prop="student_name" :label="t('schedules.studentName')" width="100" />
        <el-table-column prop="student_grade" :label="t('schedules.studentGrade')" width="100" />
        <el-table-column :label="t('schedules.completionStatus')" width="140">
          <template #default="{ row }">
            <el-select v-model="row.completion_status" size="small">
              <el-option :label="t('schedules.wordCompleted')" value="completed" />
              <el-option :label="t('schedules.wordPartial')" value="partial" />
              <el-option :label="t('schedules.wordIncomplete')" value="incomplete" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column :label="t('schedules.attentionWords')" min-width="200">
          <template #default="{ row }">
            <el-select v-model="row.attention_words" multiple filterable allow-create size="small" :placeholder="t('schedules.inputAttentionWords')" style="width: 100%;">
              <el-option v-for="w in (row.words || [])" :key="w.word" :label="w.word" :value="w.word" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column :label="t('schedules.wordCheckNotes')" min-width="150">
          <template #default="{ row }">
            <el-input v-model="row.notes" size="small" :placeholder="t('schedules.inputWordCheckNotes')" />
          </template>
        </el-table-column>
        </el-table>

      <template #footer>
        <el-button @click="wordCheckDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button @click="handleWordCheckSave(false)" :loading="wordCheckLoading">{{ t('schedules.saveAndScheduleNotify') }}</el-button>
        <el-button type="primary" @click="handleWordCheckSave(true)" :loading="wordCheckLoading">{{ t('schedules.saveAndNotifyNow') }}</el-button>
      </template>
    </el-dialog>

    <!-- 临时增员对话框 -->
    <el-dialog v-model="extraStudentDialogVisible" :title="t('schedules.extraStudentManage')" width="650px" draggable>
      <div v-if="extraStudentSchedule" style="margin-bottom: 15px;">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item :label="t('schedules.course')">{{ getCourseName(extraStudentSchedule.course_id) }}</el-descriptions-item>
          <el-descriptions-item :label="t('schedules.class')">{{ getClassName(extraStudentSchedule.class_id) }}</el-descriptions-item>
          <el-descriptions-item :label="t('schedules.date')">{{ extraStudentSchedule.start_date }} {{ extraStudentSchedule.start_time }}-{{ extraStudentSchedule.end_time }}</el-descriptions-item>
          <el-descriptions-item :label="t('schedules.teacher')">{{ getTeacherName(extraStudentSchedule.teacher_id) }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider content-position="left">{{ t('schedules.currentExtraStudents') }}</el-divider>
      <div v-if="currentExtraStudents.length > 0" style="margin-bottom: 15px;">
        <el-tag v-for="student in currentExtraStudents" :key="student.id" closable type="warning" size="large" style="margin: 3px;" @close="removeExtraStudent(student.id)">
          {{ student.name }}
        </el-tag>
      </div>
      <div v-else style="color: #909399; margin-bottom: 15px;">{{ t('schedules.noExtraStudents') }}</div>

      <el-divider content-position="left">{{ t('schedules.addExtraStudents') }}</el-divider>
      <el-form label-width="80px">
        <el-form-item :label="t('schedules.selectStudents')">
          <el-select
            v-model="selectedExtraStudentIds"
            multiple
            filterable
            :placeholder="t('schedules.selectStudentsPlaceholder')"
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
        <el-button @click="extraStudentDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddExtraStudents" :loading="extraStudentLoading" :disabled="selectedExtraStudentIds.length === 0">{{ t('schedules.confirmAddExtra') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, MagicStick, Delete, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock, InfoFilled, Link, Download, Upload, Document, Setting, Warning, Lock, Printer, Camera } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { hasFeature, FEATURES as licenseFeatures } from '@/utils/license'
import * as XLSX from 'xlsx'
import html2canvas from 'html2canvas'
import dayjs from 'dayjs'
import { useI18n } from 'vue-i18n'


const { t, locale } = useI18n()
const mainTableRef = ref(null)
const isScreenshotting = ref(false)
const topScrollbarRef = ref(null)
const scrollbarWidth = ref(0)
let scrollHandler = null

const currentUser = ref(null)
const router = useRouter()
const route = useRoute()

const isEditing = ref(false)  // 标记是否正在编辑
const loading = ref(false)
const autoScheduleLoading = ref(false)
const activeTab = ref('all')
const dialogVisible = ref(false)
const autoScheduleDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const previewSchedules = ref([])
const selectedPreviewSchedules = ref([])
const selectAll = ref(false)
const previewLoading = ref(false)
const saveLoading = ref(false)
const previewViewType = ref('table')
const selectAllCalendar = ref(false)
const previewEditDialogVisible = ref(false)
const previewEditLoading = ref(false)
const previewEditFormRef = ref(null)
const previewEditStartTime = ref('')
const previewEditEndTime = ref('')
const previewEditingTempId = ref(null)
const previewEditForm = ref({
  course_id: null,
  teacher_id: null,
  class_id: null,
  room_id: null,
  room_type: 'offline_physical',
  meeting_link: '',
  start_time: '',
  end_time: '',
  start_date: '',
  end_date: '',
})
const previewEditRules = {
  course_id: [{ required: true, message: t('schedules.validation.selectCourse'), trigger: 'change' }],
  teacher_id: [{ required: true, message: t('schedules.validation.selectTeacher'), trigger: 'change' }],
  class_id: [{ required: true, message: t('schedules.validation.selectClass'), trigger: 'change' }],
  room_type: [{ required: true, message: t('schedules.validation.selectRoomType'), trigger: 'change' }],
  start_time: [{ required: true, message: t('schedules.validation.selectStartTime'), trigger: 'change' }],
  end_time: [{ required: true, message: t('schedules.validation.selectEndTime'), trigger: 'change' }],
  start_date: [{ required: true, message: t('schedules.validation.selectStartDate'), trigger: 'change' }],
  end_date: [{ required: true, message: t('schedules.validation.selectEndDate'), trigger: 'change' }],
}
const previewEditAvailableTeachers = computed(() => {
  if (!previewEditForm.value.course_id) {
    return teachers.value
  }
  return teachers.value.filter(teacher => {
    return teacher.course_ids && teacher.course_ids.includes(previewEditForm.value.course_id)
  })
})
const dialogTitle = ref('')
const formRef = ref(null)
const autoScheduleFormRef = ref(null)
const conflictLoading = ref(false)
const popoverConflictSchedules = ref([])

const filterStartDate = ref('')
const filterEndDate = ref('')
const filterTeacherIds = ref([])
const filterStudentIds = ref([])
const filterClassIds = ref([])
const filterCourseIds = ref([])
const filterRoomIds = ref([])
const filterDaysOfWeek = ref([])
const filterHasConflict = ref(null)
const filterExecutionStatus = ref(null)
const filterScheduleType = ref(null)
const filterScheduleId = ref(null)
const filterHasAbsentStudents = ref(null)
const startTime = ref('')
const endTime = ref('')

const schedules = ref([])
const teachers = ref([])
const classes = ref([])
const students = ref([])
const courses = ref([])
const rooms = ref([])
const selectedSchedules = ref([])
const sortField = ref('id')  // 排序字段
const sortOrder = ref('desc')  // 排序顺序（倒序）

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

const resetFilters = () => {
  filterStartDate.value = ''
  filterEndDate.value = ''
  filterTeacherIds.value = []
  filterStudentIds.value = []
  filterClassIds.value = []
  filterCourseIds.value = []
  filterRoomIds.value = []
  filterDaysOfWeek.value = []
  filterHasConflict.value = null
  filterExecutionStatus.value = null
  filterScheduleType.value = null
  filterScheduleId.value = null
  filterHasAbsentStudents.value = null
  fetchSchedules()
}

const goBack = () => {
  router.back()
}

const pagination = ref({
  currentPage: 1,
  pageSize: 15,
  total: 0
})

const form = ref({
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
  schedule_type: 'formal'
})

const originalForm = ref({
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
  schedule_type: 'formal'
})

const autoScheduleForm = ref({
  algorithm: 'hybrid',
  room_type: 'offline_physical',
  classIds: [],
  start_date: '',
  end_date: ''
})

// 完训对话框
const completeDialogVisible = ref(false)
const completeFormRef = ref(null)
const currentCompleteSchedule = ref(null)
const completeForm = ref({
  content: '',
  homework: '',
  note: '',
  studentAttendance: []
})

const completeRules = computed(() => {
  // 获取当前完训的课程
  const schedule = currentCompleteSchedule.value
  if (!schedule) {
    return {
      content: [{ required: true, message: t('schedules.validation.inputCourseContent'), trigger: 'blur' }],
      homework: [{ required: true, message: t('schedules.validation.inputHomeworkContent'), trigger: 'blur' }],
      note: [{ required: true, message: t('schedules.validation.inputNoteContent'), trigger: 'blur' }]
    }
  }
  
  // 试听课不需要强制反馈
  if (schedule.schedule_type === 'trial') {
    return {}
  }
  
  // 获取导师信息
  const teacher = teachers.value.find(t => t.id === schedule.teacher_id)
  
  // 如果导师开启了"无需反馈"，则反馈字段不是必填的
  if (teacher && teacher.no_feedback_required) {
    return {}
  }
  
  // 否则反馈字段是必填的
  return {
    content: [{ required: true, message: t('schedules.validation.inputCourseContent'), trigger: 'blur' }],
    homework: [{ required: true, message: t('schedules.validation.inputHomeworkContent'), trigger: 'blur' }],
    note: [{ required: true, message: t('schedules.validation.inputNoteContent'), trigger: 'blur' }]
  }
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
const postponeRules = {
  startDate: [{ required: true, message: t('schedules.validation.selectStartDate'), trigger: 'change' }],
  endDate: [{ required: true, message: t('schedules.validation.selectEndDate'), trigger: 'change' }],
  startTime: [{ required: true, message: t('schedules.validation.selectStartTime'), trigger: 'change' }],
  endTime: [{ required: true, message: t('schedules.validation.selectEndTime'), trigger: 'change' }],
  postponeReason: [{ required: true, message: t('schedules.validation.inputPostponeReason'), trigger: 'blur' }]
}
const currentPostponeSchedule = ref(null)
// 取消对话框
const cancelDialogVisible = ref(false)
const currentCancelSchedule = ref(null)
const cancelFormRef = ref(null)
const cancelForm = ref({
  cancelReason: ''
})
const cancelRules = {
  cancelReason: [{ required: true, message: t('schedules.validation.inputCancelReason'), trigger: 'blur' }]
}
// 学员补课对话框
const makeupDialogVisible = ref(false)
const makeupFormRef = ref(null)
const makeupForm = ref({
  studentIds: [],
  startDate: '',
  endDate: '',
  startTime: '',
  endTime: '',
  roomId: null
})
// 作业安排对话框
const homeworkDialogVisible = ref(false)
const homeworkFormRef = ref(null)
const homeworkLoading = ref(false)
const currentHomeworkSchedule = ref(null)
const homeworkForm = ref({
  classHomework: '',
  regularHomework: '',
  images: []
})
const homeworkRules = {
  classHomework: [{ required: true, message: t('schedules.validation.inputClassHomework'), trigger: 'blur' }],
  regularHomework: [{ required: true, message: t('schedules.validation.inputRegularHomework'), trigger: 'blur' }]
}
// 单词检查对话框
const wordCheckDialogVisible = ref(false)
const wordCheckLoading = ref(false)
const wordCheckData = ref(null)
const wordCheckNoWords = ref(false)
const currentWordCheckSchedule = ref(null)

// 临时增员相关
const extraStudentDialogVisible = ref(false)
const extraStudentLoading = ref(false)
const extraStudentSchedule = ref(null)
const selectedExtraStudentIds = ref([])
const currentExtraStudents = ref([])
const availableExtraStudents = ref([])
const wordCheckCommonWords = computed(() => {
  if (!wordCheckData.value || !wordCheckData.value.checks || wordCheckData.value.checks.length === 0) return []
  const firstCheck = wordCheckData.value.checks.find(c => c.words && c.words.length > 0)
  return firstCheck ? firstCheck.words : []
})
const wordCheckCommonPhrases = computed(() => {
  if (!wordCheckData.value || !wordCheckData.value.checks || wordCheckData.value.checks.length === 0) return []
  const firstCheck = wordCheckData.value.checks.find(c => c.phrases && c.phrases.length > 0)
  return firstCheck ? firstCheck.phrases : []
})

const phraseTypeMap = {
  prepositional_phrase: t('schedules.prepositionalPhrase') || '介词短语',
  verb_phrase: t('schedules.verbPhrase') || '动词短语',
  noun_phrase: t('schedules.nounPhrase') || '名词短语',
  adjective_phrase: t('schedules.adjectivePhrase') || '形容词短语',
  adverb_phrase: t('schedules.adverbPhrase') || '副词短语',
  infinitive_phrase: t('schedules.infinitivePhrase') || '不定式短语',
  gerund_phrase: t('schedules.gerundPhrase') || '动名词短语',
  participle_phrase: t('schedules.participlePhrase') || '分词短语',
  conjunction_phrase: t('schedules.conjunctionPhrase') || '连词短语',
  clause_phrase: t('schedules.clausePhrase') || '从句',
}

const syntacticRoleMap = {
  subject: t('schedules.subject') || '主语',
  predicate: t('schedules.predicate') || '谓语',
  object: t('schedules.object') || '宾语',
  predicative: t('schedules.predicative') || '表语',
  attributive: t('schedules.attributive') || '定语',
  adverbial: t('schedules.adverbial') || '状语',
  complement: t('schedules.complement') || '补语',
  appositive: t('schedules.appositive') || '同位语',
  parenthetical: t('schedules.parenthetical') || '插入语',
}

const formatPhraseType = (val) => {
  if (!val) return '-'
  if (Array.isArray(val)) return val.length === 0 ? '-' : val.map(v => phraseTypeMap[v] || v).join('、')
  return phraseTypeMap[val] || val
}

const formatSyntacticRole = (val) => {
  if (!val) return '-'
  if (Array.isArray(val)) return val.length === 0 ? '-' : val.map(v => syntacticRoleMap[v] || v).join('、')
  return syntacticRoleMap[val] || val
}

const masteryRequirementMap = {
  recite: t('schedules.recite') || '会背',
  recognize: t('schedules.recognize') || '会认',
}

const formatMasteryRequirement = (val) => {
  if (!val) return '-'
  return masteryRequirementMap[val] || val
}

// 修改反馈对话框
const editFeedbackDialogVisible = ref(false)
const editFeedbackDialogTitle = ref('')
const editFeedbackFormRef = ref(null)
const editFeedbackForm = ref({
  content: '',
  homework: '',
  note: '',
  postpone_reason: '',
  cancel_reason: '',
  studentAttendance: []
})
const originalEditFeedbackForm = ref({
  content: '',
  homework: '',
  note: '',
  postpone_reason: '',
  cancel_reason: '',
  studentAttendance: []
})
const editFeedbackType = ref('')  // 'complete', 'postpone', 'cancel'
const currentEditFeedbackSchedule = ref(null)

const editFeedbackRules = computed(() => {
  // 获取当前编辑的课程
  const schedule = currentEditFeedbackSchedule.value
  if (!schedule) {
    return {}
  }
  
  // 如果是完训反馈
  if (editFeedbackType.value === 'complete') {
    // 试听课不需要强制反馈
    if (schedule.schedule_type === 'trial') {
      return {}
    }
    
    // 获取导师信息
    const teacher = teachers.value.find(t => t.id === schedule.teacher_id)
    
    // 如果导师开启了"无需反馈"，则反馈字段不是必填的
    if (teacher && teacher.no_feedback_required) {
      return {}
    }
    
    // 否则反馈字段是必填的
    return {
      content: [{ required: true, message: t('schedules.validation.inputCourseContent'), trigger: 'blur' }],
      homework: [{ required: true, message: t('schedules.validation.inputHomeworkContent'), trigger: 'blur' }],
      note: [{ required: true, message: t('schedules.validation.inputNoteContent'), trigger: 'blur' }]
    }
  }
  
  // 如果是延期原因或取消原因，则必填
  if (editFeedbackType.value === 'postpone') {
    return {
      postpone_reason: [{ required: true, message: t('schedules.validation.inputPostponeReason'), trigger: 'blur' }]
    }
  }
  
  if (editFeedbackType.value === 'cancel') {
    return {
      cancel_reason: [{ required: true, message: t('schedules.validation.inputCancelReason'), trigger: 'blur' }]
    }
  }
  
  return {}
})

const showEditFeedbackDialog = async (schedule, type) => {
  currentEditFeedbackSchedule.value = schedule
  editFeedbackType.value = type
  
  if (type === 'complete') {
    editFeedbackDialogTitle.value = t('schedules.editCompleteFeedback')
    // 解析现有的反馈内容
    let formData
    if (schedule.content_feedback) {
      const feedback = parseContentFeedback(schedule.content_feedback)
      formData = {
        content: feedback.find(f => f.rawLabel === '内容')?.content || '',
        homework: feedback.find(f => f.rawLabel === '作业')?.content || '',
        note: feedback.find(f => f.rawLabel === '注意')?.content || '',
        postpone_reason: '',
        cancel_reason: '',
        studentAttendance: []
      }
    } else {
      formData = {
        content: '',
        homework: '',
        note: '',
        postpone_reason: '',
        cancel_reason: '',
        studentAttendance: []
      }
    }
    
    // 加载该课程安排的学员列表
    try {
      const response = await api.get(`/schedules/${schedule.id}`)
      if (response.data && response.data.scheduled_students) {
        formData.studentAttendance = response.data.scheduled_students.map(s => ({
          id: s.id,
          name: s.name,
          status: s.attendance_status || 'present',
          absenceReason: ''
        }))
      } else {
        const classStudents = getActiveClassStudents(schedule.class_id)
        formData.studentAttendance = classStudents.map(student => ({
          id: student.id,
          name: student.name,
          status: 'present',
          absenceReason: ''
        }))
      }
    } catch (error) {
      window.logger.error('加载学员列表失败:', error)
      const classStudents = getActiveClassStudents(schedule.class_id)
      formData.studentAttendance = classStudents.map(student => ({
        id: student.id,
        name: student.name,
        status: 'present',
        absenceReason: ''
      }))
    }
     
    originalEditFeedbackForm.value = JSON.parse(JSON.stringify(formData))
    editFeedbackForm.value = formData
  } else if (type === 'postpone') {
    editFeedbackDialogTitle.value = t('schedules.editPostponeReason')
    const formData = {
      content: '',
      homework: '',
      note: '',
      postpone_reason: schedule.postpone_reason || '',
      cancel_reason: '',
      studentAttendance: []
    }
    originalEditFeedbackForm.value = { ...formData }
    editFeedbackForm.value = formData
  } else if (type === 'cancel') {
    editFeedbackDialogTitle.value = t('schedules.editCancelReason')
    const formData = {
      content: '',
      homework: '',
      note: '',
      postpone_reason: '',
      cancel_reason: schedule.cancel_reason || '',
      studentAttendance: []
    }
    originalEditFeedbackForm.value = { ...formData }
    editFeedbackForm.value = formData
  }
  
  editFeedbackDialogVisible.value = true
}

const handleEditFeedback = async () => {
  if (!editFeedbackFormRef.value) return
  
  await editFeedbackFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const scheduleId = currentEditFeedbackSchedule.value.id
        
        if (editFeedbackType.value === 'complete') {
          const contentFeedback = `内容：${editFeedbackForm.value.content}|作业：${editFeedbackForm.value.homework}|注意：${editFeedbackForm.value.note}`
          
          // 检查内容是否改变
          const isContentChanged = 
            editFeedbackForm.value.content !== originalEditFeedbackForm.value.content ||
            editFeedbackForm.value.homework !== originalEditFeedbackForm.value.homework ||
            editFeedbackForm.value.note !== originalEditFeedbackForm.value.note
          
          // 检查出勤状态是否改变
          const isAttendanceChanged = 
            JSON.stringify(editFeedbackForm.value.studentAttendance) !== JSON.stringify(originalEditFeedbackForm.value.studentAttendance)
          
          if (!isContentChanged && !isAttendanceChanged) {
            ElMessage.warning(t('schedules.message.noChangeSave'))
            return
          }
          
          // 更新课程反馈
          await api.put(`/schedules/${scheduleId}`, {
            content_feedback: contentFeedback
          })
          
          // 更新学员出勤状态
          if (isAttendanceChanged && editFeedbackForm.value.studentAttendance && editFeedbackForm.value.studentAttendance.length > 0) {
            const studentAttendance = {}
            const absenceReasons = {}
            editFeedbackForm.value.studentAttendance.forEach(item => {
              studentAttendance[item.id] = item.status
              if (item.status !== 'present' && item.absenceReason) {
                absenceReasons[item.id] = item.absenceReason
              }
            })
            
            await api.put(`/schedules/${scheduleId}/attendance`, {
              student_attendance: studentAttendance,
              absence_reasons: absenceReasons
            })
          }
          
          ElMessage.success(t('schedules.message.editCompleteFeedbackSuccess'))
        } else if (editFeedbackType.value === 'postpone') {
          if (editFeedbackForm.value.postpone_reason === originalEditFeedbackForm.value.postpone_reason) {
            ElMessage.warning(t('schedules.message.noChangeSave'))
            return
          }

          await api.put(`/schedules/${scheduleId}`, {
            postpone_reason: editFeedbackForm.value.postpone_reason
          })
          ElMessage.success(t('schedules.message.editPostponeReasonSuccess'))
        } else if (editFeedbackType.value === 'cancel') {
          if (editFeedbackForm.value.cancel_reason === originalEditFeedbackForm.value.cancel_reason) {
            ElMessage.warning(t('schedules.message.noChangeSave'))
            return
          }
          
          await api.put(`/schedules/${scheduleId}`, {
            cancel_reason: editFeedbackForm.value.cancel_reason
          })
          ElMessage.success(t('schedules.message.editCancelReasonSuccess'))
        }
        
        editFeedbackDialogVisible.value = false
        fetchSchedules()
      } catch (error) {
        window.logger.error('修改反馈失败:', error)
        ElMessage.error(t('schedules.message.editFeedbackFailed'))
      }
    }
  })
}

const handlePreviewSelectionChange = (selection) => {
  selectedPreviewSchedules.value = selection
}
const handleSelectAll = (checked) => {
  if (checked) {
    selectedPreviewSchedules.value = [...previewSchedules.value]
  } else {
    selectedPreviewSchedules.value = []
  }
}
const handleSelectConflicts = () => {
  selectedPreviewSchedules.value = previewSchedules.value.filter(s => s.has_conflict)
}
const handleSelectNoConflicts = () => {
  selectedPreviewSchedules.value = previewSchedules.value.filter(s => !s.has_conflict)
}
const handleSaveSelectedSchedules = async () => {
  if (selectedPreviewSchedules.value.length === 0) {
    ElMessage.warning(t('schedules.message.selectAtLeastOne'))
    return
  }
  
  saveLoading.value = true
  try {
    const response = await api.post('/schedules/save-preview-schedules', selectedPreviewSchedules.value)
    ElMessage.success(t('schedules.message.saveSuccess', { created: response.data.schedules_created, conflicts: response.data.conflicts_found }))
    previewDialogVisible.value = false
    fetchSchedules()
  } catch (error) {
    window.logger.error('保存排课失败:', error)
    ElMessage.error(t('schedules.message.saveFailed'))
  } finally {
    saveLoading.value = false
  }
}

const handleEditPreviewSchedule = (schedule) => {
  previewEditingTempId.value = schedule.temp_id
  previewEditForm.value = {
    course_id: schedule.course_id,
    teacher_id: schedule.teacher_id,
    class_id: schedule.class_id,
    room_id: schedule.room_id,
    room_type: schedule.room_type || 'offline_physical',
    meeting_link: schedule.meeting_link || '',
    start_time: schedule.start_time,
    end_time: schedule.end_time,
    start_date: schedule.start_date,
    end_date: schedule.end_date,
  }
  previewEditStartTime.value = schedule.start_time
  previewEditEndTime.value = schedule.end_time
  previewEditDialogVisible.value = true
}

const handlePreviewEditRoomTypeChange = () => {
  if (previewEditForm.value.room_type === 'online_virtual') {
    previewEditForm.value.room_id = null
  } else {
    previewEditForm.value.meeting_link = ''
  }
}

const handlePreviewEditConfirm = async () => {
  if (!previewEditFormRef.value) return

  previewEditForm.value.start_time = previewEditStartTime.value
  previewEditForm.value.end_time = previewEditEndTime.value

  await previewEditFormRef.value.validate(async (valid) => {
    if (!valid) return

    previewEditLoading.value = true
    try {
      const dayOfWeek = getDayOfWeekIntFromDate(previewEditForm.value.start_date)
      const checkData = {
        ...previewEditForm.value,
        day_of_week: dayOfWeek,
        schedule_type: 'formal',
      }
      const response = await api.post('/schedules/check-preview-conflict', checkData)

      const idx = previewSchedules.value.findIndex(s => s.temp_id === previewEditingTempId.value)
      if (idx !== -1) {
        const oldSchedule = previewSchedules.value[idx]
        const classChanged = previewEditForm.value.class_id !== oldSchedule.class_id
        let classStudents = oldSchedule.class_students || []
        if (classChanged) {
          classStudents = getActiveClassStudents(previewEditForm.value.class_id).map(s => ({
            id: s.id,
            name: s.name,
            code: s.code,
            contact_phone: s.contact_phone,
            email: s.email,
          }))
        }
        const updated = {
          ...oldSchedule,
          course_id: previewEditForm.value.course_id,
          teacher_id: previewEditForm.value.teacher_id,
          class_id: previewEditForm.value.class_id,
          room_id: previewEditForm.value.room_type === 'offline_physical' ? previewEditForm.value.room_id : null,
          room_type: previewEditForm.value.room_type,
          meeting_link: previewEditForm.value.room_type === 'online_virtual' ? previewEditForm.value.meeting_link : null,
          start_time: previewEditForm.value.start_time,
          end_time: previewEditForm.value.end_time,
          start_date: previewEditForm.value.start_date,
          end_date: previewEditForm.value.end_date,
          day_of_week: dayOfWeek,
          has_conflict: response.data.has_conflict,
          conflict_reason: response.data.conflict_reason,
          course_name: response.data.course_name,
          teacher_name: response.data.teacher_name,
          teacher_phone: response.data.teacher_phone,
          teacher_email: response.data.teacher_email,
          class_name: response.data.class_name,
          class_students: classStudents,
          room_name: response.data.room_name,
          room_location: response.data.room_location,
          room_capacity: response.data.room_capacity,
          room_facilities: response.data.room_facilities,
        }
        previewSchedules.value[idx] = updated

        const selIdx = selectedPreviewSchedules.value.findIndex(s => s.temp_id === previewEditingTempId.value)
        if (selIdx !== -1) {
          selectedPreviewSchedules.value[selIdx] = updated
        }
      }

      previewEditDialogVisible.value = false
      ElMessage.success(t('schedules.message.scheduleUpdated'))
    } catch (error) {
      window.logger.error('更新预览排课失败:', error)
      ElMessage.error(error.response?.data?.detail || t('schedules.message.updatePreviewFailed'))
    } finally {
      previewEditLoading.value = false
    }
  })
}
const makeupRules = computed(() => {
  if (makeupForm.value.makeupType === 'makeup') {
    return {
      studentIds: [{ required: true, message: t('schedules.validation.selectStudent'), trigger: 'change' }],
      startDate: [{ required: true, message: t('schedules.validation.selectStartDate'), trigger: 'change' }],
      endDate: [{ required: true, message: t('schedules.validation.selectEndDate'), trigger: 'change' }],
      startTime: [{ required: true, message: t('schedules.validation.selectStartTime'), trigger: 'change' }],
      endTime: [{ required: true, message: t('schedules.validation.selectEndTime'), trigger: 'change' }],
      roomId: [{ required: true, message: t('schedules.validation.selectRoom'), trigger: 'change' }]
    }
  } else {
    return {
      studentIds: [{ required: true, message: t('schedules.validation.selectStudent'), trigger: 'change' }],
      declinedReason: [{ required: true, message: t('schedules.validation.inputDeclinedReason'), trigger: 'blur' }]
    }
  }
})
const currentMakeupSchedule = ref(null)
const classStudents = ref([])

const rules = {
  course_id: [{ required: true, message: t('schedules.validation.selectCourse'), trigger: 'change' }],
  teacher_id: [{ required: true, message: t('schedules.validation.selectTeacher'), trigger: 'change' }],
  class_id: [{ required: true, message: t('schedules.validation.selectClass'), trigger: 'change' }],
  room_type: [{ required: true, message: t('schedules.validation.selectRoomType'), trigger: 'change' }],
  room_id: [{ 
    required: true, 
    message: t('schedules.validation.selectRoom'), 
    trigger: 'change',
    validator: (rule, value, callback) => {
      if (form.value.room_type === 'offline_physical' && !value) {
        callback(new Error(t('schedules.validation.selectRoom')))
      } else {
        callback()
      }
    }
  }],
  meeting_link: [{ 
    required: true, 
    message: t('schedules.validation.inputMeetingLink'), 
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (form.value.room_type === 'online_virtual' && !value) {
        callback(new Error(t('schedules.validation.inputMeetingLink')))
      } else {
        callback()
      }
    }
  }],
  day_of_week: [{ required: true, message: t('schedules.validation.selectDayOfWeek'), trigger: 'change' }],
  start_time: [{ required: true, message: t('schedules.validation.selectStartTime'), trigger: 'change' }],
  end_time: [{ required: true, message: t('schedules.validation.selectEndTime'), trigger: 'change' }],
  start_date: [{ required: true, message: t('schedules.validation.selectStartDate'), trigger: 'change' }],
  end_date: [{ required: true, message: t('schedules.validation.selectEndDate'), trigger: 'change' }]
}


const autoScheduleRules = {
  algorithm: [{ required: true, message: t('schedules.validation.selectAlgorithm'), trigger: 'change' }],
  room_type: [{ required: true, message: t('schedules.validation.selectRoomType'), trigger: 'change' }],
  start_date: [{ required: true, message: t('schedules.validation.selectStartDate'), trigger: 'change' }],
  end_date: [{ required: true, message: t('schedules.validation.selectEndDate'), trigger: 'change' }]
}

const handleRoomTypeChange = () => {
  if (form.value.room_type === 'online_virtual') {
    form.value.room_id = null
  } else {
    form.value.meeting_link = ''
  }
}

const loadConflictSchedules = async (schedule) => {
  if (!schedule || !schedule.id) return
  
  conflictLoading.value = true
  try {
    const response = await api.get(`/schedules/${schedule.id}/conflicts`)
    popoverConflictSchedules.value = response.data
  } catch (error) {
    window.logger.error('获取冲突课程失败:', error)
    ElMessage.error(t('schedules.message.getConflictFailed'))
  } finally {
    conflictLoading.value = false
  }
}

const conflictSchedules = computed(() => {
  return schedules.value.filter(s => s.has_conflict)
})

const fetchTeachers = async () => {
  try {
    const response = await api.get('/teachers', { params: { is_active: true, skip: 0, limit: 100000 } })
    teachers.value = response.data.items || response.data
  } catch (error) {
    if (error.response && error.response.status === 401) {
      window.logger.log('未登录，无法获取导师列表')
    } else {
      window.logger.error('获取导师列表失败:', error)
    }
  }
}

const fetchClasses = async () => {
  try {
    const response = await api.get('/classes', { params: { is_active: true, skip: 0, limit: 100000 } })
    classes.value = response.data.items || response.data
  } catch (error) {
    if (error.response && error.response.status === 401) {
      window.logger.log('未登录，无法获取班级列表')
    } else {
      window.logger.error('获取班级列表失败:', error)
    }
  }
}

const fetchStudents = async () => {
  try {
    const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    students.value = response.data.items || response.data
  } catch (error) {
    if (error.response && error.response.status === 401) {
      window.logger.log('未登录，无法获取学员列表')
    } else {
      window.logger.error('获取班级学员失败:', error)
    }
  }
}

const fetchCourses = async () => {
  try {
    const response = await api.get('/courses', { params: { is_active: true, skip: 0, limit: 100000 } })
    courses.value = response.data.items || response.data
  } catch (error) {
    if (error.response && error.response.status === 401) {
      window.logger.log('未登录，无法获取科目列表')
    } else {
      window.logger.error('获取科目失败:', error)
    }
  }
}

const fetchRooms = async () => {
  try {
    const response = await api.get('/rooms', { params: { is_active: true, skip: 0, limit: 100000 } })
    rooms.value = response.data.items || response.data
  } catch (error) {
    if (error.response && error.response.status === 401) {
      window.logger.log('未登录，无法获取教室列表')
    } else {
      window.logger.error('获取教室失败:', error)
    }
  }
}

const fetchSchedules = async () => {
  loading.value = true
  try {
    // 确保分页参数是有效的数字，防止出现 NaN
    const currentPage = Number(pagination.value.currentPage) || 1
    const pageSize = Number(pagination.value.pageSize) || 15
    
    const params = {
      skip: (currentPage - 1) * pageSize,
      limit: pageSize,
      sort_field: sortField.value,
      sort_order: sortOrder.value
    }
    
    if (filterStartDate.value) params.start_date = filterStartDate.value
    if (filterEndDate.value) params.end_date = filterEndDate.value
    if (filterCourseIds.value && filterCourseIds.value.length > 0) {
      params.course_ids = filterCourseIds.value.join(',')
    }
    if (filterTeacherIds.value && filterTeacherIds.value.length > 0) {
      params.teacher_ids = filterTeacherIds.value.join(',')
    }
    if (filterClassIds.value && filterClassIds.value.length > 0) {
      params.class_ids = filterClassIds.value.join(',')
    }
    if (filterStudentIds.value && filterStudentIds.value.length > 0) {
      params.student_ids = filterStudentIds.value.join(',')
    }
    if (filterRoomIds.value && filterRoomIds.value.length > 0) {
      params.room_ids = filterRoomIds.value.join(',')
    }
    if (filterDaysOfWeek.value && filterDaysOfWeek.value.length > 0) {
      params.days_of_week = filterDaysOfWeek.value.join(',')
    }
    if (filterHasConflict.value !== null && filterHasConflict.value !== '') {
      params.has_conflict = filterHasConflict.value
    }
    if (filterExecutionStatus.value) {
      if (Array.isArray(filterExecutionStatus.value)) {
        params.execution_status = filterExecutionStatus.value.join(',')
      } else {
        params.execution_status = filterExecutionStatus.value
      }
    }
    if (filterScheduleType.value) {
      params.schedule_type = filterScheduleType.value
    }
    if (filterScheduleId.value) {
      params.id = filterScheduleId.value
    }
    if (filterHasAbsentStudents.value !== null && filterHasAbsentStudents.value !== undefined) {
      params.has_absent_students = filterHasAbsentStudents.value
      window.logger.log('[DEBUG] has_absent_students 参数已添加:', filterHasAbsentStudents.value)
    }
    window.logger.log('[DEBUG] 请求参数:', params)
    const response = await api.get('/schedules', { params })
    schedules.value = response.data.items
    pagination.value.total = response.data.total
    
    // 同步滚动条宽度
    await nextTick()
    if (mainTableRef.value && topScrollbarRef.value) {
      const tableBody = mainTableRef.value.$el.querySelector('.el-table__body-wrapper')
      if (tableBody) {
        scrollbarWidth.value = tableBody.scrollWidth
      }
    }
  } catch (error) {
    window.logger.error('获取课程安排失败:', error)
    ElMessage.error(t('schedules.message.getScheduleFailed'))
  } finally {
    loading.value = false
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

const handleTabChange = () => {
  fetchSchedules()
}

// 辅助函数：根据名称查找ID（用于智能指令自动填充）
const findCourseByName = (name) => {
  if (!name) return null
  const course = courses.value.find(c => c.name === name)
  return course ? course.id : null
}

const findTeacherByName = (name) => {
  if (!name) return null
  const teacher = teachers.value.find(t => t.name === name)
  return teacher ? teacher.id : null
}

const findClassByName = (name) => {
  if (!name) return null
  const cls = classes.value.find(c => c.name === name)
  return cls ? cls.id : null
}

const findRoomByName = (name) => {
  if (!name) return null
  const room = rooms.value.find(r => r.name === name)
  return room ? room.id : null
}

// 监听开始日期变化，自动更新星期几
watch(() => form.value.start_date, (newDate) => {
  if (newDate && !isEditing.value) {
    form.value.day_of_week = getDayOfWeekIntFromDate(newDate)
  }
})

// 手动排课界面
const showAddDialog = () => {
  dialogTitle.value = t('schedules.manualScheduleTitle')
  startTime.value = ''
  endTime.value = ''
  // 重置编辑标志
  isEditing.value = false
  
  // 检查是否有智能指令传递的数据
  const smartCommandData = sessionStorage.getItem('smartCommandScheduleData')
  
  if (smartCommandData) {
    try {
      const data = JSON.parse(smartCommandData)
      window.logger.log('[DEBUG] 接收到智能指令数据:', data)
      window.logger.log('[DEBUG] 当前students列表:', students.value)
      window.logger.log('[DEBUG] 当前teachers列表:', teachers.value)
      window.logger.log('[DEBUG] 当前courses列表:', courses.value)
      window.logger.log('[DEBUG] 当前classes列表:', classes.value)
      window.logger.log('[DEBUG] 当前rooms列表:', rooms.value)
      
      // 根据学生姓名查找班级
      let classId = null
      if (data.studentNames && data.studentNames.length > 0) {
        window.logger.log('[DEBUG] 开始查找学生班级，学生列表:', data.studentNames)
        
        // 遍历所有学生，找到他们的共同班级
        const studentClassesList = []
        
        data.studentNames.forEach(studentName => {
          const student = students.value.find(s => s.name === studentName)
          window.logger.log(`[DEBUG] 查找学生 "${studentName}":`, student ? `找到，ID=${student.id}` : '未找到')
          if (student && student.classes && student.classes.length > 0) {
            window.logger.log(`[DEBUG] 学生 "${studentName}" 的班级:`, student.classes.map(c => c.name))
            studentClassesList.push(student.classes.map(c => ({ id: c.id, name: c.name })))
          }
        })
        
        // 找到共同班级
        if (studentClassesList.length > 0) {
          if (studentClassesList.length === 1) {
            // 只有一个学生，使用他的第一个班级
            classId = studentClassesList[0][0].id
            window.logger.log('[DEBUG] 单个学生，使用班级ID:', classId)
          } else {
            // 多个学生，找交集
            const firstStudentClassIds = studentClassesList[0].map(c => c.id)
            let commonClassIds = firstStudentClassIds
            
            for (let i = 1; i < studentClassesList.length; i++) {
              const currentClassIds = studentClassesList[i].map(c => c.id)
              commonClassIds = commonClassIds.filter(id => currentClassIds.includes(id))
            }
            
            if (commonClassIds.length > 0) {
              classId = commonClassIds[0]
              window.logger.log('[DEBUG] 多个学生，找到共同班级ID:', classId)
            } else {
              window.logger.log('[DEBUG] 多个学生，未找到共同班级')
            }
          }
        } else {
          window.logger.log('[DEBUG] 未找到任何学生的班级信息')
        }
      }
      
      // 只填充能够匹配到的字段
      const courseId = findCourseByName(data.courseName)
      const teacherId = findTeacherByName(data.teacherName)
      const roomId = findRoomByName(data.roomName)
      const classIdFromName = findClassByName(data.className)
      
      window.logger.log('[DEBUG] 字段匹配结果:', {
        courseName: data.courseName,
        courseId: courseId,
        teacherName: data.teacherName,
        teacherId: teacherId,
        className: data.className,
        classId: classId,
        classIdFromName: classIdFromName,
        finalClassId: classId || classIdFromName,
        roomName: data.roomName,
        roomId: roomId,
        dayOfWeek: data.dayOfWeek,
        startTime: data.startTime,
        endTime: data.endTime,
        startDate: data.startDate,
        endDate: data.endDate
      })
      
      // 设置表单数据，只填充匹配成功的字段
      form.value = {
        course_id: courseId,  // 如果找不到则为null
        teacher_id: teacherId,  // 如果找不到则为null
        class_id: classId || classIdFromName,  // 优先使用共同班级，其次使用指定的班级名称
        room_id: roomId,  // 如果找不到则为null
        room_type: 'offline_physical',
        meeting_link: '',
        day_of_week: data.dayOfWeek || null,
        start_time: data.startTime || '',
        end_time: data.endTime || '',
        start_date: data.startDate || '',
        end_date: data.endDate || '',
        content_feedback: '',
        schedule_type: 'formal'
      }
      
      // 重要：同时设置独立的 startTime 和 endTime 变量，用于 el-time-picker 显示
      if (data.startTime) {
        startTime.value = data.startTime
        window.logger.log('[DEBUG] 设置 startTime:', startTime.value)
      }
      if (data.endTime) {
        endTime.value = data.endTime
        window.logger.log('[DEBUG] 设置 endTime:', endTime.value)
      }
      
      window.logger.log('[DEBUG] 最终form.value:', form.value)
      window.logger.log('[DEBUG] 最终startTime:', startTime.value)
      window.logger.log('[DEBUG] 最终endTime:', endTime.value)
      
      // 清除sessionStorage中的数据
      sessionStorage.removeItem('smartCommandScheduleData')
      
      // 显示提示信息，告诉用户哪些字段已自动填充
      const filledFields = []
      if (courseId) filledFields.push(t('schedules.course'))
      if (teacherId) filledFields.push(t('schedules.teacher'))
      if (classId || classIdFromName) filledFields.push(t('schedules.class'))
      if (roomId) filledFields.push(t('schedules.room'))
      if (data.dayOfWeek) filledFields.push(t('schedules.dayOfWeek'))
      if (data.startTime) filledFields.push(t('schedules.startTime'))
      if (data.endTime) filledFields.push(t('schedules.endTime'))
      if (data.startDate) filledFields.push(t('schedules.date'))
      
      window.logger.log('[DEBUG] 已填充的字段:', filledFields)
      
      if (filledFields.length > 0) {
        ElMessage.success(t('schedules.message.autoFilled', { fields: filledFields.join(t('common.listSeparator')) }))
      } else {
        ElMessage.info(t('schedules.message.noMatchFound'))
      }
      
    } catch (error) {
      window.logger.error('解析智能指令数据失败:', error)
      window.logger.error('错误详情:', error.message, error.stack)
      sessionStorage.removeItem('smartCommandScheduleData')
      ElMessage.error(t('schedules.message.parseSmartCommandFailed') + ': ' + error.message)
    }
  } else {
    // 没有智能指令数据，正常初始化
    form.value = {
      course_id: null,
      teacher_id: null,
      class_id: null,
      room_id: null,
      room_type: 'offline_physical',
      meeting_link: '',
      day_of_week: null,
      start_time: '',
      end_time: '',
      start_date: null,
      end_date: null,
      content_feedback: '',
      schedule_type: 'formal'
    }
    startTime.value = ''
    endTime.value = ''
  }
  
  dialogVisible.value = true
}

const canEditSchedule = (row) => {
  if (!currentUser.value) return false
  
  // 超级管理员可以编辑所有课程
  if (currentUser.value.role === 'super_admin') return true
  
  // 超级导师可以编辑所有课程（需要根据站点设置判断）
  if (currentUser.value.is_subject_teacher) {
    // 如果课程状态不是completed/postponed/cancelled，可以编辑
    if (row.execution_status !== 'completed' && row.execution_status !== 'postponed' && row.execution_status !== 'cancelled') {
      return true
    }
    // 对于已完成/延期/取消的课程，检查编辑限制设置
    const scheduleEditRestricted = localStorage.getItem('schedule_edit_restricted')
    // 如果没有设置或者设置为true，则不允许编辑
    if (scheduleEditRestricted === null || scheduleEditRestricted === 'true') {
      return false
    }
    return true
  }
  
  // 系统管理员和系统审计员不能编辑课程
  if (currentUser.value.role === 'system_admin' || currentUser.value.role === 'system_audit' || currentUser.value.role === 'teaching_assistant') return false
  
  // 普通导师（course_admin，非超级导师）
  if (currentUser.value.role === 'course_admin') {
    // 只能编辑待执行的课程，不能编辑已完训的课程
    return row.execution_status === 'pending'
  }
  
  return false
}

const canDeleteSchedule = (row) => {
  if (!currentUser.value) return false
  
  // 超级管理员可以删除所有课程
  if (currentUser.value.role === 'super_admin') return true
  
  // 超级导师可以删除所有课程（需要根据站点设置判断）
  if (currentUser.value.is_subject_teacher) {
    // 如果课程状态不是completed/postponed/cancelled，可以删除
    if (row.execution_status !== 'completed' && row.execution_status !== 'postponed' && row.execution_status !== 'cancelled') {
      return true
    }
    // 对于已完成/延期/取消的课程，检查删除限制设置
    const scheduleDeleteRestricted = localStorage.getItem('schedule_delete_restricted')
    // 如果没有设置或者设置为true，则不允许删除
    if (scheduleDeleteRestricted === null || scheduleDeleteRestricted === 'true') {
      return false
    }
    return true
  }
  
  // 系统管理员和系统审计员不能删除课程
  if (currentUser.value.role === 'system_admin' || currentUser.value.role === 'system_audit' || currentUser.value.role === 'teaching_assistant') return false
  
  // 普通导师（course_admin，非超级导师）
  if (currentUser.value.role === 'course_admin') {
    // 只能删除待执行的课程，不能删除已完训的课程
    return row.execution_status === 'pending'
  }
  
  return false
}

const showEditDialog = (row) => {
  dialogTitle.value = t('schedules.editScheduleTitle')
  startTime.value = row.start_time
  endTime.value = row.end_time
  // 设置编辑标志，避免watch清空teacher_id
  isEditing.value = true
  const formData = {
    id: row.id,
    course_id: row.course_id,
    teacher_id: row.teacher_id,
    class_id: row.class_id,
    room_id: row.room_id,
    room_type: row.room_type || 'offline_physical',
    meeting_link: row.meeting_link || '',
    // 使用整数类型的星期几，对标后端要求
    day_of_week: getDayOfWeekIntFromDate(row.start_date),
    start_time: row.start_time,
    end_time: row.end_time,
    // 后端字段类型是Date，直接使用日期字符串（如"2026-05-01"）
    start_date: row.start_date || null,
    end_date: row.end_date || null,
    schedule_type: row.schedule_type || 'formal'
  }
  
  originalForm.value = { ...formData }
  form.value = formData
  dialogVisible.value = true
  // 使用nextTick延迟重置编辑标志
  nextTick(() => {
    isEditing.value = false
  })
}

const showCopyDialog = (row) => {
  dialogTitle.value = t('schedules.copyScheduleTitle')
  startTime.value = row.start_time
  endTime.value = row.end_time
  // 复制课程安排的所有参数，除了开始日期和结束日期
  form.value = {
    id: null,  // 清空id，因为是新建
    course_id: row.course_id,
    teacher_id: row.teacher_id,
    class_id: row.class_id,
    room_id: row.room_id,
    // 使用整数类型的星期几，对标后端要求
    day_of_week: getDayOfWeekIntFromDate(row.start_date),
    start_time: row.start_time,
    end_time: row.end_time,
    start_date: '',  // 开始日期为空
    end_date: '',  // 结束日期为空
    schedule_type: row.schedule_type || 'formal'  // 复制时保留原课程的类型
  }
  dialogVisible.value = true
}

// 提交表单，sendNotification参数控制是否发送通知（默认为true）
const handleSubmit = async (sendNotification = true) => {
  if (!formRef.value) return
  
  form.value.start_time = startTime.value
  form.value.end_time = endTime.value
  
  // 如果day_of_week为空，根据start_date自动计算
  if (!form.value.day_of_week && form.value.start_date) {
    form.value.day_of_week = getDayOfWeekIntFromDate(form.value.start_date)
  }
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 构建提交数据，确保只包含后端需要的字段
        const scheduleData = {
            course_id: form.value.course_id,
            teacher_id: form.value.teacher_id,
            class_id: form.value.class_id,
            room_type: form.value.room_type || 'offline_physical',
            day_of_week: form.value.day_of_week,
            start_time: form.value.start_time,
            end_time: form.value.end_time,
            start_date: form.value.start_date,
            end_date: form.value.end_date,
            content_feedback: form.value.content_feedback || '',
            schedule_type: form.value.schedule_type || 'formal',
            send_notification: sendNotification
        }
        
        // 根据教室类型添加相应字段
        if (form.value.room_type === 'offline_physical') {
          scheduleData.room_id = form.value.room_id
          scheduleData.meeting_link = null
        } else {
          scheduleData.room_id = null
          scheduleData.meeting_link = form.value.meeting_link || ''
        }

        if (form.value.id) {
          const isChanged = 
            form.value.course_id !== originalForm.value.course_id ||
            form.value.teacher_id !== originalForm.value.teacher_id ||
            form.value.class_id !== originalForm.value.class_id ||
            form.value.room_id !== originalForm.value.room_id ||
            form.value.room_type !== originalForm.value.room_type ||
            form.value.meeting_link !== originalForm.value.meeting_link ||
            form.value.day_of_week !== originalForm.value.day_of_week ||
            form.value.start_time !== originalForm.value.start_time ||
            form.value.end_time !== originalForm.value.end_time ||
            form.value.start_date !== originalForm.value.start_date ||
            form.value.end_date !== originalForm.value.end_date ||
            form.value.content_feedback !== originalForm.value.content_feedback ||
            form.value.schedule_type !== originalForm.value.schedule_type
          
          if (!isChanged) {
            ElMessage.warning(t('schedules.message.noChangeSave'))
            return
          }
          
          await api.put(`/schedules/${form.value.id}`, scheduleData)
          ElMessage.success(sendNotification ? t('schedules.message.editSuccessNotify') : t('schedules.message.editSuccess'))
        } else {
          await api.post('/schedules', scheduleData)
          ElMessage.success(sendNotification ? t('schedules.message.addSuccessNotify') : t('schedules.message.addSuccess'))
        }
        dialogVisible.value = false
        fetchSchedules()
      } catch (error) {
        window.logger.error('操作失败:', error)
        // 打印详细的错误信息以便调试
        if (error.response && error.response.data && error.response.data.detail) {
          window.logger.error('后端验证错误详情:', JSON.stringify(error.response.data.detail))
        }
        handleScheduleError(error)
      }
    }
  })
}

// 统一的排课错误处理函数
const handleScheduleError = (error) => {
  const errorMsg = error.response?.data?.detail || t('schedules.message.operationFailed')
  
  if (errorMsg.includes(t('schedules.message.studentsUnavailable'))) {
    ElMessageBox.alert(
      `<div style="line-height: 1.6;">
        <strong>⚠️ ${t('schedules.message.conflictReminder')}</strong><br/>
        ${errorMsg}<br/><br/>
        <span style="color: #e6a23c;">💡 ${t('schedules.message.conflictSuggestion')}</span><br/>
        ${t('schedules.message.conflictSuggestion1')}<br/>
        ${t('schedules.message.conflictSuggestion2')}
      </div>`,
      t('schedules.message.cannotComplete'),
      {
        confirmButtonText: t('schedules.message.iKnow'),
        dangerouslyUseHTMLString: true,
        type: 'warning'
      }
    )
  } else {
    ElMessage.error(errorMsg)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('schedules.message.deleteConfirm'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/schedules/${row.id}`)
      ElMessage.success(t('common.deleteSuccess'))
      fetchSchedules()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const handleSelectionChange = (selection) => {
  selectedSchedules.value = selection
}

const handleSortChange = ({ prop, order }) => {
  sortField.value = prop || 'id'
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  fetchSchedules()
}

const batchDeleteSchedules = () => {
  if (selectedSchedules.value.length === 0) {
    ElMessage.warning(t('schedules.message.selectAtLeastOne'))
    return
  }
  
  ElMessageBox.confirm(t('schedules.message.batchDeleteConfirm', { count: selectedSchedules.value.length }), t('schedules.message.batchDeleteTitle'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      const deletePromises = selectedSchedules.value.map(schedule => api.delete(`/schedules/${schedule.id}`))
      await Promise.all(deletePromises)
      ElMessage.success(t('schedules.message.batchDeleteSuccess', { count: selectedSchedules.value.length }))
      selectedSchedules.value = []
      fetchSchedules()
    } catch (error) {
      window.logger.error('批量删除失败:', error)
      ElMessage.error(t('schedules.message.batchDeleteFailed'))
    }
  }).catch(() => {})
}
const showAutoScheduleDialog = () => {
  autoScheduleForm.value = {
    algorithm: 'hybrid',
    room_type: 'offline_physical',
    classIds: [],
    start_date: '',
    end_date: ''
  }
  autoScheduleDialogVisible.value = true
}

const handleAutoSchedule = async () => {
  if (!autoScheduleFormRef.value) return
  
  await autoScheduleFormRef.value.validate(async (valid) => {
    if (valid) {
      autoScheduleLoading.value = true
      try {
        // 构建请求参数
        const params = {
          algorithm: autoScheduleForm.value.algorithm,
          start_date: autoScheduleForm.value.start_date,
          end_date: autoScheduleForm.value.end_date,
          room_type: autoScheduleForm.value.room_type
        }
        
        // 如果选择了班级，添加class_ids参数
        if (autoScheduleForm.value.classIds && autoScheduleForm.value.classIds.length > 0) {
          params.class_ids = autoScheduleForm.value.classIds.join(',')
        }
        
        const response = await api.post('/schedules/auto-schedule', null, {
          params: params
        })
        previewSchedules.value = response.data.schedules_preview.map((schedule, index) => ({
          ...schedule,
          temp_id: `preview_${index}`
        }))
        selectedPreviewSchedules.value = []
        selectAll.value = false
        selectAllCalendar.value = false
        autoScheduleDialogVisible.value = false
        previewDialogVisible.value = true
        
        // 根据是否指定班级显示不同的消息
        let message = t('schedules.message.autoSchedulePreview', { algorithm: response.data.algorithm })
        if (autoScheduleForm.value.classIds && autoScheduleForm.value.classIds.length > 0) {
          message += t('schedules.message.forClasses', { count: autoScheduleForm.value.classIds.length })
        } else {
          message += t('schedules.message.forAllClasses')
        }
        message += t('schedules.message.generatedSchedules', { total: response.data.total_schedules, conflicts: response.data.conflicts_found })
        
        ElMessage.success(message)
      } catch (error) {
        window.logger.error('智能算法排课失败:', error)
        ElMessage.error(t('schedules.message.autoScheduleFailed'))
      } finally {
        autoScheduleLoading.value = false
      }
    }
  })
}

// 预览日历视图相关计算属性
const previewTimeSlots = computed(() => {
  const slots = new Set()
  previewSchedules.value.forEach(schedule => {
    slots.add(schedule.start_time)
  })
  return Array.from(slots).sort()
})

const previewDisplayDates = computed(() => {
  if (previewSchedules.value.length === 0) return []
  
  const dates = new Map()
  previewSchedules.value.forEach(schedule => {
    const dateStr = schedule.start_date
    if (!dates.has(dateStr)) {
      const dateObj = new Date(dateStr)
      const dayNames = [t('schedules.sunday'), t('schedules.monday'), t('schedules.tuesday'), t('schedules.wednesday'), t('schedules.thursday'), t('schedules.friday'), t('schedules.saturday')]
      dates.set(dateStr, {
        dateStr,
        dateNum: dateObj.getDate(),
        dayName: dayNames[dateObj.getDay()],
        isToday: false
      })
    }
  })
  
  return Array.from(dates.values()).sort((a, b) => a.dateStr.localeCompare(b.dateStr))
})

// 预览视图切换处理
const handlePreviewViewTypeChange = () => {
  // 视图切换时的处理逻辑
  if (previewViewType.value === 'calendar') {
    // 同步表格视图的选择状态到日历视图
    syncSelectionToCalendar()
  } else {
    // 同步日历视图的选择状态到表格视图
    syncSelectionToTable()
  }
}

const syncSelectionToCalendar = () => {
  // 将selectedPreviewSchedules同步到selectAllCalendar
  if (selectedPreviewSchedules.value.length === previewSchedules.value.length && previewSchedules.value.length > 0) {
    selectAllCalendar.value = true
  } else {
    selectAllCalendar.value = false
  }
}

const syncSelectionToTable = () => {
  // 将selectedPreviewSchedules同步到selectAll
  if (selectedPreviewSchedules.value.length === previewSchedules.value.length && previewSchedules.value.length > 0) {
    selectAll.value = true
  } else {
    selectAll.value = false
  }
}

// 获取指定时间段的预览课程
const getPreviewSchedulesForSlot = (date, time) => {
  return previewSchedules.value.filter(schedule => 
    schedule.start_date === date.dateStr && 
    schedule.start_time === time
  )
}

// 检查预览课程是否被选中
const isPreviewScheduleSelected = (schedule) => {
  return selectedPreviewSchedules.value.some(s => s.temp_id === schedule.temp_id)
}

// 切换预览课程选择状态
const togglePreviewScheduleSelection = (schedule) => {
  const index = selectedPreviewSchedules.value.findIndex(s => s.temp_id === schedule.temp_id)
  if (index > -1) {
    selectedPreviewSchedules.value.splice(index, 1)
  } else {
    selectedPreviewSchedules.value.push(schedule)
  }
  
  // 更新全选状态
  updateSelectAllCalendarState()
}

// 更新日历视图全选状态
const updateSelectAllCalendarState = () => {
  if (selectedPreviewSchedules.value.length === previewSchedules.value.length && previewSchedules.value.length > 0) {
    selectAllCalendar.value = true
  } else {
    selectAllCalendar.value = false
  }
}

// 日历视图全选
const handleSelectAllCalendar = (checked) => {
  if (checked) {
    selectedPreviewSchedules.value = [...previewSchedules.value]
  } else {
    selectedPreviewSchedules.value = []
  }
}

// 日历视图只选择有冲突的
const handleSelectConflictsCalendar = () => {
  selectedPreviewSchedules.value = previewSchedules.value.filter(s => s.has_conflict)
  selectAllCalendar.value = false
}

// 日历视图只选择无冲突的
const handleSelectNoConflictsCalendar = () => {
  selectedPreviewSchedules.value = previewSchedules.value.filter(s => !s.has_conflict)
  selectAllCalendar.value = false
}

// 清除日历视图选择
const handleClearSelectionCalendar = () => {
  selectedPreviewSchedules.value = []
  selectAllCalendar.value = false
}

// 下载导入模板方法
const downloadImportTemplate = () => {
  const headers = [t('schedules.course'), t('schedules.teacher'), t('schedules.class'), t('schedules.roomType'), t('schedules.room'), t('schedules.meetingLink'), t('schedules.time'), t('schedules.date')]
  const exampleRow1 = [
    t('schedules.message.templateExampleCourse1'), t('schedules.message.templateExampleTeacher1'), t('schedules.message.templateExampleClass1'), t('schedules.offlinePhysical'), t('schedules.message.templateExampleRoom1'), '', '09:00-10:30', '2024-01-01'
  ]
  const exampleRow2 = [
    t('schedules.message.templateExampleCourse2'), t('schedules.message.templateExampleTeacher2'), t('schedules.message.templateExampleClass2'), t('schedules.onlineVirtual'), '', 'https://meeting.tencent.com/xxx', '14:00-15:30', '2024-01-02'
  ]
  const data = [headers, example1, example2]
  
  const ws = XLSX.utils.aoa_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, t('schedules.message.templateSheetName'))
  
  XLSX.writeFile(wb, t('schedules.message.templateFileName'))
  
  ElMessage.warning(t('schedules.message.templateDownloadTip'))
}

// 导入课程安排方法
const importDialogVisible = ref(false)
const importFile = ref(null)
const importUploading = ref(false)

const showImportDialog = () => {
  importDialogVisible.value = true
  importFile.value = null
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const handleImport = async () => {
  if (!importFile.value) {
    ElMessage.warning(t('schedules.message.selectFileFirst'))
    return
  }
  
  importUploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    
    const response = await api.post('/schedules/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    let message = t('schedules.message.importSuccess', { count: response.data.count })
    if (response.data.skipped > 0) {
      message += t('schedules.message.importSkipped', { skipped: response.data.skipped })
      
      // 显示失败详情
      if (response.data.failed_rows && response.data.failed_rows.length > 0) {
        setTimeout(() => {
          ElMessageBox.alert(
            `<div style="max-height: 300px; overflow-y: auto;">
              ${response.data.failed_rows.map(row => 
                `<p style="margin: 5px 0;"><strong>${t('schedules.message.rowFailed', { row: row.row })}:</strong> ${row.reason}</p>`
              ).join('')}
              ${response.data.skipped > 30 ? `<p style="color: #999;">${t('schedules.message.onlyShowFirst30')}</p>` : ''}
            </div>`,
            t('schedules.message.importResultTitle'),
            {
              dangerouslyUseHTMLString: true,
              confirmButtonText: t('common.confirm')
            }
          )
        }, 500)
      }
    }
    
    ElMessage.success(message)
    importDialogVisible.value = false
    fetchSchedules()
  } catch (error) {
    window.logger.error('导入失败:', error)
    ElMessage.error(error.response?.data?.detail || t('schedules.message.importFailed'))
  } finally {
    importUploading.value = false
  }
}

const handleExport = async (format) => {
  try {
    const params = {}
    
    // 添加筛选参数
    if (filterStartDate.value) {
      params.start_date = filterStartDate.value
    }
    if (filterEndDate.value) {
      params.end_date = filterEndDate.value
    }
    if (filterTeacherIds.value && filterTeacherIds.value.length > 0) {
      params.teacher_ids = filterTeacherIds.value.join(',')
    }
    if (filterStudentIds.value && filterStudentIds.value.length > 0) {
      params.student_ids = filterStudentIds.value.join(',')
    }
    if (filterClassIds.value && filterClassIds.value.length > 0) {
      params.class_ids = filterClassIds.value.join(',')
    }
    if (filterCourseIds.value && filterCourseIds.value.length > 0) {
      params.course_ids = filterCourseIds.value.join(',')
    }
    if (filterRoomIds.value && filterRoomIds.value.length > 0) {
      params.room_ids = filterRoomIds.value.join(',')
    }
    if (filterDaysOfWeek.value && filterDaysOfWeek.value.length > 0) {
      params.days_of_week = filterDaysOfWeek.value.join(',')
    }
    if (filterHasConflict.value !== null && filterHasConflict.value !== '') {
      params.has_conflict = filterHasConflict.value
    }
    if (filterExecutionStatus.value && filterExecutionStatus.value.trim()) {
      if (Array.isArray(filterExecutionStatus.value)) {
        params.execution_status = filterExecutionStatus.value.join(',')
      } else {
        params.execution_status = filterExecutionStatus.value
      }
    }
    if (filterScheduleType.value && filterScheduleType.value.trim()) {
      params.schedule_type = filterScheduleType.value
    }
    if (filterHasAbsentStudents.value !== null && filterHasAbsentStudents.value !== undefined) {
      params.has_absent_students = filterHasAbsentStudents.value
    }
    // 导出所有数据，不分页
    params.skip = 0
    params.limit = 100000
    params.lang = locale.value
    
    const response = await api.get(`/schedules/export/${format}`, {
      params,
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const timestamp = dayjs().format('YYYYMMDD_HHmmss')
    const fileExtension = format === 'excel' ? 'xlsx' : format
    link.download = `course_schedules_${timestamp}.${fileExtension}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success(t('schedules.message.exportSuccess', { format: format.toUpperCase() }))
  } catch (error) {
    window.logger.error('导出失败:', error)
    ElMessage.error(t('schedules.message.exportFailed'))
  }
}

const handleScreenshot = async () => {
  if (!mainTableRef.value) {
    ElMessage.warning(t('schedules.screenshotNoData'))
    return
  }

  isScreenshotting.value = true
  
  try {
    await nextTick()
    
    const tableEl = mainTableRef.value.$el
    
    const canvas = await html2canvas(tableEl, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      scrollX: -window.scrollX,
      scrollY: -window.scrollY,
      windowWidth: tableEl.scrollWidth,
      windowHeight: tableEl.scrollHeight,
      onclone: (clonedDoc) => {
        const clonedTable = clonedDoc.querySelector('.el-table')
        if (!clonedTable) return
        
        const clonedFixedRight = clonedTable.querySelector('.el-table__fixed-right')
        if (clonedFixedRight) clonedFixedRight.remove()
        const clonedFixedRightPatch = clonedTable.querySelector('.el-table__fixed-right-patch')
        if (clonedFixedRightPatch) clonedFixedRightPatch.remove()
        
        const clonedHeader = clonedTable.querySelector('.el-table__header-wrapper')
        const clonedBody = clonedTable.querySelector('.el-table__body-wrapper')
        const clonedScrollbar = clonedTable.querySelector('.el-scrollbar__wrap')
        
        if (clonedHeader) {
          clonedHeader.style.overflow = 'visible'
          clonedHeader.style.overflowX = 'visible'
        }
        if (clonedBody) {
          clonedBody.style.overflow = 'visible'
          clonedBody.style.overflowX = 'visible'
          clonedBody.style.maxHeight = 'none'
        }
        if (clonedScrollbar) {
          clonedScrollbar.style.overflow = 'visible'
          clonedScrollbar.style.overflowX = 'visible'
        }
        
        const allTags = clonedTable.querySelectorAll('.el-tag')
        allTags.forEach(tag => {
          const span = clonedDoc.createElement('span')
          span.textContent = tag.textContent
          span.style.display = 'inline-block'
          span.style.padding = '2px 8px'
          span.style.borderRadius = '4px'
          span.style.fontSize = '12px'
          span.style.lineHeight = '20px'
          span.style.border = '1px solid'
          span.style.whiteSpace = 'nowrap'
          
          if (tag.classList.contains('el-tag--success')) {
            span.style.backgroundColor = '#f0f9eb'
            span.style.borderColor = '#e1f3d8'
            span.style.color = '#67c23a'
          } else if (tag.classList.contains('el-tag--warning')) {
            span.style.backgroundColor = '#fdf6ec'
            span.style.borderColor = '#faecd8'
            span.style.color = '#e6a23c'
          } else if (tag.classList.contains('el-tag--info')) {
            span.style.backgroundColor = '#f4f4f5'
            span.style.borderColor = '#e9e9eb'
            span.style.color = '#909399'
          } else if (tag.classList.contains('el-tag--danger')) {
            span.style.backgroundColor = '#fef0f0'
            span.style.borderColor = '#fde2e2'
            span.style.color = '#f56c6c'
          } else if (tag.classList.contains('el-tag--primary')) {
            span.style.backgroundColor = '#ecf5ff'
            span.style.borderColor = '#d9ecff'
            span.style.color = '#409eff'
          } else {
            span.style.backgroundColor = '#f4f4f5'
            span.style.borderColor = '#e9e9eb'
            span.style.color = '#909399'
          }
          
          tag.parentNode.replaceChild(span, tag)
        })
      }
    })
    
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const timestamp = dayjs().format('YYYYMMDD_HHmmss')
    link.download = `course_schedules_${timestamp}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(t('schedules.screenshotSuccess'))
  } catch (error) {
    window.logger.error('截图失败:', error)
    ElMessage.error(t('schedules.screenshotFailed'))
  } finally {
    isScreenshotting.value = false
  }
}

const showCompleteDialog = async (schedule) => {
  currentCompleteSchedule.value = schedule
  
  // 获取导师信息
  const teacher = teachers.value.find(t => t.id === schedule.teacher_id)
  
  // 如果导师开启了"无需反馈"，清空反馈字段
  if (teacher && teacher.no_feedback_required) {
    completeForm.value = {
      content: '',
      homework: '',
      note: '',
      studentAttendance: []
    }
  } else {
    completeForm.value = {
      content: '',
      homework: '',
      note: '',
      studentAttendance: []
    }
  }
  
  // 加载该课程安排的学员列表
  try {
    const response = await api.get(`/schedules/${schedule.id}`)
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
      const classStudents = getActiveClassStudents(schedule.class_id)
      completeForm.value.studentAttendance = classStudents.map(student => ({
        id: student.id,
        name: student.name,
        status: 'present',
        absenceReason: '',
        isLocked: false  // 添加锁定标记
      }))
    }
    
    // 检测学员是否有对应日期的请假记录
    const scheduleDate = schedule.start_date
    const scheduleStartTime = schedule.start_time
    const scheduleEndTime = schedule.end_time
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
          item.absenceReason = matchedLeave.reason || t('schedules.hasLeaveRecord')
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
    const classStudents = getActiveClassStudents(schedule.class_id)
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

const handleComplete = async (sendNotification = false) => {
  if (!completeFormRef.value) return
  
  await completeFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const contentFeedback = `内容：${completeForm.value.content}|作业：${completeForm.value.homework}|注意：${completeForm.value.note}`
        
        // 构建学员出勤状态字典
        const studentAttendance = {}
        const absenceReasons = {}
        completeForm.value.studentAttendance.forEach(item => {
          studentAttendance[item.id] = item.status
          if (item.status !== 'present' && item.absenceReason) {
            absenceReasons[item.id] = item.absenceReason
          }
        })
        
        await api.post(`/schedules/${currentCompleteSchedule.value.id}/complete`, {
          content_feedback: contentFeedback,
          student_attendance: studentAttendance,
          absence_reasons: absenceReasons,
          send_notification: sendNotification
        })
        ElMessage.success(sendNotification ? t('schedules.message.editSuccessNotify') : t('schedules.completeSuccess'))
        completeDialogVisible.value = false
        fetchSchedules()
      } catch (error) {
        window.logger.error('完训失败:', error)
        ElMessage.error(t('schedules.message.operationFailed'))
      }
    }
  })
}

// 延期对话框方法
const showPostponeDialog = (schedule) => {
  currentPostponeSchedule.value = schedule
  postponeForm.value = {
    startDate: formatDate(schedule.start_date),
    endDate: formatDate(schedule.end_date),
    startTime: schedule.start_time,
    endTime: schedule.end_time
  }
  postponeDialogVisible.value = true
}
const handlePostpone = async (sendNotification = false) => {
  if (!postponeFormRef.value) return
  
  await postponeFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.post(`/schedules/${currentPostponeSchedule.value.id}/postpone`, {
          start_date: new Date(postponeForm.value.startDate).toISOString(),
          end_date: new Date(postponeForm.value.endDate).toISOString(),
          start_time: postponeForm.value.startTime,
          end_time: postponeForm.value.endTime,
          postpone_reason: postponeForm.value.postponeReason,
          send_notification: sendNotification
        })
        ElMessage.success(sendNotification ? t('schedules.message.editSuccessNotify') : t('schedules.postponeSuccess'))
        postponeDialogVisible.value = false
        fetchSchedules()
      } catch (error) {
        window.logger.error('延期失败:', error)
        ElMessage.error(t('schedules.message.operationFailed'))
      }
    }
  })
}

// 取消对话框方法
const showCancelDialog = (schedule) => {
  currentCancelSchedule.value = schedule
  cancelForm.value.cancelReason = ''
  cancelDialogVisible.value = true
}
const handleCancel = async (sendNotification = false) => {
  try {
    await cancelFormRef.value.validate()
    await api.post(`/schedules/${currentCancelSchedule.value.id}/cancel`, {
      cancel_reason: cancelForm.value.cancelReason,
      send_notification: sendNotification
    })
    ElMessage.success(sendNotification ? t('schedules.message.editSuccessNotify') : t('schedules.cancelSuccess'))
    cancelDialogVisible.value = false
    fetchSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('取消失败:', error)
      ElMessage.error(t('schedules.message.operationFailed'))
    }
  }
}

const handleNotifyNow = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('schedules.notifyNowConfirm'),
      t('schedules.notifyNow'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    await api.post(`/schedules/${row.id}/notify`)
    ElMessage.success(t('schedules.notifyNowSuccess'))
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('立即通知失败:', error)
      ElMessage.error(t('schedules.notifyNowFail'))
    }
  }
}

// 学员补课对话框方法
const showMakeupDialog = async (schedule) => {
  currentMakeupSchedule.value = schedule
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
    const response = await api.get(`/schedules/${schedule.id}/absent-students`)
    classStudents.value = response.data
    
    if (classStudents.value.length === 0) {
      ElMessage.info(t('schedules.noStudent'))
      makeupDialogVisible.value = false
      return
    }
  } catch (error) {
    window.logger.error('获取需要补课的学员失败:', error)
    ElMessage.error(t('schedules.message.operationFailed'))
    return
  }
  
  makeupDialogVisible.value = true
}

const handleMakeup = async () => {
  if (!makeupFormRef.value) return
  
  await makeupFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (makeupForm.value.makeupType === 'makeup') {
          await api.post(`/schedules/${currentMakeupSchedule.value.id}/makeup`, {
            start_date: new Date(makeupForm.value.startDate).toISOString(),
            end_date: new Date(makeupForm.value.endDate).toISOString(),
            start_time: makeupForm.value.startTime,
            end_time: makeupForm.value.endTime,
            student_ids: makeupForm.value.studentIds,
            room_id: makeupForm.value.roomId
          })
          ElMessage.success(t('schedules.makeup') + t('common.success'))
        } else {
          await api.post(`/schedules/${currentMakeupSchedule.value.id}/decline-makeup`, {
            student_ids: makeupForm.value.studentIds,
            declined_reason: makeupForm.value.declinedReason
          })
          ElMessage.success(t('schedules.declineMakeup') + t('common.success'))
        }
        makeupDialogVisible.value = false
        fetchSchedules()
      } catch (error) {
        window.logger.error('操作失败:', error)
        ElMessage.error(t('schedules.message.operationFailed'))
      }
    }
  })
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
      lines.push(`${student.name}: ${t('schedules.madeUp')} (ID: ${student.makeup_schedule_id})`)
    } else if (student.makeup_status === 'declined') {
      lines.push(`${student.name}: ${t('schedules.declineMakeup')} (${student.declined_reason})`)
    }
  })
  
  return lines.join('\n')
}

// 显示单词检查对话框
const showWordCheckDialog = async (schedule) => {
  currentWordCheckSchedule.value = schedule
  wordCheckLoading.value = true
  wordCheckDialogVisible.value = true
  wordCheckNoWords.value = false
  try {
    const response = await api.get(`/daily-words/checks/schedule/${schedule.id}`)
    wordCheckData.value = response.data
    const hasAnyWords = response.data.checks && response.data.checks.some(c => c.words && c.words.length > 0)
    wordCheckNoWords.value = !hasAnyWords
  } catch (error) {
    window.logger.error('获取单词检查数据失败:', error)
    ElMessage.error(t('common.operationFailedNetwork'))
  } finally {
    wordCheckLoading.value = false
  }
}

const goToDailyWords = () => {
  router.push('/admin/daily-words')
}

const handleWordCheckSave = async (sendNotification = false) => {
  if (!wordCheckData.value) return
  wordCheckLoading.value = true
  try {
    const checks = wordCheckData.value.checks.map(c => ({
      student_id: c.student_id,
      daily_word_id: c.daily_word_id,
      completion_status: c.completion_status,
      attention_words: c.attention_words || [],
      notes: c.notes || '',
    }))
    await api.post('/daily-words/checks/batch', {
      schedule_id: wordCheckData.value.schedule_id,
      checks: checks,
    })

    if (sendNotification) {
      try {
        await api.post('/daily-words/checks/notify', {
          schedule_id: wordCheckData.value.schedule_id,
          send_wechat: true,
          send_email: true,
        })
        ElMessage.success(t('schedules.wordCheckNotifySuccess'))
      } catch (error) {
        window.logger.error('发送单词检查通知失败:', error)
        ElMessage.warning(t('schedules.wordCheckSavedButNotifyFailed'))
      }
    } else {
      ElMessage.success(t('schedules.wordCheckSaved'))
    }
    wordCheckDialogVisible.value = false
  } catch (error) {
    window.logger.error('保存单词检查失败:', error)
    ElMessage.error(t('common.operationFailedNetwork'))
  } finally {
    wordCheckLoading.value = false
  }
}

// 打印单词检查
const printWordCheck = () => {
  const dialogEl = document.querySelector('.el-dialog')
  if (!dialogEl) return
  const printContent = dialogEl.innerHTML
  const originalContent = document.body.innerHTML
  document.body.innerHTML = printContent
  window.print()
  document.body.innerHTML = originalContent
  window.location.reload()
}

// 截图单词检查
const screenshotWordCheck = async () => {
  try {
    const dialogEl = document.querySelector('.el-dialog .el-dialog__body')
    if (!dialogEl) {
      ElMessage.warning(t('schedules.wordCheckNotFound'))
      return
    }
    const canvas = await html2canvas(dialogEl, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff'
    })
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
    await navigator.clipboard.write([
      new ClipboardItem({ 'image/png': blob })
    ])
    ElMessage.success(t('schedules.wordCheckScreenshotCopied'))
  } catch (error) {
    window.logger.error('截图失败:', error)
    ElMessage.error(t('schedules.wordCheckScreenshotFailed'))
  }
}

// 临时增员相关函数
const showExtraStudentDialog = async (schedule) => {
  extraStudentSchedule.value = schedule
  selectedExtraStudentIds.value = []
  extraStudentLoading.value = false
  extraStudentDialogVisible.value = true

  try {
    const scheduleResponse = await api.get(`/schedules/${schedule.id}`)
    const freshSchedule = scheduleResponse.data
    extraStudentSchedule.value = freshSchedule
    const extraStudents = (freshSchedule.scheduled_students || []).filter(s => s.is_extra)
    currentExtraStudents.value = extraStudents
  } catch (error) {
    // 不重置currentExtraStudents，保留之前handleAddExtraStudents中设置的值
    if (currentExtraStudents.value.length === 0) {
      const extraStudents = (schedule.scheduled_students || []).filter(s => s.is_extra)
      currentExtraStudents.value = extraStudents
    }
  }

  try {
    // 获取所有学员作为可选列表
    const response = await api.get('/students')
    const allStudents = response.data.items || response.data
    // 获取班级学员ID集合
    const classStudentIds = new Set()
    if (schedule.class_id) {
      const classResponse = await api.get(`/classes/${schedule.class_id}`)
      if (classResponse.data && classResponse.data.students) {
        classResponse.data.students.forEach(s => classStudentIds.add(s.id))
      }
    }
    // 已排课学员ID集合
    const scheduledStudentIds = new Set((schedule.scheduled_students || []).map(s => s.id))
    // 可选的学员：不在班级中且不在已排课列表中的学员
    availableExtraStudents.value = allStudents.filter(s => 
      !classStudentIds.has(s.id) && !scheduledStudentIds.has(s.id)
    )
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
    ElMessage.error(t('common.operationFailedNetwork'))
  }
}

const handleAddExtraStudents = async () => {
  if (selectedExtraStudentIds.value.length === 0) return
  extraStudentLoading.value = true
  try {
    const response = await api.post(`/schedules/${extraStudentSchedule.value.id}/extra-students`, selectedExtraStudentIds.value)
    const result = response.data
    if (result.added_students && result.added_students.length > 0) {
      ElMessage.success(t('schedules.extraStudentAdded', { count: result.added_students.length }))
    }
    if (result.skipped_students && result.skipped_students.length > 0) {
      const skippedNames = result.skipped_students.map(s => `${s.name || s.student_id}(${s.reason})`).join(', ')
      ElMessage.warning(t('schedules.extraStudentSkipped', { names: skippedNames }))
    }
    selectedExtraStudentIds.value = []
    const addedStudents = (result.added_students || []).map(s => ({
      ...s,
      id: s.student_id,
      is_extra: true,
      attendance_status: 'pending'
    }))
    currentExtraStudents.value = [...currentExtraStudents.value, ...addedStudents]
    try {
      const scheduleResponse = await api.get(`/schedules/${extraStudentSchedule.value.id}`)
      if (scheduleResponse.data) {
        const extraStudents = (scheduleResponse.data.scheduled_students || []).filter(s => s.is_extra)
        currentExtraStudents.value = extraStudents
        const scheduledStudentIds = new Set((scheduleResponse.data.scheduled_students || []).map(s => s.id))
        availableExtraStudents.value = availableExtraStudents.value.filter(s => !scheduledStudentIds.has(s.id))
      }
    } catch (refreshError) {
      // API刷新失败时保留本地数据，不清空
    }
    fetchSchedules()
  } catch (error) {
    ElMessage.error(t('common.operationFailedNetwork'))
  } finally {
    extraStudentLoading.value = false
  }
}

const removeExtraStudent = async (studentId) => {
  try {
    await api.delete(`/schedules/${extraStudentSchedule.value.id}/extra-students/${studentId}`)
    ElMessage.success(t('schedules.extraStudentRemoved'))
    currentExtraStudents.value = currentExtraStudents.value.filter(s => s.id !== studentId)
    // 将移除的学员加回可选列表
    const student = currentExtraStudents.value.find(s => s.id === studentId)
    // refresh from API
    fetchSchedules()
  } catch (error) {
    window.logger.error('移除临时增员学员失败:', error)
    ElMessage.error(t('common.operationFailedNetwork'))
  }
}

// 格式化词性
const formatPartOfSpeech = (val) => {
  const map = {
    noun: 'n.',
    pronoun: 'pron.',
    verb: 'v.',
    adjective: 'adj.',
    adverb: 'adv.',
    preposition: 'prep.',
    conjunction: 'conj.',
    interjection: 'interj.',
    article: 'art.',
    determiner: 'det.',
  }
  return map[val] || val || '-'
}

// 显示作业安排对话框
const showHomeworkDialog = (schedule) => {
  window.logger.log('DEBUG: showHomeworkDialog - schedule:', schedule)
  window.logger.log('DEBUG: showHomeworkDialog - schedule.homework_regular:', schedule.homework_regular)
  window.logger.log('DEBUG: showHomeworkDialog - schedule.homework_images:', schedule.homework_images)
  currentHomeworkSchedule.value = schedule
  
  // 从完训反馈中提取作业部分
  if (schedule.content_feedback) {
    const feedbackParts = parseContentFeedback(schedule.content_feedback)
    const homeworkPart = feedbackParts.find(p => p.rawLabel === '作业')
    homeworkForm.value.classHomework = homeworkPart ? homeworkPart.content : ''
  } else {
    homeworkForm.value.classHomework = ''
  }
  
  // 从数据库加载已保存的作业安排数据
  homeworkForm.value.regularHomework = schedule.homework_regular || ''
  
  // 从数据库加载已保存的图片
  if (schedule.homework_images) {
    const imageUrls = schedule.homework_images.split(',').filter(url => url)
    homeworkForm.value.images = imageUrls.map(url => ({
      name: url.split('/').pop(),
      url: url,
      response: { url: url }
    }))
  } else {
    homeworkForm.value.images = []
  }
  window.logger.log('DEBUG: showHomeworkDialog - homeworkForm:', homeworkForm.value)
  homeworkDialogVisible.value = true
}

// 提交作业安排
const handleHomeworkSubmit = async (sendNotification = false) => {
  if (!homeworkFormRef.value) return
  
  await homeworkFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        homeworkLoading.value = true
        
        const classInfo = classes.value.find(c => c.id === currentHomeworkSchedule.value.class_id)
        
        const feedbackParts = parseContentFeedback(currentHomeworkSchedule.value.content_feedback || '')
        const contentPart = feedbackParts.find(p => p.rawLabel === '内容')
        const notePart = feedbackParts.find(p => p.rawLabel === '注意')
        
        const newContentFeedback = `内容：${contentPart ? contentPart.content : ''}|作业：${homeworkForm.value.classHomework}|注意：${notePart ? notePart.content : ''}`
        
        const updateData = {
          content_feedback: newContentFeedback,
          homework_regular: homeworkForm.value.regularHomework,
          homework_images: homeworkForm.value.images && homeworkForm.value.images.length > 0 
            ? homeworkForm.value.images.map(img => img.response?.url || img.url).filter(url => url).join(',') 
            : ''
        }
        
        await api.put(`/schedules/${currentHomeworkSchedule.value.id}`, updateData)
        
        if (sendNotification) {
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
            const scheduleDate = currentHomeworkSchedule.value.start_date
            const scheduleTime = `${currentHomeworkSchedule.value.start_time}-${currentHomeworkSchedule.value.end_time}`
            const classStudents = getActiveClassStudents(currentHomeworkSchedule.value.class_id)
            const studentNames = classStudents.length > 0 ? classStudents.map(s => s.name).join(t('schedules.nameSeparator')) : t('common.none')
            
            let homeworkMessage = t('schedules.homeworkNotificationTemplate', {
              course: getCourseName(currentHomeworkSchedule.value.course_id),
              date: scheduleDate,
              time: scheduleTime,
              content: contentPart ? contentPart.content : t('common.none'),
              className: getClassName(currentHomeworkSchedule.value.class_id),
              students: studentNames,
              classHomework: homeworkForm.value.classHomework,
              regularHomework: homeworkForm.value.regularHomework
            })
            
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
                course_name: getCourseName(currentHomeworkSchedule.value.course_id),
                class_homework: homeworkForm.value.classHomework,
                regular_homework: homeworkForm.value.regularHomework,
                images: imageUrls
              })
            } catch (error) {
              window.logger.error('发送邮件作业通知失败:', error)
            }
          }
        }
        
        ElMessage.success(sendNotification ? t('schedules.message.editSuccessNotify') : t('schedules.homeworkNotify') + t('common.success'))
        homeworkDialogVisible.value = false
        fetchSchedules()
      } catch (error) {
        window.logger.error('作业安排失败:', error)
        ElMessage.error(t('schedules.message.operationFailed'))
      } finally {
        homeworkLoading.value = false
      }
    }
  })
}

const clearAllSchedules = () => {
  ElMessageBox.confirm(t('schedules.message.clearAllConfirm'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'error'
  }).then(async () => {
    try {
      await api.delete('/schedules/clear-all')
      ElMessage.success(t('schedules.message.clearAllSuccess'))
      fetchSchedules()
    } catch (error) {
      window.logger.error('清空失败:', error)
    }
  }).catch(() => {})
}

const getCourseName = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? course.name : '-'
}

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

const handleUploadSuccess = (response, uploadFile, uploadFiles) => {
  window.logger.log('上传成功:', response, uploadFile)
}
const handleRemove = (uploadFile, uploadFiles) => {
  window.logger.log('删除图片:', uploadFile)
}
const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error(t('schedules.message.imageOnlyError'))
    return false
  }
  if (!isLt2M) {
    ElMessage.error(t('schedules.message.imageSizeError'))
    return false
  }
  return true
}

const getClassName = (classId) => {
  const class_ = classes.value.find(c => c.id === classId)
  return class_ ? class_.name : '-'
}
const getClassStudents = (classId) => {
  return students.value.filter(s => s.class_ids && s.class_ids.includes(classId))
}
const getActiveClassStudents = (classId) => {
  // 获取某个班级的在读学员列表
  return students.value.filter(s => {
    // 检查学员是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学员是否在读
    const isActive = s.is_active
    return belongsToClass && isActive
  })
}
const getInactiveClassStudents = (classId) => {
  // 获取某个班级的非在读学员列表
  return students.value.filter(s => {
    // 检查学员是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学员是否非在读
    const isInactive = !s.is_active
    return belongsToClass && isInactive
  })
}

const getClassStudentCount = (classId) => {
  return students.value.filter(student => {
    const belongsToClass = student.class_ids && student.class_ids.includes(classId)
    return belongsToClass
  }).length
}

const hasStudentsNeedingMakeup = (schedule) => {
  if (!schedule.scheduled_students || schedule.scheduled_students.length === 0) return false
  return schedule.scheduled_students.some(student => 
    (student.attendance_status === 'absent' || student.attendance_status === 'leave') &&
    (!student.makeup_status || student.makeup_status === 'pending')
  )
}

const getCourseTeachers = (courseId) => {
  return teachers.value.filter(teacher => {
    return teacher.course_ids && teacher.course_ids.includes(courseId)
  })
}
const getTeacherName = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.name : '-'
}
const getTeacherContact = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.contact_phone : null
}
const getTeacherEmail = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.email : null
}
const getStudentName = (studentId) => {
  const student = students.value.find(s => s.id === studentId)
  return student ? student.name : '-'
}
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

const getStudentEnrollmentDate = (studentId) => {
  const student = getStudentDetail(studentId)
  if (!student || !student.enrollment_date) return '-'
  const date = new Date(student.enrollment_date)
  return date.toLocaleDateString('zh-CN')
}

const getStudentContactPerson = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.contact_person || '-') : '-'
}

const getStudentContactPhone = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.contact_phone || '-') : '-'
}

const getStudentEmail = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.email || '-') : '-'
}

const getStudentClasses = (studentId) => {
  const student = getStudentDetail(studentId)
  if (!student || !student.class_ids || student.class_ids.length === 0) {
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
const getRoomLocation = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.location : null
}
const getRoomCapacity = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.capacity : null
}
const getRoomFacilities = (roomId) => {
  const room = rooms.value.find(r => r.id === roomId)
  return room ? room.facilities : null
}
const availableTeachers = computed(() => {
  if (!form.value.course_id) {
    return teachers.value
  }
  
  // 获取选择的科目
  const selectedCourse = courses.value.find(c => c.id === form.value.course_id)
  if (!selectedCourse) {
    return teachers.value
  }
  
  // 返回能教授该科目的导师
  return teachers.value.filter(teacher => {
    return teacher.course_ids && teacher.course_ids.includes(form.value.course_id)
  })
})

watch(() => form.value.course_id, (newCourseId, oldCourseId) => {
  // 只在非编辑状态下才清空teacher_id
  if (newCourseId !== oldCourseId && !isEditing.value) {
    form.value.teacher_id = null
  }
})

const getDayOfWeekFromDate = (date) => {
  // 转换为与 Python 一致的星期几表示方式（1=周一，7=周日）
  const dayOfWeek = dayjs(date).day() || 7
  const pythonDayOfWeek = dayOfWeek === 0 ? 7 : dayOfWeek
  const days = [t('schedules.monday'), t('schedules.tuesday'), t('schedules.wednesday'), t('schedules.thursday'), t('schedules.friday'), t('schedules.saturday'), t('schedules.sunday')]
  return days[pythonDayOfWeek - 1] || '-'
}

// 获取整数类型的星期几（1-7）
const getDayOfWeekIntFromDate = (date) => {
  const dayOfWeek = dayjs(date).day() || 7
  return dayOfWeek === 0 ? 7 : dayOfWeek
}

const getDayOfWeek = (day) => {
  const days = [t('schedules.monday'), t('schedules.tuesday'), t('schedules.wednesday'), t('schedules.thursday'), t('schedules.friday'), t('schedules.saturday'), t('schedules.sunday')]
  return days[day - 1] || '-'
}

const formatDate = (date) => {
  // 直接格式化日期，不使用 UTC
  return dayjs(date).format('YYYY-MM-DD')
}

const goToPage = (path) => {
  router.push(path)
}

const feedbackLabelMap = {
  '内容': 'schedules.content',
  '作业': 'schedules.homework',
  '注意': 'schedules.note'
}

const parseContentFeedback = (feedback) => {
  if (!feedback) return []
  const lines = feedback.split('|').filter(line => line.trim())
  return lines.map(line => {
    const parts = line.split('：')
    if (parts.length >= 2) {
      const rawLabel = parts[0].trim()
      return {
        label: feedbackLabelMap[rawLabel] ? t(feedbackLabelMap[rawLabel]) : rawLabel,
        rawLabel,
        content: parts.slice(1).join('：').trim()
      }
    }
    return {
      label: t('schedules.feedback'),
      rawLabel: '',
      content: line.trim()
    }
  })
}

const initTopScrollbar = () => {
  nextTick(() => {
    if (!mainTableRef.value || !topScrollbarRef.value) {
      window.logger.warn('表格或滚动条ref未就绪')
      return
    }
    
    const tableEl = mainTableRef.value.$el
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    
    if (!scrollWrap) {
      window.logger.warn('找不到滚动容器')
      return
    }
    
    const contentWidth = scrollWrap.scrollWidth
    const containerWidth = scrollWrap.clientWidth
    
    window.logger.log('表格内容宽度:', contentWidth, '容器宽度:', containerWidth)
    
    if (contentWidth <= containerWidth) {
      topScrollbarRef.value.style.display = 'none'
      window.logger.log('内容未超出容器，隐藏滚动条')
      return
    }
    
    topScrollbarRef.value.style.display = 'block'
    scrollbarWidth.value = contentWidth
    window.logger.log('显示滚动条，宽度设置为:', contentWidth)
  })
}

const handleCompleteSchedule = async (schedule, prefillData) => {
  try {
    const contentFeedback = prefillData.content_feedback || ''
    
    await ElMessageBox.prompt(t('schedules.feedbackPlaceholder'), t('schedules.markComplete'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputPlaceholder: t('schedules.feedbackPlaceholder'),
      inputValue: contentFeedback,
      inputPattern: /.+/,
      inputErrorMessage: t('schedules.feedbackRequired')
    })
    
    const response = await api.post(`/schedules/${schedule.id}/complete`, {
      content_feedback: contentFeedback
    })
    
    ElMessage.success(t('schedules.completeSuccess'))
    await fetchSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('完成课程失败:', error)
      ElMessage.error(t('schedules.message.operationFailed'))
    }
  }
}

const handleCancelSchedule = async (schedule, prefillData) => {
  try {
    const cancelReason = prefillData.cancel_reason || ''
    const sendNotification = prefillData.send_notification || false
    
    await ElMessageBox.prompt(t('schedules.inputCancelReason'), t('schedules.markCancel'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputPlaceholder: t('schedules.inputCancelReason'),
      inputValue: cancelReason,
      inputPattern: /.+/,
      inputErrorMessage: t('schedules.validation.inputCancelReason')
    })
    
    const response = await api.post(`/schedules/${schedule.id}/cancel`, {
      cancel_reason: cancelReason,
      send_notification: sendNotification
    })
    
    ElMessage.success(t('schedules.cancelSuccess'))
    await fetchSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('取消课程失败:', error)
      ElMessage.error(t('schedules.message.operationFailed'))
    }
  }
}

const handlePostponeSchedule = async (schedule, prefillData) => {
  try {
    const startDate = prefillData.start_date || ''
    const endDate = prefillData.end_date || ''
    const startTime = prefillData.start_time || ''
    const endTime = prefillData.end_time || ''
    const postponeReason = prefillData.postpone_reason || ''
    
    if (!startDate || !startTime) {
      ElMessage.warning(t('schedules.validation.selectStartDate'))
      return
    }
    
    await ElMessageBox.prompt(t('schedules.inputPostponeReason'), t('schedules.markPostpone'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputPlaceholder: t('schedules.inputPostponeReason'),
      inputValue: postponeReason,
      inputPattern: /.+/,
      inputErrorMessage: t('schedules.validation.inputPostponeReason')
    })
    
    const response = await api.post(`/schedules/${schedule.id}/postpone`, {
      start_date: startDate,
      end_date: endDate || startDate,
      start_time: startTime,
      end_time: endTime || schedule.end_time,
      postpone_reason: postponeReason
    })
    
    ElMessage.success(t('schedules.postponeSuccess'))
    await fetchSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('延期课程失败:', error)
      ElMessage.error(t('schedules.message.operationFailed'))
    }
  }
}

const setupScrollSync = () => {
  window.logger.log('🔧 setupScrollSync 被调用')
  
  nextTick(() => {
    if (!mainTableRef.value || !topScrollbarRef.value) {
      window.logger.warn('❌ mainTableRef 或 topScrollbarRef 未就绪')
      return
    }
    
    const tableEl = mainTableRef.value.$el
    const headerWrapper = tableEl?.querySelector('.el-table__header-wrapper')
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    const fakeScrollbar = topScrollbarRef.value
    
    window.logger.log('🔍 查找元素:')
    window.logger.log('  headerWrapper:', headerWrapper)
    window.logger.log('  scrollWrap:', scrollWrap)
    window.logger.log('  fakeScrollbar:', fakeScrollbar)
    
    if (!headerWrapper || !scrollWrap || !fakeScrollbar) {
      window.logger.warn('❌ 找不到需要同步的元素')
      return
    }
    
    if (scrollHandler) {
      window.logger.log('🗑️ 清除旧的事件监听器')
      scrollWrap.removeEventListener('scroll', scrollHandler.wrapScroll)
      fakeScrollbar.removeEventListener('scroll', scrollHandler.fakeScroll)
    }
    
    const wrapScrollHandler = () => {
      const targetScroll = scrollWrap.scrollLeft
      
      if (Math.abs(fakeScrollbar.scrollLeft - targetScroll) > 1) {
        fakeScrollbar.scrollLeft = targetScroll
      }
      
      if (Math.abs(headerWrapper.scrollLeft - targetScroll) > 1) {
        headerWrapper.scrollLeft = targetScroll
      }
    }
    
    const fakeScrollHandler = () => {
      const targetScroll = fakeScrollbar.scrollLeft
      
      window.logger.log('📊 顶部滚动条滚动，目标值:', targetScroll)
      
      if (Math.abs(scrollWrap.scrollLeft - targetScroll) > 1) {
        scrollWrap.scrollLeft = targetScroll
        window.logger.log('✅ 同步 scrollWrap 到', targetScroll)
      }
      
      if (Math.abs(headerWrapper.scrollLeft - targetScroll) > 1) {
        headerWrapper.scrollLeft = targetScroll
        window.logger.log('✅ 同步 header 到', targetScroll)
      }
    }
    
    scrollWrap.addEventListener('scroll', wrapScrollHandler)
    fakeScrollbar.addEventListener('scroll', fakeScrollHandler)
    
    scrollHandler = {
      wrapScroll: wrapScrollHandler,
      fakeScroll: fakeScrollHandler
    }
    
    window.logger.log('✅ 滚动同步已设置成功')
  })
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  
  // 检查是否有来自智能指令的搜索/过滤参数
  const urlParams = new URLSearchParams(window.location.search)
  const filterBy = urlParams.get('filter_by')
  const filterValue = urlParams.get('filter_value')
  const dateFilter = urlParams.get('date')
  
  try {
    const response = await api.get('/settings')
    if (response.data) {
      localStorage.setItem('schedule_edit_restricted', response.data.schedule_edit_restricted !== undefined ? response.data.schedule_edit_restricted : true)
      localStorage.setItem('schedule_delete_restricted', response.data.schedule_delete_restricted !== undefined ? response.data.schedule_delete_restricted : true)
    }
  } catch (error) {
    window.logger.error('获取站点设置失败:', error)
  }
  
  // 并行加载所有数据
  await Promise.all([
    fetchTeachers(),
    fetchClasses(),
    fetchStudents(),
    fetchCourses(),
    fetchRooms(),
    fetchSchedules()
  ])
  
  window.logger.log('[DEBUG] 数据加载完成:', {
    studentsCount: students.value.length,
    teachersCount: teachers.value.length,
    coursesCount: courses.value.length,
    classesCount: classes.value.length,
    roomsCount: rooms.value.length
  })
  
  // 应用URL参数过滤（支持所有过滤参数的组合）
  let hasUrlFilters = false
  
  // 0. 处理课程ID过滤（最高优先级，如果指定了schedule_id，则只显示该课程）
  const scheduleIdParam = urlParams.get('schedule_id') || urlParams.get('id')
  if (scheduleIdParam) {
    const scheduleId = parseInt(scheduleIdParam)
    if (!isNaN(scheduleId)) {
      filterScheduleId.value = scheduleId
      hasUrlFilters = true
    }
  }
  
  // 1. 处理开始日期
  const startDateParam = urlParams.get('start_date')
  if (startDateParam) {
    filterStartDate.value = startDateParam
    hasUrlFilters = true
  }
  
  // 2. 处理结束日期
  const endDateParam = urlParams.get('end_date')
  if (endDateParam) {
    filterEndDate.value = endDateParam
    hasUrlFilters = true
  }
  
  // 3. 处理科目过滤（支持多个ID，用逗号分隔）
  const courseIdsParam = urlParams.get('course_ids')
  if (courseIdsParam) {
    const ids = courseIdsParam.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
    if (ids.length > 0) {
      filterCourseIds.value = ids
      hasUrlFilters = true
    }
  }
  
  // 4. 处理课程类型
  const scheduleTypeParam = urlParams.get('schedule_type')
  if (scheduleTypeParam && ['formal', 'trial'].includes(scheduleTypeParam)) {
    filterScheduleType.value = scheduleTypeParam
    hasUrlFilters = true
  }
  
  // 5. 处理导师过滤（支持多个ID，用逗号分隔）
  const teacherIdsParam = urlParams.get('teacher_ids')
  if (teacherIdsParam) {
    const ids = teacherIdsParam.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
    if (ids.length > 0) {
      filterTeacherIds.value = ids
      hasUrlFilters = true
    }
  }
  
  // 6. 处理班级过滤（支持多个ID，用逗号分隔）
  const classIdsParam = urlParams.get('class_ids')
  if (classIdsParam) {
    const ids = classIdsParam.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
    if (ids.length > 0) {
      filterClassIds.value = ids
      hasUrlFilters = true
    }
  }
  
  // 7. 处理学员过滤（支持多个ID，用逗号分隔）
  const studentIdsParam = urlParams.get('student_ids')
  if (studentIdsParam) {
    const ids = studentIdsParam.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
    if (ids.length > 0) {
      filterStudentIds.value = ids
      hasUrlFilters = true
    }
  }
  
  // 8. 处理教室过滤（支持多个ID，用逗号分隔）
  const roomIdsParam = urlParams.get('room_ids')
  if (roomIdsParam) {
    const ids = roomIdsParam.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
    if (ids.length > 0) {
      filterRoomIds.value = ids
      hasUrlFilters = true
    }
  }
  
  // 9. 处理星期几过滤（支持多个值，用逗号分隔，1-7）
  const daysOfWeekParam = urlParams.get('days_of_week')
  if (daysOfWeekParam) {
    const days = daysOfWeekParam.split(',').map(day => parseInt(day.trim())).filter(day => !isNaN(day) && day >= 1 && day <= 7)
    if (days.length > 0) {
      filterDaysOfWeek.value = days
      hasUrlFilters = true
    }
  }
  
  // 10. 处理冲突状态
  const hasConflictParam = urlParams.get('has_conflict')
  if (hasConflictParam !== null) {
    if (hasConflictParam === 'true' || hasConflictParam === '1') {
      filterHasConflict.value = true
      hasUrlFilters = true
    } else if (hasConflictParam === 'false' || hasConflictParam === '0') {
      filterHasConflict.value = false
      hasUrlFilters = true
    }
  }
  
  // 11. 处理执行状态（支持多个状态，用逗号分隔）
  const executionStatusParam = urlParams.get('execution_status')
  if (executionStatusParam) {
    const statuses = executionStatusParam.split(',').map(s => s.trim()).filter(s => ['pending', 'completed', 'postponed', 'cancelled'].includes(s))
    if (statuses.length > 0) {
      filterExecutionStatus.value = statuses
      hasUrlFilters = true
    }
  }
  
  // 11.5. 处理未全员出席过滤
  const hasAbsentStudentsParam = urlParams.get('has_absent_students')
  window.logger.log('[DEBUG] has_absent_students URL参数:', hasAbsentStudentsParam)
  if (hasAbsentStudentsParam !== null) {
    if (hasAbsentStudentsParam === 'true' || hasAbsentStudentsParam === '1') {
      filterHasAbsentStudents.value = true
      hasUrlFilters = true
      window.logger.log('[DEBUG] has_absent_students 设置为 true')
    } else if (hasAbsentStudentsParam === 'false' || hasAbsentStudentsParam === '0') {
      filterHasAbsentStudents.value = false
      hasUrlFilters = true
      window.logger.log('[DEBUG] has_absent_students 设置为 false')
    }
  }

  // 12. 处理action参数，支持从智能指令助手等外部触发的操作
  const actionParam = urlParams.get('action')
  if (actionParam === 'add') {
    window.logger.log('[DEBUG] 检测到 action=add 参数，准备打开手动排课对话框')
    showAddDialog()
  }

  // 13. 处理旧的filter_by格式（向后兼容）
  if (filterBy && filterValue) {
    let foundAndApplied = false
    
    if (filterBy === 'student') {
      filterStudentIds.value = []
      let student = students.value.find(s => s.name === filterValue)
      if (!student) {
        const studentId = parseInt(filterValue)
        if (!isNaN(studentId)) {
          student = students.value.find(s => s.id === studentId)
        }
      }
      if (student) {
        filterStudentIds.value = [student.id]
        ElMessage.success(t('schedules.message.filterStudentSuccess', { name: student.name }))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterStudentNotFound', { value: filterValue }))
      }
    } else if (filterBy === 'teacher') {
      filterTeacherIds.value = []
      let teacher = teachers.value.find(t => t.name === filterValue)
      if (!teacher) {
        const teacherId = parseInt(filterValue)
        if (!isNaN(teacherId)) {
          teacher = teachers.value.find(t => t.id === teacherId)
        }
      }
      if (teacher) {
        filterTeacherIds.value = [teacher.id]
        ElMessage.success(t('schedules.message.filterTeacherSuccess', { name: teacher.name }))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterTeacherNotFound', { value: filterValue }))
      }
    } else if (filterBy === 'class') {
      filterClassIds.value = []
      let cls = classes.value.find(c => c.name === filterValue)
      if (!cls) {
        const classId = parseInt(filterValue)
        if (!isNaN(classId)) {
          cls = classes.value.find(c => c.id === classId)
        }
      }
      if (cls) {
        filterClassIds.value = [cls.id]
        ElMessage.success(t('schedules.message.filterClassSuccess', { name: cls.name }))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterClassNotFound', { value: filterValue }))
      }
    } else if (filterBy === 'course') {
      filterCourseIds.value = []
      let course = courses.value.find(c => c.name === filterValue)
      if (!course) {
        const courseId = parseInt(filterValue)
        if (!isNaN(courseId)) {
          course = courses.value.find(c => c.id === courseId)
        }
      }
      if (course) {
        filterCourseIds.value = [course.id]
        ElMessage.success(t('schedules.message.filterCourseSuccess', { name: course.name }))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterCourseNotFound', { value: filterValue }))
      }
    } else if (filterBy === 'room') {
      filterRoomIds.value = []
      let room = rooms.value.find(r => r.name === filterValue)
      if (!room) {
        const roomId = parseInt(filterValue)
        if (!isNaN(roomId)) {
          room = rooms.value.find(r => r.id === roomId)
        }
      }
      if (room) {
        filterRoomIds.value = [room.id]
        ElMessage.success(t('schedules.message.filterRoomSuccess', { name: room.name }))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterRoomNotFound', { value: filterValue }))
      }
    } else if (filterBy === 'schedule_type') {
      if (['formal', 'trial'].includes(filterValue)) {
        filterScheduleType.value = filterValue
        ElMessage.success(t('schedules.message.filterScheduleTypeSuccess', { type: filterValue === 'formal' ? t('schedules.message.formalClass') : t('schedules.message.trialClassShort') }))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterScheduleTypeInvalid', { value: filterValue }))
      }
    } else if (filterBy === 'execution_status') {
      if (['pending', 'completed', 'postponed', 'cancelled'].includes(filterValue)) {
        filterExecutionStatus.value = filterValue
        const statusMap = {
          'pending': t('schedules.pending'),
          'completed': t('schedules.completed'),
          'postponed': t('schedules.postponed'),
          'cancelled': t('schedules.cancelled')
        }
        ElMessage.success(t('schedules.message.filterStatusSuccess', { status: statusMap[filterValue] }))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterStatusInvalid', { value: filterValue }))
      }
    } else if (filterBy === 'has_conflict') {
      if (filterValue === 'true' || filterValue === '1') {
        filterHasConflict.value = true
        ElMessage.success(t('schedules.message.filterConflictTrue'))
        foundAndApplied = true
      } else if (filterValue === 'false' || filterValue === '0') {
        filterHasConflict.value = false
        ElMessage.success(t('schedules.message.filterConflictFalse'))
        foundAndApplied = true
      } else {
        ElMessage.warning(t('schedules.message.filterConflictInvalid', { value: filterValue }))
      }
    } else {
      ElMessage.warning(t('schedules.message.filterTypeUnsupported', { value: filterBy }))
    }
    
    if (foundAndApplied) {
      hasUrlFilters = true
    }
  }
  
  // 13. 处理日期快捷过滤（今天、明天、后天等）
  if (dateFilter) {
    let targetDate = new Date()
    if (dateFilter === t('schedules.validation.dateToday')) {
      targetDate = new Date()
    } else if (dateFilter === t('schedules.validation.dateTomorrow')) {
      targetDate.setDate(targetDate.getDate() + 1)
    } else if (dateFilter === t('schedules.validation.dateDayAfterTomorrow')) {
      targetDate.setDate(targetDate.getDate() + 2)
    } else if (dateFilter.includes(t('schedules.validation.dateDaysLater', { n: '' }))) {
      const days = parseInt(dateFilter.replace(t('schedules.validation.dateDaysLater', { n: '' }), ''))
      targetDate.setDate(targetDate.getDate() + days)
    } else if (dateFilter.match(/\d{4}-\d{2}-\d{2}/)) {
      targetDate = new Date(dateFilter)
    }
    
    const dateStr = targetDate.toISOString().split('T')[0]
    filterStartDate.value = dateStr
    filterEndDate.value = dateStr
    hasUrlFilters = true
    
    setTimeout(() => {
      ElMessage.info(t('schedules.message.filterDateInfo', { date: dateFilter }))
    }, 600)
  }
  
  // 如果有任何URL过滤参数，重新获取数据
  if (hasUrlFilters) {
    setTimeout(() => {
      fetchSchedules()
      // 显示综合提示
      const appliedFilters = []
      if (filterStartDate.value) appliedFilters.push(`${t('schedules.date')}: ${filterStartDate.value}${filterEndDate.value && filterEndDate.value !== filterStartDate.value ? ' - ' + filterEndDate.value : ''}`)
      if (filterCourseIds.value.length > 0) appliedFilters.push(`${t('schedules.course')}: ${filterCourseIds.value.length}`)
      if (filterScheduleType.value) appliedFilters.push(`${t('schedules.scheduleType')}: ${filterScheduleType.value === 'formal' ? t('schedules.message.formalClass') : t('schedules.message.trialClassShort')}`)
      if (filterTeacherIds.value.length > 0) appliedFilters.push(`${t('schedules.teacher')}: ${filterTeacherIds.value.length}`)
      if (filterClassIds.value.length > 0) appliedFilters.push(`${t('schedules.class')}: ${filterClassIds.value.length}`)
      if (filterStudentIds.value.length > 0) appliedFilters.push(`${t('schedules.student')}: ${filterStudentIds.value.length}`)
      if (filterRoomIds.value.length > 0) appliedFilters.push(`${t('schedules.room')}: ${filterRoomIds.value.length}`)
      if (filterDaysOfWeek.value.length > 0) appliedFilters.push(`${t('schedules.dayOfWeek')}: ${filterDaysOfWeek.value.length}`)
      if (filterHasConflict.value !== null) appliedFilters.push(`${t('schedules.hasConflict')}: ${filterHasConflict.value ? t('common.yes') : t('common.no')}`)
      if (filterExecutionStatus.value) {
        const statusMap = { 'pending': t('schedules.pending'), 'completed': t('schedules.completed'), 'postponed': t('schedules.postponed'), 'cancelled': t('schedules.cancelled') }
        appliedFilters.push(`${t('schedules.executionStatus')}: ${statusMap[filterExecutionStatus.value]}`)
      }
      if (filterHasAbsentStudents.value !== null) appliedFilters.push(`${t('schedules.attendance')}: ${filterHasAbsentStudents.value ? t('schedules.notAllPresent') : t('schedules.allPresent')}`)
      
      if (appliedFilters.length > 0) {
        ElMessage.success({
          message: t('schedules.message.appliedFilters', { count: appliedFilters.length }),
          duration: 3000
        })
      }
    }, 300)
  }
})

// 监听路由参数变化，支持从悬浮球等外部触发的操作
watch(() => route.query, (newQuery) => {
  if (newQuery.action === 'add') {
    window.logger.log('[DEBUG] 路由参数变化检测到 action=add，准备打开对话框')
    showAddDialog()
  }
  
  // 处理 schedule_type 过滤参数
  if (newQuery.schedule_type !== undefined) {
    filterScheduleType.value = newQuery.schedule_type
    fetchSchedules()
  }

  // 处理 schedule_id 过滤参数
  if (newQuery.schedule_id !== undefined || newQuery.id !== undefined) {
    const scheduleId = parseInt(newQuery.schedule_id || newQuery.id)
    if (!isNaN(scheduleId)) {
      filterScheduleId.value = scheduleId
      fetchSchedules()
      ElMessage.success(t('schedules.message.locateScheduleSuccess', { id: scheduleId }))
    }
  }

  // 处理 date 过滤参数（今天、明天、后天等）
  if (newQuery.date !== undefined) {
    let targetDate = new Date()
    const dateFilter = newQuery.date
    
    if (dateFilter === t('schedules.validation.dateToday')) {
      targetDate = new Date()
    } else if (dateFilter === t('schedules.validation.dateTomorrow')) {
      targetDate.setDate(targetDate.getDate() + 1)
    } else if (dateFilter === t('schedules.validation.dateDayAfterTomorrow')) {
      targetDate.setDate(targetDate.getDate() + 2)
    } else if (dateFilter.includes(t('schedules.validation.dateDaysLater', { n: '' }))) {
      const days = parseInt(dateFilter.replace(t('schedules.validation.dateDaysLater', { n: '' }), ''))
      targetDate.setDate(targetDate.getDate() + days)
    } else if (dateFilter.match(/\d{4}-\d{2}-\d{2}/)) {
      targetDate = new Date(dateFilter)
    }
    
    const dateStr = targetDate.toISOString().split('T')[0]
    filterStartDate.value = dateStr
    filterEndDate.value = dateStr
    fetchSchedules()
    
    setTimeout(() => {
      ElMessage.info(t('schedules.message.filterDateInfo', { date: dateFilter }))
    }, 300)
  }

  // 处理 has_absent_students 过滤参数
  if (newQuery.has_absent_students !== undefined) {
    filterHasAbsentStudents.value = newQuery.has_absent_students === 'true' || newQuery.has_absent_students === true
    fetchSchedules()
    
    setTimeout(() => {
      ElMessage.info(t('schedules.message.filterAttendanceInfo', { type: filterHasAbsentStudents.value ? t('schedules.notAllPresent') : t('schedules.allPresent') }))
    }, 300)
  }
}, { deep: true })

onUnmounted(() => {
  if (scrollHandler && mainTableRef.value) {
    const tableEl = mainTableRef.value.$el
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    
    if (scrollWrap) {
      scrollWrap.removeEventListener('scroll', scrollHandler.wrapScroll)
    }
    if (topScrollbarRef.value) {
      topScrollbarRef.value.removeEventListener('scroll', scrollHandler.fakeScroll)
    }
  }
})

watch(schedules, () => {
  setTimeout(() => {
    initTopScrollbar()
    setupScrollSync()
  }, 200)
})

</script>

<style scoped>
.schedules-page {
  padding: 6px;
}

.fake-scrollbar {
  overflow-x: auto;
  overflow-y: hidden;
  height: 12px;
  margin-bottom: 5px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.fake-scrollbar .scrollbar-inner {
  height: 1px;
}

.fake-scrollbar::-webkit-scrollbar {
  height: 12px;
}

.fake-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 6px;
}

.fake-scrollbar::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 6px;
}

.fake-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.nav-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.nav-card :deep(.el-card__header) {
  border-bottom: none;
}

.nav-card :deep(.el-button) {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  transition: all 0.3s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-card :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 3px 3px rgba(0, 0, 0, 0.15);
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

.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 预览日历视图样式 */
.preview-calendar-container {
  display: flex;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  max-height: 600px;
  overflow-y: auto;
}

.time-column {
  width: 80px;
  flex-shrink: 0;
  border-right: 1px solid #dcdfe6;
  background-color: #f5f7fa;
}

.time-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border-bottom: 1px solid #dcdfe6;
  background-color: #eef1f6;
}

.time-cell {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #dcdfe6;
  font-size: 12px;
  color: #606266;
}

.dates-column {
  flex: 1;
  overflow-x: auto;
}

.date-header-row {
  display: flex;
  border-bottom: 1px solid #dcdfe6;
  background-color: #eef1f6;
}

.date-header {
  flex: 1;
  min-width: 120px;
  padding: 10px 5px;
  text-align: center;
  border-right: 1px solid #dcdfe6;
}

.date-name {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  margin-bottom: 5px;
}

.date-num {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.date-num.is-today {
  background-color: #409eff;
  color: white;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  line-height: 30px;
  margin: 0 auto;
}

.time-row {
  display: flex;
  border-bottom: 1px solid #dcdfe6;
}

.schedule-cell {
  flex: 1;
  min-width: 120px;
  min-height: 100px;
  border-right: 1px solid #dcdfe6;
  padding: 5px;
  position: relative;
}

.preview-schedule-item {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 5px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  border: 2px solid transparent;
}

.preview-schedule-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preview-schedule-item.has-conflict {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.preview-schedule-item.is-selected {
  border-color: #ffd700;
  box-shadow: 0 0 10px rgba(255, 215, 0, 0.6);
}

.schedule-checkbox {
  position: absolute;
  top: 5px;
  right: 5px;
  z-index: 10;
}

.schedule-checkbox :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #ffd700;
  border-color: #ffd700;
}

.schedule-title {
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-info {
  font-size: 11px;
  opacity: 0.9;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-time {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.95;
}

.conflict-badge {
  position: absolute;
  top: 5px;
  left: 5px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.schedule-edit-btn {
  position: absolute;
  bottom: 5px;
  right: 5px;
  z-index: 10;
}

.schedule-edit-btn .el-button {
  padding: 2px 6px;
  font-size: 11px;
}

.student-detail-info {
  padding: 8px;
  min-width: 250px;
}

.student-detail-info .info-item {
  margin-bottom: 6px;
  line-height: 1.5;
  font-size: 13px;
}

.student-detail-info .info-item:last-child {
  margin-bottom: 0;
}

.student-detail-info strong {
  color: #606266;
  display: inline-block;
  min-width: 100px;
}

@media (max-width: 768px) {
  .nav-card :deep(.el-row) {
    flex-wrap: wrap;
  }
  
  .nav-card :deep(.el-col) {
    margin-bottom: 10px;
  }
  
  .nav-card :deep(.el-button) {
    font-size: 10px;
    padding: 4px 6px;
    flex: 0 0 auto;
    min-width: auto;
    white-space: normal;
    line-height: 1.2;
    width: 100%;
  }
  
  .nav-card :deep(.el-button span) {
    display: inline;
  }
  
  .header-actions {
    gap: 6px;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .filter-bar {
    gap: 6px;
    flex-wrap: wrap;
  }
  
  .filter-bar :deep(.el-select),
  .filter-bar :deep(.el-date-picker) {
    width: 100% !important;
    max-width: none;
  }
  
  .el-table {
    font-size: 11px;
    overflow-x: auto;
  }
  
  .el-table :deep(.el-table__cell) {
    padding: 6px 3px;
  }
  
  .el-table :deep(.el-table__header-wrapper) {
    overflow-x: auto;
  }
  
  .el-table :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
  
  .el-table :deep(.el-table__fixed-right) {
    width: 120px !important;
  }
  
  .el-table :deep(.el-table__fixed-right-patch) {
    width: 120px !important;
  }
  
  .el-pagination {
    flex-wrap: wrap;
    justify-content: center !important;
  }
  
  .el-pagination :deep(.el-pagination__total),
  .el-pagination :deep(.el-pagination__sizes),
  .el-pagination :deep(.el-pagination__jump) {
    margin: 5px 0;
  }
  
  .el-pagination :deep(.btn-prev),
  .el-pagination :deep(.btn-next),
  .el-pagination :deep(.el-pager li) {
    min-width: 28px;
    height: 28px;
    line-height: 28p;
    font-size: 12px;
  }
}
</style>