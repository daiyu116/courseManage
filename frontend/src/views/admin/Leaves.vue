// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="leaves-page">
    <!-- 导航栏 -->
    <el-card class="nav-card" style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/dashboard')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('nav.dashboard') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/courses')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('nav.courses') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="success" @click="goToPage('/admin/teachers')" style="width: 100%;height: 100%;">
            <el-icon><User /></el-icon>
            {{ t('nav.teachers') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="success" @click="goToPage('/admin/classes')" style="width: 100%;height: 100%;">
            <el-icon><User /></el-icon>
            {{ t('nav.classes') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="warning" @click="goToPage('/admin/students')" style="width: 100%;height: 100%;">
            <el-icon><UserFilled /></el-icon>
            {{ t('nav.students') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="info" @click="goToPage('/admin/rooms')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
            {{ t('nav.rooms') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/schedules')" style="width: 100%;height: 100%;">
            <el-icon><Clock /></el-icon>
            {{ t('nav.schedules') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/conditions')" style="width: 100%;height: 100%;">
            <el-icon><Setting /></el-icon>
            {{ t('nav.conditions') }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('leaves.title') }}</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('common.back') }}
            </el-button>
            <el-button type="warning" @click="goToPage('/admin/holidays')">
              <el-icon><Calendar /></el-icon>
              {{ t('leaves.holidayManagement') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('leaves.addLeave') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="search-bar">
        <el-select v-model="leaveTypeFilter" :placeholder="t('leaves.leaveType')" clearable style="width: 150px" @change="handleFilterChange">
          <el-option :label="t('leaves.teacherLeave')" value="teacher" />
          <el-option :label="t('leaves.studentLeave')" value="student" />
        </el-select>
        <el-select v-model="teacherFilter" :placeholder="t('leaves.selectTeacher')" clearable style="width: 200px" @change="handleFilterChange">
          <el-option
            v-for="teacher in teachers"
            :key="teacher.id"
            :label="teacher.name"
            :value="teacher.id"
          />
        </el-select>
        <el-select v-model="studentFilter" :placeholder="t('leaves.selectStudent')" clearable style="width: 200px" @change="handleFilterChange">
          <el-option
            v-for="student in students"
            :key="student.id"
            :label="student.name"
            :value="student.id"
          />
        </el-select>
        <el-col :span="2">
          <el-form-item label-width="0">
            <el-button @click="resetFilters" style="width: 50px">{{ t('common.reset') }}</el-button>
          </el-form-item>
        </el-col>
      </div>

      <el-table :data="leaves" stripe v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="id" label="ID" width="50" />
        <el-table-column :label="t('leaves.leaveType')" width="150">
          <template #default="{ row }">
            <el-tag :type="row.leave_type === 'teacher' ? 'primary' : 'success'">
              {{ row.leave_type === 'teacher' ? t('leaves.teacherLeave') : t('leaves.studentLeave') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('leaves.teacherStudent')" width="150">
          <template #default="{ row }">
            {{ row.leave_type === 'teacher' ? getTeacherName(row.teacher_id) : getStudentName(row.student_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('leaves.startDate')" width="150">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('leaves.endDate')" width="150">
          <template #default="{ row }">
            {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" :label="t('leaves.reason')" min-width="200" />
        <el-table-column :label="t('common.operation')" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">{{ t('common.edit') }}</el-button>
            <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item :label="t('leaves.leaveType')" prop="leave_type">
          <el-select v-model="form.leave_type" :placeholder="t('leaves.leaveTypePlaceholder')" @change="handleLeaveTypeChange">
            <el-option :label="t('leaves.teacherLeave')" value="teacher" />
            <el-option :label="t('leaves.studentLeave')" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('leaves.teacher')" prop="teacher_id" v-if="form.leave_type === 'teacher'">
          <el-select v-model="form.teacher_id" filterable :placeholder="t('leaves.selectTeacherPlaceholder')">
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('leaves.teacher') }}：</strong>{{ teacher.name }}</div>
                    <div v-if="teacher.code"><strong>{{ t('common.code') }}：</strong>{{ teacher.code }}</div>
                    <div v-if="teacher.department"><strong>{{ t('leaves.department') }}：</strong>{{ teacher.department }}</div>
                    <div v-if="teacher.contact_phone"><strong>{{ t('leaves.contactPhone') }}：</strong>{{ teacher.contact_phone }}</div>
                    <div v-if="teacher.email"><strong>{{ t('leaves.email') }}：</strong>{{ teacher.email }}</div>
                  </div>
                </template>
                <span>{{ teacher.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('leaves.student')" prop="student_id" v-if="form.leave_type === 'student'">
          <el-select v-model="form.student_id" filterable :placeholder="t('leaves.selectStudentPlaceholder')">
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="student.name"
              :value="student.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('leaves.student') }}：</strong>{{ student.name }}</div>
                    <div v-if="student.code"><strong>{{ t('common.code') }}：</strong>{{ student.code }}</div>
                    <div v-if="student.school"><strong>{{ t('leaves.school') }}：</strong>{{ student.school }}</div>
                    <div v-if="student.grade"><strong>{{ t('leaves.grade') }}：</strong>{{ student.grade }}</div>
                    <div v-if="student.contact_person"><strong>{{ t('leaves.contactPerson') }}：</strong>{{ student.contact_person }}</div>
                    <div v-if="student.contact_phone"><strong>{{ t('leaves.contactPhone') }}：</strong>{{ student.contact_phone }}</div>
                    <div><strong>{{ t('leaves.isActive') }}：</strong>{{ student.is_active ? t('common.yes') : t('common.no') }}</div>
                  </div>
                </template>
                <span>{{ student.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('leaves.startDate')" prop="start_date">
          <el-date-picker
            v-model="form.start_date"
            type="datetime"
            :placeholder="t('leaves.startDatePlaceholder')"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('leaves.endDate')" prop="end_date">
          <el-date-picker
            v-model="form.end_date"
            type="datetime"
            :placeholder="t('leaves.endDatePlaceholder')"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('leaves.reason')" prop="reason">
          <el-input v-model="form.reason" type="textarea" :rows="3" :placeholder="t('leaves.reasonPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const currentUser = ref(null)
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)
const leaveTypeFilter = ref('')
const teacherFilter = ref(null)
const studentFilter = ref(null)
const leaves = ref([])
const teachers = ref([])
const students = ref([])

const goBack = () => {
  router.back()
}

const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

// 添加分页处理函数
const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchLeaves()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchLeaves()
}

const handleFilterChange = () => {
  pagination.value.currentPage = 1
  fetchLeaves()
}

const form = ref({
  leave_type: 'teacher',
  teacher_id: null,
  student_id: null,
  start_date: '',
  end_date: '',
  reason: ''
})

const originalForm = ref({
  leave_type: 'teacher',
  teacher_id: null,
  student_id: null,
  start_date: '',
  end_date: '',
  reason: ''
})

const rules = {
  leave_type: [{ required: true, message: () => t('leaves.leaveTypeRequired'), trigger: 'change' }],
  teacher_id: [{ required: true, message: () => t('leaves.teacherRequired'), trigger: 'change' }],
  student_id: [{ required: true, message: () => t('leaves.studentRequired'), trigger: 'change' }],
  start_date: [{ required: true, message: () => t('leaves.startDateRequired'), trigger: 'change' }],
  end_date: [{ required: true, message: () => t('leaves.endDateRequired'), trigger: 'change' }]
}

const fetchTeachers = async () => {
  try {
    const response = await api.get('/teachers', { params: { is_active: true, skip: 0, limit: 100000 } })
    teachers.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取导师列表失败:', error)
  }
}

const fetchStudents = async () => {
  try {
    const response = await api.get('/students', { params: { is_active: true, skip: 0, limit: 100000 } })
    students.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
  }
}

const fetchLeaves = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    if (leaveTypeFilter.value) {
      params.leave_type = leaveTypeFilter.value
    }
    if (teacherFilter.value) {
      params.teacher_id = teacherFilter.value
    }
    if (studentFilter.value) {
      params.student_id = studentFilter.value
    }
    const response = await api.get('/leaves', { params })
    leaves.value = response.data.items
    pagination.value.total = response.data.total
  } catch (error) {
    window.logger.error('获取请假列表失败:', error)
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = t('leaves.addLeaveTitle')
  
  // 检查是否有预填充数据
  const storageData = sessionStorage.getItem('smartCommandData')
  let prefillData = null
  if (storageData) {
    try {
      prefillData = JSON.parse(storageData)
      window.logger.log('[DEBUG] 读取到预填充数据:', prefillData)
      sessionStorage.removeItem('smartCommandData')
    } catch (e) {
      window.logger.error('解析预填充数据失败:', e)
    }
  }
  
  form.value = {
    leave_type: prefillData?.person_type === 'teacher' ? 'teacher' : 'student',
    teacher_id: prefillData?.teacher_id || null,
    student_id: prefillData?.student_id || null,
    start_date: prefillData?.start_date || '',
    end_date: prefillData?.end_date || prefillData?.start_date || '',
    reason: prefillData?.reason || ''
  }
  dialogVisible.value = true
}

const resetFilters = () => {
  leaveTypeFilter.value = ''
  teacherFilter.value = null
  studentFilter.value = null
  pagination.value.currentPage = 1
  fetchLeaves()
}

const showEditDialog = (row) => {
  dialogTitle.value = t('leaves.editLeaveTitle')
  const formData = {
    id: row.id,
    leave_type: row.leave_type,
    teacher_id: row.teacher_id,
    student_id: row.student_id,
    start_date: row.start_date,
    end_date: row.end_date,
    reason: row.reason
  }

  originalForm.value = { ...formData }
  form.value = formData
  dialogVisible.value = true
}

const handleLeaveTypeChange = () => {
  form.value.teacher_id = null
  form.value.student_id = null
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (form.value.id) {
          const isChanged = 
            form.value.leave_type !== originalForm.value.leave_type ||
            form.value.teacher_id !== originalForm.value.teacher_id ||
            form.value.student_id !== originalForm.value.student_id ||
            form.value.start_date !== originalForm.value.start_date ||
            form.value.end_date !== originalForm.value.end_date ||
            form.value.reason !== originalForm.value.reason
          
          if (!isChanged) {
            ElMessage.warning(t('common.noChange'))
            return
          }
          
          await api.put(`/leaves/${form.value.id}`, form.value)
          ElMessage.success(t('common.updateSuccess'))
        } else {
          await api.post('/leaves', form.value)
          ElMessage.success(t('common.createSuccess'))
        }
        dialogVisible.value = false
        fetchLeaves()
      } catch (error) {
        window.logger.error('操作失败:', error)
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('leaves.confirmDeleteLeave'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/leaves/${row.id}`)
      ElMessage.success(t('common.deleteSuccess'))
      fetchLeaves()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const getTeacherName = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.name : '-'
}

const getStudentName = (studentId) => {
  const student = students.value.find(s => s.id === studentId)
  return student ? student.name : '-'
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const goToPage = (path) => {
  router.push(path)
}

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  
  // 检查是否有来自智能指令的搜索参数
  const urlParams = new URLSearchParams(window.location.search)
  const searchQuery = urlParams.get('search')
  const filterBy = urlParams.get('filter_by')
  const filterValue = urlParams.get('filter_value')
  
  fetchTeachers()
  fetchStudents()
  fetchLeaves()
  
  // 如果有搜索参数，自动填充并执行搜索
  if (searchQuery) {
    filters.value.name = searchQuery
    setTimeout(() => {
      fetchLeaves()
    }, 500)
  }
  
  // 如果有过滤参数
  if (filterBy && filterValue) {
    setTimeout(() => {
      if (filterBy === 'teacher') {
        const teacher = teachers.value.find(t => t.name === filterValue)
        if (teacher) {
          filters.value.teacher_id = teacher.id
          fetchLeaves()
          ElMessage.info(t('leaves.filteredTeacherLeaves', { name: filterValue }))
        }
      } else if (filterBy === 'student') {
        const student = students.value.find(s => s.name === filterValue)
        if (student) {
          filters.value.student_id = student.id
          fetchLeaves()
          ElMessage.info(t('leaves.filteredStudentLeaves', { name: filterValue }))
        }
      }
    }, 500)
  }
  
  // 检查是否需要自动打开新增对话框
  if (route.query.action === 'add') {
    showAddDialog()
  }
})

// 监听路由参数变化，支持从悬浮球等外部触发的操作
watch(() => route.query, (newQuery) => {
  if (newQuery.action === 'add') {
    showAddDialog()
  }
}, { deep: true })
</script>

<style scoped>
.leaves-page {
  padding: 6px;
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

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-bar {
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
  }
  
  .card-header .header-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .search-bar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  
  .search-bar :deep(.el-select) {
    width: 100% !important;
  }
  
  .search-bar :deep(.el-date-editor) {
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
    line-height: 28px;
    font-size: 12px;
  }
}

</style>