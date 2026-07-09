// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="dashboard">
    <el-card class="header-card" style="margin-bottom: 10px;">
      <div class="header-actions">
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_audit')" type="warning" @click="showLogsDialog">
          <el-icon><Document /></el-icon>
          {{ t('dashboard.logs') }}
        </el-button>
        <el-tooltip v-if="currentUser && currentUser.role === 'super_admin' && !hasFeature(FEATURES.DATABASE_MANAGEMENT)" :content="t('dashboard.databaseManagementTip')" placement="bottom">
          <el-button type="info" plain disabled style="opacity:0.6">
            <el-icon><Setting /></el-icon>
            {{ t('dashboard.databaseManagement') }}
          </el-button>
        </el-tooltip>
        <el-button v-if="currentUser && currentUser.role === 'super_admin' && hasFeature(FEATURES.DATABASE_MANAGEMENT)" type="danger" @click="goToDatabaseManagement">
          <el-icon><Setting /></el-icon>
          {{ t('dashboard.databaseManagement') }}
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="info" @click="showSiteSettingsDialog">
          <el-icon><Setting /></el-icon>
          {{ t('dashboard.siteSettings') }}
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="success" @click="goToPage('/admin/license')">
          <el-icon><Key /></el-icon>
          {{ t('dashboard.licenseManagement') }}
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="primary" @click="goToPage('/admin/users')">
          <el-icon><User /></el-icon>
          {{ t('dashboard.userManagement') }}
        </el-button>
        <el-button type="warning" @click="showPasswordDialog">
          <el-icon><Lock /></el-icon>
          {{ t('dashboard.changePassword') }}
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="warning" @click="showPasswordResetRequests">
          <el-icon><Lock /></el-icon>
          {{ t('dashboard.handlePasswordReset') }}
        </el-button>
        <el-button type="danger" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          {{ t('dashboard.logout') }}
        </el-button>
      </div>
    </el-card>

    <el-dialog v-model="passwordResetRequestsDialogVisible" :title="t('dashboard.handlePasswordReset')" width="800px" draggable>
      <el-table :data="passwordResetRequests" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" :label="t('dashboard.username')" width="120" />
        <el-table-column prop="status" :label="t('dashboard.statusText')" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="t('dashboard.applicationTime')" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" size="small" @click="showResetPasswordDialog(row)">{{ t('dashboard.resetPassword') }}</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="danger" @click="rejectPasswordReset(row)">{{ t('dashboard.reject') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="resetPasswordDialogVisible" :title="t('dashboard.resetPasswordTitle2')" width="400px">
      <el-form :model="resetPasswordForm" :rules="resetPasswordRules" ref="resetPasswordFormRef" label-width="80px">
        <el-form-item :label="t('dashboard.newPassword')" prop="new_password">
          <el-input v-model="resetPasswordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('dashboard.confirmPassword')" prop="confirm_password">
          <el-input v-model="resetPasswordForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleResetPassword">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-row :gutter="5">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="(currentUser?.role === 'course_admin' || currentUser?.role === 'teaching_assistant') ? t('dashboard.relatedCourses') : t('dashboard.totalCourses')" :value="stats.courses">
            <template #prefix>
              <el-icon><Reading /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="(currentUser?.role === 'course_admin' || currentUser?.role === 'teaching_assistant') ? t('dashboard.relatedTeachers') : t('dashboard.totalTeachers')" :value="stats.teachers">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="(currentUser?.role === 'course_admin' || currentUser?.role === 'teaching_assistant') ? t('dashboard.relatedStudents') : t('dashboard.totalStudents')" :value="stats.students">
            <template #prefix>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="(currentUser?.role === 'course_admin' || currentUser?.role === 'teaching_assistant') ? t('dashboard.relatedRooms') : t('dashboard.totalRooms')" :value="stats.rooms">
            <template #prefix>
              <el-icon><OfficeBuilding /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="5" style="margin-top: 10px;">
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic :title="(currentUser?.role === 'course_admin' || currentUser?.role === 'teaching_assistant') ? t('dashboard.relatedClasses') : t('dashboard.totalClasses')" :value="stats.classes">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic :title="(currentUser?.role === 'course_admin' || currentUser?.role === 'teaching_assistant') ? t('dashboard.relatedSchedules') : t('dashboard.totalSchedules')" :value="stats.schedules">
            <template #prefix>
              <el-icon><Calendar /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic :title="(currentUser?.role === 'course_admin' || currentUser?.role === 'teaching_assistant') ? t('dashboard.relatedConflicts') : t('dashboard.totalConflicts')" :value="stats.conflicts">
            <template #prefix>
              <el-icon><Warning /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 10px;">
      <el-row :gutter="10">
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="success" @click="goToPage('/admin/courses')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><Reading /></el-icon>
            {{ t('dashboard.courseManagement') }}
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="primary" @click="goToPage('/admin/teachers')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><User /></el-icon>
            {{ t('dashboard.teacherManagement') }}
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="warning" @click="goToPage('/admin/students')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><UserFilled /></el-icon>
            {{ t('dashboard.studentManagement') }}
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="danger" @click="goToPage('/admin/classes')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><User /></el-icon>
            {{ t('dashboard.classManagement') }}
          </el-button>
        </el-col>
      </el-row>
      <el-row :gutter="10">
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="primary" @click="goToPage('/admin/rooms')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><OfficeBuilding /></el-icon>
            {{ t('dashboard.roomManagement') }}
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="danger" @click="goToPage('/admin/leaves')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><DocumentDelete /></el-icon>
            {{ t('dashboard.leaveManagement') }}
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="info" @click="goToPage('/admin/conditions')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><Setting /></el-icon>
            {{ t('dashboard.conditionManagement') }}
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" type="success" @click="goToPage('/admin/schedules')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><Calendar /></el-icon>
            {{ t('dashboard.scheduleManagement') }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 添加日历视图 -->
    <CalendarView v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin' || currentUser.role === 'teaching_assistant')" />

    <!-- 系统日志对话框 -->
    <el-dialog v-model="logsDialogVisible" :title="t('dashboard.systemLogs')" width="1200px" draggable>
      <el-tabs v-model="logsActiveTab">
        <el-tab-pane :label="t('dashboard.currentLogs')" name="current">
          <div style="margin-bottom: 15px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
            <el-date-picker
              v-model="logsFilters.start_date"
              type="date"
              :placeholder="t('dashboard.startDate')"
              value-format="YYYY-MM-DD"
              style="width: 150px"
              @change="fetchLogs"
            />
            <el-date-picker
              v-model="logsFilters.end_date"
              type="date"
              :placeholder="t('dashboard.endDate')"
              value-format="YYYY-MM-DD"
              style="width: 150px"
              @change="fetchLogs"
            />
            <el-input
              v-model="logsFilters.user"
              :placeholder="t('dashboard.username')"
              style="width: 150px"
              clearable
              @clear="fetchLogs"
              @keyup.enter="fetchLogs"
            />
            <el-select
              v-model="logsFilters.level"
              :placeholder="t('dashboard.logLevel')"
              style="width: 130px"
              clearable
              @change="fetchLogs"
            >
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
            <el-input
              v-model="logsFilters.search"
              :placeholder="t('dashboard.contentSearch')"
              style="width: 200px"
              clearable
              @clear="fetchLogs"
              @keyup.enter="fetchLogs"
            />
            <el-button type="primary" @click="fetchLogs">
              <el-icon><Search /></el-icon>
              {{ t('common.search') }}
            </el-button>
            <el-button @click="resetLogsFilters">
              <el-icon><Refresh /></el-icon>
              {{ t('common.reset') }}
            </el-button>
            <div style="flex-grow: 1;"></div>
            <el-button type="success" @click="handleBackupLogs" :loading="logsBackupLoading">
              <el-icon><Download /></el-icon>
              {{ t('dashboard.backupLogs') }}
            </el-button>
            <el-button type="danger" @click="handleClearLogsConfirm">
              <el-icon><Delete /></el-icon>
              {{ t('dashboard.clearLogs') }}
            </el-button>
          </div>

          <div v-if="logsStats" style="margin-bottom: 10px; font-size: 13px; color: #909399;">
            {{ t('dashboard.totalLogs', { n: logsPagination.total }) }}
            <span v-if="logsStats.level_stats" style="margin-left: 10px;">
              <span v-for="(count, lvl) in logsStats.level_stats" :key="lvl" style="margin-right: 8px;">
                <el-tag size="small" :type="lvl === 'ERROR' ? 'danger' : lvl === 'WARNING' ? 'warning' : lvl === 'DEBUG' ? 'info' : 'success'" style="margin-right: 2px;">{{ lvl }}</el-tag>{{ count }}
              </span>
            </span>
          </div>
          
          <el-table :data="logs" v-loading="logsLoading" border>
            <el-table-column prop="id" label="ID" width="65" />
            <el-table-column prop="timestamp" :label="t('dashboard.utcTime')" width="180" />
            <el-table-column prop="level" :label="t('dashboard.level')" width="85">
              <template #default="{ row }">
                <el-tag :type="row.level === 'ERROR' ? 'danger' : row.level === 'WARNING' ? 'warning' : row.level === 'DEBUG' ? 'info' : 'success'">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" :label="t('dashboard.content')" />
            <el-table-column prop="user" :label="t('dashboard.operatingUser')" width="100" />
          </el-table>
          
          <el-pagination
            v-model:current-page="logsPagination.currentPage"
            :page-size="logsPagination.pageSize"
            :total="logsPagination.total"
            @current-change="handleLogsPageChange"
            layout="total, prev, pager, next"
            style="margin-top: 20px; justify-content: center"
          />
        </el-tab-pane>

        <el-tab-pane :label="t('dashboard.archiveLogs')" name="archive">
          <div v-if="!archiveViewingFile">
            <el-table :data="archiveList" v-loading="archiveListLoading" border style="margin-bottom: 15px;">
              <el-table-column prop="filename" :label="t('dashboard.archiveFile')" min-width="280" />
              <el-table-column :label="t('dashboard.size')" width="120">
                <template #default="{ row }">
                  {{ formatFileSize(row.size) }}
                </template>
              </el-table-column>
              <el-table-column prop="created_at" :label="t('dashboard.archiveTime')" width="200" />
              <el-table-column :label="t('common.operation')" width="220" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" @click="viewArchiveFile(row.filename)">
                    <el-icon><View /></el-icon> {{ t('common.view') }}
                  </el-button>
                  <el-button type="success" size="small" @click="downloadArchiveFile(row.filename)">
                    <el-icon><Download /></el-icon> {{ t('common.download') }}
                  </el-button>
                  <el-button type="danger" size="small" @click="deleteArchiveFile(row.filename)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!archiveListLoading && archiveList.length === 0" :description="t('dashboard.noArchiveLogs')" />
          </div>

          <div v-else>
            <div style="margin-bottom: 15px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
              <el-button @click="closeArchiveView">
                <el-icon><ArrowLeft /></el-icon> {{ t('dashboard.backToArchiveList') }}
              </el-button>
              <span style="font-size: 14px; color: #606266;">
                {{ t('dashboard.viewing') }}: <strong>{{ archiveViewingFile }}</strong>
                <span style="color: #909399; margin-left: 8px;">{{ t('dashboard.totalCount', { n: archivePagination.total }) }}</span>
              </span>
              <div style="flex-grow: 1;"></div>
              <el-select v-model="archiveFilterLevel" :placeholder="t('dashboard.levelFilter')" style="width: 120px" clearable @change="viewArchiveFile(archiveViewingFile)">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
              </el-select>
              <el-input v-model="archiveFilterSearch" :placeholder="t('dashboard.contentSearch')" style="width: 180px" clearable @keyup.enter="viewArchiveFile(archiveViewingFile)" />
              <el-button type="primary" @click="viewArchiveFile(archiveViewingFile)">{{ t('common.search') }}</el-button>
            </div>

            <el-table :data="archiveLogs" v-loading="archiveLogsLoading" border>
              <el-table-column prop="id" label="ID" width="65" />
              <el-table-column prop="timestamp" :label="t('dashboard.time')" width="200" />
              <el-table-column prop="level" :label="t('dashboard.level')" width="85">
                <template #default="{ row }">
                  <el-tag :type="row.level === 'ERROR' ? 'danger' : row.level === 'WARNING' ? 'warning' : row.level === 'DEBUG' ? 'info' : 'success'">
                    {{ row.level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="message" :label="t('dashboard.content')" />
              <el-table-column prop="user" :label="t('dashboard.operatingUser')" width="100" />
            </el-table>

            <el-pagination
              v-model:current-page="archivePagination.currentPage"
              :page-size="archivePagination.pageSize"
              :total="archivePagination.total"
              @current-change="handleArchivePageChange"
              layout="total, prev, pager, next"
              style="margin-top: 20px; justify-content: center"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" :title="t('dashboard.changePassword')" width="500px" draggable>
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item :label="t('dashboard.oldPassword')" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('dashboard.newPassword')" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('dashboard.confirmNewPassword')" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handlePasswordChange">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 站点参数对话框 -->
    <el-dialog v-model="siteSettingsDialogVisible" :title="t('dashboard.siteGlobalSettings')" width="800px" draggable>
        <el-tabs type="border-card">
          <el-tab-pane :label="t('dashboard.projectIntro')">
            <div style="padding: 10px 0;">
              <el-descriptions :column="1" border>
                <el-descriptions-item :label="t('dashboard.projectVersionLabel')">
                  <el-tag type="primary" size="large">V1.0</el-tag>
                </el-descriptions-item>
                <el-descriptions-item :label="t('dashboard.developerLabel')">
                  <span style="font-size: 15px; font-weight: 500;">{{ t('dashboard.developerName') }}</span>
                </el-descriptions-item>
              </el-descriptions>

              <el-divider content-position="left">{{ t('dashboard.featureIntroLabel') }}</el-divider>

              <div style="line-height: 2; color: #303133; font-size: 14px;">
                <p style="margin-bottom: 12px;">
                  {{ t('dashboard.systemOverview') }}
                  <el-tag type="success" size="small" style="margin: 0 2px;">{{ t('dashboard.defaultAuth') }}</el-tag>{{ t('dashboard.defaultAuthReady') }}
                  <el-tag type="warning" size="small" style="margin: 0 2px;">{{ t('dashboard.advancedAuth') }}</el-tag>{{ t('dashboard.advancedAuthActivate') }}
                </p>

                <h4 style="margin: 16px 0 8px; color: #409eff;">
                  <el-tag type="success" size="small">{{ t('dashboard.defaultAuth') }}</el-tag> {{ t('dashboard.defaultAuthBasicFeatures') }}
                </h4>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureCourseScheduling') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureCourseManagement') }}</li>
                        <li>{{ t('dashboard.featureManualScheduling') }}</li>
                        <li>{{ t('dashboard.featureScheduleStatusTracking') }}</li>
                        <li>{{ t('dashboard.featureStudentAttendance') }}</li>
                        <li>{{ t('dashboard.featureDualView') }}</li>
                        <li>{{ t('dashboard.featureConstraintManagement') }}</li>
                        <li>{{ t('dashboard.featureHolidayManagement') }}</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureTeacherStudent') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureTeacherManagement') }}</li>
                        <li>{{ t('dashboard.featureStudentManagement') }}</li>
                        <li>{{ t('dashboard.featureClassManagement') }}</li>
                        <li>{{ t('dashboard.featureRoomManagement') }}</li>
                        <li>{{ t('dashboard.featureLeaveManagement') }}</li>
                        <li>{{ t('dashboard.featureTeacherVisibility') }}</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureSystemManagement') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureUserManagement') }}</li>
                        <li>{{ t('dashboard.featureTeacherRoleAuth') }}</li>
                        <li>{{ t('dashboard.featureLdapAuth') }}</li>
                        <li>{{ t('dashboard.featureOpenRegistration') }}</li>
                        <li>{{ t('dashboard.featureLoginTimeout') }}</li>
                        <li>{{ t('dashboard.featurePasswordReset') }}</li>
                        <li>{{ t('dashboard.featureEmailNotification') }}</li>
                        <li>{{ t('dashboard.featureSystemLogs') }}</li>
                        <li>{{ t('dashboard.featureSiteInfo') }}</li>
                        <li>{{ t('dashboard.featureI18n') }}</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureScheduleManagement') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureManualScheduleCreate') }}</li>
                        <li>{{ t('dashboard.featureScheduleQuery') }}</li>
                        <li>{{ t('dashboard.featureLeaveAdjustment') }}</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>

                <h4 style="margin: 20px 0 8px; color: #E6A23C;">
                  <el-tag type="warning" size="small">{{ t('dashboard.advancedAuth') }}</el-tag> {{ t('dashboard.advancedAuthEnhancedFeatures') }}
                </h4>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureSmartScheduling') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureGeneticAlgorithm') }}</li>
                        <li>{{ t('dashboard.featureBacktrackAlgorithm') }}</li>
                        <li>{{ t('dashboard.featureHybridAlgorithm') }}</li>
                        <li>{{ t('dashboard.featureSchedulePreview') }}</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureFeeManagement') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureFeeItemManagement') }}</li>
                        <li>{{ t('dashboard.featurePaymentRecord') }}</li>
                        <li>{{ t('dashboard.featureRefundManagement') }}</li>
                        <li>{{ t('dashboard.featurePaymentReminder') }}</li>
                        <li>{{ t('dashboard.featureFeeReportExport') }}</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureGradeManagement') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureGradeEntry') }}</li>
                        <li>{{ t('dashboard.featureGradeTracking') }}</li>
                        <li>{{ t('dashboard.featureGradeTrendChart') }}</li>
                        <li>{{ t('dashboard.featureGradeMultiDimension') }}</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureEvaluationManagement') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureEvaluationTemplate') }}</li>
                        <li>{{ t('dashboard.featureComprehensivePortrait') }}</li>
                        <li>{{ t('dashboard.featureSubjectPortrait') }}</li>
                        <li>{{ t('dashboard.featureEvaluationPeriod') }}</li>
                        <li>{{ t('dashboard.featureRadarChart') }}</li>
                        <li>{{ t('dashboard.featureEvaluationTeacher') }}</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureWechatNotification') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureWechatWebhook') }}</li>
                        <li>{{ t('dashboard.featureScheduleReminder') }}</li>
                        <li>{{ t('dashboard.featureManagementNotification') }}</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureSmartCommand') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureNaturalLanguageParse') }}</li>
                        <li>{{ t('dashboard.featureDualModeParse') }}</li>
                        <li>{{ t('dashboard.featureCommandExampleManagement') }}</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureDashboardView') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureKPIDashboard') }}</li>
                        <li>{{ t('dashboard.featureVisualCharts') }}</li>
                        <li>{{ t('dashboard.featureConversionFunnel') }}</li>
                        <li>{{ t('dashboard.featureFullscreenExport') }}</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureFloatingButton') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureFloatingEntry') }}</li>
                        <li>{{ t('dashboard.featureDraggableSnap') }}</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>{{ t('dashboard.featureDatabaseManagement') }}</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>{{ t('dashboard.featureManualBackup') }}</li>
                        <li>{{ t('dashboard.featureAutoBackup') }}</li>
                        <li>{{ t('dashboard.featureDatabaseRestore') }}</li>
                        <li>{{ t('dashboard.featureBackupFileManagement') }}</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.siteInfoTab')">
            <el-form :model="siteSettingsForm" :rules="siteSettingsRules" ref="siteSettingsFormRef" label-width="120px">
                <el-form-item :label="t('dashboard.siteName')" prop="site_name">
                  <el-input v-model="siteSettingsForm.site_name" :placeholder="t('dashboard.siteNamePlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('dashboard.contactPerson')">
                  <el-input v-model="siteSettingsForm.contact_person" :placeholder="t('dashboard.contactPersonPlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('dashboard.contactPhone')">
                  <el-input v-model="siteSettingsForm.contact_phone" :placeholder="t('dashboard.contactPhonePlaceholder2')" />
                </el-form-item>
                <el-form-item :label="t('dashboard.contactEmail')">
                  <el-input v-model="siteSettingsForm.contact_email" :placeholder="t('dashboard.contactEmailPlaceholder2')" />
                </el-form-item>
                <el-form-item :label="t('dashboard.contactWechat')">
                  <el-input v-model="siteSettingsForm.contact_wechat" :placeholder="t('dashboard.contactWechatPlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('dashboard.siteIpLabel')" prop="site_url">
                  <el-input v-model="siteSettingsForm.site_url" :placeholder="t('dashboard.siteIpPlaceholder')">
                    <template #prepend>http://</template>
                    <template #append>:{{ backendPort }}</template>
                  </el-input>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.siteIpTip') }}
                  </div>
                </el-form-item>
                <el-form-item :label="t('dashboard.siteLogo')" prop="site_logo">
                  <el-upload
                      class="logo-uploader"
                      action="/api/upload"
                      :show-file-list="false"
                      :on-success="handleLogoUploadSuccess"
                      :before-upload="beforeLogoUpload"
                      accept="image/*"
                      :headers="uploadHeaders"
                      name="file"
                    >
                      <img v-if="siteSettingsForm.site_logo" :src="getFullLogoUrl(siteSettingsForm.site_logo)" class="logo-preview" />
                      <el-icon v-else class="logo-placeholder"><Plus /></el-icon>
                  </el-upload>
                </el-form-item>
                <el-form-item :label="t('dashboard.orgWebsiteLink')">
                  <el-input v-model="siteSettingsForm.organization_website" :placeholder="t('dashboard.orgWebsitePlaceholder')" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.orgWebsiteTip') }}
                  </div>
                </el-form-item>
                <el-form-item :label="t('dashboard.wechatQrcode')">
                  <el-upload
                      class="qrcode-uploader"
                      action="/api/upload"
                      :show-file-list="false"
                      :on-success="(res) => handleQrcodeUploadSuccess(res, 'wechat')"
                      :before-upload="beforeQrcodeUpload"
                      accept="image/*"
                      :headers="uploadHeaders"
                      name="file"
                    >
                      <img v-if="siteSettingsForm.wechat_qrcode" :src="getFullLogoUrl(siteSettingsForm.wechat_qrcode)" class="qrcode-preview" />
                      <el-icon v-else class="qrcode-placeholder"><Plus /></el-icon>
                  </el-upload>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.wechatQrcodeTip') }}
                  </div>
                </el-form-item>
                <el-form-item :label="t('dashboard.workWechatQrcode')">
                  <el-upload
                      class="qrcode-uploader"
                      action="/api/upload"
                      :show-file-list="false"
                      :on-success="(res) => handleQrcodeUploadSuccess(res, 'work_wechat')"
                      :before-upload="beforeQrcodeUpload"
                      accept="image/*"
                      :headers="uploadHeaders"
                      name="file"
                    >
                      <img v-if="siteSettingsForm.work_wechat_qrcode" :src="getFullLogoUrl(siteSettingsForm.work_wechat_qrcode)" class="qrcode-preview" />
                      <el-icon v-else class="qrcode-placeholder"><Plus /></el-icon>
                  </el-upload>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.workWechatQrcodeTip') }}
                  </div>
                </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.teacherVisibilityTab')">
            <el-form :model="siteSettingsForm" label-width="120px">
              <el-form-item :label="t('dashboard.courseVisibility')">
                <el-switch
                  v-model="siteSettingsForm.teacher_visibility_restricted"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  <span v-if="siteSettingsForm.teacher_visibility_restricted">{{ t('dashboard.courseVisibilityTipOn') }}</span>
                  <span v-else>{{ t('dashboard.courseVisibilityTipOff') }}</span>
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.courseEditRestriction')">
                <el-switch
                  v-model="siteSettingsForm.schedule_edit_restricted"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  <span v-if="siteSettingsForm.schedule_edit_restricted">{{ t('dashboard.courseEditTipOn') }}</span>
                  <span v-else>{{ t('dashboard.courseEditTipOff') }}</span>
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.courseDeleteRestriction')">
                <el-switch
                  v-model="siteSettingsForm.schedule_delete_restricted"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  <span v-if="siteSettingsForm.schedule_delete_restricted">{{ t('dashboard.courseDeleteTipOn') }}</span>
                  <span v-else>{{ t('dashboard.courseDeleteTipOff') }}</span>
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.courseManageTeacher')">
                <el-select
                  v-model="siteSettingsForm.subject_teachers"
                  multiple
                  filterable
                  :placeholder="t('dashboard.courseManageTeacherPlaceholder')"
                  style="width: 100%"
                >
                  <el-option
                    v-for="teacher in teachers"
                    :key="teacher.id"
                    :label="teacher.name"
                    :value="teacher.id"
                  />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  {{ t('dashboard.courseManageTeacherTip') }}
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.feeManageTeacher')">
                <el-select
                  v-model="siteSettingsForm.fee_managers"
                  multiple
                  filterable
                  :placeholder="t('dashboard.feeManageTeacherPlaceholder')"
                  style="width: 100%"
                >
                  <el-option
                    v-for="teacher in teachers"
                    :key="teacher.id"
                    :label="teacher.name"
                    :value="teacher.id"
                  />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  {{ t('dashboard.feeManageTeacherTip') }}
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.gradeManageTeacher')">
                <el-select
                  v-model="siteSettingsForm.grade_managers"
                  multiple
                  filterable
                  :placeholder="t('dashboard.gradeManageTeacherPlaceholder')"
                  style="width: 100%"
                >
                  <el-option
                    v-for="teacher in teachers"
                    :key="teacher.id"
                    :label="teacher.name"
                    :value="teacher.id"
                  />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  {{ t('dashboard.gradeManageTeacherTip') }}
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.evaluationManageTeacher')">
                <el-select
                  v-model="siteSettingsForm.evaluation_managers"
                  multiple
                  filterable
                  :placeholder="t('dashboard.evaluationManageTeacherPlaceholder')"
                  style="width: 100%"
                >
                  <el-option
                    v-for="teacher in teachers"
                    :key="teacher.id"
                    :label="teacher.name"
                    :value="teacher.id"
                  />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  {{ t('dashboard.evaluationManageTeacherTip') }}
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.operationManageTeacher')">
                <el-select
                  v-model="siteSettingsForm.operation_managers"
                  multiple
                  filterable
                  :placeholder="t('dashboard.operationManageTeacherPlaceholder')"
                  style="width: 100%"
                >
                  <el-option
                    v-for="teacher in teachers"
                    :key="teacher.id"
                    :label="teacher.name"
                    :value="teacher.id"
                  />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon>
                  {{ t('dashboard.operationManageTeacherTip') }}
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.courseConfigTab')">
            <el-form :model="siteSettingsForm" label-width="140px">
              <el-form-item :label="t('dashboard.hoursPerLesson')">
                <el-input-number
                  v-model="siteSettingsForm.hours_per_lesson"
                  :min="0.1"
                  :max="10"
                  :step="0.1"
                  :precision="1"
                  style="width: 200px"
                />
                <span style="margin-left: 10px; color: #909399;">{{ t('dashboard.hoursUnit') }}</span>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.hoursPerLessonTip') }}
                </div>
              </el-form-item>
              <el-divider content-position="left">{{ t('dashboard.gradeOptionsConfig') }}</el-divider>
              <el-form-item :label="t('dashboard.gradeList')">
                <div style="width: 100%;">
                  <draggable
                    :list="siteSettingsForm.grade_options"
                    item-key="_drag_idx"
                    handle=".grade-drag-handle"
                    animation="200"
                    ghost-class="ghost"
                  >
                    <template #item="{ index }">
                      <div style="display: flex; align-items: center; margin-bottom: 8px; background: #fff; border: 1px solid #ebeef5; border-radius: 4px; padding: 4px 8px;">
                        <el-icon class="grade-drag-handle" style="cursor: grab; margin-right: 8px; color: #909399;"><Rank /></el-icon>
                        <el-tag type="info" style="margin-right: 8px; min-width: 30px; text-align: center;">{{ index + 1 }}</el-tag>
                        <el-input v-model="siteSettingsForm.grade_options[index]" :placeholder="t('dashboard.gradeNamePlaceholder')" style="flex: 1;" />
                        <el-button type="danger" :icon="Delete" circle style="margin-left: 8px;" @click="removeGradeOption(index)" />
                      </div>
                    </template>
                  </draggable>
                  <el-button type="primary" :icon="Plus" @click="addGradeOption">{{ t('dashboard.addGrade') }}</el-button>
                  <el-button @click="resetGradeOptions">{{ t('dashboard.resetDefault') }}</el-button>
                </div>
                <div style="margin-top: 5px; font-size: 12px; color: #909399; width: 100%;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.gradeOrderTip') }}
                </div>
              </el-form-item>
              <el-divider content-position="left">{{ t('dashboard.examStageConfig') }}</el-divider>
              <el-form-item :label="t('dashboard.examStageList')">
                <div style="width: 100%;">
                  <draggable
                    :list="siteSettingsForm.exam_stages"
                    item-key="_drag_idx"
                    handle=".exam-drag-handle"
                    animation="200"
                    ghost-class="ghost"
                  >
                    <template #item="{ index }">
                      <div style="display: flex; align-items: center; margin-bottom: 8px; background: #fff; border: 1px solid #ebeef5; border-radius: 4px; padding: 4px 8px;">
                        <el-icon class="exam-drag-handle" style="cursor: grab; margin-right: 8px; color: #909399;"><Rank /></el-icon>
                        <el-tag type="info" style="margin-right: 8px; min-width: 30px; text-align: center;">{{ index + 1 }}</el-tag>
                        <el-input v-model="siteSettingsForm.exam_stages[index]" :placeholder="t('dashboard.examStageNamePlaceholder')" style="flex: 1;" />
                        <el-button type="danger" :icon="Delete" circle style="margin-left: 8px;" @click="removeExamStage(index)" />
                      </div>
                    </template>
                  </draggable>
                  <el-button type="primary" :icon="Plus" @click="addExamStage">{{ t('dashboard.addExamStage') }}</el-button>
                  <el-button @click="resetExamStages">{{ t('dashboard.resetDefault') }}</el-button>
                </div>
                <div style="margin-top: 5px; font-size: 12px; color: #909399; width: 100%;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.examStageOrderTip') }}
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.emailTab')">
            <div style="margin-bottom: 20px; color: #606266;">
              {{ t('dashboard.configDescPrefix') }}<strong>{{ t('dashboard.emailConfigDesc') }}</strong>
            </div>
            <el-divider content-position="left">{{ t('dashboard.smtpConfig') }}</el-divider>
            <el-form :model="emailConfig" :rules="emailConfigRules" ref="emailConfigFormRef" label-width="160px">
              <el-form-item :label="t('dashboard.smtpServer')" prop="smtp_host">
                <el-input v-model="emailConfig.smtp_host" :placeholder="t('dashboard.smtpHostPlaceholder')" />
              </el-form-item>
              <el-form-item :label="t('dashboard.smtpPort')" prop="smtp_port">
                <el-input-number v-model="emailConfig.smtp_port" :min="1" :max="65535" :placeholder="t('dashboard.smtpPortPlaceholder')" />
              </el-form-item>
              <el-form-item :label="t('dashboard.smtpUser')" prop="smtp_user">
                <el-input v-model="emailConfig.smtp_user" :placeholder="t('dashboard.smtpUserPlaceholder')" />
              </el-form-item>
              <el-form-item :label="t('dashboard.smtpPassword')" prop="smtp_password">
                <el-input v-model="emailConfig.smtp_password" type="password" show-password :placeholder="t('dashboard.smtpPasswordPlaceholder')" />
              </el-form-item>
              <el-form-item :label="t('dashboard.smtpFromName')" prop="smtp_from_name">
                <el-input v-model="emailConfig.smtp_from_name" :placeholder="t('dashboard.smtpFromNamePlaceholder')" />
              </el-form-item>
              <el-form-item :label="t('dashboard.useSSL')">
                <el-switch v-model="emailConfig.smtp_ssl" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="testingEmail" @click="testEmailConfig">{{ t('dashboard.testEmailSend') }}</el-button>
              </el-form-item>
            </el-form>
            <el-divider content-position="left">{{ t('dashboard.scheduleReminderConfig') }}</el-divider>
            <el-form label-width="160px">
              <el-form-item :label="t('dashboard.enableEmailReminder')">
                <el-switch v-model="emailNotificationSettings.enabled" />
              </el-form-item>
              <el-form-item :label="t('dashboard.reminderTime')">
                <el-checkbox-group v-model="emailNotificationSettings.reminders">
                  <el-checkbox value="morning">{{ t('dashboard.morningReminder') }}</el-checkbox>
                  <el-checkbox value="evening">{{ t('dashboard.eveningReminder') }}</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
              <el-form-item :label="t('dashboard.recipients')">
                <el-checkbox-group v-model="emailNotificationSettings.recipients">
                  <el-checkbox value="teachers">{{ t('dashboard.teacher') }}</el-checkbox>
                  <el-checkbox value="students">{{ t('dashboard.student') }}</el-checkbox>
                </el-checkbox-group>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.emailRecipientsTip') }}
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.wechatTab')">
            <div v-if="!hasFeature(FEATURES.WECHAT_NOTIFY)" style="display: flex; align-items: center; justify-content: center; min-height: 300px; color: #909399;">
              <div style="text-align: center;">
                <el-icon :size="48"><Lock /></el-icon>
                <p style="margin-top: 12px; font-size: 16px;">{{ t('dashboard.wechatLicenseRequired') }}</p>
                <p>{{ t('dashboard.wechatLicenseActivate') }}</p>
              </div>
            </div>
            <template v-else>
            <div style="margin-bottom: 20px; color: #606266;">
              {{ t('dashboard.configDescPrefix') }}<strong>{{ t('dashboard.wechatConfigDesc') }}</strong>
            </div>

            <el-divider content-position="left">{{ t('dashboard.managementNotification') }}</el-divider>
            <el-form label-width="160px">
              <el-form-item :label="t('dashboard.managementGroup')">
                <div style="display: flex; gap: 10px;">
                  <el-input v-model="wechatConfig.fee_alert[0]" :placeholder="t('dashboard.webhookPlaceholder')" />
                  <el-button type="primary" :loading="testingUrl === 'fee_0'" @click="testSingleUrl('fee_alert', 0)">{{ t('dashboard.testButton') }}</el-button>
                </div>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">{{ t('dashboard.scheduleReminderMethod') }}</el-divider>
            <el-form label-width="160px">
              <el-form-item :label="t('dashboard.reminderTime')">
                <el-checkbox-group v-model="notificationSettings.reminders">
                  <el-checkbox value="morning">{{ t('dashboard.morningReminder') }}</el-checkbox>
                  <el-checkbox value="evening">{{ t('dashboard.eveningReminder') }}</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">{{ t('dashboard.teacherInfoGroup') }}</el-divider>
            <el-form label-width="160px">
              <el-form-item :label="t('dashboard.teacherGroupLabel')">
                <div v-for="(url, index) in (wechatConfig.schedule_arrange.default || [])" :key="'d'+index" style="display: flex; gap: 10px; margin-bottom: 5px;">
                  <el-input v-model="wechatConfig.schedule_arrange.default[index]" :placeholder="t('dashboard.teacherWebhookPlaceholder')" />
                  <el-button type="primary" :loading="testingUrl === `schedule_arrange_default_${index}`" @click="testSingleUrl('schedule_arrange', 'default', index)">{{ t('dashboard.testButton') }}</el-button>
                  <el-button type="danger" size="small" @click="removeUrl('schedule_arrange', 'default', index)">{{ t('common.delete') }}</el-button>
                </div>
                <el-button size="small" @click="addUrl('schedule_arrange', 'default')">{{ t('dashboard.addTeacherGroup') }}</el-button>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">{{ t('dashboard.classInfoGroup') }}</el-divider>
            <el-form label-width="160px">
              <el-form-item :label="t('dashboard.selectClasses')">
                <el-select
                  v-model="notificationSettings.enabled_classes"
                  multiple
                  filterable
                  :placeholder="t('dashboard.selectWechatClassesPlaceholder')"
                  style="width: 100%"
                >
                  <el-option
                    v-for="c in classes"
                    :key="c.id"
                    :label="`${c.code} - ${c.name}`"
                    :value="c.id"
                  >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div v-if="getActiveClassStudents(c.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('dashboard.activeStudentsLabel') }}</div>
                          <div v-for="student in getActiveClassStudents(c.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getInactiveClassStudents(c.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('dashboard.inactiveStudentsLabel') }}</div>
                          <div v-for="student in getInactiveClassStudents(c.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getActiveClassStudents(c.id).length === 0 && getInactiveClassStudents(c.id).length === 0">
                          {{ t('dashboard.noStudentsLabel') }}
                        </div>
                        <div v-if="getClassTeachers(c.id).length > 0" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                          <div style="font-weight: bold; margin-bottom: 8px; color: #409EFF;">{{ t('dashboard.classTeachersLabel') }}</div>
                          <div v-for="teacher in getClassTeachers(c.id)" :key="teacher.id" style="margin-bottom: 4px;">
                            {{ teacher.name }}
                            <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                          </div>
                        </div>
                        <div v-else style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                          <div style="color: #999;">{{ t('dashboard.noTeachersLabel') }}</div>
                        </div>
                      </template>
                      <span>{{ c.code }} - {{ c.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.wechatClassTip') }}
                </div>
              </el-form-item>
            </el-form>
            </template>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.aiConfigTab')">
            <div v-if="!hasFeature(FEATURES.SMART_COMMAND)" style="display: flex; align-items: center; justify-content: center; min-height: 300px; color: #909399;">
              <div style="text-align: center;">
                <el-icon :size="48"><Lock /></el-icon>
                <p style="margin-top: 12px; font-size: 16px;">{{ t('dashboard.aiLicenseRequired') }}</p>
                <p>{{ t('dashboard.wechatLicenseActivate') }}</p>
              </div>
            </div>
            <template v-else>
            <div style="margin-bottom: 20px; color: #606266;">
              {{ t('dashboard.configDescPrefix') }}<strong>{{ t('dashboard.aiConfigDesc') }}</strong>
            </div>
            
            <el-form :model="aiConfig" label-width="160px">
              <el-form-item :label="t('dashboard.enableAI')">
                <el-switch
                  v-model="aiConfig.enabled"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.enableAITip') }}
                </div>
              </el-form-item>
              
              <el-form-item :label="t('dashboard.apiProvider')">
                <el-select v-model="aiConfig.provider" :placeholder="t('dashboard.selectAIProvider')" style="width: 100%">
                  <el-option label="DeepSeek" value="deepseek" />
                  <el-option :label="t('dashboard.qwenLabel')" value="qwen" />
                  <el-option :label="t('dashboard.ernieLabel')" value="ernie" />
                  <el-option :label="t('dashboard.zhipuLabel')" value="zhipu" />
                  <el-option label="OpenAI" value="openai" />
                  <el-option :label="t('dashboard.customLabel')" value="custom" />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.selectAIProviderTip') }}
                </div>
              </el-form-item>
              
              <el-form-item :label="t('dashboard.apiUrl')">
                <el-input 
                  v-model="aiConfig.api_url" 
                  placeholder="https://api.deepseek.com/chat/completions"
                  @blur="validateAIUrl"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 
                  {{ t('dashboard.apiUrlTip') }}

                </div>
                <div v-if="apiUrlError" style="margin-top: 5px; font-size: 12px; color: #F56C6C;">
                  {{ apiUrlError }}
                </div>
              </el-form-item>
              
              <el-form-item :label="t('dashboard.apiKey')">
                <el-input 
                  v-model="aiConfig.api_key" 
                  type="password"
                  show-password
                  :placeholder="t('dashboard.apiKeyPlaceholder')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.apiKeyTip') }}
                </div>
              </el-form-item>
              
              <el-form-item :label="t('dashboard.modelName')">
                <el-input 
                  v-model="aiConfig.model" 
                  placeholder="deepseek-v4-flash / deepseek-v4-pro"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 
                  {{ t('dashboard.modelTip') }}

                </div>
              </el-form-item>
              
              <el-form-item :label="t('dashboard.timeout')">
                <el-input-number 
                  v-model="aiConfig.timeout" 
                  :min="1" 
                  :max="60"
                  :placeholder="t('dashboard.timeoutPlaceholder')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.timeoutTip') }}
                </div>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="testAIConnection" :loading="testingAI">{{ t('dashboard.testConnection') }}</el-button>
                <el-button @click="resetAIConfig">{{ t('dashboard.resetConfig') }}</el-button>
                <el-button type="success" @click="showSmartCommandExamplesDialog">{{ t('dashboard.smartCommandExamples') }}</el-button>
              </el-form-item>
            </el-form>
            
            <el-divider content-position="left">{{ t('dashboard.aiUsageGuide') }}</el-divider>
            <div style="padding: 15px; background-color: #f5f7fa; border-radius: 4px;">
              <h4 style="margin-top: 0;">{{ t('dashboard.supportedProviders') }}</h4>
              <ul>
                <li><strong>DeepSeek</strong>：{{ t('dashboard.deepseekDesc') }}</li>
                <li><strong>{{ t('dashboard.qwenLabel') }}</strong>：{{ t('dashboard.qwenDesc') }}</li>
                <li><strong>{{ t('dashboard.ernieLabel') }}</strong>：{{ t('dashboard.ernieDesc') }}</li>
                <li><strong>{{ t('dashboard.zhipuLabel') }}</strong>：{{ t('dashboard.zhipuDesc') }}</li>
                <li><strong>OpenAI</strong>：{{ t('dashboard.openaiDesc') }}</li>
                <li><strong>{{ t('dashboard.customLabel') }}</strong>：{{ t('dashboard.customDesc') }}</li>
              </ul>
              <h4>{{ t('dashboard.deepseekConfigTitle') }}</h4>
              <ul>
                <li>{{ t('dashboard.deepseekApiUrlLabel') }}<code>https://api.deepseek.com/chat/completions</code></li>
                <li>{{ t('dashboard.deepseekRecommendedModel') }}<code>deepseek-v4-flash</code>({{ t('common.fast') }}) or <code>deepseek-v4-pro</code>({{ t('common.deepThinking') }})</li>
                <li>{{ t('dashboard.deepseekDeprecationNote') }}</li>
              </ul>
              <h4>{{ t('dashboard.qwenConfigTitle') }}</h4>
              <ul>
                <li>{{ t('dashboard.qwenApiUrlLabel') }}<code>https://dashscope.aliyuncs.com/compatible-mode/v1</code></li>
                <li>{{ t('dashboard.qwenRecommendedModel') }}<code>qwen-plus</code>({{ t('common.balanced') }}) or <code>qwen-turbo</code>({{ t('common.fast') }})</li>
                <li>{{ t('dashboard.qwenCompatibilityNote') }}</li>
              </ul>
              <h4>{{ t('dashboard.aiNotesTitle') }}</h4>
              <ul>
                <li>{{ t('dashboard.aiNote1') }}</li>
                <li>{{ t('dashboard.aiNote2') }}</li>
                <li>{{ t('dashboard.aiNote3') }}</li>
                <li>{{ t('dashboard.aiNote4') }}</li>
              </ul>
            </div>
            </template>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.userManagementTab')">
            <div style="margin-bottom: 20px; color: #606266;">
              {{ t('dashboard.configDescPrefix') }}<strong>{{ t('dashboard.userConfigDesc') }}</strong>
            </div>
            
            <el-divider content-position="left">{{ t('dashboard.loginTimeoutSection') }}</el-divider>
            <el-form :model="siteSettingsForm" label-width="180px">
              <el-form-item :label="t('dashboard.loginTimeout')">
                <el-input-number 
                  v-model="siteSettingsForm.session_timeout_minutes" 
                  :min="5" 
                  :max="43200" 
                  :step="5" 
                  style="width: 200px"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.loginTimeoutTip') }}
                </div>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">{{ t('dashboard.openRegistrationSection') }}</el-divider>
            <el-form :model="siteSettingsForm" label-width="180px">
              <el-form-item :label="t('dashboard.enableOpenRegistration')">
                <el-switch
                  v-model="siteSettingsForm.open_registration_enabled"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.openRegistrationTip') }}
                </div>
                <div v-if="siteSettingsForm.open_registration_enabled" style="margin-top: 8px; padding: 10px; background: #fdf6ec; border: 1px solid #faecd8; border-radius: 4px;">
                  <div style="color: #E6A23C; font-size: 13px; font-weight: bold;">
                    <el-icon><Warning /></el-icon> {{ t('dashboard.securityWarning') }}
                  </div>
                  <div style="color: #E6A23C; font-size: 12px; margin-top: 4px;">
                    {{ t('dashboard.openRegistrationAutoClose') }}
                  </div>
                  <div v-if="siteSettingsForm.open_registration_expiry" style="color: #909399; font-size: 12px; margin-top: 4px;">
                    {{ t('dashboard.autoCloseTime') }}{{ formatDateTime(siteSettingsForm.open_registration_expiry) }}
                  </div>
                </div>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">{{ t('dashboard.ldapSection') }}</el-divider>
            <el-form :model="siteSettingsForm" label-width="180px">
              <el-form-item :label="t('dashboard.enableLdap')">
                <el-switch
                  v-model="siteSettingsForm.ldap_enabled"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.ldapEnableTip') }}
                </div>
              </el-form-item>
              
              <template v-if="siteSettingsForm.ldap_enabled">
                <el-divider content-position="left">{{ t('dashboard.ldapServerConfig') }}</el-divider>
                
                <el-form-item :label="t('dashboard.ldapServer')" required>
                  <el-input v-model="siteSettingsForm.ldap_config.server" :placeholder="t('dashboard.ldapServerPlaceholder')" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.ldapServerTip') }}
                  </div>
                </el-form-item>
                
                <el-form-item :label="t('dashboard.ldapPort')" required>
                  <el-input-number v-model="siteSettingsForm.ldap_config.port" :min="1" :max="65535" style="width: 200px" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.ldapPortTip') }}
                  </div>
                </el-form-item>
                
                <el-form-item :label="t('dashboard.useSSLEncryption')">
                  <el-switch
                    v-model="siteSettingsForm.ldap_config.use_ssl"
                    :active-text="t('common.yes')"
                    :inactive-text="t('common.no')"
                  />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.ldapSslTip') }}
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">{{ t('dashboard.adminBindConfig') }}</el-divider>
                
                <el-form-item :label="t('dashboard.adminDN')">
                  <el-input v-model="siteSettingsForm.ldap_config.bind_dn" :placeholder="t('dashboard.adminDnPlaceholder')" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.adminDnTip') }}
                  </div>
                </el-form-item>
                
                <el-form-item :label="t('dashboard.adminPassword')">
                  <el-input v-model="siteSettingsForm.ldap_config.bind_password" type="password" :placeholder="t('dashboard.adminPasswordPlaceholder2')" show-password />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.adminPasswordTip') }}
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">{{ t('dashboard.userSearchConfig') }}</el-divider>
                
                <el-form-item :label="t('dashboard.userSearchBase')" required>
                  <el-input v-model="siteSettingsForm.ldap_config.user_search_base" :placeholder="t('dashboard.userSearchBasePlaceholder')" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.userSearchBaseTip') }}
                  </div>
                </el-form-item>
                
                <el-form-item :label="t('dashboard.userSearchFilter')" required>
                  <el-input v-model="siteSettingsForm.ldap_config.user_search_filter" :placeholder="t('dashboard.userSearchFilterPlaceholder')" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.userSearchFilterTip') }}
                  </div>
                </el-form-item>
                
                <el-form-item :label="t('dashboard.userDNTemplate')">
                  <el-input v-model="siteSettingsForm.ldap_config.user_dn_template" :placeholder="t('dashboard.userDnTemplatePlaceholder')" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.userDnTemplateTip') }}
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">{{ t('dashboard.defaultUserConfig') }}</el-divider>
                
                <el-form-item :label="t('dashboard.defaultUserRole')">
                  <el-select v-model="siteSettingsForm.ldap_config.default_role" :placeholder="t('dashboard.selectDefaultRole')" style="width: 200px">
                    <el-option :label="t('users.courseAdmin')" value="course_admin" />
                    <el-option :label="t('users.systemAdmin')" value="system_admin" />
                    <el-option :label="t('users.systemAudit')" value="system_audit" />
                  </el-select>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.defaultRoleTip') }}
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">{{ t('dashboard.roleMappingConfig') }}</el-divider>
                
                <el-form-item :label="t('dashboard.roleMappingType')">
                  <el-radio-group v-model="siteSettingsForm.ldap_config.role_mapping_type">
                    <el-radio value="default">{{ t('dashboard.useDefaultRoleRadio') }}</el-radio>
                    <el-radio value="attribute">{{ t('dashboard.mapByLdapAttributeRadio') }}</el-radio>
                  </el-radio-group>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> {{ t('dashboard.roleMappingTip') }}
                  </div>
                </el-form-item>
                
                <template v-if="siteSettingsForm.ldap_config.role_mapping_type === 'attribute'">
                  <el-form-item :label="t('dashboard.roleMappingAttribute')">
                    <el-select v-model="siteSettingsForm.ldap_config.role_mapping_attribute" :placeholder="t('dashboard.selectMappingAttribute')" style="width: 200px">
                      <el-option :label="t('dashboard.organizationUnit')" value="ou" />
                      <el-option :label="t('dashboard.groupMembership')" value="memberOf" />
                      <el-option :label="t('dashboard.customAttribute')" value="custom" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item :label="t('dashboard.courseAdminMapping')" v-if="siteSettingsForm.ldap_config.role_mapping_attribute !== 'custom'">
                    <el-input v-model="siteSettingsForm.ldap_config.role_mappings.course_admin" :placeholder="t('dashboard.courseAdminMappingPlaceholder')" />
                  </el-form-item>
                  
                  <el-form-item :label="t('dashboard.systemAdminMapping')" v-if="siteSettingsForm.ldap_config.role_mapping_attribute !== 'custom'">
                    <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_admin" :placeholder="t('dashboard.systemAdminMappingPlaceholder')" />
                  </el-form-item>
                  
                  <el-form-item :label="t('dashboard.systemAuditMapping')" v-if="siteSettingsForm.ldap_config.role_mapping_attribute !== 'custom'">
                    <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_audit" :placeholder="t('dashboard.systemAuditMappingPlaceholder')" />
                  </el-form-item>
                  
                  <template v-if="siteSettingsForm.ldap_config.role_mapping_attribute === 'custom'">
                    <el-form-item :label="t('dashboard.customAttributeName')">
                      <el-input v-model="siteSettingsForm.ldap_config.custom_attribute_name" :placeholder="t('dashboard.customAttributeNamePlaceholder')" />
                    </el-form-item>
                    
                    <el-form-item :label="t('dashboard.courseAdminValue')">
                      <el-input v-model="siteSettingsForm.ldap_config.role_mappings.course_admin" :placeholder="t('dashboard.courseAdminValuePlaceholder')" />
                    </el-form-item>
                    
                    <el-form-item :label="t('dashboard.systemAdminValue')">
                      <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_admin" :placeholder="t('dashboard.systemAdminValuePlaceholder')" />
                    </el-form-item>
                    
                    <el-form-item :label="t('dashboard.systemAuditValue')">
                      <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_audit" :placeholder="t('dashboard.systemAuditValuePlaceholder')" />
                    </el-form-item>
                  </template>
                </template>
                
                <el-form-item>
                  <el-button type="primary" @click="testLDAPConnection" :loading="testingLDAP">{{ t('dashboard.testLdapConnection') }}</el-button>
                  <el-button @click="resetLDAPConfig">{{ t('dashboard.resetLdapConfig') }}</el-button>
                </el-form-item>
              </template>
            </el-form>
          </el-tab-pane>
          <el-tab-pane :label="t('dashboard.logConfigTab')">
            <div style="margin-bottom: 20px; color: #606266;">
              {{ t('dashboard.configDescPrefix') }}<strong>{{ t('dashboard.logConfigDesc') }}</strong>
            </div>
            
            <el-form :model="siteSettingsForm" label-width="160px">
              <el-form-item :label="t('dashboard.enableBackendLog')">
                <el-switch
                  v-model="siteSettingsForm.log_enabled"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.disableBackendLogTip') }}
                </div>
              </el-form-item>
              <el-form-item :label="t('dashboard.backendLogLevel')">
                <el-select v-model="siteSettingsForm.log_level" :placeholder="t('dashboard.selectLogLevel')" style="width: 200px">
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.logLevelTip') }}
                </div>
              </el-form-item>
              
              <el-form-item :label="t('dashboard.enableFrontendLog')">
                <el-switch
                  v-model="siteSettingsForm.frontend_log_enabled"
                  :active-text="t('common.enabled')"
                  :inactive-text="t('common.disabled')"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('dashboard.disableFrontendLogTip') }}
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
        </el-tabs>
        <template #footer>
          <el-button @click="siteSettingsDialogVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="handleSiteSettingsSave">{{ t('dashboard.saveAllConfig') }}</el-button>
        </template>
    </el-dialog>

    <!-- ==================== 智能指令示例管理弹窗 ==================== -->
    <el-dialog 
      v-model="smartCommandExamplesDialogVisible" 
      :title="t('dashboard.smartCommandExamplesTitle')" 
      width="90%"
      :close-on-click-modal="false"
      draggable
    >
      <!-- 顶部操作区 -->
      <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
        <el-button type="primary" @click="startBatchTest('ai')" :loading="testingAll && !isBatchPaused">
          <el-icon><Refresh /></el-icon>
          {{ t('dashboard.batchTestAI') }}
        </el-button>
        <el-button type="warning" @click="startBatchTest('regex')" :loading="testingAll && !isBatchPaused">
          <el-icon><Setting /></el-icon>
          {{ t('dashboard.batchTestRegex') }}
        </el-button>
        
        <el-divider direction="vertical" />
        
        <el-input 
          v-model="singleTestInput" 
          :placeholder="t('dashboard.testInputPlaceholder')" 
          style="width: 400px"
          @keyup.enter="testSingleCommand"
        />
        <el-button type="success" @click="testSingleCommand" :loading="testingSingle">
          {{ t('dashboard.quickTestAI') }}
        </el-button>
        
        <el-divider direction="vertical" />
        
        <el-button type="primary" @click="showAddExampleDialog">
          <el-icon><Plus /></el-icon>
          {{ t('dashboard.addExampleTitle') }}
        </el-button>

        <!-- 继续测试按钮（仅在暂停时显示） -->
        <el-button v-if="isBatchPaused" type="success" @click="continueBatchTest('ai')">
          {{ t('dashboard.continueTestAI') }}
        </el-button>
      </div>

      <!-- 搜索区域 -->
      <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
        <el-input
          v-model="examplesSearch"
          :placeholder="t('dashboard.examplesSearchPlaceholder')"
          clearable
          style="width: 500px"
          @clear="resetExamplesSearch"
          @keyup.enter="handleExamplesSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleExamplesSearch">
          <el-icon><Search /></el-icon>
          {{ t('common.search') }}
        </el-button>
        <el-button @click="resetExamplesSearch">
          <el-icon><Refresh /></el-icon>
          {{ t('common.reset') }}
        </el-button>
      </div>

      <!-- 单条测试结果展示 -->
      <el-alert 
        v-if="singleTestResult" 
        :type="singleTestResult.success ? 'success' : 'error'"
        :title="singleTestResult.success ? t('dashboard.parseSuccessTitle') : t('dashboard.parseFailedTitle')"
        :description="singleTestResult.message"
        show-icon
        closable
        style="margin-bottom: 20px"
      >
        <div v-if="singleTestResult.parsed_intent" style="margin-top: 10px;">
          <strong>{{ t('dashboard.parsedIntentLabel') }}</strong>{{ singleTestResult.parsed_intent }}
        </div>
        <div v-if="singleTestResult.parsed_fields" style="margin-top: 5px;">
          <strong>{{ t('dashboard.parsedFieldsLabel') }}</strong>
          <pre style="background: #f5f7fa; padding: 10px; border-radius: 4px; margin-top: 5px;">{{ JSON.stringify(singleTestResult.parsed_fields, null, 2) }}</pre>
        </div>
      </el-alert>

      <!-- 批量测试结果展示 -->
      <el-alert 
        v-if="testResults.length > 0" 
        type="info"
        :title="t('dashboard.testResultSummary', { success: testResults.filter(r => r.success).length, failed: testResults.filter(r => !r.success).length })"
        show-icon
        closable
        style="margin-bottom: 20px"
      />

      <!-- 批量测试结果表格 -->
      <el-table 
        v-if="testResults.length > 0" 
        :data="testResults" 
        border 
        stripe
        max-height="400"
        style="margin-bottom: 20px"
      >
        <el-table-column prop="command_text" :label="t('dashboard.commandTextLabel')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="expected_intent" :label="t('dashboard.expectedIntentLabel')" width="120" />
        <el-table-column prop="parsed_intent" :label="t('dashboard.actualIntentLabel')" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.intent_match ? '#67C23A' : '#F56C6C' }">
              {{ row.parsed_intent || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="t('dashboard.fieldMatchLabel')" width="100">
          <template #default="{ row }">
            <span v-if="row.field_comparison">
              {{ (row.field_comparison.match_rate * 100).toFixed(0) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.status')" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'">
              {{ row.success ? t('dashboard.passedLabel') : t('dashboard.failedLabel') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('dashboard.detailLabel')" min-width="150">
          <template #default="{ row }">
            <div v-if="row.field_comparison && row.field_comparison.mismatched_fields">
              <div v-for="(val, key) in row.field_comparison.mismatched_fields" :key="key" style="font-size: 12px; color: #F56C6C;">
                {{ key }}: {{ t('dashboard.expected') }}={{ val.expected }}, {{ t('dashboard.actual') }}={{ val.actual }}
              </div>
            </div>
            <div v-else-if="!row.success" style="font-size: 12px; color: #F56C6C;">
              {{ row.message }}
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 示例列表表格 -->
      <el-table 
        :data="examplesList" 
        border 
        stripe 
        max-height="500"
        @sort-change="handleExamplesSortChange"
      >
        <el-table-column prop="category" :label="t('dashboard.categoryLabel')" width="120" sortable="custom">
          <template #default="{ row }">
            {{ categoryOptions.find(opt => opt.value === row.category)?.label || row.category }}
          </template>
        </el-table-column>
        <el-table-column prop="action_name" :label="t('dashboard.actionNameLabel')" width="120" sortable="custom" />
        <el-table-column prop="example_text" :label="t('dashboard.exampleTextLabel')" min-width="250" show-overflow-tooltip />
        <el-table-column prop="expected_intent" :label="t('dashboard.expectedIntentLabel2')" width="120" sortable="custom" />
        <el-table-column :label="t('dashboard.expectedFieldsLabel')" width="100">
          <template #default="{ row }">
            <el-popover trigger="hover" placement="top">
              <template #reference>
                <el-button link type="primary">{{ t('common.view') }}</el-button>
              </template>
              <pre style="max-width: 300px;">{{ JSON.stringify(row.expected_fields, null, 2) }}</pre>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="t('dashboard.descriptionLabel')" min-width="150" show-overflow-tooltip />
        <el-table-column prop="is_active" :label="t('common.status')" width="80" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? t('common.active') : t('common.inactive') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" :label="t('dashboard.priorityLabel')" width="80" sortable="custom" />
        <el-table-column :label="t('common.action')" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showEditExampleDialog(row)">{{ t('dashboard.editExampleLabel') }}</el-button>
            <el-button link type="success" size="small" @click="testSingleExampleWithMode(row, 'ai')">{{ t('dashboard.testAILabel') }}</el-button>
            <el-button link type="warning" size="small" @click="testSingleExampleWithMode(row, 'regex')">{{ t('dashboard.testRegexLabel') }}</el-button>
            <el-button link type="danger" size="small" @click="deleteExample(row)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="examplesPagination.currentPage"
        v-model:page-size="examplesPagination.pageSize"
        :page-sizes="[15, 25, 50, 100]"
        :total="examplesPagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchExamplesList"
        @current-change="fetchExamplesList"
        style="margin-top: 20px; justify-content: flex-end;"
      />

      <template #footer>
        <el-button @click="smartCommandExamplesDialogVisible = false">{{ t('common.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 新增/编辑示例弹窗 ==================== -->
    <el-dialog 
      v-model="exampleEditDialogVisible" 
      :title="currentExample ? t('dashboard.editExampleTitle') : t('dashboard.addExampleTitle')" 
      width="600px"
      draggable
    >
      <el-form :model="exampleForm" label-width="120px">
        <el-form-item :label="t('dashboard.categoryRequired')" required>
          <el-select v-model="exampleForm.category" :placeholder="t('dashboard.selectCategoryPlaceholder')" style="width: 100%">
            <el-option 
              v-for="opt in categoryOptions" 
              :key="opt.value" 
              :label="opt.label" 
              :value="opt.value" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item :label="t('dashboard.actionNameRequired')" required>
          <el-input v-model="exampleForm.action_name" :placeholder="t('dashboard.actionNamePlaceholder')" />
        </el-form-item>
        
        <el-form-item :label="t('dashboard.exampleTextRequired')" required>
          <el-input 
            v-model="exampleForm.example_text" 
            type="textarea" 
            :rows="3"
            :placeholder="t('dashboard.exampleTextPlaceholder')" 
          />
        </el-form-item>
        
        <el-form-item :label="t('dashboard.expectedIntentLabel2')">
          <el-input v-model="exampleForm.expected_intent" :placeholder="t('dashboard.expectedIntentPlaceholder')" />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            {{ t('dashboard.expectedIntentValues') }}
          </div>
        </el-form-item>
        
        <el-form-item :label="t('dashboard.expectedFieldsJsonLabel')">
          <div style="margin-bottom: 10px;">
            <el-button size="small" type="primary" @click="autoGenerateExpectedFields">
              <el-icon><MagicStick /></el-icon>
              {{ t('dashboard.autoGenerate') }}
            </el-button>
            <el-button size="small" type="success" @click="showTemplateDialog">
              <el-icon><Document /></el-icon>
              {{ t('dashboard.selectTemplate') }}
            </el-button>
            <el-button size="small" @click="formatJson">
              <el-icon><Sort /></el-icon>
              {{ t('dashboard.formatJson') }}
            </el-button>
          </div>
          <el-input 
            v-model="exampleForm.expected_fields_json" 
            type="textarea" 
            :rows="8"
            placeholder='{"action": "navigate", "path": "/admin/students", "storage_data": {...}}' 
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            {{ t('dashboard.expectedFieldsTip') }}
          </div>
          <div v-if="jsonError" style="font-size: 12px; color: #f56c6c; margin-top: 5px;">
            {{ jsonError }}
          </div>
        </el-form-item>
        
        <el-form-item :label="t('dashboard.descriptionLabel')">
          <el-input 
            v-model="exampleForm.description" 
            type="textarea" 
            :rows="2"
            :placeholder="t('dashboard.descriptionPlaceholder')" 
          />
        </el-form-item>
        
        <el-form-item :label="t('dashboard.isActiveLabel')">
          <el-switch v-model="exampleForm.is_active" />
        </el-form-item>
        
        <el-form-item :label="t('dashboard.priorityInput')">
          <el-input-number v-model="exampleForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exampleEditDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveExample">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 预期字段模板选择弹窗 ==================== -->
    <el-dialog 
      v-model="templateDialogVisible" 
      :title="t('dashboard.selectTemplateTitle')" 
      width="700px"
      draggable
    >
      <div style="margin-bottom: 15px; color: #606266;">
        {{ t('dashboard.selectTemplateDesc') }}
      </div>
      
      <el-row :gutter="20">
        <el-col :span="12" v-for="(item, key) in commonTemplates" :key="key" style="margin-bottom: 15px;">
          <el-card 
            shadow="hover" 
            @click="applyTemplate(item.template)"
            style="cursor: pointer; transition: all 0.3s;"
            class="template-card"
          >
            <template #header>
              <div style="display: flex; align-items: center;">
                <el-icon style="margin-right: 8px; font-size: 18px;"><Document /></el-icon>
                <span style="font-weight: bold;">{{ item.name }}</span>
              </div>
            </template>
            <pre style="font-size: 12px; background: #f5f7fa; padding: 10px; border-radius: 4px; overflow-x: auto;">{{ JSON.stringify(item.template, null, 2) }}</pre>
          </el-card>
        </el-col>
      </el-row>
      
      <template #footer>
        <el-button @click="templateDialogVisible = false">{{ t('common.close') }}</el-button>
      </template>
    </el-dialog>

  </div>
</template>


<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import CalendarView from '@/components/CalendarView.vue'
import { Reading, UserFilled, User, OfficeBuilding, DocumentDelete, Setting, Calendar, Document, Money, Plus, InfoFilled, Search, Refresh, Rank, Delete, Download, View, ArrowLeft, Key, Lock, Warning, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import draggable from 'vuedraggable'
import dayjs from 'dayjs'
import { hasFeature, FEATURES } from '@/utils/license'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const router = useRouter()

const logsDialogVisible = ref(false)
const logs = ref([])
const logsLoading = ref(false)
const logsPagination = ref({
  currentPage: 1,
  pageSize: 15,
  total: 0
})
// 日志筛选条件
const logsFilters = ref({
  start_date: '',
  end_date: '',
  user: '',
  level: '',
  search: ''
})

// 修改fetchLogs函数
const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const params = {
      page: logsPagination.value.currentPage,
      page_size: logsPagination.value.pageSize
    }
    
    // 添加筛选条件
    if (logsFilters.value.start_date) {
      params.start_date = logsFilters.value.start_date
    }
    if (logsFilters.value.end_date) {
      params.end_date = logsFilters.value.end_date
    }
    if (logsFilters.value.user) {
      params.user = logsFilters.value.user
    }
    if (logsFilters.value.level) {
      params.level = logsFilters.value.level
    }
    if (logsFilters.value.search) {
      params.search = logsFilters.value.search
    }
    
    const response = await api.get('/logs', { params })
    logs.value = response.data.items
    logsPagination.value.total = response.data.total
  } catch (error) {
    window.logger.error('获取日志失败:', error)
    ElMessage.error(t('dashboard.getLogsFailed'))
  } finally {
    logsLoading.value = false
  }
}

// 重置日志筛选条件
const resetLogsFilters = () => {
  logsFilters.value = {
    start_date: '',
    end_date: '',
    user: '',
    level: '',
    search: ''
  }
  logsPagination.value.currentPage = 1
  fetchLogs()
}

const showLogsDialog = async () => {
  logsDialogVisible.value = true
  logsActiveTab.value = 'current'
  await fetchLogs()
  fetchLogStats()
}

const logsActiveTab = ref('current')

const archiveList = ref([])
const archiveListLoading = ref(false)
const archiveViewingFile = ref(null)
const archiveLogs = ref([])
const archiveLogsLoading = ref(false)
const archivePagination = ref({ currentPage: 1, pageSize: 20, total: 0 })
const archiveFilterLevel = ref('')
const archiveFilterSearch = ref('')

const fetchArchiveList = async () => {
  archiveListLoading.value = true
  try {
    const response = await api.get('/logs/backup/list')
    archiveList.value = response.data.backups || []
  } catch (error) {
    window.logger.error('获取归档列表失败:', error)
    ElMessage.error(t('dashboard.getArchiveListFailed'))
  } finally {
    archiveListLoading.value = false
  }
}

const viewArchiveFile = async (filename) => {
  archiveViewingFile.value = filename
  archiveLogsLoading.value = true
  try {
    const params = {
      page: archivePagination.value.currentPage,
      page_size: archivePagination.value.pageSize,
    }
    if (archiveFilterLevel.value) params.level = archiveFilterLevel.value
    if (archiveFilterSearch.value) params.search = archiveFilterSearch.value
    const response = await api.get(`/logs/backup/view/${encodeURIComponent(filename)}`, { params })
    archiveLogs.value = response.data.items
    archivePagination.value.total = response.data.total
  } catch (error) {
    window.logger.error('查看归档日志失败:', error)
    ElMessage.error(t('dashboard.viewArchiveFailed') + ': ' + (error.response?.data?.detail || error.message))
  } finally {
    archiveLogsLoading.value = false
  }
}

const closeArchiveView = () => {
  archiveViewingFile.value = null
  archiveLogs.value = []
  archivePagination.value = { currentPage: 1, pageSize: 20, total: 0 }
  archiveFilterLevel.value = ''
  archiveFilterSearch.value = ''
}

const handleArchivePageChange = (page) => {
  archivePagination.value.currentPage = page
  if (archiveViewingFile.value) {
    viewArchiveFile(archiveViewingFile.value)
  }
}

const downloadArchiveFile = async (filename) => {
  try {
    const response = await api.get(`/logs/backup/download/${encodeURIComponent(filename)}`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    window.logger.error('下载归档文件失败:', error)
    ElMessage.error(t('dashboard.downloadArchiveFailed'))
  }
}

const deleteArchiveFile = async (filename) => {
  try {
    await ElMessageBox.confirm(t('dashboard.confirmDeleteArchive', { filename }), t('dashboard.deleteConfirm'), {
      confirmButtonText: t('dashboard.confirmDelete'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
    await api.delete(`/logs/backup/${encodeURIComponent(filename)}`)
    ElMessage.success(t('dashboard.archiveDeleted'))
    fetchArchiveList()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('删除归档文件失败:', error)
      ElMessage.error(t('dashboard.deleteArchiveFailed'))
    }
  }
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1) + ' ' + units[i]
}

watch(logsActiveTab, (val) => {
  if (val === 'archive') {
    archiveViewingFile.value = null
    fetchArchiveList()
  }
})

const testEmailConfig = async () => {
  if (!emailConfigFormRef.value) return
  
  await emailConfigFormRef.value.validate(async (valid) => {
    if (valid) {
      testingEmail.value = true
      try {
        await api.post('/settings/test-email', emailConfig.value)
        ElMessage.success(t('dashboard.testEmailSuccess'))
      } catch (error) {
        window.logger.error('邮件测试失败:', error)
        ElMessage.error(t('dashboard.emailTestFailed') + ': ' + (error.response?.data?.detail || error.message))
      } finally {
        testingEmail.value = false
      }
    }
  })
}

const handleLogsPageChange = (page) => {
  logsPagination.value.currentPage = page
  fetchLogs()
}

const logsStats = ref(null)
const logsBackupLoading = ref(false)

const fetchLogStats = async () => {
  try {
    const response = await api.get('/logs/stats')
    logsStats.value = response.data
  } catch (error) {
    window.logger.error('获取日志统计失败:', error)
  }
}

const _buildLogFilterParams = () => {
  const params = {}
  if (logsFilters.value.start_date) params.start_date = logsFilters.value.start_date
  if (logsFilters.value.end_date) params.end_date = logsFilters.value.end_date
  if (logsFilters.value.user) params.user = logsFilters.value.user
  if (logsFilters.value.level) params.level = logsFilters.value.level
  if (logsFilters.value.search) params.search = logsFilters.value.search
  return params
}

const handleBackupLogs = async () => {
  logsBackupLoading.value = true
  try {
    const params = _buildLogFilterParams()
    const response = await api.post('/logs/backup', null, { params })
    if (response.data.count === 0) {
      ElMessage.info(response.data.message)
    } else {
      ElMessage.success(response.data.message)
    }
    fetchLogStats()
  } catch (error) {
    window.logger.error('备份日志失败:', error)
    ElMessage.error(t('dashboard.backupLogFailed') + ': ' + (error.response?.data?.detail || error.message))
  } finally {
    logsBackupLoading.value = false
  }
}

const handleClearLogsConfirm = () => {
  const hasFilter = logsFilters.value.start_date || logsFilters.value.end_date || logsFilters.value.user || logsFilters.value.level || logsFilters.value.search
  const filterDesc = hasFilter ? t('dashboard.filteredLogs') : t('dashboard.allLogs2')
  ElMessageBox.confirm(
    t('dashboard.confirmClearLogs', { filterDesc }),
    t('dashboard.clearLogsConfirm'),
    { confirmButtonText: t('dashboard.confirmClear'), cancelButtonText: t('common.cancel'), type: 'warning' }
  ).then(() => {
    handleClearLogs()
  }).catch(() => {})
}

const handleClearLogs = async () => {
  try {
    const params = _buildLogFilterParams()
    const response = await api.delete('/logs/clear', { params })
    if (response.data.count === 0) {
      ElMessage.info(response.data.message)
    } else {
      ElMessage.success(response.data.message)
    }
    logsPagination.value.currentPage = 1
    fetchLogs()
    fetchLogStats()
  } catch (error) {
    window.logger.error('清除日志失败:', error)
    ElMessage.error(t('dashboard.clearLogsFailed') + ': ' + (error.response?.data?.detail || error.message))
  }
}

const goToDatabaseManagement = () => {
  router.push('/admin/database')
}

const showLicenseWarning = (featureName) => {
  ElMessage.warning(`${featureName}${t('dashboard.wechatLicenseRequired')}${t('dashboard.wechatLicenseActivate')}`)
}

const stats = ref({
  courses: 0,
  teachers: 0,
  students: 0,
  rooms: 0,
  classes: 0,
  schedules: 0,
  conflicts: 0
})

const passwordDialogVisible = ref(false)
const passwordFormRef = ref(null)

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const siteSettingsDialogVisible = ref(false)
const siteSettingsFormRef = ref(null)
const emailConfigFormRef = ref(null)
const siteSettingsForm = ref({
  site_name: '',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  contact_wechat: '',
  site_url: '',
  site_logo: '',
  organization_website: '',
  wechat_qrcode: '',
  work_wechat_qrcode: '',
  teacher_visibility_restricted: true,
  schedule_edit_restricted: true,
  schedule_delete_restricted: true,
  subject_teachers: [],
  fee_managers: [],
  grade_managers: [],
  evaluation_managers: [],
  operation_managers: [],
  log_enabled: true,
  log_level: 'INFO',
  frontend_log_enabled: true,
  ldap_enabled: false,
  open_registration_enabled: false,
  open_registration_expiry: null,
  session_timeout_minutes: 1440,
  hours_per_lesson: 2.0,
  grade_options: [
    t('dashboard.grade1'), t('dashboard.grade2'), t('dashboard.grade3'), t('dashboard.grade4'), t('dashboard.grade5'), t('dashboard.grade6'),
    t('dashboard.grade7'), t('dashboard.grade8'), t('dashboard.grade9'),
    t('dashboard.grade10'), t('dashboard.grade11'), t('dashboard.grade12'),
    t('dashboard.grade13'), t('dashboard.grade14'), t('dashboard.grade15'), t('dashboard.grade16'),
    t('dashboard.grade17'), t('dashboard.grade18'), t('dashboard.grade19')
  ],
  exam_stages: [
    t('dashboard.examAutumnA'), t('dashboard.examAutumnB'), t('dashboard.examAutumnMid'), t('dashboard.examAutumnC'), t('dashboard.examAutumnD'), t('dashboard.examAutumnFinal'),
    t('dashboard.examSpringA'), t('dashboard.examSpringB'), t('dashboard.examSpringMid'), t('dashboard.examSpringC'), t('dashboard.examSpringD'), t('dashboard.examSpringFinal'),
    t('dashboard.examZhongkao1'), t('dashboard.examZhongkao2'), t('dashboard.examZhongkao3'), t('dashboard.examZhongkao'), t('dashboard.examHuikao'),
    t('dashboard.examGaokaoA'), t('dashboard.examGaokaoB'), t('dashboard.examGaokaoC'), t('dashboard.examSpringGaokao'),
    t('dashboard.examGaokao1'), t('dashboard.examGaokao2'), t('dashboard.examGaokao3'), t('dashboard.examSummerGaokao')
  ],
  ldap_config: {
    enabled: false,
    server: '',
    port: 389,
    use_ssl: false,
    bind_dn: '',
    bind_password: '',
    user_search_base: '',
    user_search_filter: '(uid={username})',
    user_dn_template: '',
    default_role: 'course_admin',
    role_mapping_type: 'default',
    role_mapping_attribute: 'ou',
    custom_attribute_name: '',
    role_mappings: {
      course_admin: '',
      system_admin: '',
      system_audit: ''
    }
  }
})

const backendPort = ref(35000)
const frontendPort = ref(18080)
const classes = ref([])
const teachers = ref([])
const students = ref([])
const testingUrl = ref(null) // 用于控制测试按钮的加载状态

const wechatConfig = ref({
  fee_alert: [''],
  schedule_arrange: { default: [''] }
})
const emailConfig = ref({
  smtp_host: '',
  smtp_port: 465,
  smtp_user: '',
  smtp_password: '',
  smtp_from_name: '',
  smtp_ssl: true
})
const emailNotificationSettings = ref({
  enabled: false,
  reminders: ['morning', 'evening'],
  recipients: ['teachers', 'students'],
  homework_enabled: false,
  homework_recipients: ['students']
})
const testingEmail = ref(false)

const aiConfig = ref({
  enabled: true,
  provider: 'DeepSeek',
  api_url: '',
  api_key: '',
  model: 'deepseek-v4-flash',
  timeout: 60
})
const testingAI = ref(false)
const testingLDAP = ref(false)
const apiUrlError = ref('')

// ==================== 智能指令示例管理相关变量 ====================
const smartCommandExamplesDialogVisible = ref(false)
const exampleEditDialogVisible = ref(false)
const examplesList = ref([])
const examplesPagination = ref({
  currentPage: 1,
  pageSize: 20,
  total: 0
})
const currentExample = ref(null)
const exampleForm = ref({
  category: '',
  action_name: '',
  example_text: '',
  expected_intent: '',
  expected_fields_json: '{}',
  description: '',
  is_active: true,
  sort_order: 0
})

// 排序相关变量
const examplesSort = ref({
  prop: 'sort_order',
  order: 'ascending'
})

// 搜索相关变量
const examplesSearch = ref('')

// 测试结果相关变量
const testResults = ref([])
const testingAll = ref(false)
const testingSingle = ref(false)
const singleTestInput = ref('')
const singleTestResult = ref(null)
const jsonError = ref('')
const templateDialogVisible = ref(false)

// 分批测试相关变量
const batchTestingIndex = ref(0) // 当前正在测试的索引
const currentBatchResults = ref([]) // 当前批次的测试结果
const isBatchPaused = ref(false) // 是否暂停等待用户确认

// 分类选项
const categoryOptions = [
  { label: t('dashboard.categoryCourseManagement'), value: 'course_management' },
  { label: t('dashboard.categoryTeacherManagement'), value: 'teacher_management' },
  { label: t('dashboard.categoryStudentManagement'), value: 'student_management' },
  { label: t('dashboard.categoryClassManagement'), value: 'class_management' },
  { label: t('dashboard.categoryRoomManagement'), value: 'room_management' },
  { label: t('dashboard.categoryScheduleManagement'), value: 'schedule_management' },
  { label: t('dashboard.categoryLeaveManagement'), value: 'leave_management' },
  { label: t('dashboard.categoryHolidayManagement'), value: 'holiday_management' },
  { label: t('dashboard.categoryFeeManagement'), value: 'fee_management' },
  { label: t('dashboard.categoryGradeManagement'), value: 'grade_management' },
  { label: t('dashboard.categoryDataSearch'), value: 'data_search' }
]

const validateAIUrl = () => {
  if (!aiConfig.value.api_url) {
    apiUrlError.value = ''
    return
  }
  
  const urlPattern = /^https?:\/\/.+/i
  if (!urlPattern.test(aiConfig.value.api_url)) {
    apiUrlError.value = t('dashboard.apiUrlError')
  } else {
    apiUrlError.value = ''
  }
}

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})
 
const siteSettingsRules = {
  site_name: [{ required: true, message: t('dashboard.siteNameRequired'), trigger: 'blur' }],
  site_url: [
    { required: true, message: t('dashboard.localIpRequired'), trigger: 'blur' },
    { 
      pattern: /^(\d{1,3}\.){3}\d{1,3}$|^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/,
      message: t('dashboard.localIpMustBeValid'),
      trigger: 'blur'
    }
  ]
}

const emailConfigRules = {
  smtp_host: [{ required: true, message: t('dashboard.smtpHostRequired'), trigger: 'blur' }],
  smtp_port: [{ required: true, message: t('dashboard.smtpPortRequired'), trigger: 'blur' }],
  smtp_user: [{ required: true, message: t('dashboard.smtpUserRequired'), trigger: 'blur' }],
  smtp_password: [{ required: true, message: t('dashboard.smtpPasswordRequired'), trigger: 'blur' }],
  smtp_from_name: [{ required: true, message: t('dashboard.smtpFromNameRequired'), trigger: 'blur' }]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error(t('dashboard.reenterPassword')))
  } else if (value !== passwordForm.value.new_password) {
    callback(new Error(t('dashboard.passwordMismatch')))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: t('dashboard.oldPasswordRequired'), trigger: 'blur' }],
  new_password: [
    { required: true, message: t('dashboard.newPasswordRequired'), trigger: 'blur' },
    { min: 6, message: t('dashboard.passwordMinLength'), trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const getActiveClassStudents = (classId) => {
  return students.value.filter(s => {
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    const isActive = s.is_active
    return belongsToClass && isActive
  })
}
 
const getInactiveClassStudents = (classId) => {
  return students.value.filter(s => {
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    const isInactive = !s.is_active
    return belongsToClass && isInactive
  })
}
 
const getClassTeachers = (classId) => {
  return teachers.value.filter(t => {
    return t.class_ids && t.class_ids.includes(classId)
  })
}

const fetchStats = async () => {
  try {
    const [courses, teachers, students, rooms, classes, schedules] = await Promise.all([
      api.get('/courses', { params: { skip: 0, limit: 100000 } }),
      api.get('/teachers', { params: { skip: 0, limit: 100000 } }),
      api.get('/students', { params: { skip: 0, limit: 100000 } }),
      api.get('/rooms', { params: { skip: 0, limit: 100000 } }),
      api.get('/classes', { params: { skip: 0, limit: 100000 } }),
      api.get('/schedules', { params: { skip: 0, limit: 100000 } })
    ])
    
    stats.value.courses = (courses.data.items || courses.data).length
    stats.value.teachers = (teachers.data.items || teachers.data).length
    stats.value.students = (students.data.items || students.data).length
    stats.value.rooms = (rooms.data.items || rooms.data).length
    stats.value.classes = (classes.data.items || classes.data).length
    stats.value.schedules = (schedules.data.items || schedules.data).length
    stats.value.conflicts = (schedules.data.items || schedules.data).filter(s => s.has_conflict).length
  } catch (error) {
    window.logger.error('获取统计数据失败:', error)
  }
}

const goToPage = (path) => {
  router.push(path)
}

const showPasswordDialog = () => {
  passwordDialogVisible.value = true
}

const handlePasswordChange = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.post('/auth/change-password', passwordForm.value)
        ElMessage.success(t('dashboard.resetSuccess'))
        passwordDialogVisible.value = false
        passwordForm.value = {
          old_password: '',
          new_password: ''
        }
      } catch (error) {
        window.logger.error('密码修改失败:', error)
      }
    }
  })
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  // 触发自定义登出事件
  window.dispatchEvent(new CustomEvent('user-logged-out'))
  window.location.href = '/admin/login'
}

const showSiteSettingsDialog = () => {
  siteSettingsDialogVisible.value = true
  fetchSiteSettings()
}

const testSingleUrl = async (type, key, index = 0) => {
  let urlToTest = ''
  if (type === 'fee_alert') {
    urlToTest = wechatConfig.value.fee_alert[index]
  } else {
    urlToTest = wechatConfig.value[type]?.[key]?.[index]
  }

  if (!urlToTest) {
    ElMessage.warning(t('dashboard.fillWebhookFirst'))
    return
  }

  const loadingKey = type === 'fee_alert' ? `fee_${index}` : `${type}_${key}_${index}`
  testingUrl.value = loadingKey

  try {
    // 调用后端接口，传入要测试的具体 URL
    await api.post('/settings/test-wechat-url', { webhook_url: urlToTest })
    ElMessage.success(t('dashboard.testMessageSuccess'))
  } catch (error) {
    window.logger.error(error)
    ElMessage.error(error.response?.data?.detail || t('dashboard.testSendFailed'))
  } finally {
    testingUrl.value = null
  }
}

const handleSiteSettingsSave = async () => {
  if (!siteSettingsFormRef.value) return
  
  await siteSettingsFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 过滤掉空的 Webhook 地址，避免保存无效数据
        const cleanConfig = JSON.parse(JSON.stringify(wechatConfig.value))
        
        const notifConfig = {
          morning_reminder: notificationSettings.value.reminders.includes('morning'),
          evening_reminder: notificationSettings.value.reminders.includes('evening'),
          enabled_classes: notificationSettings.value.enabled_classes
        }

        const emailNotifConfig = {
          enabled: emailNotificationSettings.value.enabled,
          morning_reminder: emailNotificationSettings.value.reminders.includes('morning'),
          evening_reminder: emailNotificationSettings.value.reminders.includes('evening'),
          recipients: emailNotificationSettings.value.recipients,
          homework_enabled: emailNotificationSettings.value.homework_enabled,
          homework_recipients: emailNotificationSettings.value.homework_recipients
        }

        const aiConfigData = {
          enabled: aiConfig.value.enabled,
          provider: aiConfig.value.provider,
          api_url: aiConfig.value.api_url,
          api_key: aiConfig.value.api_key,
          model: aiConfig.value.model,
          timeout: aiConfig.value.timeout
        }

        const ldapConfigData = {
          enabled: siteSettingsForm.value.ldap_enabled,
          server: siteSettingsForm.value.ldap_config.server,
          port: siteSettingsForm.value.ldap_config.port,
          use_ssl: siteSettingsForm.value.ldap_config.use_ssl,
          bind_dn: siteSettingsForm.value.ldap_config.bind_dn,
          bind_password: siteSettingsForm.value.ldap_config.bind_password,
          user_search_base: siteSettingsForm.value.ldap_config.user_search_base,
          user_search_filter: siteSettingsForm.value.ldap_config.user_search_filter,
          user_dn_template: siteSettingsForm.value.ldap_config.user_dn_template,
          default_role: siteSettingsForm.value.ldap_config.default_role,
          role_mapping_type: siteSettingsForm.value.ldap_config.role_mapping_type,
          role_mapping_attribute: siteSettingsForm.value.ldap_config.role_mapping_attribute,
          custom_attribute_name: siteSettingsForm.value.ldap_config.custom_attribute_name,
          role_mappings: siteSettingsForm.value.ldap_config.role_mappings
        }

        // 只发送schema中定义的字段
        const payload = {
          site_name: siteSettingsForm.value.site_name,
          contact_person: siteSettingsForm.value.contact_person,
          contact_phone: siteSettingsForm.value.contact_phone,
          contact_email: siteSettingsForm.value.contact_email,
          contact_wechat: siteSettingsForm.value.contact_wechat,
          site_url: siteSettingsForm.value.site_url,
          site_logo: siteSettingsForm.value.site_logo,
          organization_website: siteSettingsForm.value.organization_website,
          wechat_qrcode: siteSettingsForm.value.wechat_qrcode,
          work_wechat_qrcode: siteSettingsForm.value.work_wechat_qrcode,
          wechat_webhook_config: JSON.stringify(cleanConfig),
          notification_settings: JSON.stringify(notifConfig),
          email_config: JSON.stringify(emailConfig.value),
          email_notification_settings: JSON.stringify(emailNotifConfig),
          teacher_visibility_restricted: siteSettingsForm.value.teacher_visibility_restricted,
          subject_teachers: siteSettingsForm.value.subject_teachers,
          fee_managers: siteSettingsForm.value.fee_managers,
          grade_managers: siteSettingsForm.value.grade_managers,
          evaluation_managers: siteSettingsForm.value.evaluation_managers,
          operation_managers: siteSettingsForm.value.operation_managers,
          schedule_edit_restricted: siteSettingsForm.value.schedule_edit_restricted,
          schedule_delete_restricted: siteSettingsForm.value.schedule_delete_restricted,
          log_enabled: siteSettingsForm.value.log_enabled,
          log_level: siteSettingsForm.value.log_level,
          log_debug_enabled: siteSettingsForm.value.log_debug_enabled,
          frontend_log_enabled: siteSettingsForm.value.frontend_log_enabled,
          ai_config: JSON.stringify(aiConfigData),
          ldap_enabled: siteSettingsForm.value.ldap_enabled,
          ldap_config: JSON.stringify(ldapConfigData),
          open_registration_enabled: siteSettingsForm.value.open_registration_enabled,
          session_timeout_minutes: siteSettingsForm.value.session_timeout_minutes,
          hours_per_lesson: siteSettingsForm.value.hours_per_lesson,
          course_config: JSON.stringify({
            grade_options: siteSettingsForm.value.grade_options.filter(g => g.trim() !== ''),
            exam_stages: siteSettingsForm.value.exam_stages.filter(s => s.trim() !== '')
          })
        }
        
        window.logger.log('[DEBUG] 正在保存配置，ai_config:', payload.ai_config)
        window.logger.log('[DEBUG] 完整的payload:', JSON.stringify(payload, null, 2))
        
        const response = await api.post('/settings', payload)
        window.logger.log('[DEBUG] Save successful, server returned ai_config:', response.data.ai_config)
        
        ElMessage.success(t('dashboard.configSaved'))
        siteSettingsDialogVisible.value = false
        updateSiteInfo()
      } catch (error) {
        window.logger.error('保存失败:', error)
        ElMessage.error(t('dashboard.saveFailed') + ': ' + (error.response?.data?.detail || error.message))
      }
    }
  })
}

