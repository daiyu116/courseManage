// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="grade-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('grade.title') }}</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('grade.goBack') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">{{ t('grade.addGradeButton') }}</el-button>
            <el-button type="success" @click="showBatchAddDialog">{{ t('grade.batchAddButtonShort') }}</el-button>
          </div>
        </div>
      </template>

      <!-- 查询条件 -->
      <div class="search-bar">
        <el-select v-model="filters.student_id" :placeholder="t('grade.selectStudent')" clearable filterable style="width: 200px">
          <el-option
            v-for="student in students"
            :key="student.id"
            :label="student.name"
            :value="student.id"
          >
            <el-tooltip placement="right" :show-after="200">
              <template #content>
                <div style="min-width: 200px;">
                  <div><strong>{{ t('grade.studentLabel') }}：</strong>{{ student.name }}</div>
                  <div v-if="student.school"><strong>{{ t('grade.schoolLabel') }}：</strong>{{ student.school }}</div>
                  <div v-if="student.grade"><strong>{{ t('grade.gradeLabel') }}：</strong>{{ student.grade }}</div>
                  <div v-if="student.classes && student.classes.length > 0">
                    <strong>{{ t('grade.classLabel') }}：</strong>
                    <div v-for="cls in student.classes" :key="cls.id" style="margin-left: 10px;">
                      {{ cls.name }}
                    </div>
                  </div>
                  <div v-else><strong>{{ t('grade.classLabel') }}：</strong>{{ t('grade.noClass') }}</div>
                  <div><strong>{{ t('grade.isActiveLabel') }}：</strong>{{ student.is_active ? t('grade.yes') : t('grade.no') }}</div>
                </div>
              </template>
              <span>{{ student.name }}</span>
            </el-tooltip>
          </el-option>
        </el-select>
        <el-select v-model="filters.course_id" :placeholder="t('grade.selectCourse')" clearable style="width: 200px">
          <el-option
            v-for="course in courses"
            :key="course.id"
            :label="course.name"
            :value="course.id"
          >
            <el-tooltip placement="right" :show-after="200">
              <template #content>
                <div style="min-width: 200px;">
                  <div><strong>{{ t('grade.course') }}：</strong>{{ course.name }}</div>
                  <div v-if="course.code"><strong>{{ t('grade.code') }}：</strong>{{ course.code }}</div>
                  <div v-if="course.teachers && course.teachers.length > 0">
                    <strong>{{ t('grade.teacherLabel') }}：</strong>
                    <div v-for="teacher in course.teachers" :key="teacher.id" style="margin-left: 10px;">
                      {{ teacher.name }}
                      <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                    </div>
                  </div>
                  <div v-else><strong>{{ t('grade.teacherLabel') }}：</strong>{{ t('grade.noClass') }}</div>
                </div>
              </template>
              <span>{{ course.name }}</span>
            </el-tooltip>
          </el-option>
        </el-select>
        <el-date-picker
          v-model="filters.date_range"
          type="daterange"
          :range-separator="t('grade.to')"
          :start-placeholder="t('grade.startDate')"
          :end-placeholder="t('grade.endDate')"
          value-format="YYYY-MM-DD"
          style="width: 300px"
        />
        <el-button @click="handleSearch">
          <el-icon><Search /></el-icon>
          {{ t('grade.search') }}
        </el-button>
        <el-button @click="resetFilters">{{ t('grade.reset') }}</el-button>
      </div>

      <!-- 成绩比例趋势图 -->
      <el-card v-if="filters.student_id && filters.course_id" style="margin-top: 20px;">
        <template #header>
          <span>{{ t('grade.scoreProportionTrend') }}</span>
        </template>
        <div ref="trendChart" style="width: 100%; height: 400px;"></div>
      </el-card>

      <!-- 成绩列表表格 -->
      <el-table :data="grades" stripe v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="student_name" :label="t('grade.student')" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light">
              <template #content>
                <div v-if="row.student_school">
                  <div><strong>{{ t('grade.schoolLabel') }}：</strong>{{ row.student_school }}</div>
                </div>
                <div v-if="row.student_grade">
                  <div><strong>{{ t('grade.gradeLabel') }}：</strong>{{ row.student_grade }}</div>
                </div>
                <div v-if="row.student_contact_person">
                  <div><strong>{{ t('grade.contactLabel') }}：</strong>{{ row.student_contact_person }}</div>
                </div>
                <div v-if="row.student_contact_phone">
                  <div><strong>{{ t('grade.contactPhoneLabel') }}：</strong>{{ row.student_contact_phone }}</div>
                </div>
                <div v-if="row.student_classes && row.student_classes.length > 0">
                  <div><strong>{{ t('grade.classLabel') }}：</strong></div>
                  <div v-for="class_ in row.student_classes" :key="class_.id" style="margin-left: 10px;">
                    {{ class_.name }}
                  </div>
                </div>
                <div v-else><strong>{{ t('grade.classLabel') }}：</strong>{{ t('grade.noClass') }}</div>
                <div>
                  <div><strong>{{ t('grade.isActiveLabel') }}：</strong>{{ row.student_is_active ? t('grade.reading') : t('grade.notReading') }}</div>
                </div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ row.student_name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="course_name" :label="t('grade.course')" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light">
              <template #content>
                <div v-if="row.course_teachers && row.course_teachers.length > 0">
                  <div><strong>{{ t('grade.teacherLabel') }}：</strong></div>
                  <div v-for="teacher in row.course_teachers" :key="teacher.id" style="margin-left: 10px;">
                    {{ teacher.name }}
                    <div v-if="teacher.contact_phone" style="margin-left: 10px; color: #909399;">
                      {{ t('grade.contactPhoneLabel') }}：{{ teacher.contact_phone }}
                    </div>
                    <div v-if="teacher.email" style="margin-left: 10px; color: #909399;">
                      {{ t('grade.emailLabel') }}：{{ teacher.email }}
                    </div>
                  </div>
                </div>
                <div v-else><strong>{{ t('grade.teacherLabel') }}：</strong>{{ t('grade.noClass') }}</div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ row.course_name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="grade_level" :label="t('grade.gradeLevel')" width="120" />
        <el-table-column prop="exam_stage" :label="t('grade.examStage')" width="120" />
        <el-table-column prop="exam_date" :label="t('grade.examDate')" width="120">
          <template #default="{ row }">
            {{ row.exam_date ? formatDate(row.exam_date) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="score" :label="t('grade.currentScore')" width="100">
          <template #default="{ row }">
            {{ row.score.toFixed(1) }}{{ t('grade.scoreUnit') }}
          </template>
        </el-table-column>
        <el-table-column prop="total_score" :label="t('grade.totalScoreLabel')" width="100">
          <template #default="{ row }">
            {{ row.total_score ? row.total_score.toFixed(1) + t('grade.scoreUnit') : '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="t('grade.scoreChange')" width="150">
          <template #default="{ row }">
            <span v-if="row.score_change > 0" style="color: #67c23a;">+{{ row.score_change.toFixed(1) }}{{ t('grade.scoreUnit') }}</span>
            <span v-else-if="row.score_change < 0" style="color: #f56c6c;">{{ row.score_change.toFixed(1) }}{{ t('grade.scoreUnit') }}</span>
            <span v-else style="color: #909399;">{{ t('grade.flat') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="t('grade.remark')" />
        <el-table-column :label="t('grade.action')" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">{{ t('grade.edit') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ t('grade.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 25, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item :label="t('grade.student')" prop="student_id">
          <el-select v-model="form.student_id" :placeholder="t('grade.selectStudent')" filterable style="width: 100%">
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="student.name"
              :value="student.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('grade.studentLabel') }}：</strong>{{ student.name }}</div>
                    <div v-if="student.school"><strong>{{ t('grade.schoolLabel') }}：</strong>{{ student.school }}</div>
                    <div v-if="student.grade"><strong>{{ t('grade.gradeLabel') }}：</strong>{{ student.grade }}</div>
                    <div v-if="student.classes && student.classes.length > 0">
                      <strong>{{ t('grade.classLabel') }}：</strong>
                      <div v-for="cls in student.classes" :key="cls.id" style="margin-left: 10px;">
                        {{ cls.name }}
                      </div>
                    </div>
                    <div v-else><strong>{{ t('grade.classLabel') }}：</strong>{{ t('grade.noClass') }}</div>
                    <div><strong>{{ t('grade.isActiveLabel') }}：</strong>{{ student.is_active ? t('grade.yes') : t('grade.no') }}</div>
                  </div>
                </template>
                <span>{{ student.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('grade.course')" prop="course_id">
          <el-select v-model="form.course_id" filterable :placeholder="t('grade.selectCourse')" style="width: 100%">
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('grade.course') }}：</strong>{{ course.name }}</div>
                    <div v-if="course.code"><strong>{{ t('grade.code') }}：</strong>{{ course.code }}</div>
                    <div v-if="course.teachers && course.teachers.length > 0">
                      <strong>{{ t('grade.teacherLabel') }}：</strong>
                      <div v-for="teacher in course.teachers" :key="teacher.id" style="margin-left: 10px;">
                        {{ teacher.name }}
                        <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                        <span v-if="teacher.email" style="color: #999; font-size: 12px;">（{{ teacher.email }}）</span>
                      </div>
                    </div>
                    <div v-else><strong>{{ t('grade.teacherLabel') }}：</strong>{{ t('grade.noClass') }}</div>
                  </div>
                </template>
                <span>{{ course.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('grade.gradeLabelShort')" prop="grade_level">
          <el-select v-model="form.grade_level" :placeholder="t('grade.selectGradeLevel')" style="width: 100%" @change="handleGradeLevelChange">
            <el-option
              v-for="grade in gradeOptions"
              :key="grade"
              :label="grade"
              :value="grade"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('grade.examStage')" prop="exam_stage">
          <el-select v-model="form.exam_stage" :placeholder="t('grade.selectExamStage')" style="width: 100%" @change="handleExamStageChange">
            <el-option
              v-for="stage in examStageOptions"
              :key="stage"
              :label="stage"
              :value="stage"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('grade.examDate')">
          <el-date-picker
            v-model="form.exam_date"
            type="date"
            :placeholder="t('grade.selectExamDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('grade.currentScore')" prop="score">
          <el-input-number v-model="form.score" :min="0" :precision="1" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('grade.totalScoreLabel')" prop="total_score">
          <el-input-number v-model="form.total_score" :min="0.1" :precision="1" style="width: 100%" :placeholder="t('grade.totalScorePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('grade.remark')">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="t('grade.remarkPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('grade.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ t('grade.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 批量添加成绩对话框 -->
    <el-dialog v-model="batchDialogVisible" :title="t('grade.batchAddTitle')" width="90%" top="5vh" draggable>
      <div style="margin-bottom: 15px;">
        <el-alert
          :title="t('grade.batchAddInfo')"
          type="info"
          :closable="false"
          show-icon
        >
          <p>1. {{ t('grade.batchAddStep1') }}</p>
          <p>2. {{ t('grade.batchAddStep2') }}</p>
          <p>3. {{ t('grade.batchAddStep3') }}</p>
          <p>4. {{ t('grade.batchAddStep4') }}</p>
        </el-alert>
      </div>
      
      <div style="max-height: 60vh; overflow-y: auto;">
        <el-table :data="batchForm.grades" border style="width: 100%">
          <el-table-column :label="t('grade.serialNumber')" width="60">
            <template #default="{ $index }">
              {{ $index + 1 }}
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.student')" min-width="90">
            <template #default="{ row, $index }">
              <el-select 
                v-model="row.student_id" 
                :placeholder="t('grade.selectStudent')" 
                filterable 
                style="width: 100%"
              >
                <el-option
                  v-for="student in students"
                  :key="student.id"
                  :label="student.name"
                  :value="student.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.course')" min-width="150">
            <template #default="{ row }">
              <el-select 
                v-model="row.course_id" 
                :placeholder="t('grade.selectCourse')" 
                filterable 
                style="width: 100%"
              >
                <el-option
                  v-for="course in courses"
                  :key="course.id"
                  :label="course.name"
                  :value="course.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.gradeLabelShort')" width="140">
            <template #default="{ row }">
              <el-select 
                v-model="row.grade_level" 
                :placeholder="t('grade.selectGradeLevel')" 
                style="width: 100%"
              >
                <el-option
                  v-for="grade in gradeOptions"
                  :key="grade"
                  :label="grade"
                  :value="grade"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.examStage')" width="140">
            <template #default="{ row }">
              <el-select 
                v-model="row.exam_stage" 
                :placeholder="t('grade.selectStageShort')" 
                style="width: 100%"
              >
                <el-option
                  v-for="stage in examStageOptions"
                  :key="stage"
                  :label="stage"
                  :value="stage"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.examDate')" width="160">
            <template #default="{ row }">
              <el-date-picker
                v-model="row.exam_date"
                type="date"
                :placeholder="t('grade.selectDateShort')"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.scoreShort')" width="130">
            <template #default="{ row }">
              <el-input-number 
                v-model="row.score" 
                :min="0" 
                :precision="1" 
                style="width: 100%" 
              />
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.totalScoreShort')" width="130">
            <template #default="{ row }">
              <el-input-number 
                v-model="row.total_score" 
                :min="0.1" 
                :precision="1" 
                style="width: 100%" 
              />
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.remark')" min-width="135">
            <template #default="{ row }">
              <el-input 
                v-model="row.description" 
                :placeholder="t('grade.optional')" 
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column :label="t('grade.action')" width="80" fixed="right">
            <template #default="{ $index }">
              <el-button 
                size="small" 
                type="danger" 
                @click="removeBatchRow($index)"
                :disabled="batchForm.grades.length <= 1"
              >
                {{ t('grade.deleteShort') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
        <el-button type="primary" plain @click="addBatchRow">
          <el-icon><Plus /></el-icon>
          {{ t('grade.addRow') }}
        </el-button>
        <span style="color: #909399;">{{ t('grade.totalRecords', { n: batchForm.grades.length }) }}</span>
      </div>
      
      <template #footer>
        <el-button @click="batchDialogVisible = false">{{ t('grade.cancel') }}</el-button>
        <el-button type="primary" @click="handleBatchSubmit" :loading="batchSubmitting">
          {{ t('grade.batchSubmit') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Search, Plus } from '@element-plus/icons-vue'
import api from '@/utils/api'
import * as echarts from 'echarts'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()

const grades = ref([])
const students = ref([])
const courses = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)
const loading = ref(false)
const batchDialogVisible = ref(false)
const batchSubmitting = ref(false)
const batchForm = ref({
  grades: []
})
const goBack = () => {
  router.back()
}
const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

// 添加分页处理函数
const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchGrades()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchGrades()
}

const handleSearch = () => {
  pagination.value.currentPage = 1
  fetchGrades()
}

const form = ref({
  id: null,
  student_id: null,
  course_id: null,
  exam_date: '',
  grade_level: '',
  exam_stage: '',
  score: 0,
  total_score: null,
  description: ''
})

const originalForm = ref({
  id: null,
  student_id: null,
  course_id: null,
  exam_date: '',
  grade_level: '',
  exam_stage: '',
  score: 0,
  total_score: null,
  description: ''
})

const filters = ref({
  student_id: null,
  course_id: null,
  date_range: []
})
const trendChart = ref(null)
let chartInstance = null
const defaultGradeOptions = [
  '小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
  '初中一年级', '初中二年级', '初中三年级',
  '高中一年级', '高中二年级', '高中三年级',
  '大学一年级', '大学二年级', '大学三年级', '大学四年级',
  '研究生一年级', '研究生二年级', '研究生三年级'
]
const gradeOptions = ref([...defaultGradeOptions])

const defaultExamStages = [
  '秋季月考A', '秋季月考B', '秋季期中', '秋季月考C', '秋季月考D', '秋季期末',
  '春季月考A', '春季月考B', '春季期中', '春季月考C', '春季月考D', '春季期末', 
  '中考一模', '中考二模', '中考三模', '中考', '会考', 
  '高考特训A', '高考特训B', '高考特训C', '春季高考',
  '高考一模', '高考二模', '高考三模', '夏季高考'
]
const examStageOptions = ref([...defaultExamStages])

const rules = {
  student_id: [{ required: true, message: t('grade.studentRequired'), trigger: 'change' }],
  course_id: [{ required: true, message: t('grade.courseRequired'), trigger: 'change' }],
  grade_level: [{ required: true, message: t('grade.gradeLevelRequired'), trigger: 'change' }],
  exam_stage: [{ required: true, message: t('grade.examStageRequired'), trigger: 'change' }],
  score: [{ required: true, message: t('grade.scoreRequired'), trigger: 'blur' }],
  total_score: [
    { required: true, message: t('grade.totalScoreRequired'), trigger: 'blur' },
    { validator: (rule, value, callback) => {
        if (value === null || value === undefined || value <= 0) {
          callback(new Error(t('grade.totalScoreGreaterThanZero')))
        } else {
          callback()
        }
      }, trigger: 'blur' }
  ]
}

const handleExamStageChange = (value) => {
  const zhongkaoStages = ['中考一模', '中考二模', '中考三模', '中考']
  const gaokaoStages = ['会考', '高考特训A', '高考特训B', '高考特训C', '春季高考', '高考一模',  '高考二模', '高考三模', '夏季高考']
  
  if (zhongkaoStages.includes(value)) {
    form.value.grade_level = '初中三年级'
  } else if (gaokaoStages.includes(value)) {
    form.value.grade_level = '高中三年级'
  }
}

const fetchStudents = async () => {
  try {
    const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    students.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
    ElMessage.error(t('grade.fetchStudentsFailed'))
  }
}

const fetchCourses = async () => {
  try {
    const response = await api.get('/courses', { params: { skip: 0, limit: 100000 } })
    courses.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取科目列表失败:', error)
    ElMessage.error(t('grade.fetchCoursesFailed'))
  }
}

const fetchGrades = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    if (filters.value.student_id) {
      params.student_id = filters.value.student_id
    }
    if (filters.value.course_id) {
      params.course_id = filters.value.course_id
    }
    if (filters.value.date_range && filters.value.date_range.length === 2) {
      params.start_date = filters.value.date_range[0]
      params.end_date = filters.value.date_range[1]
    }
    
    const response = await api.get('/grades', { params })
    grades.value = response.data.items
    pagination.value.total = response.data.total
    
    if (filters.value.student_id && filters.value.course_id) {
      await fetchGradeTrend()
    } else {
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
    }
  } catch (error) {
    window.logger.error('获取成绩列表失败:', error)
    ElMessage.error(t('grade.fetchGradesFailed'))
  } finally {
    loading.value = false
  }
}

const fetchGradeTrend = async () => {
  try {
    const params = {}
    if (filters.value.date_range && filters.value.date_range.length === 2) {
      params.start_date = filters.value.date_range[0]
      params.end_date = filters.value.date_range[1]
    }
    
    const response = await api.get(`/grades/trend/${filters.value.student_id}/${filters.value.course_id}`, { params })
    const trendData = response.data
    
    await nextTick()
    renderTrendChart(trendData)
  } catch (error) {
    window.logger.error('获取成绩趋势失败:', error)
    ElMessage.error(t('grade.fetchTrendFailed'))
  }
}

const renderTrendChart = (data) => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(trendChart.value)
  
  const option = {
    title: {
      text: t('grade.scoreProportionTrend'),
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const param = params[0]
        let html = `<strong>${param.name}</strong><br/>`
        
        const score = param.data.score !== null && param.data.score !== undefined ? param.data.score : 0
        const totalScore = param.data.total_score !== null && param.data.total_score !== undefined ? param.data.total_score : 0
        const ratio = param.data.ratio !== null && param.data.ratio !== undefined ? param.data.ratio : 0
        
        html += `${t('grade.currentExamScore')}: ${Number(score).toFixed(1)}${t('grade.scoreUnit')}<br/>`
        html += `${t('grade.currentTotalScore')}: ${Number(totalScore).toFixed(1)}${t('grade.scoreUnit')}<br/>`
        
        if (ratio !== null && ratio !== undefined) {
          html += `${t('grade.scoreRatio')}: ${Number(ratio).toFixed(1)}%<br/>`
        } else {
          html += `${t('grade.scoreRatioUncalculated')}<br/>`
        }
        
        html += `${t('grade.examDateLabel')}: ${param.name}<br/>`
        
        if (param.data.score_change !== null && param.data.score_change !== undefined) {
          if (param.data.score_change > 0) {
            html += `<span style="color: #67c23a;">${t('grade.comparedToLastTime')} +${param.data.score_change.toFixed(1)}${t('grade.scoreUnit')}</span>`
          } else if (param.data.score_change < 0) {
            html += `<span style="color: #f56c6c;">${t('grade.comparedToLastTime')} ${param.data.score_change.toFixed(1)}${t('grade.scoreUnit')}</span>`
          } else {
            html += `<span style="color: #909399;">${t('grade.comparedToLastTime')}${t('grade.flat')}</span>`
          }
        }
        return html
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date)
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: t('grade.scoreRatio'),
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [{
      data: data.map(item => ({
        value: item.ratio || 0,
        score: item.score,
        total_score: item.total_score,
        score_change: item.score_change
      })),
      type: 'line',
      smooth: true,
      markPoint: {
        data: [
          { type: 'max', name: t('grade.maxRatio') },
          { type: 'min', name: t('grade.minRatio') }
        ]
      },
      markLine: {
        data: [
          { type: 'average', name: t('grade.averageRatio') }
        ]
      }
    }]
  }
  
  chartInstance.setOption(option)
}

const showAddDialog = () => {
  dialogTitle.value = t('grade.addGradeTitle')
  
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
    id: null,
    student_id: prefillData?.student_id || null,
    course_id: prefillData?.course_id || null,
    exam_date: prefillData?.exam_date || '',
    grade_level: prefillData?.grade_level || '',
    exam_stage: prefillData?.exam_stage || '',
    score: prefillData?.score || 0,
    total_score: prefillData?.total_score || null,
    description: ''
  }
  dialogVisible.value = true
}

const showBatchAddDialog = () => {
  batchForm.value = {
    grades: [{
      student_id: null,
      course_id: null,
      exam_date: '',
      grade_level: '',
      exam_stage: '',
      score: 0,
      total_score: null,
      description: ''
    }]
  }
  batchDialogVisible.value = true
}

const addBatchRow = () => {
  batchForm.value.grades.push({
    student_id: null,
    course_id: null,
    exam_date: '',
    grade_level: '',
    exam_stage: '',
    score: 0,
    total_score: null,
    description: ''
  })
}

const removeBatchRow = (index) => {
  if (batchForm.value.grades.length > 1) {
    batchForm.value.grades.splice(index, 1)
  }
}

const handleBatchSubmit = async () => {
  // 验证所有行
  const invalidRows = []
  batchForm.value.grades.forEach((row, index) => {
    const errors = []
    if (!row.student_id) errors.push(t('grade.student'))
    if (!row.course_id) errors.push(t('grade.course'))
    if (!row.grade_level) errors.push(t('grade.gradeLabelShort'))
    if (!row.exam_stage) errors.push(t('grade.examStageShort'))
    if (row.score === null || row.score === undefined) errors.push(t('grade.scoreShort'))
    if (!row.total_score || row.total_score <= 0) errors.push(t('grade.totalScoreShort'))
    
    if (errors.length > 0) {
      invalidRows.push(`${t('grade.batchRow', { n: index + 1 })}${errors.join(t('grade.comma'))}`)
    }
  })
  
  if (invalidRows.length > 0) {
    ElMessage.error(t('grade.batchValidationFailed') + '\n' + invalidRows.join('\n'))
    return
  }
  
  batchSubmitting.value = true
  try {
    const gradesData = batchForm.value.grades.map(row => ({
      student_id: row.student_id,
      course_id: row.course_id,
      exam_date: row.exam_date ? new Date(row.exam_date).toISOString() : null,
      grade_level: row.grade_level,
      exam_stage: row.exam_stage,
      score: Number(row.score),
      total_score: Number(row.total_score),
      description: row.description || ''
    }))
    
    const response = await api.post('/grades/batch', { grades: gradesData })
    
    const { success_count, failed_count, errors } = response.data
    
    let message = t('grade.batchAddComplete', { success: success_count })
    if (failed_count > 0) {
      message += t('grade.batchAddWithFail', { fail: failed_count })
      if (errors && errors.length > 0) {
        message += '\n\n' + t('grade.failureDetails') + '\n' + errors.join('\n')
      }
    }
    
    if (success_count > 0) {
      ElMessage.success(message)
      batchDialogVisible.value = false
      fetchGrades()
    } else {
      ElMessage.error(message)
    }
  } catch (error) {
    window.logger.error('批量添加失败:', error)
    const errorMsg = error.response?.data?.detail || error.message
    ElMessage.error(t('grade.batchAddFailedMsg') + errorMsg)
  } finally {
    batchSubmitting.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = t('grade.editGradeTitle')
  const formData = {
    id: row.id,
    student_id: row.student_id,
    course_id: row.course_id,
    exam_date: row.exam_date ? row.exam_date.split('T')[0] : '',
    grade_level: row.grade_level || '',
    exam_stage: row.exam_stage || '',
    score: row.score,
    total_score: row.total_score,
    description: row.description || ''
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
        const formData = {
          student_id: form.value.student_id,
          course_id: form.value.course_id,
          exam_date: form.value.exam_date ? new Date(form.value.exam_date).toISOString() : null,
          grade_level: form.value.grade_level,
          exam_stage: form.value.exam_stage,
          score: Number(form.value.score),
          total_score: form.value.total_score ? Number(form.value.total_score) : null,
          description: form.value.description || ''
        }
        
        if (form.value.id) {
          const isChanged = 
            form.value.student_id !== originalForm.value.student_id ||
            form.value.course_id !== originalForm.value.course_id ||
            form.value.exam_date !== originalForm.value.exam_date ||
            form.value.grade_level !== originalForm.value.grade_level ||
            form.value.exam_stage !== originalForm.value.exam_stage ||
            form.value.score !== originalForm.value.score ||
            form.value.total_score !== originalForm.value.total_score ||
            form.value.description !== originalForm.value.description
          
          if (!isChanged) {
            ElMessage.warning(t('grade.noChange'))
            return
          }
          
          await api.put(`/grades/${form.value.id}`, formData)
          ElMessage.success(t('grade.updateSuccess'))
        } else {
          await api.post('/grades', formData)
          ElMessage.success(t('grade.addSuccess'))
        }
        
        dialogVisible.value = false
        fetchGrades()
      } catch (error) {
        window.logger.error('操作失败:', error)
        if (error.response && error.response.data && error.response.data.detail) {
          ElMessage.error(t('grade.operationFailed') + ': ' + JSON.stringify(error.response.data.detail))
        } else {
          ElMessage.error(t('grade.operationFailed'))
        }
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('grade.confirmDeleteMsg'), t('grade.confirmDeleteTitle'), {
    confirmButtonText: t('grade.confirm'),
    cancelButtonText: t('grade.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/grades/${row.id}`)
      ElMessage.success(t('grade.deleteSuccess'))
      fetchGrades()
    } catch (error) {
      window.logger.error('删除失败:', error)
      ElMessage.error(t('grade.deleteFailed'))
    }
  }).catch(() => {})
}

const resetFilters = () => {
  filters.value = {
    student_id: null,
    course_id: null,
    date_range: []
  }
  pagination.value.currentPage = 1
  fetchGrades()
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

watch(() => filters.value.student_id, () => {
  if (filters.value.student_id && filters.value.course_id) {
    fetchGradeTrend()
  }
})

watch(() => filters.value.course_id, () => {
  if (filters.value.student_id && filters.value.course_id) {
    fetchGradeTrend()
  }
})

onMounted(() => {
  // 从后端读取考试阶段配置
  api.get('/settings').then(res => {
    if (res.data && res.data.course_config) {
      try {
        const config = JSON.parse(res.data.course_config)
        if (config.grade_options && Array.isArray(config.grade_options) && config.grade_options.length > 0) {
          gradeOptions.value = config.grade_options
        }
        if (config.exam_stages && Array.isArray(config.exam_stages) && config.exam_stages.length > 0) {
          examStageOptions.value = config.exam_stages
        }
      } catch (e) {}
    }
  }).catch(() => {})

  // 检查是否有来自智能指令的搜索参数
  const urlParams = new URLSearchParams(window.location.search)
  const searchQuery = urlParams.get('search')
  const relatedTo = urlParams.get('related_to')
  
  fetchStudents()
  fetchCourses()
  fetchGrades()
  
  // 如果有搜索参数，自动填充并执行搜索
  if (searchQuery) {
    filters.value.student_name = searchQuery
    setTimeout(() => {
      fetchGrades()
      
      // 如果需要查看关联信息
      if (relatedTo && sessionStorage.getItem('smartCommandData')) {
        try {
          const smartData = JSON.parse(sessionStorage.getItem('smartCommandData'))
          if (smartData.target_path && smartData.target_label) {
            ElMessage.info(t('grade.foundStudentRecord', { name: searchQuery, target: smartData.target_label }))
            setTimeout(() => {
              window.location.href = `${smartData.target_path}?filter_by=student&filter_value=${encodeURIComponent(searchQuery)}`
            }, 1500)
          }
        } catch (e) {
          window.logger.error('解析智能指令数据失败', e)
        }
      }
    }, 500)
  }
  
  // 检查是否需要自动打开新增对话框
  if (route.query.action === 'add') {
    showAddDialog()
    
    // 如果URL中有student_id参数，预填充到表单
    if (route.query.student_id) {
      const studentId = parseInt(route.query.student_id)
      form.value.student_id = studentId
    }
  }
})

// 监听语言变化，刷新图表以更新翻译
watch(locale, () => {
  if (chartInstance && trendChart.value) {
    fetchTrendData()
  }
})

// 监听路由参数变化，支持从悬浮球等外部触发的操作
watch(() => route.query, (newQuery) => {
  if (newQuery.action === 'add') {
    showAddDialog()
    
    // 如果URL中有student_id参数，预填充到表单
    if (newQuery.student_id) {
      const studentId = parseInt(newQuery.student_id)
      form.value.student_id = studentId
    }
  }
}, { deep: true })
</script>

<style scoped>
.grade-management {
  padding: 6px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.search-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.el-card {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .search-bar {
    flex-direction: column;
  }
  
  .search-bar :deep(.el-select) {
    width: 100% !important;
  }
  
  .search-bar :deep(.el-date-editor) {
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