// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="database-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据库管理</span>
          <el-button @click="goBack">返回上一页</el-button>
        </div>
      </template>

      <div v-if="!hasFeature(FEATURES.DATABASE_MANAGEMENT)" class="no-auth-tip">
        <el-icon :size="48" color="#909399"><Lock /></el-icon>
        <p style="margin-top: 12px; color: #909399; font-size: 14px;">数据库管理功能未授权</p>
        <p style="color: #c0c4cc; font-size: 12px;">请前往授权管理页面获取相应功能授权</p>
        <el-button type="primary" size="small" style="margin-top: 12px" @click="goToLicense">前往授权管理</el-button>
      </div>

      <template v-else>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>数据库手动备份</span>
              </template>
              <el-button type="primary" @click="backupDatabase" :loading="backupLoading">
                <el-icon><Download /></el-icon>
                备份数据库
              </el-button>
              <p style="margin-top: 20px; color: #666">
                备份当前数据库的所有数据，导出为 SQL 文件
              </p>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                <span>数据库恢复</span>
              </template>
              <el-upload
                :auto-upload="false"
                :on-change="handleRestoreFileChange"
                :limit="1"
                accept=".csv,.sql"
              >
                <el-button type="warning">
                  <el-icon><Upload /></el-icon>
                  选择备份文件
                </el-button>
              </el-upload>
              <el-button
                type="danger"
                @click="restoreDatabase"
                :loading="restoreLoading"
                :disabled="!restoreFile"
                style="margin-top: 10px"
              >
                恢复数据库
              </el-button>
              <p style="margin-top: 20px; color: #666">
                注意！危险操作：将从备份文件恢复数据库，此操作将覆盖当前数据
              </p>
            </el-card>
          </el-col>
        </el-row>

        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>数据库自动备份</span>
              <el-tag :type="autoBackupConfig.enabled ? 'success' : 'info'" size="small">
                {{ autoBackupConfig.enabled ? '已启用' : '未启用' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="autoBackupConfig" label-width="120px" style="max-width: 500px">
            <el-form-item label="启用自动备份">
              <el-switch v-model="autoBackupConfig.enabled" />
            </el-form-item>
            <el-form-item label="备份频率">
              <el-select v-model="autoBackupConfig.frequency" style="width: 100%">
                <el-option label="每天（凌晨2点）" value="daily" />
                <el-option label="每12小时（0:00/12:00）" value="every_12_hours" />
                <el-option label="每6小时（0:00/6:00/12:00/18:00）" value="every_6_hours" />
                <el-option label="每周一（凌晨2点）" value="weekly" />
              </el-select>
            </el-form-item>
            <el-form-item label="保留备份数">
              <el-input-number v-model="autoBackupConfig.keep_count" :min="1" :max="90" />
              <span style="margin-left: 8px; color: #909399; font-size: 12px">超过此数量将自动删除最旧的备份</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveAutoBackupConfig" :loading="saveConfigLoading">保存配置</el-button>
              <el-button @click="triggerManualBackup" :loading="triggerLoading">立即执行一次备份</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div class="card-header" style="margin-bottom: 12px">
            <span>备份文件列表</span>
            <el-button size="small" @click="fetchBackupList" :loading="listLoading">刷新</el-button>
          </div>

          <el-table :data="backupList" style="width: 100%" size="small" v-loading="listLoading" empty-text="暂无备份文件">
            <el-table-column prop="filename" label="文件名" min-width="200" />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag :type="row.type === 'sql' ? 'success' : 'warning'" size="small">{{ row.type.toUpperCase() }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="size" label="大小" width="120">
              <template #default="{ row }">{{ formatSize(row.size) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="downloadBackup(row.filename)">下载</el-button>
                <el-popconfirm title="确定删除此备份文件？" @confirm="deleteBackup(row.filename)">
                  <template #reference>
                    <el-button size="small" type="danger" link>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>

          <p style="margin-top: 12px; color: #909399; font-size: 12px">
            备份存储路径：{{ backupDir }}
          </p>
        </el-card>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Upload, Lock } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { hasFeature, FEATURES } from '@/utils/license'

const router = useRouter()

const backupLoading = ref(false)
const restoreLoading = ref(false)
const restoreFile = ref(null)
const saveConfigLoading = ref(false)
const triggerLoading = ref(false)
const listLoading = ref(false)
const backupList = ref([])
const backupDir = ref('')

const autoBackupConfig = ref({
  enabled: false,
  frequency: 'daily',
  keep_count: 7,
})

const goBack = () => {
  router.back()
}

const goToLicense = () => {
  router.push('/admin/license')
}

const backupDatabase = async () => {
  try {
    await ElMessageBox.confirm('确定要备份数据库吗？', '确认备份', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    backupLoading.value = true
    const response = await api.get('/database/backup', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `database_backup_${new Date().toISOString().split('T')[0]}.sql`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('数据库备份成功')
    fetchBackupList()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('备份失败:', error)
      ElMessage.error('数据库备份失败')
    }
  } finally {
    backupLoading.value = false
  }
}

const handleRestoreFileChange = (file) => {
  restoreFile.value = file.raw
}

const restoreDatabase = async () => {
  try {
    await ElMessageBox.confirm(
      '恢复数据库将覆盖当前所有数据，此操作不可恢复！确定要继续吗？',
      '危险操作',
      { confirmButtonText: '确定恢复', cancelButtonText: '取消', type: 'error' }
    )
    restoreLoading.value = true
    const formData = new FormData()
    formData.append('file', restoreFile.value)
    await api.post('/database/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('数据库恢复成功，请刷新页面')
    setTimeout(() => { window.location.reload() }, 2000)
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('恢复失败:', error)
      ElMessage.error(error.response?.data?.detail || '数据库恢复失败')
    }
  } finally {
    restoreLoading.value = false
  }
}

const fetchAutoBackupConfig = async () => {
  try {
    const { data } = await api.get('/database/auto-backup/config')
    autoBackupConfig.value = {
      enabled: data.enabled || false,
      frequency: data.frequency || 'daily',
      keep_count: data.keep_count || 7,
    }
  } catch (error) {
    window.logger.error('获取自动备份配置失败:', error)
  }
}

const saveAutoBackupConfig = async () => {
  saveConfigLoading.value = true
  try {
    await api.post('/database/auto-backup/config', autoBackupConfig.value)
    ElMessage.success('自动备份配置已保存')
  } catch (error) {
    window.logger.error('保存自动备份配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    saveConfigLoading.value = false
  }
}

const triggerManualBackup = async () => {
  triggerLoading.value = true
  try {
    const { data } = await api.post('/database/auto-backup/trigger')
    ElMessage.success(`备份成功: ${data.filename}`)
    fetchBackupList()
  } catch (error) {
    window.logger.error('手动触发备份失败:', error)
    ElMessage.error(error.response?.data?.detail || '备份失败')
  } finally {
    triggerLoading.value = false
  }
}

const fetchBackupList = async () => {
  listLoading.value = true
  try {
    const { data } = await api.get('/database/auto-backup/list')
    backupList.value = data.backups || []
    backupDir.value = data.backup_dir || ''
  } catch (error) {
    window.logger.error('获取备份列表失败:', error)
  } finally {
    listLoading.value = false
  }
}

const downloadBackup = (filename) => {
  window.open(`/api/database/auto-backup/download/${filename}`, '_blank')
}

const deleteBackup = async (filename) => {
  try {
    await api.delete(`/database/auto-backup/${filename}`)
    ElMessage.success('已删除备份文件')
    fetchBackupList()
  } catch (error) {
    window.logger.error('删除备份文件失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

const formatTime = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleString('zh-CN')
}

onMounted(() => {
  if (hasFeature(FEATURES.DATABASE_MANAGEMENT)) {
    fetchAutoBackupConfig()
    fetchBackupList()
  }
})
</script>

<style scoped>
.database-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.no-auth-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}
</style>