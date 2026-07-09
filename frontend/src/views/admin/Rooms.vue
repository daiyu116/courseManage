// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="rooms-page">
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
          <span>{{ t('rooms.title') }}</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('common.back') }}
            </el-button>
            <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('rooms.addRoom') }}
            </el-button>
            <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" type="success" @click="showBatchAddDialog">
              <el-icon><Upload /></el-icon>
              {{ t('common.batchAdd') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          :placeholder="t('rooms.searchPlaceholder')"
          style="width: 300px"
          clearable
          @clear="fetchRooms"
          @keyup.enter="fetchRooms"
        >
          <template #append>
            <el-button @click="fetchRooms">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
        <el-select v-model="facilitiesFilter" :placeholder="t('rooms.facilitiesType')" clearable style="width: 150px" @change="fetchRooms">
          <el-option :label="t('rooms.multimedia')" value="多媒体" />
          <el-option :label="t('rooms.normal')" value="普通" />
        </el-select>
        <el-select v-model="isActiveFilter" :placeholder="t('rooms.activeStatus')" clearable style="width: 120px" @change="fetchRooms">
          <el-option :label="t('common.enabled')" :value="true" />
          <el-option :label="t('common.disabled')" :value="false" />
        </el-select>
        <el-button @click="resetFilters" style="width: 50px">{{ t('common.reset') }}</el-button>
      </div>

      <el-table :data="rooms" stripe v-loading="loading" style="margin-top: 20px" @sort-change="handleSortChange">
        <el-table-column prop="id" label="ID" width="70" sortable />
        <el-table-column prop="code" :label="t('rooms.roomCode')" width="120" sortable />
        <el-table-column prop="name" :label="t('rooms.roomName')" width="200" sortable />
        <el-table-column prop="location" :label="t('rooms.roomLocation')" width="200" sortable />
        <el-table-column prop="capacity" :label="t('rooms.capacity')" width="120" sortable />
        <el-table-column :label="t('rooms.facilities')" width="450" sortable >
          <template #default="{ row }">
            <div>
              <el-tag :type="row.facilities === '多媒体' ? 'primary' : 'info'" style="margin-right: 10px;">
                {{ row.facilities === '多媒体' ? t('rooms.multimedia') : t('rooms.normal') }}
              </el-tag>
            </div>
            <div v-if="row.facility_details" style="margin-top: 3px;">
                <el-tag 
                  v-for="item in parseFacilityDetails(row.facility_details)" 
                  :key="item" 
                  size="small" 
                  style="margin-right: 3px; margin-bottom: 3px;"
                >
                  {{ item }}
                </el-tag>
              </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('rooms.isActive')" width="100">
            <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? t('common.enabled') : t('common.disabled') }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="80" fixed="right">
          <template #default="{ row }">
            <el-button v-if="currentUser && currentUser.role !== 'teaching_assistant'" size="small" @click="showEditDialog(row)">{{ t('common.edit') }}</el-button>
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
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item :label="t('rooms.roomCode')" prop="code">
          <el-input v-model="form.code" :placeholder="lastRoomCode ? t('rooms.roomCodePlaceholderWithLast', { code: lastRoomCode }) : t('rooms.roomCodePlaceholder')" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item :label="t('rooms.roomName')" prop="name">
          <el-input v-model="form.name" :placeholder="t('rooms.roomNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('rooms.roomLocation')" prop="location">
          <el-input v-model="form.location" :placeholder="t('rooms.roomLocationPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('rooms.capacity')" prop="capacity">
          <el-input-number v-model="form.capacity" :min="1" :max="200" />
        </el-form-item>
        <el-form-item :label="t('rooms.facilities')" prop="facilities">
          <el-select v-model="form.facilities" :placeholder="t('rooms.selectFacilitiesPlaceholder')">
            <el-option :label="t('rooms.multimedia')" value="多媒体" />
            <el-option :label="t('rooms.normal')" value="普通" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('rooms.facilityDetails')" prop="facility_details">
          <el-checkbox-group v-model="form.facility_details">
            <el-checkbox 
              v-for="item in facilityOptions[form.facilities] || []" 
              :key="item" 
              :label="item"
            >
              {{ item }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item :label="t('rooms.isActive')" prop="is_active">
            <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 批量添加教室对话框 -->
    <el-dialog v-model="batchAddDialogVisible" :title="t('rooms.batchAddTitle')" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          :title="t('rooms.batchAddInfo')"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>{{ t('rooms.batchAddFormat') }}</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              {{ t('rooms.batchAddFormatLine') }}
            </div>
            <div style="margin-top: 10px;">{{ t('rooms.batchAddExample') }}</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              {{ t('rooms.batchAddExampleLine1') }}<br/>
              {{ t('rooms.batchAddExampleLine2') }}
            </div>
            <div style="margin-top: 10px;">{{ t('rooms.batchAddNote') }}</div>
            <ul style="margin-top: 5px;">
              <li>{{ t('rooms.batchAddNoteCode') }}<span v-if="lastRoomCode">{{ lastRoomCode }}</span><span v-else>{{ t('rooms.batchAddNoteNone') }}</span>{{ t('rooms.batchAddNoteCodeContinue') }}</li>
              <li>{{ t('rooms.batchAddNoteFacilities') }}</li>
            </ul>
          </template>
        </el-alert>
      </div>
      
      <el-form label-width="120px">
        <el-form-item :label="t('rooms.roomInfo')">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            :placeholder="t('rooms.batchAddPlaceholder')"
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
import { ref, computed, onMounted } from 'vue'
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
const facilitiesFilter = ref('')
const rooms = ref([])
const isActiveFilter = ref(null)
const lastRoomCode = ref('')
const batchAddDialogVisible = ref(false)
const batchAddText = ref('')
const batchAddLoading = ref(false)
// 设施选项定义
const facilityOptions = computed(() => ({
  '普通': [t('rooms.whiteboard'), t('rooms.fan'), t('rooms.airConditioner')],
  '多媒体': [t('rooms.projector'), t('rooms.tv'), t('rooms.computer'), t('rooms.whiteboard'), t('rooms.fan'), t('rooms.airConditioner')]
}))

const goBack = () => {
  router.back()
}
// 添加排序相关变量
const sortField = ref('')
const sortOrder = ref('asc')
const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

// 添加分页处理函数
const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchRooms()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchRooms()
}

// 添加排序处理函数
const handleSortChange = ({ prop, order }) => {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  pagination.value.currentPage = 1
  fetchRooms()
}

const form = ref({
  code: '',
  name: '',
  location: '',
  capacity: 30,
  facilities: '普通',
  facility_details: [], 
  is_active: true
})

const originalForm = ref({
  code: '',
  name: '',
  location: '',
  capacity: 30,
  facilities: '普通',
  facility_details: [], 
  is_active: true
})

const rules = {
  code: [{ required: true, message: () => t('rooms.roomCodeRequired'), trigger: 'blur' }],
  name: [{ required: true, message: () => t('rooms.roomNameRequired'), trigger: 'blur' }]
}

const fetchRooms = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (facilitiesFilter.value) {
      params.facilities = facilitiesFilter.value
    }
    if (isActiveFilter.value !== null && isActiveFilter.value !== undefined) {
      params.is_active = isActiveFilter.value
    }
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    const response = await api.get('/rooms', { params })
    rooms.value = response.data.items
    pagination.value.total = response.data.total
    
    // 获取最后一个教室代码（按代码排序后的最后一个）
    if (response.data.items && response.data.items.length > 0) {
      const sortedByCode = [...response.data.items].sort((a, b) => a.code.localeCompare(b.code))
      lastRoomCode.value = sortedByCode[sortedByCode.length - 1].code
    } else {
      lastRoomCode.value = ''
    }
  } catch (error) {
    window.logger.error('获取教室列表失败:', error)
  } finally {
    loading.value = false
  }
}