const notificationSettings = ref({
  reminders: [],
  enabled_classes: []
})

const fetchSystemInfo = async () => {
  try {
    const response = await api.get('/system-info')
    if (response.data) {
      backendPort.value = response.data.backend_port || 35000
      frontendPort.value = response.data.frontend_port || 18080
    }
  } catch (error) {
    window.logger.error('获取系统信息失败:', error)
    // 使用默认值
    backendPort.value = 35000
    frontendPort.value = 18080
  }
}

const fetchSiteSettings = async () => {
  try {
    const response = await api.get('/settings')
    if (response.data) {
      siteSettingsForm.value.site_name = response.data.site_name || ''
      siteSettingsForm.value.contact_person = response.data.contact_person || ''
      siteSettingsForm.value.contact_phone = response.data.contact_phone || ''
      siteSettingsForm.value.contact_email = response.data.contact_email || ''
      siteSettingsForm.value.contact_wechat = response.data.contact_wechat || ''

      // 从完整的 URL 中提取纯 IP（去掉 http:// 和 :端口）
      let fullUrl = response.data.site_url || ''
      let pureIp = ''
      if (fullUrl) {
        // 移除 http:// 或 https://
        pureIp = fullUrl.replace(/^https?:\/\//, '')
        // 移除端口号
        pureIp = pureIp.replace(/:\d+$/, '')
      }
      siteSettingsForm.value.site_url = pureIp

      siteSettingsForm.value.site_logo = response.data.site_logo || ''
      siteSettingsForm.value.organization_website = response.data.organization_website || ''
      siteSettingsForm.value.wechat_qrcode = response.data.wechat_qrcode || ''
      siteSettingsForm.value.work_wechat_qrcode = response.data.work_wechat_qrcode || ''
      siteSettingsForm.value.teacher_visibility_restricted = response.data.teacher_visibility_restricted !== undefined ? response.data.teacher_visibility_restricted : true
      siteSettingsForm.value.schedule_edit_restricted = response.data.schedule_edit_restricted !== undefined ? response.data.schedule_edit_restricted : true
      siteSettingsForm.value.schedule_delete_restricted = response.data.schedule_delete_restricted !== undefined ? response.data.schedule_delete_restricted : true
      siteSettingsForm.value.subject_teachers = response.data.subject_teachers || []
      siteSettingsForm.value.fee_managers = response.data.fee_managers || []
      siteSettingsForm.value.grade_managers = response.data.grade_managers || []
      siteSettingsForm.value.evaluation_managers = response.data.evaluation_managers || []
      siteSettingsForm.value.operation_managers = response.data.operation_managers || []
      siteSettingsForm.value.log_enabled = response.data.log_enabled !== undefined ? response.data.log_enabled : true
      siteSettingsForm.value.log_level = response.data.log_level || 'INFO'
      siteSettingsForm.value.log_debug_enabled = response.data.log_debug_enabled !== undefined ? response.data.log_debug_enabled : false
      siteSettingsForm.value.frontend_log_enabled = response.data.frontend_log_enabled !== undefined ? response.data.frontend_log_enabled : true
      siteSettingsForm.value.ldap_enabled = response.data.ldap_enabled !== undefined ? response.data.ldap_enabled : false
      siteSettingsForm.value.open_registration_enabled = response.data.open_registration_enabled !== undefined ? response.data.open_registration_enabled : false
      siteSettingsForm.value.open_registration_expiry = response.data.open_registration_expiry || null
      siteSettingsForm.value.session_timeout_minutes = response.data.session_timeout_minutes !== undefined ? response.data.session_timeout_minutes : 1440
      siteSettingsForm.value.hours_per_lesson = response.data.hours_per_lesson !== undefined ? response.data.hours_per_lesson : 2.0
      
      // 解析课程配置
      if (response.data.course_config) {
        try {
          const courseConfig = JSON.parse(response.data.course_config)
          if (courseConfig.grade_options && Array.isArray(courseConfig.grade_options) && courseConfig.grade_options.length > 0) {
            siteSettingsForm.value.grade_options = courseConfig.grade_options
          }
          if (courseConfig.exam_stages && Array.isArray(courseConfig.exam_stages) && courseConfig.exam_stages.length > 0) {
            siteSettingsForm.value.exam_stages = courseConfig.exam_stages
          }
        } catch (e) {
          window.logger.error('解析课程配置失败:', e)
        }
      }

      // 解析LDAP配置
      if (response.data.ldap_config) {
        try {
          siteSettingsForm.value.ldap_config = JSON.parse(response.data.ldap_config)
          siteSettingsForm.value.ldap_config.enabled = siteSettingsForm.value.ldap_enabled
        } catch (e) {
          window.logger.error('解析LDAP配置失败:', e)
          siteSettingsForm.value.ldap_config = {
            enabled: false,
            server: '',
            port: 389,
            use_ssl: false,
            bind_dn: '',
            bind_password: '',
            user_search_base: '',
            user_search_filter: '(uid={username})',
            user_dn_template: '',
            default_role: 'course_admin',
            role_mapping_type: 'default',
            role_mapping_attribute: 'ou',
            custom_attribute_name: '',
            role_mappings: {
              course_admin: '',
              system_admin: '',
              system_audit: ''
            }
          }
        }
      }

      // ✅ 获取导师列表用于超级导师选择
      const teachersResponse = await api.get('/teachers', { params: { skip: 0, limit: 100000 } })
      teachers.value = teachersResponse.data.items || teachersResponse.data
      // ✅ 获取学员列表用于班级悬浮信息
      const studentsResponse = await api.get('/students', { params: { skip: 0, limit: 100000 } })
      students.value = studentsResponse.data.items || studentsResponse.data
      
      // 解析通知设置
      if (response.data.notification_settings) {
        try {
          const parsed = JSON.parse(response.data.notification_settings)
          notificationSettings.value.reminders = []
          if (parsed.morning_reminder) notificationSettings.value.reminders.push('morning')
          if (parsed.evening_reminder) notificationSettings.value.reminders.push('evening')
          notificationSettings.value.enabled_classes = parsed.enabled_classes || []
        } catch (e) { window.logger.error(e) }
      }

      // 解析微信配置
      if (response.data.wechat_webhook_config) {
        try {
          const parsed = JSON.parse(response.data.wechat_webhook_config)
          // 兼容旧key：将 schedule_change/schedule_create 迁移为 schedule_arrange
          let scheduleArrange = parsed.schedule_arrange || parsed.schedule_change || parsed.schedule_create || null
          if (parsed.schedule_change && parsed.schedule_create && !parsed.schedule_arrange) {
            // 如果同时存在 schedule_change 和 schedule_create，合并到 schedule_arrange
            const changeDefaults = parsed.schedule_change.default || []
            const createDefaults = parsed.schedule_create.default || []
            const mergedDefaults = [...new Set([...changeDefaults, ...createDefaults])]
            scheduleArrange = { ...parsed.schedule_change, default: mergedDefaults }
            for (const [key, value] of Object.entries(parsed.schedule_create)) {
              if (key !== 'default' && !(key in scheduleArrange)) {
                scheduleArrange[key] = value
              }
            }
          }
          // 只有当解析出的对象确实有我们需要的键时才覆盖，否则保持默认结构
          if (parsed.fee_alert || scheduleArrange) {
            wechatConfig.value = {
              fee_alert: parsed.fee_alert || [''],
              schedule_arrange: scheduleArrange || { default: [''] }
            }
          } else {
            window.logger.log('数据库中配置为空或不完整，使用默认结构')
          }
        } catch (e) {
          window.logger.error('解析微信配置JSON失败', e)
        }
      }
      // 解析邮箱配置
      if (response.data.email_config) {
        try {
          const parsed = JSON.parse(response.data.email_config)
          emailConfig.value = {
            smtp_host: parsed.smtp_host || '',
            smtp_port: parsed.smtp_port || 465,
            smtp_user: parsed.smtp_user || '',
            smtp_password: parsed.smtp_password || '',
            smtp_from_name: parsed.smtp_from_name || '',
            smtp_ssl: parsed.smtp_ssl !== undefined ? parsed.smtp_ssl : true
          }
        } catch (e) {
          window.logger.error('解析邮箱配置JSON失败', e)
        }
      }

      // 解析邮箱通知设置
      if (response.data.email_notification_settings) {
        try {
          const parsed = JSON.parse(response.data.email_notification_settings)
          emailNotificationSettings.value = {
            enabled: parsed.enabled || false,
            reminders: [],
            recipients: parsed.recipients || [],
            homework_enabled: parsed.homework_enabled || false,
            homework_recipients: parsed.homework_recipients || []
          }
          if (parsed.morning_reminder) emailNotificationSettings.value.reminders.push('morning')
          if (parsed.evening_reminder) emailNotificationSettings.value.reminders.push('evening')
        } catch (e) {
          window.logger.error('解析邮箱通知设置JSON失败', e)
        }
      }

      // 解析AI配置
      if (response.data.ai_config) {
        window.logger.log('[DEBUG] 从服务器获取的ai_config原始值:', response.data.ai_config)
        window.logger.log('[DEBUG] ai_config类型:', typeof response.data.ai_config)
        try {
          const parsed = JSON.parse(response.data.ai_config)
          window.logger.log('[DEBUG] 解析后的AI配置:', parsed)
          aiConfig.value = {
            enabled: parsed.enabled || false,
            provider: parsed.provider || 'qwen',
            api_url: parsed.api_url || '',
            api_key: parsed.api_key || '',
            model: parsed.model || 'qwen-turbo',
            timeout: parsed.timeout || 10
          }
          window.logger.log('[DEBUG] 设置到aiConfig.value:', aiConfig.value)
        } catch (e) {
          window.logger.error('解析AI配置JSON失败', e)
          window.logger.error('原始ai_config内容:', response.data.ai_config)
        }
      } else {
        window.logger.warn('[DEBUG] 服务器返回的数据中没有ai_config字段')
      }
    }
  } catch (error) {
    window.logger.error('获取站点参数失败:', error)
  }
}

// ==================== 智能指令示例管理方法 ====================

const fetchExamplesList = async () => {
  try {
    const params = {
      skip: (examplesPagination.value.currentPage - 1) * examplesPagination.value.pageSize,
      limit: examplesPagination.value.pageSize
    }
    
    // 添加排序参数
    if (examplesSort.value.prop && examplesSort.value.order) {
      params.sort_by = examplesSort.value.prop
      params.sort_order = examplesSort.value.order === 'ascending' ? 'asc' : 'desc'
    }
    
    // 添加搜索参数
    if (examplesSearch.value.trim()) {
      params.search = examplesSearch.value.trim()
    }
    
    const response = await api.get('/smart-command-examples/list', {
      params: params
    })
    
    // 调试日志
    window.logger.log('API响应完整数据:', response)
    window.logger.log('response.data:', response.data)
    
    // 兼容不同的返回格式
    let items = []
    let total = 0
    
    if (response.data && typeof response.data === 'object') {
      if (response.data.items && Array.isArray(response.data.items)) {
        // 新格式：{ items: [...], total: 55 }
        items = response.data.items
        total = Number(response.data.total) || 0
      } else if (Array.isArray(response.data)) {
        // 旧格式：直接返回数组 [...]
        items = response.data
        total = response.data.length
      }
    }

    // 确保items是数组
    if (!Array.isArray(items)) {
      window.logger.warn('items is not an array, resetting to empty array', items)
      items = []
    }
    examplesList.value = items
    examplesPagination.value.total = total
    
    window.logger.log('最终列表数据条数:', items.length)
    window.logger.log('最终总条数:', total)
  } catch (error) {
    window.logger.error('获取示例列表失败:', error)
    ElMessage.error(t('dashboard.getExamplesFailed'))
    // 出错时确保是空数组和数字0
    examplesList.value = []
    examplesPagination.value.total = 0
  }
}

const testSingleExampleWithMode = async (example, mode) => {
  singleTestInput.value = example.example_text
  testingSingle.value = true
  singleTestResult.value = null
  
  try {
    const url = mode === 'ai' ? '/smart-command-examples/test-one' : '/smart-command-examples/test-regex'
    const response = await api.post(url, {
      command_text: singleTestInput.value,
      use_ai: mode === 'ai'
    }, { timeout: 60000 })
    
    singleTestResult.value = response.data
    if (response.data.success) {
      ElMessage.success(t('dashboard.parseSuccess2', { mode: mode === 'ai' ? 'AI' : t('dashboard.regexMode') }))
    } else {
      ElMessage.warning(response.data.message)
    }
  } catch (error) {
    window.logger.error('测试失败:', error)
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      ElMessage.error(t('dashboard.requestTimeout'))
    } else {
      ElMessage.error(t('dashboard.testFailed') + ': ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    testingSingle.value = false
  }
}

const startBatchTest = async (mode) => {
  if (examplesList.value.length === 0) {
    ElMessage.warning(t('dashboard.noTestableExamples'))
    return
  }
  
  testingAll.value = true
  batchTestingIndex.value = 0
  testResults.value = [] // 清空历史总结果
  currentBatchResults.value = []
  isBatchPaused.value = false
  
  await executeNextBatch(mode)
}

// 分批执行测试，执行完一批后暂停，等待用户点击“继续”
const executeNextBatch = async (mode) => {
  // 双重检查，确保examplesList是数组
  if (!Array.isArray(examplesList.value)) {
    window.logger.error('executeNextBatch: examplesList不是数组', examplesList.value)
    testingAll.value = false
    ElMessage.error(t('dashboard.dataError'))
    return
  }
  
  const batchSize = 5
  const endIndex = Math.min(batchTestingIndex.value + batchSize, examplesList.value.length)
  
  if (batchTestingIndex.value >= examplesList.value.length) {
    testingAll.value = false
    ElMessage.success(t('dashboard.allTestsComplete'))
    return
  }

  currentBatchResults.value = []
  const batch = examplesList.value.slice(batchTestingIndex.value, endIndex)
  
  for (const example of batch) {
    try {
      const url = mode === 'ai' ? '/smart-command-examples/test-one' : '/smart-command-examples/test-regex'
      const res = await api.post(url, {
        command_text: example.example_text,
        use_ai: mode === 'ai'
      }, { timeout: 60000 })
      
      // 对比预期结果
      let expectedFields = {}
      try { expectedFields = JSON.parse(example.expected_fields) } catch(e){}
      
      const resultItem = {
        ...res.data,
        expected_intent: example.expected_intent,
        expected_fields: expectedFields,
        intent_match: res.data.parsed_intent === example.expected_intent,
        field_comparison: compareFieldsLocal(expectedFields, res.data.parsed_fields || {})
      }
      
      // 判定整体成功
      resultItem.success = resultItem.intent_match && resultItem.field_comparison.match_rate >= 0.8
      
      currentBatchResults.value.push(resultItem)
      testResults.value.push(resultItem) // 加入总结果列表
    } catch (error) {
      currentBatchResults.value.push({
        command_text: example.example_text,
        success: false,
        message: error.message.includes('timeout') ? t('dashboard.timeoutLabel') : t('dashboard.requestFailedLabel'),
        expected_intent: example.expected_intent
      })
      testResults.value.push(currentBatchResults.value[currentBatchResults.value.length - 1])
    }
  }
  
  batchTestingIndex.value = endIndex
  isBatchPaused.value = true // 暂停，等待用户点击“继续”
}

const continueBatchTest = (mode) => {
  isBatchPaused.value = false
  executeNextBatch(mode)
}

// 本地简单的字段对比逻辑（用于前端展示）
const compareFieldsLocal = (expected, actual) => {
  if (!expected || Object.keys(expected).length === 0) return { match_rate: 1.0, mismatched_fields: {} }
  let matched = 0
  const total = Object.keys(expected).length
  const mismatched = {}
  
  for (const key in expected) {
    if (String(expected[key]).toLowerCase() === String(actual[key] || '').toLowerCase()) {
      matched++
    } else {
      mismatched[key] = { expected: expected[key], actual: actual[key] }
    }
  }
  return { match_rate: matched / total, mismatched_fields: mismatched }
}

const showSmartCommandExamplesDialog = () => {
  smartCommandExamplesDialogVisible.value = true
  fetchExamplesList()
  testResults.value = []
  singleTestResult.value = null
}

const showAddExampleDialog = () => {
  currentExample.value = null
  exampleForm.value = {
    category: '',
    action_name: '',
    example_text: '',
    expected_intent: '',
    expected_fields_json: '{}',
    description: '',
    is_active: true,
    sort_order: 0
  }
  exampleEditDialogVisible.value = true
}

const showEditExampleDialog = (example) => {
  currentExample.value = example
  exampleForm.value = {
    category: example.category,
    action_name: example.action_name,
    example_text: example.example_text,
    expected_intent: example.expected_intent || '',
    expected_fields_json: JSON.stringify(example.expected_fields || {}, null, 2),
    description: example.description || '',
    is_active: example.is_active,
    sort_order: example.sort_order
  }
  exampleEditDialogVisible.value = true
}

// ==================== 预期字段辅助方法 ====================

const formatJson = () => {
  try {
    const parsed = JSON.parse(exampleForm.value.expected_fields_json)
    exampleForm.value.expected_fields_json = JSON.stringify(parsed, null, 2)
    jsonError.value = ''
    ElMessage.success(t('dashboard.jsonFormatSuccess'))
  } catch (e) {
    jsonError.value = t('dashboard.jsonFormatErrorPrefix') + ': ' + e.message
    ElMessage.error(t('dashboard.jsonFormatError'))
  }
}

const autoGenerateExpectedFields = async () => {
  if (!exampleForm.value.example_text) {
    ElMessage.warning(t('dashboard.enterExampleTextFirst'))
    return
  }
  
  if (!exampleForm.value.expected_intent) {
    ElMessage.warning(t('dashboard.selectIntentFirst'))
    return
  }
  
  try {
    // 调用后端API自动生成预期字段
    const response = await api.post('/smart-command-examples/auto-generate', {
      example_text: exampleForm.value.example_text,
      expected_intent: exampleForm.value.expected_intent
    })
    
    if (response.data.success) {
      exampleForm.value.expected_fields_json = JSON.stringify(response.data.expected_fields, null, 2)
      jsonError.value = ''
      ElMessage.success(t('dashboard.autoGenerateSuccess'))
    } else {
      ElMessage.warning(t('dashboard.autoGenerateFailed') + ': ' + response.data.message)
    }
  } catch (error) {
    window.logger.error('自动生成预期字段失败:', error)
    ElMessage.error(t('dashboard.autoGenerateFailedManual'))
  }
}

const showTemplateDialog = () => {
  templateDialogVisible.value = true
}

// 常用模板定义
const commonTemplates = {
  search_template: {
    name: t('dashboard.templateSearchList'),
    template: {
      action: "navigate",
      path: "/admin/{entity}",
      query: {},
      storage_data: {
        search_mode: true,
        entity_type: "{entity}"
      }
    }
  },
  create_template: {
    name: t('dashboard.templateCreateRecord'),
    template: {
      action: "navigate",
      path: "/admin/{entity}",
      query: {},
      storage_data: {
        form_data: {},
        mode: "create"
      }
    }
  },
  update_template: {
    name: t('dashboard.templateUpdateRecord'),
    template: {
      action: "navigate",
      path: "/admin/{entity}",
      query: {
        search: "{keyword}"
      },
      storage_data: {
        form_data: {},
        mode: "update",
        search_keyword: "{keyword}"
      }
    }
  },
  schedule_template: {
    name: t('dashboard.templateSchedule'),
    template: {
      action: "navigate",
      path: "/admin/schedules",
      query: {},
      storage_data: {
        student_name: "{student}",
        date: "{date}",
        start_time: "{start_time}",
        end_time: "{end_time}",
        course_name: "{course}",
        mode: "create"
      }
    }
  },
  confirm_template: {
    name: t('dashboard.templateConfirmAction'),
    template: {
      action: "confirm",
      operation: "{operation}",
      storage_data: {}
    }
  }
}

const applyTemplate = (template) => {
  exampleForm.value.expected_fields_json = JSON.stringify(template, null, 2)
  jsonError.value = ''
  templateDialogVisible.value = false
  ElMessage.success(t('dashboard.templateApplySuccess'))
}

// ==================== 保存示例方法 ====================

const saveExample = async () => {
  try {
    // 验证JSON格式
    let expectedFields = {}
    try {
      expectedFields = JSON.parse(exampleForm.value.expected_fields_json)
    } catch (e) {
      ElMessage.error(t('dashboard.expectedFieldsJsonError'))
      return
    }

    const payload = {
      category: exampleForm.value.category,
      action_name: exampleForm.value.action_name,
      example_text: exampleForm.value.example_text,
      expected_intent: exampleForm.value.expected_intent || null,
      expected_fields: expectedFields,
      description: exampleForm.value.description || null,
      is_active: exampleForm.value.is_active,
      sort_order: exampleForm.value.sort_order
    }

    let apiUrl = '/smart-command-examples/create'
    let method = 'post'
    
    if (currentExample.value) {
      apiUrl = `/smart-command-examples/update/${currentExample.value.id}`
      method = 'put'
    }

    if (method === 'post') {
      await api.post(apiUrl, payload)
    } else {
      await api.put(apiUrl, payload)
    }
    
    ElMessage.success(currentExample.value ? t('dashboard.updateSuccess') : t('dashboard.createSuccess'))
    exampleEditDialogVisible.value = false
    fetchExamplesList()
  } catch (error) {
    window.logger.error('保存示例失败:', error)
    ElMessage.error(t('dashboard.saveFailed') + ': ' + (error.response?.data?.detail || error.message))
  }
}

const deleteExample = async (example) => {
  try {
    await ElMessageBox.confirm(t('dashboard.confirmDeleteExample'), t('dashboard.hint'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })

    await api.delete(`/smart-command-examples/delete/${example.id}`)
    ElMessage.success(t('dashboard.deleteSuccess'))
    fetchExamplesList()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('删除示例失败:', error)
      ElMessage.error(t('dashboard.deleteFailed'))
    }
  }
}

const testAllExamples = async () => {
  testingAll.value = true
  testResults.value = []
  
  try {
    const response = await api.post('/smart-command-examples/test-all')
    testResults.value = response.data.results
    
    const summary = t('dashboard.batchTestSummary', {
      total: response.data.total,
      success: response.data.success_count,
      failed: response.data.failed_count,
      duration: response.data.test_duration_ms.toFixed(2)
    })
    ElMessage.info(summary)
  } catch (error) {
    window.logger.error('批量测试失败:', error)
    ElMessage.error(t('dashboard.testFailed') + ': ' + (error.response?.data?.detail || error.message))
  } finally {
    testingAll.value = false
  }
}

const testSingleCommand = async () => {
  if (!singleTestInput.value.trim()) {
    ElMessage.warning(t('dashboard.enterTestCommand'))
    return
  }

  testingSingle.value = true
  singleTestResult.value = null
  
  try {
    // 使用自定义的超时时间，确保测试时有足够的等待时间
    const response = await api.post('/smart-command-examples/test-one', {
      command_text: singleTestInput.value,
      use_ai: aiConfig.value.enabled // 明确告诉后端是否启用AI
    }, {
      timeout: 60000 // 前端请求也设置为60秒
    })
    singleTestResult.value = response.data
    
    if (response.data.success) {
      ElMessage.success(t('dashboard.parseSuccessSimple'))
    } else {
      ElMessage.warning(response.data.message)
    }
  } catch (error) {
    window.logger.error('单条测试失败:', error)
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      ElMessage.error(t('dashboard.aiResponseTimeout'))
    } else {
      ElMessage.error(t('dashboard.testFailed') + ': ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    testingSingle.value = false
  }
}

const testSingleExample = async (example) => {
  singleTestInput.value = example.example_text
  await testSingleCommand()
}

const handleLogoUploadSuccess = (response) => {
  window.logger.log('上传成功，响应:', response)
  if (response && response.url) {
    siteSettingsForm.value.site_logo = response.url
    ElMessage.success(t('dashboard.logoUploadSuccess'))
  } else if (response && response.data && response.data.url) {
    siteSettingsForm.value.site_logo = response.data.url
    ElMessage.success(t('dashboard.logoUploadSuccess'))
  } else {
    ElMessage.error(t('dashboard.logoUploadFailed'))
  }
}

const handleQrcodeUploadSuccess = (response, type) => {
  window.logger.log('二维码上传成功，响应:', response)
  let url = ''
  if (response && response.url) {
    url = response.url
  } else if (response && response.data && response.data.url) {
    url = response.data.url
  }
  
  if (url) {
    if (type === 'wechat') {
      siteSettingsForm.value.wechat_qrcode = url
      ElMessage.success(t('dashboard.wechatQrcodeUploadSuccess'))
    } else if (type === 'work_wechat') {
      siteSettingsForm.value.work_wechat_qrcode = url
      ElMessage.success(t('dashboard.workWechatQrcodeUploadSuccess'))
    }
  } else {
    ElMessage.error(t('dashboard.qrcodeUploadFailed'))
  }
}

const beforeQrcodeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error(t('dashboard.onlyImageFiles'))
    return false
  }
  if (!isLt2M) {
    ElMessage.error(t('dashboard.imageSizeLimit'))
    return false
  }
  return true
}

