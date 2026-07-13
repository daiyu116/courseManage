// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="daily-words-page">
    <el-card class="nav-card" style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/dashboard')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('dailyWords.dashboard') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="success" @click="goToPage('/admin/schedules')" style="width: 100%;height: 100%;">
            <el-icon><Calendar /></el-icon>
            {{ t('dailyWords.scheduleManagement') }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('dailyWords.title') }}</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('dailyWords.goBack') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('dailyWords.addDailyWord') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="filterGrade" :placeholder="t('dailyWords.grade')" clearable @change="fetchDailyWords" style="width: 150px;">
          <el-option v-for="grade in grades" :key="grade" :label="grade" :value="grade" />
        </el-select>
        <el-date-picker
          v-model="filterDateFrom"
          type="date"
          :placeholder="t('dailyWords.startDate')"
          value-format="YYYY-MM-DD"
          @change="fetchDailyWords"
        />
        <el-date-picker
          v-model="filterDateTo"
          type="date"
          :placeholder="t('dailyWords.endDate')"
          value-format="YYYY-MM-DD"
          @change="fetchDailyWords"
        />
        <el-button @click="resetFilters">{{ t('common.reset') }}</el-button>
      </div>

      <el-table :data="dailyWords" stripe v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="grade" :label="t('dailyWords.grade')" width="120" />
        <el-table-column prop="date" :label="t('dailyWords.date')" width="120" />
        <el-table-column :label="t('dailyWords.wordCount')" width="100">
          <template #default="{ row }">
            {{ row.words ? row.words.length : 0 }}
          </template>
        </el-table-column>
        <el-table-column :label="t('dailyWords.wordPreview')" min-width="300">
          <template #default="{ row }">
            <div v-if="row.words && row.words.length > 0">
              <el-tag v-for="(w, idx) in row.words.slice(0, 5)" :key="idx" size="small" style="margin: 2px;">
                {{ w.word }}
              </el-tag>
              <span v-if="row.words.length > 5" style="color: #909399; margin-left: 4px;">
                ...+{{ row.words.length - 5 }}
              </span>
            </div>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" :label="t('dailyWords.creator')" width="100" />
        <el-table-column :label="t('common.operation')" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showViewDialog(row)">{{ t('common.view') }}</el-button>
            <el-button size="small" type="primary" @click="showEditDialog(row)">{{ t('common.edit') }}</el-button>
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
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-card>

    <el-dialog v-model="addDialogVisible" :title="isEditing ? t('dailyWords.editDailyWord') : t('dailyWords.addDailyWord')" width="700px" draggable>
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item :label="t('dailyWords.grade')" prop="grade">
          <el-input v-model="form.grade" :placeholder="t('dailyWords.inputGrade')" />
        </el-form-item>
        <el-form-item :label="t('dailyWords.date')" prop="date">
          <el-date-picker v-model="form.date" type="date" :placeholder="t('dailyWords.selectDate')" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item :label="t('dailyWords.wordList')" prop="words">
          <div style="width: 100%;">
            <div v-for="(word, index) in form.words" :key="index" style="display: flex; gap: 8px; margin-bottom: 8px; align-items: center;">
              <el-input v-model="word.word" :placeholder="t('dailyWords.word')" style="flex: 1;" />
              <el-input v-model="word.phonetic" :placeholder="t('dailyWords.phonetic')" style="flex: 1;" />
              <el-input v-model="word.meaning" :placeholder="t('dailyWords.meaning')" style="flex: 1;" />
              <el-button type="danger" :icon="Delete" circle @click="removeWord(index)" />
            </div>
            <el-button type="primary" @click="addWord" style="width: 100%;">
              <el-icon><Plus /></el-icon>
              {{ t('dailyWords.addWord') }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDialogVisible" :title="t('dailyWords.wordDetail')" width="700px" draggable>
      <div v-if="currentDailyWord">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="t('dailyWords.grade')">{{ currentDailyWord.grade }}</el-descriptions-item>
          <el-descriptions-item :label="t('dailyWords.date')">{{ currentDailyWord.date }}</el-descriptions-item>
          <el-descriptions-item :label="t('dailyWords.creator')">{{ currentDailyWord.creator_name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="t('dailyWords.wordCount')">{{ currentDailyWord.words ? currentDailyWord.words.length : 0 }}</el-descriptions-item>
        </el-descriptions>
        <el-table v-if="currentDailyWord.words && currentDailyWord.words.length > 0" :data="currentDailyWord.words" border style="margin-top: 15px;">
          <el-table-column type="index" :label="t('dailyWords.index')" width="60" />
          <el-table-column prop="word" :label="t('dailyWords.word')" />
          <el-table-column prop="phonetic" :label="t('dailyWords.phonetic')" />
          <el-table-column prop="meaning" :label="t('dailyWords.meaning')" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Plus, Delete, Reading, Calendar } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()

const loading = ref(false)
const submitLoading = ref(false)
const dailyWords = ref([])
const grades = ref([])
const filterGrade = ref('')
const filterDateFrom = ref('')
const filterDateTo = ref('')
const pagination = ref({ currentPage: 1, pageSize: 15, total: 0 })

const addDialogVisible = ref(false)
const viewDialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const currentDailyWord = ref(null)
const formRef = ref(null)

const form = ref({
  grade: '',
  date: '',
  words: [{ word: '', phonetic: '', meaning: '' }],
})

const formRules = {
  grade: [{ required: true, message: t('dailyWords.validation.inputGrade'), trigger: 'blur' }],
  date: [{ required: true, message: t('dailyWords.validation.selectDate'), trigger: 'change' }],
  words: [{ required: true, message: t('dailyWords.validation.addAtLeastOneWord'), trigger: 'change' }],
}

const goToPage = (path) => {
  router.push(path)
}

const goBack = () => {
  router.back()
}

const fetchDailyWords = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize,
    }
    if (filterGrade.value) params.grade = filterGrade.value
    if (filterDateFrom.value) params.date_from = filterDateFrom.value
    if (filterDateTo.value) params.date_to = filterDateTo.value

    const response = await api.get('/daily-words', { params })
    dailyWords.value = response.data.items
    pagination.value.total = response.data.total
  } catch (error) {
    window.logger.error('获取每日单词失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchGrades = async () => {
  try {
    const response = await api.get('/daily-words/grades')
    grades.value = response.data
  } catch (error) {
    window.logger.error('获取年级列表失败:', error)
  }
}

const resetFilters = () => {
  filterGrade.value = ''
  filterDateFrom.value = ''
  filterDateTo.value = ''
  pagination.value.currentPage = 1
  fetchDailyWords()
}

const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchDailyWords()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchDailyWords()
}

