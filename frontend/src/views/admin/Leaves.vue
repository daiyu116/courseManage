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
          <el-button type="success" @click="goToPage('/admin/teachers')" style="width: 100%;height: 100%;">
            <el-icon><User /></el-icon>
            导师管理
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
          <span>请假管理</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回上一页
            </el-button>
            <el-button type="warning" @click="goToPage('/admin/holidays')">
              <el-icon><Calendar /></el-icon>
              假期管理
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              新增请假
            </el-button>
          </div>
        </div>
      </template>

      <div class="search-bar">
        <el-select v-model="leaveTypeFilter" placeholder="请假类型" clearable style="width: 150px" @change="handleFilterChange">
          <el-option label="导师请假" value="teacher" />
          <el-option label="学员请假" value="student" />
        </el-select>
        <el-select v-model="teacherFilter" placeholder="选择导师" clearable style="width: 200px" @change="handleFilterChange">
          <el-option
            v-for="teacher in teachers"
            :key="teacher.id"
            :label="teacher.name"
            :value="teacher.id"
          />
        </el-select>
        <el-select v-model="studentFilter" placeholder="选择学员" clearable style="width: 200px" @change="handleFilterChange">
          <el-option
            v-for="student in students"
            :key="student.id"
            :label="student.name"
            :value="student.id"
          />
        </el-select>
        <el-col :span="2">
          <el-form-item label-width="0">
            <el-button @click="resetFilters" style="width: 50px">重置</el-button>
          </el-form-item>
        </el-col>
      </div>

      <el-table :data="leaves" stripe v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="id" label="ID" width="50" />
        <el-table-column label="请假类型" width="150">
          <template #default="{ row }">
            <el-tag :type="row.leave_type === 'teacher' ? 'primary' : 'success'">
              {{ row.leave_type === 'teacher' ? '导师请假' : '学员请假' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="导师/学员" width="150">
          <template #default="{ row }">
            {{ row.leave_type === 'teacher' ? getTeacherName(row.teacher_id) : getStudentName(row.student_id) }}
          </template>
        </el-table-column>
        <el-table-column label="开始日期" width="150">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }}
          </template>
        </el-table-column>
        <el-table-column label="结束日期" width="150">
          <template #default="{ row }">
            {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="请假原因" min-width="200" />
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
        <el-form-item label="请假类型" prop="leave_type">
          <el-select v-model="form.leave_type" placeholder="请选择请假类型" @change="handleLeaveTypeChange">
            <el-option label="导师请假" value="teacher" />
            <el-option label="学员请假" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="导师" prop="teacher_id" v-if="form.leave_type === 'teacher'">
          <el-select v-model="form.teacher_id" filterable placeholder="请选择导师">
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>导师：</strong>{{ teacher.name }}</div>
                    <div v-if="teacher.code"><strong>代码：</strong>{{ teacher.code }}</div>
                    <div v-if="teacher.department"><strong>部门：</strong>{{ teacher.department }}</div>
                    <div v-if="teacher.contact_phone"><strong>联系电话：</strong>{{ teacher.contact_phone }}</div>
                    <div v-if="teacher.email"><strong>邮箱：</strong>{{ teacher.email }}</div>
                  </div>
                </template>
                <span>{{ teacher.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="学员" prop="student_id" v-if="form.leave_type === 'student'">
          <el-select v-model="form.student_id" filterable placeholder="请选择学员">
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="student.name"
              :value="student.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>学员：</strong>{{ student.name }}</div>
                    <div v-if="student.code"><strong>代码：</strong>{{ student.code }}</div>
                    <div v-if="student.school"><strong>学校：</strong>{{ student.school }}</div>
                    <div v-if="student.grade"><strong>年级：</strong>{{ student.grade }}</div>
                    <div v-if="student.contact_person"><strong>联系人：</strong>{{ student.contact_person }}</div>
                    <div v-if="student.contact_phone"><strong>联系电话：</strong>{{ student.contact_phone }}</div>
                    <div><strong>是否在读：</strong>{{ student.is_active ? '是' : '否' }}</div>
                  </div>
                </template>
                <span>{{ student.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker
            v-model="form.start_date"
            type="datetime"
            placeholder="选择开始日期"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker
            v-model="form.end_date"
            type="datetime"
            placeholder="选择结束日期"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="请假原因" prop="reason">
          <el-input v-model="form.reason" type="textarea" :rows="3" placeholder="请输入请假原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
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
  leave_type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  teacher_id: [{ required: true, message: '请选择导师', trigger: 'change' }],
  student_id: [{ required: true, message: '请选择学员', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }]
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
  dialogTitle.value = '新增请假'
  
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
  dialogTitle.value = '编辑请假'
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
            ElMessage.warning('内容未发生改变，无需保存')
            return
          }
          
          await api.put(`/leaves/${form.value.id}`, form.value)
          ElMessage.success('更新成功')
        } else {
          await api.post('/leaves', form.value)
          ElMessage.success('创建成功')
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
  ElMessageBox.confirm('确定要删除该请假记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/leaves/${row.id}`)
      ElMessage.success('删除成功')
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
          ElMessage.info(`已筛选导师"${filterValue}"的请假记录`)
        }
      } else if (filterBy === 'student') {
        const student = students.value.find(s => s.name === filterValue)
        if (student) {
          filters.value.student_id = student.id
          fetchLeaves()
          ElMessage.info(`已筛学员"${filterValue}"的请假记录`)
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