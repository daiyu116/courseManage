// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="fee-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('fee.title') }}</span>
          <div class="header-actions">
            <el-button type="info" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              {{ t('fee.goBack') }}
            </el-button>
            <el-button type="primary" @click="showAddDialog">{{ t('fee.addStudentFeeItem') }}</el-button>
          </div>
        </div>
      </template>

      <!-- 查询条件 -->
      <div class="search-bar">
       <el-input
          v-model="searchKeyword"
          :placeholder="t('fee.searchPlaceholder')"
          style="width: 200px"
          clearable
          @clear="resetFilters"
          @keyup.enter="handleSearch"
        />
        <el-button @click="handleSearch">
          <el-icon><Search /></el-icon>
        </el-button>
        
        <el-button type="warning" @click="showAlerts">
          <el-icon><Bell /></el-icon>
          {{ t('fee.feeReminder') }}
        </el-button>
        <el-button type="success" @click="exportPaymentRecords">
          <el-icon><Download /></el-icon>
          {{ t('fee.exportAllFeeItems') }}
        </el-button>
        <el-button type="danger" @click="exportFeeLogs">
          <el-icon><Download /></el-icon>
          {{ t('fee.exportAllFeeLogs') }}
        </el-button>
        
      </div>

      <!-- 课费项表格 -->
      <div class="fake-scrollbar" ref="topScrollbarRef">
        <div class="scrollbar-inner" :style="{ width: scrollbarWidth + 'px' }"></div>
      </div>
        <el-table :data="studentFees" stripe v-loading="loading" style="margin-top: 0" @sort-change="handleSortChange" ref="mainTableRef">
          <el-table-column prop="id" label="ID" width="80" sortable />
          <el-table-column prop="student_name" :label="t('fee.student')" width="120" sortable>
            <template #default="{ row }">
              <el-tooltip placement="top" effect="light">
                <template #content>
                  <div v-if="row.student_school">
                    <div><strong>{{ t('fee.school') }}：</strong>{{ row.student_school }}</div>
                  </div>
                  <div v-if="row.student_grade">
                    <div><strong>{{ t('fee.grade') }}：</strong>{{ row.student_grade }}</div>
                  </div>
                  <div v-if="row.student_contact_person">
                    <div><strong>{{ t('fee.contact') }}：</strong>{{ row.student_contact_person }}</div>
                  </div>
                  <div v-if="row.student_contact_phone">
                    <div><strong>{{ t('fee.contactInfo') }}：</strong>{{ row.student_contact_phone }}</div>
                  </div>
                  <div v-if="row.student_classes && row.student_classes.length > 0">
                    <div><strong>{{ t('fee.classLabel') }}：</strong></div>
                    <div v-for="class_ in row.student_classes" :key="class_.id" style="margin-left: 10px;">
                      {{ class_.name }}
                    </div>
                  </div>
                  <div>
                    <div><strong>{{ t('fee.isActiveLabel') }}：</strong>{{ row.student_is_active ? t('fee.reading') : t('fee.notReading') }}</div>
                  </div>
                </template>
                <span style="cursor: help; color: #409EFF;">{{ row.student_name }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="course_name" :label="t('fee.course')" width="120" sortable>
            <template #default="{ row }">
              <el-tooltip placement="top" effect="light">
                <template #content>
                  <div v-if="row.course_teachers && row.course_teachers.length > 0">
                    <div><strong>{{ t('fee.teacherLabel') }}：</strong></div>
                    <div v-for="teacher in row.course_teachers" :key="teacher.id" style="margin-left: 10px;">
                      {{ teacher.name }}
                      <div v-if="teacher.contact_phone" style="margin-left: 10px; color: #909399;">
                        {{ t('fee.contactPhoneLabel') }}：{{ teacher.contact_phone }}
                      </div>
                      <div v-if="teacher.email" style="margin-left: 10px; color: #909399;">
                        {{ t('fee.emailLabel') }}：{{ teacher.email }}
                      </div>
                    </div>
                  </div>
                </template>
                <span style="cursor: help; color: #409EFF;">{{ row.course_name }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="start_date" :label="t('fee.startDate')" width="120" sortable>
            <template #default="{ row }">
              {{ formatDate(row.start_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="remaining_hours" :label="t('fee.remainingHours')" width="180" sortable>
            <template #default="{ row }">
              <span :style="{ 
                color: row.remaining_hours <= row.alert_threshold ? '#ff0000' : '#67C23A',
                fontWeight: 'bold',
                fontSize: '16px',
                display: 'inline-block',
                padding: '4px 8px',
                borderRadius: '4px',
                backgroundColor: row.remaining_hours <= row.alert_threshold ? '#fef0f0' : '#f0f9ff',
                border: row.remaining_hours <= row.alert_threshold ? '1px solid #f56c6c' : '1px solid #67C23A'
              }">
                {{ row.remaining_hours.toFixed(2) }} {{ t('fee.hours') }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="consumed_hours" :label="t('fee.consumedHours')" width="160" sortable>
            <template #default="{ row }">
              {{ row.consumed_hours.toFixed(2) }} {{ t('fee.hours') }}
            </template>
          </el-table-column>
          <el-table-column prop="hourly_fee" :label="t('fee.hourlyFee')" width="140" sortable>
            <template #default="{ row }">
              ¥{{ row.hourly_fee.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="current_remaining_amount" :label="t('fee.currentRemainingAmount')" width="270" sortable>
            <template #default="{ row }">
              <span :style="{ 
                color: (row.total_actual_amount - row.total_refund_amount) <= row.alert_threshold * row.hourly_fee ? '#ff0000' : '#67C23A',
                fontWeight: 'bold',
                fontSize: '16px',
                display: 'inline-block',
                padding: '4px 8px',
                borderRadius: '4px',
                backgroundColor: (row.total_actual_amount - row.total_refund_amount) <= row.alert_threshold * row.hourly_fee ? '#fef0f0' : '#f0f9ff',
                border: (row.total_actual_amount - row.total_refund_amount) <= row.alert_threshold * row.hourly_fee ? '1px solid #f56c6c' : '1px solid #67C23A'
              }">
                ¥{{ (row.total_actual_amount - row.total_refund_amount).toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="total_receivable_amount" :label="t('fee.totalReceivableAmount')" width="140" sortable>
            <template #default="{ row }">
              ¥{{ row.total_receivable_amount.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="total_actual_amount" :label="t('fee.totalActualAmount')" width="140" sortable>
            <template #default="{ row }">
              ¥{{ row.total_actual_amount.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="total_refund_amount" :label="t('fee.totalRefundAmountLabel')" width="140" sortable>
            <template #default="{ row }">
              ¥{{ row.total_refund_amount.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="alert_threshold" :label="t('fee.alertThreshold')" width="160" sortable>
            <template #default="{ row }">
              {{ row.alert_threshold.toFixed(2) }} {{ t('fee.hours') }}
            </template>
          </el-table-column>
          <el-table-column :label="t('fee.status')" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? t('fee.enabled') : t('fee.disabled') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('fee.action')" width="115" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="showEditDialog(row)">{{ t('fee.editParams') }}</el-button>
              <el-button size="small" @click="showPaymentDialog(row)">{{ t('fee.collectPayment') }}</el-button>
              <el-button size="small" @click="showRefundDialog(row)">{{ t('fee.refund') }}</el-button>
              <el-button size="small" @click="showFeeLogsDialog(row)">{{ t('fee.viewLogs') }}</el-button>
              <el-button size="small" type="warning" @click="debugAutoConsume(row)">{{ t('fee.debug') }}</el-button>
              <el-button size="small" type="success" @click="triggerAutoConsume(row)">{{ t('fee.triggerConsume') }}</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">{{ t('fee.delete') }}</el-button>
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

    <!-- 新增学员课费项对话框 -->
    <el-dialog v-model="addDialogVisible" :title="t('fee.addStudentFeeItem')" width="600px" draggable>
      <el-form :model="addForm" :rules="addFormRules" ref="addFormRef" label-width="140px">
        <el-form-item :label="t('fee.student')" prop="student_id">
          <el-select v-model="addForm.student_id" filterable :placeholder="t('fee.selectStudent')" style="width: 100%">
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="student.name"
              :value="student.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('fee.student') }}：</strong>{{ student.name }}</div>
                    <div v-if="student.school"><strong>{{ t('fee.school') }}：</strong>{{ student.school }}</div>
                    <div v-if="student.grade"><strong>{{ t('fee.grade') }}：</strong>{{ student.grade }}</div>
                    <div v-if="student.classes && student.classes.length > 0">
                      <strong>{{ t('fee.classLabel') }}：</strong>
                      <div v-for="cls in student.classes" :key="cls.id" style="margin-left: 10px;">
                        {{ cls.name }}
                      </div>
                    </div>
                    <div v-else><strong>{{ t('fee.classLabel') }}：</strong>{{ t('fee.noClass') }}</div>
                    <div><strong>{{ t('fee.isActiveLabel') }}：</strong>{{ student.is_active ? t('fee.yes') : t('fee.no') }}</div>
                  </div>
                </template>
                <span>{{ student.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fee.course')" prop="course_id">
          <el-select v-model="addForm.course_id" filterable :placeholder="t('fee.selectCourse')" style="width: 100%">
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.parent_course_name ? course.parent_course_name + ' > ' + course.name : course.name"
              :value="course.id"
            >
              <el-tooltip placement="right" :show-after="200">
                <template #content>
                  <div style="min-width: 200px;">
                    <div><strong>{{ t('fee.course') }}：</strong>{{ course.name }}</div>
                    <div v-if="course.parent_course_name"><strong>{{ t('courses.parentCourse') }}：</strong>{{ course.parent_course_name }}</div>
                    <div v-if="course.teachers && course.teachers.length > 0">
                      <strong>{{ t('fee.teacherLabel') }}：</strong>
                      <div v-for="teacher in course.teachers" :key="teacher.id" style="margin-left: 10px;">
                        {{ teacher.name }}
                        <span v-if="teacher.contact_phone" style="color: #999; font-size: 12px;">（{{ teacher.contact_phone }}）</span>
                        <span v-if="teacher.email" style="color: #999; font-size: 12px;">（{{ teacher.email }}）</span>
                      </div>
                    </div>
                    <div v-else><strong>{{ t('fee.teacherLabel') }}：</strong>{{ t('fee.noClass') }}</div>
                  </div>
                </template>
                <span>{{ course.name }}</span>
              </el-tooltip>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fee.startDate')" prop="start_date">
          <el-date-picker
            v-model="addForm.start_date"
            type="date"
            :placeholder="t('fee.selectStartDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('fee.hourlyFee')" prop="hourly_fee">
          <el-input-number v-model="addForm.hourly_fee" :min="0" :precision="2" style="width: 100%" @change="calculateAddPaymentAmount" :value-on-clear="0" />
        </el-form-item>
        <el-form-item :label="t('fee.lessonCount')" prop="lesson_count">
          <el-input-number v-model="addForm.lesson_count" :min="0" :step="1" :precision="0" style="width: 100%" @change="calculateAddPaymentAmount" :value-on-clear="0" />
          <span style="margin-left: 10px; color: #999; font-size: 12px;">{{ t('fee.lessonCountTip') }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.receivableAmount')">
          <span style="color: #409EFF; font-weight: bold;">¥{{ addForm.receivable_amount.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.discountAmountLabel')" prop="discount_amount">
          <el-input-number v-model="addForm.discount_amount" :min="0" :precision="2" style="width: 100%" @change="calculateAddActualAmount" :value-on-clear="0" />
        </el-form-item>
        <el-form-item :label="t('fee.actualAmount')">
          <span style="color: #67C23A; font-weight: bold;">¥{{ addForm.actual_amount.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.chargeDate')" prop="payment_date">
          <el-date-picker
            v-model="addForm.payment_date"
            type="date"
            :placeholder="t('fee.selectChargeDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('fee.chargeMethod')" prop="payment_method">
          <el-select v-model="addForm.payment_method" :placeholder="t('fee.selectPaymentMethod')" style="width: 100%">
            <el-option :label="t('fee.wechat')" value="微信" />
            <el-option :label="t('fee.alipay')" value="支付宝" />
            <el-option :label="t('fee.cash')" value="现金" />
            <el-option :label="t('fee.bankCard')" value="银行卡" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fee.alertThresholdLabel')" prop="alert_threshold">
          <el-input-number v-model="addForm.alert_threshold" :min="0" :precision="1" style="width: 100%" :value-on-clear="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">{{ t('fee.cancel') }}</el-button>
        <el-button type="primary" @click="handleAdd" :loading="isSubmitting">{{ t('fee.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 编辑课费项参数对话框 -->
    <el-dialog v-model="editDialogVisible" :title="t('fee.editFeeParams')" width="600px" draggable>
      <el-form :model="editForm" :rules="editFormRules" ref="editFormRef" label-width="140px">
        <el-form-item :label="t('fee.student')">
          <span>{{ currentFee.student_name }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.course')">
          <span>{{ currentFee.course_name }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.startDate')" prop="start_date">
          <el-date-picker
            v-model="editForm.start_date"
            type="date"
            :placeholder="t('fee.selectStartDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('fee.hourlyFee')" prop="hourly_fee">
          <el-input-number v-model="editForm.hourly_fee" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('fee.totalActualAmountLabel')">
          <span style="color: #409EFF; font-weight: bold;">¥{{ currentFee.total_amount.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.totalRemainingAmount')">
          <span :style="{ color: currentFee.remaining_amount <= currentFee.alert_threshold * currentFee.hourly_fee ? 'red' : 'green', fontWeight: 'bold' }">
            ¥{{ currentFee.remaining_amount.toFixed(2) }}
          </span>
        </el-form-item>
        <el-form-item :label="t('fee.totalRemainingHours')">
          <span :style="{ color: currentFee.remaining_hours <= currentFee.alert_threshold ? 'red' : 'green', fontWeight: 'bold' }">
            {{ currentFee.remaining_hours.toFixed(2) }} {{ t('fee.hours') }}
          </span>
        </el-form-item>
        <el-form-item :label="t('fee.alertThresholdLabel')" prop="alert_threshold">
          <el-input-number v-model="editForm.alert_threshold" :min="0" :precision="1" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('fee.status')" prop="is_active">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ t('fee.cancel') }}</el-button>
        <el-button type="primary" @click="handleEdit">{{ t('fee.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 追缴对话框 -->
    <el-dialog v-model="paymentDialogVisible" :title="t('fee.collectPaymentTitle')" width="600px" draggable>
      <el-form :model="paymentForm" :rules="paymentRules" ref="paymentFormRef" label-width="140px">
        <el-form-item :label="t('fee.student')">
          <span>{{ currentFee.student_name }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.course')">
          <span>{{ currentFee.course_name }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.lessonCount')" prop="lesson_count">
          <el-input-number v-model="paymentForm.lesson_count" :min="0" :step="1" :precision="0" style="width: 100%" @change="calculatePaymentAmount" :value-on-clear="0" />
          <span style="margin-left: 10px; color: #999; font-size: 12px;">{{ t('fee.lessonCountTipShort') }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.currentReceivable')">
          <span style="color: #409EFF; font-weight: bold;">¥{{ paymentForm.receivable_amount.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.currentDiscount')" prop="discount_amount">
          <el-input-number v-model="paymentForm.discount_amount" :min="0" :precision="2" style="width: 100%" @change="calculateActualAmount" :value-on-clear="0" />
        </el-form-item>
        <el-form-item :label="t('fee.currentActual')">
          <span style="color: #67C23A; font-weight: bold;">¥{{ paymentForm.actual_amount.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.chargeDate')" prop="payment_date">
          <el-date-picker
            v-model="paymentForm.payment_date"
            type="date"
            :placeholder="t('fee.selectChargeDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('fee.paymentMethodLabel')" prop="payment_method">
          <el-select v-model="paymentForm.payment_method" :placeholder="t('fee.selectPaymentMethod')" style="width: 100%">
            <el-option :label="t('fee.wechat')" value="微信" />
            <el-option :label="t('fee.alipay')" value="支付宝" />
            <el-option :label="t('fee.cash')" value="现金" />
            <el-option :label="t('fee.bankCard')" value="银行卡" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fee.remark')">
          <el-input v-model="paymentForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paymentDialogVisible = false">{{ t('fee.cancel') }}</el-button>
        <el-button type="primary" @click="handlePayment">{{ t('fee.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 退费对话框 -->
    <el-dialog v-model="refundDialogVisible" :title="t('fee.refundTitle')" width="500px" draggable>
      <el-form :model="refundForm" :rules="refundRules" ref="refundFormRef" label-width="120px">
        <el-form-item :label="t('fee.student')">
          <span>{{ currentFee.student_name }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.course')">
          <span>{{ currentFee.course_name }}</span>
        </el-form-item>
        <el-form-item :label="t('fee.remainingAmountLabel')">
          <el-input :value="'¥' + currentFee.remaining_amount.toFixed(2)" disabled />
        </el-form-item>
        <el-form-item :label="t('fee.refundAmount')" prop="amount">
          <el-input-number v-model="refundForm.amount" :min="0" :max="currentFee.remaining_amount" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('fee.refundDate')" prop="refund_date">
          <el-date-picker
            v-model="refundForm.refund_date"
            type="date"
            :placeholder="t('fee.selectRefundDate')"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('fee.refundMethod')" prop="refund_method">
          <el-select v-model="refundForm.refund_method" :placeholder="t('fee.selectRefundMethod')" style="width: 100%">
            <el-option :label="t('fee.wechat')" value="微信" />
            <el-option :label="t('fee.alipay')" value="支付宝" />
            <el-option :label="t('fee.cash')" value="现金" />
            <el-option :label="t('fee.bankCard')" value="银行卡" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fee.refundReason')" prop="refund_reason">
          <el-input v-model="refundForm.refund_reason" type="textarea" :rows="3" :placeholder="t('fee.refundReasonRequired')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refundDialogVisible = false">{{ t('fee.cancel') }}</el-button>
        <el-button type="primary" @click="handleRefund">{{ t('fee.confirm') }}</el-button>
      </template>
    </el-dialog>
    <!-- 课时费记录对话框 -->
    <el-dialog v-model="feeLogsDialogVisible" width="90%" draggable>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>{{ t('fee.feeLogsTitle') }}</span>
          <el-button type="success" @click="exportStudentFeeLogs" :loading="exportLoading">
            <el-icon><Download /></el-icon>
            {{ t('fee.exportStudentFeeLogs') }}
          </el-button>
        </div>
      </template>
      <el-table :data="feeLogs" stripe v-loading="feeLogsLoading" style="margin-top: 20px" @sort-change="handleFeeLogsSortChange">
        <el-table-column prop="created_at" :label="t('fee.logDate')" width="150" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="student_name" :label="t('fee.student')" width="120" />
        <el-table-column prop="course_name" :label="t('fee.course')" width="120" />
        <el-table-column prop="log_type" :label="t('fee.logType')" width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="getLogTypeColor(row.log_type)">
              {{ getLogTypeText(row.log_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" :label="t('fee.logAmount')" width="120" sortable>
          <template #default="{ row }">
            <span :style="{ color: row.amount > 0 ? 'green' : 'red' }">
              {{ row.amount > 0 ? '+' : '' }}¥{{ row.amount.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="hours" :label="t('fee.logHours')" width="120" sortable>
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light" v-if="row.log_type === 'consume' && (row.schedule_date || row.teacher_name || row.class_name || row.room_name || row.content_feedback)">
              <template #content>
                <div v-if="row.schedule_date">
                  <div><strong>{{ t('fee.scheduleDate') }}：</strong>{{ row.schedule_date }}</div>
                </div>
                <div v-if="row.schedule_time">
                  <div><strong>{{ t('fee.time') }}：</strong>{{ row.schedule_time }}</div>
                </div>
                <div v-if="row.teacher_name">
                  <div><strong>{{ t('fee.teacherLabel') }}：</strong>{{ row.teacher_name }}</div>
                </div>
                <div v-if="row.class_name">
                  <div><strong>{{ t('fee.classLabel') }}：</strong>{{ row.class_name }}</div>
                </div>
                <div>
                  <div><strong>{{ t('fee.student') }}：</strong>{{ row.student_name }}</div>
                </div>
                <div v-if="row.room_name">
                  <div><strong>{{ t('fee.room') }}：</strong>{{ row.room_name }}</div>
                </div>
                <div v-if="row.content_feedback">
                  <el-tooltip placement="top" effect="light">
                    <template #content>
                      <div v-for="(item, index) in parseContentFeedbackForTooltip(row.content_feedback)" :key="index">
                        <div v-if="item.label === t('fee.contentLabel')">
                          <div><strong>{{ t('fee.courseContent') }}：</strong>{{ item.content }}</div>
                        </div>
                        <div v-else-if="item.label === t('fee.homeworkLabel')">
                          <div><strong>{{ t('fee.homework') }}：</strong>{{ item.content }}</div>
                        </div>
                        <div v-else-if="item.label === t('fee.noteLabel')">
                          <div><strong>{{ t('fee.note') }}：</strong>{{ item.content || t('fee.none') }}</div>
                        </div>
                      </div>
                    </template>
                    <span style="cursor: help; color: #409EFF;">{{ t('fee.viewCourseFeedback') }}</span>
                  </el-tooltip>
                </div>
              </template>
              <span style="cursor: help; color: #409EFF;">
                {{ row.hours > 0 ? row.hours.toFixed(2) + ' ' + t('fee.hours') : '-' }}
              </span>
            </el-tooltip>
            <span v-else>{{ row.hours > 0 ? row.hours.toFixed(2) + ' ' + t('fee.hours') : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remaining_amount" :label="t('fee.remainingAmountLabel')" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.remaining_amount < 0 ? 'red' : 'green' }">
              ¥{{ row.remaining_amount.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="remaining_hours" :label="t('fee.remainingHoursLabel')" width="120">
          <template #default="{ row }">
            {{ row.remaining_hours.toFixed(2) }} {{ t('fee.hours') }}
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="t('fee.logDescription')" width="300" show-overflow-tooltip />
      </el-table>
      <el-pagination
        v-model:current-page="feeLogsPagination.currentPage"
        v-model:page-size="feeLogsPagination.pageSize"
        :page-sizes="[15, 30, 50, 100]"
        :total="feeLogsPagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handleFeeLogsPageChange"
        @size-change="handleFeeLogsSizeChange"
        style="margin-top: 20px; justify-content: center; display: flex;"
      />
    </el-dialog>
    <!-- 课费提醒对话框 -->
    <el-dialog v-model="alertsDialogVisible" :title="t('fee.feeReminder')" width="80%" draggable>
      <el-table :data="alerts" stripe>
        <el-table-column prop="student_name" :label="t('fee.student')" width="120" />
        <el-table-column prop="course_name" :label="t('fee.course')" width="120" />
        <el-table-column prop="remaining_hours" :label="t('fee.totalRemainingHours')" width="120">
          <template #default="{ row }">
            <span style="color: red;">
              {{ row.remaining_hours.toFixed(2) }} {{ t('fee.hours') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="remaining_amount" :label="t('fee.totalRemainingAmount')" width="120">
          <template #default="{ row }">
            <span style="color: red;">
              ¥{{ row.remaining_amount.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="alert_threshold" :label="t('fee.alertThresholdHours')" width="120">
          <template #default="{ row }">
            {{ row.alert_threshold.toFixed(2) }} {{ t('fee.hours') }}
          </template>
        </el-table-column>
        <el-table-column :label="t('fee.action')" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="showPaymentDialog(row)">{{ t('fee.charge') }}</el-button>
            <el-button size="small" @click="showEditThresholdDialog(row)">{{ t('fee.modifyThreshold') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 修改预警阈值对话框 -->
    <el-dialog v-model="thresholdDialogVisible" :title="t('fee.modifyThresholdTitle')" width="400px">
      <el-form :model="thresholdForm" :rules="thresholdRules" ref="thresholdFormRef" label-width="120px">
        <el-form-item :label="t('fee.student')">
          <el-input v-model="currentAlert.student_name" disabled />
        </el-form-item>
        <el-form-item :label="t('fee.course')">
          <el-input v-model="currentAlert.course_name" disabled />
        </el-form-item>
        <el-form-item :label="t('fee.alertThresholdLabel')" prop="alert_threshold">
          <el-input-number v-model="thresholdForm.alert_threshold" :min="0" :precision="2" style="width: 100%" />
          <span style="margin-left: 10px; color: #999; font-size: 12px;">
            {{ t('fee.hours') }}
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="thresholdDialogVisible = false">{{ t('fee.cancel') }}</el-button>
        <el-button type="primary" @click="handleUpdateThreshold">{{ t('fee.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 自动消耗调试结果对话框 -->
    <el-dialog 
      v-model="debugDialogVisible" 
      :title="t('fee.debugTitle')" 
      width="80%" 
      :close-on-click-modal="false"
      draggable
    >
      <div class="debug-info">
        <el-descriptions :column="3" border>
          <el-descriptions-item :label="t('fee.studentId')">{{ debugData.student_id }}</el-descriptions-item>
          <el-descriptions-item :label="t('fee.courseId')">{{ debugData.course_id }}</el-descriptions-item>
          <el-descriptions-item :label="t('fee.completedSchedules')">{{ debugData.totalSchedules }}</el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div class="debug-table-container">
        <el-table 
          :data="paginatedDebugChecks" 
          border 
          stripe 
          max-height="500"
          style="width: 100%"
        >
          <el-table-column prop="schedule_id" :label="t('fee.scheduleId')" width="120" fixed />
          <el-table-column prop="start_date" :label="t('fee.scheduleDate')" width="120" />
          <el-table-column prop="fee_start_date" :label="t('fee.startDate')" width="180" />
          <el-table-column :label="t('fee.dateCheck')" width="180">
            <template #default="{ row }">
              <el-tag :type="row.date_check && row.date_check.includes('通过') ? 'success' : 'info'" size="small">
                {{ row.date_check || '-' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('fee.studentParticipation')" width="100">
            <template #default="{ row }">
              <el-tag :type="row.student_in_schedule?.in_list ? 'success' : 'danger'" size="small">
                {{ row.student_in_schedule?.in_list ? t('fee.yes') : t('fee.no') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('fee.participantList')" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.student_in_schedule?.scheduled_students?.join(', ') || '-' }}
            </template>
          </el-table-column>
          <el-table-column :label="t('fee.existingConsumeLog')" width="120">
            <template #default="{ row }">
              <el-tag :type="row.existing_log?.exists ? 'warning' : 'info'" size="small">
                {{ row.existing_log?.exists ? `${t('fee.yes')} (ID:${row.existing_log.log_id})` : t('fee.no') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('fee.shouldConsume')" width="120" fixed="right">
            <template #default="{ row }">
              <el-tag :type="row.should_consume ? 'success' : 'info'" size="small" effect="dark">
                {{ row.should_consume ? '✓ ' + t('fee.yes') : '✗ ' + t('fee.no') }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <el-pagination
          v-model:current-page="debugPagination.currentPage"
          v-model:page-size="debugPagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="debugPagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handleDebugPageChange"
          @size-change="handleDebugSizeChange"
          style="margin-top: 20px; justify-content: center; display: flex;"
        />
      </div>
      
      <template #footer>
        <el-button @click="debugDialogVisible = false">{{ t('fee.close') }}</el-button>
        <el-button type="primary" @click="triggerAutoConsumeFromDebug">{{ t('fee.triggerConsume') }}</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Search, Download, Bell } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const mainTableRef = ref(null)
const topScrollbarRef = ref(null)
const scrollbarWidth = ref(0)
let scrollHandler = null
const exportLoading = ref(false)

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const isSubmitting = ref(false)
const studentFees = ref([])
const searchKeyword = ref('')
const addDialogVisible = ref(false)
const addFormRef = ref(null)
const addForm = ref({
  student_id: null,
  course_id: null,
  start_date: null,
  hourly_fee: 100,
  lesson_count: 0,
  receivable_amount: 0,
  discount_amount: 0,
  actual_amount: 0,
  payment_method: '',
  payment_date: '',
  alert_threshold: 5
})

const addFormRules = {
  student_id: [{ required: true, message: t('fee.selectStudent'), trigger: 'change' }],
  course_id: [{ required: true, message: t('fee.selectCourse'), trigger: 'change' }],
  start_date: [{ required: true, message: t('fee.selectStartDate'), trigger: 'change' }],
  hourly_fee: [{ required: true, message: t('fee.hourlyFeeRequired'), trigger: 'blur' }],
  lesson_count: [{ required: true, message: t('fee.lessonCountRequired'), trigger: 'blur' }],
  payment_method: [{ required: true, message: t('fee.paymentMethodRequired'), trigger: 'change' }],
  payment_date: [{ required: true, message: t('fee.paymentDateRequired'), trigger: 'change' }],
  alert_threshold: [{ required: true, message: t('fee.alertThresholdRequired'), trigger: 'blur' }]
}

const goBack = () => {
  router.back()
}

const calculateAddPaymentAmount = () => {
  const lessonCount = addForm.value.lesson_count || 0
  const hourlyFee = addForm.value.hourly_fee || 0
  // 每次应收 = 课节数 * 2 * 课时费/小时
  addForm.value.receivable_amount = lessonCount * 2 * hourlyFee
  calculateAddActualAmount()
}

const calculateAddActualAmount = () => {
  // 每次实收 = 每次应收 - 本次优惠
  addForm.value.actual_amount = Math.max(0, addForm.value.receivable_amount - (addForm.value.discount_amount || 0))
}
const calculatePaymentAmount = () => {
  const lessonCount = paymentForm.value.lesson_count || 0
  const hourlyFee = currentFee.value.hourly_fee || 0
  // 每次应收 = 课节数 * 2 * 课时费/小时
  paymentForm.value.receivable_amount = lessonCount * 2 * hourlyFee
  calculateActualAmount()
}

const calculateActualAmount = () => {
  // 每次实收 = 每次应收 - 本次优惠
  paymentForm.value.actual_amount = Math.max(0, paymentForm.value.receivable_amount - (paymentForm.value.discount_amount || 0))
}


const editDialogVisible = ref(false)
const editFormRef = ref(null)
const editForm = ref({
  start_date: null,
  hourly_fee: 100,
  alert_threshold: 5,
  is_active: true
})

const editFormRules = {
  start_date: [{ required: true, message: t('fee.selectStartDate'), trigger: 'change' }],
  hourly_fee: [{ required: true, message: t('fee.hourlyFeeRequired'), trigger: 'blur' }],
  alert_threshold: [{ required: true, message: t('fee.alertThresholdRequired'), trigger: 'blur' }]
}

const students = ref([])
const courses = ref([])

const paymentDialogVisible = ref(false)
const paymentFormRef = ref(null)
const paymentForm = ref({
  student_id: null,
  course_id: null,
  lesson_count: 0,
  receivable_amount: 0,
  discount_amount: 0,
  actual_amount: 0,
  payment_method: '',
  payment_date: '',
  description: ''
})
 
const paymentRules = {
  lesson_count: [{ required: true, message: t('fee.lessonCountRequired'), trigger: 'blur' }],
  payment_method: [{ required: true, message: t('fee.paymentMethodRequired'), trigger: 'change' }],
  payment_date: [{ required: true, message: t('fee.paymentDateRequired'), trigger: 'change' }]
}
const refundDialogVisible = ref(false)
const refundFormRef = ref(null)
const refundForm = ref({
  student_id: null,
  course_id: null,
  amount: 0,
  refund_date: '',
  refund_method: '',
  refund_reason: ''
})

const refundRules = {
  amount: [{ required: true, message: t('fee.refundAmountRequired'), trigger: 'blur' }],
  refund_date: [{ required: true, message: t('fee.refundDateRequired'), trigger: 'change' }],
  refund_method: [{ required: true, message: t('fee.refundMethodRequired'), trigger: 'change' }],
  refund_reason: [{ required: true, message: t('fee.refundReasonRequired'), trigger: 'blur' }]
}

const currentFee = ref({})

const feeLogsDialogVisible = ref(false)
const feeLogsLoading = ref(false)
const feeLogs = ref([])

const alertsDialogVisible = ref(false)
const alerts = ref([])
const currentRow = ref({})
const sortField = ref('')
const sortOrder = ref('asc')
const feeLogsSortField = ref('')
const feeLogsSortOrder = ref('asc')
const thresholdDialogVisible = ref(false)
const thresholdFormRef = ref(null)
const thresholdForm = ref({
  alert_threshold: 6
})

const pagination = ref({
  currentPage: 1,
  pageSize: 15,
  total: 0
})

// 添加分页处理函数
const handlePageChange = (page) => {
  pagination.value.currentPage = page
  fetchStudentFees()
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchStudentFees()
}

const handleSearch = () => {
  pagination.value.currentPage = 1
  fetchStudentFees()
}

// 调试数据分页 - 计算属性
const paginatedDebugChecks = computed(() => {
  const scheduleChecks = debugData.value.checks.filter(c => c.schedule_id)
  debugPagination.value.total = scheduleChecks.length
  
  const start = (debugPagination.value.currentPage - 1) * debugPagination.value.pageSize
  const end = start + debugPagination.value.pageSize
  
  return scheduleChecks.slice(start, end)
})

const handleDebugPageChange = (page) => {
  debugPagination.value.currentPage = page
}

const handleDebugSizeChange = (size) => {
  debugPagination.value.pageSize = size
  debugPagination.value.currentPage = 1
}

// 课时费记录分页处理
const handleFeeLogsPageChange = (page) => {
  feeLogsPagination.value.currentPage = page
  if (currentRow.value) {
    showFeeLogsDialog(currentRow.value)
  }
}

const handleFeeLogsSizeChange = (size) => {
  feeLogsPagination.value.pageSize = size
  feeLogsPagination.value.currentPage = 1
  if (currentRow.value) {
    showFeeLogsDialog(currentRow.value)
  }
}

const debugAutoConsume = async (row) => {
  try {
    ElMessage.info(t('fee.checkingAutoConsume'))
    const response = await api.get(`/fees/debug-auto-consume/${row.student_id}/${row.course_id}`)
    
    window.logger.log('=== 自动消耗调试信息 ===', response.data)
    
    // 统计完训课程安排数量
    const scheduleCheck = response.data.checks.find(c => c.count !== undefined)
    const totalSchedules = scheduleCheck ? scheduleCheck.count : 0
    
    debugData.value = {
      student_id: response.data.student_id,
      course_id: response.data.course_id,
      totalSchedules: totalSchedules,
      checks: response.data.checks
    }
    
    // 重置分页
    debugPagination.value.currentPage = 1
    debugPagination.value.pageSize = 20
    
    currentDebugRow.value = row
    debugDialogVisible.value = true
  } catch (error) {
    window.logger.error('调试失败:', error)
    ElMessage.error(t('fee.debugFailed') + ': ' + (error.response?.data?.detail || error.message))
  }
}

const triggerAutoConsumeFromDebug = async () => {
  if (!currentDebugRow.value) return
  
  try {
    await ElMessageBox.confirm(t('fee.confirmTriggerConsume'), t('fee.confirmTitle'), {
      confirmButtonText: t('fee.confirm'),
      cancelButtonText: t('fee.cancel'),
      type: 'warning'
    })
    
    ElMessage.info(t('fee.triggeringAutoConsume'))
    const response = await api.post(`/fees/trigger-auto-consume/${currentDebugRow.value.id}`)
    
    ElMessage.success(response.data.message)
    debugDialogVisible.value = false
    fetchStudentFees()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('触发消耗失败:', error)
      ElMessage.error(t('fee.triggerConsumeFailed') + ': ' + (error.response?.data?.detail || error.message))
    }
  }
}

// 手动触发课时消耗检查并补录消耗记录
const triggerAutoConsume = async (row) => {
  try {
    await ElMessageBox.confirm(t('fee.confirmTriggerConsume'), t('fee.confirmTitle'), {
      confirmButtonText: t('fee.confirm'),
      cancelButtonText: t('fee.cancel'),
      type: 'warning'
    })
    
    ElMessage.info(t('fee.triggeringAutoConsume'))
    const response = await api.post(`/fees/trigger-auto-consume/${row.id}`)
    
    ElMessage.success(response.data.message)
    fetchStudentFees()
  } catch (error) {
    if (error !== 'cancel') {
      window.logger.error('触发消耗失败:', error)
      ElMessage.error(t('fee.triggerConsumeFailed') + ': ' + (error.response?.data?.detail || error.message))
    }
  }
}

const thresholdRules = {
  alert_threshold: [{ required: true, message: t('fee.alertThresholdRequired'), trigger: 'blur' }]
}

const currentAlert = ref({})
const debugDialogVisible = ref(false)
const debugData = ref({
  student_id: null,
  course_id: null,
  totalSchedules: 0,
  checks: []
})
const currentDebugRow = ref(null)
// debug数据分页
const debugPagination = ref({
  currentPage: 1,
  pageSize: 20,
  total: 0
})
// 缴费记录分页
const feeLogsPagination = ref({
  currentPage: 1,
  pageSize: 15,
  total: 0
})

// 导出单个学员课时费记录
const exportStudentFeeLogs = async () => {
  if (!currentRow.value) {
    ElMessage.warning(t('fee.selectStudentFirst'))
    return
  }
  
  exportLoading.value = true
  try {
    const params = {
      student_id: currentRow.value.student_id,
      course_id: currentRow.value.course_id,
      lang: locale.value
    }
    const response = await api.get('/fees/export-fee-logs', {
      params,
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const studentName = currentRow.value.student_name || t('fee.defaultStudentName')
    const courseName = currentRow.value.course_name || t('fee.defaultCourseName')
    link.setAttribute('download', `${studentName}_${courseName}_${t('fee.feeRecordExport')}_${new Date().toLocaleDateString('zh-CN')}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(t('fee.exportSuccessMsg'))
  } catch (error) {
    window.logger.error('导出失败:', error)
    ElMessage.error(t('fee.exportFailed'))
  } finally {
    exportLoading.value = false
  }
}
const fetchStudentFees = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.value.currentPage - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value
    }
    const response = await api.get('/fees/student-fees', { params })
    studentFees.value = response.data.items
    pagination.value.total = response.data.total
  } catch (error) {
    window.logger.error('获取课时费记录失败:', error)
    ElMessage.error(t('fee.fetchFeeRecordsFailed'))
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  searchKeyword.value = ''
  sortField.value = ''
  sortOrder.value = 'asc'
  pagination.value.currentPage = 1
  fetchStudentFees()
}

const handleSortChange = ({ prop, order }) => {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  pagination.value.currentPage = 1
  fetchStudentFees()
}

const fetchStudents = async () => {
  try {
    const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    students.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取学员列表失败:', error)
  }
}

const fetchCourses = async () => {
  try {
    const response = await api.get('/courses', { params: { skip: 0, limit: 100000 } })
    courses.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取科目列表失败:', error)
  }
}

const showAddDialog = () => {
  addForm.value = {
    student_id: null,
    course_id: null,
    start_date: null,
    hourly_fee: 100,
    lesson_count: 0,
    receivable_amount: 0,
    discount_amount: 0,
    actual_amount: 0,
    payment_method: '',
    payment_date: '',
    alert_threshold: 6
  }
  addDialogVisible.value = true
}

const handleAdd = async () => {
  if (!addFormRef.value) return
  
  await addFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 防止重复提交
        if (isSubmitting.value) {
          ElMessage.warning(t('fee.submitting'))
          return
        }
        isSubmitting.value = true
        
        // 计算应收金额：课节数 * 2小时 * 课时费
        const lessonCount = addForm.value.lesson_count || 0
        const hourlyFee = addForm.value.hourly_fee || 0
        const receivableAmount = lessonCount * 2 * hourlyFee
        
        // 计算实收金额：应收 - 优惠
        const discountAmount = addForm.value.discount_amount || 0
        const actualAmount = Math.max(0, receivableAmount - discountAmount)
        
        window.logger.log('费用计算:', {
          lessonCount,
          hourlyFee,
          receivableAmount,
          discountAmount,
          actualAmount
        })
        
        const formatDate = (date) => {
          if (!date) return null
          const d = new Date(date)
          const year = d.getFullYear()
          const month = String(d.getMonth() + 1).padStart(2, '0')
          const day = String(d.getDate()).padStart(2, '0')
          return `${year}-${month}-${day}T00:00:00`
        }
        
        const createData = {
          student_id: addForm.value.student_id,
          course_id: addForm.value.course_id,
          start_date: formatDate(addForm.value.start_date),
          hourly_fee: hourlyFee,
          lesson_count: lessonCount,
          discount_amount: discountAmount,
          payment_date: addForm.value.payment_date || null,
          payment_method: addForm.value.payment_method || '',
          alert_threshold: addForm.value.alert_threshold || 6,
          is_active: true
        }
        
        window.logger.log('创建课费记录数据:', createData)
        await api.post('/fees/student-fees', createData)
        
        ElMessage.success(t('fee.createSuccess'))
        addDialogVisible.value = false
        fetchStudentFees()
      } catch (error) {
        window.logger.error('创建失败:', error)
        ElMessage.error(t('fee.createFailed') + ': ' + (error.response?.data?.detail || error.message))
      } finally {
        isSubmitting.value = false
      }
    }
  })
}

const showEditDialog = (row) => {
  currentFee.value = row
  // 将后端返回的datetime字符串转换为YYYY-MM-DD格式
  let startDateStr = null
  if (row.start_date) {
    const date = new Date(row.start_date)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    startDateStr = `${year}-${month}-${day}`
  }
  
  editForm.value = {
    start_date: startDateStr,
    hourly_fee: row.hourly_fee,
    alert_threshold: row.alert_threshold,
    is_active: row.is_active
  }
  editDialogVisible.value = true
}

const handleEdit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const updateData = {
          start_date: editForm.value.start_date ? new Date(editForm.value.start_date).toISOString() : null,
          hourly_fee: editForm.value.hourly_fee,
          alert_threshold: editForm.value.alert_threshold,
          is_active: editForm.value.is_active
        }
        await api.put(`/fees/student-fees/${currentFee.value.id}`, updateData)
        ElMessage.success(t('fee.updateSuccess'))
        editDialogVisible.value = false
        fetchStudentFees()
      } catch (error) {
        window.logger.error('更新失败:', error)
        ElMessage.error(t('fee.updateFailed'))
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('fee.confirmDeleteFeeRecord'), t('fee.confirmTitle'), {
    confirmButtonText: t('fee.confirm'),
    cancelButtonText: t('fee.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await api.delete(`/fees/student-fees/${row.id}`)
      ElMessage.success(t('fee.deleteSuccess'))
      fetchStudentFees()
    } catch (error) {
      window.logger.error('删除失败:', error)
      ElMessage.error(t('fee.deleteFailed'))
    }
  }).catch(() => {})
}

const showPaymentDialog = (row) => {
  currentFee.value = row
  paymentForm.value = {
    student_id: row.student_id,
    course_id: row.course_id,
    lesson_count: 0,
    receivable_amount: 0,
    discount_amount: 0,
    actual_amount: 0,
    payment_method: '',
    payment_date: '',
    description: ''
  }
  paymentDialogVisible.value = true
}

// 处理追缴
const handlePayment = async () => {
  if (!paymentFormRef.value) return
  
  await paymentFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const lessonCount = paymentForm.value.lesson_count || 0
        const discountAmount = paymentForm.value.discount_amount || 0
        
        const paymentData = {
          student_id: paymentForm.value.student_id,
          course_id: paymentForm.value.course_id,
          lesson_count: lessonCount,
          discount_amount: discountAmount,
          payment_date: paymentForm.value.payment_date || null,
          description: paymentForm.value.description || t('fee.paymentDescription', { lessonCount, hours: lessonCount * 2, discount: discountAmount > 0 ? t('fee.discountYuan', { amount: discountAmount }) : '', method: paymentForm.value.payment_method })
        }
        
        window.logger.log('追缴费用数据:', paymentData)
        await api.post('/fees/payments', paymentData)
        ElMessage.success(t('fee.paymentSuccessMsg'))
        paymentDialogVisible.value = false
        fetchStudentFees()
      } catch (error) {
        window.logger.error('缴费失败:', error)
        const errorMsg = error.response?.data?.detail
        if (Array.isArray(errorMsg)) {
          ElMessage.error(t('fee.paymentFailed') + ': ' + errorMsg.map(e => e.msg).join(', '))
        } else if (typeof errorMsg === 'object') {
          ElMessage.error(t('fee.paymentFailed') + ': ' + JSON.stringify(errorMsg))
        } else {
          ElMessage.error(t('fee.paymentFailed') + ': ' + (errorMsg || error.message))
        }
      }
    }
  })
}

const showRefundDialog = (row) => {
  currentFee.value = row
  refundForm.value = {
    student_id: row.student_id,
    course_id: row.course_id,
    amount: 0,
    refund_date: '',
    refund_method: '',
    refund_reason: ''
  }
  refundDialogVisible.value = true
}

const handleRefund = async () => {
  if (!refundFormRef.value) return
  
  await refundFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.post('/fees/refunds', {
          student_id: refundForm.value.student_id,
          course_id: refundForm.value.course_id,
          amount: refundForm.value.amount,
          refund_date: refundForm.value.refund_date,
          refund_reason: t('fee.refundReasonWithMethod', { reason: refundForm.value.refund_reason || '', method: refundForm.value.refund_method })
        })
        ElMessage.success(t('fee.refundSuccessMsg'))
        refundDialogVisible.value = false
        fetchStudentFees()
      } catch (error) {
        window.logger.error('退费失败:', error)
        ElMessage.error(t('fee.refundFailed'))
      }
    }
  })
}

const showFeeLogsDialog = async (row) => {
  currentRow.value = row
  feeLogsLoading.value = true
  feeLogsDialogVisible.value = true
  try {
    const params = {
      student_id: row.student_id,
      course_id: row.course_id,
      skip: (feeLogsPagination.value.currentPage - 1) * feeLogsPagination.value.pageSize,
      limit: feeLogsPagination.value.pageSize
    }
    if (feeLogsSortField.value) {
      params.sort_field = feeLogsSortField.value
      params.sort_order = feeLogsSortOrder.value
    }
    const response = await api.get('/fees/fee-logs', { params })
    feeLogs.value = response.data.items || response.data
    feeLogsPagination.value.total = response.data.total || response.data.length
  } catch (error) {
    window.logger.error('获取课时费记录失败:', error)
    ElMessage.error(t('fee.fetchFeeRecordsFailed'))
  } finally {
    feeLogsLoading.value = false
  }
}

const handleFeeLogsSortChange = ({ prop, order }) => {
  feeLogsSortField.value = prop || ''
  feeLogsSortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  showFeeLogsDialog(currentRow.value)
}

const showAlerts = async () => {
  try {
    const response = await api.get('/fees/alerts')
    alerts.value = response.data
    if (alerts.value.length === 0) {
      ElMessage.info(t('fee.noReminderStudents'))
    } else {
      alertsDialogVisible.value = true
    }
  } catch (error) {
    window.logger.error('获取课费提醒失败:', error)
    ElMessage.error(t('fee.fetchReminderFailed'))
  }
}

const showEditThresholdDialog = (row) => {
  currentAlert.value = row
  thresholdForm.value = {
    alert_threshold: row.alert_threshold
  }
  thresholdDialogVisible.value = true
}

const handleUpdateThreshold = async () => {
  if (!thresholdFormRef.value) return
  
  await thresholdFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.put(`/fees/alert-threshold/${currentAlert.value.fee_id}`, thresholdForm.value)
        ElMessage.success(t('fee.thresholdUpdateSuccess'))
        thresholdDialogVisible.value = false
        showAlerts()
      } catch (error) {
        window.logger.error('更新预警阈值失败:', error)
        ElMessage.error(t('fee.thresholdUpdateFailed'))
      }
    }
  })
}

const exportPaymentRecords = async () => {
  try {
    const params = { lang: locale.value }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    const response = await api.get('/fees/export-payment-records', {
      params,
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${t('fee.studentFeeRecordExport')}_${new Date().toLocaleDateString('zh-CN')}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(t('fee.exportSuccessMsg'))
  } catch (error) {
    window.logger.error('导出失败:', error)
    ElMessage.error(t('fee.exportFailed'))
  }
}

const exportFeeLogs = async () => {
  try {
    const params = { lang: locale.value }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    const response = await api.get('/fees/export-fee-logs', {
      params,
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${t('fee.feeRecordExport')}_${new Date().toLocaleDateString('zh-CN')}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(t('fee.exportSuccessMsg'))
  } catch (error) {
    window.logger.error('导出失败:', error)
    ElMessage.error(t('fee.exportFailed'))
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const formatContentFeedback = (content) => {
  if (!content) return ''
  
  // 将分隔符转换为换行，并将标签加粗
  const lines = content.split('|').filter(line => line.trim())
  
  return lines.map(line => {
    // 将 "内容："、"作业："、"注意：" 等标签加粗
    return line.replace(new RegExp(`^(${t('fee.content')}|${t('fee.homework')}|${t('fee.attention')})(：)`, 'g'), '<strong>$1$2</strong>')
  }).join('<br/>')
}

const parseContentFeedbackForTooltip = (feedback) => {
  if (!feedback) return []
  const lines = feedback.split('|').filter(line => line.trim())
  return lines.map(line => {
    const parts = line.split('：')
    if (parts.length >= 2) {
      return {
        label: parts[0].trim(),
        content: parts.slice(1).join('：').trim()
      }
    }
    return {
      label: t('fee.feedback'),
      content: line.trim()
    }
  })
}

const getLogTypeColor = (type) => {
  const colors = {
    'payment': 'success',
    'refund': 'warning',
    'consume': 'danger'
  }
  return colors[type] || 'info'
}

const getLogTypeText = (type) => {
  const texts = {
    'payment': t('fee.payment'),
    'refund': t('fee.refundType'),
    'consume': t('fee.consume')
  }
  return texts[type] || type
}

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

onMounted(() => {
  // 检查是否有来自智能指令的搜索参数
  const urlParams = new URLSearchParams(window.location.search)
  const searchQuery = urlParams.get('search')
  const relatedTo = urlParams.get('related_to')
  
  fetchStudentFees()
  fetchStudents()
  fetchCourses()
  
  // 如果有搜索参数，自动填充并执行搜索
  if (searchQuery) {
    filters.value.student_name = searchQuery
    setTimeout(() => {
      fetchStudentFees()
      
      // 如果需要查看关联信息
      if (relatedTo && sessionStorage.getItem('smartCommandData')) {
        try {
          const smartData = JSON.parse(sessionStorage.getItem('smartCommandData'))
          if (smartData.target_path && smartData.target_label) {
            ElMessage.info(t('fee.foundStudentJumping', { name: searchQuery, label: smartData.target_label }))
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
  
  // 检查URL参数
  const action = route.query.action
  
  if (action === 'add') {
    showAddDialog()
  } else if (action === 'collect' || action === 'refund') {
    // 从sessionStorage读取预填充数据
    const storageData = sessionStorage.getItem('smartCommandData')
    if (storageData) {
      try {
        const prefillData = JSON.parse(storageData)
        window.logger.log('[DEBUG] 读取到预填充数据:', prefillData)
        sessionStorage.removeItem('smartCommandData')
        
        // 查找对应的学员课费项
        const matchingFee = studentFees.value.find(fee => 
          fee.student_id === prefillData.student_id && 
          (!prefillData.course_id || fee.course_id === prefillData.course_id)
        )
        
        if (matchingFee) {
          if (action === 'collect') {
            // 打开追缴对话框并预填充
            currentFee.value = matchingFee
            paymentForm.value = {
              student_id: matchingFee.student_id,
              course_id: matchingFee.course_id,
              lesson_count: 0,
              receivable_amount: 0,
              discount_amount: 0,
              actual_amount: prefillData.amount || 0,
              payment_method: '',
              payment_date: prefillData.fee_date || new Date().toISOString().split('T')[0],
              description: ''
            }
            paymentDialogVisible.value = true
            ElMessage.info(t('fee.paymentPageOpened'))
          } else if (action === 'refund') {
            // 打开退费对话框并预填充
            currentFee.value = matchingFee
            refundForm.value = {
              student_id: matchingFee.student_id,
              course_id: matchingFee.course_id,
              amount: prefillData.amount || 0,
              refund_date: prefillData.refund_date || new Date().toISOString().split('T')[0],
              reason: prefillData.reason || '',
              description: ''
            }
            refundDialogVisible.value = true
            ElMessage.info(t('fee.refundPageOpened'))
          }
        }
      } catch (error) {
        window.logger.error('解析智能指令数据失败', error)
      }
    }
  } else if (action === 'view_logs') {
    // 查看课时费记录 - 直接从路由参数构建row对象
    const studentId = parseInt(route.query.student_id)
    const courseId = parseInt(route.query.course_id)
    
    if (studentId && courseId) {
      // 直接构建row对象，只需要student_id和course_id即可
      const row = {
        student_id: studentId,
        course_id: courseId
      }
      
      // 立即打开对话框，API会根据ID查询数据
      showFeeLogsDialog(row)
      ElMessage.success(t('fee.loadingFeeLogs'))
    }
  }
  
  setTimeout(() => {
    initTopScrollbar()
    setupScrollSync()
  }, 200)
})

onUnmounted(() => {
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

watch(studentFees, () => {
  setTimeout(() => {
    initTopScrollbar()
    setupScrollSync()
  }, 200)
})

</script>

<style scoped>
.fee-management {
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

.debug-info {
  margin-bottom: 20px;
}

.debug-table-container {
  margin-top: 10px;
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

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
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
  
  .search-bar :deep(.el-input) {
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