const addWord = () => {
  form.value.words.push({ word: '', phonetic: '', meaning: '' })
}

const removeWord = (index) => {
  if (form.value.words.length > 1) {
    form.value.words.splice(index, 1)
  } else {
    ElMessage.warning(t('dailyWords.validation.atLeastOneWord'))
  }
}

const showAddDialog = () => {
  isEditing.value = false
  editingId.value = null
  form.value = {
    grade: '',
    date: '',
    words: [{ word: '', phonetic: '', meaning: '' }],
  }
  addDialogVisible.value = true
}

const showEditDialog = (row) => {
  isEditing.value = true
  editingId.value = row.id
  form.value = {
    grade: row.grade,
    date: row.date,
    words: row.words && row.words.length > 0
      ? row.words.map(w => ({ word: w.word || '', phonetic: w.phonetic || '', meaning: w.meaning || '' }))
      : [{ word: '', phonetic: '', meaning: '' }],
  }
  addDialogVisible.value = true
}

const showViewDialog = (row) => {
  currentDailyWord.value = row
  viewDialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    const validWords = form.value.words.filter(w => w.word.trim())
    if (validWords.length === 0) {
      ElMessage.warning(t('dailyWords.validation.addAtLeastOneWord'))
      return
    }

    try {
      submitLoading.value = true
      const data = {
        grade: form.value.grade,
        date: form.value.date,
        words: validWords,
      }

      if (isEditing.value) {
        await api.put(`/daily-words/${editingId.value}`, data)
        ElMessage.success(t('common.updateSuccess'))
      } else {
        await api.post('/daily-words', data)
        ElMessage.success(t('common.createSuccess'))
      }

      addDialogVisible.value = false
      fetchDailyWords()
      fetchGrades()
    } catch (error) {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error(t('common.operationFailed'))
      }
    } finally {
      submitLoading.value = false
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('common.confirmDelete'), t('common.tip'), { type: 'warning' })
    await api.delete(`/daily-words/${row.id}`)
    ElMessage.success(t('common.deleteSuccess'))
    fetchDailyWords()
    fetchGrades()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('common.operationFailed'))
    }
  }
}

onMounted(() => {
  fetchDailyWords()
  fetchGrades()
})
</script>

<style scoped>
.daily-words-page {
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
}
.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}
</style>