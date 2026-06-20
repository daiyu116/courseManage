// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="database-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('database.title') }}</span>
          <el-button @click="goBack">{{ t('common.back') }}</el-button>
        </div>
      </template>

      <div v-if="!hasFeature(FEATURES.DATABASE_MANAGEMENT)" class="no-auth-tip">
        <el-icon :size="48" color="#909399"><Lock /></el-icon>
        <p style="margin-top: 12px; color: #909399; font-size: 14px;">{{ t('database.noAuth') }}</p>
        <p style="color: #c0c4cc; font-size: 12px;">{{ t('database.noAuthTip') }}</p>
        <el-button type="primary" size="small" style="margin-top: 12px" @click="goToLicense">{{ t('database.goToLicense') }}</el-button>
      </div>

      <template v-else>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>{{ t('database.manualBackup') }}</span>
              </template>
              <el-button type="primary" @click="backupDatabase" :loading="backupLoading">
                <el-icon><Download /></el-icon>
                {{ t('database.backupDatabase') }}
              </el-button>
              <p style="margin-top: 20px; color: #666">
                {{ t('database.backupTip') }}
              </p>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                <span>{{ t('database.restore') }}</span>
              </template>
              <el-upload
                :auto-upload="false"
                :on-change="handleRestoreFileChange"
                :limit="1"
                accept=".csv,.sql"
              >
                <el-button type="warning">
                  <el-icon><Upload /></el-icon>
                  {{ t('database.selectBackupFile') }}
                </el-button>
              </el-upload>
              <el-button
                type="danger"
                @click="restoreDatabase"
                :loading="restoreLoading"
                :disabled="!restoreFile"
                style="margin-top: 10px"
              >
                {{ t('database.restoreDatabase') }}
              </el-button>
              <p style="margin-top: 20px; color: #666">
                {{ t('database.restoreWarning') }}
              </p>
            </el-card>
          </el-col>
        </el-row>

        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>{{ t('database.autoBackup') }}</span>
              <el-tag :type="autoBackupConfig.enabled ? 'success' : 'info'" size="small">
                {{ autoBackupConfig.enabled ? t('database.enabled') : t('database.notEnabled') }}
              </el-tag>
            </div>
          </template>

          <el-form :model="autoBackupConfig" label-width="120px" style="max-width: 500px">
            <el-form-item :label="t('database.enableAutoBackup')">
              <el-switch v-model="autoBackupConfig.enabled" />
            </el-form-item>
            <el-form-item :label="t('database.backupFrequency')">
              <el-select v-model="autoBackupConfig.frequency" style="width: 100%">
                <el-option :label="t('database.daily')" value="daily" />
                <el-option :label="t('database.every12Hours')" value="every_12_hours" />
                <el-option :label="t('database.every6Hours')" value="every_6_hours" />
                <el-option :label="t('database.weekly')" value="weekly" />
              </el-select>
            </el-form-item>
            <el-form-item :label="t('database.keepCount')">
              <el-input-number v-model="autoBackupConfig.keep_count" :min="1" :max="90" />
              <span style="margin-left: 8px; color: #909399; font-size: 12px">{{ t('database.keepCountTip') }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveAutoBackupConfig" :loading="saveConfigLoading">{{ t('database.saveConfig') }}</el-button>
              <el-button @click="triggerManualBackup" :loading="triggerLoading">{{ t('database.triggerBackup') }}</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div class="card-header" style="margin-bottom: 12px">
            <span>{{ t('database.backupFileList') }}</span>
            <el-button size="small" @click="fetchBackupList" :loading="listLoading">{{ t('common.refresh') }}</el-button>
          </div>

          <el-table :data="backupList" style="width: 100%" size="small" v-loading="listLoading" :empty-text="t('database.noBackupFiles')">
            <el-table-column prop="filename" :label="t('database.filename')" min-width="200" />
            <el-table-column prop="type" :label="t('database.fileType')" width="80">
              <template #default="{ row }">
                <el-tag :type="row.type === 'sql' ? 'success' : 'warning'" size="small">{{ row.type.toUpperCase() }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="size" :label="t('database.fileSize')" width="120">
              <template #default="{ row }">{{ formatSize(row.size) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" :label="t('database.createdAt')" width="180">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column :label="t('common.operation')" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="downloadBackup(row.filename)">{{ t('common.download') }}</el-button>
                <el-popconfirm :title="t('database.confirmDeleteBackup')" @confirm="deleteBackup(row.filename)">
                  <template #reference>
                    <el-button size="small" type="danger" link>{{ t('common.delete') }}</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>

          <p style="margin-top: 12px; color: #909399; font-size: 12px">
            {{ t('database.backupPath') }}{{ backupDir }}
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
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
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
    await ElMessageBox.confirm(t('database.confirmBackup'), t('database.confirmBackupTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
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
    ElMessage.success(t('database.backupSuccess'))
    fetchBackupList()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('备份失败:', error)
      ElMessage.error(t('database.backupFailed'))
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
      t('database.confirmRestore'),
      t('database.confirmRestoreTitle'),
      { confirmButtonText: t('database.confirmRestoreButton'), cancelButtonText: t('common.cancel'), type: 'error' }
    )
    restoreLoading.value = true
    const formData = new FormData()
    formData.append('file', restoreFile.value)
    await api.post('/database/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success(t('database.restoreSuccess'))
    setTimeout(() => { window.location.reload() }, 2000)
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('恢复失败:', error)
      ElMessage.error(error.response?.data?.detail || t('database.restoreFailed'))
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
    ElMessage.success(t('database.saveConfigSuccess'))
  } catch (error) {
    window.logger.error('保存自动备份配置失败:', error)
    ElMessage.error(error.response?.data?.detail || t('database.saveConfigFailed'))
  } finally {
    saveConfigLoading.value = false
  }
}

const triggerManualBackup = async () => {
  triggerLoading.value = true
  try {
    const { data } = await api.post('/database/auto-backup/trigger')
    ElMessage.success(t('database.triggerBackupSuccess', { filename: data.filename }))
    fetchBackupList()
  } catch (error) {
    window.logger.error('手动触发备份失败:', error)
    ElMessage.error(error.response?.data?.detail || t('database.triggerBackupFailed'))
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
    ElMessage.success(t('database.deleteBackupSuccess'))
    fetchBackupList()
  } catch (error) {
    window.logger.error('删除备份文件失败:', error)
    ElMessage.error(error.response?.data?.detail || t('common.operationFailed'))
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