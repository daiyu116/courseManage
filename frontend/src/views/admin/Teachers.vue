// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="teachers-page">
    <!-- 导航栏 -->
    <el-card class="nav-card" style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/dashboard')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            面板
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/courses')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            科目管理
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="success" @click="goToPage('/admin/classes')" style="width: 100%;height: 100%;">
            <el-icon><User /></el-icon>
            班级管理
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="warning" @click="goToPage('/admin/students')" style="width: 100%;height: 100%;">
            <el-icon><UserFilled /></el-icon>
            学员管理
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="info" @click="goToPage('/admin/rooms')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
            教室管理
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="danger" @click="goToPage('/admin/leaves')" style="width: 100%;height: 100%;">
            <el-icon><Calendar /></el-icon>
            假日管理
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/schedules')" style="width: 100%;height: 100%;">
            <el-icon><Clock /></el-icon>
            排课管理
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/conditions')" style="width: 100%;height: 100%;">
            <el-icon><Setting /></el-icon>
            条件管理
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>导师管理</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回上一页
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              新增导师
            </el-button>
            <el-button type="success" @click="showBatchAddDialog">
              <el-icon><Upload /></el-icon>
              批量添加
            </el-button>
          </div>
        </div>
      </template>

      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索导师姓名、代码、部门、联系方式"
          style="width: 350px"
          clearable
          @clear="resetFilters"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
        <el-select v-model="isActiveFilter" placeholder="本机构在职状态" clearable style="width: 150px" @change="handleFilterChange">
          <el-option label="在职" :value="true" />
          <el-option label="离职" :value="false" />
        </el-select>
        <el-button @click="resetFilters" style="width: 50px">重置</el-button>
      </div>

      <div class="fake-scrollbar" ref="topScrollbarRef">
        <div class="scrollbar-inner" :style="{ width: scrollbarWidth + 'px' }"></div>
      </div>
      <el-table :data="teachers" stripe v-loading="loading" style="margin-top: 0" @sort-change="handleSortChange" ref="mainTableRef">
          <el-table-column prop="id" label="ID" width="70" sortable />
          <el-table-column prop="code" label="导师代码" width="120" sortable />
          <el-table-column prop="name" label="导师姓名" width="120" sortable />
          <el-table-column label="进驻机构日期" width="150" sortable>
            <template #default="{ row }">
              {{ row.join_date ? new Date(row.join_date).toLocaleDateString('zh-CN') : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="title" label="职称" width="120" sortable />
          <el-table-column prop="department" label="部门" width="150" sortable />
          <el-table-column label="联系电话" width="150" sortable >
            <template #default="{ row }">
              {{ row.contact_phone || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="电子邮箱" width="200" sortable >
            <template #default="{ row }">
              {{ row.email || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="非节假每周可安排日" width="200">
            <template #default="{ row }">
              <el-tag v-for="day in parseAvailableDays(row.available_days)" :key="day" size="small" style="margin-right: 5px; margin-bottom: 5px;">
                {{ day }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="可安排课时段" width="300">
            <template #default="{ row }">
              <el-tag v-for="slot in parseAvailableTimeSlots(row.available_time_slots)" :key="slot" size="small" style="margin-right: 5px; margin-bottom: 5px;">
                {{ slot }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="max_weekly_hours" label="周最大课时" width="100" />
          <el-table-column label="节假日可排课" width="100">
            <template #default="{ row }">
              <el-tag :type="row.allow_holiday_scheduling ? 'success' : 'info'">
                {{ row.allow_holiday_scheduling ? '可排课' : '不可排课' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="本机构在职状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '在职' : '离职' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
        <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
            <el-form-item label="导师代码" prop="code">
              <el-input v-model="form.code" :placeholder="lastTeacherCode ? `请输入导师代码(不能与现有重复否则无法创建，当前已到：${lastTeacherCode})` : '请输入导师代码(不能与现有重复)'" :disabled="!!form.id" />
            </el-form-item>
            <el-form-item label="导师姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入导师姓名" />
            </el-form-item>
            <el-form-item label="进驻机构日期" prop="join_date">
              <el-date-picker
                v-model="form.join_date"
                type="date"
                placeholder="选择进驻机构日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="职称" prop="title">
              <el-input v-model="form.title" placeholder="请输入职称" />
            </el-form-item>
            <el-form-item label="部门" prop="department">
              <el-input v-model="form.department" placeholder="请输入部门" />
            </el-form-item>
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="form.contact_phone" placeholder="请输入手机或座机号码" />
            </el-form-item>
            <el-form-item label="电子邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入电子邮箱" />
            </el-form-item>
            <el-form-item label="周最大课时" prop="max_weekly_hours">
              <el-input-number v-model="form.max_weekly_hours" :min="1" :max="100" />
            </el-form-item>
            <el-form-item label="非节假每周可安排日" prop="available_days">
                <el-checkbox-group v-model="selectedDays">
                    <el-checkbox :value="1">周一</el-checkbox>
                    <el-checkbox :value="2">周二</el-checkbox>
                    <el-checkbox :value="3">周三</el-checkbox>
                    <el-checkbox :value="4">周四</el-checkbox>
                    <el-checkbox :value="5">周五</el-checkbox>
                    <el-checkbox :value="6">周六</el-checkbox>
                    <el-checkbox :value="7">周日</el-checkbox>
                </el-checkbox-group>
            </el-form-item>
            <el-form-item label="节假日可排课">
              <el-switch v-model="form.allow_holiday_scheduling" />
              <span style="margin-left: 10px; color: #999; font-size: 12px;">
                勾选后，节假日(包含法定与自定义假日)也可以安排课程
              </span>
            </el-form-item>
            <el-form-item label="可安排课时段" prop="available_time_slots">
              <el-row :gutter="10">
                <el-col :span="12">
                  <div style="margin-bottom: 5px; font-size: 12px; color: #909399;">
                      <el-icon><InfoFilled /></el-icon> 上午
                  </div>
                  <el-checkbox-group v-model="selectedTimeSlots" @change="handleTimeSlotChange">
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="08:00-10:00" :class="{ 'overlapping-slot': isOverlappingSlot('08:00-10:00') }">08:00-10:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="10:00-12:00" :class="{ 'overlapping-slot': isOverlappingSlot('10:00-12:00') }">10:00-12:00</el-checkbox>
                    </div>
                  </el-checkbox-group>
                </el-col>
                <el-col :span="12">
                  <div style="margin-bottom: 5px; font-size: 12px; color: #909399;">
                      <el-icon><InfoFilled /></el-icon> 下午（重叠时间段）
                  </div>
                  <el-checkbox-group v-model="selectedTimeSlots" @change="handleTimeSlotChange">
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="13:30-15:30" :class="{ 'overlapping-slot': isOverlappingSlot('13:30-15:30') }">13:30-15:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="14:00-16:00" :class="{ 'overlapping-slot': isOverlappingSlot('14:00-16:00') }">14:00-16:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="14:30-16:30" :class="{ 'overlapping-slot': isOverlappingSlot('14:30-16:30') }">14:30-16:30</el-checkbox>
                    </div>                    
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="15:30-17:30" :class="{ 'overlapping-slot': isOverlappingSlot('15:30-17:30') }">15:30-17:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="16:00-18:00" :class="{ 'overlapping-slot': isOverlappingSlot('16:00-18:00') }">16:00-18:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="16:30-18:30" :class="{ 'overlapping-slot': isOverlappingSlot('16:30-18:30') }">16:30-18:30</el-checkbox>
                    </div>                    
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="17:30-19:30" :class="{ 'overlapping-slot': isOverlappingSlot('17:30-19:30') }">17:30-19:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="18:00-20:00" :class="{ 'overlapping-slot': isOverlappingSlot('18:00-20:00') }">18:00-20:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="18:30-20:30" :class="{ 'overlapping-slot': isOverlappingSlot('18:30-20:30') }">18:30-20:30</el-checkbox>
                    </div>                    
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="19:30-21:30" :class="{ 'overlapping-slot': isOverlappingSlot('19:30-21:30') }">19:30-21:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="20:00-22:00" :class="{ 'overlapping-slot': isOverlappingSlot('20:00-22:00') }">20:00-22:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="20:30-22:30" :class="{ 'overlapping-slot': isOverlappingSlot('20:30-22:30') }">20:30-22:30</el-checkbox>
                    </div>
                  </el-checkbox-group>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item label="无需填写反馈">
              <el-switch v-model="form.no_feedback_required" />
              <span style="margin-left: 10px; color: #999; font-size: 12px;">
                勾选后，该导师的任何课程可以不写反馈就完训结课
              </span>
            </el-form-item>
            <el-form-item label="本机构在职状态" prop="is_active">
              <el-switch v-model="form.is_active" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit">确定</el-button>
        </template>
        <el-form-item label="离职日期" prop="end_date" v-if="!form.is_active">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="选择离职日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
    </el-dialog>
    <!-- 批量添加导师对话框 -->
    <el-dialog v-model="batchAddDialogVisible" title="批量添加导师" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          title="批量添加说明"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>请按照以下格式输入导师信息，每行一个导师：</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              代码(*必填),姓名(*必填),进驻日期(YYYY-MM-DD),职称,部门,联系方式,电子邮箱,周最大课时,可排课日(1-7,逗号分隔)
            </div>
            <div style="margin-top: 10px;">例如：</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              T001,张老师,2024-01-15,高级导师,数学部,13800138000,zhang@example.com,40,6,7<br/>
              T002,李老师,2024-02-20,中级导师,英语部,13900139000,li@example.com,35,1,2,3,4,5<br/>
              T003,王老师,, , , , , ,6,7
            </div>
            <div style="margin-top: 10px;">注意：</div>
            <ul style="margin-top: 5px;">
              <li>代码不能与现有导师重复，上一个导师代码：<span v-if="lastTeacherCode">{{ lastTeacherCode }}</span><span v-else>无</span>，请在这个代码+1的基础上开始</li>
              <li>可排课日：1=周一, 2=周二, 3=周三, 4=周四, 5=周五, 6=周六, 7=周日</li>
              <li>可排课日支持多个值，用逗号分隔，如：6,7 表示周六和周日</li>
              <li>可在上方选择可排课时间段，所有批量添加的导师都会应用相同的设置</li>
            </ul>
          </template>
        </el-alert>
      </div>
      <el-form>
        <el-form-item label="可排课时间段">
          <el-select
            v-model="selectedBatchTimeSlots"
            multiple
            placeholder="请选择可排课时间段（可多选，不选则使用默认）"
            style="width: 100%"
            @change="handleBatchTimeSlotChange"
          >
            <el-option label="08:00-10:00" value="08:00-10:00" />
            <el-option label="10:00-12:00" value="10:00-12:00" />
            <el-option label="13:30-15:30" value="13:30-15:30" />
            <el-option label="14:00-16:00" value="14:00-16:00" />
            <el-option label="14:30-16:30" value="14:30-16:30" />
            <el-option label="15:30-17:30" value="15:30-17:30" />
            <el-option label="16:00-18:00" value="16:00-18:00" />
            <el-option label="16:30-18:30" value="16:30-18:30" />
            <el-option label="17:30-19:30" value="17:30-19:30" />
            <el-option label="18:00-20:00" value="18:00-20:00" />
            <el-option label="18:30-20:30" value="18:30-20:30" />
            <el-option label="19:30-21:30" value="19:30-21:30" />
            <el-option label="20:00-22:00" value="20:00-22:00" />
            <el-option label="20:30-22:30" value="20:30-22:30" />
          </el-select>
          <div style="margin-top: 5px; font-size: 12px; color: #909399;">
            <el-icon><InfoFilled /></el-icon> 说明：选择的时间段不能重叠，重叠的时间段会自动取消选择
          </div>
        </el-form-item>
      </el-form>
      <el-form label-width="120px">
        <el-form-item label="导师信息">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            placeholder="请输入导师信息，每行一个导师"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="batchAddDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchAddSubmit" :loading="batchAddLoading">批量添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Search, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock, InfoFilled, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const mainTableRef = ref(null)
const topScrollbarRef = ref(null)
const scrollbarWidth = ref(0)
let scrollHandler = null

const currentUser = ref(null)
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)
const searchKeyword = ref('')
const isActiveFilter = ref(null)

const teachers = ref([])
const lastTeacherCode = ref('')
const batchAddDialogVisible = ref(false)
const batchAddText = ref('')
const batchAddLoading = ref(false)
const selectedBatchTimeSlots = ref([])

const goBack = () => {
  router.back()
}

const pagination = ref({
  currentPage: 1,
  pageSize: 15,
  total: 0
})

const selectedDays = ref([1, 2, 3, 4, 5, 6, 7])
const selectedTimeSlots = ref([])
// 添加排序相关变量
const sortField = ref('')
const sortOrder = ref('asc')

// 添加排序处理函数
const handleSortChange = ({ prop, order }) => {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  pagination.value.currentPage = 1
  fetchTeachers()
}

const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchTeachers()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchTeachers()
}

const handleSearch = () => {
  pagination.value.currentPage = 1
  fetchTeachers()
}

const handleFilterChange = () => {
  pagination.value.currentPage = 1
  fetchTeachers()
}

const form = ref({
  code: '',
  name: '',
  join_date: null,
  title: '',
  department: '',
  contact_phone: '',
  email: '',
  max_weekly_hours: 40,
  available_days: [1, 2, 3, 4, 5, 6, 7],
  available_time_slots: ['08:00-10:00', '10:00-12:00', '13:30-15:30', '15:30-17:30', '17:30-19:30', '19:30-21:30', '14:00-16:00', '16:00-18:00', '18:00-20:00', '20:00-22:00', '14:30-16:30', '16:30-18:30', '18:30-20:30', '20:30-22:30'],
  allow_holiday_scheduling: true,
  no_feedback_required: false,
  is_active: true,
  end_date: null
})

// 表单数据备份储存
const originalForm = ref({
  code: '',
  name: '',
  join_date: null,
  title: '',
  department: '',
  contact_phone: '',
  email: '',
  max_weekly_hours: 40,
  available_days: [1, 2, 3, 4, 5, 6, 7],
  available_time_slots: ['08:00-10:00', '10:00-12:00', '13:30-15:30', '15:30-17:30', '17:30-19:30', '19:30-21:30', '14:00-16:00', '16:00-18:00', '18:00-20:00', '20:00-22:00', '14:30-16:30', '16:30-18:30', '18:30-20:30', '20:30-22:30'],
  allow_holiday_scheduling: true,
  no_feedback_required: false,
  is_active: true,
  end_date: null
})

const rules = {
  code: [{ required: true, message: '请输入导师代码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入导师姓名', trigger: 'blur' }]
}

watch(selectedDays, (newVal) => {
  form.value.available_days = newVal.sort().join(',')
})

watch(selectedTimeSlots, (newVal) => {
  form.value.available_time_slots = newVal.sort().join(',')
})

const parseAvailableDays = (daysStr) => {
  const days = daysStr.split(',').map(d => parseInt(d.trim()))
  const dayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return days.map(d => dayNames[d] || '')
}

const parseAvailableTimeSlots = (timeSlotsStr) => {
  if (!timeSlotsStr) return []
  return timeSlotsStr.split(',').map(t => t.trim()).filter(t => t)
}

// 判断两个时间段是否重叠
const isTimeSlotOverlap = (slot1, slot2) => {
  const [start1, end1] = slot1.split('-')
  const [start2, end2] = slot2.split('-')
  // 重叠条件：start1 < end2 && end1 > start2
  return start1 < end2 && end1 > start2
}

// 检查某个时间段是否与已选时间段重叠
const isOverlappingSlot = (slot) => {
  for (const selectedSlot of selectedTimeSlots.value) {
    if (selectedSlot !== slot && isTimeSlotOverlap(slot, selectedSlot)) {
      return true
    }
  }
  return false
}

const handleTimeSlotChange = (value) => {
  // 检查是否有重叠的时间段
  const hasOverlap = value.some(slot => {
    return value.filter(s => s !== slot).some(otherSlot => 
      isTimeSlotOverlap(slot, otherSlot)
    )
  })
  
  if (hasOverlap) {
    ElMessage.warning('检测到重叠的时间段，请重新选择')
  }
}

// 处理批量添加时间段选择
const handleBatchTimeSlotChange = (value) => {
  // 获取当前选中的所有时间段
  const currentSelected = value
  
  // 检查每个选中的时间段是否与其他时间段重叠
  const nonOverlappingSlots = []
  const overlappingSlots = []
  
  currentSelected.forEach(selectedSlot => {
    let hasOverlap = false
    
    // 检查与已选时间段是否重叠
    for (const existingSlot of nonOverlappingSlots) {
      if (isTimeSlotOverlap(selectedSlot, existingSlot)) {
        hasOverlap = true
        overlappingSlots.push(selectedSlot)
        break
      }
    }
    
    // 如果不重叠，添加到结果中
    if (!hasOverlap) {
      nonOverlappingSlots.push(selectedSlot)
    }
  })
  
  // 如果有重叠的时间段，显示提示
  if (overlappingSlots.length > 0) {
    ElMessage.warning(`以下时间段与其他时间段重叠，已自动取消选择：${overlappingSlots.join(', ')}`)
  }
  
  // 更新选中的时间段
  selectedBatchTimeSlots.value = nonOverlappingSlots
}

const handleTeacherStatusChange = (newValue) => {
  if (newValue === false && !form.value.end_date) {
    // 如果从在职变为离职，自动设置离职日期为今天
    form.value.end_date = new Date().toISOString().split('T')[0]
  } else if (newValue === true) {
    // 如果从离职变为在职，清空离职日期
    form.value.end_date = null
  }
}

// 从URL参数应用筛选条件
const applyUrlFilters = (query) => {
  let hasChanges = false
  
  // 处理搜索关键词
  if (query.search !== undefined && query.search !== null) {
    const searchValue = decodeURIComponent(query.search)
    if (searchValue !== searchKeyword.value) {
      searchKeyword.value = searchValue
      hasChanges = true
    }
  }
  
  // 处理在职状态过滤
  if (query.is_active !== undefined && query.is_active !== null) {
    const isActiveValue = query.is_active === 'true' || query.is_active === true || query.is_active === '1'
    if (isActiveValue !== isActiveFilter.value) {
      isActiveFilter.value = isActiveValue
      hasChanges = true
    }
  }
  
  // 处理排序字段
  if (query.sort_field !== undefined && query.sort_field !== null) {
    const sortFieldValue = decodeURIComponent(query.sort_field)
    if (sortFieldValue !== sortField.value) {
      sortField.value = sortFieldValue
      hasChanges = true
    }
  }
  
  // 处理排序顺序
  if (query.sort_order !== undefined && query.sort_order !== null) {
    const sortOrderValue = query.sort_order === 'desc' ? 'desc' : 'asc'
    if (sortOrderValue !== sortOrder.value) {
      sortOrder.value = sortOrderValue
      hasChanges = true
    }
  }
  
  // 处理页码
  if (query.page !== undefined && query.page !== null) {
    const pageNum = parseInt(query.page)
    if (!isNaN(pageNum) && pageNum > 0 && pageNum !== pagination.value.currentPage) {
      pagination.value.currentPage = pageNum
      hasChanges = true
    }
  }
  
  // 处理每页数量
  if (query.page_size !== undefined && query.page_size !== null) {
    const pageSizeNum = parseInt(query.page_size)
    if (!isNaN(pageSizeNum) && [15, 25, 50, 100].includes(pageSizeNum) && pageSizeNum !== pagination.value.pageSize) {
      pagination.value.pageSize = pageSizeNum
      hasChanges = true
    }
  }
  
  return hasChanges
}

const fetchTeachers = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (isActiveFilter.value !== null) {
      params.is_active = isActiveFilter.value
    }
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    const response = await api.get('/teachers', { params })
    teachers.value = response.data.items
    pagination.value.total = response.data.total
    
    // 获取最后一个导师代码（按代码排序后的最后一个）
    if (response.data.items && response.data.items.length > 0) {
      const sortedByCode = [...response.data.items].sort((a, b) => a.code.localeCompare(b.code))
      lastTeacherCode.value = sortedByCode[sortedByCode.length - 1].code
    } else {
      lastTeacherCode.value = ''
    }
  } catch (error) {
    window.logger.error('获取导师列表失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  searchKeyword.value = ''
  isActiveFilter.value = null
  sortField.value = ''
  sortOrder.value = 'asc'
  pagination.value.currentPage = 1
  fetchTeachers()
}

const showAddDialog = () => {
  dialogTitle.value = '新增导师'
  
  // 检查是否有预填充数据
  const storageData = sessionStorage.getItem('smartCommandData')
  let prefillData = null
  if (storageData) {
    try {
      prefillData = JSON.parse(storageData)
      window.logger.log('[DEBUG] 读取到预填充数据:', prefillData)
      // 清除sessionStorage中的数据，避免重复使用
      sessionStorage.removeItem('smartCommandData')
    } catch (e) {
      window.logger.error('解析预填充数据失败:', e)
    }
  }
  
  form.value = {
    code: '',
    name: prefillData?.teacher_name || '',
    title: prefillData?.title || '',
    join_date: null,
    department: prefillData?.department || '',
    contact_phone: prefillData?.contact_phone || '',
    email: prefillData?.email || '',
    max_weekly_hours: 40,
    available_days: '6,7',
    available_time_slots: '',
    allow_holiday_scheduling: true,
    no_feedback_required: false,
    is_active: true
  }
  selectedDays.value = [6, 7]
  selectedTimeSlots.value = []
  dialogVisible.value = true
}

const showBatchAddDialog = () => {
  batchAddText.value = ''
  selectedBatchTimeSlots.value = []
  batchAddDialogVisible.value = true
}
const handleBatchAddSubmit = async () => {
  if (!batchAddText.value.trim()) {
    ElMessage.warning('请输入导师信息')
    return
  }
  
  const lines = batchAddText.value.trim().split('\n')
  const teachersToAdd = []
  const errors = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    const parts = line.split(',').map(p => p.trim())
    if (parts.length < 2) {
      errors.push(`第${i + 1}行：格式错误，至少需要代码和姓名`)
      continue
    }
    
    const teacher = {
      code: parts[0],
      name: parts[1],
      join_date: parts[2] || null,
      title: parts[3] || '',
      department: parts[4] || '',
      contact_phone: parts[5] || '',
      email: parts[6] || '',
      max_weekly_hours: parts[7] ? parseInt(parts[7]) : 40,
      available_days: parts.slice(8).filter(p => p).join(',') || '6,7',
      available_time_slots: selectedBatchTimeSlots.value.length > 0 ? selectedBatchTimeSlots.value.join(',') : '08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30',
      allow_holiday_scheduling: true,
      no_feedback_required: false,
      is_active: true
    }
    
    teachersToAdd.push(teacher)
  }
  
  if (errors.length > 0) {
    ElMessage.error(`发现${errors.length}个错误：\n${errors.join('\n')}`)
    if (teachersToAdd.length === 0) {
      return
    }
  }
  
  if (teachersToAdd.length === 0) {
    ElMessage.warning('没有有效的导师信息')
    return
  }
  
  batchAddLoading.value = true
  try {
    let successCount = 0
    let failCount = 0
    const failMessages = []
    
    for (const teacher of teachersToAdd) {
      try {
        await api.post('/teachers', teacher)
        successCount++
      } catch (error) {
        failCount++
        failMessages.push(`${teacher.code}(${teacher.name}): ${error.response?.data?.detail || error.message}`)
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(`批量添加完成：成功${successCount}个，失败${failCount}个\n失败详情：\n${failMessages.join('\n')}`)
    } else {
      ElMessage.success(`批量添加成功，共添加${successCount}个导师`)
    }
    
    batchAddDialogVisible.value = false
    await fetchTeachers()
  } catch (error) {
    window.logger.error('批量添加导师失败:', error)
    ElMessage.error('批量添加导师失败')
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = '编辑导师'

  // 转换日期格式
  let formattedJoinDate = null
  if (row.join_date) {
    const date = new Date(row.join_date)
    formattedJoinDate = date.toISOString().split('T')[0]
  }
  let formattedEndDate = null
  if (row.end_date) {
    // end_date是datetime类型，需要转换为ISO格式的datetime字符串
    const date = new Date(row.end_date)
    formattedEndDate = date.toISOString()
  }

  const formData = {
    id: row.id,
    code: row.code,
    name: row.name,
    join_date: formattedJoinDate,
    title: row.title,
    department: row.department,
    contact_phone: row.contact_phone || '',
    email: row.email || '',
    max_weekly_hours: row.max_weekly_hours,
    available_days: row.available_days ? row.available_days : '1,2,3,4,5,6,7',
    available_time_slots: row.available_time_slots ? row.available_time_slots : '',
    allow_holiday_scheduling: row.allow_holiday_scheduling !== undefined ? row.allow_holiday_scheduling : true,
    no_feedback_required: row.no_feedback_required !== undefined ? row.no_feedback_required : false,
    is_active: row.is_active,
    end_date: formattedEndDate
  }
  originalForm.value = { ...formData }
  form.value = formData

  selectedDays.value = row.available_days ? row.available_days.split(',').map(Number) : [1, 2, 3, 4, 5, 6, 7]
  selectedTimeSlots.value = row.available_time_slots ? row.available_time_slots.split(',').map(t => t.trim()).filter(t => t) : []
  
  // 如果有预填充的更新数据，应用到表单
  const storageData = sessionStorage.getItem('smartCommandData')
  if (storageData) {
    try {
      const prefillData = JSON.parse(storageData)
      if (prefillData.updates) {
        Object.keys(prefillData.updates).forEach(key => {
          if (form.value.hasOwnProperty(key)) {
            form.value[key] = prefillData.updates[key]
          }
        })
        window.logger.log('[DEBUG] 应用预填充更新数据:', prefillData.updates)
      }
      sessionStorage.removeItem('smartCommandData')
    } catch (e) {
      window.logger.error('解析预填充数据失败:', e)
    }
  }
  
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 检查是否有重叠的时间段
        const hasOverlap = selectedTimeSlots.value.some(slot => {
          return selectedTimeSlots.value.filter(s => s !== slot).some(otherSlot => 
            isTimeSlotOverlap(slot, otherSlot)
          )
        })
        
        if (hasOverlap) {
          ElMessage.error('存在重叠的时间段，请重新选择')
          return
        }
        
        const formData = {
          code: form.value.code,
          name: form.value.name,
          join_date: form.value.join_date,
          title: form.value.title,
          department: form.value.department,
          contact_phone: form.value.contact_phone,
          email: form.value.email,
          max_weekly_hours: form.value.max_weekly_hours,
          available_days: form.value.available_days,
          available_time_slots: form.value.available_time_slots,
          allow_holiday_scheduling: form.value.allow_holiday_scheduling,
          no_feedback_required: form.value.no_feedback_required,
          is_active: form.value.is_active,
          end_date: form.value.end_date
        }
        
        if (form.value.id) {
          const isChanged = 
            formData.code !== originalForm.value.code ||
            formData.name !== originalForm.value.name ||
            formData.join_date !== originalForm.value.join_date ||
            formData.title !== originalForm.value.title ||
            formData.department !== originalForm.value.department ||
            formData.contact_phone !== originalForm.value.contact_phone ||
            formData.email !== originalForm.value.email ||
            formData.max_weekly_hours !== originalForm.value.max_weekly_hours ||
            formData.available_days !== originalForm.value.available_days ||
            formData.available_time_slots !== originalForm.value.available_time_slots ||
            formData.allow_holiday_scheduling !== originalForm.value.allow_holiday_scheduling ||
            formData.no_feedback_required !== originalForm.value.no_feedback_required ||
            formData.is_active !== originalForm.value.is_active ||
            formData.end_date !== originalForm.value.end_date
          
          if (!isChanged) {
            ElMessage.warning('内容未发生改变，无需保存')
            return
          }
          
          await api.put(`/teachers/${form.value.id}`, formData)
          ElMessage.success('更新成功')
        } else {
          await api.post('/teachers', formData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchTeachers()
      } catch (error) {
        window.logger.error('操作失败:', error)
        if (error.response && error.response.data && error.response.data.detail) {
          // 详细显示验证错误
          const detail = error.response.data.detail
          if (Array.isArray(detail)) {
            const errors = detail.map(d => `${d.loc?.join('.')}: ${d.msg}`).join('; ')
            ElMessage.error(`操作失败: ${errors}`)
          } else {
            ElMessage.error(`操作失败: ${detail}`)
          }
        } else {
          ElMessage.error('操作失败')
        }
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该导师吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/teachers/${row.id}`)
      ElMessage.success('删除成功')
      fetchTeachers()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const formatAvailableDays = (days) => {
  if (!days) return '-'
  const dayMap = {
    1: '周一',
    2: '周二',
    3: '周三',
    4: '周四',
    5: '周五',
    6: '周六',
    7: '周日'
  }
  const dayArray = days.split(',').map(Number)
  return dayArray.map(day => dayMap[day]).join('、')
}

const formatAvailableTimeSlots = (slots) => {
  if (!slots) return '-'
  const slotArray = slots.split(',')
  return slotArray.join('、')
}

const goToPage = (path) => {
  router.push(path)
}

// ========== 核心功能：初始化顶部滚动条 ==========
const initTopScrollbar = () => {
  nextTick(() => {
    if (!mainTableRef.value || !topScrollbarRef.value) {
      window.logger.warn('表格或滚动条ref未就绪')
      return
    }
    
    const tableEl = mainTableRef.value.$el
    
    // 找到真正的滚动容器
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    
    if (!scrollWrap) {
      window.logger.warn('找不到滚动容器')
      return
    }
    
    // 计算内容宽度
    const contentWidth = scrollWrap.scrollWidth
    const containerWidth = scrollWrap.clientWidth
    
    window.logger.log('表格内容宽度:', contentWidth, '容器宽度:', containerWidth)
    
    if (contentWidth <= containerWidth) {
      // 不需要滚动条
      topScrollbarRef.value.style.display = 'none'
      window.logger.log('内容未超出容器，隐藏滚动条')
      return
    }
    
    // 显示滚动条并设置内部宽度
    topScrollbarRef.value.style.display = 'block'
    scrollbarWidth.value = contentWidth
    window.logger.log('显示滚动条，宽度设置为:', contentWidth)
  })
}

// ========== 核心功能：设置滚动同步 ==========
const setupScrollSync = () => {
  window.logger.log('🔧 setupScrollSync 被调用')
  
  nextTick(() => {
    if (!mainTableRef.value || !topScrollbarRef.value) {
      window.logger.warn('❌ mainTableRef 或 topScrollbarRef 未就绪')
      return
    }
    
    const tableEl = mainTableRef.value.$el
    const headerWrapper = tableEl?.querySelector('.el-table__header-wrapper')
    
    // 找到真正的滚动容器
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    const fakeScrollbar = topScrollbarRef.value
    
    window.logger.log('🔍 查找元素:')
    window.logger.log('  headerWrapper:', headerWrapper)
    window.logger.log('  scrollWrap (真实滚动容器):', scrollWrap)
    window.logger.log('  fakeScrollbar:', fakeScrollbar)
    
    if (!headerWrapper || !scrollWrap || !fakeScrollbar) {
      window.logger.warn('❌ 找不到需要同步的元素')
      return
    }
    
    // 清除旧的事件监听器
    if (scrollHandler) {
      window.logger.log('🗑️ 清除旧的事件监听器')
      scrollWrap.removeEventListener('scroll', scrollHandler.wrapScroll)
      fakeScrollbar.removeEventListener('scroll', scrollHandler.fakeScroll)
    }
    
    // 头部滚动 → 同步到顶部滚动条（header 本身不滚动，只是显示）
    const headerScrollHandler = () => {
      // header 不实际滚动，这个handler可能不会被触发
    }
    
    // 真实滚动容器滚动 → 同步到顶部滚动条
    const wrapScrollHandler = () => {
      const targetScroll = scrollWrap.scrollLeft
      
      if (Math.abs(fakeScrollbar.scrollLeft - targetScroll) > 1) {
        fakeScrollbar.scrollLeft = targetScroll
      }
      
      // 同步 header 的 scrollLeft（用于视觉对齐）
      if (Math.abs(headerWrapper.scrollLeft - targetScroll) > 1) {
        headerWrapper.scrollLeft = targetScroll
      }
    }
    
    // 顶部滚动条滚动 → 同步到真实滚动容器
    const fakeScrollHandler = () => {
      const targetScroll = fakeScrollbar.scrollLeft
      
      window.logger.log('📊 顶部滚动条滚动，目标值:', targetScroll)
      
      // 同步到真实的滚动容器
      if (Math.abs(scrollWrap.scrollLeft - targetScroll) > 1) {
        scrollWrap.scrollLeft = targetScroll
        window.logger.log('✅ 同步 scrollWrap 到', targetScroll)
      }
      
      // 同步 header
      if (Math.abs(headerWrapper.scrollLeft - targetScroll) > 1) {
        headerWrapper.scrollLeft = targetScroll
        window.logger.log('✅ 同步 header 到', targetScroll)
      }
    }
    
    // 绑定事件监听器
    scrollWrap.addEventListener('scroll', wrapScrollHandler)
    fakeScrollbar.addEventListener('scroll', fakeScrollHandler)
    
    // 保存引用以便清理
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
  
  // 检查是否有来自智能指令的搜索参数
  const urlParams = new URLSearchParams(window.location.search)
  const searchQuery = urlParams.get('search')
  const relatedTo = urlParams.get('related_to')
  const viewDetail = urlParams.get('view_detail')
  
  // 应用URL中的筛选条件
  const hasFilters = applyUrlFilters(route.query)

  await fetchTeachers()
  
  // 如果有搜索参数，自动填充并执行搜索
  if (searchQuery) {
    filters.value.name = searchQuery
    setTimeout(() => {
      fetchTeachers()
      
      // 如果需要查看关联信息
      if (relatedTo && sessionStorage.getItem('smartCommandData')) {
        try {
          const smartData = JSON.parse(sessionStorage.getItem('smartCommandData'))
          if (smartData.target_path && smartData.target_label) {
            ElMessage.info(`已找到导师"${searchQuery}"，正在跳转到${smartData.target_label}...`)
            setTimeout(() => {
              window.location.href = `${smartData.target_path}?filter_by=teacher&filter_value=${encodeURIComponent(searchQuery)}`
            }, 1500)
          }
        } catch (e) {
          window.logger.error('解析智能指令数据失败', e)
        }
      }
      
      // 如果需要查看详情
      if (viewDetail === 'true') {
        setTimeout(() => {
          const firstTeacher = teachers.value.find(t => t.name === searchQuery)
          if (firstTeacher) {
            showEditDialog(firstTeacher)
          }
        }, 1000)
      }
    }, 500)
  }
  
  // 如果应用了URL筛选条件，重新获取数据
  if (hasFilters && !searchQuery) {
    await fetchTeachers()
  }

  // 检查是否需要自动打开新增对话框
  if (route.query.action === 'add') {
    showAddDialog()
  }
  
  // 检查是否需要自动打开编辑对话框
  if (route.query.action === 'edit' && route.query.id) {
    const teacherId = parseInt(route.query.id)
    const teacher = teachers.value.find(t => t.id === teacherId)
    if (teacher) {
      showEditDialog(teacher)
    } else {
      try {
        const response = await api.get(`/teachers/${teacherId}`)
        if (response.data) {
          showEditDialog(response.data)
        }
      } catch (error) {
        window.logger.error('获取导师信息失败:', error)
        ElMessage.error('无法加载导师信息')
      }
    }
  }
  
  setTimeout(() => {
    initTopScrollbar()
    setupScrollSync()
  }, 200)
})

// 监听路由参数变化，支持从悬浮球等外部触发的操作
watch(() => route.query, (newQuery, oldQuery) => {
  // 处理新增操作
  if (newQuery.action === 'add') {
    showAddDialog()
  } 
  // 处理编辑操作
  else if (newQuery.action === 'edit' && newQuery.id) {
    const teacherId = parseInt(newQuery.id)
    const teacher = teachers.value.find(t => t.id === teacherId)
    if (teacher) {
      showEditDialog(teacher)
    } else {
      api.get(`/teachers/${teacherId}`).then(response => {
        if (response.data) {
          showEditDialog(response.data)
        }
      }).catch(error => {
        window.logger.error('获取导师信息失败:', error)
        ElMessage.error('无法加载导师信息')
      })
    }
  }
  
  // 处理筛选条件变化
  const hasFilterChanges = applyUrlFilters(newQuery)
  if (hasFilterChanges) {
    pagination.value.currentPage = 1
    fetchTeachers()
  }
}, { deep: true })

onUnmounted(() => {
  // 清理事件监听器
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

watch(teachers, () => {
  setTimeout(() => {
    initTopScrollbar()
    setupScrollSync()
  }, 200)
})

</script>

<style scoped>
.teachers-page {
  padding: 6px;
}

/* 顶部滚动条样式 */
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

/* 自定义滚动条外观 */
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

.overlapping-slot {
  color: #f56c6c !important;
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
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
  flex-wrap: wrap;
  gap: 10px;
}

.card-header .button-group {
  display: flex;
  gap: 10px;
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
  
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .card-header .button-group {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .search-bar {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
  }
  
  .search-bar :deep(.el-input) {
    width: 100% !important;
  }
  
  .search-bar :deep(.el-select) {
    width: 100% !important;
  }
  
  .search-bar :deep(.el-button) {
    width: 100%;
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
    width: 100px !important;
  }
  
  .el-table :deep(.el-table__fixed-right-patch) {
    width: 100px !important;
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