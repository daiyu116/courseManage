// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="classes-page">
    <el-card class="nav-card" style="margin-bottom: 20px;">
      <el-row :gutter="20">
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/dashboard')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('nav.dashboard') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/courses')" style="width: 100%;height: 100%;">
            <el-icon><Reading /></el-icon>
            {{ t('nav.courses') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="success" @click="goToPage('/admin/teachers')" style="width: 100%;height: 100%;">
            <el-icon><User /></el-icon>
            {{ t('nav.teachers') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="info" @click="goToPage('/admin/students')" style="width: 100%;height: 100%;">
            <el-icon><UserFilled /></el-icon>
            {{ t('nav.students') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="info" @click="goToPage('/admin/rooms')" style="width: 100%;height: 100%;">
            <el-icon><OfficeBuilding /></el-icon>
            {{ t('nav.rooms') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="danger" @click="goToPage('/admin/leaves')" style="width: 100%;height: 100%;">
            <el-icon><Calendar /></el-icon>
            {{ t('nav.leaves') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/schedules')" style="width: 100%;height: 100%;">
            <el-icon><Clock /></el-icon>
            {{ t('nav.schedules') }}
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/conditions')" style="width: 100%;height: 100%;">
            <el-icon><Setting /></el-icon>
            {{ t('nav.conditions') }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('classes.title') }}</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('common.back') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              {{ t('classes.addClass') }}
            </el-button>
            <el-button type="success" @click="showBatchAddDialog">
              <el-icon><Upload /></el-icon>
              {{ t('common.batchAdd') }}
            </el-button>
          </div>
        </div>
      </template>
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          :placeholder="t('classes.searchPlaceholder')"
          style="width: 300px"
          clearable
          @clear="resetFilters"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
        <el-select v-model="isActiveFilter" :placeholder="t('classes.isActive')" clearable style="width: 150px" @change="handleFilterChange">
          <el-option :label="t('classes.enabled')" :value="true" />
          <el-option :label="t('classes.disabled')" :value="false" />
        </el-select>
        <el-button @click="resetFilters" style="width: 50px">{{ t('common.reset') }}</el-button>
      </div>
      <el-table 
        :data="classes" 
        stripe 
        v-loading="loading" 
        style="margin-top: 20px"
        :default-sort="{ prop: 'id', order: 'ascending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="id" label="ID" width="70" sortable />
        <el-table-column prop="code" :label="t('classes.classCode')" width="120" sortable />
        <el-table-column prop="name" :label="t('classes.className')" min-width="150">
          <template #default="{ row }">
            <el-popover placement="right" :width="300" trigger="hover">
              <template #reference>
                <span style="cursor: pointer;">{{ row.name }}</span>
              </template>
              <div>
                <div v-if="getActiveClassStudents(row.id).length > 0">
                  <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">{{ t('classes.activeStudents') }}</div>
                  <div v-for="student in getActiveClassStudents(row.id)" :key="student.id" style="margin-bottom: 4px;">
                    {{ student.name }}
                  </div>
                </div>
                <div v-if="getInactiveClassStudents(row.id).length > 0">
                  <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">{{ t('classes.inactiveStudents') }}</div>
                  <div v-for="student in getInactiveClassStudents(row.id)" :key="student.id" style="margin-bottom: 4px;">
                    {{ student.name }}
                  </div>
                </div>
                <div v-if="getActiveClassStudents(row.id).length === 0 && getInactiveClassStudents(row.id).length === 0">
                  {{ t('classes.noStudents') }}
                </div>
                <!-- 添加班级对应的导师信息 -->
                <div v-if="getClassTeachers(row.id).length > 0" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                  <div style="font-weight: bold; margin-bottom: 8px; color: #409EFF;">{{ t('classes.classTeachers') }}</div>
                  <div v-for="teacher in getClassTeachers(row.id)" :key="teacher.id" style="margin-bottom: 4px;">
                    {{ teacher.name }}
                    <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                  </div>
                </div>
                <div v-else style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                  <div style="color: #999;">{{ t('classes.noTeacher') }}</div>
                </div>
              </div>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="t('classes.classDescription')" min-width="150" sortable />
        <el-table-column :label="t('classes.webhookUrl')" min-width="300">
          <template #default="{ row }">
            <div style="display: flex; gap: 5px; align-items: center;">
              <el-input
                v-model="row.wechat_webhook"
                :placeholder="t('classes.webhookPlaceholder')"
                size="small"
                style="flex: 1"
                @change="handleWebhookChange(row)"
              />
              <el-button
                type="primary"
                size="small"
                :loading="testingWebhook === row.id"
                @click="testWebhook(row)"
              >
                {{ t('classes.testWebhook') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('classes.inactiveStudentCount')" width="150" sortable >
          <template #default="{ row }">
            {{ getStudentCount(row.id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('classes.activeStudentCount')" width="150" sortable >
          <template #default="{ row }">
            {{ getActiveStudentCount(row.id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('classes.isActive')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? t('classes.enabled') : t('classes.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.operation')" width="90" fixed="right">
            <template #default="{ row }">
                <el-button size="small" @click="showStudentsDialog(row)">{{ t('classes.viewStudents') }}</el-button>
                <el-button size="small" @click="showEditDialog(row)">{{ t('common.edit') }}</el-button>
                <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" size="small" type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" draggable>
        <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
            <el-form-item :label="t('classes.classCode')" prop="code">
              <el-input v-model="form.code" :placeholder="lastClassCode ? t('classes.classCodePlaceholderWithLast', { code: lastClassCode }) : t('classes.classCodePlaceholder')" :disabled="!!form.id" />
            </el-form-item>
            <el-form-item :label="t('classes.className')" prop="name">
              <el-input v-model="form.name" :placeholder="t('classes.classNamePlaceholder')" />
            </el-form-item>
            <el-form-item :label="t('classes.classDescription')" prop="description">
              <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="t('classes.classDescriptionPlaceholder')" />
            </el-form-item>
            <el-form-item :label="t('classes.selectStudents')" prop="student_ids">
              <el-select
                  v-model="selectedStudentIds"
                  multiple
                  filterable
                  value-key="id"
                  :placeholder="t('classes.selectStudentsPlaceholder')"
                  style="width: 100%"
              >
                  <el-option
                      v-for="student in availableStudents"
                      :key="student.id"
                      :label="`${student.code} - ${student.name}`"
                      :value="student.id"
                  >
                    <el-tooltip placement="right" :show-after="200">
                      <template #content>
                        <div style="min-width: 200px;">
                          <div><strong>{{ t('classes.studentLabel') }}</strong>{{ student.name }}</div>
                          <div v-if="student.code"><strong>{{ t('classes.codeLabel') }}</strong>{{ student.code }}</div>
                          <div v-if="student.school"><strong>{{ t('classes.schoolLabel') }}</strong>{{ student.school }}</div>
                          <div v-if="student.grade"><strong>{{ t('classes.gradeLabel') }}</strong>{{ student.grade }}</div>
                          <div v-if="student.contact_person"><strong>{{ t('classes.contactPersonLabel') }}</strong>{{ student.contact_person }}</div>
                          <div v-if="student.contact_phone"><strong>{{ t('classes.contactPhoneLabel') }}</strong>{{ student.contact_phone }}</div>
                          <div><strong>{{ t('classes.isActiveLabel') }}</strong>{{ student.is_active ? t('common.yes') : t('common.no') }}</div>
                        </div>
                      </template>
                      <span>{{ student.code }} - {{ student.name }}</span>
                    </el-tooltip>
                  </el-option>
              </el-select>
              <div style="margin-top: 5px; font-size: 12px; color: #909399;">
                  <el-icon><InfoFilled /></el-icon> {{ t('classes.editStudentTip') }}
              </div>
            </el-form-item>
            <el-form-item :label="t('classes.isActive')" prop="is_active">
              <el-switch v-model="form.is_active" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
            <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
        </template>
    </el-dialog>
    <!-- 学员列表对话框 -->
    <el-dialog v-model="studentsDialogVisible" :title="t('classes.studentListTitle')" width="800px" draggable>
        <div style="margin-bottom: 15px;">
            <el-button type="primary" size="small" @click="showAddStudentDialog">
            <el-icon><Plus /></el-icon>
            {{ t('classes.addStudent') }}
            </el-button>
            <el-button type="danger" size="small" @click="handleRemoveStudents">
            <el-icon><Delete /></el-icon>
            {{ t('classes.removeSelectedStudents') }}
            </el-button>
        </div>
        <el-table :data="classStudents" stripe @selection-change="handleSelectionChange" style="width: 100%">
            <el-table-column type="selection" width="55" />
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="code" :label="t('classes.studentCode')" width="120" />
            <el-table-column prop="name" :label="t('classes.studentName')" width="120" />
            <el-table-column prop="school" :label="t('classes.studentSchool')" min-width="150" />
            <el-table-column prop="grade" :label="t('classes.studentGrade')" width="100" />
            <el-table-column :label="t('classes.status')" width="80">
            <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? t('classes.activeStudent') : t('classes.inactiveStudent') }}
                </el-tag>
            </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <el-button @click="studentsDialogVisible = false">{{ t('common.close') }}</el-button>
        </template>
    </el-dialog>
    <el-dialog v-model="addStudentDialogVisible" :title="t('classes.addStudentToClass')" width="600px" draggable>
        <el-select
            v-model="selectedStudents"
            multiple
            filterable
            value-key="id"
            :placeholder="t('classes.selectStudentsPlaceholder')"
            style="width: 100%"
        >
            <el-option
                v-for="student in availableStudents"
                :key="student.id"
                :label="`${student.code} - ${student.name}`"
                :value="student"
            >
                <el-tooltip placement="right" :show-after="200">
                    <template #content>
                        <div style="min-width: 200px;">
                            <div><strong>{{ t('classes.studentLabel') }}</strong>{{ student.name }}</div>
                            <div v-if="student.code"><strong>{{ t('classes.codeLabel') }}</strong>{{ student.code }}</div>
                            <div v-if="student.school"><strong>{{ t('classes.schoolLabel') }}</strong>{{ student.school }}</div>
                            <div v-if="student.grade"><strong>{{ t('classes.gradeLabel') }}</strong>{{ student.grade }}</div>
                            <div v-if="student.contact_person"><strong>{{ t('classes.contactPersonLabel') }}</strong>{{ student.contact_person }}</div>
                            <div v-if="student.contact_phone"><strong>{{ t('classes.contactPhoneLabel') }}</strong>{{ student.contact_phone }}</div>
                            <div><strong>{{ t('classes.isActiveLabel') }}</strong>{{ student.is_active ? t('common.yes') : t('common.no') }}</div>
                        </div>
                    </template>
                    <span>{{ student.code }} - {{ student.name }}</span>
                </el-tooltip>
            </el-option>
        </el-select>
        <template #footer>
            <el-button @click="addStudentDialogVisible = false">{{ t('common.cancel') }}</el-button>
            <el-button type="primary" @click="handleAddStudents">{{ t('common.confirm') }}</el-button>
        </template>
    </el-dialog>
    <!-- 批量添加班级对话框 -->
    <el-dialog v-model="batchAddDialogVisible" :title="t('classes.batchAddTitle')" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          :title="t('classes.batchAddInfo')"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>{{ t('classes.batchAddFormat') }}</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              {{ t('classes.batchAddFormatLine') }}
            </div>
            <div style="margin-top: 10px;">{{ t('courses.batchAddExample') }}</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              CLASS001,{{ t('classes.batchAddExampleMath') }},{{ t('classes.batchAddExampleMathDesc') }},https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx<br/>
              CLASS002,{{ t('classes.batchAddExampleEnglish') }},{{ t('classes.batchAddExampleEnglishDesc') }},
            </div>
            <div style="margin-top: 10px;">{{ t('teachers.batchAddNote') }}</div>
            <ul style="margin-top: 5px;">
              <li>{{ t('classes.batchAddNoteCode') }}<span v-if="lastClassCode">{{ lastClassCode }}</span><span v-else>{{ t('teachers.batchAddNoteNone') }}</span>{{ t('teachers.batchAddNoteCodeContinue') }}</li>
            </ul>
          </template>
        </el-alert>
      </div>
      
      <el-form label-width="120px">
        <el-form-item :label="t('classes.batchAddClassInfo')">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            :placeholder="t('classes.batchAddPlaceholder')"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="batchAddDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleBatchAddSubmit" :loading="batchAddLoading">{{ t('common.batchAdd') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Delete, InfoFilled, Reading, User, UserFilled, OfficeBuilding, Calendar, Setting, Search, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const currentUser = ref(null)
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const classes = ref([])
const lastClassCode = ref('')
const testingWebhook = ref(null)  // 用于控制Webhook测试按钮的加载状态
const batchAddDialogVisible = ref(false)
const batchAddText = ref('')
const batchAddLoading = ref(false)
const goBack = () => {
  router.back()
}

const pagination = ref({
  currentPage: 1,
  pageSize: 25,
  total: 0
})

const sortField = ref('id')  // 排序字段
const sortOrder = ref('asc')  // 排序顺序
const searchKeyword = ref('')  // 搜索关键词
const isActiveFilter = ref(null)  // 是否启用过滤
const students = ref([])
const schedules = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)
const studentsDialogVisible = ref(false)
const addStudentDialogVisible = ref(false)
const classStudents = ref([])
const availableStudents = ref([])
const selectedStudentIds = ref([])
const selectedStudents = ref([])
const currentClass = ref(null)

// 添加分页处理函数
const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchClasses()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchClasses()
}

const handleSearch = () => {
  pagination.value.currentPage = 1
  fetchClasses()
}

const handleFilterChange = () => {
  pagination.value.currentPage = 1
  fetchClasses()
}

const showStudentsDialog = async (class_) => {
  currentClass.value = class_
  try {
    const response = await api.get('/students', { params: { class_id: class_.id, skip: 0, limit: 100000 } })
    classStudents.value = response.data.items || response.data
    studentsDialogVisible.value = true
  } catch (error) {
    window.logger.error('获取班级学员失败:', error)
    ElMessage.error(t('classes.fetchClassStudentsFailed'))
  }
}

const showAddStudentDialog = async () => {
  try {
    // 获取不属于任何班级或属于其他班级的学员
    const response = await api.get('/students', { params: { is_active: true, skip: 0, limit: 100000 } })
    availableStudents.value = (response.data.items || response.data).filter(s => !s.class_id || s.class_id !== currentClass.value.id)
    selectedStudentIds.value = []
    addStudentDialogVisible.value = true
  } catch (error) {
    window.logger.error('获取可用学员失败:', error)
    ElMessage.error(t('classes.fetchAvailableStudentsFailed'))
  }
}

const handleAddStudents = async () => {
  if (selectedStudents.value.length === 0) {
    ElMessage.warning(t('classes.selectStudentWarning'))
    return
  }

  try {
    await ElMessageBox.confirm(
      t('classes.confirmAddStudents', { count: selectedStudents.value.length, name: currentClass.value.name }),
      t('common.tip'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    // 批量更新学员的班级
    for (const student of selectedStudents.value) {
      // 获取学员当前的班级ID列表
      const currentClassIds = student.class_ids || []
      // 将新班级ID添加到列表中
      const newClassIds = [...currentClassIds, currentClass.value.id]
      await api.put(`/students/${student.id}`, { class_ids: newClassIds })
    }

    ElMessage.success(t('classes.addSuccess'))
    addStudentDialogVisible.value = false
    showStudentsDialog(currentClass.value) // 刷新学员列表
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('添加学员失败:', error)
      ElMessage.error(t('classes.addStudentFailed'))
    }
  }
}

const handleSelectionChange = (selection) => {
  selectedStudents.value = selection
}

const handleRemoveStudents = async () => {
  if (selectedStudents.value.length === 0) {
    ElMessage.warning(t('classes.selectRemoveStudentWarning'))
    return
  }

  try {
    await ElMessageBox.confirm(
      t('classes.confirmRemoveStudents', { count: selectedStudents.value.length, name: currentClass.value.name }),
      t('common.tip'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    // 批量更新学员的班级为 null
    for (const student of selectedStudents.value) {
      // 获取学员当前的班级ID列表
      const currentClassIds = student.class_ids || []
      // 从列表中移除当前班级ID
      const newClassIds = currentClassIds.filter(id => id !== currentClass.value.id)
      await api.put(`/students/${student.id}`, { class_ids: newClassIds })
    }

    ElMessage.success(t('classes.removeSuccess'))
    showStudentsDialog(currentClass.value) // 刷新学员列表
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('移除学员失败:', error)
      if (error.response) {
        window.logger.error('错误状态:', error.response.status)
        window.logger.error('错误详情:', error.response.data)
        ElMessage.error(t('classes.removeStudentFailed') + `: ${error.response.status} - ${JSON.stringify(error.response.data)}`)
      } else {
        ElMessage.error(t('classes.removeStudentFailedNetwork'))
      }
    }
  }
}

const form = ref({
  code: '',
  name: '',
  description: '',
  is_active: true
})

const originalForm = ref({
  code: '',
  name: '',
  description: '',
  is_active: true
})

const originalStudentIds = ref([])

const rules = {
  code: [{ required: true, message: t('classes.classCodeRequired'), trigger: 'blur' }],
  name: [{ required: true, message: t('classes.classNameRequired'), trigger: 'blur' }]
}

const fetchClasses = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (isActiveFilter.value !== null && isActiveFilter.value !== '') {
      params.is_active = isActiveFilter.value
    }
    // 添加排序参数
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    
    window.logger.log('DEBUG: fetchClasses - 请求参数:', params)
    const response = await api.get('/classes', { params })
    window.logger.log('DEBUG: fetchClasses - 响应数据:', response.data)
    classes.value = response.data.items
    pagination.value.total = response.data.total
    
    // 获取最后一个班级代码（按代码排序后的最后一个）
    if (response.data.items && response.data.items.length > 0) {
      const sortedByCode = [...response.data.items].sort((a, b) => a.code.localeCompare(b.code))
      lastClassCode.value = sortedByCode[sortedByCode.length - 1].code
    } else {
      lastClassCode.value = ''
    }
  } catch (error) {
    window.logger.error('获取班级列表失败:', error)
    window.logger.error('DEBUG: fetchClasses - 错误详情:', error.response?.data || error.message)
    ElMessage.error(t('classes.fetchClassesFailed'))
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  searchKeyword.value = ''
  isActiveFilter.value = null
  sortField.value = 'id'
  sortOrder.value = 'asc'
  pagination.value.currentPage = 1
  fetchClasses()
}

// 处理排序变化
const handleSortChange = ({ prop, order }) => {
  sortField.value = prop || 'id'
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  pagination.value.currentPage = 1
  fetchClasses()
}

const getClassTeachers = (classId) => {
  const classTeachers = []
  schedules.value.forEach(schedule => {
    if (schedule.class_id === classId && schedule.teacher) {
      const existing = classTeachers.find(t => t.id === schedule.teacher.id)
      if (!existing) {
        classTeachers.push(schedule.teacher)
      }
    }
  })
  return classTeachers
}

const fetchStudents = async () => {
  try {
    const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    students.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
  }
}

const fetchSchedules = async () => {
  try {
    const response = await api.get('/schedules')
    schedules.value = response.data.items || response.data  // 处理分页数据
  } catch (error) {
    window.logger.error('获取课程安排失败:', error)
  }
}

const getStudentCount = (classId) => {
  // 计算非在读学员数量
  return students.value.filter(s => {
    // 检查学生是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学生是否非在读
    const isInactive = !s.is_active
    return belongsToClass && isInactive
  }).length
}

const getActiveStudentCount = (classId) => {
  // 计算在读学员数量
  return students.value.filter(s => {
    // 检查学生是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学生是否在读
    const isActive = s.is_active
    return belongsToClass && isActive
  }).length
}

const getActiveClassStudents = (classId) => {
  // 获取某个班级的在读学员列表
  return students.value.filter(s => {
    // 检查学生是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学生是否在读
    const isActive = s.is_active
    return belongsToClass && isActive
  })
}
const getInactiveClassStudents = (classId) => {
  // 获取某个班级的非在读学员列表
  return students.value.filter(s => {
    // 检查学生是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学生是否非在读
    const isInactive = !s.is_active
    return belongsToClass && isInactive
  })
}

const fetchAvailableStudents = async () => {
  try {
    const response = await api.get('/students', { params: { is_active: true, skip: 0, limit: 100000 } })
    // 获取所有可用学员（包括已分配班级的学员）
    availableStudents.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取可用学员失败:', error)
  }
}

const showAddDialog = () => {
  dialogTitle.value = t('classes.addClass')
  
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
    code: '',
    name: prefillData?.class_name || '',
    description: '',
    is_active: true
  }
  selectedStudentIds.value = []
  fetchAvailableStudents()
  dialogVisible.value = true
}

const showBatchAddDialog = () => {
  batchAddText.value = ''
  batchAddDialogVisible.value = true
}
const handleBatchAddSubmit = async () => {
  if (!batchAddText.value.trim()) {
    ElMessage.warning(t('classes.batchAddWarning'))
    return
  }
  
  const lines = batchAddText.value.trim().split('\n')
  const classesToAdd = []
  const errors = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    const parts = line.split(',').map(p => p.trim())
    if (parts.length < 2) {
      errors.push(t('classes.batchAddLineError', { line: i + 1 }))
      continue
    }
    
    const class_ = {
      code: parts[0],
      name: parts[1],
      description: parts[2] || '',
      wechat_webhook: parts[3] || null,
      is_active: true
    }
    
    classesToAdd.push(class_)
  }
  
  if (errors.length > 0) {
    ElMessage.error(t('classes.batchAddErrorCount', { count: errors.length }) + '\n' + errors.join('\n'))
    if (classesToAdd.length === 0) {
      return
    }
  }
  
  if (classesToAdd.length === 0) {
    ElMessage.warning(t('classes.batchAddNoValid'))
    return
  }
  
  batchAddLoading.value = true
  try {
    let successCount = 0
    let failCount = 0
    const failMessages = []
    
    for (const class_ of classesToAdd) {
      try {
        await api.post('/classes', class_)
        successCount++
      } catch (error) {
        failCount++
        failMessages.push(`${class_.code}(${class_.name}): ${error.response?.data?.detail || error.message}`)
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(t('classes.batchAddPartial', { success: successCount, fail: failCount }) + '\n' + failMessages.join('\n'))
    } else {
      ElMessage.success(t('classes.batchAddSuccess', { n: successCount }))
    }
    
    batchAddDialogVisible.value = false
    await fetchClasses()
  } catch (error) {
    window.logger.error('批量添加班级失败:', error)
    ElMessage.error(t('classes.batchAddFailed'))
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = async (row) => {
  dialogTitle.value = t('classes.editClass')
  form.value = {
    id: row.id,
    code: row.code,
    name: row.name,
    description: row.description,
    is_active: row.is_active
  }
  originalForm.value = {
    id: row.id,
    code: row.code,
    name: row.name,
    description: row.description,
    is_active: row.is_active
  }
  // 加载当前班级的学员 - 使用更可靠的查询方式
  try {
    const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    const allStudents = response.data.items || response.data
    // 过滤出属于当前班级的学员
    selectedStudentIds.value = allStudents
      .filter(s => s.class_ids && s.class_ids.includes(row.id))
      .map(s => s.id)
    selectedStudents.value = allStudents.filter(s => s.class_ids && s.class_ids.includes(row.id))
    originalStudentIds.value = [...selectedStudentIds.value]
  } catch (error) {
    window.logger.error('获取班级学员失败:', error)
    selectedStudentIds.value = []
    selectedStudents.value = []
    originalStudentIds.value = []
  }
  
  // 加载可用学员（所有学员）
  await fetchAvailableStudents()
  
  // 如果有预填充的更新数据，应用到表单
  const storageData = sessionStorage.getItem('smartCommandData')
  if (storageData) {
    try {
      const prefillData = JSON.parse(storageData)
      if (prefillData.updates) {
        Object.keys(prefillData.updates).forEach(key => {
          if (form.value.hasOwnProperty(key)) {
            form.value[key] = prefillData.updates[key]
          }
        })
        window.logger.log('[DEBUG] 应用预填充更新数据:', prefillData.updates)
      }
      sessionStorage.removeItem('smartCommandData')
    } catch (e) {
      window.logger.error('解析预填充数据失败:', e)
    }
  }
  
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (form.value.id) {
          const isFormChanged = 
            form.value.code !== originalForm.value.code ||
            form.value.name !== originalForm.value.name ||
            form.value.description !== originalForm.value.description ||
            form.value.is_active !== originalForm.value.is_active
          
          const isStudentsChanged = 
            JSON.stringify(selectedStudentIds.value.sort()) !== JSON.stringify(originalStudentIds.value.sort())
          
          if (!isFormChanged && !isStudentsChanged) {
            ElMessage.warning(t('common.noChange'))
            return
          }
          
          // 编辑班级 - 先保存班级基本信息
          await api.put(`/classes/${form.value.id}`, form.value)
          
          // 获取所有学员，然后过滤出属于当前班级的学员
          const allStudentsResponse = await api.get('/students', { params: { skip: 0, limit: 100000 } })
          const allStudents = allStudentsResponse.data.items || allStudentsResponse.data
          const currentStudents = allStudents.filter(s => s.class_ids && s.class_ids.includes(form.value.id))
          const currentStudentIds = currentStudents.map(s => s.id)
          
          // 计算需要添加和移除的学员
          const toAdd = selectedStudentIds.value.filter(id => !currentStudentIds.includes(id))
          const toRemove = currentStudentIds.filter(id => !selectedStudentIds.value.includes(id))
          
          // 添加新学员
          for (const studentId of toAdd) {
            try {
              const student = availableStudents.value.find(s => s.id === studentId)
              if (student) {
                const currentClassIds = student.class_ids || []
                if (!currentClassIds.includes(form.value.id)) {
                  const newClassIds = [...currentClassIds, form.value.id]
                  await api.put(`/students/${studentId}`, { class_ids: newClassIds })
                }
              }
            } catch (studentError) {
              window.logger.error(`添加学员 ${studentId} 到班级失败:`, studentError)
            }
          }
          
          // 移除学员
          for (const studentId of toRemove) {
            try {
              const student = availableStudents.value.find(s => s.id === studentId)
              if (student) {
                const currentClassIds = student.class_ids || []
                const newClassIds = currentClassIds.filter(id => id !== form.value.id)
                await api.put(`/students/${studentId}`, { class_ids: newClassIds })
              }
            } catch (studentError) {
              window.logger.error(`从班级移除学员 ${studentId} 失败:`, studentError)
            }
          }
          
          ElMessage.success(t('common.updateSuccess'))
        } else {
          // 新建班级
          const response = await api.post('/classes', form.value)
          const newClassId = response.data.id
          
          // 将选中的学员添加到班级
          if (selectedStudentIds.value.length > 0) {
            for (const studentId of selectedStudentIds.value) {
              try {
                const student = availableStudents.value.find(s => s.id === studentId)
                if (student) {
                  const currentClassIds = student.class_ids || []
                  if (!currentClassIds.includes(newClassId)) {
                    const newClassIds = [...currentClassIds, newClassId]
                    await api.put(`/students/${studentId}`, { class_ids: newClassIds })
                  }
                }
              } catch (studentError) {
                window.logger.error(`添加学员 ${studentId} 到新班级失败:`, studentError)
              }
            }
          }
          
          ElMessage.success(t('common.createSuccess'))
        }
        dialogVisible.value = false
        fetchClasses()
      } catch (error) {
        window.logger.error('操作失败:', error)
        if (error.response) {
          window.logger.error('错误状态:', error.response.status)
          window.logger.error('错误详情:', error.response.data)
          ElMessage.error(t('common.operationFailed') + `: ${error.response.status} - ${JSON.stringify(error.response.data)}`)
        } else {
          ElMessage.error(t('common.operationFailedNetwork'))
        }
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('classes.confirmDeleteClass'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/classes/${row.id}`)
      ElMessage.success(t('common.deleteSuccess'))
      fetchClasses()
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const goToPage = (path) => {
  router.push(path)
}

const handleWebhookChange = async (row) => {
  try {
    await api.put(`/classes/${row.id}`, { wechat_webhook: row.wechat_webhook })
    ElMessage.success(t('classes.webhookUpdateSuccess'))
  } catch (error) {
    window.logger.error('更新Webhook地址失败:', error)
    ElMessage.error(t('classes.webhookUpdateFailed'))
    fetchClasses()
  }
}

const testWebhook = async (row) => {
  if (!row.wechat_webhook) {
    ElMessage.warning(t('classes.webhookRequired'))
    return
  }
  
  testingWebhook.value = row.id
  try {
    await api.post('/settings/test-wechat-url', { webhook_url: row.wechat_webhook })
    ElMessage.success(t('classes.webhookTestSuccess'))
  } catch (error) {
    window.logger.error('测试发送失败:', error)
    ElMessage.error(error.response?.data?.detail || t('classes.webhookTestFailed'))
  } finally {
    testingWebhook.value = null
  }
}

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  
  // 检查是否有来自智能指令的搜索参数
  const urlParams = new URLSearchParams(window.location.search)
  const searchQuery = urlParams.get('search')
  const relatedTo = urlParams.get('related_to')
  const viewDetail = urlParams.get('view_detail')
  
  // 支持通过URL参数设置筛选条件
  const urlIsActive = urlParams.get('is_active')
  const urlSortField = urlParams.get('sort_field')
  const urlSortOrder = urlParams.get('sort_order')
  const urlPage = urlParams.get('page')
  const urlPageSize = urlParams.get('page_size')
  
  // 应用URL参数到筛选条件
  if (urlIsActive !== null && urlIsActive !== '') {
    isActiveFilter.value = urlIsActive === 'true' ? true : (urlIsActive === 'false' ? false : null)
  }
  
  if (urlSortField) {
    sortField.value = urlSortField
  }
  
  if (urlSortOrder) {
    sortOrder.value = urlSortOrder === 'desc' ? 'desc' : 'asc'
  }
  
  if (urlPage) {
    pagination.value.currentPage = parseInt(urlPage) || 1
  }
  
  if (urlPageSize) {
    pagination.value.pageSize = parseInt(urlPageSize) || 25
  }

  fetchClasses()
  fetchStudents()
  fetchSchedules()
  
  // 如果有搜索参数，自动填充并执行搜索
  if (searchQuery) {
    searchKeyword.value = searchQuery
    setTimeout(() => {
      handleSearch()
      
      // 如果需要查看关联信息
      if (relatedTo && sessionStorage.getItem('smartCommandData')) {
        try {
          const smartData = JSON.parse(sessionStorage.getItem('smartCommandData'))
          if (smartData.target_path && smartData.target_label) {
            ElMessage.info(t('classes.foundClassJump', { name: searchQuery, label: smartData.target_label }))
            setTimeout(() => {
              window.location.href = `${smartData.target_path}?filter_by=class&filter_value=${encodeURIComponent(searchQuery)}`
            }, 1500)
          }
        } catch (e) {
          window.logger.error('解析智能指令数据失败', e)
        }
      }
      
      // 如果需要查看详情
      if (viewDetail === 'true') {
        setTimeout(() => {
          const firstClass = classes.value.find(c => c.name === searchQuery || c.code === searchQuery)
          if (firstClass) {
            showEditDialog(firstClass)
          } else {
            ElMessage.warning(t('classes.noMatchingClass'))
          }
        }, 1000)
      }
    }, 500)
  }
  
  // 检查是否需要自动打开新增对话框
  if (route.query.action === 'add') {
    showAddDialog()
  }
})

// 监听路由参数变化，支持从悬浮球等外部触发的操作
watch(() => route.query, (newQuery) => {
  if (newQuery.action === 'add') {
    showAddDialog()
  }
}, { deep: true })
</script>

<style scoped>
.classes-page {
  padding: 6px;
}

.search-bar {
  display: flex;
  gap: 5px;
  margin-bottom: 20px;
}
.search-bar .el-input {
  width: 100%;
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-card :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.card-header .button-group {
  display: flex;
  gap: 10px;
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
    gap: 10px;
  }
  
  .card-header .button-group {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .search-bar {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
  }
  
  .search-bar :deep(.el-input) {
    width: 100% !important;
  }
  
  .search-bar :deep(.el-select) {
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