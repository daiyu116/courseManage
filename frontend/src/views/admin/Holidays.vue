// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="holidays-page">
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
          <span>{{ t('holidays.title') }}</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('common.back') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('holidays.addHoliday') }}
            </el-button>
            <el-button type="success" @click="showBatchAddDialog">
              <el-icon><Upload /></el-icon>
              {{ t('common.batchAdd') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="holidays" stripe v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="date" :label="t('holidays.holidayDate')" width="150">
          <template #default="{ row }">
            {{ formatDate(row.date) }}
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="t('holidays.holidayName')" width="200" />
        <el-table-column prop="description" :label="t('holidays.holidayDescription')" min-width="200" show-overflow-tooltip />
        <el-table-column :label="t('common.operation')" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">{{ t('common.edit') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[15, 25, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item :label="t('holidays.holidayDate')" prop="date">
          <el-date-picker
            v-model="form.date"
            type="date"
            :placeholder="t('holidays.datePlaceholder')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('holidays.holidayName')" prop="name">
          <el-input v-model="form.name" :placeholder="t('holidays.holidayNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('holidays.holidayDescription')" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="t('holidays.descriptionPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 批量添加假期对话框 -->
    <el-dialog v-model="batchAddDialogVisible" :title="t('holidays.batchAddTitle')" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          :title="t('holidays.batchAddInfo')"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>{{ t('holidays.batchAddFormat') }}</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              {{ t('holidays.batchAddFormatLine') }}
            </div>
            <div style="margin-top: 10px;">{{ t('holidays.batchAddExample') }}</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              {{ t('holidays.batchAddExampleLine1') }}<br/>
              {{ t('holidays.batchAddExampleLine2') }}<br/>
              {{ t('holidays.batchAddExampleLine3') }}
            </div>
            <div style="margin-top: 10px;">{{ t('holidays.batchAddNote') }}</div>
            <ul style="margin-top: 5px;">
              <li>{{ t('holidays.batchAddNoteDateFormat') }}</li>
              <li>{{ t('holidays.batchAddNoteNoDuplicate') }}</li>
            </ul>
          </template>
        </el-alert>
      </div>
      
      <el-form label-width="120px">
        <el-form-item :label="t('holidays.holidayInfo')">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            :placeholder="t('holidays.batchAddPlaceholder')"
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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Search, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const currentUser = ref(null)
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)

const holidays = ref([])
const batchAddDialogVisible = ref(false)
const batchAddText = ref('')
const batchAddLoading = ref(false)

const goBack = () => {
  router.back()
}

const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchHolidays()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchHolidays()
}

const form = ref({
  date: '',
  name: '',
  description: ''
})

const originalForm = ref({
  date: '',
  name: '',
  description: ''
})

const rules = {
  date: [{ required: true, message: () => t('holidays.dateRequired'), trigger: 'change' }],
  name: [{ required: true, message: () => t('holidays.holidayNameRequired'), trigger: 'blur' }]
}

const fetchHolidays = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    const response = await api.get('/holidays/holidays', { params })
    holidays.value = response.data.items
    pagination.value.total = response.data.total
  } catch (error) {
    window.logger.error('获取节假日列表失败:', error)
    ElMessage.error(t('holidays.fetchHolidaysFailed'))
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = t('holidays.addHolidayTitle')
  
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
    date: prefillData?.start_date || '',
    name: prefillData?.holiday_name || '',
    description: ''
  }
  dialogVisible.value = true
}

const showBatchAddDialog = () => {
  batchAddText.value = ''
  batchAddDialogVisible.value = true
}
const handleBatchAddSubmit = async () => {
  if (!batchAddText.value.trim()) {
    ElMessage.warning(t('holidays.batchAddWarning'))
    return
  }
  
  const lines = batchAddText.value.trim().split('\n')
  const holidaysToAdd = []
  const errors = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    const parts = line.split(',').map(p => p.trim())
    if (parts.length < 2) {
      errors.push(t('holidays.lineError', { n: i + 1, msg: t('holidays.lineFormatError') }))
      continue
    }
    
    // 验证日期格式
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/
    if (!dateRegex.test(parts[0])) {
      errors.push(t('holidays.lineError', { n: i + 1, msg: t('holidays.lineDateFormatError') }))
      continue
    }
    
    const holiday = {
      date: parts[0],
      name: parts[1],
      description: parts[2] || ''
    }
    
    holidaysToAdd.push(holiday)
  }
  
  if (errors.length > 0) {
    ElMessage.error(t('holidays.batchAddErrorCount', { count: errors.length }) + '\n' + errors.join('\n'))
    if (holidaysToAdd.length === 0) {
      return
    }
  }
  
  if (holidaysToAdd.length === 0) {
    ElMessage.warning(t('holidays.batchAddNoValid'))
    return
  }
  
  batchAddLoading.value = true
  try {
    let successCount = 0
    let failCount = 0
    const failMessages = []
    
    for (const holiday of holidaysToAdd) {
      try {
        await api.post('/holidays/holidays', holiday)
        successCount++
      } catch (error) {
        failCount++
        failMessages.push(t('holidays.batchAddFailDetail', { date: holiday.date, name: holiday.name, detail: error.response?.data?.detail || error.message }))
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(t('holidays.batchAddPartial', { success: successCount, fail: failCount }) + '\n' + failMessages.join('\n'))
    } else {
      ElMessage.success(t('holidays.batchAddSuccess', { n: successCount }))
    }
    
    batchAddDialogVisible.value = false
    await fetchHolidays()
  } catch (error) {
    window.logger.error('批量添加假期失败:', error)
    ElMessage.error(t('holidays.batchAddFailed'))
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = t('holidays.editHolidayTitle')
  const formData = {
    id: row.id,
    date: row.date,
    name: row.name,
    description: row.description
  }
  
  originalForm.value = { ...formData }
  form.value = formData
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (form.value.id) {
          const isChanged = 
            form.value.date !== originalForm.value.date ||
            form.value.name !== originalForm.value.name ||
            form.value.description !== originalForm.value.description
          
          if (!isChanged) {
            ElMessage.warning(t('common.noChange'))
            return
          }
          
          await api.put(`/holidays/holidays/${form.value.id}`, {
            name: form.value.name,
            description: form.value.description
          })
          ElMessage.success(t('common.updateSuccess'))
        } else {
          // 确保日期格式正确
          const submitData = {
            date: form.value.date,
            name: form.value.name,
            description: form.value.description || ''
          }
          window.logger.log('提交数据:', submitData)
          await api.post('/holidays/holidays', submitData)
          ElMessage.success(t('common.createSuccess'))
        }
        dialogVisible.value = false
        fetchHolidays()
      } catch (error) {
        window.logger.error('操作失败:', error)
        ElMessage.error(error.response?.data?.detail || t('common.operationFailed'))
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('holidays.confirmDeleteHoliday'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/holidays/holidays/${row.id}`)
      ElMessage.success(t('common.deleteSuccess'))
      fetchHolidays()
    } catch (error) {
      window.logger.error('删除失败:', error)
      ElMessage.error(t('holidays.deleteFailed'))
    }
  }).catch(() => {})
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD')
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
  
  fetchHolidays()
  
  // 如果有搜索参数，自动填充并执行搜索
  if (searchQuery) {
    filters.value.name = searchQuery
    setTimeout(() => {
      fetchHolidays()
    }, 500)
  }
  
  // 检查是否需要自动打开新增对话框
  if (route.query.action === 'add') {
    showAddDialog()
  }
})
</script>

<style scoped>
.holidays-page {
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