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
          <span>教室管理</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回上一页
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              新增教室
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
          placeholder="搜索教室名称、代码或位置"
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
        <el-select v-model="facilitiesFilter" placeholder="设施类型" clearable style="width: 150px" @change="fetchRooms">
          <el-option label="多媒体" value="多媒体" />
          <el-option label="普通" value="普通" />
        </el-select>
        <el-select v-model="isActiveFilter" placeholder="启用状态" clearable style="width: 120px" @change="fetchRooms">
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        <el-button @click="resetFilters" style="width: 50px">重置</el-button>
      </div>

      <el-table :data="rooms" stripe v-loading="loading" style="margin-top: 20px" @sort-change="handleSortChange">
        <el-table-column prop="id" label="ID" width="70" sortable />
        <el-table-column prop="code" label="教室代码" width="120" sortable />
        <el-table-column prop="name" label="教室名称" width="200" sortable />
        <el-table-column prop="location" label="教室位置" width="200" sortable />
        <el-table-column prop="capacity" label="容量(人数)" width="120" sortable />
        <el-table-column label="设施" width="450" sortable >
          <template #default="{ row }">
            <div>
              <el-tag :type="row.facilities === '多媒体' ? 'primary' : 'info'" style="margin-right: 10px;">
                {{ row.facilities }}
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
        <el-table-column label="是否启用" width="100">
            <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '启用' : '禁用' }}
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
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="教室代码" prop="code">
          <el-input v-model="form.code" :placeholder="lastRoomCode ? `请输入教室代码(不能与现有重复，当前已到：${lastRoomCode})` : '请输入教室代码(不能与现有重复)'" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="教室名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入教室名称" />
        </el-form-item>
        <el-form-item label="教室位置" prop="location">
          <el-input v-model="form.location" placeholder="请输入教室位置" />
        </el-form-item>
        <el-form-item label="容量(人数)" prop="capacity">
          <el-input-number v-model="form.capacity" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="设施" prop="facilities">
          <el-select v-model="form.facilities" placeholder="请选择设施类型">
            <el-option label="多媒体" value="多媒体" />
            <el-option label="普通" value="普通" />
          </el-select>
        </el-form-item>
        <el-form-item label="设施内容" prop="facility_details">
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
        <el-form-item label="是否启用" prop="is_active">
            <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    <!-- 批量添加教室对话框 -->
    <el-dialog v-model="batchAddDialogVisible" title="批量添加教室" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          title="批量添加说明"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>请按照以下格式输入教室信息，每行一个教室：</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              代码(*必填),名称(*必填),位置,容量(人数),设施
            </div>
            <div style="margin-top: 10px;">例如：</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              R001,101教室,一楼东侧,30,多媒体<br/>
              R002,102教室,二楼西侧,40,普通
            </div>
            <div style="margin-top: 10px;">注意：</div>
            <ul style="margin-top: 5px;">
              <li>代码不能与现有教室重复否则无法创建，上一个教室代码：<span v-if="lastRoomCode">{{ lastRoomCode }}</span><span v-else>无</span>，请在这个代码+1的基础上开始</li>
              <li>设施：多媒体/普通</li>
            </ul>
          </template>
        </el-alert>
      </div>
      
      <el-form label-width="120px">
        <el-form-item label="教室信息">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            placeholder="请输入教室信息，每行一个教室"
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
const facilityOptions = {
  普通: ['手写白板', '电风扇', '空调'],
  多媒体: ['投影仪', '投屏电视', '计算机', '手写白板', '电风扇', '空调']
}

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
  code: [{ required: true, message: '请输入教室代码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入教室名称', trigger: 'blur' }]
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
  dialogTitle.value = '新增教室'
  
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
    ElMessage.warning('请输入教室信息')
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
      errors.push(`第${i + 1}行：格式错误，至少需要代码和名称`)
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
    ElMessage.error(`发现${errors.length}个错误：\n${errors.join('\n')}`)
    if (roomsToAdd.length === 0) {
      return
    }
  }
  
  if (roomsToAdd.length === 0) {
    ElMessage.warning('没有有效的教室信息')
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
        failMessages.push(`${room.code}(${room.name}): ${error.response?.data?.detail || error.message}`)
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(`批量添加完成：成功${successCount}个，失败${failCount}个\n失败详情：\n${failMessages.join('\n')}`)
    } else {
      ElMessage.success(`批量添加成功，共添加${successCount}个教室`)
    }
    
    batchAddDialogVisible.value = false
    await fetchRooms()
  } catch (error) {
    window.logger.error('批量添加教室失败:', error)
    ElMessage.error('批量添加教室失败')
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = '编辑教室'
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
            ElMessage.warning('内容未发生改变，无需保存')
            return
          }
          
          await api.put(`/rooms/${form.value.id}`, submitData)
          ElMessage.success('更新成功')
        } else {
          await api.post('/rooms', submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchRooms()
      } catch (error) {
        window.logger.error('操作失败:', error)
        ElMessage.error('操作失败')
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该教室吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/rooms/${row.id}`)
      ElMessage.success('删除成功')
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
        ElMessage.info(`已找到相关教室，正在跳转到${smartData.target_label}...`)
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
        ElMessage.error('无法加载教室信息')
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