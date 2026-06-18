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
          <span>假期管理</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回上一页
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              新增假期
            </el-button>
            <el-button type="success" @click="showBatchAddDialog">
              <el-icon><Upload /></el-icon>
              批量添加
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="holidays" stripe v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="date" label="日期" width="150">
          <template #default="{ row }">
            {{ formatDate(row.date) }}
          </template>
        </el-table-column>
        <el-table-column prop="name" label="假期名称" width="200" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
        <el-form-item label="日期" prop="date">
          <el-date-picker
            v-model="form.date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="假期名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入假期名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    <!-- 批量添加假期对话框 -->
    <el-dialog v-model="batchAddDialogVisible" title="批量添加假期" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          title="批量添加说明"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>请按照以下格式输入假期信息，每行一个假期：</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              日期,假期名称,描述
            </div>
            <div style="margin-top: 10px;">例如：</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              2024-05-01,劳动节,五一劳动节假期<br/>
              2024-05-02,劳动节,五一劳动节假期<br/>
              2024-05-03,劳动节,五一劳动节假期
            </div>
            <div style="margin-top: 10px;">注意：</div>
            <ul style="margin-top: 5px;">
              <li>日期格式：YYYY-MM-DD（如：2024-05-01）</li>
              <li>日期不能与现有假期重复</li>
            </ul>
          </template>
        </el-alert>
      </div>
      
      <el-form label-width="120px">
        <el-form-item label="假期信息">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            placeholder="请输入假期信息，每行一个假期"
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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Search, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'

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
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  name: [{ required: true, message: '请输入假期名称', trigger: 'blur' }]
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
    ElMessage.error('获取节假日列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = '新增假期'
  
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
    ElMessage.warning('请输入假期信息')
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
      errors.push(`第${i + 1}行：格式错误，至少需要日期和假期名称`)
      continue
    }
    
    // 验证日期格式
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/
    if (!dateRegex.test(parts[0])) {
      errors.push(`第${i + 1}行：日期格式错误，应为YYYY-MM-DD格式`)
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
    ElMessage.error(`发现${errors.length}个错误：\n${errors.join('\n')}`)
    if (holidaysToAdd.length === 0) {
      return
    }
  }
  
  if (holidaysToAdd.length === 0) {
    ElMessage.warning('没有有效的假期信息')
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
        failMessages.push(`${holiday.date}(${holiday.name}): ${error.response?.data?.detail || error.message}`)
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(`批量添加完成：成功${successCount}个，失败${failCount}个\n失败详情：\n${failMessages.join('\n')}`)
    } else {
      ElMessage.success(`批量添加成功，共添加${successCount}个假期`)
    }
    
    batchAddDialogVisible.value = false
    await fetchHolidays()
  } catch (error) {
    window.logger.error('批量添加假期失败:', error)
    ElMessage.error('批量添加假期失败')
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = '编辑假期'
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
            ElMessage.warning('内容未发生改变，无需保存')
            return
          }
          
          await api.put(`/holidays/holidays/${form.value.id}`, {
            name: form.value.name,
            description: form.value.description
          })
          ElMessage.success('更新成功')
        } else {
          // 确保日期格式正确
          const submitData = {
            date: form.value.date,
            name: form.value.name,
            description: form.value.description || ''
          }
          window.logger.log('提交数据:', submitData)
          await api.post('/holidays/holidays', submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchHolidays()
      } catch (error) {
        window.logger.error('操作失败:', error)
        ElMessage.error(error.response?.data?.detail || '操作失败')
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该节假日吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/holidays/holidays/${row.id}`)
      ElMessage.success('删除成功')
      fetchHolidays()
    } catch (error) {
      window.logger.error('删除失败:', error)
      ElMessage.error('删除失败')
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