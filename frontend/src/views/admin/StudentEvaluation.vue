// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="student-evaluation-page">
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
          <span>评价管理</span>
          <el-button type="info" @click="goBack" size="small">
            <el-icon><ArrowLeft /></el-icon>
            返回上一页
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="评价模板管理" name="templates">
          <div style="margin-bottom: 15px;">
            <el-button type="primary" @click="showAddTemplateDialog">新增模板</el-button>
            <el-button @click="showPresetDialog">从预设创建</el-button>
          </div>
          <el-table :data="templates" stripe>
            <el-table-column prop="template_name" label="模板名称" width="180" />
            <el-table-column prop="subject_type" label="学科类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ subjectTypeLabels[row.subject_type] || row.subject_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="course_name" label="关联科目" width="120">
              <template #default="{ row }">{{ row.course_name || '通用' }}</template>
            </el-table-column>
            <el-table-column label="维度数" width="80">
              <template #default="{ row }">{{ row.dimensions ? row.dimensions.length : 0 }}</template>
            </el-table-column>
            <el-table-column label="维度详情" min-width="200">
              <template #default="{ row }">
                <span v-for="(d, i) in (row.dimensions || [])" :key="i">
                  {{ d.name }}<span v-if="i < row.dimensions.length - 1">、</span>
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="editTemplate(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteTemplate(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="综合能力画像" name="comprehensive">
          <div class="search-bar">
            <el-select v-model="compFilters.student_id" placeholder="选择学员" clearable filterable style="width: 200px">
              <el-option v-for="s in students" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
            <el-select v-model="compFilters.profile_type" placeholder="画像类型" clearable style="width: 200px">
              <el-option label="学习态度/知识掌握/实践能力/创新思维/协作素养" value="academic" />
              <el-option label="德智体美劳" value="virtue" />
            </el-select>
            <el-select v-model="compFilters.eval_period" placeholder="评价周期" clearable style="width: 220px">
              <el-option v-for="p in evalPeriodOptions" :key="p" :label="p" :value="p" />
            </el-select>
            <el-button type="primary" @click="fetchComprehensiveEvals">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="resetCompFilters">重置</el-button>
            <el-button type="success" @click="showAddComprehensiveDialog">新增综合评价</el-button>
          </div>

          <el-row :gutter="20" v-if="compEvals.length > 0">
            <el-col :span="10">
              <el-card shadow="hover" style="margin-top: 20px;">
                <template #header>
                  <span>综合能力雷达图</span>
                </template>
                <div ref="compRadarChart" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
            <el-col :span="14">
              <el-table :data="compEvals" stripe style="margin-top: 20px;" @row-click="selectCompRow" highlight-current-row>
                <el-table-column prop="student_name" label="学员" width="100" />
                <el-table-column prop="eval_period" label="评价周期" width="150" />
                <el-table-column prop="profile_type" label="画像类型" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.profile_type === 'virtue' ? 'success' : 'primary'" size="small">
                      {{ row.profile_type === 'virtue' ? '德智体美劳' : '学知实创协' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="compDimensionLabels[0]" width="80">
                  <template #default="{ row }">{{ row.attitude_score }}</template>
                </el-table-column>
                <el-table-column :label="compDimensionLabels[1]" width="80">
                  <template #default="{ row }">{{ row.knowledge_score }}</template>
                </el-table-column>
                <el-table-column :label="compDimensionLabels[2]" width="80">
                  <template #default="{ row }">{{ row.practice_score }}</template>
                </el-table-column>
                <el-table-column :label="compDimensionLabels[3]" width="80">
                  <template #default="{ row }">{{ row.innovation_score }}</template>
                </el-table-column>
                <el-table-column :label="compDimensionLabels[4]" width="80">
                  <template #default="{ row }">{{ row.collaboration_score }}</template>
                </el-table-column>
                <el-table-column prop="evaluator_name" label="评价导师" width="100" />
                <el-table-column label="操作" width="160" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" @click="editComprehensiveEval(row)">编辑</el-button>
                    <el-button size="small" type="danger" @click="deleteComprehensiveEval(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div style="margin-top: 15px; display: flex; justify-content: center;">
                <el-pagination
                  v-model:current-page="compPagination.currentPage"
                  v-model:page-size="compPagination.pageSize"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="compPagination.total"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="fetchComprehensiveEvals"
                  @current-change="fetchComprehensiveEvals"
                />
              </div>
            </el-col>
          </el-row>
          <el-empty v-else description="暂无综合评价数据，点击新增综合评价开始评价" />
        </el-tab-pane>

        <el-tab-pane label="单科能力画像" name="subject">
          <div class="search-bar">
            <el-select v-model="subjFilters.student_id" placeholder="选择学员" clearable filterable style="width: 200px" @change="onSubjStudentChange">
              <el-option v-for="s in students" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
            <el-select v-model="subjFilters.course_id" placeholder="选择科目" clearable style="width: 200px">
              <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-select v-model="subjFilters.eval_period" placeholder="评价周期" clearable style="width: 220px">
              <el-option v-for="p in evalPeriodOptions" :key="p" :label="p" :value="p" />
            </el-select>
            <el-button type="primary" @click="fetchSubjectEvals">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="resetSubjFilters">重置</el-button>
            <el-button type="success" @click="showAddSubjectDialog">新增单科评价</el-button>
          </div>

          <el-row :gutter="20" v-if="subjEvals.length > 0">
            <el-col :span="10">
              <el-card shadow="hover" style="margin-top: 20px;">
                <template #header>
                  <span>单科能力雷达图</span>
                </template>
                <div ref="subjRadarChart" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
            <el-col :span="14">
              <el-table :data="subjEvals" stripe style="margin-top: 20px;" @row-click="selectSubjRow" highlight-current-row>
                <el-table-column prop="student_name" label="学员" width="100" />
                <el-table-column prop="course_name" label="科目" width="100" />
                <el-table-column prop="eval_period" label="评价周期" width="150" />
                <el-table-column prop="average_score" label="均分" width="70" />
                <el-table-column prop="strengths" label="优势" show-overflow-tooltip width="150" />
                <el-table-column prop="improvements" label="待提升" show-overflow-tooltip width="150" />
                <el-table-column prop="evaluator_name" label="评价导师" width="100" />
                <el-table-column label="操作" width="160" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" @click="editSubjectEval(row)">编辑</el-button>
                    <el-button size="small" type="danger" @click="deleteSubjectEval(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div style="margin-top: 15px; display: flex; justify-content: center;">
                <el-pagination
                  v-model:current-page="subjPagination.currentPage"
                  v-model:page-size="subjPagination.pageSize"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="subjPagination.total"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="fetchSubjectEvals"
                  @current-change="fetchSubjectEvals"
                />
              </div>
            </el-col>
          </el-row>
          <el-empty v-else description="暂无单科评价数据，点击新增单科评价开始评价" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新增/编辑综合评价弹窗 -->
    <el-dialog v-model="compDialogVisible" :title="compDialogTitle" width="650px" draggable>
      <el-form :model="compForm" :rules="compFormRules" ref="compFormRef" label-width="120px">
        <el-form-item label="学员" prop="student_id">
          <el-select v-model="compForm.student_id" placeholder="选择学员" filterable style="width: 100%" :disabled="compIsEdit" @change="onCompFormStudentChange">
            <el-option v-for="s in students" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="评价周期" prop="eval_period">
          <el-select v-model="compForm.eval_period" placeholder="请选择评价周期" filterable allow-create style="width: 100%">
            <el-option v-for="p in compFormEvalPeriodOptions" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="画像类型" prop="profile_type">
          <el-radio-group v-model="compForm.profile_type">
            <el-radio value="academic">学习态度/知识掌握/实践能力/创新思维/协作素养</el-radio>
            <el-radio value="virtue">德智体美劳</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-divider>{{ compForm.profile_type === 'virtue' ? '德智体美劳评分' : '五维能力评分' }}</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="compDimensionLabels[0]" prop="attitude_score">
              <el-slider v-model="compForm.attitude_score" :min="1" :max="5" :step="0.5" show-input input-size="small" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="compDimensionLabels[1]" prop="knowledge_score">
              <el-slider v-model="compForm.knowledge_score" :min="1" :max="5" :step="0.5" show-input input-size="small" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="compDimensionLabels[2]" prop="practice_score">
              <el-slider v-model="compForm.practice_score" :min="1" :max="5" :step="0.5" show-input input-size="small" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="compDimensionLabels[3]" prop="innovation_score">
              <el-slider v-model="compForm.innovation_score" :min="1" :max="5" :step="0.5" show-input input-size="small" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="compDimensionLabels[4]" prop="collaboration_score">
              <el-slider v-model="compForm.collaboration_score" :min="1" :max="5" :step="0.5" show-input input-size="small" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="评价导师">
          <el-select v-model="compForm.evaluator_id" placeholder="选择评价导师" clearable filterable style="width: 100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="综合评语">
          <el-input v-model="compForm.overall_comment" type="textarea" :rows="3" placeholder="请输入综合评语" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="compDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveComprehensiveEval">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑单科评价弹窗 -->
    <el-dialog v-model="subjDialogVisible" :title="subjDialogTitle" width="750px" draggable>
      <el-form :model="subjForm" :rules="subjFormRules" ref="subjFormRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学员" prop="student_id">
              <el-select v-model="subjForm.student_id" placeholder="选择学员" filterable style="width: 100%" :disabled="subjIsEdit" @change="onSubjFormStudentChange">
                <el-option v-for="s in students" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="科目" prop="course_id">
              <el-select v-model="subjForm.course_id" placeholder="选择科目" style="width: 100%" :disabled="subjIsEdit" @change="onCourseChange">
                <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="评价周期" prop="eval_period">
              <el-select v-model="subjForm.eval_period" placeholder="请选择评价周期" filterable allow-create style="width: 100%">
                <el-option v-for="p in subjFormEvalPeriodOptions" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="评价模板">
              <el-select v-model="subjForm.template_id" placeholder="选择评价模板" clearable style="width: 100%" @change="onTemplateChange">
                <el-option v-for="t in templates" :key="t.id" :label="t.template_name" :value="t.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider>各维度评分（1-5分）</el-divider>
        <div v-if="currentDimensions.length > 0">
          <el-row v-for="(dim, idx) in currentDimensions" :key="idx" :gutter="20" style="margin-bottom: 10px;">
            <el-col :span="6" style="text-align: right; line-height: 38px;">
              <el-tooltip :content="dim.description" placement="top" :disabled="!dim.description">
                <span>{{ dim.name }}：</span>
              </el-tooltip>
            </el-col>
            <el-col :span="18">
              <el-slider
                v-model="subjForm.dimension_scores[dim.name]"
                :min="1" :max="5" :step="0.5"
                show-input input-size="small"
              />
            </el-col>
          </el-row>
        </div>
        <el-empty v-else description="请先选择科目或评价模板" :image-size="60" />
        <el-form-item label="评价导师">
          <el-select v-model="subjForm.evaluator_id" placeholder="选择评价导师" clearable filterable style="width: 100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优势/亮点">
          <el-input v-model="subjForm.strengths" type="textarea" :rows="2" placeholder="请输入学员的优势与亮点" />
        </el-form-item>
        <el-form-item label="待提升方面">
          <el-input v-model="subjForm.improvements" type="textarea" :rows="2" placeholder="请输入学员待提升的方面" />
        </el-form-item>
        <el-form-item label="单科评语">
          <el-input v-model="subjForm.comment" type="textarea" :rows="3" placeholder="请输入单科评语" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subjDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSubjectEval">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑模板弹窗 -->
    <el-dialog v-model="templateFormDialogVisible" :title="templateFormTitle" width="700px" draggable>
      <el-form :model="templateForm" label-width="100px">
        <el-form-item label="模板名称">
          <el-input v-model="templateForm.template_name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="学科类型">
          <el-select v-model="templateForm.subject_type" placeholder="选择学科类型" style="width: 100%">
            <el-option v-for="(label, key) in subjectTypeLabels" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联科目">
          <el-select v-model="templateForm.course_id" placeholder="选择关联科目（可选）" clearable style="width: 100%">
            <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-divider>评价维度配置</el-divider>
        <div v-for="(dim, idx) in templateForm.dimensions" :key="idx" style="margin-bottom: 10px;">
          <el-row :gutter="10">
            <el-col :span="6">
              <el-input v-model="dim.name" placeholder="维度名称" />
            </el-col>
            <el-col :span="12">
              <el-input v-model="dim.description" placeholder="维度说明" />
            </el-col>
            <el-col :span="4">
              <el-input-number v-model="dim.weight" :min="0.1" :max="10" :step="0.1" size="default" style="width: 100%" />
            </el-col>
            <el-col :span="2">
              <el-button type="danger" :icon="Delete" circle @click="removeDimension(idx)" />
            </el-col>
          </el-row>
        </div>
        <el-button type="primary" link @click="addDimension">+ 添加维度</el-button>
      </el-form>
      <template #footer>
        <el-button @click="templateFormDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 预设模板弹窗 -->
    <el-dialog v-model="presetDialogVisible" title="从预设创建模板" width="600px" draggable>
      <el-row :gutter="20">
        <el-col :span="12" v-for="(preset, key) in presetOptions" :key="key" style="margin-bottom: 15px;">
          <el-card shadow="hover" @click="createFromPreset(key)" style="cursor: pointer;">
            <template #header><strong>{{ preset.name }}</strong></template>
            <div style="font-size: 12px; color: #606266;">
              <span v-for="(d, i) in preset.dimensions" :key="i">
                {{ d.name }}<span v-if="i < preset.dimensions.length - 1">、</span>
              </span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import api from '@/utils/api'
import * as echarts from 'echarts'
import { hasFeature } from '@/utils/license'

const router = useRouter()
const route = useRoute()
const goToPage = (path) => router.push(path)
const goBack = () => router.back()

const canAccessEvaluation = computed(() => {
  if (!hasFeature('student_evaluation')) return false
  const currentUser = JSON.parse(localStorage.getItem('user'))
  if (!currentUser) return false
  if (['super_admin', 'system_admin'].includes(currentUser.role)) return true
  const evaluationManagersStr = localStorage.getItem('evaluation_managers')
  if (evaluationManagersStr && currentUser.teacher_id) {
    try {
      const evaluationManagers = JSON.parse(evaluationManagersStr)
      if (Array.isArray(evaluationManagers) && evaluationManagers.includes(currentUser.teacher_id)) {
        return true
      }
    } catch (e) {}
  }
  return false
})

const activeTab = ref('comprehensive')
const students = ref([])
const courses = ref([])
const teachers = ref([])
const templates = ref([])
const presetOptions = ref({})

const defaultGradeOptions = [
  '小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
  '初中一年级', '初中二年级', '初中三年级',
  '高中一年级', '高中二年级', '高中三年级',
  '大学一年级', '大学二年级', '大学三年级', '大学四年级',
  '研究生一年级', '研究生二年级', '研究生三年级'
]
const gradeOptions = ref([...defaultGradeOptions])

const subjectTypeLabels = {
  language: '语言类',
  math: '数学类',
  science: '理科类',
  humanities: '文科类',
  art: '艺术类',
  sports: '体育类',
  custom: '自定义',
}

const compDimensionLabelsMap = {
  academic: ['学习态度', '知识掌握', '实践能力', '创新思维', '协作素养'],
  virtue: ['德', '智', '体', '美', '劳'],
}
const compDimensionLabels = computed(() => compDimensionLabelsMap[compForm.profile_type] || compDimensionLabelsMap.academic)

const getStudentGrade = (studentId) => {
  const s = students.value.find(s => s.id === studentId)
  return s ? (s.grade || '') : ''
}

const buildEvalPeriodOptions = (grade) => {
  if (grade) {
    return [`${grade}上学期（秋季）`, `${grade}下学期（春季）`]
  }
  const options = []
  for (const g of gradeOptions.value) {
    options.push(`${g}上学期（秋季）`)
    options.push(`${g}下学期（春季）`)
  }
  return options
}

const evalPeriodOptions = computed(() => {
  const compGrade = compFilters.student_id ? getStudentGrade(compFilters.student_id) : ''
  const subjGrade = subjFilters.student_id ? getStudentGrade(subjFilters.student_id) : ''
  const grade = compGrade || subjGrade
  return buildEvalPeriodOptions(grade)
})

const compFormEvalPeriodOptions = computed(() => {
  const grade = compForm.student_id ? getStudentGrade(compForm.student_id) : ''
  return buildEvalPeriodOptions(grade)
})

const subjFormEvalPeriodOptions = computed(() => {
  const grade = subjForm.student_id ? getStudentGrade(subjForm.student_id) : ''
  return buildEvalPeriodOptions(grade)
})

const compEvals = ref([])
const compFilters = reactive({ student_id: null, profile_type: null, eval_period: '' })
const compPagination = reactive({ currentPage: 1, pageSize: 10, total: 0 })
const compDialogVisible = ref(false)
const compDialogTitle = ref('新增综合评价')
const compIsEdit = ref(false)
const compEditId = ref(null)
const compFormRef = ref(null)
const compRadarChart = ref(null)
let compChartInstance = null

const compForm = reactive({
  student_id: null,
  eval_period: '',
  profile_type: 'academic',
  attitude_score: 3,
  knowledge_score: 3,
  practice_score: 3,
  innovation_score: 3,
  collaboration_score: 3,
  overall_comment: '',
  evaluator_id: null,
})

const compFormRules = {
  student_id: [{ required: true, message: '请选择学员', trigger: 'change' }],
  eval_period: [{ required: true, message: '请选择评价周期', trigger: 'change' }],
  profile_type: [{ required: true, message: '请选择画像类型', trigger: 'change' }],
}

const subjEvals = ref([])
const subjFilters = reactive({ student_id: null, course_id: null, eval_period: '' })
const subjPagination = reactive({ currentPage: 1, pageSize: 10, total: 0 })
const subjDialogVisible = ref(false)
const subjDialogTitle = ref('新增单科评价')
const subjIsEdit = ref(false)
const subjEditId = ref(null)
const subjFormRef = ref(null)
const subjRadarChart = ref(null)
let subjChartInstance = null

const currentDimensions = ref([])

const subjForm = reactive({
  student_id: null,
  course_id: null,
  template_id: null,
  eval_period: '',
  dimension_scores: {},
  comment: '',
  strengths: '',
  improvements: '',
  evaluator_id: null,
})

const subjFormRules = {
  student_id: [{ required: true, message: '请选择学员', trigger: 'change' }],
  course_id: [{ required: true, message: '请选择科目', trigger: 'change' }],
  eval_period: [{ required: true, message: '请选择评价周期', trigger: 'change' }],
}

const templateFormDialogVisible = ref(false)
const templateFormTitle = ref('新增评价模板')
const templateIsEdit = ref(false)
const templateEditId = ref(null)
const presetDialogVisible = ref(false)

const templateForm = reactive({
  template_name: '',
  subject_type: 'custom',
  course_id: null,
  dimensions: [{ name: '', description: '', weight: 1.0 }],
})

const fetchData = async () => {
  try {
    const [studentsRes, coursesRes, teachersRes, templatesRes, presetsRes, settingsRes] = await Promise.all([
      api.get('/students', { params: { skip: 0, limit: 10000 } }),
      api.get('/courses', { params: { skip: 0, limit: 10000 } }),
      api.get('/teachers', { params: { skip: 0, limit: 10000 } }),
      api.get('/evaluations/templates', { params: { skip: 0, limit: 1000 } }),
      api.get('/evaluations/presets'),
      api.get('/settings'),
    ])
    students.value = studentsRes.data.items || studentsRes.data
    courses.value = coursesRes.data.items || coursesRes.data
    teachers.value = (teachersRes.data.items || teachersRes.data).filter(t => t.is_active)
    templates.value = templatesRes.data.items || templatesRes.data
    presetOptions.value = presetsRes.data
    if (settingsRes.data && settingsRes.data.course_config) {
      try {
        const config = JSON.parse(settingsRes.data.course_config)
        if (config.grade_options && Array.isArray(config.grade_options) && config.grade_options.length > 0) {
          gradeOptions.value = config.grade_options
        }
      } catch (e) {}
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
  }
}

const fetchComprehensiveEvals = async () => {
  try {
    const params = {
      skip: (compPagination.currentPage - 1) * compPagination.pageSize,
      limit: compPagination.pageSize,
    }
    if (compFilters.student_id) params.student_id = compFilters.student_id
    if (compFilters.profile_type) params.profile_type = compFilters.profile_type
    if (compFilters.eval_period) params.eval_period = compFilters.eval_period
    const res = await api.get('/evaluations/comprehensive', { params })
    compEvals.value = res.data.items || []
    compPagination.total = res.data.total || 0
    if (compEvals.value.length > 0) {
      await nextTick()
      renderCompRadar(compEvals.value[0])
    }
  } catch (error) {
    if (error.response?.status !== 403) ElMessage.error('加载综合评价失败')
  }
}

const fetchSubjectEvals = async () => {
  try {
    const params = {
      skip: (subjPagination.currentPage - 1) * subjPagination.pageSize,
      limit: subjPagination.pageSize,
    }
    if (subjFilters.student_id) params.student_id = subjFilters.student_id
    if (subjFilters.course_id) params.course_id = subjFilters.course_id
    if (subjFilters.eval_period) params.eval_period = subjFilters.eval_period
    const res = await api.get('/evaluations/subject', { params })
    subjEvals.value = res.data.items || []
    subjPagination.total = res.data.total || 0
    if (subjEvals.value.length > 0) {
      await nextTick()
      renderSubjRadar(subjEvals.value[0])
    }
  } catch (error) {
    if (error.response?.status !== 403) ElMessage.error('加载单科评价失败')
  }
}

const renderCompRadar = (evalItem) => {
  if (!compRadarChart.value) return
  if (!compChartInstance) compChartInstance = echarts.init(compRadarChart.value)
  const labels = compDimensionLabelsMap[evalItem.profile_type] || compDimensionLabelsMap.academic
  const values = [evalItem.attitude_score, evalItem.knowledge_score, evalItem.practice_score, evalItem.innovation_score, evalItem.collaboration_score]
  compChartInstance.setOption({
    tooltip: {},
    radar: { indicator: labels.map(name => ({ name, max: 5 })), shape: 'polygon', splitNumber: 5 },
    series: [{ type: 'radar', data: [{ value: values, name: evalItem.student_name || '学员', areaStyle: { opacity: 0.2 }, lineStyle: { width: 2 } }] }],
  })
}

const renderSubjRadar = (evalItem) => {
  if (!subjRadarChart.value) return
  if (!subjChartInstance) subjChartInstance = echarts.init(subjRadarChart.value)
  const scores = evalItem.dimension_scores || {}
  const names = Object.keys(scores)
  const values = Object.values(scores)
  if (names.length === 0) return
  subjChartInstance.setOption({
    tooltip: {},
    radar: { indicator: names.map(name => ({ name, max: 5 })), shape: 'polygon', splitNumber: 5 },
    series: [{ type: 'radar', data: [{ value: values, name: `${evalItem.student_name || '学员'} - ${evalItem.course_name || ''}`, areaStyle: { opacity: 0.2 }, lineStyle: { width: 2 } }] }],
  })
}

const selectCompRow = (row) => renderCompRadar(row)
const selectSubjRow = (row) => renderSubjRadar(row)

const resetCompFilters = () => {
  compFilters.student_id = null
  compFilters.profile_type = null
  compFilters.eval_period = ''
  compPagination.currentPage = 1
  fetchComprehensiveEvals()
}

const resetSubjFilters = () => {
  subjFilters.student_id = null
  subjFilters.course_id = null
  subjFilters.eval_period = ''
  subjPagination.currentPage = 1
  fetchSubjectEvals()
}

const onSubjStudentChange = () => {
  subjFilters.eval_period = ''
}

const onCompFormStudentChange = () => {
  compForm.eval_period = ''
}

const onSubjFormStudentChange = () => {
  subjForm.eval_period = ''
}

const showAddComprehensiveDialog = () => {
  compIsEdit.value = false
  compEditId.value = null
  compDialogTitle.value = '新增综合评价'
  Object.assign(compForm, {
    student_id: null, eval_period: '', profile_type: 'academic',
    attitude_score: 3, knowledge_score: 3, practice_score: 3,
    innovation_score: 3, collaboration_score: 3,
    overall_comment: '', evaluator_id: null,
  })
  compDialogVisible.value = true
}

const editComprehensiveEval = (row) => {
  compIsEdit.value = true
  compEditId.value = row.id
  compDialogTitle.value = '编辑综合评价'
  Object.assign(compForm, {
    student_id: row.student_id,
    eval_period: row.eval_period,
    profile_type: row.profile_type,
    attitude_score: row.attitude_score,
    knowledge_score: row.knowledge_score,
    practice_score: row.practice_score,
    innovation_score: row.innovation_score,
    collaboration_score: row.collaboration_score,
    overall_comment: row.overall_comment || '',
    evaluator_id: row.evaluator_id,
  })
  compDialogVisible.value = true
}

const saveComprehensiveEval = async () => {
  try { await compFormRef.value.validate() } catch { return }
  try {
    if (compIsEdit.value) {
      await api.put(`/evaluations/comprehensive/${compEditId.value}`, compForm)
      ElMessage.success('更新成功')
    } else {
      await api.post('/evaluations/comprehensive', compForm)
      ElMessage.success('添加成功')
    }
    compDialogVisible.value = false
    fetchComprehensiveEvals()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

const deleteComprehensiveEval = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该综合评价记录？', '确认', { type: 'warning' })
    await api.delete(`/evaluations/comprehensive/${row.id}`)
    ElMessage.success('删除成功')
    fetchComprehensiveEvals()
  } catch {}
}

const onCourseChange = async (courseId) => {
  subjForm.template_id = null
  currentDimensions.value = []
  subjForm.dimension_scores = {}
  if (!courseId) return
  const matched = templates.value.filter(t => t.course_id === courseId && t.is_active)
  if (matched.length > 0) {
    subjForm.template_id = matched[0].id
    applyTemplate(matched[0])
  }
}

const onTemplateChange = (templateId) => {
  if (!templateId) {
    currentDimensions.value = []
    subjForm.dimension_scores = {}
    return
  }
  const t = templates.value.find(t => t.id === templateId)
  if (t) applyTemplate(t)
}

const applyTemplate = (template) => {
  const dims = template.dimensions || []
  currentDimensions.value = dims
  const newScores = {}
  dims.forEach(d => { newScores[d.name] = subjForm.dimension_scores[d.name] || 3 })
  subjForm.dimension_scores = newScores
}

const showAddSubjectDialog = () => {
  subjIsEdit.value = false
  subjEditId.value = null
  subjDialogTitle.value = '新增单科评价'
  Object.assign(subjForm, {
    student_id: null, course_id: null, template_id: null,
    eval_period: '', dimension_scores: {},
    comment: '', strengths: '', improvements: '', evaluator_id: null,
  })
  currentDimensions.value = []
  subjDialogVisible.value = true
}

const editSubjectEval = (row) => {
  subjIsEdit.value = true
  subjEditId.value = row.id
  subjDialogTitle.value = '编辑单科评价'
  Object.assign(subjForm, {
    student_id: row.student_id,
    course_id: row.course_id,
    template_id: row.template_id,
    eval_period: row.eval_period,
    dimension_scores: { ...row.dimension_scores },
    comment: row.comment || '',
    strengths: row.strengths || '',
    improvements: row.improvements || '',
    evaluator_id: row.evaluator_id,
  })
  if (row.template_id) {
    const t = templates.value.find(t => t.id === row.template_id)
    if (t) currentDimensions.value = t.dimensions || []
    else currentDimensions.value = Object.keys(row.dimension_scores || {}).map(name => ({ name, description: '', weight: 1.0 }))
  } else {
    currentDimensions.value = Object.keys(row.dimension_scores || {}).map(name => ({ name, description: '', weight: 1.0 }))
  }
  subjDialogVisible.value = true
}

const saveSubjectEval = async () => {
  try { await subjFormRef.value.validate() } catch { return }
  if (Object.keys(subjForm.dimension_scores).length === 0) {
    ElMessage.warning('请至少为一个维度评分')
    return
  }
  try {
    const payload = { ...subjForm }
    if (subjIsEdit.value) {
      await api.put(`/evaluations/subject/${subjEditId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/evaluations/subject', payload)
      ElMessage.success('添加成功')
    }
    subjDialogVisible.value = false
    fetchSubjectEvals()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

const deleteSubjectEval = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该单科评价记录？', '确认', { type: 'warning' })
    await api.delete(`/evaluations/subject/${row.id}`)
    ElMessage.success('删除成功')
    fetchSubjectEvals()
  } catch {}
}

const showAddTemplateDialog = () => {
  templateIsEdit.value = false
  templateEditId.value = null
  templateFormTitle.value = '新增评价模板'
  Object.assign(templateForm, {
    template_name: '', subject_type: 'custom',
    course_id: null, dimensions: [{ name: '', description: '', weight: 1.0 }],
  })
  templateFormDialogVisible.value = true
}

const editTemplate = (row) => {
  templateIsEdit.value = true
  templateEditId.value = row.id
  templateFormTitle.value = '编辑评价模板'
  Object.assign(templateForm, {
    template_name: row.template_name,
    subject_type: row.subject_type,
    course_id: row.course_id,
    dimensions: (row.dimensions || []).map(d => ({ ...d })),
  })
  templateFormDialogVisible.value = true
}

const saveTemplate = async () => {
  if (!templateForm.template_name) { ElMessage.warning('请输入模板名称'); return }
  const validDims = templateForm.dimensions.filter(d => d.name.trim())
  if (validDims.length === 0) { ElMessage.warning('请至少添加一个维度'); return }
  try {
    const payload = { ...templateForm, dimensions: validDims }
    if (templateIsEdit.value) {
      await api.put(`/evaluations/templates/${templateEditId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/evaluations/templates', payload)
      ElMessage.success('添加成功')
    }
    templateFormDialogVisible.value = false
    const res = await api.get('/evaluations/templates', { params: { skip: 0, limit: 1000 } })
    templates.value = res.data.items || []
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

const deleteTemplate = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该评价模板？', '确认', { type: 'warning' })
    await api.delete(`/evaluations/templates/${row.id}`)
    ElMessage.success('删除成功')
    const res = await api.get('/evaluations/templates', { params: { skip: 0, limit: 1000 } })
    templates.value = res.data.items || []
  } catch {}
}

const addDimension = () => {
  templateForm.dimensions.push({ name: '', description: '', weight: 1.0 })
}

const removeDimension = (idx) => {
  templateForm.dimensions.splice(idx, 1)
}

const showPresetDialog = () => {
  presetDialogVisible.value = true
}

const createFromPreset = (key) => {
  const preset = presetOptions.value[key]
  if (!preset) return
  templateIsEdit.value = false
  templateEditId.value = null
  templateFormTitle.value = '新增评价模板'
  Object.assign(templateForm, {
    template_name: preset.name + '评价模板',
    subject_type: key,
    course_id: null,
    dimensions: preset.dimensions.map(d => ({ ...d })),
  })
  presetDialogVisible.value = false
  templateFormDialogVisible.value = true
}

watch(compForm, () => {}, { deep: true })

onMounted(async () => {
  await fetchData()
  if (route.query.student_id) {
    const sid = parseInt(route.query.student_id)
    compFilters.student_id = sid
    subjFilters.student_id = sid
  }
  fetchComprehensiveEvals()
  fetchSubjectEvals()
})
</script>

<style scoped>
.student-evaluation-page {
  padding: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.search-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
.nav-card :deep(.el-card__body) {
  padding: 10px;
}
</style>