const parseFacilityDetails = (details) => {
  if (!details) return []
  try {
    return JSON.parse(details)
  } catch (error) {
    window.logger.error('解析设施详情失败:', error)
    return []
  }
}

const resetFilters = () => {
  searchKeyword.value = ''
  facilitiesFilter.value = ''
  isActiveFilter.value = null
  sortField.value = ''
  sortOrder.value = 'asc'
  pagination.value.currentPage = 1
  fetchRooms()
}

const showAddDialog = () => {
  dialogTitle.value = t('rooms.addRoomTitle')
  
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
    name: prefillData?.room_name || '',
    location: prefillData?.location || '',
    capacity: prefillData?.capacity || 30,
    facilities: '普通',
    is_active: true
  }
  dialogVisible.value = true
}
 
const showBatchAddDialog = () => {
  batchAddText.value = ''
  batchAddDialogVisible.value = true
}
 
const handleBatchAddSubmit = async () => {
  if (!batchAddText.value.trim()) {
    ElMessage.warning(t('rooms.batchAddWarning'))
    return
  }
  
  const lines = batchAddText.value.trim().split('\n')
  const roomsToAdd = []
  const errors = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    const parts = line.split(',').map(p => p.trim())
    if (parts.length < 2) {
      errors.push(t('rooms.lineError', { n: i + 1, msg: t('rooms.lineFormatError') }))
      continue
    }
    
    const room = {
      code: parts[0],
      name: parts[1],
      location: parts[2] || '',
      capacity: parts[3] ? parseInt(parts[3]) : 30,
      facilities: parts[4] || '普通',
      is_active: true
    }
    
    roomsToAdd.push(room)
  }
  
  if (errors.length > 0) {
    ElMessage.error(t('rooms.batchAddErrorCount', { count: errors.length }) + '\n' + errors.join('\n'))
    if (roomsToAdd.length === 0) {
      return
    }
  }
  
  if (roomsToAdd.length === 0) {
    ElMessage.warning(t('rooms.batchAddNoValid'))
    return
  }
  
  batchAddLoading.value = true
  try {
    let successCount = 0
    let failCount = 0
    const failMessages = []
    
    for (const room of roomsToAdd) {
      try {
        await api.post('/rooms', room)
        successCount++
      } catch (error) {
        failCount++
        failMessages.push(t('rooms.batchAddFailDetail', { code: room.code, name: room.name, detail: error.response?.data?.detail || error.message }))
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(t('rooms.batchAddPartial', { success: successCount, fail: failCount }) + '\n' + failMessages.join('\n'))
    } else {
      ElMessage.success(t('rooms.batchAddSuccess', { n: successCount }))
    }
    
    batchAddDialogVisible.value = false
    await fetchRooms()
  } catch (error) {
    window.logger.error('批量添加教室失败:', error)
    ElMessage.error(t('rooms.batchAddFailed'))
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = t('rooms.editRoomTitle')
  const formData = {
    id: row.id,
    code: row.code,
    name: row.name,
    location: row.location,
    capacity: row.capacity,
    facilities: row.facilities,
    facility_details: parseFacilityDetails(row.facility_details),
    is_active: row.is_active
  }
  originalForm.value = { ...formData }
  form.value = formData
  
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
        const submitData = {
          ...form.value,
          facility_details: JSON.stringify(form.value.facility_details || [])
        }
        
        if (form.value.id) {
          const isChanged = 
            form.value.code !== originalForm.value.code ||
            form.value.name !== originalForm.value.name ||
            form.value.location !== originalForm.value.location ||
            form.value.capacity !== originalForm.value.capacity ||
            form.value.facilities !== originalForm.value.facilities ||
            JSON.stringify(form.value.facility_details || []) !== JSON.stringify(originalForm.value.facility_details || []) ||
            form.value.is_active !== originalForm.value.is_active
          
          if (!isChanged) {
            ElMessage.warning(t('common.noChange'))
            return
          }
          
          await api.put(`/rooms/${form.value.id}`, submitData)
          ElMessage.success(t('common.updateSuccess'))
        } else {
          await api.post('/rooms', submitData)
          ElMessage.success(t('common.createSuccess'))
        }
        dialogVisible.value = false
        fetchRooms()
      } catch (error) {
        window.logger.error('操作失败:', error)
        ElMessage.error(t('rooms.operationFailed'))
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('rooms.confirmDeleteRoom'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/rooms/${row.id}`)
      ElMessage.success(t('common.deleteSuccess'))
      fetchRooms()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const goToPage = (path) => {
  router.push(path)
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  
  // 检查是否有来自智能指令的搜索参数
  const urlParams = new URLSearchParams(window.location.search)
  const searchQuery = urlParams.get('search')
  const facilitiesQuery = urlParams.get('facilities')
  const isActiveQuery = urlParams.get('is_active')
  const sortFieldQuery = urlParams.get('sort_field')
  const sortOrderQuery = urlParams.get('sort_order')
  const pageQuery = urlParams.get('page')
  const pageSizeQuery = urlParams.get('page_size')
  const relatedTo = urlParams.get('related_to')
  const viewDetail = urlParams.get('view_detail')
  
  // 应用URL参数到筛选条件
  if (searchQuery) {
    searchKeyword.value = searchQuery
  }
  if (facilitiesQuery) {
    facilitiesFilter.value = facilitiesQuery
  }
  if (isActiveQuery !== null && isActiveQuery !== undefined) {
    isActiveFilter.value = isActiveQuery === 'true' ? true : (isActiveQuery === 'false' ? false : null)
  }
  if (sortFieldQuery) {
    sortField.value = sortFieldQuery
  }
  if (sortOrderQuery) {
    sortOrder.value = sortOrderQuery === 'desc' ? 'desc' : 'asc'
  }
  if (pageQuery && !isNaN(parseInt(pageQuery))) {
    pagination.value.currentPage = parseInt(pageQuery)
  }
  if (pageSizeQuery && !isNaN(parseInt(pageSizeQuery))) {
    pagination.value.pageSize = parseInt(pageSizeQuery)
  }
  
  await fetchRooms()
  
  // 如果需要查看关联信息
  if (relatedTo && sessionStorage.getItem('smartCommandData')) {
    try {
      const smartData = JSON.parse(sessionStorage.getItem('smartCommandData'))
      if (smartData.target_path && smartData.target_label) {
        ElMessage.info(t('rooms.foundRelatedRoom', { label: smartData.target_label }))
        setTimeout(() => {
          window.location.href = `${smartData.target_path}?filter_by=room&filter_value=${encodeURIComponent(searchQuery || '')}`
        }, 1500)
      }
    } catch (e) {
      window.logger.error('解析智能指令数据失败', e)
    }
  }
  
  // 如果需要查看详情
  if (viewDetail === 'true' && searchQuery) {
    setTimeout(() => {
      const firstRoom = rooms.value.find(r => r.name === searchQuery || r.code === searchQuery)
      if (firstRoom) {
        showEditDialog(firstRoom)
      } else if (rooms.value.length > 0) {
        showEditDialog(rooms.value[0])
      }
    }, 1000)
  }
  
  // 检查是否需要自动打开新增对话框
  if (route.query.action === 'add') {
    showAddDialog()
  }
  
  // 检查是否需要自动打开编辑对话框
  if (route.query.action === 'edit' && route.query.id) {
    const roomId = parseInt(route.query.id)
    const room = rooms.value.find(r => r.id === roomId)
    if (room) {
      showEditDialog(room)
    } else {
      try {
        const response = await api.get(`/rooms/${roomId}`)
        if (response.data) {
          showEditDialog(response.data)
        }
      } catch (error) {
        window.logger.error('获取教室信息失败:', error)
        ElMessage.error(t('rooms.fetchRoomFailed'))
      }
    }
  }
})
</script>

<style scoped>
.rooms-page {
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