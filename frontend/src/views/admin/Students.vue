// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 CourseArrange Contributors
<template>
  <div class="students-page">
    <!-- 导航栏 -->
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
        <el-col :span="3">
          <el-button type="primary" @click="goToPage('/admin/conditions')" style="width: 100%;height: 100%;">
            <el-icon><Setting /></el-icon>
            条件管理
          </el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学员管理</span>
          <div class="button-group">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回上一页
            </el-button>
            <el-button v-if="canAccessFeeManagement" type="danger" @click="goToFeeManagement">
              <el-icon><Money /></el-icon>
              费用管理
            </el-button>
            <el-tooltip v-else-if="hasFeeManagementRole" content="费用管理为授权功能，请在系统授权管理中激活" placement="bottom">
              <el-button type="danger" disabled>
                <el-icon><Lock /></el-icon>
                费用管理
              </el-button>
            </el-tooltip>
            <el-button v-if="canAccessGradeManagement && hasFeature('grade_trend')" type="warning" @click="goToGradeManagement">
              <el-icon><Document /></el-icon>
              成绩管理
            </el-button>
            <el-tooltip v-else-if="canAccessGradeManagement" content="成绩管理为授权功能，请在系统授权管理中激活" placement="bottom">
              <el-button type="warning" disabled>
                <el-icon><Lock /></el-icon>
                成绩管理
              </el-button>
            </el-tooltip>
            <el-button v-if="canAccessEvaluationManagement" type="warning" @click="goToEvaluationManagement">
              <el-icon><DataAnalysis /></el-icon>
              评价管理
            </el-button>
            <el-tooltip v-else-if="canAccessGradeManagement" content="学员评价为授权功能，请在系统授权管理中激活" placement="bottom">
              <el-button type="warning" disabled>
                <el-icon><Lock /></el-icon>
                评价管理
              </el-button>
            </el-tooltip>
            <el-button type="primary" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              新增学员
            </el-button>
            <el-button type="success" @click="showBatchAddDialog">
              <el-icon><Upload /></el-icon>
              批量添加
            </el-button>
          </div>
        </div>
      </template>

      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="姓名、代码、学校、年级或联系信息"
          style="width: 350px"
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
        <el-select v-model="isActiveFilter" placeholder="本机构在读状态" clearable style="width: 150px" @change="handleFilterChange">
          <el-option label="在读" :value="true" />
          <el-option label="非在读" :value="false" />
        </el-select>
        <el-button @click="resetFilters" style="width: 50px">重置</el-button>
      </div>

      <div class="fake-scrollbar" ref="topScrollbarRef">
        <div class="scrollbar-inner" :style="{ width: scrollbarWidth + 'px' }"></div>
      </div>
      <el-table :data="students" stripe v-loading="loading" style="margin-top: 0" @sort-change="handleSortChange" ref="mainTableRef">
          <el-table-column prop="id" label="ID" width="70" sortable />
          <el-table-column prop="code" label="学员代码" width="120" sortable />
          <el-table-column prop="name" label="学员姓名" width="120" sortable>
            <template #default="{ row }">
              <el-tooltip placement="top" effect="light">
                <template #content>
                  <div v-if="row.classes && row.classes.length > 0">
                    <div><strong>本机构所属班级：</strong></div>
                    <div v-for="cls in row.classes" :key="cls.id" style="margin-left: 10px;">
                      {{ cls.name }}
                    </div>
                  </div>
                  <div v-else>
                    <div><strong>本机构所属班级：</strong>无</div>
                  </div>
                  <div>
                    <div><strong>本机构是否在读：</strong>{{ row.is_active ? '在读' : '非在读' }}</div>
                  </div>
                </template>
                <span style="cursor: help; color: #409EFF;">{{ row.name }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="school" label="就读学校" width="150" sortable />
          <el-table-column prop="grade" label="就读年级" width="120" sortable />
          <el-table-column label="进入机构日期" width="150" sortable>
            <template #default="{ row }">
              {{ row.enrollment_date ? new Date(row.enrollment_date).toLocaleDateString('zh-CN') : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="联系人" width="120" sortable >
            <template #default="{ row }">
              {{ row.contact_person || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="联系电话" width="120" sortable >
            <template #default="{ row }">
              {{ row.contact_phone || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="电子邮箱" width="200" sortable >
            <template #default="{ row }">
              {{ row.email || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="非节假每周可安排日" width="200">
              <template #default="{ row }">
                  <el-tag v-for="day in parseAvailableDays(row.available_days)" :key="day" size="small" style="margin-right: 5px; margin-bottom: 5px;">
                  {{ day }}
                  </el-tag>
              </template>
          </el-table-column>
          <el-table-column label="可安排课时段" width="300">
              <template #default="{ row }">
                  <el-tag v-for="slot in parseAvailableTimeSlots(row.available_time_slots)" :key="slot" size="small" style="margin-right: 5px; margin-bottom: 5px;">
                  {{ slot }}
                  </el-tag>
              </template>
          </el-table-column>
          <el-table-column label="节假日可排课" width="120">
            <template #default="{ row }">
              <el-tag :type="row.allow_holiday_scheduling ? 'success' : 'info'">
                {{ row.allow_holiday_scheduling ? '可排课' : '不可排课' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="本机构在读状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '在读' : '非在读' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button v-if="hasFeature('grade_trend')" size="small" type="primary" @click="showGradeCurve(row)">成绩曲线</el-button>
              <el-tooltip v-else content="学员成绩曲线为授权功能，请在系统授权管理中激活" placement="top">
                <el-button size="small" type="primary" disabled>
                  <el-icon><Lock /></el-icon>
                  成绩曲线
                </el-button>
              </el-tooltip>
              <el-button v-if="canAccessEvaluationManagement" size="small" type="warning" @click="showStudentEvaluation(row)">评价内容</el-button>
              <el-tooltip v-else content="学员评价为授权功能，请在系统授权管理中激活" placement="top">
                <el-button size="small" type="warning" disabled>
                  <el-icon><Lock /></el-icon>
                  评价内容
                </el-button>
              </el-tooltip>
              <el-button v-if="currentUser && (currentUser.role === 'super_admin' || currentUser.role === 'course_admin')" size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" draggable>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="学员代码" prop="code">
          <el-input v-model="form.code" :placeholder="lastStudentCode ? `请输入学员代码(不能与现有重复否则无法创建，当前已到：${lastStudentCode})` : '请输入学员代码(不能与现有重复)'" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="学员姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入学员姓名" />
        </el-form-item>
        <el-form-item label="就读学校" prop="school">
          <el-input v-model="form.school" placeholder="请输入就读学校" />
        </el-form-item>
        <el-form-item label="就读年级" prop="grade">
          <el-select v-model="form.grade" placeholder="请选择就读年级" clearable filterable allow-create style="width: 100%">
            <el-option v-for="g in gradeOptions" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人" prop="contact_person">
          <el-input v-model="form.contact_person" placeholder="请输入联系人（家长或监护人）" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="form.contact_phone" placeholder="请输入手机号码或座机号码" />
        </el-form-item>
        <el-form-item label="电子邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入电子邮箱" />
        </el-form-item>
        <el-form-item label="进入机构日期" prop="enrollment_date">
          <el-date-picker
            v-model="form.enrollment_date"
            type="date"
            placeholder="选择进入机构日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="本机构所属班级" prop="class_ids">
          <el-select v-model="form.class_ids" multiple filterable placeholder="请选择班级" clearable style="width: 100%">
            <el-option
              v-for="class_ in classes"
              :key="class_.id"
              :label="class_.name"
              :value="class_.id"
            >
            <el-tooltip placement="right" :show-after="200">
              <template #content>
                <div v-if="getActiveClassStudents(class_.id).length > 0">
                  <div style="font-weight: bold; margin-bottom: 8px; color: #67c23a;">在读学员:</div>
                  <div v-for="student in getActiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                    {{ student.name }}
                  </div>
                </div>
                <div v-if="getInactiveClassStudents(class_.id).length > 0">
                  <div style="font-weight: bold; margin-bottom: 8px; margin-top: 12px; color: #909399;">非在读学员:</div>
                  <div v-for="student in getInactiveClassStudents(class_.id)" :key="student.id" style="margin-bottom: 4px;">
                    {{ student.name }}
                  </div>
                </div>
                <div v-if="getActiveClassStudents(class_.id).length === 0 && getInactiveClassStudents(class_.id).length === 0">
                  暂无学员
                </div>
                <!-- 添加班级对应的导师信息 -->
                <div v-if="getClassTeachers(class_.id).length > 0" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                  <div style="font-weight: bold; margin-bottom: 8px; color: #409EFF;">班级导师:</div>
                  <div v-for="teacher in getClassTeachers(class_.id)" :key="teacher.id" style="margin-bottom: 4px;">
                    {{ teacher.name }}
                    <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                  </div>
                </div>
                <div v-else style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;">
                  <div style="color: #999;">暂无导师</div>
                </div>
              </template>
              <span>{{ class_.name }}</span>
            </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="非节假每周可安排日" prop="available_days">
            <el-checkbox-group v-model="selectedDays">
                <el-checkbox :value="1">周一</el-checkbox>
                <el-checkbox :value="2">周二</el-checkbox>
                <el-checkbox :value="3">周三</el-checkbox>
                <el-checkbox :value="4">周四</el-checkbox>
                <el-checkbox :value="5">周五</el-checkbox>
                <el-checkbox :value="6">周六</el-checkbox>
                <el-checkbox :value="7">周日</el-checkbox>
            </el-checkbox-group>
        </el-form-item>
        <el-form-item label="节假日可排课">
          <el-switch v-model="form.allow_holiday_scheduling" />
          <span style="margin-left: 10px; color: #999; font-size: 12px;">
            勾选后，节假日(包含法定与自定义假日)也可以安排课程
          </span>
        </el-form-item>
        <el-form-item label="可安排课时段" prop="available_time_slots">
            <el-row :gutter="10">
                <el-col :span="12">
                <div style="margin-bottom: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 上午
                </div>
                <el-checkbox-group v-model="selectedTimeSlots" @change="handleTimeSlotChange">
                    <div style="margin-bottom: 5px;">
                    <el-checkbox value="08:00-10:00" :class="{ 'overlapping-slot': isOverlappingSlot('08:00-10:00') }">08:00-10:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                    <el-checkbox value="10:00-12:00" :class="{ 'overlapping-slot': isOverlappingSlot('10:00-12:00') }">10:00-12:00</el-checkbox>
                    </div>
                </el-checkbox-group>
                </el-col>
                <el-col :span="12">
                <div style="margin-bottom: 5px; font-size: 12px; color: #909399;">
                    <el-icon><InfoFilled /></el-icon> 下午（重叠时间段）
                </div>
                <el-checkbox-group v-model="selectedTimeSlots" @change="handleTimeSlotChange">
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="13:30-15:30" :class="{ 'overlapping-slot': isOverlappingSlot('13:30-15:30') }">13:30-15:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="14:00-16:00" :class="{ 'overlapping-slot': isOverlappingSlot('14:00-16:00') }">14:00-16:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="14:30-16:30" :class="{ 'overlapping-slot': isOverlappingSlot('14:30-16:30') }">14:30-16:30</el-checkbox>
                    </div>                    
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="15:30-17:30" :class="{ 'overlapping-slot': isOverlappingSlot('15:30-17:30') }">15:30-17:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="16:00-18:00" :class="{ 'overlapping-slot': isOverlappingSlot('16:00-18:00') }">16:00-18:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="16:30-18:30" :class="{ 'overlapping-slot': isOverlappingSlot('16:30-18:30') }">16:30-18:30</el-checkbox>
                    </div>                    
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="17:30-19:30" :class="{ 'overlapping-slot': isOverlappingSlot('17:30-19:30') }">17:30-19:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="18:00-20:00" :class="{ 'overlapping-slot': isOverlappingSlot('18:00-20:00') }">18:00-20:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="18:30-20:30" :class="{ 'overlapping-slot': isOverlappingSlot('18:30-20:30') }">18:30-20:30</el-checkbox>
                    </div>                    
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="19:30-21:30" :class="{ 'overlapping-slot': isOverlappingSlot('19:30-21:30') }">19:30-21:30</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="20:00-22:00" :class="{ 'overlapping-slot': isOverlappingSlot('20:00-22:00') }">20:00-22:00</el-checkbox>
                    </div>
                    <div style="margin-bottom: 5px;">
                      <el-checkbox value="20:30-22:30" :class="{ 'overlapping-slot': isOverlappingSlot('20:30-22:30') }">20:30-22:30</el-checkbox>
                    </div>
                </el-checkbox-group>
                </el-col>
            </el-row>
            <div style="margin-top: 10px; font-size: 12px; color: #909399;">
              <el-icon><InfoFilled /></el-icon> 
              说明：纵坐标显示成绩比例（当次考试成绩÷当次科目总分×100%），实线表示有成绩数据，虚线表示该考试阶段无成绩数据（过渡显示）
            </div>
        </el-form-item>
        <el-form-item label="本机构在读状态" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date" v-if="!form.is_active">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="选择结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    <!-- 批量添加学员对话框 -->
    <el-dialog v-model="batchAddDialogVisible" title="批量添加学员" width="800px" draggable>
      <div style="margin-bottom: 20px;">
        <el-alert
          title="批量添加说明"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div>请按照以下格式输入学员信息，每行一个学员：</div>
            <div style="margin-top: 10px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              代码(*必填),姓名(*必填),进入日期(YYYY-MM-DD),学校,年级,联系人,联系方式,电子邮箱,可排课日(1-7,逗号分隔)
            </div>
            <div style="margin-top: 10px;">例如：</div>
            <div style="margin-top: 5px; font-family: monospace; background: #f5f7fa; padding: 10px; border-radius: 4px;">
              S001,张三,2024-01-15,第一中学,高一,张爸爸,13800138000,zhangsan@example.com,6,7<br/>
              S002,李四,2024-02-20,第二中学,高二,李妈妈,13900139000,lisi@example.com,1,2,3,4,5<br/>
              S003,王五,, , , , , ,6,7
            </div>
            <div style="margin-top: 10px;">注意：</div>
            <ul style="margin-top: 5px;">
              <li>代码不能与现有学员重复否则无法创建，上一个学员代码：<span v-if="lastStudentCode">{{ lastStudentCode }}</span><span v-else>无</span>，请在这个代码+1的基础上开始</li>
              <li>可排课日：1=周一, 2=周二, 3=周三, 4=周四, 5=周五, 6=周六, 7=周日</li>
              <li>可排课日支持多个值，用逗号分隔，如：6,7 表示周六和周日</li>
              <li>可在上方选择班级和可排课时间段，所有批量添加的学员都会应用相同的设置</li>
            </ul>
          </template>
        </el-alert>
      </div>
      <el-form>
        <el-form-item label="所属班级">
          <el-select
            v-model="selectedBatchClassIds"
            multiple
            filterable
            placeholder="请选择班级（可多选，不选则不分配班级）"
            style="width: 100%"
          >
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="`${cls.code} - ${cls.name}`"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="可排课时间段">
          <el-select
            v-model="selectedBatchTimeSlots"
            multiple
            placeholder="请选择可排课时间段（可多选，不选则使用默认）"
            style="width: 100%"
            @change="handleBatchTimeSlotChange"
          >
            <el-option label="08:00-10:00" value="08:00-10:00" />
            <el-option label="10:00-12:00" value="10:00-12:00" />
            <el-option label="13:30-15:30" value="13:30-15:30" />
            <el-option label="14:00-16:00" value="14:00-16:00" />
            <el-option label="14:30-16:30" value="14:30-16:30" />
            <el-option label="15:30-17:30" value="15:30-17:30" />
            <el-option label="16:00-18:00" value="16:00-18:00" />
            <el-option label="16:30-18:30" value="16:30-18:30" />
            <el-option label="17:30-19:30" value="17:30-19:30" />
            <el-option label="18:00-20:00" value="18:00-20:00" />
            <el-option label="18:30-20:30" value="18:30-20:30" />
            <el-option label="19:30-21:30" value="19:30-21:30" />
            <el-option label="20:00-22:00" value="20:00-22:00" />
            <el-option label="20:30-22:30" value="20:30-22:30" />
          </el-select>
          <div style="margin-top: 5px; font-size: 12px; color: #909399;">
            <el-icon><InfoFilled /></el-icon> 说明：选择的时间段不能重叠，重叠的时间段会自动取消选择
          </div>
        </el-form-item>
        <el-form-item label="学员信息">
          <el-input
            v-model="batchAddText"
            type="textarea"
            :rows="15"
            placeholder="请输入学员信息，每行一个学员"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchAddDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchAddSubmit" :loading="batchAddLoading">批量添加</el-button>
      </template>
    </el-dialog>
    <!-- 成绩比例曲线对话框 -->
    <el-dialog v-model="gradeCurveDialogVisible" :title="`成绩比例曲线 - ${currentStudentName}`" width="90%" top="5vh" draggable>
      <div v-loading="gradeCurveLoading">
        <div v-if="!gradeCurveLoading && (!gradeCurveData || !gradeCurveData.courses || gradeCurveData.courses.length === 0)" style="text-align: center; padding: 40px; color: #909399;">
          <el-empty description="暂无成绩数据" />
        </div>
        <div v-else>
          <div ref="gradeCurveChart" style="width: 100%; height: 600px;"></div>
          <div style="margin-top: 20px; padding: 15px; background: #f5f7fa; border-radius: 4px;">
            <h4 style="margin-top: 0; margin-bottom: 10px;">图例说明：</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 15px;">
              <div v-for="course in gradeCurveData?.courses" :key="course.course_name" style="display: flex; align-items: center; gap: 5px;">
                <div :style="{ width: '20px', height: '3px', backgroundColor: course.color }"></div>
                <span>{{ course.course_name }}</span>
              </div>
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #909399;">
              <el-icon><InfoFilled /></el-icon> 
              说明：实线表示有成绩数据，虚线表示该考试阶段无成绩数据（过渡显示）
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="gradeCurveDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Search, Reading, User, UserFilled, OfficeBuilding, Calendar, Clock, InfoFilled, Money, Document, Upload, Lock, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { hasFeature } from '@/utils/license'
import * as echarts from 'echarts'

const mainTableRef = ref(null)
const topScrollbarRef = ref(null)
const scrollbarWidth = ref(0)
let scrollHandler = null

const currentUser = ref(null)
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)
const searchKeyword = ref('')
const isActiveFilter = ref(null)
const selectedDays = ref([1, 2, 3, 4, 5, 6, 7])
const selectedTimeSlots = ref([])
const classes = ref([])

const defaultGradeOptions = [
  '小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
  '初中一年级', '初中二年级', '初中三年级',
  '高中一年级', '高中二年级', '高中三年级',
  '大学一年级', '大学二年级', '大学三年级', '大学四年级',
  '研究生一年级', '研究生二年级', '研究生三年级'
]
const gradeOptions = ref([...defaultGradeOptions])

const goBack = () => {
  router.back()
}

// 检查是否有权限访问费用管理
const canAccessFeeManagement = computed(() => {
  const currentUser = JSON.parse(localStorage.getItem('user'))
  if (!currentUser) {
    return false
  }
  if (!hasFeature('fee_management')) {
      return false
    }
  if (['super_admin', 'system_admin'].includes(currentUser.role)) {
    return true
  }
  const feeManagersStr = localStorage.getItem('fee_managers')
  if (feeManagersStr && currentUser.teacher_id) {
    try {
      const feeManagers = JSON.parse(feeManagersStr)
      if (Array.isArray(feeManagers) && feeManagers.includes(currentUser.teacher_id)) {
        return true
      }
    } catch (e) {
      window.logger.error('[权限检查] 解析费用管理导师列表失败:', e)
    }
  }
  return false
})

const hasFeeManagementRole = computed(() => {
  const currentUser = JSON.parse(localStorage.getItem('user'))
  if (!currentUser) {
    return false
  }
  if (['super_admin', 'system_admin'].includes(currentUser.role)) {
    return true
  }
  const feeManagersStr = localStorage.getItem('fee_managers')
  if (feeManagersStr && currentUser.teacher_id) {
    try {
      const feeManagers = JSON.parse(feeManagersStr)
      if (Array.isArray(feeManagers) && feeManagers.includes(currentUser.teacher_id)) {
        return true
      }
    } catch (e) {
      window.logger.error('[权限检查] 解析费用管理导师列表失败:', e)
    }
  }
  return false
})

// 检查是否有权限访问成绩管理
const canAccessGradeManagement = computed(() => {
  const currentUser = JSON.parse(localStorage.getItem('user'))
  if (!currentUser) {
    window.logger.log('[权限检查] currentUser为空')
    return false
  }
  if (['super_admin', 'system_admin'].includes(currentUser.role)) {
    window.logger.log('[权限检查] 管理员角色，允许访问成绩管理')
    return true
  }
  const gradeManagersStr = localStorage.getItem('grade_managers')
  window.logger.log('[权限检查] grade_managers:', gradeManagersStr)
  window.logger.log('[权限检查] teacher_id:', currentUser.teacher_id)
  if (gradeManagersStr && currentUser.teacher_id) {
    try {
      const gradeManagers = JSON.parse(gradeManagersStr)
      window.logger.log('[权限检查] 解析后的grade_managers:', gradeManagers)
      if (Array.isArray(gradeManagers) && gradeManagers.includes(currentUser.teacher_id)) {
        window.logger.log('[权限检查] 是成绩管理导师，允许访问')
        return true
      }
    } catch (e) {
      window.logger.error('[权限检查] 解析成绩管理导师列表失败:', e)
    }
  }
  window.logger.log('[权限检查] 不允许访问成绩管理')
  return false
})

const canAccessEvaluationManagement = computed(() => {
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

// 添加排序相关变量
const sortField = ref('')
const sortOrder = ref('asc')

// 添加排序处理函数
const handleSortChange = ({ prop, order }) => {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  pagination.value.currentPage = 1
  fetchStudents()
}

const getClassTeachers = (classId) => {
  const classTeachers = []
  if (schedules.value && schedules.value.length > 0) {
    schedules.value.forEach(schedule => {
      if (schedule.class_id === classId && schedule.teacher) {
        const existing = classTeachers.find(t => t.id === schedule.teacher.id)
        if (!existing) {
          classTeachers.push(schedule.teacher)
        }
      }
    })
  }
  return classTeachers
}
const fetchClasses = async () => {
  try {
    const response = await api.get('/classes', { params: { skip: 0, limit: 100000 } })
    classes.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取班级列表失败:', error)
  }
}

const getClassName = (classId) => {
  const class_ = classes.value.find(c => c.id === classId)
  return class_ ? class_.name : '-'
}

// 判断两个时间段是否重叠
const isTimeSlotOverlap = (slot1, slot2) => {
  const [start1, end1] = slot1.split('-')
  const [start2, end2] = slot2.split('-')
  // 重叠条件：start1 < end2 && end1 > start2
  return start1 < end2 && end1 > start2
}

// 检查某个时间段是否与已选时间段重叠
const isOverlappingSlot = (slot) => {
  for (const selectedSlot of selectedTimeSlots.value) {
    if (selectedSlot !== slot && isTimeSlotOverlap(slot, selectedSlot)) {
      return true
    }
  }
  return false
}

// 处理时间段选择
const handleTimeSlotChange = (value) => {
  // 获取当前选中的所有时间段
  const currentSelected = value
  
  // 检查每个选中的时间段是否与其他时间段重叠
  const nonOverlappingSlots = []
  const overlappingSlots = []
  
  currentSelected.forEach(selectedSlot => {
    let hasOverlap = false
    
    // 检查与已选时间段是否重叠
    for (const existingSlot of nonOverlappingSlots) {
      if (isTimeSlotOverlap(selectedSlot, existingSlot)) {
        hasOverlap = true
        overlappingSlots.push(selectedSlot)
        break
      }
    }
    
    // 如果不重叠，添加到结果中
    if (!hasOverlap) {
      nonOverlappingSlots.push(selectedSlot)
    }
  })
  
  // 如果有重叠的时间段，显示提示
  if (overlappingSlots.length > 0) {
    ElMessage.warning(`以下时间段与其他时间段重叠，已自动取消选择：${overlappingSlots.join(', ')}`)
  }
  
  // 更新选中的时间段
  selectedTimeSlots.value = nonOverlappingSlots
}

// 处理批量添加时间段选择
const handleBatchTimeSlotChange = (value) => {
  // 获取当前选中的所有时间段
  const currentSelected = value
  
  // 检查每个选中的时间段是否与其他时间段重叠
  const nonOverlappingSlots = []
  const overlappingSlots = []
  
  currentSelected.forEach(selectedSlot => {
    let hasOverlap = false
    
    // 检查与已选时间段是否重叠
    for (const existingSlot of nonOverlappingSlots) {
      if (isTimeSlotOverlap(selectedSlot, existingSlot)) {
        hasOverlap = true
        overlappingSlots.push(selectedSlot)
        break
      }
    }
    
    // 如果不重叠，添加到结果中
    if (!hasOverlap) {
      nonOverlappingSlots.push(selectedSlot)
    }
  })
  
  // 如果有重叠的时间段，显示提示
  if (overlappingSlots.length > 0) {
    ElMessage.warning(`以下时间段与其他时间段重叠，已自动取消选择：${overlappingSlots.join(', ')}`)
  }
  
  // 更新选中的时间段
  selectedBatchTimeSlots.value = nonOverlappingSlots
}

const students = ref([])
const allStudents = ref([])
const schedules = ref([])
const batchAddDialogVisible = ref(false)
const batchAddText = ref('')
const batchAddLoading = ref(false)
const lastStudentCode = ref('')
const selectedBatchClassIds = ref([])
const selectedBatchTimeSlots = ref([])

const pagination = ref({
  currentPage: 1,
  pageSize: 15,
  total: 0
})

// 添加分页处理函数
const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchStudents()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchStudents()
}

const handleSearch = () => {
  pagination.value.currentPage = 1
  fetchStudents()
  updateUrlParams()
}

const handleFilterChange = () => {
  pagination.value.currentPage = 1
  fetchStudents()
  updateUrlParams()
}

const form = ref({
  code: '',
  name: '',
  school: '',
  grade: '',
  enrollment_date: null,
  class_ids: [],
  available_days: '1,2,3,4,5,6,7',
  available_time_slots: '08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30',
  allow_holiday_scheduling: true,
  contact_person: '',
  contact_phone: '',
  email: '',
  is_active: true,
  end_date: null
})

const originalForm = ref({
  code: '',
  name: '',
  school: '',
  grade: '',
  enrollment_date: null,
  class_ids: [],
  available_days: '1,2,3,4,5,6,7',
  available_time_slots: '08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30',
  allow_holiday_scheduling: true,
  contact_person: '',
  contact_phone: '',
  email: '',
  is_active: true,
  end_date: null
})

const rules = {
  code: [{ required: true, message: '请输入学员代码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入学员姓名', trigger: 'blur' }]
}

// 更新URL参数以反映当前筛选状态
const updateUrlParams = () => {
  const params = new URLSearchParams(window.location.search)
  
  if (searchKeyword.value) {
    params.set('search', searchKeyword.value)
  } else {
    params.delete('search')
  }
  
  if (isActiveFilter.value !== null && isActiveFilter.value !== undefined) {
    params.set('is_active', isActiveFilter.value.toString())
  } else {
    params.delete('is_active')
  }
  
  if (sortField.value) {
    params.set('sort_field', sortField.value)
  } else {
    params.delete('sort_field')
  }
  
  if (sortOrder.value) {
    params.set('sort_order', sortOrder.value)
  } else {
    params.delete('sort_order')
  }
  
  const queryString = params.toString()
  const newUrl = queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname
  
  window.history.replaceState({}, '', newUrl)
}

watch(selectedDays, (newVal) => {
  form.value.available_days = newVal.sort().join(',')
})

watch(selectedTimeSlots, (newVal) => {
  form.value.available_time_slots = newVal.sort().join(',')
})

const parseAvailableDays = (daysStr) => {
  const days = daysStr.split(',').map(d => parseInt(d.trim()))
  const dayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return days.map(d => dayNames[d] || '')
}

const parseAvailableTimeSlots = (timeSlotsStr) => {
  if (!timeSlotsStr) return []
  return timeSlotsStr.split(',').map(t => t.trim()).filter(t => t)
}

const handleStudentStatusChange = (newValue) => {
  if (newValue === false && !form.value.end_date) {
    // 如果从在读变为非在读，自动设置结束日期为今天
    form.value.end_date = new Date().toISOString().split('T')[0]
  } else if (newValue === true) {
    // 如果从非在读变为在读，清空结束日期
    form.value.end_date = null
  }
}

const getActiveClassStudents = (classId) => {
  // 获取某个班级的在读学员列表
  return allStudents.value.filter(s => {
    // 检查学生是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学生是否在读
    const isActive = s.is_active
    return belongsToClass && isActive
  })
}

const getInactiveClassStudents = (classId) => {
  // 获取某个班级的非在读学员列表
  return allStudents.value.filter(s => {
    // 检查学生是否属于该班级
    const belongsToClass = s.class_ids && s.class_ids.includes(classId)
    // 检查学生是否非在读
    const isInactive = !s.is_active
    return belongsToClass && isInactive
  })
}

const fetchStudents = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (isActiveFilter.value !== null) {
      params.is_active = isActiveFilter.value
    }
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    const response = await api.get('/students', { params })
    students.value = response.data.items
    pagination.value.total = response.data.total
    
    // 获取最后一个学员代码（按代码排序后的最后一个）
    if (response.data.items && response.data.items.length > 0) {
      const sortedByCode = [...response.data.items].sort((a, b) => a.code.localeCompare(b.code))
      lastStudentCode.value = sortedByCode[sortedByCode.length - 1].code
    } else {
      lastStudentCode.value = ''
    }
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
  } finally {
    loading.value = false
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

const resetFilters = () => {
  searchKeyword.value = ''
  isActiveFilter.value = null
  sortField.value = ''
  sortOrder.value = 'asc'
  pagination.value.currentPage = 1
  fetchStudents()
}

const goToFeeManagement = () => {
  router.push('/admin/feemanagement')
}

const goToGradeManagement = () => {
  router.push('/admin/grades')
}

const goToEvaluationManagement = () => {
  router.push('/admin/evaluations')
}

const showAddDialog = async () => {
  dialogTitle.value = '新增学员'
  
  // 确保加载所有学员数据到allStudents，以便班级悬浮信息能正确显示
  if (allStudents.value.length === 0) {
    try {
      const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
      allStudents.value = response.data.items || response.data
    } catch (error) {
      window.logger.error('获取学员列表失败:', error)
    }
  }
  
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
    name: prefillData?.student_name || '',
    school: prefillData?.school || '',
    grade: prefillData?.grade || '',
    enrollment_date: new Date().toISOString().split('T')[0],
    class_ids: prefillData?.class_id ? [prefillData.class_id] : [],
    available_days: '1,2,3,4,5,6,7',
    available_time_slots: '08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30',
    allow_holiday_scheduling: true,
    contact_person: prefillData?.contact_person || '',
    contact_phone: prefillData?.contact_phone || '',
    email: prefillData?.email || '',
    is_active: true,
    end_date: null
  }
  
  // 初始化 selectedDays 和 selectedTimeSlots
  selectedDays.value = [1, 2, 3, 4, 5, 6, 7]
  selectedTimeSlots.value = ['08:00-10:00', '10:00-12:00', '13:30-15:30', '15:30-17:30', '17:30-19:30', '19:30-21:30']
  
  dialogVisible.value = true
}

const showBatchAddDialog = () => {
  batchAddText.value = ''
  selectedBatchClassIds.value = []
  selectedBatchTimeSlots.value = []
  batchAddDialogVisible.value = true
}
const handleBatchAddSubmit = async () => {
  if (!batchAddText.value.trim()) {
    ElMessage.warning('请输入学员信息')
    return
  }
  
  const lines = batchAddText.value.trim().split('\n')
  const studentsToAdd = []
  const errors = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    const parts = line.split(',').map(p => p.trim())
    if (parts.length < 2) {
      errors.push(`第${i + 1}行：格式错误，至少需要代码和姓名`)
      continue
    }
    
    const student = {
      code: parts[0],
      name: parts[1],
      enrollment_date: parts[2] || null,
      school: parts[3] || '',
      grade: parts[4] || '',
      contact_person: parts[5] || '',
      contact_phone: parts[6] || '',
      email: parts[7] || '',
      available_days: parts.slice(8).filter(p => p).join(',') || '6,7',
      available_time_slots: selectedBatchTimeSlots.value.length > 0 ? selectedBatchTimeSlots.value.join(',') : '08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30',
      allow_holiday_scheduling: true,
      class_ids: selectedBatchClassIds.value || [],
      is_active: true
    }
    
    studentsToAdd.push(student)
  }
  
  if (errors.length > 0) {
    ElMessage.error(`发现${errors.length}个错误：\n${errors.join('\n')}`)
    if (studentsToAdd.length === 0) {
      return
    }
  }
  
  if (studentsToAdd.length === 0) {
    ElMessage.warning('没有有效的学员信息')
    return
  }
  
  batchAddLoading.value = true
  try {
    let successCount = 0
    let failCount = 0
    const failMessages = []
    
    for (const student of studentsToAdd) {
      try {
        await api.post('/students', student)
        successCount++
      } catch (error) {
        failCount++
        failMessages.push(`${student.code}(${student.name}): ${error.response?.data?.detail || error.message}`)
      }
    }
    
    if (failCount > 0) {
      ElMessage.warning(`批量添加完成：成功${successCount}个，失败${failCount}个\n失败详情：\n${failMessages.join('\n')}`)
    } else {
      ElMessage.success(`批量添加成功，共添加${successCount}个学员`)
    }
    
    batchAddDialogVisible.value = false
    await fetchStudents()
    // 重新加载allStudents数据
    try {
      const allStudentsResponse = await api.get('/students', { params: { skip: 0, limit: 100000 } })
      allStudents.value = allStudentsResponse.data.items || allStudentsResponse.data
    } catch (error) {
      window.logger.error('重新加载所有学员数据失败:', error)
    }
  } catch (error) {
    window.logger.error('批量添加学员失败:', error)
    ElMessage.error('批量添加学员失败')
  } finally {
    batchAddLoading.value = false
  }
}

const showEditDialog = async (row) => {
  dialogTitle.value = '编辑学员'
  
  // 确保加载所有学员数据到allStudents，以便班级悬浮信息能正确显示
  if (allStudents.value.length === 0) {
    try {
      const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
      allStudents.value = response.data.items || response.data
    } catch (error) {
      window.logger.error('获取学员列表失败:', error)
    }
  }
  // 格式化日期字段
  const formattedBirthDate = row.birth_date ? new Date(row.birth_date).toISOString().split('T')[0] : null
  const formattedJoinDate = row.join_date ? new Date(row.join_date).toISOString().split('T')[0] : null
  
  const formData = {
    id: row.id,
    code: row.code,
    name: row.name,
    school: row.school || '',
    grade: row.grade || '',
    enrollment_date: row.enrollment_date ? new Date(row.enrollment_date).toISOString().split('T')[0] : null,
    class_ids: row.class_ids || [],
    available_days: row.available_days || '1,2,3,4,5,6,7',
    available_time_slots: row.available_time_slots || '08:00-10:00,10:00-12:00,13:30-15:30,15:30-17:30,17:30-19:30,19:30-21:30,14:00-16:00,16:00-18:00,18:00-20:00,20:00-22:00,14:30-16:30,16:30-18:30,18:30-20:30,20:30-22:30',
    allow_holiday_scheduling: row.allow_holiday_scheduling !== undefined ? row.allow_holiday_scheduling : true,
    contact_person: row.contact_person || '',
    contact_phone: row.contact_phone || '',
    email: row.email || '',
    is_active: row.is_active !== undefined ? row.is_active : true,
    end_date: row.end_date ? new Date(row.end_date).toISOString().split('T')[0] : null
  }
  originalForm.value = { ...formData }
  form.value = formData
  
  // 同步更新 selectedDays 和 selectedTimeSlots
  if (row.available_days) {
    selectedDays.value = row.available_days.split(',').map(d => parseInt(d.trim()))
  } else {
    selectedDays.value = [1, 2, 3, 4, 5, 6, 7]
  }
  
  if (row.available_time_slots) {
    selectedTimeSlots.value = row.available_time_slots.split(',').map(t => t.trim()).filter(t => t)
  } else {
    selectedTimeSlots.value = ['08:00-10:00', '10:00-12:00', '13:30-15:30', '15:30-17:30', '17:30-19:30', '19:30-21:30']
  }
  
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
        // 如果更新了class_id，转换为class_ids数组
        if (prefillData.updates.class_id) {
          form.value.class_ids = [prefillData.updates.class_id]
        }
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
          const isChanged = 
            form.value.code !== originalForm.value.code ||
            form.value.name !== originalForm.value.name ||
            form.value.school !== originalForm.value.school ||
            form.value.grade !== originalForm.value.grade ||
            form.value.enrollment_date !== originalForm.value.enrollment_date ||
            JSON.stringify(form.value.class_ids || []) !== JSON.stringify(originalForm.value.class_ids || []) ||
            form.value.available_days !== originalForm.value.available_days ||
            form.value.available_time_slots !== originalForm.value.available_time_slots ||
            form.value.allow_holiday_scheduling !== originalForm.value.allow_holiday_scheduling ||
            form.value.contact_person !== originalForm.value.contact_person ||
            form.value.contact_phone !== originalForm.value.contact_phone ||
            form.value.email !== originalForm.value.email ||
            form.value.is_active !== originalForm.value.is_active ||
            form.value.end_date !== originalForm.value.end_date
          
          if (!isChanged) {
            ElMessage.warning('内容未发生改变，无需保存')
            return
          }
          
          // 编辑学员
          await api.put(`/students/${form.value.id}`, form.value)
          ElMessage.success('更新成功')
          // 重新加载allStudents数据
          try {
            const allStudentsResponse = await api.get('/students', { params: { skip: 0, limit: 100000 } })
            allStudents.value = allStudentsResponse.data.items || allStudentsResponse.data
          } catch (error) {
            window.logger.error('重新加载所有学员数据失败:', error)
          }
        } else {
          // 新建学员
          await api.post('/students', form.value)
          ElMessage.success('创建成功')
          // 重新加载allStudents数据
          try {
            const allStudentsResponse = await api.get('/students', { params: { skip: 0, limit: 100000 } })
            allStudents.value = allStudentsResponse.data.items || allStudentsResponse.data
          } catch (error) {
            window.logger.error('重新加载所有学员数据失败:', error)
          }
        }
        dialogVisible.value = false
        fetchStudents()
      } catch (error) {
        window.logger.error('操作失败:', error)
        if (error.response) {
          window.logger.error('错误状态:', error.response.status)
          window.logger.error('错误详情:', error.response.data)
          ElMessage.error(`操作失败: ${error.response.status} - ${JSON.stringify(error.response.data)}`)
        } else {
          ElMessage.error('操作失败，请检查网络连接')
        }
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该学员吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/students/${row.id}`)
      ElMessage.success('删除成功')
      fetchStudents()
      // 重新加载allStudents数据
      try {
        const allStudentsResponse = await api.get('/students', { params: { skip: 0, limit: 100000 } })
        allStudents.value = allStudentsResponse.data.items || allStudentsResponse.data
      } catch (error) {
        window.logger.error('重新加载所有学员数据失败:', error)
      }
    } catch (error) {
      window.logger.error('删除失败:', error)
    }
  }).catch(() => {})
}

const goToPage = (path) => {
  router.push(path)
}

const gradeCurveDialogVisible = ref(false)
const gradeCurveLoading = ref(false)
const gradeCurveData = ref(null)
const currentStudentName = ref('')
const gradeCurveChart = ref(null)
let gradeChartInstance = null

const showGradeCurve = async (row) => {
  currentStudentName.value = row.name
  gradeCurveDialogVisible.value = true
  gradeCurveLoading.value = true
  
  try {
    const response = await api.get(`/grades/student-trend/${row.id}`)
    gradeCurveData.value = response.data
    
    await nextTick()
    renderGradeCurveChart(response.data)
  } catch (error) {
    window.logger.error('获取成绩曲线数据失败:', error)
    ElMessage.error('获取成绩曲线数据失败')
  } finally {
    gradeCurveLoading.value = false
  }
}

const showStudentEvaluation = (row) => {
  router.push({ path: '/admin/evaluations', query: { student_id: row.id } })
}

const renderGradeCurveChart = (data) => {
  if (!gradeCurveChart.value) return
  
  if (gradeChartInstance) {
    gradeChartInstance.dispose()
  }
  
  gradeChartInstance = echarts.init(gradeCurveChart.value)
  
  if (!data.exam_stages || data.exam_stages.length === 0) {
    const option = {
      title: {
        text: `${data.student_name} 成绩趋势图`,
        left: 'center',
        textStyle: {
          fontSize: 18,
          fontWeight: 'bold'
        }
      },
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '暂无成绩数据',
          fill: '#999',
          fontSize: 16
        }
      }
    }
    gradeChartInstance.setOption(option)
    return
  }
  
  const examStages = data.exam_stages.map(stage => {
    const date = new Date(stage.date)
    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${stage.stage}\n${month}/${day}`
  })
  
  const series = data.courses.map(course => {
    const values = course.data.map(item => {
      if (item.has_data) {
        return {
          value: item.value,
          score: item.score,
          total_score: item.total_score,
          ratio: item.ratio,
          has_data: item.has_data,
          exam_stage: item.exam_stage,
          exam_date: item.exam_date
        }
      } else {
        return {
          value: null,
          score: null,
          total_score: null,
          ratio: null,
          has_data: false,
          exam_stage: item.exam_stage,
          exam_date: item.exam_date
        }
      }
    })
    
    return {
      name: course.course_name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: course.color
      },
      itemStyle: {
        color: course.color
      },
      data: values,
      connectNulls: false
    }
  })
  
  const option = {
    title: {
      text: `${data.student_name} 成绩比例趋势图`,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let html = `<strong>${params[0].axisValue.replace('\n', ' ')}</strong><br/>`
        params.forEach(param => {
          if (param.value !== null && param.value !== undefined && param.data && param.data.has_data) {
            const score = param.data.score !== null && param.data.score !== undefined ? param.data.score : 0
            const totalScore = param.data.total_score !== null && param.data.total_score !== undefined ? param.data.total_score : 0
            const ratio = param.data.ratio !== null && param.data.ratio !== undefined ? param.data.ratio : 0
            
            html += `${param.marker} ${param.seriesName}:<br/>`
            html += `&nbsp;&nbsp;当次考试成绩: ${Number(score).toFixed(1)}分<br/>`
            html += `&nbsp;&nbsp;当次科目总分: ${Number(totalScore).toFixed(1)}分<br/>`
            
            if (ratio !== null && ratio !== undefined) {
              html += `&nbsp;&nbsp;成绩比例: ${Number(ratio).toFixed(1)}%<br/>`
            } else {
              html += `&nbsp;&nbsp;成绩比例: 未计算（总分可能为0）<br/>`
            }
          } else {
            html += `${param.marker} ${param.seriesName}: 无数据<br/>`
          }
        })
        return html
      }
    },
    legend: {
      data: data.courses.map(c => c.course_name),
      top: 40,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: examStages,
      axisLabel: {
        interval: 0,
        rotate: 30,
        fontSize: 11
      },
      axisTick: {
        alignWithLabel: true
      }
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
    series: series
  }
  
  gradeChartInstance.setOption(option)
  
  if (!gradeChartInstance._resizeHandlerAdded) {
    window.addEventListener('resize', handleChartResize)
    gradeChartInstance._resizeHandlerAdded = true
  }
}

const handleChartResize = () => {
  if (gradeChartInstance) {
    gradeChartInstance.resize()
  }
}

const cleanupGradeChart = () => {
  if (gradeChartInstance) {
    gradeChartInstance.dispose()
    gradeChartInstance = null
  }
  window.removeEventListener('resize', handleChartResize)
}

watch(gradeCurveDialogVisible, (newVal) => {
  if (!newVal) {
    cleanupGradeChart()
  }
})

const initTopScrollbar = () => {
  nextTick(() => {
    if (!mainTableRef.value || !topScrollbarRef.value) {
      window.logger.warn('表格或滚动条ref未就绪')
      return
    }
    
    const tableEl = mainTableRef.value.$el
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    
    if (!scrollWrap) {
      window.logger.warn('找不到滚动容器')
      return
    }
    
    const contentWidth = scrollWrap.scrollWidth
    const containerWidth = scrollWrap.clientWidth
    
    window.logger.log('表格内容宽度:', contentWidth, '容器宽度:', containerWidth)
    
    if (contentWidth <= containerWidth) {
      topScrollbarRef.value.style.display = 'none'
      window.logger.log('内容未超出容器，隐藏滚动条')
      return
    }
    
    topScrollbarRef.value.style.display = 'block'
    scrollbarWidth.value = contentWidth
    window.logger.log('显示滚动条，宽度设置为:', contentWidth)
  })
}

const setupScrollSync = () => {
  window.logger.log('🔧 setupScrollSync 被调用')
  
  nextTick(() => {
    if (!mainTableRef.value || !topScrollbarRef.value) {
      window.logger.warn('❌ mainTableRef 或 topScrollbarRef 未就绪')
      return
    }
    
    const tableEl = mainTableRef.value.$el
    const headerWrapper = tableEl?.querySelector('.el-table__header-wrapper')
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    const fakeScrollbar = topScrollbarRef.value
    
    window.logger.log('🔍 查找元素:')
    window.logger.log('  headerWrapper:', headerWrapper)
    window.logger.log('  scrollWrap:', scrollWrap)
    window.logger.log('  fakeScrollbar:', fakeScrollbar)
    
    if (!headerWrapper || !scrollWrap || !fakeScrollbar) {
      window.logger.warn('❌ 找不到需要同步的元素')
      return
    }
    
    if (scrollHandler) {
      window.logger.log('🗑️ 清除旧的事件监听器')
      scrollWrap.removeEventListener('scroll', scrollHandler.wrapScroll)
      fakeScrollbar.removeEventListener('scroll', scrollHandler.fakeScroll)
    }
    
    const wrapScrollHandler = () => {
      const targetScroll = scrollWrap.scrollLeft
      
      if (Math.abs(fakeScrollbar.scrollLeft - targetScroll) > 1) {
        fakeScrollbar.scrollLeft = targetScroll
      }
      
      if (Math.abs(headerWrapper.scrollLeft - targetScroll) > 1) {
        headerWrapper.scrollLeft = targetScroll
      }
    }
    
    const fakeScrollHandler = () => {
      const targetScroll = fakeScrollbar.scrollLeft
      
      window.logger.log('📊 顶部滚动条滚动，目标值:', targetScroll)
      
      if (Math.abs(scrollWrap.scrollLeft - targetScroll) > 1) {
        scrollWrap.scrollLeft = targetScroll
        window.logger.log('✅ 同步 scrollWrap 到', targetScroll)
      }
      
      if (Math.abs(headerWrapper.scrollLeft - targetScroll) > 1) {
        headerWrapper.scrollLeft = targetScroll
        window.logger.log('✅ 同步 header 到', targetScroll)
      }
    }
    
    scrollWrap.addEventListener('scroll', wrapScrollHandler)
    fakeScrollbar.addEventListener('scroll', fakeScrollHandler)
    
    scrollHandler = {
      wrapScroll: wrapScrollHandler,
      fakeScroll: fakeScrollHandler
    }
    
    window.logger.log('✅ 滚动同步已设置成功')
  })
}

onMounted(async () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    currentUser.value = JSON.parse(userStr)
  }
  
  // 检查是否有来自智能指令的搜索参数
  const urlParams = new URLSearchParams(window.location.search)
  const searchQuery = urlParams.get('search')
  const relatedTo = urlParams.get('related_to')
  const viewDetail = urlParams.get('view_detail')
  const isActiveParam = urlParams.get('is_active')
  const sortFieldParam = urlParams.get('sort_field')
  const sortOrderParam = urlParams.get('sort_order')
  
  // 应用URL参数到筛选条件
  if (searchQuery) {
    searchKeyword.value = searchQuery
  }
  
  if (isActiveParam !== null) {
    isActiveFilter.value = isActiveParam === 'true' || isActiveParam === '1'
  }
  
  if (sortFieldParam) {
    sortField.value = sortFieldParam
    sortOrder.value = sortOrderParam || 'asc'
  }
  
  await fetchStudents()
  await fetchClasses()
  await fetchSchedules()

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

  // 确保加载所有学员数据到allStudents，以便班级悬浮信息能正确显示
  try {
    const allStudentsResponse = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    allStudents.value = allStudentsResponse.data.items || allStudentsResponse.data
  } catch (error) {
    window.logger.error('获取所有学员数据失败:', error)
  }
  // 如果有搜索参数，执行相关操作
  if (searchQuery) {
    setTimeout(() => {
      // 如果需要查看关联信息
      if (relatedTo && sessionStorage.getItem('smartCommandData')) {
        try {
          const smartData = JSON.parse(sessionStorage.getItem('smartCommandData'))
          if (smartData.target_path && smartData.target_label) {
            ElMessage.info(`已找到学员"${searchQuery}"，正在跳转到${smartData.target_label}...`)
            setTimeout(() => {
              window.location.href = `${smartData.target_path}?filter_by=student&filter_value=${encodeURIComponent(searchQuery)}`
            }, 1500)
          }
        } catch (e) {
          window.logger.error('解析智能指令数据失败', e)
        }
      }
      
      // 如果需要查看详情
      if (viewDetail === 'true') {
        setTimeout(() => {
          const firstStudent = students.value.find(s => s.name === searchQuery)
          if (firstStudent) {
            showEditDialog(firstStudent)
          }
        }, 1000)
      }
    }, 500)
  }
  
  // 检查是否需要自动打开新增对话框
  if (route.query.action === 'add') {
    showAddDialog()
  }
  
  // 检查是否需要自动打开编辑对话框
  if (route.query.action === 'edit' && route.query.id) {
    const studentId = parseInt(route.query.id)
    const student = students.value.find(s => s.id === studentId)
    if (student) {
      showEditDialog(student)
    } else {
      try {
        const response = await api.get(`/students/${studentId}`)
        if (response.data) {
          showEditDialog(response.data)
        }
      } catch (error) {
        window.logger.error('获取学员信息失败:', error)
        ElMessage.error('无法加载学员信息')
      }
    }
  }
  
  setTimeout(() => {
    initTopScrollbar()
    setupScrollSync()
  }, 200)
})

// 监听路由参数变化，支持从悬浮球等外部触发的操作
watch(() => route.query, (newQuery) => {
  if (newQuery.action === 'add') {
    showAddDialog()
  } else if (newQuery.action === 'edit' && newQuery.id) {
    const studentId = parseInt(newQuery.id)
    const student = students.value.find(s => s.id === studentId)
    if (student) {
      showEditDialog(student)
    } else {
      api.get(`/students/${studentId}`).then(response => {
        if (response.data) {
          showEditDialog(response.data)
        }
      }).catch(error => {
        window.logger.error('获取学员信息失败:', error)
        ElMessage.error('无法加载学员信息')
      })
    }
  }
  
  // 处理 is_active 过滤参数
  if (newQuery.is_active !== undefined) {
    const isActiveValue = newQuery.is_active === 'true' || newQuery.is_active === true
    isActiveFilter.value = isActiveValue
    fetchStudents()
  }
  
  // 处理 search 参数
  if (newQuery.search !== undefined) {
    searchKeyword.value = newQuery.search
    fetchStudents()
  }
  
  // 处理排序参数
  if (newQuery.sort_field !== undefined) {
    sortField.value = newQuery.sort_field
    sortOrder.value = newQuery.sort_order || 'asc'
    fetchStudents()
  }
}, { deep: true })

onUnmounted(() => {
  cleanupGradeChart()
  
  if (scrollHandler && mainTableRef.value) {
    const tableEl = mainTableRef.value.$el
    const scrollWrap = tableEl?.querySelector('.el-scrollbar__wrap.el-scrollbar__wrap--hidden-default')
    
    if (scrollWrap) {
      scrollWrap.removeEventListener('scroll', scrollHandler.wrapScroll)
    }
    if (topScrollbarRef.value) {
      topScrollbarRef.value.removeEventListener('scroll', scrollHandler.fakeScroll)
    }
  }
})

watch(students, () => {
  setTimeout(() => {
    initTopScrollbar()
    setupScrollSync()
  }, 200)
})
</script>

<style scoped>
.students-page {
  padding: 6px;
}

.fake-scrollbar {
  overflow-x: auto;
  overflow-y: hidden;
  height: 12px;
  margin-bottom: 5px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.fake-scrollbar .scrollbar-inner {
  height: 1px;
}

.fake-scrollbar::-webkit-scrollbar {
  height: 12px;
}

.fake-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 6px;
}

.fake-scrollbar::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 6px;
}

.fake-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.overlapping-slot {
  color: #f56c6c !important;
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
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
  transition: all 0.3s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-card :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 3px 3px rgba(0, 0, 0, 0.15);
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

.search-bar {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
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
    gap: 5px;
  }
  
  .card-header .button-group {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .search-bar {
    gap: 6px;
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
    width: 100px !important;
  }
  
  .el-table :deep(.el-table__fixed-right-patch) {
    width: 100px !important;
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