// 处理表格排序变化
const handleExamplesSortChange = ({ prop, order }) => {
  examplesSort.value.prop = prop
  examplesSort.value.order = order
  examplesPagination.value.currentPage = 1 // 排序时重置到第一页
  fetchExamplesList()
}

// 处理搜索
const handleExamplesSearch = () => {
  examplesPagination.value.currentPage = 1 // 搜索时重置到第一页
  fetchExamplesList()
}

// 重置搜索
const resetExamplesSearch = () => {
  examplesSearch.value = ''
  examplesPagination.value.currentPage = 1 // 重置时回到第一页
  fetchExamplesList()
}

const beforeLogoUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error(t('dashboard.onlyImageFiles'))
    return false
  }
  if (!isLt2M) {
    ElMessage.error(t('dashboard.imageSizeLimit'))
    return false
  }
  return true
}
const updateSiteInfo = () => {
  localStorage.setItem('site_name', siteSettingsForm.value.site_name)
  // 保存完整的 URL（带协议和端口）
  const fullUrl = `http://${siteSettingsForm.value.site_url}:${backendPort.value}`
  localStorage.setItem('site_url', fullUrl)
  localStorage.setItem('site_logo', siteSettingsForm.value.site_logo)
  localStorage.setItem('teacher_visibility_restricted', siteSettingsForm.value.teacher_visibility_restricted)
  localStorage.setItem('schedule_edit_restricted', siteSettingsForm.value.schedule_edit_restricted)
  localStorage.setItem('schedule_delete_restricted', siteSettingsForm.value.schedule_delete_restricted)
  localStorage.setItem('subject_teachers', JSON.stringify(siteSettingsForm.value.subject_teachers))
  localStorage.setItem('fee_managers', JSON.stringify(siteSettingsForm.value.fee_managers))
  localStorage.setItem('grade_managers', JSON.stringify(siteSettingsForm.value.grade_managers))
  localStorage.setItem('evaluation_managers', JSON.stringify(siteSettingsForm.value.evaluation_managers))
  localStorage.setItem('operation_managers', JSON.stringify(siteSettingsForm.value.operation_managers))
  localStorage.setItem('frontend_log_enabled', siteSettingsForm.value.frontend_log_enabled)
  
  // 刷新日志配置缓存，使配置立即生效
  if (window.logger && window.logger.refreshConfig) {
    const newStatus = window.logger.refreshConfig()
    window.logger.log('[Dashboard] 前端日志配置已更新，新状态:', newStatus)
  }
}

