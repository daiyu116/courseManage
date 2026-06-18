// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="dashboard">
    <!-- 顶部操作栏 -->
    <el-card class="header-card" style="margin-bottom: 10px;">
      <div class="header-actions">
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_audit')" type="warning" @click="showLogsDialog">
          <el-icon><Document /></el-icon>
          日志
        </el-button>
        <el-tooltip v-if="currentUser && currentUser.role === 'super_admin' && !hasFeature(FEATURES.DATABASE_MANAGEMENT)" content="数据库管理为授权功能，请在系统授权管理中激活" placement="bottom">
          <el-button type="info" plain disabled style="opacity:0.6">
            <el-icon><Setting /></el-icon>
            数据库管理
          </el-button>
        </el-tooltip>
        <el-button v-if="currentUser && currentUser.role === 'super_admin' && hasFeature(FEATURES.DATABASE_MANAGEMENT)" type="danger" @click="goToDatabaseManagement">
          <el-icon><Setting /></el-icon>
          数据库管理
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="info" @click="showSiteSettingsDialog">
          <el-icon><Setting /></el-icon>
          站点参数
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="success" @click="goToPage('/admin/license')">
          <el-icon><Key /></el-icon>
          授权管理
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="primary" @click="goToPage('/admin/users')">
          <el-icon><User /></el-icon>
          用户管理
        </el-button>
        <el-button type="warning" @click="showPasswordDialog">
          <el-icon><Lock /></el-icon>
          修改当前账户密码
        </el-button>
        <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'system_admin')" type="warning" @click="showPasswordResetRequests">
          <el-icon><Lock /></el-icon>
          处理密码重置请求
        </el-button>
        <el-button type="danger" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出登录·返回登录界面
        </el-button>
      </div>
    </el-card>

    <!-- 密码重置请求对话框 -->
    <el-dialog v-model="passwordResetRequestsDialogVisible" title="处理密码重置请求" width="800px" draggable>
      <el-table :data="passwordResetRequests" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" size="small" @click="showResetPasswordDialog(row)">重置密码</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="danger" @click="rejectPasswordReset(row)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPasswordDialogVisible" title="重置用户密码" width="400px">
      <el-form :model="resetPasswordForm" :rules="resetPasswordRules" ref="resetPasswordFormRef" label-width="80px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetPasswordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="resetPasswordForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPassword">确定</el-button>
      </template>
    </el-dialog>

    <el-row :gutter="5">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="currentUser?.role === 'course_admin' ? '相关科目数' : '总科目数'" :value="stats.courses">
            <template #prefix>
              <el-icon><Reading /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="currentUser?.role === 'course_admin' ? '相关导师数' : '总导师数'" :value="stats.teachers">            
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="currentUser?.role === 'course_admin' ? '相关学员数' : '总学员数'" :value="stats.students">            
            <template #prefix>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic :title="currentUser?.role === 'course_admin' ? '相关教室数' : '总教室数'" :value="stats.rooms">            
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
          <el-statistic :title="currentUser?.role === 'course_admin' ? '相关班级数' : '总班级数'" :value="stats.classes">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic :title="currentUser?.role === 'course_admin' ? '相关课程安排数' : '总课程安排数'" :value="stats.schedules">
            <template #prefix>
              <el-icon><Calendar /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic :title="currentUser?.role === 'course_admin' ? '相关排课冲突数' : '总排课冲突数'" :value="stats.conflicts">
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
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="success" @click="goToPage('/admin/courses')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><Reading /></el-icon>
            科目管理
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="primary" @click="goToPage('/admin/teachers')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><User /></el-icon>
            导师管理
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="warning" @click="goToPage('/admin/students')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><UserFilled /></el-icon>
            学员管理
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="danger" @click="goToPage('/admin/classes')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><User /></el-icon>
            班级管理
          </el-button>
        </el-col>
      </el-row>
      <el-row :gutter="10">
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="primary" @click="goToPage('/admin/rooms')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><OfficeBuilding /></el-icon>
            教室管理
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="danger" @click="goToPage('/admin/leaves')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><DocumentDelete /></el-icon>
            假日管理
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="info" @click="goToPage('/admin/conditions')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><Setting /></el-icon>
            条件管理
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" type="success" @click="goToPage('/admin/schedules')" style="width: 100%; margin-bottom: 5px;">
            <el-icon><Calendar /></el-icon>
            排课管理
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 添加日历视图 -->
    <CalendarView v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" />

    <!-- 系统日志对话框 -->
    <el-dialog v-model="logsDialogVisible" title="系统日志" width="1200px" draggable>
      <el-tabs v-model="logsActiveTab">
        <!-- 当前日志 Tab -->
        <el-tab-pane label="当前日志" name="current">
          <div style="margin-bottom: 15px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
            <el-date-picker
              v-model="logsFilters.start_date"
              type="date"
              placeholder="开始日期"
              value-format="YYYY-MM-DD"
              style="width: 150px"
              @change="fetchLogs"
            />
            <el-date-picker
              v-model="logsFilters.end_date"
              type="date"
              placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 150px"
              @change="fetchLogs"
            />
            <el-input
              v-model="logsFilters.user"
              placeholder="用户名"
              style="width: 150px"
              clearable
              @clear="fetchLogs"
              @keyup.enter="fetchLogs"
            />
            <el-select
              v-model="logsFilters.level"
              placeholder="日志级别"
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
              placeholder="内容模糊查询"
              style="width: 200px"
              clearable
              @clear="fetchLogs"
              @keyup.enter="fetchLogs"
            />
            <el-button type="primary" @click="fetchLogs">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="resetLogsFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
            <div style="flex-grow: 1;"></div>
            <el-button type="success" @click="handleBackupLogs" :loading="logsBackupLoading">
              <el-icon><Download /></el-icon>
              备份日志
            </el-button>
            <el-button type="danger" @click="handleClearLogsConfirm">
              <el-icon><Delete /></el-icon>
              清除日志
            </el-button>
          </div>

          <div v-if="logsStats" style="margin-bottom: 10px; font-size: 13px; color: #909399;">
            共 {{ logsPagination.total }} 条日志
            <span v-if="logsStats.level_stats" style="margin-left: 10px;">
              <span v-for="(count, lvl) in logsStats.level_stats" :key="lvl" style="margin-right: 8px;">
                <el-tag size="small" :type="lvl === 'ERROR' ? 'danger' : lvl === 'WARNING' ? 'warning' : lvl === 'DEBUG' ? 'info' : 'success'" style="margin-right: 2px;">{{ lvl }}</el-tag>{{ count }}
              </span>
            </span>
          </div>
          
          <el-table :data="logs" v-loading="logsLoading" border>
            <el-table-column prop="id" label="ID" width="65" />
            <el-table-column prop="timestamp" label="UTC时间" width="180" />
            <el-table-column prop="level" label="级别" width="85">
              <template #default="{ row }">
                <el-tag :type="row.level === 'ERROR' ? 'danger' : row.level === 'WARNING' ? 'warning' : row.level === 'DEBUG' ? 'info' : 'success'">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="内容" />
            <el-table-column prop="user" label="操作用户" width="100" />
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

        <!-- 归档日志 Tab -->
        <el-tab-pane label="归档日志" name="archive">
          <div v-if="!archiveViewingFile">
            <el-table :data="archiveList" v-loading="archiveListLoading" border style="margin-bottom: 15px;">
              <el-table-column prop="filename" label="归档文件" min-width="280" />
              <el-table-column label="大小" width="120">
                <template #default="{ row }">
                  {{ formatFileSize(row.size) }}
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="归档时间" width="200" />
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" @click="viewArchiveFile(row.filename)">
                    <el-icon><View /></el-icon> 查看
                  </el-button>
                  <el-button type="success" size="small" @click="downloadArchiveFile(row.filename)">
                    <el-icon><Download /></el-icon> 下载
                  </el-button>
                  <el-button type="danger" size="small" @click="deleteArchiveFile(row.filename)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!archiveListLoading && archiveList.length === 0" description="暂无归档日志文件" />
          </div>

          <div v-else>
            <div style="margin-bottom: 15px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
              <el-button @click="closeArchiveView">
                <el-icon><ArrowLeft /></el-icon> 返回归档列表
              </el-button>
              <span style="font-size: 14px; color: #606266;">
                正在查看: <strong>{{ archiveViewingFile }}</strong>
                <span style="color: #909399; margin-left: 8px;">共 {{ archivePagination.total }} 条</span>
              </span>
              <div style="flex-grow: 1;"></div>
              <el-select v-model="archiveFilterLevel" placeholder="级别筛选" style="width: 120px" clearable @change="viewArchiveFile(archiveViewingFile)">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
              </el-select>
              <el-input v-model="archiveFilterSearch" placeholder="内容搜索" style="width: 180px" clearable @keyup.enter="viewArchiveFile(archiveViewingFile)" />
              <el-button type="primary" @click="viewArchiveFile(archiveViewingFile)">搜索</el-button>
            </div>

            <el-table :data="archiveLogs" v-loading="archiveLogsLoading" border>
              <el-table-column prop="id" label="ID" width="65" />
              <el-table-column prop="timestamp" label="时间" width="200" />
              <el-table-column prop="level" label="级别" width="85">
                <template #default="{ row }">
                  <el-tag :type="row.level === 'ERROR' ? 'danger' : row.level === 'WARNING' ? 'warning' : row.level === 'DEBUG' ? 'info' : 'success'">
                    {{ row.level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="message" label="内容" />
              <el-table-column prop="user" label="操作用户" width="100" />
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

    <!-- 修改密码对话框 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="500px" draggable>
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePasswordChange">确定</el-button>
      </template>
    </el-dialog>
    <!-- 站点参数对话框 -->
    <el-dialog v-model="siteSettingsDialogVisible" title="站点全局参数配置" width="800px" draggable>
        <el-tabs type="border-card">
          <el-tab-pane label="项目介绍">
            <div style="padding: 10px 0;">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="项目版本">
                  <el-tag type="primary" size="large">V1.0</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="开发者">
                  <span style="font-size: 15px; font-weight: 500;">求索教育咨询&稷智瑞云</span>
                </el-descriptions-item>
              </el-descriptions>

              <el-divider content-position="left">项目功能介绍</el-divider>

              <div style="line-height: 2; color: #303133; font-size: 14px;">
                <p style="margin-bottom: 12px;">
                  本系统是一套面向教育培训机构的综合管理平台，涵盖从排课调度、学员管理到费用统计的全流程业务。功能模块按授权方式分为两类：
                  <el-tag type="success" size="small" style="margin: 0 2px;">默认授权</el-tag>即开即用，
                  <el-tag type="warning" size="small" style="margin: 0 2px;">高级授权</el-tag>需在"系统授权管理"中激活后方可使用。
                </p>

                <h4 style="margin: 16px 0 8px; color: #409eff;">
                  <el-tag type="success" size="small">默认授权</el-tag> 基础功能
                </h4>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>📚 科目与排课</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>科目管理：科目代码/名称维护、批量导入</li>
                        <li>手动排课：按导师/班级/教室/科目灵活排课，冲突自动检测</li>
                        <li>排课状态跟踪：待上课、已完训、延期、取消</li>
                        <li>学员考勤：出席/请假/缺席签到，缺席自动标记待补课</li>
                        <li>日历视图与表格视图双模式展示课程安排</li>
                        <li>约束条件管理：硬性约束（导师/学员/班级/教室时间约束）与软性约束</li>
                        <li>节假日管理：假期维护与批量导入，排课自动避开节假日</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>👨‍🏫 导师与学员</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>导师管理：信息维护、科目关联、在职/离职状态</li>
                        <li>学员管理：档案维护、班级归属、多维度筛选与搜索</li>
                        <li>班级管理：班级信息、学员分配、试听/正式课标记</li>
                        <li>教室管理：教室代码/名称/位置/容量维护</li>
                        <li>请假管理：导师/学员请假记录、请假后排课自动规避</li>
                        <li>导师可见性控制：开启后导师仅可见自己相关的科目、班级与排课</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>⚙️ 系统管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>用户管理：多角色权限（超级管理员/系统管理员/课程管理员/系统审计员）</li>
                        <li>导师角色授权：费用管理导师、成绩管理导师、评价管理导师、运营管理导师</li>
                        <li>LDAP统一认证：支持LDAP/AD域账号登录，角色自动映射</li>
                        <li>开放注册：限时开放用户自助注册（3天自动关闭）</li>
                        <li>登录超时配置：自定义Token过期时间（5分钟~30天）</li>
                        <li>密码重置：用户自助申请、管理员审核重置</li>
                        <li>邮箱通知：SMTP邮件向课程安排关联的导师/学员发送课程安排提醒和课程变更提醒</li>
                        <li>系统日志：操作日志记录、日志归档备份与清除</li>
                        <li>站点信息：机构名称/LOGO/官网/二维码等全局参数配置</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>📋 排课管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>手动排课：灵活创建课程安排</li>
                        <li>排课查询：按条件筛选查看排课记录</li>
                        <li>请假/调课：便捷处理临时变动</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>

                <h4 style="margin: 20px 0 8px; color: #E6A23C;">
                  <el-tag type="warning" size="small">高级授权</el-tag> 增强功能
                </h4>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>🧠 智能算法排课</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>遗传算法：适合大规模排课场景，全局搜索较优解</li>
                        <li>回溯算法：精确搜索最优解，适合中小规模</li>
                        <li>混合算法：结合两者优点，推荐使用</li>
                        <li>排课预览：生成结果可逐条选择、编辑后再保存</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>💰 费用管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>学员课费项管理：新增/编辑课费项，关联科目与班级</li>
                        <li>缴费记录：支持多种缴费途径，优惠金额管理</li>
                        <li>退费管理：退费流程、退费途径与退费说明</li>
                        <li>收费提醒：自动提醒待缴费项</li>
                        <li>课费报表导出</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>📈 学员成绩管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>成绩录入：单条/批量添加学员成绩</li>
                        <li>成绩变化追踪：对比历次成绩变化趋势</li>
                        <li>成绩比例趋势图：ECharts可视化展示历次成绩变化</li>
                        <li>多维度对比：按科目、班级、学员筛选分析</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>📊 学员评价管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>评价模板管理：按科目类型自定义评价维度与权重</li>
                        <li>综合能力画像：支持"学习态度/知识掌握/实践能力/创新思维/协作素养"五维或"德智体美劳"五维模型</li>
                        <li>单科能力画像：学科专属评价维度（如语言类听说读写、数学类逻辑推理等）</li>
                        <li>评价周期管理：按学期（上学期秋季/下学期春季）灵活记录</li>
                        <li>雷达图可视化：ECharts五维/多维雷达图直观展示学员能力结构</li>
                        <li>评价管理导师：独立授权评价管理权限，精细控制访问范围</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>💬 微信通知管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>企业微信群机器人Webhook通知</li>
                        <li>课程安排提醒：新建、更新、完训、延期、取消等信息向导师信息群/班级信息群分别推送</li>
                        <li>综合管理通知：费用管理等信息推送</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>🤖 智能指令管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>自然语言指令解析：一句话完成添加科目/导师/学员/排课/请假等操作</li>
                        <li>双模式解析：规则解析（内置）与AI大模型解析（须配置大模型API KEY）（Deepseek/千问/OpenAI/自定义）</li>
                        <li>指令示例管理：自定义智能指令，同时内置示例库，支持批量AI/正则对比测试</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>📺 运营大屏</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>KPI看板：收入/转化率/学员数/导师数/课次/出勤率等核心指标</li>
                        <li>可视化图表：科目分布、导师工作量、收入相关图表分析（可一键隐藏）、月度趋势等</li>
                        <li>试听转化漏斗、导师效能排行</li>
                        <li>全屏模式展示，支持导出图片</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 4px;">
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>🔮 全站快捷按钮</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>桌面端悬浮快捷入口，一键直达智能指令、排课、新建等常用功能</li>
                        <li>可拖拽定位，自动吸附边缘</li>
                      </ul>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div style="padding: 6px 0;">
                      <strong>🗄️ 数据库管理</strong>
                      <ul style="margin: 4px 0 0 0; padding-left: 20px; color: #606266;">
                        <li>手动备份：一键导出SQL备份文件</li>
                        <li>自动备份：定时备份（每小时/每天/每周），自动清理旧备份</li>
                        <li>数据库恢复：从备份文件还原</li>
                        <li>备份文件管理：列表查看、下载、删除</li>
                      </ul>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="机构信息">
            <el-form :model="siteSettingsForm" :rules="siteSettingsRules" ref="siteSettingsFormRef" label-width="120px">
                <el-form-item label="机构名称" prop="site_name">
                  <el-input v-model="siteSettingsForm.site_name" placeholder="请输入机构名称" />
                </el-form-item>
                <el-form-item label="联系人">
                  <el-input v-model="siteSettingsForm.contact_person" placeholder="请输入联系人姓名" />
                </el-form-item>
                <el-form-item label="联系电话">
                  <el-input v-model="siteSettingsForm.contact_phone" placeholder="请输入联系电话" />
                </el-form-item>
                <el-form-item label="电子邮件">
                  <el-input v-model="siteSettingsForm.contact_email" placeholder="请输入电子邮件" />
                </el-form-item>
                <el-form-item label="联系微信">
                  <el-input v-model="siteSettingsForm.contact_wechat" placeholder="请输入微信号" />
                </el-form-item>
                <el-form-item label="本站内网IP" prop="site_url">
                  <el-input v-model="siteSettingsForm.site_url" placeholder="请输入内网IP，如：10.11.12.99（系统将自动拼接为 http://IP:端口）">
                    <template #prepend>http://</template>
                    <template #append>:{{ backendPort }}</template>
                  </el-input>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：此IP用于构建文件访问地址，确保上传的图片、LOGO等资源可以正常访问，务必填写承载本课程管理系统的准确真实的IP地址，否则文件将无法上传和访问
                  </div>
                </el-form-item>
                <el-form-item label="机构LOGO" prop="site_logo">
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
                <el-form-item label="机构宣传网站链接">
                  <el-input v-model="siteSettingsForm.organization_website" placeholder="请输入机构官方网站链接，如：https://www.example.com" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：此链接将显示在网站页脚和微信/邮件通知中
                  </div>
                </el-form-item>
                <el-form-item label="公众号二维码">
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
                    <el-icon><InfoFilled /></el-icon> 提示：上传公众号二维码图片，将显示在网站页脚和微信/邮件通知中
                  </div>
                </el-form-item>
                <el-form-item label="企业微信二维码">
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
                    <el-icon><InfoFilled /></el-icon> 提示：上传企业微信二维码图片，将显示在网站页脚和微信/邮件通知中
                  </div>
                </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="导师配置">
            <el-form :model="siteSettingsForm" label-width="120px">
              <el-form-item label="课程可见性限制">
                <el-switch
                  v-model="siteSettingsForm.teacher_visibility_restricted"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：
                  <span v-if="siteSettingsForm.teacher_visibility_restricted">开启后，导师角色的用户只能看到自己相关的科目、班级（以及由班级关联的学员）、课程安排</span>
                  <span v-else>关闭后，所有导师可以看到系统所有的科目、班级、学员、课程安排</span>
                </div>
              </el-form-item>
              <el-form-item label="课程编辑限制">
                <el-switch
                  v-model="siteSettingsForm.schedule_edit_restricted"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：
                  <span v-if="siteSettingsForm.schedule_edit_restricted">开启后，仅超级管理员可编辑已完训/延期/取消排课状态的课程安排</span>
                  <span v-else>关闭后，课程管理导师也可编辑"已完训/延期/取消"状态的课程安排</span>
                </div>
              </el-form-item>
              <el-form-item label="课程删除限制">
                <el-switch
                  v-model="siteSettingsForm.schedule_delete_restricted"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：
                  <span v-if="siteSettingsForm.schedule_delete_restricted">开启后，仅超级管理员可删除已完训/延期/取消排课状态的课程安排</span>
                  <span v-else>关闭后，课程管理导师也可删除"已完训/延期/取消"状态的课程安排</span>
                </div>
              </el-form-item>
              <el-form-item label="课程管理导师">
                <el-select
                  v-model="siteSettingsForm.subject_teachers"
                  multiple
                  filterable
                  placeholder="选择课程管理导师（不受导师课程可见性和用户角色的限制）"
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
                  提示：被选择的导师将不受"导师可见性限制"选项和导师角色的限制，不受科目、班级、课程安排的访问限制
                </div>
              </el-form-item>
              <el-form-item label="费用管理导师">
                <el-select
                  v-model="siteSettingsForm.fee_managers"
                  multiple
                  filterable
                  placeholder="选择费用管理导师（可访问费用管理模块）"
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
                  提示：被选择的导师可以访问"学员管理"中的"费用管理"模块（需已激活“费用管理”授权），不受导师角色对学员费用的访问限制
                </div>
              </el-form-item>
              <el-form-item label="成绩管理导师">
                <el-select
                  v-model="siteSettingsForm.grade_managers"
                  multiple
                  filterable
                  placeholder="选择成绩管理导师（可访问成绩管理模块）"
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
                  提示：被选择的导师可以访问“学员管理”中的“成绩管理”模块（需已激活“学员成绩管理”授权），不受导师角色对学员成绩的访问限制
                </div>
              </el-form-item>
              <el-form-item label="评价管理导师">
                <el-select
                  v-model="siteSettingsForm.evaluation_managers"
                  multiple
                  filterable
                  placeholder="选择评价管理导师（可访问评价管理模块）"
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
                  提示：被选择的导师可以访问"学员管理"中的"评价管理"模块（需已激活"学员评价"授权），不受导师角色对学员评价的访问限制
                </div>
              </el-form-item>
              <el-form-item label="运营管理导师">
                <el-select
                  v-model="siteSettingsForm.operation_managers"
                  multiple
                  filterable
                  placeholder="选择运营管理导师（可访问运营大屏）"
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
                  提示：被选择的课程管理导师可以访问"运营大屏"模块，查看KPI数据、统计图表等运营信息
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="课程配置">
            <el-form :model="siteSettingsForm" label-width="140px">
              <el-form-item label="每节课课时数">
                <el-input-number
                  v-model="siteSettingsForm.hours_per_lesson"
                  :min="0.1"
                  :max="10"
                  :step="0.1"
                  :precision="1"
                  style="width: 200px"
                />
                <span style="margin-left: 10px; color: #909399;">小时（即课时）</span>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：设置每节课等于多少课时数，默认2小时（即2课时）。支持小数点后一位，例如1.5小时。此参数影响课费计算和统计。
                </div>
              </el-form-item>
              <el-divider content-position="left">年级选项配置</el-divider>
              <el-form-item label="年级列表">
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
                        <el-input v-model="siteSettingsForm.grade_options[index]" placeholder="年级名称" style="flex: 1;" />
                        <el-button type="danger" :icon="Delete" circle style="margin-left: 8px;" @click="removeGradeOption(index)" />
                      </div>
                    </template>
                  </draggable>
                  <el-button type="primary" :icon="Plus" @click="addGradeOption">添加年级</el-button>
                  <el-button @click="resetGradeOptions">恢复默认</el-button>
                </div>
                <div style="margin-top: 5px; font-size: 12px; color: #909399; width: 100%;">
                  <el-icon><InfoFilled /></el-icon> 提示：拖动左侧图标可调整年级顺序，年级顺序影响成绩趋势图中的排序和连贯性。
                </div>
              </el-form-item>
              <el-divider content-position="left">考试阶段配置</el-divider>
              <el-form-item label="考试阶段列表">
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
                        <el-input v-model="siteSettingsForm.exam_stages[index]" placeholder="考试阶段名称" style="flex: 1;" />
                        <el-button type="danger" :icon="Delete" circle style="margin-left: 8px;" @click="removeExamStage(index)" />
                      </div>
                    </template>
                  </draggable>
                  <el-button type="primary" :icon="Plus" @click="addExamStage">添加考试阶段</el-button>
                  <el-button @click="resetExamStages">恢复默认</el-button>
                </div>
                <div style="margin-top: 5px; font-size: 12px; color: #909399; width: 100%;">
                  <el-icon><InfoFilled /></el-icon> 提示：拖动左侧图标可调整考试阶段顺序，顺序影响成绩趋势图中的X轴排序和连贯性。
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="邮箱通知配置">
            <div style="margin-bottom: 20px; color: #606266;">
              <strong>配置说明：</strong>配置SMTP邮件发送参数，用于发送课程安排提醒、作业安排通知和费用提醒。
            </div>
            <el-divider content-position="left">SMTP配置</el-divider>
            <el-form :model="emailConfig" :rules="emailConfigRules" ref="emailConfigFormRef" label-width="160px">
              <el-form-item label="SMTP服务器" prop="smtp_host">
                <el-input v-model="emailConfig.smtp_host" placeholder="例如：smtp.qq.com" />
              </el-form-item>
              <el-form-item label="SMTP端口" prop="smtp_port">
                <el-input-number v-model="emailConfig.smtp_port" :min="1" :max="65535" placeholder="例如：465" />
              </el-form-item>
              <el-form-item label="发送邮箱" prop="smtp_user">
                <el-input v-model="emailConfig.smtp_user" placeholder="例如：yourname@qq.com" />
              </el-form-item>
              <el-form-item label="邮箱密码/授权码" prop="smtp_password">
                <el-input v-model="emailConfig.smtp_password" type="password" show-password placeholder="请输入邮箱密码或授权码" />
              </el-form-item>
              <el-form-item label="发件人名称" prop="smtp_from_name">
                <el-input v-model="emailConfig.smtp_from_name" placeholder="例如：课程安排系统" />
              </el-form-item>
              <el-form-item label="使用SSL">
                <el-switch v-model="emailConfig.smtp_ssl" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="testingEmail" @click="testEmailConfig">测试邮件发送</el-button>
              </el-form-item>
            </el-form>
            <el-divider content-position="left">课程安排提醒设置</el-divider>
            <el-form label-width="160px">
              <el-form-item label="启用邮件提醒">
                <el-switch v-model="emailNotificationSettings.enabled" />
              </el-form-item>
              <el-form-item label="提醒时间">
                <el-checkbox-group v-model="emailNotificationSettings.reminders">
                  <el-checkbox value="morning">早上7点发送当天提醒</el-checkbox>
                  <el-checkbox value="evening">晚上7点发送第二天提醒</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
              <el-form-item label="接收对象">
                <el-checkbox-group v-model="emailNotificationSettings.recipients">
                  <el-checkbox value="teachers">导师</el-checkbox>
                  <el-checkbox value="students">学员</el-checkbox>
                </el-checkbox-group>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：选中的对象将在定义的提醒时间收到与自己相关的课程安排提醒邮件（需要导师/学员已配置邮箱）
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="微信通知配置">
            <div v-if="!hasFeature(FEATURES.WECHAT_NOTIFY)" style="display: flex; align-items: center; justify-content: center; min-height: 300px; color: #909399;">
              <div style="text-align: center;">
                <el-icon :size="48"><Lock /></el-icon>
                <p style="margin-top: 12px; font-size: 16px;">微信通知为授权功能</p>
                <p>请在系统授权管理中激活</p>
              </div>
            </div>
            <template v-else>
            <div style="margin-bottom: 20px; color: #606266;">
              <strong>配置说明：</strong>配置综合管理通知和课程安排提醒。班级的webhook地址在班级管理中配置。
            </div>

            <el-divider content-position="left">综合管理通知(费用等)</el-divider>
            <el-form label-width="160px">
              <el-form-item label="综合管理群">
                <div style="display: flex; gap: 10px;">
                  <el-input v-model="wechatConfig.fee_alert[0]" placeholder="输入管理群的Webhook地址" />
                  <el-button type="primary" :loading="testingUrl === 'fee_0'" @click="testSingleUrl('fee_alert', 0)">测试</el-button>
                </div>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">课程安排提醒方式</el-divider>
            <el-form label-width="160px">
              <el-form-item label="提醒时间">
                <el-checkbox-group v-model="notificationSettings.reminders">
                  <el-checkbox value="morning">早上7点发送当天提醒</el-checkbox>
                  <el-checkbox value="evening">晚上7点发送第二天提醒</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">课程安排提醒-导师信息群</el-divider>
            <el-form label-width="160px">
              <el-form-item label="导师信息群">
                <div v-for="(url, index) in (wechatConfig.schedule_change.default || [])" :key="'d'+index" style="display: flex; gap: 10px; margin-bottom: 5px;">
                  <el-input v-model="wechatConfig.schedule_change.default[index]" placeholder="导师信息群Webhook" />
                  <el-button type="primary" :loading="testingUrl === `default_${index}`" @click="testSingleUrl('schedule_change', 'default', index)">测试</el-button>
                  <el-button type="danger" size="small" @click="removeUrl('schedule_change', 'default', index)">删除</el-button>
                </div>
                <el-button size="small" @click="addUrl('schedule_change', 'default')">+ 添加导师群</el-button>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">课程安排提醒-班级信息群</el-divider>
            <el-form label-width="160px">
              <el-form-item label="选择班级">
                <el-select
                  v-model="notificationSettings.enabled_classes"
                  multiple
                  filterable
                  placeholder="请选择开启微信通知的班级"
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
                          <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">在读学员:</div>
                          <div v-for="student in getActiveClassStudents(c.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getInactiveClassStudents(c.id).length > 0">
                          <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">非在读学员:</div>
                          <div v-for="student in getInactiveClassStudents(c.id)" :key="student.id" style="margin-bottom: 4px;">
                            {{ student.name }}
                          </div>
                        </div>
                        <div v-if="getActiveClassStudents(c.id).length === 0 && getInactiveClassStudents(c.id).length === 0">
                          暂无学员
                        </div>
                        <div v-if="getClassTeachers(c.id).length > 0" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                          <div style="font-weight: bold; margin-bottom: 8px; color: #409EFF;">班级导师:</div>
                          <div v-for="teacher in getClassTeachers(c.id)" :key="teacher.id" style="margin-bottom: 4px;">
                            {{ teacher.name }}
                            <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                          </div>
                        </div>
                        <div v-else style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                          <div style="color: #999;">暂无导师</div>
                        </div>
                      </template>
                      <span>{{ c.code }} - {{ c.name }}</span>
                    </el-tooltip>
                  </el-option>
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：选中的班级将接收微信通知，请确保在班级管理中配置了webhook地址
                </div>
              </el-form-item>
            </el-form>
            </template>
          </el-tab-pane>
          <el-tab-pane label="人工智能配置">
            <div v-if="!hasFeature(FEATURES.SMART_COMMAND)" style="display: flex; align-items: center; justify-content: center; min-height: 300px; color: #909399;">
              <div style="text-align: center;">
                <el-icon :size="48"><Lock /></el-icon>
                <p style="margin-top: 12px; font-size: 16px;">智能指令为授权功能</p>
                <p>请在系统授权管理中激活</p>
              </div>
            </div>
            <template v-else>
            <div style="margin-bottom: 20px; color: #606266;">
              <strong>配置说明：</strong>配置AI大语言模型API，用于智能指令解析。如果不配置，系统将使用基于规则的解析方式。
            </div>
            
            <el-form :model="aiConfig" label-width="160px">
              <el-form-item label="启用AI解析">
                <el-switch
                  v-model="aiConfig.enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：开启后将使用AI大模型解析指令，否则使用规则解析
                </div>
              </el-form-item>
              
              <el-form-item label="API提供商">
                <el-select v-model="aiConfig.provider" placeholder="选择AI服务提供商" style="width: 100%">
                  <el-option label="DeepSeek" value="deepseek" />
                  <el-option label="通义千问（阿里云）" value="qwen" />
                  <el-option label="文心一言（百度）" value="ernie" />
                  <el-option label="智谱AI" value="zhipu" />
                  <el-option label="OpenAI" value="openai" />
                  <el-option label="自定义" value="custom" />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：选择不同的AI服务提供商
                </div>
              </el-form-item>
              
              <el-form-item label="API地址">
                <el-input 
                  v-model="aiConfig.api_url" 
                  placeholder="例如：https://api.deepseek.com/chat/completions"
                  @blur="validateAIUrl"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 
                  提示：DeepSeek API地址为 https://api.deepseek.com/chat/completions  
                  通义千问使用 https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
                </div>
                <div v-if="apiUrlError" style="margin-top: 5px; font-size: 12px; color: #F56C6C;">
                  {{ apiUrlError }}
                </div>
              </el-form-item>
              
              <el-form-item label="API密钥">
                <el-input 
                  v-model="aiConfig.api_key" 
                  type="password"
                  show-password
                  placeholder="请输入API密钥"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：从AI服务提供商获取的API密钥
                </div>
              </el-form-item>
              
              <el-form-item label="模型名称">
                <el-input 
                  v-model="aiConfig.model" 
                  placeholder="例如：deepseek-v4-flash 或 deepseek-v4-pro"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 
                  提示：推荐使用 deepseek-v4-flash（快速）或 deepseek-v4-pro（高质量）
                  通义千问推荐 qwen-plus（均衡）或 qwen-turbo（快速）
                </div>
              </el-form-item>
              
              <el-form-item label="超时时间(秒)">
                <el-input-number 
                  v-model="aiConfig.timeout" 
                  :min="1" 
                  :max="60"
                  placeholder="API请求超时时间"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：API请求的最大等待时间
                </div>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="testAIConnection" :loading="testingAI">测试连接</el-button>
                <el-button @click="resetAIConfig">重置配置</el-button>
                <el-button type="success" @click="showSmartCommandExamplesDialog">智能指令示例管理</el-button>
              </el-form-item>
            </el-form>
            
            <el-divider content-position="left">使用说明</el-divider>
            <div style="padding: 15px; background-color: #f5f7fa; border-radius: 4px;">
              <h4 style="margin-top: 0;">支持的AI服务提供商：</h4>
              <ul>
                <li><strong>DeepSeek</strong>：需要注册DeepSeek开放平台，获取API密钥</li>
                <li><strong>通义千问（阿里云）</strong>：需要注册阿里云账号，开通DashScope服务</li>
                <li><strong>文心一言（百度）</strong>：需要注册百度智能云，开通ERNIE Bot服务</li>
                <li><strong>智谱AI</strong>：需要注册智谱AI开放平台</li>
                <li><strong>OpenAI</strong>：需要OpenAI API密钥</li>
                <li><strong>自定义</strong>：可以配置其他兼容OpenAI格式的API服务</li>
              </ul>
              <h4>DeepSeek配置说明：</h4>
              <ul>
                <li>API地址：<code>https://api.deepseek.com/chat/completions</code></li>
                <li>推荐模型：<code>deepseek-v4-flash</code>（快速）或 <code>deepseek-v4-pro</code>（深度思考）</li>
                <li>注意：<code>deepseek-chat</code>以及<code>deepseek-reasoner</code> 将于2026年7月24日弃用</li>
              </ul>
              <h4>通义千问配置说明：</h4>
              <ul>
                <li>API地址：<code>https://dashscope.aliyuncs.com/compatible-mode/v1</code></li>
                <li>推荐模型：<code>qwen-plus</code>（均衡）或 <code>qwen-turbo</code>（快速）</li>
                <li>注意：使用OpenAI兼容接口，格式与OpenAI完全一致</li>
              </ul>
              <h4>注意事项：</h4>
              <ul>
                <li>AI解析会产生API调用费用，请合理使用</li>
                <li>建议先使用规则解析，必要时再启用AI解析</li>
                <li>确保API密钥安全，不要泄露给他人</li>
                <li>测试连接成功后才能正常使用AI功能</li>
              </ul>
            </div>
            </template>
          </el-tab-pane>
          <el-tab-pane label="用户管理">
            <div style="margin-bottom: 20px; color: #606266;">
              <strong>配置说明：</strong>配置用户认证方式，包括登录超时、LDAP认证和开放注册。
            </div>
            
            <el-divider content-position="left">登录超时</el-divider>
            <el-form :model="siteSettingsForm" label-width="180px">
              <el-form-item label="登录超时时间（分钟）">
                <el-input-number 
                  v-model="siteSettingsForm.session_timeout_minutes" 
                  :min="5" 
                  :max="43200" 
                  :step="5" 
                  style="width: 200px"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：设置用户登录Token的过期时间，范围5-43200分钟（30天），默认1440分钟（24小时）。修改后新登录的用户将使用新的超时时间
                </div>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">开放注册</el-divider>
            <el-form :model="siteSettingsForm" label-width="180px">
              <el-form-item label="启用开放注册">
                <el-switch
                  v-model="siteSettingsForm.open_registration_enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：开启后，用户可以在登录页面通过邮箱自行注册账户，注册后默认角色为"课程管理员"
                </div>
                <div v-if="siteSettingsForm.open_registration_enabled" style="margin-top: 8px; padding: 10px; background: #fdf6ec; border: 1px solid #faecd8; border-radius: 4px;">
                  <div style="color: #E6A23C; font-size: 13px; font-weight: bold;">
                    <el-icon><Warning /></el-icon> 安全提示
                  </div>
                  <div style="color: #E6A23C; font-size: 12px; margin-top: 4px;">
                    开放注册将在<strong>3天后自动关闭</strong>，以防止非法注册。到期后需管理员重新开启。
                  </div>
                  <div v-if="siteSettingsForm.open_registration_expiry" style="color: #909399; font-size: 12px; margin-top: 4px;">
                    自动关闭时间：{{ formatDateTime(siteSettingsForm.open_registration_expiry) }}
                  </div>
                </div>
              </el-form-item>
            </el-form>

            <el-divider content-position="left">LDAP认证</el-divider>
            <el-form :model="siteSettingsForm" label-width="180px">
              <el-form-item label="启用LDAP认证">
                <el-switch
                  v-model="siteSettingsForm.ldap_enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：开启后用户可以使用LDAP账号登录，关闭后只能使用本地账号登录
                </div>
              </el-form-item>
              
              <template v-if="siteSettingsForm.ldap_enabled">
                <el-divider content-position="left">LDAP服务器配置</el-divider>
                
                <el-form-item label="LDAP服务器地址" required>
                  <el-input v-model="siteSettingsForm.ldap_config.server" placeholder="例如: ldap.example.com" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：LDAP服务器的主机名或IP地址
                  </div>
                </el-form-item>
                
                <el-form-item label="LDAP端口" required>
                  <el-input-number v-model="siteSettingsForm.ldap_config.port" :min="1" :max="65535" style="width: 200px" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：标准LDAP端口为389，LDAPS端口为636
                  </div>
                </el-form-item>
                
                <el-form-item label="使用SSL加密">
                  <el-switch
                    v-model="siteSettingsForm.ldap_config.use_ssl"
                    active-text="是"
                    inactive-text="否"
                  />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：启用SSL后使用LDAPS协议（端口636）
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">管理员绑定配置</el-divider>
                
                <el-form-item label="管理员DN">
                  <el-input v-model="siteSettingsForm.ldap_config.bind_dn" placeholder="例如: cn=admin,dc=example,dc=com" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：用于搜索用户的LDAP管理员账号DN
                  </div>
                </el-form-item>
                
                <el-form-item label="管理员密码">
                  <el-input v-model="siteSettingsForm.ldap_config.bind_password" type="password" placeholder="管理员密码" show-password />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：用于搜索用户的LDAP管理员密码
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">用户搜索配置</el-divider>
                
                <el-form-item label="用户搜索基础DN" required>
                  <el-input v-model="siteSettingsForm.ldap_config.user_search_base" placeholder="例如: ou=users,dc=example,dc=com" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：用户搜索的起始DN
                  </div>
                </el-form-item>
                
                <el-form-item label="用户搜索过滤器" required>
                  <el-input v-model="siteSettingsForm.ldap_config.user_search_filter" placeholder="例如: (uid={username})" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：使用{username}作为用户名占位符，例如: (uid={username}) 或 (sAMAccountName={username})
                  </div>
                </el-form-item>
                
                <el-form-item label="用户DN模板">
                  <el-input v-model="siteSettingsForm.ldap_config.user_dn_template" placeholder="例如: uid={username},ou=users,dc=example,dc=com" />
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：如果填写此项，将直接使用模板进行认证，不进行用户搜索
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">默认用户配置</el-divider>
                
                <el-form-item label="默认用户角色">
                  <el-select v-model="siteSettingsForm.ldap_config.default_role" placeholder="选择默认角色" style="width: 200px">
                    <el-option label="课程管理员" value="course_admin" />
                    <el-option label="系统管理员" value="system_admin" />
                    <el-option label="系统审计员" value="system_audit" />
                  </el-select>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：LDAP用户首次登录时的默认角色（超级管理员角色需要手动分配）
                  </div>
                </el-form-item>
                
                <el-divider content-position="left">角色映射配置</el-divider>
                
                <el-form-item label="角色映射方式">
                  <el-radio-group v-model="siteSettingsForm.ldap_config.role_mapping_type">
                    <el-radio value="default">使用默认角色</el-radio>
                    <el-radio value="attribute">根据LDAP属性映射</el-radio>
                  </el-radio-group>
                  <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 提示：选择"根据LDAP属性映射"可以根据用户的组织单位或组成员身份自动分配角色
                  </div>
                </el-form-item>
                
                <template v-if="siteSettingsForm.ldap_config.role_mapping_type === 'attribute'">
                  <el-form-item label="角色映射属性">
                    <el-select v-model="siteSettingsForm.ldap_config.role_mapping_attribute" placeholder="选择映射属性" style="width: 200px">
                      <el-option label="组织单位(OU)" value="ou" />
                      <el-option label="组成员身份" value="memberOf" />
                      <el-option label="自定义属性" value="custom" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="课程管理员映射" v-if="siteSettingsForm.ldap_config.role_mapping_attribute !== 'custom'">
                    <el-input v-model="siteSettingsForm.ldap_config.role_mappings.course_admin" placeholder="例如: Teachers 或 ou=Teachers" />
                  </el-form-item>
                  
                  <el-form-item label="系统管理员映射" v-if="siteSettingsForm.ldap_config.role_mapping_attribute !== 'custom'">
                    <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_admin" placeholder="例如: Admins 或 ou=Admins" />
                  </el-form-item>
                  
                  <el-form-item label="系统审计员映射" v-if="siteSettingsForm.ldap_config.role_mapping_attribute !== 'custom'">
                    <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_audit" placeholder="例如: Auditors 或 ou=Auditors" />
                  </el-form-item>
                  
                  <template v-if="siteSettingsForm.ldap_config.role_mapping_attribute === 'custom'">
                    <el-form-item label="自定义属性名">
                      <el-input v-model="siteSettingsForm.ldap_config.custom_attribute_name" placeholder="例如: department" />
                    </el-form-item>
                    
                    <el-form-item label="课程管理员值">
                      <el-input v-model="siteSettingsForm.ldap_config.role_mappings.course_admin" placeholder="例如: teacher" />
                    </el-form-item>
                    
                    <el-form-item label="系统管理员值">
                      <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_admin" placeholder="例如: admin" />
                    </el-form-item>
                    
                    <el-form-item label="系统审计员值">
                      <el-input v-model="siteSettingsForm.ldap_config.role_mappings.system_audit" placeholder="例如: auditor" />
                    </el-form-item>
                  </template>
                </template>
                
                <el-form-item>
                  <el-button type="primary" @click="testLDAPConnection" :loading="testingLDAP">测试LDAP连接</el-button>
                  <el-button @click="resetLDAPConfig">重置LDAP配置</el-button>
                </el-form-item>
              </template>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="日志配置">
            <div style="margin-bottom: 20px; color: #606266;">
              <strong>配置说明：</strong>配置系统日志记录的级别和输出控制。
            </div>
            
            <el-form :model="siteSettingsForm" label-width="160px">
              <el-form-item label="启用后端日志记录">
                <el-switch
                  v-model="siteSettingsForm.log_enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：关闭后将不再记录任何系统日志
                </div>
              </el-form-item>
              <el-form-item label="后端日志级别">
                <el-select v-model="siteSettingsForm.log_level" placeholder="选择日志级别" style="width: 200px">
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                </el-select>
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：只记录指定级别及以上的日志
                </div>
              </el-form-item>
              
              <el-form-item label="启用前端日志记录">
                <el-switch
                  v-model="siteSettingsForm.frontend_log_enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
                <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> 提示：关闭后将不在浏览器控制台输出任何日志
                </div>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
        </el-tabs>
        <template #footer>
          <el-button @click="siteSettingsDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSiteSettingsSave">保存所有配置</el-button>
        </template>
    </el-dialog>

    <!-- ==================== 智能指令示例管理弹窗 ==================== -->
    <el-dialog 
      v-model="smartCommandExamplesDialogVisible" 
      title="智能指令示例管理" 
      width="90%"
      :close-on-click-modal="false"
      draggable
    >
      <!-- 顶部操作区 -->
      <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
        <el-button type="primary" @click="startBatchTest('ai')" :loading="testingAll && !isBatchPaused">
          <el-icon><Refresh /></el-icon>
          分批测试AI解析
        </el-button>
        <el-button type="warning" @click="startBatchTest('regex')" :loading="testingAll && !isBatchPaused">
          <el-icon><Setting /></el-icon>
          分批测试正则解析
        </el-button>
        
        <el-divider direction="vertical" />
        
        <el-input 
          v-model="singleTestInput" 
          placeholder="输入要测试的指令..." 
          style="width: 400px"
          @keyup.enter="testSingleCommand"
        />
        <el-button type="success" @click="testSingleCommand" :loading="testingSingle">
          快速测试(AI)
        </el-button>
        
        <el-divider direction="vertical" />
        
        <el-button type="primary" @click="showAddExampleDialog">
          <el-icon><Plus /></el-icon>
          新增示例
        </el-button>

        <!-- 继续测试按钮（仅在暂停时显示） -->
        <el-button v-if="isBatchPaused" type="success" @click="continueBatchTest('ai')">
          继续测试下一组(AI)
        </el-button>
      </div>

      <!-- 搜索区域 -->
      <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
        <el-input
          v-model="examplesSearch"
          placeholder="模糊搜索：分类、动作名称、示例文本、预期意图、描述..."
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
          搜索
        </el-button>
        <el-button @click="resetExamplesSearch">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>

      <!-- 单条测试结果展示 -->
      <el-alert 
        v-if="singleTestResult" 
        :type="singleTestResult.success ? 'success' : 'error'"
        :title="singleTestResult.success ? '解析成功' : '解析失败'"
        :description="singleTestResult.message"
        show-icon
        closable
        style="margin-bottom: 20px"
      >
        <div v-if="singleTestResult.parsed_intent" style="margin-top: 10px;">
          <strong>解析意图：</strong>{{ singleTestResult.parsed_intent }}
        </div>
        <div v-if="singleTestResult.parsed_fields" style="margin-top: 5px;">
          <strong>解析字段：</strong>
          <pre style="background: #f5f7fa; padding: 10px; border-radius: 4px; margin-top: 5px;">{{ JSON.stringify(singleTestResult.parsed_fields, null, 2) }}</pre>
        </div>
      </el-alert>

      <!-- 批量测试结果展示 -->
      <el-alert 
        v-if="testResults.length > 0" 
        type="info"
        :title="`测试结果汇总：成功 ${testResults.filter(r => r.success).length} 条，失败 ${testResults.filter(r => !r.success).length} 条`"
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
        <el-table-column prop="command_text" label="指令文本" min-width="200" show-overflow-tooltip />
        <el-table-column prop="expected_intent" label="预期意图" width="120" />
        <el-table-column prop="parsed_intent" label="实际意图" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.intent_match ? '#67C23A' : '#F56C6C' }">
              {{ row.parsed_intent || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="字段匹配" width="100">
          <template #default="{ row }">
            <span v-if="row.field_comparison">
              {{ (row.field_comparison.match_rate * 100).toFixed(0) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'">
              {{ row.success ? '通过' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="详情" min-width="150">
          <template #default="{ row }">
            <div v-if="row.field_comparison && row.field_comparison.mismatched_fields">
              <div v-for="(val, key) in row.field_comparison.mismatched_fields" :key="key" style="font-size: 12px; color: #F56C6C;">
                {{ key }}: 期望={{ val.expected }}, 实际={{ val.actual }}
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
        <el-table-column prop="category" label="分类" width="120" sortable="custom">
          <template #default="{ row }">
            {{ categoryOptions.find(opt => opt.value === row.category)?.label || row.category }}
          </template>
        </el-table-column>
        <el-table-column prop="action_name" label="动作名称" width="120" sortable="custom" />
        <el-table-column prop="example_text" label="示例文本" min-width="250" show-overflow-tooltip />
        <el-table-column prop="expected_intent" label="预期意图" width="120" sortable="custom" />
        <el-table-column label="预期字段" width="100">
          <template #default="{ row }">
            <el-popover trigger="hover" placement="top">
              <template #reference>
                <el-button link type="primary">查看</el-button>
              </template>
              <pre style="max-width: 300px;">{{ JSON.stringify(row.expected_fields, null, 2) }}</pre>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="80" sortable="custom">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="优先级" width="80" sortable="custom" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showEditExampleDialog(row)">编辑</el-button>
            <el-button link type="success" size="small" @click="testSingleExampleWithMode(row, 'ai')">测试AI</el-button>
            <el-button link type="warning" size="small" @click="testSingleExampleWithMode(row, 'regex')">测试正则</el-button>
            <el-button link type="danger" size="small" @click="deleteExample(row)">删除</el-button>
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
        <el-button @click="smartCommandExamplesDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 新增/编辑示例弹窗 ==================== -->
    <el-dialog 
      v-model="exampleEditDialogVisible" 
      :title="currentExample ? '编辑示例' : '新增示例'" 
      width="600px"
      draggable
    >
      <el-form :model="exampleForm" label-width="120px">
        <el-form-item label="分类" required>
          <el-select v-model="exampleForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option 
              v-for="opt in categoryOptions" 
              :key="opt.value" 
              :label="opt.label" 
              :value="opt.value" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="动作名称" required>
          <el-input v-model="exampleForm.action_name" placeholder="例如：添加科目、创建排课" />
        </el-form-item>
        
        <el-form-item label="示例文本" required>
          <el-input 
            v-model="exampleForm.example_text" 
            type="textarea" 
            :rows="3"
            placeholder="例如：添加科目数学，优先级5" 
          />
        </el-form-item>
        
        <el-form-item label="预期意图">
          <el-input v-model="exampleForm.expected_intent" placeholder="例如：add_course" />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            可选值：add_course, update_course, search_courses, add_teacher, update_teacher, search_teachers, add_class, update_class, search_classes, add_student, update_student, search_students, add_room, update_room, search_rooms, add_leave, add_holiday, collect_fee, refund_fee, search_fees, add_grade, search_grades, create_schedule, complete_schedule, cancel_schedule, postpone_schedule, search_schedules, advanced_search
          </div>
        </el-form-item>
        
        <el-form-item label="预期字段(JSON)">
          <div style="margin-bottom: 10px;">
            <el-button size="small" type="primary" @click="autoGenerateExpectedFields">
              <el-icon><MagicStick /></el-icon>
              自动生成
            </el-button>
            <el-button size="small" type="success" @click="showTemplateDialog">
              <el-icon><Document /></el-icon>
              选择模板
            </el-button>
            <el-button size="small" @click="formatJson">
              <el-icon><Sort /></el-icon>
              格式化
            </el-button>
          </div>
          <el-input 
            v-model="exampleForm.expected_fields_json" 
            type="textarea" 
            :rows="8"
            placeholder='{"action": "navigate", "path": "/admin/students", "storage_data": {...}}' 
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            填写解析后应该得到的完整数据结构（JSON格式），包含 action、path、storage_data 等字段
          </div>
          <div v-if="jsonError" style="font-size: 12px; color: #f56c6c; margin-top: 5px;">
            {{ jsonError }}
          </div>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="exampleForm.description" 
            type="textarea" 
            :rows="2"
            placeholder="示例说明" 
          />
        </el-form-item>
        
        <el-form-item label="是否激活">
          <el-switch v-model="exampleForm.is_active" />
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-input-number v-model="exampleForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exampleEditDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveExample">保存</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 预期字段模板选择弹窗 ==================== -->
    <el-dialog 
      v-model="templateDialogVisible" 
      title="选择预期字段模板" 
      width="700px"
      draggable
    >
      <div style="margin-bottom: 15px; color: #606266;">
        选择一个模板作为基础，然后根据实际需求修改字段值
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
        <el-button @click="templateDialogVisible = false">关闭</el-button>
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
    ElMessage.error('获取日志失败')
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
    ElMessage.error('获取归档列表失败')
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
    ElMessage.error('查看归档日志失败: ' + (error.response?.data?.detail || error.message))
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
    ElMessage.error('下载归档文件失败')
  }
}

const deleteArchiveFile = async (filename) => {
  try {
    await ElMessageBox.confirm(`确定删除归档文件 "${filename}" 吗？删除后无法恢复。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await api.delete(`/logs/backup/${encodeURIComponent(filename)}`)
    ElMessage.success('归档文件已删除')
    fetchArchiveList()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('删除归档文件失败:', error)
      ElMessage.error('删除归档文件失败')
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
        ElMessage.success('测试邮件发送成功！请检查收件箱')
      } catch (error) {
        window.logger.error('邮件测试失败:', error)
        ElMessage.error('邮件测试失败: ' + (error.response?.data?.detail || error.message))
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
    ElMessage.error('备份日志失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    logsBackupLoading.value = false
  }
}

const handleClearLogsConfirm = () => {
  const hasFilter = logsFilters.value.start_date || logsFilters.value.end_date || logsFilters.value.user || logsFilters.value.level || logsFilters.value.search
  const filterDesc = hasFilter ? '当前筛选条件下的' : '所有'
  ElMessageBox.confirm(
    `确定要清除${filterDesc}日志吗？清除前将自动备份，备份文件可在服务器备份目录中找到。`,
    '清除日志确认',
    { confirmButtonText: '确定清除', cancelButtonText: '取消', type: 'warning' }
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
    ElMessage.error('清除日志失败: ' + (error.response?.data?.detail || error.message))
  }
}

const goToDatabaseManagement = () => {
  router.push('/admin/database')
}

const showLicenseWarning = (featureName) => {
  ElMessage.warning(`${featureName}为授权功能，请在系统授权管理中激活`)
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
    '小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
    '初中一年级', '初中二年级', '初中三年级',
    '高中一年级', '高中二年级', '高中三年级',
    '大学一年级', '大学二年级', '大学三年级', '大学四年级',
    '研究生一年级', '研究生二年级', '研究生三年级'
  ],
  exam_stages: [
    '秋季月考A', '秋季月考B', '秋季期中', '秋季月考C', '秋季月考D', '秋季期末',
    '春季月考A', '春季月考B', '春季期中', '春季月考C', '春季月考D', '春季期末',
    '中考一模', '中考二模', '中考三模', '中考', '会考',
    '高考特训A', '高考特训B', '高考特训C', '春季高考',
    '高考一模', '高考二模', '高考三模', '夏季高考'
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
  schedule_change: { default: [''] }
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
  { label: '科目管理', value: 'course_management' },
  { label: '导师管理', value: 'teacher_management' },
  { label: '学员管理', value: 'student_management' },
  { label: '班级管理', value: 'class_management' },
  { label: '教室管理', value: 'room_management' },
  { label: '排课管理', value: 'schedule_management' },
  { label: '请假管理', value: 'leave_management' },
  { label: '假期管理', value: 'holiday_management' },
  { label: '课费管理', value: 'fee_management' },
  { label: '成绩管理', value: 'grade_management' },
  { label: '数据查询', value: 'data_search' }
]

const validateAIUrl = () => {
  if (!aiConfig.value.api_url) {
    apiUrlError.value = ''
    return
  }
  
  const urlPattern = /^https?:\/\/.+/i
  if (!urlPattern.test(aiConfig.value.api_url)) {
    apiUrlError.value = 'API地址必须以 http:// 或 https:// 开头'
  } else {
    apiUrlError.value = ''
  }
}

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})
 
const siteSettingsRules = {
  site_name: [{ required: true, message: '请输入机构名称', trigger: 'blur' }],
  site_url: [
    { required: true, message: '请输入本站内网IP', trigger: 'blur' },
    { 
      pattern: /^(\d{1,3}\.){3}\d{1,3}$|^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/,
      message: '请务必输入[有效真实准确的本网站的内网IP地址]',
      trigger: 'blur'
    }
  ]
}

const emailConfigRules = {
  smtp_host: [{ required: true, message: '请输入SMTP服务器', trigger: 'blur' }],
  smtp_port: [{ required: true, message: '请输入SMTP端口', trigger: 'blur' }],
  smtp_user: [{ required: true, message: '请输入发送邮箱', trigger: 'blur' }],
  smtp_password: [{ required: true, message: '请输入邮箱密码/授权码', trigger: 'blur' }],
  smtp_from_name: [{ required: true, message: '请输入发件人名称', trigger: 'blur' }]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.value.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
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
        ElMessage.success('密码修改成功')
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
    urlToTest = wechatConfig.value.schedule_change[key]?.[index]
  }

  if (!urlToTest) {
    ElMessage.warning('请先填写 Webhook 地址')
    return
  }

  const loadingKey = type === 'fee_alert' ? `fee_${index}` : `${key}_${index}`
  testingUrl.value = loadingKey

  try {
    // 调用后端接口，传入要测试的具体 URL
    await api.post('/settings/test-wechat-url', { webhook_url: urlToTest })
    ElMessage.success('测试消息发送成功！')
  } catch (error) {
    window.logger.error(error)
    ElMessage.error(error.response?.data?.detail || '测试发送失败')
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
        window.logger.log('[DEBUG] 保存成功，服务器返回的ai_config:', response.data.ai_config)
        
        ElMessage.success('配置已保存并生效')
        siteSettingsDialogVisible.value = false
        updateSiteInfo()
      } catch (error) {
        window.logger.error('保存失败:', error)
        ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message))
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
          // 只有当解析出的对象确实有我们需要的键时才覆盖，否则保持默认结构
          if (parsed.fee_alert || parsed.schedule_change) {
            wechatConfig.value = parsed
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
      window.logger.warn('items不是数组，重置为空数组', items)
      items = []
    }
    examplesList.value = items
    examplesPagination.value.total = total
    
    window.logger.log('最终列表数据条数:', items.length)
    window.logger.log('最终总条数:', total)
  } catch (error) {
    window.logger.error('获取示例列表失败:', error)
    ElMessage.error('获取示例列表失败')
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
      ElMessage.success(`${mode === 'ai' ? 'AI' : '正则'}解析成功`)
    } else {
      ElMessage.warning(response.data.message)
    }
  } catch (error) {
    window.logger.error('测试失败:', error)
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      ElMessage.error('请求超时，请检查网络或AI服务状态')
    } else {
      ElMessage.error('测试失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    testingSingle.value = false
  }
}

const startBatchTest = async (mode) => {
  if (examplesList.value.length === 0) {
    ElMessage.warning('当前列表没有可测试的示例')
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
    ElMessage.error('数据异常，请刷新页面重试')
    return
  }
  
  const batchSize = 5
  const endIndex = Math.min(batchTestingIndex.value + batchSize, examplesList.value.length)
  
  if (batchTestingIndex.value >= examplesList.value.length) {
    testingAll.value = false
    ElMessage.success('所有示例测试完成！')
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
        message: error.message.includes('timeout') ? '超时' : '请求失败',
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
    ElMessage.success('JSON格式化成功')
  } catch (e) {
    jsonError.value = 'JSON格式错误: ' + e.message
    ElMessage.error('JSON格式错误，无法格式化')
  }
}

const autoGenerateExpectedFields = async () => {
  if (!exampleForm.value.example_text) {
    ElMessage.warning('请先输入示例文本')
    return
  }
  
  if (!exampleForm.value.expected_intent) {
    ElMessage.warning('请先选择或输入预期意图')
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
      ElMessage.success('自动生成成功')
    } else {
      ElMessage.warning('自动生成失败: ' + response.data.message)
    }
  } catch (error) {
    window.logger.error('自动生成预期字段失败:', error)
    ElMessage.error('自动生成失败，请手动填写')
  }
}

const showTemplateDialog = () => {
  templateDialogVisible.value = true
}

// 常用模板定义
const commonTemplates = {
  search_template: {
    name: '查询列表模板',
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
    name: '创建记录模板',
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
    name: '更新记录模板',
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
    name: '排课模板',
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
    name: '确认操作模板',
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
  ElMessage.success('模板应用成功')
}

// ==================== 保存示例方法 ====================

const saveExample = async () => {
  try {
    // 验证JSON格式
    let expectedFields = {}
    try {
      expectedFields = JSON.parse(exampleForm.value.expected_fields_json)
    } catch (e) {
      ElMessage.error('预期字段JSON格式错误')
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
    
    ElMessage.success(currentExample.value ? '更新成功' : '创建成功')
    exampleEditDialogVisible.value = false
    fetchExamplesList()
  } catch (error) {
    window.logger.error('保存示例失败:', error)
    ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

const deleteExample = async (example) => {
  try {
    await ElMessageBox.confirm('确定删除该示例吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.delete(`/smart-command-examples/delete/${example.id}`)
    ElMessage.success('删除成功')
    fetchExamplesList()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('删除示例失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const testAllExamples = async () => {
  testingAll.value = true
  testResults.value = []
  
  try {
    const response = await api.post('/smart-command-examples/test-all')
    testResults.value = response.data.results
    
    const summary = `测试完成！共 ${response.data.total} 条，成功 ${response.data.success_count} 条，失败 ${response.data.failed_count} 条，耗时 ${response.data.test_duration_ms.toFixed(2)}ms`
    ElMessage.info(summary)
  } catch (error) {
    window.logger.error('批量测试失败:', error)
    ElMessage.error('测试失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testingAll.value = false
  }
}

const testSingleCommand = async () => {
  if (!singleTestInput.value.trim()) {
    ElMessage.warning('请输入要测试的指令')
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
      ElMessage.success('解析成功')
    } else {
      ElMessage.warning(response.data.message)
    }
  } catch (error) {
    window.logger.error('单条测试失败:', error)
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      ElMessage.error('AI 响应超时，请检查网络连接或尝试简化指令')
    } else {
      ElMessage.error('测试失败: ' + (error.response?.data?.detail || error.message))
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
    ElMessage.success('LOGO上传成功')
  } else if (response && response.data && response.data.url) {
    siteSettingsForm.value.site_logo = response.data.url
    ElMessage.success('LOGO上传成功')
  } else {
    ElMessage.error('LOGO上传失败')
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
      ElMessage.success('公众号二维码上传成功')
    } else if (type === 'work_wechat') {
      siteSettingsForm.value.work_wechat_qrcode = url
      ElMessage.success('企业微信二维码上传成功')
    }
  } else {
    ElMessage.error('二维码上传失败')
  }
}

const beforeQrcodeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
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
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过2MB!')
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
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
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
      ElMessage.error(`获取密码重置请求失败: ${error.response.status} - ${JSON.stringify(error.response.data)}`)
    } else {
      ElMessage.error('获取密码重置请求失败，请检查网络连接')
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
    'pending': '待处理',
    'completed': '已完成',
    'rejected': '已拒绝'
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
        
        ElMessage.success('密码重置成功')
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
    await ElMessageBox.confirm('确定拒绝该密码重置请求吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.put(`/auth/password-reset-requests/${request.id}`, {
      status: 'rejected'
    })
    
    ElMessage.success('已拒绝该请求')
    showPasswordResetRequests() // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('拒绝请求失败:', error)
    }
  }
}

const testAIConnection = async () => {
  if (!aiConfig.value.api_url || !aiConfig.value.api_key) {
    ElMessage.warning('请先填写API地址和API密钥')
    return
  }

  // 验证API地址格式
  const urlPattern = /^https?:\/\/.+/i
  if (!urlPattern.test(aiConfig.value.api_url)) {
    ElMessage.error('API地址格式不正确，必须以 http:// 或 https:// 开头')
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
    
    ElMessage.success(response.data.message || 'AI连接测试成功！')
  } catch (error) {
    window.logger.error('AI连接测试失败:', error)
    ElMessage.error('测试失败: ' + (error.response?.data?.detail || error.message))
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
  ElMessage.success('已重置AI配置')
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
  ElMessage.success('已重置LDAP配置')
}

// 考试阶段的管理
const defaultExamStages = [
  '秋季月考A', '秋季月考B', '秋季期中', '秋季月考C', '秋季月考D', '秋季期末',
  '春季月考A', '春季月考B', '春季期中', '春季月考C', '春季月考D', '春季期末',
  '中考一模', '中考二模', '中考三模', '中考', '会考',
  '高考特训A', '高考特训B', '高考特训C', '春季高考',
  '高考一模', '高考二模', '高考三模', '夏季高考'
]
const addExamStage = () => {
  siteSettingsForm.value.exam_stages.push('')
}
const removeExamStage = (index) => {
  siteSettingsForm.value.exam_stages.splice(index, 1)
}
const resetExamStages = () => {
  siteSettingsForm.value.exam_stages = [...defaultExamStages]
  ElMessage.success('已恢复默认考试阶段')
}

//年级选项的管理
const defaultGradeOptions = [
  '小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
  '初中一年级', '初中二年级', '初中三年级',
  '高中一年级', '高中二年级', '高中三年级',
  '大学一年级', '大学二年级', '大学三年级', '大学四年级',
  '研究生一年级', '研究生二年级', '研究生三年级'
]
const addGradeOption = () => {
  siteSettingsForm.value.grade_options.push('')
}
const removeGradeOption = (index) => {
  siteSettingsForm.value.grade_options.splice(index, 1)
}
const resetGradeOptions = () => {
  siteSettingsForm.value.grade_options = [...defaultGradeOptions]
  ElMessage.success('已恢复默认年级选项')
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