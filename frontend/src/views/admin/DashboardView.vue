// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="dashboard-container" :class="{ 'fullscreen': isFullscreen }">
    <!-- 顶部工具栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1 class="dashboard-title">
          <el-icon><DataAnalysis /></el-icon>
          运营大屏
        </h1>
        <span class="last-update">最后更新: {{ lastUpdateTime }}</span>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Refresh" @click="refreshData" :loading="loading">
          刷新数据
        </el-button>
        <el-button type="info" :icon="Hide" @click="toggleRevenueVisibility">
          {{ hideRevenue ? '显示营收' : '隐藏营收' }}
        </el-button>
        <el-button type="success" :icon="FullScreen" @click="toggleFullscreen">
          {{ isFullscreen ? '退出全屏' : '全屏模式' }}
        </el-button>
        <el-button type="warning" :icon="Download" @click="exportDashboard">
          导出图片
        </el-button>
      </div>
    </div>

    <!-- KPI卡片区域 -->
    <el-row :gutter="20" class="kpi-section">
      <template v-for="(kpi, index) in kpiData" :key="index">
        <el-col 
          :xs="12" 
          :sm="8" 
          :md="4" 
          :lg="4"
          v-if="!['本月收入', '当年收入', '退费总额', '累计优惠额度', '本月续费率'].includes(kpi.label)"
        >
          <el-card class="kpi-card" shadow="hover" @click="handleKpiClick(kpi)">
            <div class="kpi-content">
              <div class="kpi-icon" :style="{ background: kpi.color }">
                <el-icon :size="32"><component :is="kpi.icon" /></el-icon>
              </div>
              <div class="kpi-info">
                <div class="kpi-value">{{ kpi.value }}</div>
                <div class="kpi-label">{{ kpi.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col 
          :xs="12" 
          :sm="12" 
          :md="6" 
          :lg="6"
          v-else-if="['本月收入', '当年收入'].includes(kpi.label) && !hideRevenue && hasFeature('fee_management')"
        >
          <el-card class="kpi-card income-card" shadow="hover" @click="handleKpiClick(kpi)">
            <div class="kpi-content">
              <div class="kpi-icon" :style="{ background: kpi.color }">
                <el-icon :size="32"><component :is="kpi.icon" /></el-icon>
              </div>
              <div class="kpi-info">
                <div class="kpi-value">{{ kpi.value }}</div>
                <div class="kpi-label">{{ kpi.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col 
          :xs="12" 
          :sm="12" 
          :md="6" 
          :lg="6"
          v-else-if="['本月收入', '当年收入'].includes(kpi.label) && !hideRevenue && !hasFeature('fee_management')"
        >
          <el-tooltip content="费用管理为授权功能，请在系统授权管理中激活" placement="bottom">
            <el-card class="kpi-card income-card" style="opacity: 0.5; cursor: not-allowed;">
              <div class="kpi-content">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #909399 0%, #b1b3b8 100%);">
                  <el-icon :size="32"><Lock /></el-icon>
                </div>
                <div class="kpi-info">
                  <div class="kpi-value" style="color: #909399;">--</div>
                  <div class="kpi-label">{{ kpi.label }}</div>
                </div>
              </div>
            </el-card>
          </el-tooltip>
        </el-col>
        <el-col 
          :xs="12" 
          :sm="8" 
          :md="4" 
          :lg="4"
          v-else-if="['退费总额', '累计优惠额度', '本月续费率'].includes(kpi.label) && !hideRevenue && hasFeature('fee_management')"
        >
          <el-card class="kpi-card" shadow="hover" @click="handleKpiClick(kpi)">
            <div class="kpi-content">
              <div class="kpi-icon" :style="{ background: kpi.color }">
                <el-icon :size="32"><component :is="kpi.icon" /></el-icon>
              </div>
              <div class="kpi-info">
                <div class="kpi-value">{{ kpi.value }}</div>
                <div class="kpi-label">{{ kpi.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col 
          :xs="12" 
          :sm="8" 
          :md="4" 
          :lg="4"
          v-else-if="['退费总额', '累计优惠额度', '本月续费率'].includes(kpi.label) && !hideRevenue && !hasFeature('fee_management')"
        >
          <el-tooltip content="费用管理为授权功能，请在系统授权管理中激活" placement="bottom">
            <el-card class="kpi-card" style="opacity: 0.5; cursor: not-allowed;">
              <div class="kpi-content">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #909399 0%, #b1b3b8 100%);">
                  <el-icon :size="32"><Lock /></el-icon>
                </div>
                <div class="kpi-info">
                  <div class="kpi-value" style="color: #909399;">--</div>
                  <div class="kpi-label">{{ kpi.label }}</div>
                </div>
              </div>
            </el-card>
          </el-tooltip>
        </el-col>
        <el-col 
          :xs="12" 
          :sm="8" 
          :md="4" 
          :lg="4"
          v-else-if="['本月转化率'].includes(kpi.label)"
        >
          <el-card class="kpi-card" shadow="hover" @click="handleKpiClick(kpi)">
            <div class="kpi-content">
              <div class="kpi-icon" :style="{ background: kpi.color }">
                <el-icon :size="32"><component :is="kpi.icon" /></el-icon>
              </div>
              <div class="kpi-info">
                <div class="kpi-value">{{ kpi.value }}</div>
                <div class="kpi-label">{{ kpi.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col 
          :xs="12" 
          :sm="8" 
          :md="4" 
          :lg="4"
          v-else-if="!hideRevenue"
        >
          <el-card class="kpi-card" shadow="hover" @click="handleKpiClick(kpi)">
            <div class="kpi-content">
              <div class="kpi-icon" :style="{ background: kpi.color }">
                <el-icon :size="32"><component :is="kpi.icon" /></el-icon>
              </div>
              <div class="kpi-info">
                <div class="kpi-value">{{ kpi.value }}</div>
                <div class="kpi-label">{{ kpi.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </template>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-section">
      <!-- 成绩等级分布 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>成绩等级分布</span>
              <el-tooltip v-if="!hasFeature('grade_trend')" content="学员成绩曲线为授权功能，请在系统授权管理中激活" placement="top">
                <el-tag type="info" effect="plain" style="cursor: not-allowed;">
                  <el-icon><Lock /></el-icon> 未授权
                </el-tag>
              </el-tooltip>
            </div>
          </template>
          <div v-if="hasFeature('grade_trend')" ref="gradeDistChart" class="chart-container" style="height: 350px;"></div>
          <div v-else class="unauthorized-placeholder" style="height: 350px; display: flex; align-items: center; justify-content: center; color: #909399;">
            <div style="text-align: center;">
              <el-icon :size="48"><Lock /></el-icon>
              <p style="margin-top: 12px;">学员成绩曲线为授权功能</p>
              <p>请在系统授权管理中激活</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <!-- 学员进步榜TopN -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>学员进步榜TopN</span>
              <el-select v-if="hasFeature('grade_trend')" v-model="improvementRankingLimit" @change="handleImprovementRankingLimitChange" style="width: 120px">
                <el-option label="TOP10" :value="10" />
                <el-option label="TOP15" :value="15" />
                <el-option label="TOP30" :value="30" />
                <el-option label="TOP50" :value="50" />
                <el-option label="TOP100" :value="100" />
              </el-select>
              <el-tooltip v-if="!hasFeature('grade_trend')" content="学员成绩曲线为授权功能，请在系统授权管理中激活" placement="top">
                <el-tag type="info" effect="plain" style="cursor: not-allowed;">
                  <el-icon><Lock /></el-icon> 未授权
                </el-tag>
              </el-tooltip>
            </div>
          </template>
          <template v-if="hasFeature('grade_trend')">
          <el-table :data="improvementRanking" style="width: 100%" max-height="350">
            <el-table-column prop="student_name" label="学员姓名" width="100">
              <template #default="{ row }">
                <el-tooltip placement="right" effect="light" popper-class="student-info-tooltip">
                  <template #content>
                    <div class="student-detail-info">
                      <div class="info-item"><strong>学员代码：</strong>{{ getStudentCode(row.student_id) }}</div>
                      <div class="info-item"><strong>学员姓名：</strong>{{ row.student_name }}</div>
                      <div class="info-item"><strong>学校：</strong>{{ getStudentSchool(row.student_id) }}</div>
                      <div class="info-item"><strong>年级：</strong>{{ getStudentGrade(row.student_id) }}</div>
                      <div class="info-item"><strong>进入机构日期：</strong>{{ getStudentJoinDate(row.student_id) }}</div>
                      <div class="info-item"><strong>联系人：</strong>{{ getStudentContact(row.student_id) }}</div>
                      <div class="info-item"><strong>联系电话：</strong>{{ getStudentPhone(row.student_id) }}</div>
                      <div class="info-item"><strong>邮箱：</strong>{{ getStudentEmail(row.student_id) }}</div>
                      <div class="info-item"><strong>所属班级：</strong>{{ getStudentClasses(row.student_id) }}</div>
                      <div class="info-item"><strong>是否在读：</strong>{{ getStudentIsActive(row.student_id) ? '是' : '否' }}</div>
                    </div>
                  </template>
                  <span style="cursor: pointer; color: #409eff;">{{ row.student_name }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="course_name" label="科目" width="180" />
            <el-table-column prop="score_change" label="最大进步幅度" width="120">
              <template #default="{ row }">
                <span :style="{ color: row.score_change > 0 ? '#67C23A' : '#F56C6C' }">
                  {{ row.score_change > 0 ? '+' : '' }}{{ row.score_change }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="max_ratio" label="最高得分比" width="100">
              <template #default="{ row }">
                <el-tooltip placement="top" effect="dark">
                  <template #content>
                    <div>该次考试年级：{{ row.grade_level }}</div>
                    <div>该次考试阶段：{{ row.max_ratio_exam_stage }}</div>
                  </template>
                  <span>{{ row.max_ratio }}%</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="current_ratio" label="最近得分比" width="100">
              <template #default="{ row }">
                <el-tooltip placement="top" effect="dark">
                  <template #content>
                    <div>该次考试年级：{{ row.grade_level }}</div>
                    <div>该次考试阶段：{{ row.exam_stage }}</div>
                  </template>
                  <span>{{ row.current_ratio }}%</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="显示" width="180" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="showGradeCurve(row)">
                  成绩曲线
                </el-button>
                <el-button v-if="hasFeature('student_evaluation')" type="warning" size="small" @click="goToStudentEvaluation(row)">
                  评价信息
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          </template>
          <div v-else class="unauthorized-placeholder" style="height: 350px; display: flex; align-items: center; justify-content: center; color: #909399;">
            <div style="text-align: center;">
              <el-icon :size="48"><Lock /></el-icon>
              <p style="margin-top: 12px;">学员成绩曲线为授权功能</p>
              <p>请在系统授权管理中激活</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 收费预警列表 -->
    <el-row :gutter="20" class="chart-section" v-if="!hideRevenue && hasFeature('fee_management')">
      <el-col :span="12">
        <el-card class="chart-card" shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>收费预警列表</span>
              <el-tag type="danger" effect="dark">{{ feeAlerts.length }} 条预警</el-tag>
            </div>
          </template>
          <el-table :data="feeAlerts" style="width: 100%" max-height="400">
            <el-table-column prop="student_name" label="学员姓名" width="120">
              <template #default="{ row }">
                <el-tooltip placement="right" effect="light" popper-class="student-info-tooltip">
                  <template #content>
                    <div class="student-detail-info">
                      <div class="info-item"><strong>学员代码：</strong>{{ getStudentCode(row.student_id) }}</div>
                      <div class="info-item"><strong>学员姓名：</strong>{{ row.student_name }}</div>
                      <div class="info-item"><strong>学校：</strong>{{ getStudentSchool(row.student_id) }}</div>
                      <div class="info-item"><strong>年级：</strong>{{ getStudentGrade(row.student_id) }}</div>
                      <div class="info-item"><strong>进入机构日期：</strong>{{ getStudentJoinDate(row.student_id) }}</div>
                      <div class="info-item"><strong>联系人：</strong>{{ getStudentContact(row.student_id) }}</div>
                      <div class="info-item"><strong>联系电话：</strong>{{ getStudentPhone(row.student_id) }}</div>
                      <div class="info-item"><strong>邮箱：</strong>{{ getStudentEmail(row.student_id) }}</div>
                      <div class="info-item"><strong>所属班级：</strong>{{ getStudentClasses(row.student_id) }}</div>
                      <div class="info-item"><strong>是否在读：</strong>{{ getStudentIsActive(row.student_id) ? '是' : '否' }}</div>
                    </div>
                  </template>
                  <span style="cursor: pointer; color: #409eff;">{{ row.student_name }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="course_name" label="科目" width="120" />
            <el-table-column prop="remaining_hours" label="剩余课时" width="100">
              <template #default="{ row }">
                <el-tag :type="row.alert_level === 'danger' ? 'danger' : row.alert_level === 'warning' ? 'warning' : 'info'">
                  {{ row.remaining_hours }}小时
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="remaining_amount" label="剩余金额" width="120">
              <template #default="{ row }">
                ¥{{ row.remaining_amount.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="alert_threshold" label="预警阈值" width="100">
              <template #default="{ row }">
                {{ row.alert_threshold }}小时
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="goToFeeManagement(row)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 未交费面板 -->
      <el-col :span="12" v-if="!hideRevenue && hasFeature('fee_management')">
        <el-card class="chart-card" shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>待缴费学员列表</span>
              <el-tag type="warning" effect="dark">{{ unpaidStudents.length }} 人</el-tag>
            </div>
          </template>
          <el-table :data="unpaidStudents" style="width: 100%" max-height="400">
            <el-table-column prop="student_name" label="学员姓名" width="120">
              <template #default="{ row }">
                <el-tooltip placement="right" effect="light" popper-class="student-info-tooltip">
                  <template #content>
                    <div class="student-detail-info">
                      <div class="info-item"><strong>学员代码：</strong>{{ getStudentCode(row.student_id) }}</div>
                      <div class="info-item"><strong>学员姓名：</strong>{{ row.student_name }}</div>
                      <div class="info-item"><strong>学校：</strong>{{ getStudentSchool(row.student_id) }}</div>
                      <div class="info-item"><strong>年级：</strong>{{ getStudentGrade(row.student_id) }}</div>
                      <div class="info-item"><strong>进入机构日期：</strong>{{ getStudentJoinDate(row.student_id) }}</div>
                      <div class="info-item"><strong>联系人：</strong>{{ getStudentContact(row.student_id) }}</div>
                      <div class="info-item"><strong>联系电话：</strong>{{ getStudentPhone(row.student_id) }}</div>
                      <div class="info-item"><strong>邮箱：</strong>{{ getStudentEmail(row.student_id) }}</div>
                      <div class="info-item"><strong>所属班级：</strong>{{ getStudentClasses(row.student_id) }}</div>
                      <div class="info-item"><strong>是否在读：</strong>{{ getStudentIsActive(row.student_id) ? '是' : '否' }}</div>
                    </div>
                  </template>
                  <span style="cursor: pointer; color: #409eff;">{{ row.student_name }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="未缴费科目" min-width="250">
              <template #default="{ row }">
                <div v-if="row.unpaid_courses && row.unpaid_courses.length > 0">
                  <el-tag
                    v-for="(course, index) in row.unpaid_courses"
                    :key="index"
                    type="warning"
                    effect="plain"
                    style="margin-right: 5px; margin-bottom: 5px; cursor: pointer;"
                  >
                    <el-tooltip placement="top" effect="light">
                      <template #content>
                        <div style="padding: 5px;">
                          <div><strong>科目：</strong>{{ course.course_name }}</div>
                          <div><strong>导师：</strong>{{ course.teacher_name }}</div>
                          <div><strong>已上课：</strong>{{ course.schedule_count }} 节</div>
                          <div><strong>欠缴课时：</strong>{{ course.unpaid_hours }} 小时</div>
                        </div>
                      </template>
                      {{ course.course_name }}
                    </el-tooltip>
                  </el-tag>
                </div>
                <span v-else style="color: #909399;">-</span>
              </template>
            </el-table-column>
            <el-table-column label="总欠缴课时" width="110" align="center">
              <template #default="{ row }">
                <el-tag type="danger" effect="dark">
                  {{ row.total_unpaid_hours }} 小时
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 未完训排课 -->
    <el-row :gutter="20" class="chart-section">
      <el-col :span="24">
        <el-card class="chart-card" shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>未完训排课</span>
              <el-tag type="warning" effect="dark">{{ incompleteSchedules.length }} 条</el-tag>
            </div>
          </template>
          <el-table :data="incompleteSchedules" style="width: 100%" max-height="400">
            <el-table-column prop="course_name" label="科目" width="120" />
            <el-table-column prop="teacher_name" label="导师" width="100" />
            <el-table-column prop="class_name" label="班级" width="120" />
            <el-table-column prop="room_name" label="教室" width="100" />
            <el-table-column label="上课时间" width="200">
              <template #default="{ row }">
                {{ row.start_date }} {{ row.start_time }}<br/>
                {{ row.end_date }} {{ row.end_time }}
              </template>
            </el-table-column>
            <el-table-column prop="execution_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.execution_status === 'cancelled' ? 'danger' : row.execution_status === 'postponed' ? 'warning' : 'info'">
                  {{ row.execution_status === 'pending' ? '待执行' : row.execution_status === 'postponed' ? '延期' : '取消' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="student_count" label="在读学员数" width="80" />
            <el-table-column prop="student_names" label="在读学员" min-width="200" show-overflow-tooltip />
            <el-table-column label="原因" min-width="150" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.cancel_reason || row.postpone_reason || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="显示" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="goToScheduleDetail(row.schedule_id)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-section">
      <!-- 课程趋势 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>课程趋势</span>
              <el-select v-model="scheduleTrendDays" @change="handleScheduleTrendDaysChange" style="width: 120px">
                <el-option label="近30天" :value="30" />
                <el-option label="近90天" :value="90" />
                <el-option label="近120天" :value="120" />
                <el-option label="近半年" :value="180" />
                <el-option label="近1年" :value="365" />
              </el-select>
            </div>
          </template>
          <div ref="scheduleTrendChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 新学员增长率 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover" v-loading="chartLoading.studentGrowth">
          <template #header>
            <div class="card-header">
              <span>新学员增长率</span>
              <el-select v-model="studentGrowthMonths" @change="handleStudentGrowthMonthsChange" style="width: 120px">
                <el-option label="最近3月" :value="3" />
                <el-option label="最近6月" :value="6" />
                <el-option label="最近9月" :value="9" />
                <el-option label="最近1年" :value="12" />
                <el-option label="最近2年" :value="24" />
              </el-select>
            </div>
          </template>
          <div ref="studentGrowthChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 热门科目TOP5 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover" v-loading="chartLoading.popularCourses">
          <template #header>
            <div class="card-header">
              <span>热门科目TopN榜</span>
              <el-select v-model="popularCoursesLimit" @change="handlePopularCoursesLimitChange" style="width: 120px">
                <el-option label="TOP5" :value="5" />
                <el-option label="TOP10" :value="10" />
                <el-option label="TOP15" :value="15" />
                <el-option label="TOP30" :value="30" />
                <el-option label="TOP50" :value="50" />
              </el-select>
            </div>
          </template>
          <div ref="popularCoursesChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-section">
      <!-- 课程分析 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>科目分布</span>
            </div>
          </template>
          <div ref="courseDistChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 长效学员榜TOPn榜 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>长效学员榜TOPn榜</span>
              <el-select v-model="longTermStudentsLimit" @change="handleLongTermStudentsLimitChange" style="width: 120px">
                <el-option label="TOP10" :value="10" />
                <el-option label="TOP15" :value="15" />
                <el-option label="TOP30" :value="30" />
                <el-option label="TOP50" :value="50" />
                <el-option label="TOP100" :value="100" />
              </el-select>
            </div>
          </template>
          <el-table :data="longTermStudents" style="width: 100%" max-height="350">
            <el-table-column prop="student_name" label="学员姓名" width="100">
              <template #default="{ row }">
                <el-tooltip placement="right" effect="light" popper-class="student-info-tooltip">
                  <template #content>
                    <div class="student-detail-info">
                      <div class="info-item"><strong>学员代码：</strong>{{ row.student_code }}</div>
                      <div class="info-item"><strong>学员姓名：</strong>{{ row.student_name }}</div>
                      <div class="info-item"><strong>学校：</strong>{{ row.school }}</div>
                      <div class="info-item"><strong>年级：</strong>{{ row.grade }}</div>
                      <div class="info-item"><strong>进入机构日期：</strong>{{ row.enrollment_date }}</div>
                      <div class="info-item"><strong>联系人：</strong>{{ row.contact_person }}</div>
                      <div class="info-item"><strong>联系电话：</strong>{{ row.contact_phone }}</div>
                      <div class="info-item"><strong>邮箱：</strong>{{ row.email }}</div>
                      <div class="info-item"><strong>是否在读：</strong>{{ row.is_active ? '是' : '否' }}</div>
                    </div>
                  </template>
                  <span style="cursor: pointer; color: #409eff;">{{ row.student_name }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="enrollment_date" label="进入机构日期" width="120" />
            <el-table-column prop="days_in_organization" label="在机构时长" width="100">
              <template #default="{ row }">
                <span :style="{ color: row.days_in_organization > 365 ? '#67C23A' : row.days_in_organization > 180 ? '#E6A23C' : '#909399' }">
                  {{ row.days_in_organization }}天
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="total_completed_hours" label="累计完成课时" width="120">
              <template #default="{ row }">
                <span :style="{ color: row.total_completed_hours > 100 ? '#67C23A' : row.total_completed_hours > 50 ? '#E6A23C' : '#909399' }">
                  {{ row.total_completed_hours }}课时
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="school" label="学校" width="120" />
            <el-table-column prop="grade" label="年级" width="80" />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '在读' : '非在读' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <!-- 课时余量分布 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>课时余量分布</span>
            </div>
          </template>
          <div ref="balanceDistChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 各教室利用率 -->
    <el-row :gutter="20" class="chart-section">
      <el-col :span="24">
        <el-card class="chart-card" shadow="hover" v-loading="chartLoading.roomUtilization">
          <template #header>
            <div class="card-header">
              <span>各教室利用率</span>
              <el-select v-model="roomUtilizationDays" @change="handleRoomUtilizationDaysChange" style="width: 120px">
                <el-option label="最近30天" :value="30" />
                <el-option label="最近60天" :value="60" />
                <el-option label="最近90天" :value="90" />
                <el-option label="最近半年" :value="180" />
                <el-option label="最近1年" :value="365" />
              </el-select>
            </div>
          </template>
          <div ref="roomUtilizationChart" class="chart-container" style="height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导师周课时排行榜 -->
    <el-row :gutter="20" class="chart-section">
      <el-col :span="24">
        <el-card class="chart-card" shadow="hover" v-loading="chartLoading.weeklyWorkload">
          <template #header>
            <div class="card-header">
              <span>导师课时排行榜</span>
              <el-select v-model="weeklyWorkloadDays" @change="handleWeeklyWorkloadDaysChange" style="width: 120px">
                <el-option label="最近9天" :value="8" />
                <el-option label="最近30天" :value="29" />
                <el-option label="最近90天" :value="89" />
                <el-option label="最近180天" :value="179" />
                <el-option label="最近1年" :value="364" />
                <el-option label="最近2年" :value="728" />
              </el-select>
            </div>
          </template>
          <div ref="weeklyWorkloadChart" class="chart-container" style="height: 350px;"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-section" v-if="!hideRevenue && hasFeature('fee_management')">
      <!-- 费用分析 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>收入构成</span>
            </div>
          </template>
          <div ref="feeCompositionChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 月度收入趋势 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>月度收入趋势</span>
              <el-select v-model="feeTrendMonths" @change="handleFeeTrendMonthsChange" style="width: 120px">
                <el-option label="最近3月" :value="3" />
                <el-option label="最近6月" :value="6" />
                <el-option label="最近9月" :value="9" />
                <el-option label="最近1年" :value="12" />
                <el-option label="最近2年" :value="24" />
              </el-select>
            </div>
          </template>
          <div ref="feeTrendChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 月度退费率 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover" v-loading="chartLoading.refundRate">
          <template #header>
            <div class="card-header">
              <span>月度退费率趋势</span>
              <el-select v-model="refundRateMonths" @change="handleRefundRateMonthsChange" style="width: 120px">
                <el-option label="最近3月" :value="3" />
                <el-option label="最近6月" :value="6" />
                <el-option label="最近9月" :value="9" />
                <el-option label="最近1年" :value="12" />
                <el-option label="最近2年" :value="24" />
              </el-select>
            </div>
          </template>
          <div ref="refundRateChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-section">
      <!-- 导师试听效能榜 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>导师试听效能榜</span>
              <el-select v-model="trialEfficiencyDays" @change="handleTrialEfficiencyDaysChange" style="width: 120px">
                <el-option label="最近30天" :value="30" />
                <el-option label="最近60天" :value="60" />
                <el-option label="最近90天" :value="90" />
                <el-option label="最近半年" :value="180" />
                <el-option label="最近1年" :value="365" />
              </el-select>
            </div>
          </template>
          <div ref="trialEfficiencyChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 导师试听转化漏斗 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>试听转化漏斗</span>
              <el-select v-model="trialFunnelDays" @change="handleTrialFunnelDaysChange" style="width: 120px">
                <el-option label="最近30天" :value="30" />
                <el-option label="最近60天" :value="60" />
                <el-option label="最近90天" :value="90" />
                <el-option label="最近半年" :value="180" />
                <el-option label="最近1年" :value="365" />
              </el-select>
            </div>
          </template>
          <div ref="trialFunnelChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <!-- 导师工作量 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>导师工作量排行</span>
              <el-select v-model="teacherWorkloadDays" @change="handleTeacherWorkloadDaysChange" style="width: 120px">
                <el-option label="最近30天" :value="30" />
                <el-option label="最近60天" :value="60" />
                <el-option label="最近90天" :value="90" />
                <el-option label="最近半年" :value="180" />
                <el-option label="最近1年" :value="365" />
              </el-select>
            </div>
          </template>
          <div ref="teacherWorkloadChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 成绩曲线对话框 -->
    <el-dialog v-model="gradeCurveDialogVisible" :title="`成绩比例曲线 - ${currentStudentName}`" width="90%" top="5vh">
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

    <!-- 密码验证对话框 -->
    <el-dialog v-model="passwordDialogVisible" title="密码验证" width="400px" center>
      <el-form>
        <el-form-item label="请输入当前用户密码">
          <el-input v-model="passwordInput" type="password" placeholder="请输入密码" show-password autocomplete="new-password" @keyup.enter="verifyPasswordAndShowRevenue" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="verifyPasswordAndShowRevenue">确认</el-button>
      </template>
    </el-dialog>

    <!-- KPI详细数据对话框 -->
    <el-dialog v-model="kpiDetailDialogVisible" :title="`${currentKpiTitle} - 详细数据`" width="90%" top="5vh" draggable>
      <div v-loading="kpiDetailData.loading">
        <el-empty v-if="!kpiDetailData.loading && (!kpiDetailData.data || kpiDetailData.data.length === 0)" description="暂无数据" />
        
        <!-- 本月收入/当年收入 -->
        <el-table v-else-if="['本月收入', '当年收入'].includes(currentKpiTitle)" :data="kpiDetailData.data" style="width: 100%" max-height="500">
          <el-table-column prop="student_name" label="学员姓名" width="120" />
          <el-table-column prop="course_name" label="科目" width="120" />
          <el-table-column prop="amount" label="金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="payment_date" label="缴费日期" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag type="success">{{ row.status || '已缴费' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        </el-table>
        
        <!-- 退费总额 -->
        <el-table v-else-if="currentKpiTitle === '退费总额'" :data="kpiDetailData.data" style="width: 100%" max-height="500">
          <el-table-column prop="student_name" label="学员姓名" width="120" />
          <el-table-column prop="course_name" label="科目" width="120" />
          <el-table-column prop="amount" label="退费金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="refund_date" label="退费日期" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag type="danger">{{ row.status || '已退费' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        </el-table>
        
        <!-- 累计优惠额度 -->
        <el-table v-else-if="currentKpiTitle === '累计优惠额度'" :data="kpiDetailData.data" style="width: 100%" max-height="500">
          <el-table-column prop="student_name" label="学员姓名" width="120" />
          <el-table-column prop="course_name" label="科目" width="120" />
          <el-table-column prop="amount" label="优惠金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="receivable_amount" label="应收金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.receivable_amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="actual_amount" label="实收金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.actual_amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag type="warning">{{ row.status || '优惠' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        </el-table>
        
        <!-- 本月续费率 -->
        <el-table v-else-if="currentKpiTitle === '本月续费率'" :data="kpiDetailData.data" style="width: 100%" max-height="500">
          <el-table-column prop="student_name" label="学员姓名" width="120" />
          <el-table-column prop="course_name" label="科目" width="120" />
          <el-table-column prop="previous_amount" label="累计缴费金额" width="140">
            <template #default="{ row }">
              ¥{{ (row.previous_amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="renewal_amount" label="续费金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.renewal_amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="renewal_date" label="续费日期" width="150" />
          <el-table-column prop="renewal_type" label="续费类型" width="120">
            <template #default="{ row }">
              <el-tag :type="row.renewal_type === '创建新记录' ? 'primary' : 'success'">{{ row.renewal_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="renewed" label="是否续费" width="100">
            <template #default="{ row }">
              <el-tag :type="row.renewed === '是' ? 'success' : 'info'">{{ row.renewed }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 本月转化率 -->
        <el-table v-else-if="currentKpiTitle === '本月转化率'" :data="kpiDetailData.data" style="width: 100%" max-height="500">
          <el-table-column prop="student_name" label="学员姓名" width="120" />
          <el-table-column prop="course_name" label="科目" width="120" />
          <el-table-column prop="teacher_name" label="导师" width="100" />
          <el-table-column prop="trial_date" label="试听日期" width="150" />
          <el-table-column prop="converted" label="是否转化" width="100">
            <template #default="{ row }">
              <el-tag :type="row.converted === '是' ? 'success' : 'info'">{{ row.converted }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="payment_date" label="缴费日期" width="150" />
          <el-table-column prop="amount" label="缴费金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 默认表格 -->
        <el-table v-else :data="kpiDetailData.data" style="width: 100%" max-height="500">
          <el-table-column prop="student_name" label="学员姓名" width="120" />
          <el-table-column prop="course_name" label="科目" width="120" />
          <el-table-column prop="amount" label="金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="payment_date" label="缴费日期" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'paid' ? 'success' : row.status === 'refunded' ? 'danger' : 'warning'">
                {{ row.status === 'paid' ? '已缴费' : row.status === 'refunded' ? '已退费' : '其他' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="kpiDetailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import html2canvas from 'html2canvas'
import {
  DataAnalysis, Refresh, FullScreen, Download, Hide, Lock,
  Tickets, User, Reading, Money, TrendCharts, Bell,
  OfficeBuilding, Calendar, InfoFilled, Warning, Connection
} from '@element-plus/icons-vue'
import api from '@/utils/api'
import { hasFeature } from '@/utils/license'

const router = useRouter()
const loading = ref(false)
const isFullscreen = ref(false)
const hideRevenue = ref(localStorage.getItem('hideRevenue') === 'true')
const passwordDialogVisible = ref(false)
const passwordInput = ref('')
const kpiDetailData = ref({})
const kpiDetailLoading = ref({})
const kpiDetailDialogVisible = ref(false)
const lastUpdateTime = ref('')
let refreshTimer = null

const chartLoading = ref({
  weeklyWorkload: false,
  refundRate: false,
  studentGrowth: false,
  popularCourses: false,
  roomUtilization: false
})

// KPI数据
const kpiData = ref([
  //'本月收入': '计算逻辑：统计本月所有已缴费记录的实际收入金额\n数据来源：fee_records表中本月所有status为"paid"的记录\n计算公式：SUM(amount) WHERE status="paid" AND payment_date在当前月份',
  { label: '本月收入', value: '¥0', icon: Money, color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', route: '/admin/feemanagement' },
  // '当年收入': '计算逻辑：统计当年所有已缴费记录的实际收入金额\n数据来源：fee_records表中当年所有status为"paid"的记录\n计算公式：SUM(amount) WHERE status="paid" AND payment_date在当前年份',
  { label: '当年收入', value: '¥0', icon: Money, color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', route: '/admin/feemanagement' },
  // '本月转化率': '计算逻辑：试听转化人数/试听总人数\n数据来源：schedules表中本月试听课记录\n计算公式：(完训并缴费的试听人数/本月试听总人数) × 100%'
  { label: '本月转化率', value: '0%', icon: TrendCharts, color: 'linear-gradient(135deg, #66bb6a 0%, #43a047 100%)', route: '/admin/schedules', query: { schedule_type: 'trial' } },
  { label: '今日试听课', value: 0, icon: Bell, color: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', route: '/admin/schedules', query: { schedule_type: 'trial', date: '今天' } },
  { label: '今日正式课', value: 0, icon: Bell, color: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', route: '/admin/schedules', query: { schedule_type: 'formal', date: '今天' } },
  //'退费总额': '计算逻辑：统计所有退费记录的退费金额\n数据来源：fee_records表中所有status为"refunded"的记录\n计算公式：SUM(amount) WHERE status="refunded"',
  { label: '退费总额', value: '¥0', icon: Money, color: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)', route: '/admin/feemanagement' },
  //'累计优惠额度': '计算逻辑：统计所有学员的屡次优惠金额之和\n数据来源：学员账户余额为负数的记录\n计算公式：SUM(ABS(balance)) WHERE balance < 0',
  { label: '累计优惠额度', value: '¥0', icon: Money, color: 'linear-gradient(135deg, #ffa726 0%, #fb8c00 100%)', route: '/admin/feemanagement' },
  // '本月续费率': '计算逻辑：续费学员数/到期学员数\n数据来源：student_fee_records表\n计算公式：(续费学员数/到期学员数) × 100%',
  { label: '本月续费率', value: '0%', icon: TrendCharts, color: 'linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%)', route: '/admin/students' },
  { label: '待补课学员数', value: 0, icon: Bell, color: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', route: '/admin/schedules', query: { execution_status: 'completed', has_absent_students: true } },
  { label: '未完训排课', value: 0, icon: Warning, color: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)', route: '/admin/schedules', query: { execution_status: 'pending,postponed,cancelled' } },
  { label: '已完训排课', value: 0, icon: Warning, color: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)', route: '/admin/schedules', query: { execution_status: 'completed' } },
  { label: '总排课数', value: 0, icon: Calendar, color: 'linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)', route: '/admin/schedules' },
  { label: '总科目数', value: 0, icon: Tickets, color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', route: '/admin/courses' },
  { label: '总班级数', value: 0, icon: OfficeBuilding, color: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', route: '/admin/classes' },
  { label: '在读学员', value: 0, icon: Reading, color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', route: '/admin/students', query: { is_active: true } },
  { label: '在职导师', value: 0, icon: User, color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', route: '/admin/teachers', query: { is_active: true } },
  { label: '在用教室', value: 0, icon: OfficeBuilding, color: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)', route: '/admin/rooms' , query: { is_active: true } },
  { label: '数据库连接', value: '正常', icon: Connection, color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', route: null }
])

// 图表引用
const courseDistChart = ref(null)
const teacherWorkloadChart = ref(null)
const trialEfficiencyChart = ref(null)
const scheduleTrendChart = ref(null)
const feeCompositionChart = ref(null)
const feeTrendChart = ref(null)
const balanceDistChart = ref(null)
const gradeDistChart = ref(null)
const trialFunnelChart = ref(null)
const weeklyWorkloadChart = ref(null)
const refundRateChart = ref(null)
const studentGrowthChart = ref(null)
const popularCoursesChart = ref(null)
const roomUtilizationChart = ref(null)

// 数据
const improvementRanking = ref([])
const longTermStudents = ref([])
const feeAlerts = ref([])
const unpaidStudents = ref([])
const incompleteSchedules = ref([])
const students = ref([])
const classes = ref([])
const currentKpiTitle = ref('')
// 筛选条件
const scheduleTrendDays = ref(90)
const improvementRankingLimit = ref(50)
const weeklyWorkloadDays = ref(8)
const studentGrowthMonths = ref(12)
const popularCoursesLimit = ref(5)
const roomUtilizationDays = ref(60)
const teacherWorkloadDays = ref(30)
const feeTrendMonths = ref(12)
const refundRateMonths = ref(6)
const trialEfficiencyDays = ref(30)
const trialFunnelDays = ref(30)
const longTermStudentsLimit = ref(30)
// 成绩曲线相关
const gradeCurveDialogVisible = ref(false)
const gradeCurveLoading = ref(false)
const gradeCurveData = ref(null)
const currentStudentName = ref('')
const gradeCurveChart = ref(null)
let gradeChartInstance = null

// 图表实例
let charts = {}

// 数据库连接池状态
const dbPoolStatus = ref({
  pool_size: 0,
  checked_in: 0,
  checked_out: 0,
  overflow: 0,
  total_connections: 0
})

// 获取KPI数据
const fetchKPIData = async () => {
  try {
    const response = await api.get('/statistics/kpi')
    const data = response.data
    
    let yearlyRevenue = 0
    if (hasFeature('fee_management')) {
      const currentYear = new Date().getFullYear()
      try {
        const yearResponse = await api.get('/statistics/fees/monthly-trend', {
          params: { months: 12 }
        })
        const monthlyData = yearResponse.data
        yearlyRevenue = monthlyData.reduce((sum, item) => {
          const itemYear = parseInt(item.month.split('-')[0])
          if (itemYear === currentYear) {
            return sum + item.actual_income
          }
          return sum
        }, 0)
      } catch (error) {
        window.logger.error('获取年度收入失败:', error)
      }
    }
    
    const feeKpis = hasFeature('fee_management') ? [
      { label: '本月收入', value: `¥${data.monthly_revenue.toFixed(2)}`, icon: Money, color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', route: '/admin/feemanagement' },
      { label: '当年收入', value: `¥${yearlyRevenue.toFixed(2)}`, icon: Money, color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', route: '/admin/feemanagement' },
    ] : [
      { label: '本月收入', value: '--', icon: Money, color: 'linear-gradient(135deg, #909399 0%, #b1b3b8 100%)', route: null },
      { label: '当年收入', value: '--', icon: Money, color: 'linear-gradient(135deg, #909399 0%, #b1b3b8 100%)', route: null },
    ]
    
    const feeExtraKpis = hasFeature('fee_management') ? [
      { label: '退费总额', value: `¥${(data.total_refund_amount || 0).toFixed(2)}`, icon: Money, color: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)', route: '/admin/feemanagement' },
      { label: '累计优惠额度', value: `¥${(data.total_owed_amount || 0).toFixed(2)}`, icon: Money, color: 'linear-gradient(135deg, #ffa726 0%, #fb8c00 100%)', route: '/admin/feemanagement' },
      { label: '本月续费率', value: `${data.renewal_rate || 0}%`, icon: TrendCharts, color: 'linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%)', route: '/admin/students' },
    ] : [
      { label: '退费总额', value: '--', icon: Money, color: 'linear-gradient(135deg, #909399 0%, #b1b3b8 100%)', route: null },
      { label: '累计优惠额度', value: '--', icon: Money, color: 'linear-gradient(135deg, #909399 0%, #b1b3b8 100%)', route: null },
      { label: '本月续费率', value: '--', icon: TrendCharts, color: 'linear-gradient(135deg, #909399 0%, #b1b3b8 100%)', route: null },
    ]
    
    kpiData.value = [
      ...feeKpis,
      { label: '本月转化率', value: `${data.conversion_rate || 0}%`, icon: TrendCharts, color: 'linear-gradient(135deg, #66bb6a 0%, #43a047 100%)', route: '/admin/schedules', query: { schedule_type: 'trial' } },
      { label: '今日试听课', value: data.today_trial_schedules, icon: Bell, color: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', route: '/admin/schedules', query: { schedule_type: 'trial', date: '今天' } },
      { label: '今日正式课', value: data.today_schedules - data.today_trial_schedules, icon: Bell, color: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', route: '/admin/schedules', query: { schedule_type: 'formal', date: '今天' } },
      ...feeExtraKpis,
      { label: '待补课学员数', value: data.pending_makeup_students || 0, icon: Bell, color: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', route: '/admin/schedules', query: { execution_status: 'completed', has_absent_students: true } },
      { label: '未完训排课', value: data.incomplete_schedules || 0, icon: Warning, color: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)', route: '/admin/schedules', query: { execution_status: 'pending,postponed,cancelled' } },
      { label: '已完训排课', value: data.completed_schedules || 0, icon: Warning, color: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)', route: '/admin/schedules', query: { execution_status: 'completed' } },
      { label: '总排课数', value: data.total_schedules, icon: Calendar, color: 'linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)', route: '/admin/schedules' },
      { label: '总科目数', value: data.total_courses, icon: Tickets, color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', route: '/admin/courses' },
      { label: '总班级数', value: data.active_classes, icon: OfficeBuilding, color: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', route: '/admin/classes' },
      { label: '在读学员', value: data.active_students, icon: Reading, color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', route: '/admin/students', query: { is_active: true } },
      { label: '在职导师', value: data.active_teachers, icon: User, color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', route: '/admin/teachers', query: { is_active: true } },
      { label: '数据库连接', value: '正常', icon: Connection, color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', route: null }
    ]
    
    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  } catch (error) {
    window.logger.error('获取KPI数据失败:', error)
    ElMessage.error('获取KPI数据失败')
  }
}

// 获取数据库连接池状态
const fetchDBPoolStatus = async () => {
  try {
    const response = await api.get('/statistics/db-pool-status')
    dbPoolStatus.value = response.data
    
    // 更新KPI卡片中的数据库连接状态
    const dbCard = kpiData.value.find(kpi => kpi.label === '数据库连接')
    if (dbCard) {
      const usageRate = Math.round((dbPoolStatus.value.checked_out / dbPoolStatus.value.pool_size) * 100)
      
      if (usageRate > 80) {
        dbCard.value = `繁忙(${usageRate}%)`
        dbCard.color = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)'
      } else if (usageRate > 50) {
        dbCard.value = `正常(${usageRate}%)`
        dbCard.color = 'linear-gradient(135deg, #ffa726 0%, #fb8c00 100%)'
      } else {
        dbCard.value = '空闲'
        dbCard.color = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }
    }
  } catch (error) {
    window.logger.error('获取数据库连接状态失败:', error)
    const dbCard = kpiData.value.find(kpi => kpi.label === '数据库连接')
    if (dbCard) {
      dbCard.value = '异常'
      dbCard.color = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)'
    }
  }
}

// 获取科目分布
const fetchCourseDistribution = async () => {
  try {
    const response = await api.get('/statistics/courses/distribution')
    const data = response.data
    
    if (!courseDistChart.value) return
    
    const chart = echarts.init(courseDistChart.value)
    charts.courseDist = chart
    
    const option = {
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left', top: 'middle' },
      series: [
        {
          name: '学员人数',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          emphasis: {
            label: { show: true, fontSize: 16, fontWeight: 'bold' }
          },
          data: data.map(item => ({
            name: item.course_name,
            value: item.student_count
          }))
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取科目分布失败:', error)
  }
}

// 获取课程趋势
const fetchScheduleTrend = async () => {
  try {
    const response = await api.get(`/statistics/schedules/trend?days=${scheduleTrendDays.value}`)
    const data = response.data
    
    if (!scheduleTrendChart.value) return
    
    const chart = echarts.init(scheduleTrendChart.value)
    charts.scheduleTrend = chart
    
    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['正式课', '试听课'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.map(item => item.date.substring(5))
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '正式课',
          type: 'line',
          smooth: true,
          stack: 'Total',
          data: data.map(item => item.formal_count),
          areaStyle: { opacity: 0.3 },
          itemStyle: { color: '#667eea' }
        },
        {
          name: '试听课',
          type: 'line',
          smooth: true,
          stack: 'Total',
          data: data.map(item => item.trial_count),
          areaStyle: { opacity: 0.3 },
          itemStyle: { color: '#f5576c' }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取课程趋势失败:', error)
  }
}
const handleScheduleTrendDaysChange = () => {
  fetchScheduleTrend()
}

// 获取收入构成
const fetchFeeComposition = async () => {
  try {
    const response = await api.get('/statistics/fees/composition')
    const data = response.data
    
    if (!feeCompositionChart.value) return
    
    const chart = echarts.init(feeCompositionChart.value)
    charts.feeComposition = chart
    
    const option = {
      tooltip: { trigger: 'item', formatter: '{b}: ¥{c}' },
      series: [
        {
          name: '收入',
          type: 'pie',
          radius: '50%',
          roseType: 'area',
          itemStyle: { borderRadius: 8 },
          data: data.map((item, index) => ({
            name: item.course_name,
            value: item.amount,
            itemStyle: {
              color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de'][index % 5]
            }
          }))
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取收入构成失败:', error)
  }
}

// 获取月度收入趋势
const fetchFeeTrend = async () => {
  try {
    const response = await api.get(`/statistics/fees/monthly-trend?months=${feeTrendMonths.value}`)
    const data = response.data
    
    if (!feeTrendChart.value) return
    
    const chart = echarts.init(feeTrendChart.value)
    charts.feeTrend = chart
    
    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['实收金额', '退费金额'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.map(item => item.month)
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '实收金额',
          type: 'line',
          smooth: true,
          data: data.map(item => item.actual_income),
          itemStyle: { color: '#67C23A' },
          areaStyle: { opacity: 0.3 }
        },
        {
          name: '退费金额',
          type: 'line',
          smooth: true,
          data: data.map(item => item.refund_amount),
          itemStyle: { color: '#F56C6C' }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取月度趋势失败:', error)
  }
}
const handleFeeTrendMonthsChange = () => {
  fetchFeeTrend()
}

// 获取导师工作量排行
const fetchTeacherWorkload = async () => {
  try {
    window.logger.log('[Dashboard] 开始获取导师工作量数据...');
    const response = await api.get(`/statistics/teachers/workload?days=${teacherWorkloadDays.value}`)
    const data = response.data
    
    window.logger.log('[Dashboard] 导师工作量数据:', data);
    window.logger.log('[Dashboard] 数据长度:', data.length);
    window.logger.log('[Dashboard] teacherWorkloadChart ref值:', teacherWorkloadChart.value);
    
    if (!teacherWorkloadChart.value) {
      window.logger.error('[Dashboard] ❌ teacherWorkloadChart ref为null，图表容器未找到！');
      return;
    }
    
    if (data.length === 0) {
      window.logger.warn('[Dashboard] ⚠️ 导师工作量数据为空');
      return;
    }
    
    const chart = echarts.init(teacherWorkloadChart.value)
    charts.teacherWorkload = chart
    
    const option = {
      tooltip: { 
        trigger: 'axis', 
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          const item = params[0];
          const d = data[data.length - 1 - item.dataIndex];
          return `${d.teacher_name}<br/>
                  课程数: ${d.schedule_count}节<br/>
                  总时长: ${d.total_hours}小时<br/>
                  完训率: ${d.completion_rate}%`;
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', name: '课时' },
      yAxis: {
        type: 'category',
        data: data.map(item => item.teacher_name).reverse(),
        axisLabel: { interval: 0 }
      },
      series: [
        {
          name: '授课时长(小时)',
          type: 'bar',
          label: { show: true, position: 'right' },
          emphasis: { focus: 'series' },
          data: data.map(item => item.total_hours).reverse(),
          itemStyle: { color: '#409EFF' }
        }
      ]
    }
    
    window.logger.log('[Dashboard] 设置图表配置...');
    chart.setOption(option);
    window.logger.log('[Dashboard] ✅ 导师工作量图表渲染成功');
  } catch (error) {
    window.logger.error('[Dashboard] ❌ 获取导师工作量失败:', error);
    window.logger.error('[Dashboard] 错误详情:', error.message);
    window.logger.error('[Dashboard] 错误堆栈:', error.stack);
  }
}
const handleTeacherWorkloadDaysChange = () => {
  fetchTeacherWorkload()
}

// 获取导师试听效能榜
const fetchTrialEfficiency = async () => {
  try {
    window.logger.log('[Dashboard] 开始获取导师试听效能数据...');
    
    if (!trialEfficiencyChart.value) {
      window.logger.warn('[Dashboard] trialEfficiencyChart ref为null');
      return;
    }
    
    const response = await api.get(`/statistics/teachers/trial-efficiency?days=${trialEfficiencyDays.value}`)
    const data = response.data
    
    window.logger.log('[Dashboard] 导师试听效能数据:', data);
    window.logger.log('[Dashboard] 数据长度:', data.length);
    
    if (data.length === 0) {
      window.logger.warn('[Dashboard] ⚠️ 导师试听效能数据为空');
      return;
    }
    
    const chart = echarts.init(trialEfficiencyChart.value)
    charts.trialEfficiency = chart
    
    const option = {
      tooltip: { 
        trigger: 'axis', 
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          const item = params[0];
          const d = data[data.length - 1 - item.dataIndex];
          return `${d.teacher_name}<br/>
                  试听课数: ${d.trial_count}节<br/>
                  完训数: ${d.completed_count}节<br/>
                  转化学生: ${d.converted_students}人<br/>
                  转化率: ${d.conversion_rate}%`;
        }
      },
      legend: {
        data: ['试听课时数', '转化率'],
        top: 10
      },
      grid: { 
        left: '3%', 
        right: '15%', 
        bottom: '3%', 
        containLabel: true 
      },
      xAxis: [
        {
          type: 'value',
          name: '试听课时数',
          position: 'left',
          axisLine: {
            lineStyle: { color: '#409EFF' }
          },
          axisLabel: {
            formatter: '{value} 节'
          }
        },
        {
          type: 'value',
          name: '转化率',
          position: 'right',
          axisLine: {
            lineStyle: { color: '#67C23A' }
          },
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      yAxis: {
        type: 'category',
        data: data.map(item => item.teacher_name).reverse(),
        axisLabel: { interval: 0 }
      },
      series: [
        {
          name: '试听课时数',
          type: 'bar',
          xAxisIndex: 0,
          label: { show: true, position: 'right' },
          emphasis: { focus: 'series' },
          data: data.map(item => item.trial_count).reverse(),
          itemStyle: { color: '#409EFF' }
        },
        {
          name: '转化率',
          type: 'line',
          xAxisIndex: 1,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          label: { 
            show: true, 
            position: 'right',
            formatter: '{c}%'
          },
          emphasis: { focus: 'series' },
          data: data.map(item => item.conversion_rate).reverse(),
          itemStyle: { color: '#67C23A' },
          lineStyle: { width: 3 }
        }
      ]
    }
    
    window.logger.log('[Dashboard] 设置图表配置...');
    chart.setOption(option);
    window.logger.log('[Dashboard] ✅ 导师试听效能图表渲染成功');
  } catch (error) {
    window.logger.error('[Dashboard] ❌ 获取导师试听效能失败:', error);
    window.logger.error('[Dashboard] 错误详情:', error.message);
    window.logger.error('[Dashboard] 错误堆栈:', error.stack);
  }
}
const handleTrialEfficiencyDaysChange = () => {
  fetchTrialEfficiency()
}

// 获取试听转化漏斗
const fetchTrialFunnel = async () => {
  try {
    const response = await api.get(`/statistics/funnel/trial-conversion?days=${trialFunnelDays.value}`)
    const data = response.data
    
    if (!trialFunnelChart.value) return
    
    const chart = echarts.init(trialFunnelChart.value)
    charts.trialFunnel = chart
    
    window.logger.log('漏斗原始数据:', data)
    
    // 固定三层数据的顺序：试听课总数 > 完训试听课 > 成功转化
    let funnelData = [
      { value: data.find(item => item.name === '试听课总数')?.value || 0, name: '试听课总数' },
      { value: data.find(item => item.name === '完训试听课')?.value || 0, name: '完训试听课' },
      { value: data.find(item => item.name === '成功转化(缴费)')?.value || 0, name: '成功转化(缴费)' }
    ]
    
    window.logger.log('漏斗排序后数据:', funnelData)
    
    const maxValue = Math.max(...funnelData.map(item => item.value))
    
    // 如果所有数据都是0，使用示例数据展示漏斗形状
    const isNoData = maxValue === 0
    const displayData = isNoData ? [
      { value: 100, name: '试听课总数' },
      { value: 60, name: '完训试听课' },
      { value: 30, name: '成功转化(缴费)' }
    ] : funnelData
    
    const displayMaxValue = isNoData ? 100 : maxValue
    
    const option = {
      tooltip: { 
        trigger: 'item', 
        formatter: function(params) {
          if (isNoData) {
            return `${params.name}<br/>暂无数据（示意图）`
          }
          const percent = displayMaxValue > 0 ? ((params.value / displayMaxValue) * 100).toFixed(1) : 0
          return `${params.name}<br/>数量: ${params.value}<br/>占比: ${percent}%`
        }
      },
      title: isNoData ? {
        text: '暂无数据',
        left: 'center',
        bottom: 10,
        textStyle: {
          color: '#999',
          fontSize: 12
        }
      } : undefined,
      series: [
        {
          name: '转化漏斗',
          type: 'funnel',
          left: '10%',
          top: 30,
          bottom: isNoData ? 50 : 30,
          width: '80%',
          height: '85%',
          min: 0,
          max: displayMaxValue,
          minSize: '5%',
          maxSize: '100%',
          sort: 'descending',
          gap: 2,
          funnelAlign: 'center',
          label: {
            show: true,
            position: 'inside',
            fontSize: 13,
            fontWeight: 'bold',
            color: '#fff',
            formatter: function(params) {
              if (isNoData) {
                return params.name
              }
              const percent = displayMaxValue > 0 ? ((params.value / displayMaxValue) * 100).toFixed(1) : 0
              return `${params.name}\n${params.value} (${percent}%)`
            }
          },
          labelLine: {
            length: 10,
            lineStyle: {
              width: 1,
              type: 'solid'
            }
          },
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 2,
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.2)',
            opacity: isNoData ? 0.6 : 1
          },
          emphasis: {
            label: {
              fontSize: 15
            },
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }
          },
          data: [
            {
              value: displayData[0].value,
              name: displayData[0].name,
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#667eea' },
                  { offset: 1, color: '#764ba2' }
                ])
              }
            },
            {
              value: displayData[1].value,
              name: displayData[1].name,
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#91cc75' },
                  { offset: 1, color: '#5cb85c' }
                ])
              }
            },
            {
              value: displayData[2].value,
              name: displayData[2].name,
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#fac858' },
                  { offset: 1, color: '#ee6666' }
                ])
              }
            }
          ]
        }
      ]
    }
    
    chart.setOption(option, true)
  } catch (error) {
    window.logger.error('获取漏斗数据失败:', error)
  }
}
const handleTrialFunnelDaysChange = () => {
  fetchTrialFunnel()
}

// 跳转到费用管理
const goToFeeManagement = (row) => {
  router.push({
    path: '/admin/feemanagement',
    query: { 
      student_id: row.student_id, 
      course_id: row.course_id,
      action: 'view_logs'
    }
  })
}

// 获取课时余量分布
const fetchBalanceDistribution = async () => {
  try {
    const response = await api.get('/statistics/fees/balance-distribution')
    const data = response.data
    
    if (!balanceDistChart.value) return
    
    const chart = echarts.init(balanceDistChart.value)
    charts.balanceDist = chart
    
    const option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.map(item => item.range)
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '学员数',
          type: 'bar',
          data: data.map(item => item.count),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#83bff6' },
              { offset: 1, color: '#188df0' }
            ])
          }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取课时余量分布失败:', error)
  }
}

// 获取成绩分布
const fetchGradeDistribution = async () => {
  try {
    const response = await api.get('/statistics/grades/distribution')
    const data = response.data
    
    if (!gradeDistChart.value) return
    
    const chart = echarts.init(gradeDistChart.value)
    charts.gradeDist = chart
    
    const option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['优秀(≥90%)', '良好(75-90%)', '及格(60-75%)', '不及格(<60%)'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.map(item => item.course_name)
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '优秀(≥90%)',
          type: 'bar',
          stack: 'total',
          data: data.map(item => item.excellent),
          itemStyle: { color: '#67C23A' }
        },
        {
          name: '良好(75-90%)',
          type: 'bar',
          stack: 'total',
          data: data.map(item => item.good),
          itemStyle: { color: '#409EFF' }
        },
        {
          name: '及格(60-75%)',
          type: 'bar',
          stack: 'total',
          data: data.map(item => item.pass),
          itemStyle: { color: '#E6A23C' }
        },
        {
          name: '不及格(<60%)',
          type: 'bar',
          stack: 'total',
          data: data.map(item => item.fail),
          itemStyle: { color: '#F56C6C' }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取成绩分布失败:', error)
  }
}

// 获取学员进步榜
const fetchImprovementRanking = async () => {
  try {
    const response = await api.get(`/statistics/grades/improvement-ranking?limit=${improvementRankingLimit.value}`)
    improvementRanking.value = response.data
  } catch (error) {
    window.logger.error('获取进步榜失败:', error)
  }
}
const handleImprovementRankingLimitChange = () => {
  fetchImprovementRanking()
}

// 获取长效学员榜
const fetchLongTermStudents = async () => {
  try {
    const response = await api.get(`/statistics/students/long-term-ranking?limit=${longTermStudentsLimit.value}`)
    longTermStudents.value = response.data
  } catch (error) {
    window.logger.error('获取长效学员榜失败:', error)
  }
}
const handleLongTermStudentsLimitChange = () => {
  fetchLongTermStudents()
}

// 获取收费预警
const fetchFeeAlerts = async () => {
  try {
    const response = await api.get('/statistics/fees/alerts?limit=100000')
    feeAlerts.value = response.data
  } catch (error) {
    window.logger.error('获取收费预警失败:', error)
  }
}

// 获取待缴费学员列表
const fetchUnpaidStudents = async () => {
  try {
    const response = await api.get('/statistics/fees/unpaid-students?limit=100000')
    unpaidStudents.value = response.data
  } catch (error) {
    window.logger.error('获取待缴费学员列表失败:', error)
    ElMessage.error(`获取待缴费学员列表失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 获取导师课时排行榜
const fetchWeeklyWorkload = async () => {
  chartLoading.value.weeklyWorkload = true
  try {
    window.logger.log('[Dashboard] 开始获取导师课时数据...');
    const response = await api.get(`/statistics/teachers/weekly-workload?limit=${weeklyWorkloadDays.value}`)
    const data = response.data
    
    window.logger.log('[Dashboard] 导师课时数据:', data);
    window.logger.log('[Dashboard] 数据长度:', data.length);
    window.logger.log('[Dashboard] weeklyWorkloadChart ref值:', weeklyWorkloadChart.value);
    
    if (!weeklyWorkloadChart.value) {
      window.logger.error('[Dashboard] ❌ weeklyWorkloadChart ref为null，图表容器未找到！');
      return;
    }
    
    if (data.length === 0) {
      window.logger.warn('[Dashboard] ⚠️ 导师课时数据为空');
      return;
    }
    
    const chart = echarts.init(weeklyWorkloadChart.value)
    charts.weeklyWorkload = chart
    
    const option = {
      tooltip: { 
        trigger: 'axis', 
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          const item = params[0];
          const d = data[data.length - 1 - item.dataIndex];
          return `${d.teacher_name}<br/>
                  课程数: ${d.schedule_count}节<br/>
                  总时长: ${d.total_hours}小时`;
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', name: '课时' },
      yAxis: {
        type: 'category',
        data: data.map(item => item.teacher_name).reverse(),
        axisLabel: { interval: 0 }
      },
      series: [
        {
          name: '授课时长(小时)',
          type: 'bar',
          label: { show: true, position: 'right' },
          emphasis: { focus: 'series' },
          data: data.map(item => item.total_hours).reverse(),
          itemStyle: { color: '#409EFF' }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('[Dashboard] 获取导师课时失败:', error)
    ElMessage.error(`获取导师课时失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    chartLoading.value.weeklyWorkload = false
  }
}
const handleWeeklyWorkloadDaysChange = () => {
  fetchWeeklyWorkload()
}

// 获取未完训排课列表
const fetchIncompleteSchedules = async () => {
  try {
    const response = await api.get('/statistics/schedules/incomplete-list?limit=100000')
    incompleteSchedules.value = response.data
  } catch (error) {
    window.logger.error('获取未完训排课失败:', error)
    ElMessage.error(`获取未完训排课失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 获取退费率趋势（近半年）
const fetchRefundRate = async () => {
  chartLoading.value.refundRate = true
  try {
    const response = await api.get(`/statistics/fees/refund-rate?months=${refundRateMonths.value}`)
    const data = response.data
    
    if (!refundRateChart.value) return
    
    const chart = echarts.init(refundRateChart.value)
    charts.refundRate = chart
    
    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['退费率'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.map(item => item.month)
      },
      yAxis: { 
        type: 'value',
        name: '退费率(%)',
        axisLabel: { formatter: '{value}%' }
      },
      series: [
        {
          name: '退费率',
          type: 'line',
          smooth: true,
          data: data.map(item => item.refund_rate),
          itemStyle: { color: '#F56C6C' },
          areaStyle: { opacity: 0.3 }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取退费率趋势失败:', error)
    ElMessage.error(`获取退费率趋势失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    chartLoading.value.refundRate = false
  }
}
const handleRefundRateMonthsChange = () => {
  fetchRefundRate()
}

// 获取新学员增长率
const fetchStudentGrowth = async () => {
  chartLoading.value.studentGrowth = true
  try {
    const response = await api.get(`/statistics/students/growth-rate?months=${studentGrowthMonths.value}`)
    const data = response.data
    
    if (!studentGrowthChart.value) return
    
    const chart = echarts.init(studentGrowthChart.value)
    charts.studentGrowth = chart
    
    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['新增学员数', '增长率'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.map(item => item.month)
      },
      yAxis: [
        {
          type: 'value',
          name: '学员数',
          position: 'left'
        },
        {
          type: 'value',
          name: '增长率(%)',
          position: 'right',
          axisLabel: { formatter: '{value}%' }
        }
      ],
      series: [
        {
          name: '新增学员数',
          type: 'bar',
          data: data.map(item => item.new_students),
          itemStyle: { color: '#409EFF' }
        },
        {
          name: '增长率',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          data: data.map(item => item.growth_rate),
          itemStyle: { color: '#67C23A' }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取学员增长率失败:', error)
    ElMessage.error(`获取学员增长率失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    chartLoading.value.studentGrowth = false
  }
}
const handleStudentGrowthMonthsChange = () => {
  fetchStudentGrowth()
}

// 获取热门科目TopN
const fetchPopularCourses = async () => {
  chartLoading.value.popularCourses = true
  try {
    const response = await api.get(`/statistics/courses/popular-topN?limit=${popularCoursesLimit.value}`)
    const data = response.data
    
    if (!popularCoursesChart.value) return
    
    const chart = echarts.init(popularCoursesChart.value)
    charts.popularCourses = chart
    
    const option = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.map(item => item.course_name),
        axisLabel: { interval: 0, rotate: 30 }
      },
      yAxis: { type: 'value', name: '学员数' },
      series: [
        {
          name: '学员数',
          type: 'bar',
          data: data.map(item => item.student_count),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#83bff6' },
              { offset: 1, color: '#188df0' }
            ])
          },
          label: { show: true, position: 'top' }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取热门科目失败:', error)
    ElMessage.error(`获取热门科目失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    chartLoading.value.popularCourses = false
  }
}
const handlePopularCoursesLimitChange = () => {
  fetchPopularCourses()
}

// 获取各教室利用率
const fetchRoomUtilization = async () => {
  chartLoading.value.roomUtilization = true
  try {
    const response = await api.get(`/statistics/rooms/utilization?days=${roomUtilizationDays.value}`)
    const data = response.data
    
    if (!roomUtilizationChart.value) return
    
    const chart = echarts.init(roomUtilizationChart.value)
    charts.roomUtilization = chart
    
    const option = {
      tooltip: { 
        trigger: 'axis', 
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          const item = params[0];
          const d = data[data.length - 1 - item.dataIndex];
          return `${d.room_name}<br/>
                  容量: ${d.capacity}人<br/>
                  课程数: ${d.schedule_count}节<br/>
                  平均利用率: ${d.avg_utilization}%`;
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', name: '利用率(%)', axisLabel: { formatter: '{value}%' } },
      yAxis: {
        type: 'category',
        data: data.map(item => item.room_name).reverse(),
        axisLabel: { interval: 0 }
      },
      series: [
        {
          name: '平均利用率',
          type: 'bar',
          label: { show: true, position: 'right', formatter: '{c}%' },
          emphasis: { focus: 'series' },
          data: data.map(item => item.avg_utilization).reverse(),
          itemStyle: { color: '#67C23A' }
        }
      ]
    }
    
    chart.setOption(option)
  } catch (error) {
    window.logger.error('获取教室利用率失败:', error)
    ElMessage.error(`获取教室利用率失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    chartLoading.value.roomUtilization = false
  }
}
const handleRoomUtilizationDaysChange = () => {
  fetchRoomUtilization()
}

// 获取学生数据
const fetchStudents = async () => {
  try {
    const response = await api.get('/students', { params: { skip: 0, limit: 100000 } })
    students.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取学生数据失败:', error)
  }
}

// 获取班级数据
const fetchClasses = async () => {
  try {
    const response = await api.get('/classes', { params: { skip: 0, limit: 100000 } })
    classes.value = response.data.items || response.data
  } catch (error) {
    window.logger.error('获取班级数据失败:', error)
  }
}

// 学员详细信息辅助函数
const getStudentDetail = (studentId) => {
  return students.value.find(s => s.id === studentId)
}

const getStudentCode = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? student.code : '-'
}

const getStudentSchool = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.school || '-') : '-'
}

const getStudentGrade = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.grade || '-') : '-'
}

const getStudentJoinDate = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.enrollment_date || '-') : '-'
}

const getStudentContact = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.contact_person || '-') : '-'
}

const getStudentPhone = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.contact_phone || '-') : '-'
}

const getStudentEmail = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? (student.email || '-') : '-'
}

const getStudentClasses = (studentId) => {
  const student = getStudentDetail(studentId)
  if (!student || !student.class_ids || !Array.isArray(student.class_ids) || student.class_ids.length === 0) {
    return '-'
  }
  const classNames = student.class_ids.map(classId => {
    const cls = classes.value.find(c => c.id === classId)
    return cls ? cls.name : `ID:${classId}`
  })
  return classNames.join('、')
}

const getStudentIsActive = (studentId) => {
  const student = getStudentDetail(studentId)
  return student ? student.is_active : false
}

// 显示成绩曲线
const showGradeCurve = async (row) => {
  currentStudentName.value = row.student_name
  gradeCurveDialogVisible.value = true
  gradeCurveLoading.value = true
  
  try {
    const response = await api.get(`/grades/student-trend/${row.student_id}`)
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

const goToStudentEvaluation = (row) => {
  router.push({ path: '/admin/evaluations', query: { student_id: row.student_id } })
}

// 渲染成绩曲线图表
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

// 图表resize处理
const handleChartResize = () => {
  if (gradeChartInstance) {
    gradeChartInstance.resize()
  }
}

// 清理成绩曲线图表
const cleanupGradeChart = () => {
  if (gradeChartInstance) {
    gradeChartInstance.dispose()
    gradeChartInstance = null
  }
  window.removeEventListener('resize', handleChartResize)
}

// 监听对话框关闭
watch(gradeCurveDialogVisible, (newVal) => {
  if (!newVal) {
    cleanupGradeChart()
  }
})

// 刷新所有数据
const refreshData = async () => {
  loading.value = true
  try {
    const promises = [
      fetchKPIData(),
      fetchCourseDistribution(),
      fetchTeacherWorkload(),
      fetchTrialEfficiency(),
      fetchScheduleTrend(),
      fetchBalanceDistribution(),
      fetchLongTermStudents(),
      fetchTrialFunnel(),
      fetchStudents(),
      fetchClasses(),
      fetchWeeklyWorkload(),
      fetchIncompleteSchedules(),
      fetchStudentGrowth(),
      fetchPopularCourses(),
      fetchRoomUtilization(),
      fetchDBPoolStatus()
    ]
    if (hasFeature('fee_management')) {
      promises.push(fetchFeeComposition(), fetchFeeTrend(), fetchFeeAlerts(), fetchUnpaidStudents(), fetchRefundRate())
    }
    if (hasFeature('grade_trend')) {
      promises.push(fetchGradeDistribution(), fetchImprovementRanking())
    }
    await Promise.all(promises)
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

// 显示KPI详细数据
const showKpiDetail = async (label) => {
  currentKpiTitle.value = label
  kpiDetailData.value = { loading: true, data: [] }
  kpiDetailDialogVisible.value = true
  
  try {
    let response
    switch (label) {
      case '本月收入':
        const now = new Date()
        const year = now.getFullYear()
        const month = String(now.getMonth() + 1).padStart(2, '0')
        response = await api.get(`/statistics/fees/monthly-details?year=${year}&month=${month}`)
        break
      case '当年收入':
        const currentYear = new Date().getFullYear()
        response = await api.get(`/statistics/fees/yearly-details?year=${currentYear}`)
        break
      case '退费总额':
        response = await api.get('/statistics/fees/refund-details')
        break
      case '累计优惠额度':
        response = await api.get('/statistics/fees/owed-details')
        break
      case '本月续费率':
        response = await api.get('/statistics/students/renewal-details')
        break
      case '本月转化率':
        response = await api.get('/statistics/schedules/conversion-details?days=30')
        break
      default:
        kpiDetailData.value = { loading: false, data: [] }
        return
    }
    
    kpiDetailData.value = { loading: false, data: response.data || [] }
  } catch (error) {
    window.logger.error(`获取${label}详细数据失败:`, error)
    kpiDetailData.value = { loading: false, data: [], error: error.message }
  }
}

// 切换营收显示
const toggleRevenueVisibility = () => {
  if (hideRevenue.value) {
    passwordDialogVisible.value = true
    passwordInput.value = ''
  } else {
    hideRevenue.value = true
    localStorage.setItem('hideRevenue', 'true')
    ElMessage.success('营收信息已隐藏')
  }
}

// 验证密码并显示营收
const verifyPasswordAndShowRevenue = async () => {
  if (!passwordInput.value) {
    ElMessage.warning('请输入密码')
    return
  }
  
  try {
    const response = await api.post('/auth/verify-password', {
      password: passwordInput.value
    })
    
    if (response.data.valid) {
      passwordDialogVisible.value = false  // 立即关闭对话框
      hideRevenue.value = false // 显示营收信息
      localStorage.setItem('hideRevenue', 'false')
      passwordInput.value = ''
      ElMessage.success('营收信息已恢复显示')
      
      setTimeout(() => {
        refreshData()
      }, 300)
    }
  } catch (error) {
    window.logger.error('密码验证失败:', error)
    ElMessage.error('密码验证失败')
  }
}

// 切换全屏
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// 导出图片
const exportDashboard = async () => {
  try {
    ElMessage.info('正在生成图片...')
    const element = document.querySelector('.dashboard-container')
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#f5f7fa'
    })
    
    const link = document.createElement('a')
    link.download = `运营大屏_${new Date().getTime()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    
    ElMessage.success('导出成功')
  } catch (error) {
    window.logger.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// KPI卡片点击跳转
const handleKpiClick = (kpi) => {
  const detailLabels = ['本月收入', '当年收入', '退费总额', '累计优惠额度', '本月续费率', '本月转化率']
  if (detailLabels.includes(kpi.label)) {
    showKpiDetail(kpi.label)
    return
  }
  
  if (!kpi.route) {
    if (kpi.label === '数据库连接') {
      showDBPoolDetail()
    }
    return
  }
  
  const query = {}
  if (kpi.query) {
    Object.keys(kpi.query).forEach(key => {
      query[key] = kpi.query[key]
    })
  }
  
  router.push({
    path: kpi.route,
    query: query
  })
}

// 显示数据库连接池详情
const showDBPoolDetail = () => {
  const status = dbPoolStatus.value
  const usageRate = Math.round((status.checked_out / status.pool_size) * 100)
  
  let message = `数据库连接池状态：\n`
  message += `━━━━━━━━━━━━━━━━━━━━\n`
  message += `连接池大小：${status.pool_size}\n`
  message += `已使用连接：${status.checked_out}\n`
  message += `空闲连接：${status.checked_in}\n`
  message += `溢出连接：${status.overflow}\n`
  message += `总连接数：${status.total_connections}\n`
  message += `━━━━━━━━━━━━━━━━━━━━\n`
  message += `使用率：${usageRate}%\n`
  
  if (usageRate > 80) {
    message += `\n⚠️ 警告：连接池使用率过高！`
  } else if (usageRate > 50) {
    message += `\n✅ 状态：正常使用中`
  } else {
    message += `\n✅ 状态：连接充足`
  }
  
  ElMessage({
    message: message,
    type: usageRate > 80 ? 'warning' : 'success',
    duration: 5000,
    showClose: true
  })
}

// 跳转到学员详情
const goToStudentDetail = (studentId) => {
  router.push({
    path: '/admin/students',
    query: { student_id: studentId }
  })
}

// 跳转到课程安排详情
const goToScheduleDetail = (scheduleId) => {
  router.push({
    path: '/admin/schedules',
    query: { schedule_id: scheduleId }
  })
}

// 窗口resize处理
const handleResize = () => {
  Object.values(charts).forEach(chart => {
    if (chart && typeof chart.resize === 'function') {
      chart.resize()
    }
  })
}

// 初始化
onMounted(async () => {
  await nextTick()
  await refreshData()
  
  // 设置30分钟自动刷新
  refreshTimer = setInterval(refreshData, 30 * 60 * 1000)
  
  // 监听窗口resize
  window.addEventListener('resize', handleResize)
})

// 清理
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  
  Object.values(charts).forEach(chart => {
    if (chart) {
      chart.dispose()
    }
  })
  
  cleanupGradeChart()

  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 60px);
  transition: all 0.3s ease;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.dashboard-container.fullscreen {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  width: 100vw;
  max-width: 100vw;
  margin: 0;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 5px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.dashboard-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 10px;
}

.last-update {
  font-size: 14px;
  color: #909399;
}

.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;  /* 允许按钮换行 */
}

.kpi-section {
  margin-bottom: 15px;
}

.kpi-card {
  border-radius: 12px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.kpi-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.income-card {
  border: 2px solid #67C23A;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

.income-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(103, 194, 58, 0.3);
}

.kpi-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.kpi-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.kpi-info {
  flex: 1;
}

.kpi-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.kpi-label {
  font-size: 14px;
  color: #909399;
}

.chart-section {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 12px;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #303133;
}

.chart-container {
  width: 100%;
  height: 300px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 5px;
    padding: 5px;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .dashboard-title {
    font-size: 20px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-start;  /* 改为左对齐 */
    flex-wrap: wrap;  /* 确保允许换行 */
    gap: 8px;  /* 添加间距 */
  }
  
  .header-right .el-button {
    flex: 1 1 calc(50% - 8px);  /* 每行显示2个按钮 */
    min-width: 120px;  /* 设置最小宽度 */
    font-size: 14px;
  }
  
  .kpi-value {
    font-size: 22px;
  }
  
  .kpi-icon {
    width: 50px;
    height: 50px;
  }
  
  .chart-container {
    height: 250px;
  }
}

@media (max-width: 480px) {
  .dashboard-title {
    font-size: 18px;
  }
  
  .kpi-value {
    font-size: 18px;
  }
  
  .kpi-label {
    font-size: 12px;
  }
  
  .header-right .el-button {
    flex: 1 1 100%;  /* 每行显示1个按钮 */
    min-width: auto;
    font-size: 13px;
    padding: 8px 12px;
  }
  
  .header-right .el-button span {
    display: inline;  /* 保持显示文字 */
  }
}

/* 全屏模式优化 */
.dashboard-container.fullscreen .dashboard-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  margin: 0 auto 5px;
  max-width: 1800px;
}

.dashboard-container.fullscreen .dashboard-title {
  color: #303133;
}

.dashboard-container.fullscreen .last-update {
  color: #909399;
}

.dashboard-container.fullscreen .kpi-card,
.dashboard-container.fullscreen .chart-card {
  background: rgba(255, 255, 255, 0.95);
}

.dashboard-container.fullscreen .el-row {
  max-width: 1800px;
  margin: 0 auto 5px;
}

/* 学员信息 Tooltip 样式 */
.student-info-tooltip {
  max-width: 400px !important;
}

.student-detail-info {
  padding: 8px 0;
  line-height: 1.8;
}

.student-detail-info .info-item {
  margin-bottom: 4px;
  font-size: 13px;
}

.student-detail-info .info-item strong {
  color: #606266;
  display: inline-block;
  min-width: 100px;
}
</style>