const getFullLogoUrl = (logoPath) => {
  if (!logoPath) return ''
  if (logoPath.startsWith('http')) {
    return logoPath
  }
  // 直接使用相对路径，让浏览器自动处理域名和端口
  return logoPath
}

// --- 微信配置辅助函数 ---
const fetchClasses = async () => {
  try {
    const res = await api.get('/classes', { params: { skip: 0, limit: 100000 } })
    classes.value = res.data.items || res.data
  } catch (e) { window.logger.error(e) }
}

const addUrl = (type, key) => {
  if (!wechatConfig.value[type]) wechatConfig.value[type] = {}
  if (!wechatConfig.value[type][key]) wechatConfig.value[type][key] = []
  wechatConfig.value[type][key].push('')
}

const removeUrl = (type, key, index) => {
  if (wechatConfig.value[type] && wechatConfig.value[type][key]) {
    wechatConfig.value[type][key].splice(index, 1)
  }
}

const currentUser = ref(null)

const fetchCurrentUser = async () => {
  try {
    const response = await api.get('/auth/me')
    currentUser.value = response.data
  } catch (error) {
    window.logger.error('获取当前用户信息失败:', error)
    // 如果获取失败，清除token
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      currentUser.value = null
      // 触发自定义登出事件
      window.dispatchEvent(new CustomEvent('user-logged-out'))
  }
}

