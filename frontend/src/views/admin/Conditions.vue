// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="conditions-page">
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
            <el-button type="warning" @click="goToPage('/admin/classes')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
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
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>条件管理</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="硬性约束" name="hard">
          <el-table :data="hardConstraints" stripe>
            <el-table-column prop="name" label="约束名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag type="success">启用</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="软性约束" name="soft">
          <div class="table-operations">
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              新增条件
            </el-button>
          </div>
          <el-table :data="softConstraints" stripe v-loading="loading">
            <el-table-column prop="id" label="ID" width="50" />
            <el-table-column prop="name" label="条件名称" />
            <el-table-column prop="condition_type" label="条件类型" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
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
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            style="margin-top: 20px; justify-content: center; display: flex;"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="条件名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入条件名称" />
        </el-form-item>
        <el-form-item label="条件类型" prop="condition_type">
          <el-select v-model="form.condition_type" placeholder="请选择条件类型">
            <el-option label="导师偏好" value="teacher_preference" />
            <el-option label="教室偏好" value="room_preference" />
            <el-option label="时间偏好" value="time_preference" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入条件描述" />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="form.is_active" />
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Plus, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const currentUser = ref(null)
const router = useRouter()

const loading = ref(false)
const activeTab = ref('hard')
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)

const goBack = () => {
  router.back()
}

const hardConstraints = ref([
  {
    name: '导师时间约束',
    description: '一个导师在同一个时间（课节）内只能教授一门课程'
  },
  {
    name: '学员时间约束',
    description: '一个学员在同一个时间（课节）内只能被安排一门课程'
  },  
  {
    name: '班级时间约束',
    description: '一个班级在同一个时间（课节）内只能安排一门课程'
  },
  {
    name: '教室时间约束',
    description: '一个教室在同一个时间（课节）内只能承接一门课程'
  }
])

const softConstraints = ref([])

const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchSoftConstraints()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchSoftConstraints()
}

const form = ref({
  name: '',
  condition_type: '',
  description: '',
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入条件名称', trigger: 'blur' }],
  condition_type: [{ required: true, message: '请选择条件类型', trigger: 'change' }]
}

const fetchSoftConstraints = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    const response = await api.get('/conditions/soft', { params })
    softConstraints.value = response.data.items
    pagination.value.total = response.data.total
  } catch (error) {
    window.logger.error('获取软性约束失败:', error)
  } finally {
    loading.value = false
  }
}
const showAddDialog = () => {
  dialogTitle.value = '新增条件'
  form.value = {
    name: '',
    condition_type: '',
    description: '',
    is_active: true
  }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  dialogTitle.value = '编辑条件'
  form.value = {
    id: row.id,
    name: row.name,
    condition_type: row.condition_type,
    description: row.description,
    is_active: row.is_active
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (form.value.id) {
          await api.put(`/conditions/${form.value.id}`, form.value)
          ElMessage.success('更新成功')
        } else {
          await api.post('/conditions', form.value)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchSoftConstraints()
      } catch (error) {
        window.logger.error('操作失败:', error)
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该条件吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/conditions/${row.id}`)
      ElMessage.success('删除成功')
      fetchSoftConstraints()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const goToPage = (path) => {
  router.push(path)
}

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  fetchSoftConstraints()
})
</script>

<style scoped>
.conditions-page {
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

.table-operations {
  margin-bottom: 15px;
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