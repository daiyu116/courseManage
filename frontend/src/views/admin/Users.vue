// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="users-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('users.title') }}</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('common.back') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('users.addUser') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm">
        <el-form-item :label="t('users.username')">
          <el-input v-model="searchForm.search" :placeholder="t('users.usernamePlaceholder')" clearable @clear="fetchUsers" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchUsers">
            <el-icon><Search /></el-icon>
            {{ t('common.search') }}
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="users" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" :label="t('users.username')" />
        <el-table-column prop="teacher_id" :label="t('users.boundTeacher')" width="150">
          <template #default="{ row }">
            <span v-if="(row.role === 'course_admin' || row.role === 'teaching_assistant') && row.teacher_id">
              {{ getTeacherName(row.teacher_id) }}
            </span>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="role" :label="t('users.role')" width="180">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="t('users.createdAt')" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">{{ t('common.edit') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" @opened="fetchTeachers">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item :label="t('users.username')" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item :label="t('users.password')" prop="password">
          <el-input v-model="form.password" type="password" show-password :placeholder="t('users.passwordPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('users.role')" prop="role">
          <el-select v-model="form.role" :placeholder="t('users.rolePlaceholder')" @change="handleRoleChange">
            <el-option :label="t('users.superAdmin')" value="super_admin" />
            <el-option :label="t('users.systemAdmin')" value="system_admin" />
            <el-option :label="t('users.courseAdmin')" value="course_admin" />
            <el-option :label="t('users.systemAudit')" value="system_audit" />
            <el-option :label="t('users.teachingAssistant')" value="teaching_assistant" />
          </el-select>
        </el-form-item>
        <!-- 导师绑定 -->
        <el-form-item :label="t('users.relatedTeacher')" prop="teacher_id" v-if="form.role === 'course_admin' || form.role === 'teaching_assistant'">
          <el-select 
            v-model="form.teacher_id" 
            :placeholder="t('users.relatedTeacherPlaceholder')" 
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
            {{ t('users.relatedTeacherTip') }}
            <br>
            {{ t('users.currentTeacherCount') }} {{ teachers.length }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" :title="t('users.changePasswordTitle')" width="500px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item :label="t('users.oldPassword')" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('users.newPassword')" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handlePasswordChange">{{ t('common.confirm') }}</el-button>
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
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const router = useRouter()
const users = ref([])
const teachers = ref([])
const dialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const dialogTitle = ref(t('users.addUser'))
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
  username: [{ required: true, message: t('users.usernameRequired'), trigger: 'blur' }],
  password: [
    { 
      validator: (rule, value, callback) => {
        if (!form.id && !value) { // 如果是新增且没填密码
          callback(new Error(t('users.passwordRequired')));
        } else if (value && value.length < 6) {
          callback(new Error(t('users.passwordMinLength')));
        } else {
          callback();
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

const passwordRules = {
  old_password: [{ required: true, message: t('users.oldPasswordRequired'), trigger: 'blur' }],
  new_password: [
    { required: true, message: t('users.newPasswordRequired'), trigger: 'blur' },
    { min: 6, message: t('users.passwordMinLength'), trigger: 'blur' }
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
  if (val !== 'course_admin' && val !== 'teaching_assistant') {
    form.teacher_id = null
  }
}

const showAddDialog = () => {
  dialogTitle.value = t('users.addUser')
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
  dialogTitle.value = t('users.editUser')
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
          ElMessage.success(t('common.updateSuccess'))
        } else {
          await api.post('/auth', payload)
          ElMessage.success(t('common.createSuccess'))
        }
        dialogVisible.value = false
        fetchUsers()
      } catch (error) {
        window.logger.error('操作失败:', error)
        ElMessage.error(error.response?.data?.detail || t('common.operationFailed'))
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('users.confirmDeleteUser'), t('common.confirm'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/auth/${row.id}`)
      ElMessage.success(t('common.deleteSuccess'))
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
        ElMessage.success(t('users.passwordChangeSuccess'))
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
    'system_audit': 'info',
    'teaching_assistant': 'success'
  }
  return typeMap[role] || 'info'
}
 
const getRoleText = (role) => {
  const textMap = {
    'super_admin': t('users.superAdmin'),
    'system_admin': t('users.systemAdmin'),
    'course_admin': t('users.courseAdmin'),
    'system_audit': t('users.systemAudit'),
    'teaching_assistant': t('users.teachingAssistant')
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