// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="courses-page">
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
          <el-button type="danger" @click="goToPage('/admin/leaves')" style="width: 100%;height: 100%;">
            <el-icon><Calendar /></el-icon>
            {{ t('nav.leaves') }}
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
          <span>{{ t('courses.title') }}</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('common.back') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('courses.addCourse') }}
            </el-button>
            <el-button type="success" @click="showBatchAddDialog">
              <el-icon><Upload /></el-icon>
              {{ t('common.batchAdd') }}
            </el-button>
          </div>
        </div>
      </template>
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          :placeholder="t('courses.searchPlaceholder')"
          style="width: 300px"
          clearable
          @clear="fetchCourses"
          @keyup.enter="fetchCourses"
        >
          <template #append>
            <el-button @click="fetchCourses">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
        <el-button @click="resetFilters" style="width: 50px">{{ t('common.reset') }}</el-button>
      </div>
      <el-table :data="courses" stripe v-loading="loading" style="margin-top: 20px" @sort-change="handleSortChange">
        <el-table-column prop="id" label="ID" width="70" sortable />
        <el-table-column prop="code" :label="t('courses.courseCode')" width="120" sortable />
        <el-table-column prop="name" :label="t('courses.courseName')" width="200" sortable />
        <el-table-column prop="priority" :label="t('courses.priority')" width="100" sortable />
        <el-table-column :label="t('courses.teachingTeachers')" min-width="200">
          <template #default="{ row }">
            <el-tooltip v-for="teacherId in row.teacher_ids" :key="teacherId" placement="top" effect="light">
              <template #content>
                <div style="min-width: 200px;">
                  <div><strong>{{ t('courses.teacher') }}：</strong>{{ getTeacherName(teacherId) }}</div>
                  <div v-if="getTeacherContactPhone(teacherId)"><strong>{{ t('courses.contactPhone') }}：</strong>{{ getTeacherContactPhone(teacherId) }}</div>
                  <div v-if="getTeacherEmail(teacherId)"><strong>{{ t('courses.email') }}：</strong>{{ getTeacherEmail(teacherId) }}</div>
                </div>
              </template>
              <el-tag style="margin-right: 5px; margin-bottom: 5px; cursor: help;">
                {{ getTeacherName(teacherId) }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
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
        :page-sizes="[15, 25, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item :label="t('courses.courseCode')" prop="code">
          <el-input v-model="form.code" :placeholder="lastCourseCode ? t('courses.courseCodePlaceholderWithLast', { code: lastCourseCode }) : t('courses.courseCodePlaceholder')" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item :label="t('courses.courseName')" prop="name">
          <el-input v-model="form.name" :placeholder="t('courses.courseNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('courses.priority')" prop="priority">
          <el-input-number v-model="form.priority" :min="0" :max="100" />
        </el-form-item>
        <el-form-item :label="t('courses.teachingTeachers')" prop="teacher_ids">
          <el-select v-model="form.teacher_ids" multiple filterable :placeholder="t('courses.selectTeachers')" style="width: 100%">
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('courses.teacher') }}：</strong>{{ teacher.name }}</div>
                    <div v-if="teacher.code"><strong>{{ t('courses.code') }}：</strong>{{ teacher.code }}</div>
                    <div v-if="teacher.department"><strong>{{ t('courses.department') }}：</strong>{{ teacher.department }}</div>
                    <div v-if="teacher.contact_phone"><strong>{{ t('courses.contactPhone') }}：</strong>{{ teacher.contact_phone }}</div>
                    <div v-if="teacher.email"><strong>{{ t('courses.email') }}：</strong>{{ teacher.email }}</div>
                  </div>
                </template>
                <span>{{ teacher.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 批量添加科目对话框 -->
    <el-dialog v-model="batchAddDialogVisible" :title="t('courses.batchAddTitle')" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          :title="t('courses.batchAddInfo')"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>{{ t('courses.batchAddFormat') }}</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              {{ t('courses.batchAddFormatLine') }}
            </div>
            <div style="margin-top: 10px;">{{ t('courses.batchAddExample') }}</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              MATH001,{{ t('courses.batchAddExampleMath') }},10<br/>
              CHIN001,{{ t('courses.batchAddExampleChinese') }},20<br/>
              ENG001,{{ t('courses.batchAddExampleEnglish') }},15
            </div>
            <div style="margin-top: 10px;">{{ t('courses.batchAddNote') }}</div>
            <ul style="margin-top: 5px;">
              <li>{{ t('courses.batchAddNoteCode') }}<span v-if="lastCourseCode">{{ lastCourseCode }}</span><span v-else>{{ t('courses.batchAddNoteNone') }}</span>{{ t('courses.batchAddNoteCodeContinue') }}</li>
              <li>{{ t('courses.batchAddNotePriority') }}</li>
            </ul>
          </template>
        </el-alert>
      </div>
      
      <el-form label-width="120px">
        <el-form-item :label="t('courses.courseInfo')">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            :placeholder="t('courses.batchAddPlaceholder')"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="batchAddDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleBatchAddSubmit" :loading="batchAddLoading">{{ t('common.batchAdd') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Search, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const currentUser = ref(null)
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)
const searchKeyword = ref('')

const courses = ref([])
const lastCourseCode = ref('')
const batchAddDialogVisible = ref(false)
const batchAddText = ref('')
const batchAddLoading = ref(false)
const teachers = ref([])

const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

const goBack = () => {
  router.back()
}

// 添加排序相关变量
const sortField = ref('')
const sortOrder = ref('asc')

// 添加排序处理函数
const handleSortChange = ({ prop, order }) => {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  pagination.value.currentPage = 1
  fetchCourses()
}

// 添加过滤相关变量
const filterName = ref('')
const filterCode = ref('')

const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchCourses()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchCourses()
}

const handleSearch = () => {
  pagination.value.currentPage = 1
  fetchCourses()
}

const form = ref({
  code: '',
  name: '',
  priority: 0,
  teacher_ids: []
})

// 表单数据备份储存
const originalForm = ref({
  code: '',
  name: '',
  priority: 0,
  teacher_ids: []
})

const rules = {
  code: [{ required: true, message: () => t('courses.courseCodeRequired'), trigger: 'blur' }],
  name: [{ required: true, message: () => t('courses.courseNameRequired'), trigger: 'blur' }]
}

const fetchTeachers = async () => {
  try {
    const response = await api.get('/teachers', { params: { skip: 0, limit: 100000 } })
    teachers.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取导师列表失败:', error)
  }
}

const fetchCourses = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    
    // 优先使用专门的过滤参数
    if (filterName.value) {
      params.name = filterName.value
    } else if (filterCode.value) {
      params.code = filterCode.value
    } else if (searchKeyword.value) {
      // 如果没有专门过滤，则使用通用搜索
      params.search = searchKeyword.value
    }
    
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    const response = await api.get('/courses', { params })
    courses.value = response.data.items
    pagination.value.total = response.data.total
    
    // 获取最后一个科目代码（按代码排序后的最后一个）
    if (response.data.items && response.data.items.length > 0) {
      const sortedByCode = [...response.data.items].sort((a, b) => a.code.localeCompare(b.code))
      lastCourseCode.value = sortedByCode[sortedByCode.length - 1].code
    } else {
      lastCourseCode.value = ''
    }
  } catch (error) {
    window.logger.error('获取科目列表失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterName.value = ''
  filterCode.value = ''
  sortField.value = ''
  sortOrder.value = 'asc'
  pagination.value.currentPage = 1
  fetchCourses()
}

const showAddDialog = () => {
  dialogTitle.value = t('courses.addCourseTitle')
  
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
    code: '',
    name: prefillData?.course_name || '',
    priority: prefillData?.priority || 0,
    teacher_ids: prefillData?.teacher_id ? [parseInt(prefillData.teacher_id)] : []
  }
  dialogVisible.value = true
}

const showBatchAddDialog = () => {
  batchAddText.value = ''
  batchAddDialogVisible.value = true
}
const handleBatchAddSubmit = async () => {
  if (!batchAddText.value.trim()) {
    ElMessage.warning(t('courses.batchAddWarning'))
    return
  }
  
  const lines = batchAddText.value.trim().split('\n')
  const coursesToAdd = []
  const errors = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    const parts = line.split(',').map(p => p.trim())
    if (parts.length < 2) {
      errors.push(t('courses.lineError', { line: i + 1, msg: t('courses.lineFormatError') }))
      continue
    }
    
    const course = {
      code: parts[0],
      name: parts[1],
      priority: parts[2] ? parseInt(parts[2]) : 0,
      teacher_ids: []
    }
    
    coursesToAdd.push(course)
  }
  
  if (errors.length > 0) {
    ElMessage.error(t('courses.batchAddErrorCount', { count: errors.length }) + '\n' + errors.join('\n'))
    if (coursesToAdd.length === 0) {
      return
    }
  }
  
  if (coursesToAdd.length === 0) {
    ElMessage.warning(t('courses.batchAddNoValid'))
    return
  }
  
  batchAddLoading.value = true
  try {
    let successCount = 0
    let failCount = 0
    const failMessages = []
    
    for (const course of coursesToAdd) {
      try {
        await api.post('/courses', course)
        successCount++
      } catch (error) {
        failCount++
        failMessages.push(t('courses.batchAddFailDetail', { code: course.code, name: course.name, detail: error.response?.data?.detail || error.message }))
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(t('courses.batchAddPartial', { success: successCount, fail: failCount }) + '\n' + failMessages.join('\n'))
    } else {
      ElMessage.success(t('courses.batchAddSuccess', { n: successCount }))
    }
    
    batchAddDialogVisible.value = false
    await fetchCourses()
  } catch (error) {
    window.logger.error('批量添加科目失败:', error)
    ElMessage.error(t('courses.batchAddFailed'))
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = t('courses.editCourseTitle')
  originalForm.value = {
    id: row.id,
    code: row.code,
    name: row.name,
    priority: row.priority,
    teacher_ids: row.teacher_ids || []
  }
  form.value = {
    id: row.id,
    code: row.code,
    name: row.name,
    priority: row.priority,
    teacher_ids: row.teacher_ids || []
  }
  
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
        if (form.value.id) {
          const isChanged = 
            form.value.code !== originalForm.value.code ||
            form.value.name !== originalForm.value.name ||
            form.value.priority !== originalForm.value.priority ||
            JSON.stringify(form.value.teacher_ids || []) !== JSON.stringify(originalForm.value.teacher_ids || [])
          
          if (!isChanged) {
            ElMessage.warning(t('common.noChange'))
            return
          }
          
          await api.put(`/courses/${form.value.id}`, form.value)
          ElMessage.success(t('common.updateSuccess'))
        } else {
          await api.post('/courses', form.value)
          ElMessage.success(t('common.createSuccess'))
        }
        dialogVisible.value = false
        fetchCourses()
      } catch (error) {
        window.logger.error('操作失败:', error)
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('courses.confirmDeleteCourse'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/courses/${row.id}`)
      ElMessage.success(t('common.deleteSuccess'))
      fetchCourses()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const getTeacherName = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.name : '-'
}

const getTeacherContactPhone = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.contact_phone : null
}

const getTeacherEmail = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.email : null
}

const goToPage = (path) => {
  router.push(path)
}

// 应用URL筛选参数的辅助函数
const applyUrlFilters = (urlParams) => {
  let hasUrlFilters = false
  const appliedFilters = []
  
  // 1. 处理按名称过滤
  if (urlParams.get('name')) {
    filterName.value = urlParams.get('name')
    hasUrlFilters = true
    appliedFilters.push(t('courses.filterName', { value: filterName.value }))
  }
  
  // 2. 处理按代码过滤
  if (urlParams.get('code')) {
    filterCode.value = urlParams.get('code')
    hasUrlFilters = true
    appliedFilters.push(t('courses.filterCode', { value: filterCode.value }))
  }
  
  // 3. 处理旧的search参数（向后兼容，仅在没有name和code时使用）
  if (urlParams.get('search') && !urlParams.get('name') && !urlParams.get('code')) {
    searchKeyword.value = urlParams.get('search')
    hasUrlFilters = true
    appliedFilters.push(t('courses.filterSearch', { value: searchKeyword.value }))
  }
  
  return { hasUrlFilters, appliedFilters }
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  
  // 获取URL参数
  const urlParams = new URLSearchParams(window.location.search)
  const action = route.query.action
  const relatedTo = urlParams.get('related_to')
  const viewDetail = urlParams.get('view_detail')
  
  // 先加载基础数据
  await fetchTeachers()
  
  // 应用URL筛选参数
  const { hasUrlFilters, appliedFilters } = applyUrlFilters(urlParams)
  
  // 如果有筛选参数，使用筛选条件获取数据
  if (hasUrlFilters) {
    pagination.value.currentPage = 1
    await fetchCourses()
    
    // 显示应用的过滤条件提示
    if (appliedFilters.length > 0) {
      ElMessage.success({
        message: t('courses.appliedFilters', { filters: appliedFilters.join(t('common.listSeparator')) }),
        duration: 3000
      })
    }
    
    // 如果需要查看关联信息
    if (relatedTo && sessionStorage.getItem('smartCommandData')) {
      try {
        const smartData = JSON.parse(sessionStorage.getItem('smartCommandData'))
        if (smartData.target_path && smartData.target_label) {
          const filterValue = filterName.value || filterCode.value || searchKeyword.value
          ElMessage.info(t('courses.foundCourseJump', { name: filterValue, label: smartData.target_label }))
          setTimeout(() => {
            window.location.href = `${smartData.target_path}?filter_by=course&filter_value=${encodeURIComponent(filterValue)}`
          }, 1500)
        }
      } catch (e) {
        window.logger.error('解析智能指令数据失败', e)
      }
    }
    
    // 如果需要查看详情
    if (viewDetail === 'true') {
      setTimeout(() => {
        const targetCourse = courses.value.find(c => 
          (filterName.value && c.name === filterName.value) ||
          (filterCode.value && c.code === filterCode.value) ||
          (searchKeyword.value && (c.name === searchKeyword.value || c.code === searchKeyword.value))
        )
        if (targetCourse) {
          showEditDialog(targetCourse)
        } else {
          ElMessage.warning(t('courses.noMatchingCourse'))
        }
      }, 800)
    }
  } else {
    // 没有筛选参数，正常获取数据
    await fetchCourses()
  }
  
  // 处理action参数
  if (action === 'add') {
    showAddDialog()
  } else if (action === 'edit' && route.query.id) {
    const courseId = parseInt(route.query.id)
    const course = courses.value.find(c => c.id === courseId)
    if (course) {
      showEditDialog(course)
    } else {
      try {
        const response = await api.get(`/courses/${courseId}`)
        if (response.data) {
          showEditDialog(response.data)
        }
      } catch (error) {
        window.logger.error('获取科目信息失败:', error)
        ElMessage.error(t('courses.fetchCourseFailed'))
      }
    }
  }

})

// 监听路由参数变化，支持从悬浮球等外部触发的操作
watch(() => route.query, (newQuery, oldQuery) => {
  // 避免初始化时触发
  if (!oldQuery || Object.keys(oldQuery).length === 0) {
    return
  }
  
  if (newQuery.action === 'add') {
    showAddDialog()
  } else if (newQuery.action === 'edit' && newQuery.id) {
    const courseId = parseInt(newQuery.id)
    const course = courses.value.find(c => c.id === courseId)
    if (course) {
      showEditDialog(course)
    } else {
      api.get(`/courses/${courseId}`).then(response => {
        if (response.data) {
          showEditDialog(response.data)
        }
      }).catch(error => {
        window.logger.error('获取科目信息失败:', error)
        ElMessage.error(t('courses.fetchCourseFailed'))
      })
    }
  } else if (newQuery.name !== undefined || newQuery.code !== undefined || newQuery.search !== undefined) {
    // 支持动态更新过滤参数
    const urlParams = new URLSearchParams()
    if (newQuery.name) urlParams.set('name', newQuery.name)
    if (newQuery.code) urlParams.set('code', newQuery.code)
    if (newQuery.search) urlParams.set('search', newQuery.search)
    
    const { hasUrlFilters, appliedFilters } = applyUrlFilters(urlParams)
    
    if (hasUrlFilters) {
      pagination.value.currentPage = 1
      fetchCourses()
      
      if (appliedFilters.length > 0) {
        ElMessage.success({
          message: t('courses.appliedFilters', { filters: appliedFilters.join(t('common.listSeparator')) }),
          duration: 3000
        })
      }
    }
  }
}, { deep: true })
</script>

<style scoped>
.courses-page {
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

.card-header .button-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-bar {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
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