const passwordResetRequestsDialogVisible = ref(false)
const passwordResetRequests = ref([])
const resetPasswordDialogVisible = ref(false)
const resetPasswordForm = ref({
  new_password: '',
  confirm_password: ''
})
const resetPasswordFormRef = ref(null)
const currentResetUser = ref(null)

const resetPasswordRules = {
  new_password: [
    { required: true, message: t('dashboard.newPasswordRequired'), trigger: 'blur' },
    { min: 6, message: t('dashboard.passwordMinLength'), trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: t('dashboard.reenterPassword'), trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.value.new_password) {
          callback(new Error(t('dashboard.passwordMismatch')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const showPasswordResetRequests = async () => {
  try {
    const response = await api.get('/auth/password-reset-requests')
    passwordResetRequests.value = response.data
    passwordResetRequestsDialogVisible.value = true
  } catch (error) {
    window.logger.error('获取密码重置请求失败:', error)
    if (error.response) {
      window.logger.error('错误状态:', error.response.status)
      window.logger.error('错误详情:', error.response.data)
      ElMessage.error(t('dashboard.getPasswordResetFailed') + `: ${error.response.status} - ${JSON.stringify(error.response.data)}`)
    } else {
      ElMessage.error(t('dashboard.getPasswordResetNetworkError'))
    }
  }
}

const getStatusType = (status) => {
  const types = {
    'pending': 'warning',
    'completed': 'success',
    'rejected': 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'pending': t('dashboard.statusPending'),
    'completed': t('dashboard.statusCompleted'),
    'rejected': t('dashboard.statusRejected')
  }
  return texts[status] || status
}

const formatDateTime = (datetime) => {
  return dayjs(datetime).format('YYYY-MM-DD HH:mm:ss')
}

const showResetPasswordDialog = (request) => {
  currentResetUser.value = request
  resetPasswordForm.value = {
    new_password: '',
    confirm_password: ''
  }
  resetPasswordDialogVisible.value = true
}

const handleResetPassword = async () => {
  if (!resetPasswordFormRef.value) return
  
  await resetPasswordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.post(`/auth/reset-password/${currentResetUser.value.user_id}`, {
          new_password: resetPasswordForm.value.new_password
        })
        
        // 更新请求状态
        await api.put(`/auth/password-reset-requests/${currentResetUser.value.id}`, {
          status: 'completed'
        })
        
        ElMessage.success(t('dashboard.resetSuccess'))
        resetPasswordDialogVisible.value = false
        showPasswordResetRequests() // 刷新列表
      } catch (error) {
        window.logger.error('重置密码失败:', error)
      }
    }
  })
}

const rejectPasswordReset = async (request) => {
  try {
    await ElMessageBox.confirm(t('dashboard.confirmRejectPasswordReset'), t('dashboard.hint'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    
    await api.put(`/auth/password-reset-requests/${request.id}`, {
      status: 'rejected'
    })
    
    ElMessage.success(t('dashboard.requestRejected'))
    showPasswordResetRequests() // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('拒绝请求失败:', error)
    }
  }
}

const testAIConnection = async () => {
  if (!aiConfig.value.api_url || !aiConfig.value.api_key) {
    ElMessage.warning(t('dashboard.fillApiUrlAndKey'))
    return
  }

  // 验证API地址格式
  const urlPattern = /^https?:\/\/.+/i
  if (!urlPattern.test(aiConfig.value.api_url)) {
    ElMessage.error(t('dashboard.apiUrlFormatError'))
    return
  }

  testingAI.value = true
  try {
    // 先保存配置
    const cleanConfig = JSON.parse(JSON.stringify(wechatConfig.value))
    
    const notifConfig = {
      morning_reminder: notificationSettings.value.reminders.includes('morning'),
      evening_reminder: notificationSettings.value.reminders.includes('evening'),
      enabled_classes: notificationSettings.value.enabled_classes
    }

    const emailNotifConfig = {
      enabled: emailNotificationSettings.value.enabled,
      morning_reminder: emailNotificationSettings.value.reminders.includes('morning'),
      evening_reminder: emailNotificationSettings.value.reminders.includes('evening'),
      recipients: emailNotificationSettings.value.recipients,
      homework_enabled: emailNotificationSettings.value.homework_enabled,
      homework_recipients: emailNotificationSettings.value.homework_recipients
    }

    const aiConfigData = {
      enabled: aiConfig.value.enabled,
      provider: aiConfig.value.provider,
      api_url: aiConfig.value.api_url,
      api_key: aiConfig.value.api_key,
      model: aiConfig.value.model,
      timeout: aiConfig.value.timeout
    }

    const ldapConfigData = {
      enabled: siteSettingsForm.value.ldap_enabled,
      server: siteSettingsForm.value.ldap_config.server,
      port: siteSettingsForm.value.ldap_config.port,
      use_ssl: siteSettingsForm.value.ldap_config.use_ssl,
      bind_dn: siteSettingsForm.value.ldap_config.bind_dn,
      bind_password: siteSettingsForm.value.ldap_config.bind_password,
      user_search_base: siteSettingsForm.value.ldap_config.user_search_base,
      user_search_filter: siteSettingsForm.value.ldap_config.user_search_filter,
      user_dn_template: siteSettingsForm.value.ldap_config.user_dn_template,
      default_role: siteSettingsForm.value.ldap_config.default_role,
      role_mapping_type: siteSettingsForm.value.ldap_config.role_mapping_type,
      role_mapping_attribute: siteSettingsForm.value.ldap_config.role_mapping_attribute,
      custom_attribute_name: siteSettingsForm.value.ldap_config.custom_attribute_name,
      role_mappings: siteSettingsForm.value.ldap_config.role_mappings
    }

    const payload = {
      site_name: siteSettingsForm.value.site_name,
      contact_person: siteSettingsForm.value.contact_person,
      contact_phone: siteSettingsForm.value.contact_phone,
      contact_email: siteSettingsForm.value.contact_email,
      contact_wechat: siteSettingsForm.value.contact_wechat,
      site_url: siteSettingsForm.value.site_url,
      site_logo: siteSettingsForm.value.site_logo,
      organization_website: siteSettingsForm.value.organization_website,
      wechat_qrcode: siteSettingsForm.value.wechat_qrcode,
      work_wechat_qrcode: siteSettingsForm.value.work_wechat_qrcode,
      teacher_visibility_restricted: siteSettingsForm.value.teacher_visibility_restricted,
      subject_teachers: siteSettingsForm.value.subject_teachers,
      fee_managers: siteSettingsForm.value.fee_managers,
      grade_managers: siteSettingsForm.value.grade_managers,
      evaluation_managers: siteSettingsForm.value.evaluation_managers,
      operation_managers: siteSettingsForm.value.operation_managers,
      schedule_edit_restricted: siteSettingsForm.value.schedule_edit_restricted,
      schedule_delete_restricted: siteSettingsForm.value.schedule_delete_restricted,
      log_enabled: siteSettingsForm.value.log_enabled,
      log_level: siteSettingsForm.value.log_level,
      log_debug_enabled: siteSettingsForm.value.log_debug_enabled,
      frontend_log_enabled: siteSettingsForm.value.frontend_log_enabled,
      wechat_webhook_config: JSON.stringify(cleanConfig),
      notification_settings: JSON.stringify(notifConfig),
      email_config: JSON.stringify(emailConfig.value),
      email_notification_settings: JSON.stringify(emailNotifConfig),
      ai_config: JSON.stringify(aiConfigData),
      ldap_enabled: siteSettingsForm.value.ldap_enabled,
      ldap_config: JSON.stringify(ldapConfigData),
      open_registration_enabled: siteSettingsForm.value.open_registration_enabled,
      session_timeout_minutes: siteSettingsForm.value.session_timeout_minutes
    }
    
    await api.post('/settings', payload)
    
    // 再测试连接
    const response = await api.post('/settings/test-ai', {
      api_url: aiConfig.value.api_url,
      api_key: aiConfig.value.api_key,
      provider: aiConfig.value.provider,
      model: aiConfig.value.model,
      timeout: aiConfig.value.timeout
    })
    
    ElMessage.success(response.data.message || t('dashboard.aiTestSuccess'))
  } catch (error) {
    window.logger.error('AI连接测试失败:', error)
    ElMessage.error(t('dashboard.testFailed') + ': ' + (error.response?.data?.detail || error.message))
  } finally {
    testingAI.value = false
  }
}

const resetAIConfig = () => {
  aiConfig.value = {
    enabled: false,
    provider: 'qwen',
    api_url: '',
    api_key: '',
    model: 'deepseek-v4-flash',
    timeout: 10
  }
  apiUrlError.value = ''
  ElMessage.success(t('dashboard.aiConfigReset'))
}

const resetLDAPConfig = () => {
  siteSettingsForm.value.ldap_config = {
    enabled: false,
    server: '',
    port: 389,
    use_ssl: false,
    bind_dn: '',
    bind_password: '',
    user_search_base: '',
    user_search_filter: '(uid={username})',
    user_dn_template: '',
    default_role: 'course_admin',
    role_mapping_type: 'default',
    role_mapping_attribute: 'ou',
    custom_attribute_name: '',
    role_mappings: {
      course_admin: '',
      system_admin: '',
      system_audit: ''
    }
  }
  siteSettingsForm.value.ldap_enabled = false
  ElMessage.success(t('dashboard.ldapConfigReset'))
}

const testLDAPConnection = async () => {
  testingLDAP.value = true
  try {
    const config = siteSettingsForm.value.ldap_config
    if (!config.server) {
      ElMessage.warning(t('dashboard.ldapServerPlaceholder'))
      return
    }
    if (!config.user_search_base) {
      ElMessage.warning(t('dashboard.userSearchBasePlaceholder'))
      return
    }
    const response = await api.post('/settings/test-ldap', {
      server: config.server,
      port: config.port,
      use_ssl: config.use_ssl,
      bind_dn: config.bind_dn,
      bind_password: config.bind_password,
      user_search_base: config.user_search_base,
      user_search_filter: config.user_search_filter,
      user_dn_template: config.user_dn_template
    })
    ElMessage.success(response.data.message || t('dashboard.ldapTestSuccess'))
  } catch (error) {
    window.logger.error('LDAP连接测试失败:', error)
    ElMessage.error(t('dashboard.testFailed') + ': ' + (error.response?.data?.detail || error.message))
  } finally {
    testingLDAP.value = false
  }
}

// 考试阶段的管理
const defaultExamStages = computed(() => [
  t('dashboard.examAutumnA'), t('dashboard.examAutumnB'), t('dashboard.examAutumnMid'), t('dashboard.examAutumnC'), t('dashboard.examAutumnD'), t('dashboard.examAutumnFinal'),
  t('dashboard.examSpringA'), t('dashboard.examSpringB'), t('dashboard.examSpringMid'), t('dashboard.examSpringC'), t('dashboard.examSpringD'), t('dashboard.examSpringFinal'),
  t('dashboard.examZhongkao1'), t('dashboard.examZhongkao2'), t('dashboard.examZhongkao3'), t('dashboard.examZhongkao'), t('dashboard.examHuikao'),
  t('dashboard.examGaokaoA'), t('dashboard.examGaokaoB'), t('dashboard.examGaokaoC'), t('dashboard.examSpringGaokao'),
  t('dashboard.examGaokao1'), t('dashboard.examGaokao2'), t('dashboard.examGaokao3'), t('dashboard.examSummerGaokao')
])
const addExamStage = () => {
  siteSettingsForm.value.exam_stages.push('')
}
const removeExamStage = (index) => {
  siteSettingsForm.value.exam_stages.splice(index, 1)
}
const resetExamStages = () => {
  siteSettingsForm.value.exam_stages = [...defaultExamStages.value]
  ElMessage.success(t('dashboard.examStagesReset'))
}

//年级选项的管理
const defaultGradeOptions = computed(() => [
  t('dashboard.grade1'), t('dashboard.grade2'), t('dashboard.grade3'), t('dashboard.grade4'), t('dashboard.grade5'), t('dashboard.grade6'),
  t('dashboard.grade7'), t('dashboard.grade8'), t('dashboard.grade9'),
  t('dashboard.grade10'), t('dashboard.grade11'), t('dashboard.grade12'),
  t('dashboard.grade13'), t('dashboard.grade14'), t('dashboard.grade15'), t('dashboard.grade16'),
  t('dashboard.grade17'), t('dashboard.grade18'), t('dashboard.grade19')
])
const addGradeOption = () => {
  siteSettingsForm.value.grade_options.push('')
}
const removeGradeOption = (index) => {
  siteSettingsForm.value.grade_options.splice(index, 1)
}
const resetGradeOptions = () => {
  siteSettingsForm.value.grade_options = [...defaultGradeOptions.value]
  ElMessage.success(t('dashboard.gradesReset'))
}

onMounted(() => {
  fetchStats()
  fetchCurrentUser()
  fetchClasses()
  fetchSystemInfo()
  fetchSiteSettings()
  if (router.currentRoute.value.query.force_change_password === '1') {
    passwordDialogVisible.value = true
  }
})

</script>

<style scoped>
.ghost {
  opacity: 0.5;
  background: #e6f7ff !important;
  border: 1px dashed #1890ff !important;
}
.dashboard {
  padding: 10px;
}

.header-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.stat-card {
  text-align: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-uploader {
  display: inline-block;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}
.logo-uploader:hover {
  border-color: #409eff;
}
.logo-placeholder {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  line-height: 178px;
  text-align: center;
}
.logo-preview {
  width: 178px;
  height: 178px;
  display: block;
  object-fit: contain;
}

.qrcode-uploader {
  display: inline-block;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}
.qrcode-uploader:hover {
  border-color: #409eff;
}
.qrcode-placeholder {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  line-height: 178px;
  text-align: center;
}
.qrcode-preview {
  width: 178px;
  height: 178px;
  display: block;
  object-fit: contain;
}

@media (max-width: 768px) {
  .header-actions {
    justify-content: center;
    gap: 8px;
  }
  
  .header-actions .el-button {
    font-size: 12px;
    padding: 8px 12px;
    flex: 0 0 auto;
  }
  
  .header-actions .el-button span {
    display: inline;
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
    line-height: 28px;
    font-size: 12px;
  }
}


</style>