// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 CourseArrange Contributors
<template>
  <div class="grade-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>成绩管理</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回上一页
            </el-button>
            <el-button type="primary" @click="showAddDialog">添加成绩</el-button>
            <el-button type="success" @click="showBatchAddDialog">批量添加</el-button>
          </div>
        </div>
      </template>

      <!-- 查询条件 -->
      <div class="search-bar">
        <el-select v-model="filters.student_id" placeholder="选择学员" clearable filterable style="width: 200px">
          <el-option
            v-for="student in students"
            :key="student.id"
            :label="student.name"
            :value="student.id"
          >
            <el-tooltip placement="right" :show-after="200">
              <template #content>
                <div style="min-width: 200px;">
                  <div><strong>学员：</strong>{{ student.name }}</div>
                  <div v-if="student.school"><strong>学校：</strong>{{ student.school }}</div>
                  <div v-if="student.grade"><strong>年级：</strong>{{ student.grade }}</div>
                  <div v-if="student.classes && student.classes.length > 0">
                    <strong>本机构所属班级：</strong>
                    <div v-for="cls in student.classes" :key="cls.id" style="margin-left: 10px;">
                      {{ cls.name }}
                    </div>
                  </div>
                  <div v-else><strong>本机构所属班级：</strong>无</div>
                  <div><strong>是否在读：</strong>{{ student.is_active ? '是' : '否' }}</div>
                </div>
              </template>
              <span>{{ student.name }}</span>
            </el-tooltip>
          </el-option>
        </el-select>
        <el-select v-model="filters.course_id" placeholder="选择科目" clearable style="width: 200px">
          <el-option
            v-for="course in courses"
            :key="course.id"
            :label="course.name"
            :value="course.id"
          >
            <el-tooltip placement="right" :show-after="200">
              <template #content>
                <div style="min-width: 200px;">
                  <div><strong>科目：</strong>{{ course.name }}</div>
                  <div v-if="course.code"><strong>代码：</strong>{{ course.code }}</div>
                  <div v-if="course.teachers && course.teachers.length > 0">
                    <strong>教授导师：</strong>
                    <div v-for="teacher in course.teachers" :key="teacher.id" style="margin-left: 10px;">
                      {{ teacher.name }}
                      <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                    </div>
                  </div>
                  <div v-else><strong>教授导师：</strong>无</div>
                </div>
              </template>
              <span>{{ course.name }}</span>
            </el-tooltip>
          </el-option>
        </el-select>
        <el-date-picker
          v-model="filters.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 300px"
        />
        <el-button @click="handleSearch">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>

      <!-- 成绩比例趋势图 -->
      <el-card v-if="filters.student_id && filters.course_id" style="margin-top: 20px;">
        <template #header>
          <span>成绩比例趋势</span>
        </template>
        <div ref="trendChart" style="width: 100%; height: 400px;"></div>
      </el-card>

      <!-- 成绩列表表格 -->
      <el-table :data="grades" stripe v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="student_name" label="学员" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light">
              <template #content>
                <div v-if="row.student_school">
                  <div><strong>学校：</strong>{{ row.student_school }}</div>
                </div>
                <div v-if="row.student_grade">
                  <div><strong>年级：</strong>{{ row.student_grade }}</div>
                </div>
                <div v-if="row.student_contact_person">
                  <div><strong>联系人：</strong>{{ row.student_contact_person }}</div>
                </div>
                <div v-if="row.student_contact_phone">
                  <div><strong>联系电话：</strong>{{ row.student_contact_phone }}</div>
                </div>
                <div v-if="row.student_classes && row.student_classes.length > 0">
                  <div><strong>本机构所属班级：</strong></div>
                  <div v-for="class_ in row.student_classes" :key="class_.id" style="margin-left: 10px;">
                    {{ class_.name }}
                  </div>
                </div>
                <div v-else><strong>本机构所属班级：</strong>无</div>
                <div>
                  <div><strong>本机构是否在读：</strong>{{ row.student_is_active ? '在读' : '非在读' }}</div>
                </div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ row.student_name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="course_name" label="科目" width="120">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light">
              <template #content>
                <div v-if="row.course_teachers && row.course_teachers.length > 0">
                  <div><strong>教授导师：</strong></div>
                  <div v-for="teacher in row.course_teachers" :key="teacher.id" style="margin-left: 10px;">
                    {{ teacher.name }}
                    <div v-if="teacher.contact_phone" style="margin-left: 10px; color: #909399;">
                      联系电话：{{ teacher.contact_phone }}
                    </div>
                    <div v-if="teacher.email" style="margin-left: 10px; color: #909399;">
                      电子邮件：{{ teacher.email }}
                    </div>
                  </div>
                </div>
                <div v-else><strong>教授导师：</strong>无</div>
              </template>
              <span style="cursor: help; color: #409EFF;">{{ row.course_name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="grade_level" label="考试年级" width="120" />
        <el-table-column prop="exam_stage" label="考试阶段" width="120" />
        <el-table-column prop="exam_date" label="考试日期" width="120">
          <template #default="{ row }">
            {{ row.exam_date ? formatDate(row.exam_date) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="score" label="当次成绩" width="100">
          <template #default="{ row }">
            {{ row.score.toFixed(1) }}分
          </template>
        </el-table-column>
        <el-table-column prop="total_score" label="当次总分" width="100">
          <template #default="{ row }">
            {{ row.total_score ? row.total_score.toFixed(1) + '分' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="成绩变化" width="150">
          <template #default="{ row }">
            <span v-if="row.score_change > 0" style="color: #67c23a;">+{{ row.score_change.toFixed(1) }}分</span>
            <span v-else-if="row.score_change < 0" style="color: #f56c6c;">{{ row.score_change.toFixed(1) }}分</span>
            <span v-else style="color: #909399;">持平</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="备注" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
        <el-form-item label="学员" prop="student_id">
          <el-select v-model="form.student_id" placeholder="选择学员" filterable style="width: 100%">
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="student.name"
              :value="student.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>学员：</strong>{{ student.name }}</div>
                    <div v-if="student.school"><strong>学校：</strong>{{ student.school }}</div>
                    <div v-if="student.grade"><strong>年级：</strong>{{ student.grade }}</div>
                    <div v-if="student.classes && student.classes.length > 0">
                      <strong>本机构所属班级：</strong>
                      <div v-for="cls in student.classes" :key="cls.id" style="margin-left: 10px;">
                        {{ cls.name }}
                      </div>
                    </div>
                    <div v-else><strong>本机构所属班级：</strong>无</div>
                    <div><strong>是否在读：</strong>{{ student.is_active ? '是' : '否' }}</div>
                  </div>
                </template>
                <span>{{ student.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="科目" prop="course_id">
          <el-select v-model="form.course_id" filterable placeholder="选择科目" style="width: 100%">
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>科目：</strong>{{ course.name }}</div>
                    <div v-if="course.code"><strong>代码：</strong>{{ course.code }}</div>
                    <div v-if="course.teachers && course.teachers.length > 0">
                      <strong>教授导师：</strong>
                      <div v-for="teacher in course.teachers" :key="teacher.id" style="margin-left: 10px;">
                        {{ teacher.name }}
                        <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                        <span v-if="teacher.email" style="color: #999; font-size: 12px;">（{{ teacher.email }}）</span>
                      </div>
                    </div>
                    <div v-else><strong>教授导师：</strong>无</div>
                  </div>
                </template>
                <span>{{ course.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="年级" prop="grade_level">
          <el-select v-model="form.grade_level" placeholder="选择年级" style="width: 100%" @change="handleGradeLevelChange">
            <el-option
              v-for="grade in gradeOptions"
              :key="grade"
              :label="grade"
              :value="grade"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="考试阶段" prop="exam_stage">
          <el-select v-model="form.exam_stage" placeholder="选择考试阶段" style="width: 100%" @change="handleExamStageChange">
            <el-option
              v-for="stage in examStageOptions"
              :key="stage"
              :label="stage"
              :value="stage"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="考试日期">
          <el-date-picker
            v-model="form.exam_date"
            type="date"
            placeholder="选择考试日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="当次成绩" prop="score">
          <el-input-number v-model="form.score" :min="0" :precision="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="当次总分" prop="total_score">
          <el-input-number v-model="form.total_score" :min="0.1" :precision="1" style="width: 100%" placeholder="请输入当次科目总分（必填）" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量添加成绩对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量添加成绩" width="90%" top="5vh" draggable>
      <div style="margin-bottom: 15px;">
        <el-alert
          title="批量添加说明"
          type="info"
          :closable="false"
          show-icon
        >
          <p>1. 点击"添加行"按钮可以添加多条成绩记录</p>
          <p>2. 可以为不同学员、不同科目批量添加成绩</p>
          <p>3. 所有字段均为必填项</p>
          <p>4. 提交后将显示成功和失败的记录数</p>
        </el-alert>
      </div>
      
      <div style="max-height: 60vh; overflow-y: auto;">
        <el-table :data="batchForm.grades" border style="width: 100%">
          <el-table-column label="序号" width="60">
            <template #default="{ $index }">
              {{ $index + 1 }}
            </template>
          </el-table-column>
          <el-table-column label="学员" min-width="90">
            <template #default="{ row, $index }">
              <el-select 
                v-model="row.student_id" 
                placeholder="选择学员" 
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
          <el-table-column label="科目" min-width="150">
            <template #default="{ row }">
              <el-select 
                v-model="row.course_id" 
                placeholder="选择科目" 
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
          <el-table-column label="年级" width="140">
            <template #default="{ row }">
              <el-select 
                v-model="row.grade_level" 
                placeholder="选择年级" 
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
          <el-table-column label="考试阶段" width="140">
            <template #default="{ row }">
              <el-select 
                v-model="row.exam_stage" 
                placeholder="选择阶段" 
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
          <el-table-column label="考试日期" width="160">
            <template #default="{ row }">
              <el-date-picker
                v-model="row.exam_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </template>
          </el-table-column>
          <el-table-column label="成绩" width="130">
            <template #default="{ row }">
              <el-input-number 
                v-model="row.score" 
                :min="0" 
                :precision="1" 
                style="width: 100%" 
              />
            </template>
          </el-table-column>
          <el-table-column label="总分" width="130">
            <template #default="{ row }">
              <el-input-number 
                v-model="row.total_score" 
                :min="0.1" 
                :precision="1" 
                style="width: 100%" 
              />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="135">
            <template #default="{ row }">
              <el-input 
                v-model="row.description" 
                placeholder="选填" 
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ $index }">
              <el-button 
                size="small" 
                type="danger" 
                @click="removeBatchRow($index)"
                :disabled="batchForm.grades.length <= 1"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
        <el-button type="primary" plain @click="addBatchRow">
          <el-icon><Plus /></el-icon>
          添加行
        </el-button>
        <span style="color: #909399;">共 {{ batchForm.grades.length }} 条记录</span>
      </div>
      
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchSubmit" :loading="batchSubmitting">
          批量提交
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
  student_id: [{ required: true, message: '请选择学员', trigger: 'change' }],
  course_id: [{ required: true, message: '请选择科目', trigger: 'change' }],
  grade_level: [{ required: true, message: '请选择年级', trigger: 'change' }],
  exam_stage: [{ required: true, message: '请选择考试阶段', trigger: 'change' }],
  score: [{ required: true, message: '请输入成绩', trigger: 'blur' }],
  total_score: [
    { required: true, message: '请输入当次科目总分', trigger: 'blur' },
    { validator: (rule, value, callback) => {
        if (value === null || value === undefined || value <= 0) {
          callback(new Error('当次科目总分必须大于0'))
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
    ElMessage.error('获取学员列表失败')
  }
}

const fetchCourses = async () => {
  try {
    const response = await api.get('/courses', { params: { skip: 0, limit: 100000 } })
    courses.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取科目列表失败:', error)
    ElMessage.error('获取科目列表失败')
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
    ElMessage.error('获取成绩列表失败')
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
    ElMessage.error('获取成绩趋势失败')
  }
}

const renderTrendChart = (data) => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(trendChart.value)
  
  const option = {
    title: {
      text: '成绩比例趋势',
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
        
        html += `当次考试成绩: ${Number(score).toFixed(1)}分<br/>`
        html += `当次科目总分: ${Number(totalScore).toFixed(1)}分<br/>`
        
        if (ratio !== null && ratio !== undefined) {
          html += `成绩比例: ${Number(ratio).toFixed(1)}%<br/>`
        } else {
          html += `成绩比例: 未计算（总分可能为0）<br/>`
        }
        
        html += `考试日期: ${param.name}<br/>`
        
        if (param.data.score_change !== null && param.data.score_change !== undefined) {
          if (param.data.score_change > 0) {
            html += `<span style="color: #67c23a;">较上次 +${param.data.score_change.toFixed(1)}分</span>`
          } else if (param.data.score_change < 0) {
            html += `<span style="color: #f56c6c;">较上次 ${param.data.score_change.toFixed(1)}分</span>`
          } else {
            html += `<span style="color: #909399;">较上次持平</span>`
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
      name: '比例(%)',
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
          { type: 'max', name: '最高比例' },
          { type: 'min', name: '最低比例' }
        ]
      },
      markLine: {
        data: [
          { type: 'average', name: '平均比例' }
        ]
      }
    }]
  }
  
  chartInstance.setOption(option)
}

const showAddDialog = () => {
  dialogTitle.value = '添加成绩'
  
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
    if (!row.student_id) errors.push('学员')
    if (!row.course_id) errors.push('科目')
    if (!row.grade_level) errors.push('年级')
    if (!row.exam_stage) errors.push('考试阶段')
    if (row.score === null || row.score === undefined) errors.push('成绩')
    if (!row.total_score || row.total_score <= 0) errors.push('总分')
    
    if (errors.length > 0) {
      invalidRows.push(`第${index + 1}行缺少：${errors.join('、')}`)
    }
  })
  
  if (invalidRows.length > 0) {
    ElMessage.error('以下行数据不完整：\n' + invalidRows.join('\n'))
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
    
    let message = `批量添加完成！成功：${success_count}条`
    if (failed_count > 0) {
      message += `，失败：${failed_count}条`
      if (errors && errors.length > 0) {
        message += '\n\n失败详情：\n' + errors.join('\n')
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
    ElMessage.error('批量添加失败：' + errorMsg)
  } finally {
    batchSubmitting.value = false
  }
}

const showEditDialog = (row) => {
  dialogTitle.value = '编辑成绩'
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
            ElMessage.warning('内容未发生改变，无需保存')
            return
          }
          
          await api.put(`/grades/${form.value.id}`, formData)
          ElMessage.success('更新成功')
        } else {
          await api.post('/grades', formData)
          ElMessage.success('添加成功')
        }
        
        dialogVisible.value = false
        fetchGrades()
      } catch (error) {
        window.logger.error('操作失败:', error)
        if (error.response && error.response.data && error.response.data.detail) {
          ElMessage.error(`操作失败: ${JSON.stringify(error.response.data.detail)}`)
        } else {
          ElMessage.error('操作失败')
        }
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该成绩记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/grades/${row.id}`)
      ElMessage.success('删除成功')
      fetchGrades()
    } catch (error) {
      window.logger.error('删除失败:', error)
      ElMessage.error('删除失败')
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
            ElMessage.info(`已找到学员"${searchQuery}"的成绩记录，正在跳转到${smartData.target_label}...`)
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