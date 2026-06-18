// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 CourseArrange Contributors
<template>
  <div class="users-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回上一页
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              新增用户
            </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.search" placeholder="请输入用户名" clearable @clear="fetchUsers" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchUsers">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="users" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="teacher_id" label="绑定导师" width="150">
          <template #default="{ row }">
            <span v-if="row.role === 'course_admin' && row.teacher_id">
              {{ getTeacherName(row.teacher_id) }}
            </span>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="180">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间(UTC时间)" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" @opened="fetchTeachers">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="不修改请留空" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" @change="handleRoleChange">
            <el-option label="超级管理员" value="super_admin" />
            <el-option label="系统管理员" value="system_admin" />
            <el-option label="课程管理员" value="course_admin" />
            <el-option label="系统审计员" value="system_audit" />
          </el-select>
        </el-form-item>
        <!-- 导师绑定 -->
        <el-form-item label="关联导师" prop="teacher_id" v-if="form.role === 'course_admin'">
          <el-select 
            v-model="form.teacher_id" 
            placeholder="请选择关联的导师" 
            clearable 
            filterable
            style="width: 100%"
          >
            <el-option 
              v-for="t in teachers" 
              :key="t.id" 
              :label="`${t.name} (ID: ${t.id})`" 
              :value="t.id" 
            />
          </el-select>
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            提示：绑定后，该用户登录后能且仅能看到对应导师姓名相关的科目、班级和排课。
            <br>
            当前导师数量: {{ teachers.length }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="500px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePasswordChange">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search , ArrowLeft} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const users = ref([])
const teachers = ref([])
const dialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const dialogTitle = ref('新增用户')
const formRef = ref(null)
const passwordFormRef = ref(null)

const searchForm = ref({
  search: ''
})

const goBack = () => {
  router.back()
}

const form = reactive({
  id: null,
  username: '',
  password: '',
  role: 'course_admin', // 默认角色设为 course_admin 以便触发 v-if
  teacher_id: null
})

const passwordForm = ref({
  old_password: '',
  new_password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { 
      validator: (rule, value, callback) => {
        if (!form.id && !value) { // 如果是新增且没填密码
          callback(new Error('请输入密码'));
        } else if (value && value.length < 6) {
          callback(new Error('密码长度不能少于6位'));
        } else {
          callback();
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const fetchUsers = async () => {
  try {
    const params = {}
    if (searchForm.value.search) {
      params.search = searchForm.value.search
    }
    const response = await api.get('/auth', { params })
    users.value = response.data
  } catch (error) {
    window.logger.error('获取用户列表失败:', error)
  }
}

// 获取导师列表
const fetchTeachers = async () => {
  try {
    const res = await api.get('/teachers', { params: { is_active: true, skip: 0, limit: 100000 } })
    teachers.value = res.data.items || res.data || []
  } catch (error) {
    window.logger.error('获取导师列表失败:', error)
  }
}

// 根据 ID 获取导师姓名
const getTeacherName = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId)
  return teacher ? teacher.name : `ID:${teacherId}`
}

// 监听角色变化，如果切换到非导师角色，清空 teacher_id
const handleRoleChange = (val) => {
  if (val !== 'course_admin') {
    form.teacher_id = null
  }
}

const showAddDialog = () => {
  dialogTitle.value = '新增用户'
  Object.assign(form, {
    id: null,
    username: '',
    password: '',
    role: 'course_admin',
    teacher_id: null
  })
  dialogVisible.value = true
  fetchTeachers() // 打开对话框时加载导师列表
}

const showEditDialog = (row) => {
  dialogTitle.value = '编辑用户'
  Object.assign(form, {
    id: row.id,
    username: row.username,
    password: '', // 编辑时不回填密码
    role: row.role,
    teacher_id: row.teacher_id || null
  })
  dialogVisible.value = true
  fetchTeachers() // 打开对话框时加载导师列表
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 构造提交数据，如果密码为空则不发送密码字段（视后端逻辑而定，通常后端会处理）
        const payload = { ...form }
        if (!payload.password) {
          delete payload.password
        }

        if (form.id) {
          await api.put(`/auth/${form.id}`, payload)
          ElMessage.success('更新成功')
        } else {
          await api.post('/auth', payload)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchUsers()
      } catch (error) {
        window.logger.error('操作失败:', error)
        ElMessage.error(error.response?.data?.detail || '操作失败')
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该用户吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/auth/${row.id}`)
      ElMessage.success('删除成功')
      fetchUsers()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
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

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}
 
const getRoleType = (role) => {
  const typeMap = {
    'super_admin': 'danger',
    'system_admin': 'warning',
    'course_admin': 'primary',
    'system_audit': 'info'
  }
  return typeMap[role] || 'info'
}
 
const getRoleText = (role) => {
  const textMap = {
    'super_admin': '超级管理员',
    'system_admin': '系统管理员',
    'course_admin': '课程管理员',
    'system_audit': '系统审计员'
  }
  return textMap[role] || role
}
 
onMounted(() => {
  fetchUsers()
  fetchTeachers() // 初始化时也加载一次导师列表，用于表格显示
})

</script>

<style scoped>
.users-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>