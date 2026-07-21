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
          <el-button type="primary" @click="goToPage('/admin/courses')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('dailyWords.courseManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="success" @click="goToPage('/admin/teachers')" style="width: 100%;height: 100%;">
            <el-icon><User /></el-icon>
            {{ t('dailyWords.teacherManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="warning" @click="goToPage('/admin/classes')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
            {{ t('dailyWords.classManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="warning" @click="goToPage('/admin/students')" style="width: 100%;height: 100%;">
            <el-icon><UserFilled /></el-icon>
            {{ t('dailyWords.studentManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="info" @click="goToPage('/admin/rooms')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
            {{ t('dailyWords.roomManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="danger" @click="goToPage('/admin/leaves')" style="width: 100%;height: 100%;">
            <el-icon><Calendar /></el-icon>
            {{ t('dailyWords.holidayManagement') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/conditions')" style="width: 100%;height: 100%;">
            <el-icon><Setting /></el-icon>
            {{ t('dailyWords.conditionManagement') }}
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
            <el-button type="warning" @click="showImportDialog">
              <el-icon><Upload /></el-icon>
              {{ t('dailyWords.importData') }}
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
        <el-table-column :label="t('common.operation')" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showViewDialog(row)">{{ t('common.view') }}</el-button>
            <el-button size="small" type="primary" @click="showEditDialog(row)">{{ t('common.edit') }}</el-button>
            <el-button size="small" type="success" @click="exportDocument(row)">{{ t('dailyWords.exportDoc') }}</el-button>
            <el-button size="small" type="warning" @click="printDocument(row)">{{ t('dailyWords.printDoc') }}</el-button>
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

    <el-dialog v-model="addDialogVisible" :title="isEditing ? t('dailyWords.editDailyWord') : t('dailyWords.addDailyWord')" width="90%" top="5vh" draggable>
      <div class="dialog-scroll-body">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item :label="t('dailyWords.grade')" prop="grade">
          <el-select v-model="form.grade" :placeholder="t('dailyWords.selectGrade')" clearable filterable allow-create style="width: 100%;">
            <el-option v-for="g in gradeOptions" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('dailyWords.date')" prop="date">
          <el-date-picker v-model="form.date" type="date" :placeholder="t('dailyWords.selectDate')" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item :label="t('dailyWords.wordList')" prop="words">
          <div style="width: 100%;">
            <div v-for="(word, index) in form.words" :key="index" class="word-phrase-row">
              <el-input v-model="word.word" :placeholder="t('dailyWords.word')" class="row-field-short" @blur="onWordBlur(index)" />
              <el-button type="info" :icon="Search" circle size="small" @click="fetchPhonetic(index)" :loading="word._phoneticLoading" :title="t('dailyWords.lookupPhonetic')" class="row-lookup-btn" />
              <el-select v-model="word.part_of_speech" :placeholder="t('dailyWords.selectPartOfSpeech')" clearable class="row-field-select">
                <el-option v-for="pos in partOfSpeechOptions" :key="pos.value" :label="pos.label" :value="pos.value" />
              </el-select>
              <el-input v-model="word.uk_phonetic" :placeholder="t('dailyWords.ukPhonetic')" class="row-field-short" />
              <el-input v-model="word.us_phonetic" :placeholder="t('dailyWords.usPhonetic')" class="row-field-short" />
              <el-input v-model="word.meaning" :placeholder="t('dailyWords.meaning')" class="row-field-main" />
              <el-select v-model="word.mastery_requirement" :placeholder="t('dailyWords.masteryRequirement')" clearable class="row-field-select">
                <el-option v-for="mr in masteryRequirementOptions" :key="mr.value" :label="mr.label" :value="mr.value" />
              </el-select>
              <el-input v-model="word.remark" :placeholder="t('dailyWords.remark')" class="row-field-remark" />
              <el-input v-model="word.link" :placeholder="t('dailyWords.link')" class="row-field-link" />
              <el-button type="danger" :icon="Delete" circle @click="removeWord(index)" class="row-delete-btn" />
            </div>
            <el-button type="primary" @click="addWord" style="width: 100%;">
              <el-icon><Plus /></el-icon>
              {{ t('dailyWords.addWord') }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item :label="t('dailyWords.phraseList')">
          <div style="width: 100%;">
            <div v-for="(phrase, index) in form.phrases" :key="'phrase-'+index" class="word-phrase-row">
              <el-input v-model="phrase.phrase" :placeholder="t('dailyWords.phraseContent')" class="row-field-main" />
              <el-select v-model="phrase.phrase_type" :placeholder="t('dailyWords.selectPhraseType')" clearable multiple collapse-tags class="row-field-select">
                <el-option v-for="pt in phraseTypeOptions" :key="pt.value" :label="pt.label" :value="pt.value" />
              </el-select>
              <el-select v-model="phrase.syntactic_role" :placeholder="t('dailyWords.selectSyntacticRole')" clearable multiple collapse-tags class="row-field-select">
                <el-option v-for="sr in syntacticRoleOptions" :key="sr.value" :label="sr.label" :value="sr.value" />
              </el-select>
              <el-input v-model="phrase.meaning" :placeholder="t('dailyWords.meaning')" class="row-field-main" />
              <el-select v-model="phrase.mastery_requirement" :placeholder="t('dailyWords.masteryRequirement')" clearable class="row-field-select">
                <el-option v-for="mr in masteryRequirementOptions" :key="mr.value" :label="mr.label" :value="mr.value" />
              </el-select>
              <el-input v-model="phrase.remark" :placeholder="t('dailyWords.remark')" class="row-field-remark" />
              <el-input v-model="phrase.link" :placeholder="t('dailyWords.link')" class="row-field-link" />
              <el-button type="danger" :icon="Delete" circle @click="removePhrase(index)" class="row-delete-btn" />
            </div>
            <el-button type="primary" @click="addPhrase" style="width: 100%;">
              <el-icon><Plus /></el-icon>
              {{ t('dailyWords.addPhrase') }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      </div>
      <template #footer>
        <el-button @click="addDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDialogVisible" :title="t('dailyWords.wordDetail')" width="95%" top="3vh" draggable>
      <div v-if="currentDailyWord">
        <div style="display: flex; justify-content: flex-end; margin-bottom: 10px; gap: 10px;">
          <el-button type="success" @click="exportDocument(currentDailyWord)">
            <el-icon><Download /></el-icon>
            {{ t('dailyWords.exportDoc') }}
          </el-button>
          <el-button type="warning" @click="printDocument(currentDailyWord)">
            <el-icon><Printer /></el-icon>
            {{ t('dailyWords.printDoc') }}
          </el-button>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="t('dailyWords.grade')">{{ currentDailyWord.grade }}</el-descriptions-item>
          <el-descriptions-item :label="t('dailyWords.date')">{{ currentDailyWord.date }}</el-descriptions-item>
          <el-descriptions-item :label="t('dailyWords.creator')">{{ currentDailyWord.creator_name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="t('dailyWords.wordCount')">{{ currentDailyWord.words ? currentDailyWord.words.length : 0 }}</el-descriptions-item>
        </el-descriptions>
        <el-table v-if="currentDailyWord.words && currentDailyWord.words.length > 0" :data="currentDailyWord.words" border style="margin-top: 15px;">
          <el-table-column type="index" :label="t('dailyWords.index')" width="60" />
          <el-table-column prop="word" :label="t('dailyWords.word')" />
          <el-table-column prop="part_of_speech" :label="t('dailyWords.partOfSpeech')" width="100">
            <template #default="{ row }">
              {{ getPartOfSpeechLabel(row.part_of_speech) }}
            </template>
          </el-table-column>
          <el-table-column prop="uk_phonetic" :label="t('dailyWords.ukPhonetic')" />
          <el-table-column prop="us_phonetic" :label="t('dailyWords.usPhonetic')" />
          <el-table-column prop="meaning" :label="t('dailyWords.meaning')" />
          <el-table-column prop="mastery_requirement" :label="t('dailyWords.masteryRequirement')" width="100">
            <template #default="{ row }">
              {{ getMasteryRequirementLabel(row.mastery_requirement) }}
            </template>
          </el-table-column>
          <el-table-column prop="remark" :label="t('dailyWords.remark')" />
          <el-table-column prop="link" :label="t('dailyWords.link')" width="120">
            <template #default="{ row }">
              <a v-if="row.link" :href="row.link" target="_blank" style="color: #409eff; text-decoration: underline;">{{ t('dailyWords.viewLink') }}</a>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
        <el-table v-if="currentDailyWord.phrases && currentDailyWord.phrases.length > 0" :data="currentDailyWord.phrases" border style="margin-top: 15px;">
          <el-table-column type="index" :label="t('dailyWords.index')" width="60" />
          <el-table-column prop="phrase" :label="t('dailyWords.phraseContent')" />
          <el-table-column prop="phrase_type" :label="t('dailyWords.phraseType')" width="120">
            <template #default="{ row }">
              {{ getPhraseTypeLabels(row.phrase_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="syntactic_role" :label="t('dailyWords.syntacticRole')" width="120">
            <template #default="{ row }">
              {{ getSyntacticRoleLabels(row.syntactic_role) }}
            </template>
          </el-table-column>
          <el-table-column prop="meaning" :label="t('dailyWords.meaning')" />
          <el-table-column prop="mastery_requirement" :label="t('dailyWords.masteryRequirement')" width="100">
            <template #default="{ row }">
              {{ getMasteryRequirementLabel(row.mastery_requirement) }}
            </template>
          </el-table-column>
          <el-table-column prop="remark" :label="t('dailyWords.remark')" />
          <el-table-column prop="link" :label="t('dailyWords.link')" width="120">
            <template #default="{ row }">
              <a v-if="row.link" :href="row.link" target="_blank" style="color: #409eff; text-decoration: underline;">{{ t('dailyWords.viewLink') }}</a>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" :title="t('dailyWords.importData')" width="600px" draggable>
      <el-form :model="importForm" ref="importFormRef" label-width="100px">
        <el-form-item :label="t('dailyWords.grade')" prop="grade">
          <el-select v-model="importForm.grade" :placeholder="t('dailyWords.selectGrade')" clearable filterable allow-create style="width: 100%;">
            <el-option v-for="g in gradeOptions" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('dailyWords.date')" prop="date">
          <el-date-picker v-model="importForm.date" type="date" :placeholder="t('dailyWords.selectDate')" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item :label="t('dailyWords.selectFile')">
          <div style="display: flex; gap: 10px; align-items: center;">
            <el-upload
              ref="importUploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls,.csv"
              :on-change="handleImportFileChange"
              :on-remove="handleImportFileRemove"
            >
              <el-button type="primary">{{ t('dailyWords.selectFileBtn') }}</el-button>
            </el-upload>
            <el-button type="success" @click="downloadImportTemplate">
              <el-icon><Download /></el-icon>
              {{ t('dailyWords.downloadTemplate') }}
            </el-button>
          </div>
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            {{ t('dailyWords.importFileTip') }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleImport" :loading="importLoading">{{ t('dailyWords.startImport') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Plus, Delete, Reading, Calendar, Download, Printer, Upload, User, UserFilled, OfficeBuilding, Setting, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { useI18n } from 'vue-i18n'
import * as XLSX from 'xlsx'

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
  words: [{ word: '', uk_phonetic: '', us_phonetic: '', meaning: '', part_of_speech: '', mastery_requirement: 'full_mastery', remark: '', link: '' }],
  phrases: [{ phrase: '', meaning: '', phrase_type: [], syntactic_role: [], mastery_requirement: 'full_mastery', remark: '', link: '' }],
})

const defaultGradeOptions = computed(() => [
  t('dailyWords.gradePrimary', { n: 1 }), t('dailyWords.gradePrimary', { n: 2 }), t('dailyWords.gradePrimary', { n: 3 }), t('dailyWords.gradePrimary', { n: 4 }), t('dailyWords.gradePrimary', { n: 5 }), t('dailyWords.gradePrimary', { n: 6 }),
  t('dailyWords.gradeJunior', { n: 1 }), t('dailyWords.gradeJunior', { n: 2 }), t('dailyWords.gradeJunior', { n: 3 }),
  t('dailyWords.gradeSenior', { n: 1 }), t('dailyWords.gradeSenior', { n: 2 }), t('dailyWords.gradeSenior', { n: 3 }),
  t('dailyWords.gradeCollege', { n: 1 }), t('dailyWords.gradeCollege', { n: 2 }), t('dailyWords.gradeCollege', { n: 3 }), t('dailyWords.gradeCollege', { n: 4 }),
  t('dailyWords.gradeGraduate', { n: 1 }), t('dailyWords.gradeGraduate', { n: 2 }), t('dailyWords.gradeGraduate', { n: 3 })
])
const gradeOptions = ref([])

watch(defaultGradeOptions, (newVal) => {
  gradeOptions.value = [...newVal]
}, { immediate: true })

const partOfSpeechOptions = computed(() => [
  { value: 'noun', label: t('dailyWords.noun') },
  { value: 'pronoun', label: t('dailyWords.pronoun') },
  { value: 'verb', label: t('dailyWords.verb') },
  { value: 'adjective', label: t('dailyWords.adjective') },
  { value: 'adverb', label: t('dailyWords.adverb') },
  { value: 'preposition', label: t('dailyWords.preposition') },
  { value: 'conjunction', label: t('dailyWords.conjunction') },
  { value: 'interjection', label: t('dailyWords.interjection') },
  { value: 'article', label: t('dailyWords.article') },
  { value: 'determiner', label: t('dailyWords.determiner') },
  { value: 'numeral', label: t('dailyWords.numeral') },
])

const getPartOfSpeechLabel = (value) => {
  const option = partOfSpeechOptions.value.find(o => o.value === value)
  return option ? option.label : (value || '-')
}

const masteryRequirementOptions = computed(() => [
  { value: 'full_mastery', label: t('dailyWords.fullMastery') },
  { value: 'use', label: t('dailyWords.use') },
])

const getMasteryRequirementLabel = (value) => {
  const option = masteryRequirementOptions.value.find(o => o.value === value)
  return option ? option.label : (value || '-')
}

const phraseTypeOptions = computed(() => [
  { value: 'prepositional_phrase', label: t('dailyWords.prepositionalPhrase') },
  { value: 'verb_phrase', label: t('dailyWords.verbPhrase') },
  { value: 'noun_phrase', label: t('dailyWords.nounPhrase') },
  { value: 'adjective_phrase', label: t('dailyWords.adjectivePhrase') },
  { value: 'adverb_phrase', label: t('dailyWords.adverbPhrase') },
  { value: 'infinitive_phrase', label: t('dailyWords.infinitivePhrase') },
  { value: 'gerund_phrase', label: t('dailyWords.gerundPhrase') },
  { value: 'participle_phrase', label: t('dailyWords.participlePhrase') },
  { value: 'conjunction_phrase', label: t('dailyWords.conjunctionPhrase') },
  { value: 'clause_phrase', label: t('dailyWords.clausePhrase') },
])

const getPhraseTypeLabel = (value) => {
  const option = phraseTypeOptions.value.find(o => o.value === value)
  return option ? option.label : (value || '-')
}

const getPhraseTypeLabels = (values) => {
  if (!values || !Array.isArray(values) || values.length === 0) return '-'
  return values.map(v => {
    const option = phraseTypeOptions.value.find(o => o.value === v)
    return option ? option.label : v
  }).join(t('common.listSeparator'))
}

const syntacticRoleOptions = computed(() => [
  { value: 'subject', label: t('dailyWords.subject') },
  { value: 'predicate', label: t('dailyWords.predicate') },
  { value: 'object', label: t('dailyWords.object') },
  { value: 'predicative', label: t('dailyWords.predicative') },
  { value: 'attributive', label: t('dailyWords.attributive') },
  { value: 'adverbial', label: t('dailyWords.adverbial') },
  { value: 'complement', label: t('dailyWords.complement') },
  { value: 'appositive', label: t('dailyWords.appositive') },
  { value: 'parenthetical', label: t('dailyWords.parenthetical') },
])

const getSyntacticRoleLabel = (value) => {
  const option = syntacticRoleOptions.value.find(o => o.value === value)
  return option ? option.label : (value || '-')
}

const getSyntacticRoleLabels = (values) => {
  if (!values || !Array.isArray(values) || values.length === 0) return '-'
  return values.map(v => {
    const option = syntacticRoleOptions.value.find(o => o.value === v)
    return option ? option.label : v
  }).join(t('common.listSeparator'))
}

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
  form.value.words.push({ word: '', uk_phonetic: '', us_phonetic: '', meaning: '', part_of_speech: '', mastery_requirement: 'full_mastery', remark: '', link: '', _phoneticLoading: false })
}

const removeWord = (index) => {
  if (form.value.words.length > 1) {
    form.value.words.splice(index, 1)
  } else {
    ElMessage.warning(t('dailyWords.validation.atLeastOneWord'))
  }
}

const addPhrase = () => {
  form.value.phrases.push({ phrase: '', meaning: '', phrase_type: [], syntactic_role: [], mastery_requirement: 'full_mastery', remark: '', link: '' })
}

const removePhrase = (index) => {
  form.value.phrases.splice(index, 1)
}

const showAddDialog = () => {
  isEditing.value = false
  editingId.value = null
  form.value = {
    grade: '',
    date: '',
    words: [{ word: '', uk_phonetic: '', us_phonetic: '', meaning: '', part_of_speech: '', mastery_requirement: 'full_mastery', remark: '', link: '', _phoneticLoading: false }],
    phrases: [{ phrase: '', meaning: '', phrase_type: [], syntactic_role: [], mastery_requirement: 'full_mastery', remark: '', link: '' }],
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
      ? row.words.map(w => ({ word: w.word || '', uk_phonetic: w.uk_phonetic || w.phonetic || '', us_phonetic: w.us_phonetic || '', meaning: w.meaning || '', part_of_speech: w.part_of_speech || '', mastery_requirement: w.mastery_requirement || 'full_mastery', remark: w.remark || '', link: w.link || '', _phoneticLoading: false }))
      : [{ word: '', uk_phonetic: '', us_phonetic: '', meaning: '', part_of_speech: '', mastery_requirement: 'full_mastery', remark: '', link: '', _phoneticLoading: false }],
    phrases: row.phrases && row.phrases.length > 0
      ? row.phrases.map(p => ({ phrase: p.phrase || '', meaning: p.meaning || '', phrase_type: Array.isArray(p.phrase_type) ? p.phrase_type : (p.phrase_type ? [p.phrase_type] : []), syntactic_role: Array.isArray(p.syntactic_role) ? p.syntactic_role : (p.syntactic_role ? [p.syntactic_role] : []), mastery_requirement: p.mastery_requirement || 'full_mastery', remark: p.remark || '', link: p.link || '' }))
      : [{ phrase: '', meaning: '', phrase_type: [], syntactic_role: [], mastery_requirement: 'full_mastery', remark: '', link: '' }],
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
    const validPhrases = form.value.phrases.filter(p => p.phrase.trim())
    if (validWords.length === 0 && validPhrases.length === 0) {
      ElMessage.warning(t('dailyWords.validation.addAtLeastOneWordOrPhrase'))
      return
    }

    for (let i = 0; i < validWords.length; i++) {
      const w = validWords[i]
      if (!w.word.trim()) {
        ElMessage.warning(t('dailyWords.validation.wordRequired', { n: i + 1 }))
        return
      }
      if (!w.part_of_speech) {
        ElMessage.warning(t('dailyWords.validation.partOfSpeechRequired', { n: i + 1 }))
        return
      }
      if (!w.uk_phonetic.trim()) {
        ElMessage.warning(t('dailyWords.validation.ukPhoneticRequired', { n: i + 1 }))
        return
      }
      if (!w.meaning.trim()) {
        ElMessage.warning(t('dailyWords.validation.meaningRequired', { n: i + 1 }))
        return
      }
      if (!w.mastery_requirement) {
        ElMessage.warning(t('dailyWords.validation.masteryRequired', { n: i + 1 }))
        return
      }
    }

    try {
      submitLoading.value = true
      const data = {
        grade: form.value.grade,
        date: form.value.date,
        words: validWords,
        phrases: validPhrases,
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

const exportDocument = (row) => {
  if (!row) return

  const dateStr = row.date || ''
  const dateParts = dateStr.split('-')
  const year = dateParts[0] || ''
  const month = dateParts[1] ? parseInt(dateParts[1]) : ''
  const day = dateParts[2] ? parseInt(dateParts[2]) : ''
  const title = `${year}年${month}月${day}日 单词和短语`

  const wb = XLSX.utils.book_new()
  const wsData = []

  wsData.push([title])
  wsData.push([])
  wsData.push([t('dailyWords.grade') + ':', row.grade || ''])
  wsData.push([t('dailyWords.date') + ':', row.date || ''])

  if (row.words && row.words.length > 0) {
    wsData.push([])
    wsData.push([t('dailyWords.wordList')])
    wsData.push([
      t('dailyWords.index'),
      t('dailyWords.word'),
      t('dailyWords.partOfSpeech'),
      t('dailyWords.ukPhonetic'),
      t('dailyWords.usPhonetic'),
      t('dailyWords.meaning'),
      t('dailyWords.masteryRequirement'),
      t('dailyWords.remark'),
    ])
    row.words.forEach((w, idx) => {
      wsData.push([
        idx + 1,
        w.word || '',
        getPartOfSpeechLabel(w.part_of_speech),
        w.uk_phonetic || w.phonetic || '',
        w.us_phonetic || '',
        w.meaning || '',
        getMasteryRequirementLabel(w.mastery_requirement),
        w.remark || '',
      ])
    })
  }

  if (row.phrases && row.phrases.length > 0) {
    wsData.push([])
    wsData.push([t('dailyWords.phraseList')])
    wsData.push([
      t('dailyWords.index'),
      t('dailyWords.phraseContent'),
      t('dailyWords.phraseType'),
      t('dailyWords.syntacticRole'),
      t('dailyWords.meaning'),
      t('dailyWords.masteryRequirement'),
      t('dailyWords.remark'),
    ])
    row.phrases.forEach((p, idx) => {
      wsData.push([
        idx + 1,
        p.phrase || '',
        getPhraseTypeLabels(p.phrase_type),
        getSyntacticRoleLabels(p.syntactic_role),
        p.meaning || '',
        getMasteryRequirementLabel(p.mastery_requirement),
        p.remark || '',
      ])
    })
  }

  const ws = XLSX.utils.aoa_to_sheet(wsData)

  const allCols = wsData.reduce((max, row) => Math.max(max, row.length), 0)
  const colWidths = []
  for (let i = 0; i < allCols; i++) {
    let maxLen = 8
    wsData.forEach(row => {
      if (row[i]) {
        const len = String(row[i]).length
        if (len > maxLen) maxLen = len
      }
    })
    colWidths.push({ wch: Math.min(maxLen + 4, 40) })
  }
  ws['!cols'] = colWidths

  if (wsData.length > 0 && wsData[0].length > 0) {
    const titleCell = ws['A1']
    if (titleCell) {
      titleCell.s = {
        font: { bold: true, sz: 16 },
        alignment: { horizontal: 'center' },
      }
    }
  }

  const mergeCount = Math.max(6, allCols)
  ws['!merges'] = [{ s: { r: 0, c: 0 }, e: { r: 0, c: mergeCount - 1 } }]

  XLSX.utils.book_append_sheet(wb, ws, t('dailyWords.wordAndPhrase'))

  const fileName = `${year}年${month}月${day}日_单词和短语.xlsx`
  XLSX.writeFile(wb, fileName)

  ElMessage.success(t('dailyWords.exportSuccess'))
}

const printDocument = (row) => {
  if (!row) return

  const dateStr = row.date || ''
  const dateParts = dateStr.split('-')
  const year = dateParts[0] || ''
  const month = dateParts[1] ? parseInt(dateParts[1]) : ''
  const day = dateParts[2] ? parseInt(dateParts[2]) : ''
  const title = `${year}年${month}月${day}日 单词和短语`

  let html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${title}</title>
  <style>
    body { font-family: "Microsoft YaHei", "SimHei", sans-serif; padding: 20px; }
    h1 { text-align: center; font-size: 22px; margin-bottom: 5px; }
    h2 { font-size: 16px; margin-top: 20px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    .info { text-align: center; color: #666; margin-bottom: 15px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th, td { border: 1px solid #333; padding: 6px 10px; text-align: center; font-size: 13px; }
    th { background: #f0f0f0; font-weight: bold; }
    td:nth-child(2), td:nth-child(5) { text-align: left; }
    @media print { body { padding: 0; } }
  </style></head><body>`

  html += `<h1>${title}</h1>`
  html += `<div class="info">${t('dailyWords.grade')}: ${row.grade || ''} &nbsp;&nbsp; ${t('dailyWords.date')}: ${row.date || ''}</div>`

  if (row.words && row.words.length > 0) {
    html += `<h2>${t('dailyWords.wordList')}</h2>`
    html += `<table><thead><tr>
      <th>${t('dailyWords.index')}</th>
      <th>${t('dailyWords.word')}</th>
      <th>${t('dailyWords.partOfSpeech')}</th>
      <th>${t('dailyWords.ukPhonetic')}</th>
      <th>${t('dailyWords.usPhonetic')}</th>
      <th>${t('dailyWords.meaning')}</th>
      <th>${t('dailyWords.masteryRequirement')}</th>
      <th>${t('dailyWords.remark')}</th>
    </tr></thead><tbody>`
    row.words.forEach((w, idx) => {
      html += `<tr>
        <td>${idx + 1}</td>
        <td>${w.word || ''}</td>
        <td>${getPartOfSpeechLabel(w.part_of_speech)}</td>
        <td>${w.uk_phonetic || w.phonetic || ''}</td>
        <td>${w.us_phonetic || ''}</td>
        <td>${w.meaning || ''}</td>
        <td>${getMasteryRequirementLabel(w.mastery_requirement)}</td>
        <td>${w.remark || ''}</td>
      </tr>`
    })
    html += `</tbody></table>`
  }

  if (row.phrases && row.phrases.length > 0) {
    html += `<h2>${t('dailyWords.phraseList')}</h2>`
    html += `<table><thead><tr>
      <th>${t('dailyWords.index')}</th>
      <th>${t('dailyWords.phraseContent')}</th>
      <th>${t('dailyWords.phraseType')}</th>
      <th>${t('dailyWords.syntacticRole')}</th>
      <th>${t('dailyWords.meaning')}</th>
      <th>${t('dailyWords.masteryRequirement')}</th>
      <th>${t('dailyWords.remark')}</th>
    </tr></thead><tbody>`
    row.phrases.forEach((p, idx) => {
      html += `<tr>
        <td>${idx + 1}</td>
        <td>${p.phrase || ''}</td>
        <td>${getPhraseTypeLabels(p.phrase_type)}</td>
        <td>${getSyntacticRoleLabels(p.syntactic_role)}</td>
        <td>${p.meaning || ''}</td>
        <td>${getMasteryRequirementLabel(p.mastery_requirement)}</td>
        <td>${p.remark || ''}</td>
      </tr>`
    })
    html += `</tbody></table>`
  }

  html += `</body></html>`

  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(html)
    printWindow.document.close()
    printWindow.focus()
    printWindow.print()
  } else {
    ElMessage.error(t('dailyWords.printFailed'))
  }
}

const importDialogVisible = ref(false)
const importLoading = ref(false)
const importFormRef = ref(null)
const importUploadRef = ref(null)
const importFileData = ref(null)
const importForm = ref({
  grade: '',
  date: '',
})

const showImportDialog = () => {
  importForm.value = { grade: '', date: '' }
  importFileData.value = null
  importDialogVisible.value = true
}

const handleImportFileChange = (file) => {
  importFileData.value = file.raw
}

const handleImportFileRemove = () => {
  importFileData.value = null
}

const handleImport = async () => {
  if (!importForm.value.grade) {
    ElMessage.warning(t('dailyWords.validation.inputGrade'))
    return
  }
  if (!importForm.value.date) {
    ElMessage.warning(t('dailyWords.validation.selectDate'))
    return
  }
  if (!importFileData.value) {
    ElMessage.warning(t('dailyWords.validation.selectFile'))
    return
  }

  importLoading.value = true
  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const workbook = XLSX.read(data, { type: 'array' })

        const words = []
        const phrases = []

        for (const sheetName of workbook.SheetNames) {
          const sheet = workbook.Sheets[sheetName]
          const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1 })

          let isWordSection = false
          let isPhraseSection = false

          for (const row of jsonData) {
            if (!row || row.length === 0) continue

            const firstCell = String(row[0] || '').trim()

            if (firstCell.includes(t('dailyWords.word')) && !firstCell.includes(t('dailyWords.phraseContent'))) {
              isWordSection = true
              isPhraseSection = false
              continue
            }
            if (firstCell.includes(t('dailyWords.phraseContent')) || firstCell.includes(t('dailyWords.phraseList'))) {
              isWordSection = false
              isPhraseSection = true
              continue
            }

            if (isWordSection && row[1]) {
              words.push({
                word: String(row[1] || '').trim(),
                part_of_speech: String(row[2] || '').trim(),
                uk_phonetic: String(row[3] || '').trim(),
                us_phonetic: String(row[4] || '').trim(),
                meaning: String(row[5] || '').trim(),
                mastery_requirement: String(row[6] || 'full_mastery').trim(),
                remark: String(row[7] || '').trim(),
                link: String(row[8] || '').trim(),
              })
            }

            if (isPhraseSection && row[1]) {
              let phraseTypeVal = String(row[2] || '').trim()
              let phraseTypeArr = []
              if (phraseTypeVal) {
                phraseTypeArr = phraseTypeVal.split(/[,，、]/).map(v => v.trim()).filter(v => v)
              }

              let syntacticRoleVal = String(row[3] || '').trim()
              let syntacticRoleArr = []
              if (syntacticRoleVal) {
                syntacticRoleArr = syntacticRoleVal.split(/[,，、]/).map(v => v.trim()).filter(v => v)
              }

              phrases.push({
                phrase: String(row[1] || '').trim(),
                phrase_type: phraseTypeArr,
                syntactic_role: syntacticRoleArr,
                meaning: String(row[4] || '').trim(),
                mastery_requirement: String(row[5] || 'full_mastery').trim(),
                remark: String(row[6] || '').trim(),
                link: String(row[7] || '').trim(),
              })
            }
          }
        }

        const validWords = words.filter(w => w.word)
        const validPhrases = phrases.filter(p => p.phrase)

        if (validWords.length === 0 && validPhrases.length === 0) {
          ElMessage.warning(t('dailyWords.validation.noDataInFile'))
          importLoading.value = false
          return
        }

        const payload = {
          grade: importForm.value.grade,
          date: importForm.value.date,
          words: validWords,
          phrases: validPhrases,
        }

        await api.post('/daily-words', payload)
        ElMessage.success(t('dailyWords.importSuccess'))
        importDialogVisible.value = false
        fetchDailyWords()
        fetchGrades()
      } catch (error) {
        window.logger.error('解析导入文件失败:', error)
        ElMessage.error(t('dailyWords.importParseFailed'))
      } finally {
        importLoading.value = false
      }
    }
    reader.onerror = () => {
      ElMessage.error(t('dailyWords.importParseFailed'))
      importLoading.value = false
    }
    reader.readAsArrayBuffer(importFileData.value)
  } catch (error) {
    window.logger.error('导入失败:', error)
    ElMessage.error(t('common.operationFailed'))
    importLoading.value = false
  }
}

const fetchPhonetic = async (index) => {
  const word = form.value.words[index]
  if (!word || !word.word.trim()) {
    ElMessage.warning(t('dailyWords.enterWordFirst'))
    return
  }

  word._phoneticLoading = true
  try {
    const response = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word.word.trim())}`)
    if (!response.ok) {
      ElMessage.warning(t('dailyWords.phoneticNotFound', { word: word.word.trim() }))
      return
    }
    const data = await response.json()
    if (!data || data.length === 0) {
      ElMessage.warning(t('dailyWords.phoneticNotFound', { word: word.word.trim() }))
      return
    }

    const entry = data[0]
    const phonetics = entry.phonetics || []

    const ukPhon = phonetics.find(p => p.text && p.text.includes('/'))
    let ukText = ukPhon ? ukPhon.text : (entry.phonetic || '')

    const usPhon = phonetics.slice(1).find(p => p.text && p.text !== ukText && p.text.includes('/'))
    let usText = usPhon ? usPhon.text : ''

    if (!usText && ukText) {
      usText = ukText
    }

    if (!ukText) {
      ElMessage.warning(t('dailyWords.phoneticNotFound', { word: word.word.trim() }))
      return
    }

    if (!word.uk_phonetic.trim()) {
      word.uk_phonetic = ukText
    }
    if (!word.us_phonetic.trim()) {
      word.us_phonetic = usText
    }

    if (!word.meaning.trim() && entry.meanings && entry.meanings.length > 0) {
      const firstMeaning = entry.meanings[0]
      if (firstMeaning.definitions && firstMeaning.definitions.length > 0) {
        word.meaning = firstMeaning.definitions[0].definition || ''
      }
    }

    if (!word.part_of_speech && entry.meanings && entry.meanings.length > 0) {
      const firstMeaning = entry.meanings[0]
      const pos = (firstMeaning.partOfSpeech || '').toLowerCase()
      const validPos = partOfSpeechOptions.value.find(o => o.value === pos)
      if (validPos) {
        word.part_of_speech = validPos.value
      }
    }

    ElMessage.success(t('dailyWords.phoneticFound'))
  } catch (error) {
    window.logger.error('查询音标失败:', error)
    ElMessage.error(t('dailyWords.phoneticQueryFailed'))
  } finally {
    word._phoneticLoading = false
  }
}

const onWordBlur = (index) => {
}

const downloadImportTemplate = () => {
  const wb = XLSX.utils.book_new()

  const wsData = []

  wsData.push([t('dailyWords.templateTitle')])
  wsData.push([t('dailyWords.templateNote')])
  wsData.push([])
  wsData.push([t('dailyWords.grade'), t('dailyWords.templateGradeExample')])
  wsData.push([t('dailyWords.date'), t('dailyWords.templateDateExample')])
  wsData.push([])
  wsData.push([t('dailyWords.wordList')])
  wsData.push([
    t('dailyWords.index'),
    t('dailyWords.word'),
    t('dailyWords.partOfSpeech'),
    t('dailyWords.ukPhonetic'),
    t('dailyWords.usPhonetic'),
    t('dailyWords.meaning'),
    t('dailyWords.masteryRequirement'),
    t('dailyWords.remark'),
    t('dailyWords.link'),
  ])
  wsData.push(['1', 'apple', 'noun', '/ˈæp.əl/', '/ˈæp.əl/', '苹果', 'full_mastery', '', ''])
  wsData.push(['2', 'run', 'verb', '/rʌn/', '/rʌn/', '跑步', 'use', '', ''])
  wsData.push([])
  wsData.push([t('dailyWords.phraseList')])
  wsData.push([
    t('dailyWords.index'),
    t('dailyWords.phraseContent'),
    t('dailyWords.phraseType'),
    t('dailyWords.syntacticRole'),
    t('dailyWords.meaning'),
    t('dailyWords.masteryRequirement'),
    t('dailyWords.remark'),
    t('dailyWords.link'),
  ])
  wsData.push(['1', 'take care of', 'verb_phrase', 'predicate', '照顾', 'full_mastery', '', ''])
  wsData.push(['2', 'a lot of', 'adjective_phrase', 'determiner', '许多', 'use', '', ''])

  const ws = XLSX.utils.aoa_to_sheet(wsData)

  ws['!cols'] = [
    { wch: 6 },
    { wch: 18 },
    { wch: 14 },
    { wch: 16 },
    { wch: 16 },
    { wch: 20 },
    { wch: 14 },
    { wch: 16 },
    { wch: 30 },
  ]

  XLSX.utils.book_append_sheet(wb, ws, t('dailyWords.importTemplate'))
  XLSX.writeFile(wb, `${t('dailyWords.importTemplate')}.xlsx`)
}

onMounted(() => {
  fetchDailyWords()
  fetchGrades()
  api.get('/settings').then(res => {
    if (res.data && res.data.course_config) {
      try {
        const config = JSON.parse(res.data.course_config)
        if (config.grade_options && Array.isArray(config.grade_options) && config.grade_options.length > 0) {
          gradeOptions.value = config.grade_options
        }
      } catch (e) {}
    }
  }).catch(() => {})
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
.dialog-scroll-body {
  max-height: 70vh;
  overflow: auto;
  padding-right: 4px;
}
.word-phrase-row {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  align-items: center;
  min-width: max-content;
}
.row-field-short {
  flex: 0 0 80px;
  min-width: 80px;
}
.row-field-main {
  flex: 1;
  min-width: 100px;
}
.row-field-select {
  flex: 0 0 140px;
  min-width: 140px;
}
.row-field-remark {
  flex: 0 0 120px;
  min-width: 120px;
}
.row-field-link {
  flex: 2;
  min-width: 180px;
}
.row-delete-btn {
  flex-shrink: 0;
}
.row-lookup-btn {
  flex-shrink: 0;
}
@media (max-width: 1200px) {
  .row-field-short {
    flex: 0 0 70px;
    min-width: 70px;
  }
  .row-field-select {
    flex: 0 0 120px;
    min-width: 120px;
  }
  .row-field-remark {
    flex: 0 0 100px;
    min-width: 100px;
  }
  .row-field-link {
    flex: 1.5;
    min-width: 140px;
  }
}
@media (max-width: 768px) {
  .dialog-scroll-body {
    max-height: 60vh;
  }
  .word-phrase-row {
    flex-wrap: wrap;
    min-width: unset;
  }
  .row-field-short,
  .row-field-main,
  .row-field-select,
  .row-field-remark,
  .row-field-link {
    flex: 1 1 120px;
    min-width: 120px;
  }
}
</style>