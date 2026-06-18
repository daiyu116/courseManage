// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
/**
 * License 状态管理
 * 前端全局单例
 */
import { reactive } from 'vue'
import api from './api'

export const FEATURES = {
  GRADE_TREND: 'grade_trend',
  FEE_MANAGEMENT: 'fee_management',
  SMART_SCHEDULING: 'smart_scheduling',
  WECHAT_NOTIFY: 'wechat_notify',
  SMART_COMMAND: 'smart_command',
  DASHBOARD_VIEW: 'dashboard_view',
  FLOATING_SPHERE: 'floating_sphere',
  DATABASE_MANAGEMENT: 'database_management',
  STUDENT_EVALUATION: 'student_evaluation',
}

export const FEATURE_NAMES = {
  [FEATURES.GRADE_TREND]: '学员成绩管理',
  [FEATURES.FEE_MANAGEMENT]: '费用管理',
  [FEATURES.SMART_SCHEDULING]: '智能算法排课',
  [FEATURES.WECHAT_NOTIFY]: '微信通知管理',
  [FEATURES.SMART_COMMAND]: '智能指令管理',
  [FEATURES.DASHBOARD_VIEW]: '运营大屏',
  [FEATURES.FLOATING_SPHERE]: '全站快捷按钮',
  [FEATURES.DATABASE_MANAGEMENT]: '数据库管理',
  [FEATURES.STUDENT_EVALUATION]: '学员评价管理',
}

export const FEATURE_DESCRIPTIONS = {
  [FEATURES.GRADE_TREND]: {
    highlights: '成绩可视化、趋势分析、多维度对比',
    details: '为学员成绩管理提供深度分析能力：\n• 成绩录入：支持单条添加与批量添加，可同时为不同学员、不同科目录入成绩\n• 成绩变化追踪：对比历次成绩变化，直观显示上升/下降趋势\n• 成绩比例趋势图：基于ECharts的可视化趋势图，支持按科目、班级、学员多维度筛选对比\n• 辅助教学决策：通过数据洞察学员学习轨迹，及时发现学习问题并调整教学策略',
  },
  [FEATURES.FEE_MANAGEMENT]: {
    highlights: '缴费/退费全流程、收费提醒、报表导出',
    details: '覆盖课费管理全流程闭环：\n• 课费项管理：新增/编辑学员课费项，关联科目与班级，记录应缴金额\n• 缴费记录：支持现金/转账/微信/支付宝等多种缴费途径，可录入优惠金额与收费日期\n• 退费管理：完整的退费流程，记录退费金额、退费途径、退费日期与退费说明\n• 收费提醒：自动识别待缴费项，一键发送提醒通知\n• 累计统计：自动汇总累计缴费、累计退费、累计优惠金额\n• 报表导出：一键导出所有课费项列表，便于财务对账与归档',
  },
  [FEATURES.SMART_SCHEDULING]: {
    highlights: '遗传/回溯/混合三种算法、约束自动满足、排课预览',
    details: '用智能算法替代手动排课，大幅提升排课效率：\n• 遗传算法：适合大规模排课场景，通过选择、交叉、变异等操作全局搜索较优解\n• 回溯算法：精确搜索最优解，适合中小规模排课，确保无冲突\n• 混合算法（推荐）：先用回溯算法生成高质量初始解，再用遗传算法优化，兼顾效率与质量\n• 约束自动满足：自动遵守硬性约束（导师/学员/班级/教室时间不可冲突）与软性约束（偏好时段等）\n• 排课预览：生成结果可逐条查看、编辑修改后再保存，不满意可重新生成\n• 按班级排课：支持指定部分班级进行智能排课，灵活控制排课范围',
  },
  [FEATURES.WECHAT_NOTIFY]: {
    highlights: '企业微信Webhook推送、课程提醒自动化、多群分流',
    details: '通过企业微信群机器人实现消息自动推送：\n• 导师信息群推送：每日自动向导师群发送当日课程安排提醒，包含上课时间、班级、教室等信息\n• 班级信息群推送：向班级群发送课程安排通知，方便学员及家长及时了解上课信息\n• 综合管理通知：系统关键事件（如新增排课、请假调课等）实时推送到管理群\n• Webhook配置：在站点设置中配置各群机器人Webhook地址，即配即用\n• 与邮件提醒互补：可同时启用邮件+微信双通道通知，确保信息触达',
  },
  [FEATURES.SMART_COMMAND]: {
    highlights: '自然语言操作、AI大模型解析、规则解析兜底',
    details: '用一句话完成日常操作，告别繁琐表单填写：\n• 自然语言指令：输入如"添加科目数学""张老师明天请假""给三年级排一节数学课"等自然语言即可完成操作\n• AI解析模式（推荐）：接入OpenAI/智谱AI/自定义大模型，智能理解指令意图并执行，支持复杂多步操作\n• 规则解析模式：基于正则匹配的本地解析，无需AI服务，响应速度快，作为AI不可用时的兜底方案\n• 自动降级：AI解析失败时自动切换到规则解析，确保指令始终可执行\n• 指令示例库：内置常用指令示例，点击即可快速执行\n• 批量测试：支持对指令示例进行AI/正则批量对比测试，验证解析准确率',
  },
  [FEATURES.DASHBOARD_VIEW]: {
    highlights: 'KPI看板、多维度图表、试听转化漏斗、全屏展示',
    details: '运营数据一屏尽览，辅助管理决策：\n• 核心KPI指标：在读学员数、试听学员数、导师人数、本月课次、出勤率、本月续费率、本月收入、当年收入、退费总额、累计优惠额度等\n• 科目分布图：直观展示各科目在读学员分布，了解课程热度\n• 导师课时排行榜：按周统计导师课时量，评估工作量分布\n• 收入构成分析：按科目/班级维度展示收入占比\n• 月度收入趋势：按月展示收入变化走势\n• 试听转化漏斗：分析各导师试听到正式报名的转化率\n• 导师工作量排行：综合评估导师效能\n• KPI详细数据：点击KPI卡片可查看明细数据表\n• 全屏模式与导出图片：支持全屏展示，可导出为图片用于汇报',
  },
  [FEATURES.FLOATING_SPHERE]: {
    highlights: '悬浮快捷入口、可拖拽定位、自动吸附边缘',
    details: '桌面端悬浮快捷操作面板，常用功能触手可及：\n• 快捷菜单：一键打开运营大屏、新增科目、新增导师、新增学员、新增班级、新增排课、新增成绩、新增请假、课费管理等常用功能\n• 智能显隐：根据用户角色和授权状态自动过滤可见菜单项，未授权功能显示提示\n• 拖拽定位：可自由拖拽到屏幕任意位置，松手后自动吸附到最近的屏幕边缘\n• 折叠/展开：点击可展开菜单面板，再次点击折叠为球形图标，不遮挡工作区域\n• 移动端适配：支持触摸拖拽与点击操作',
  },
  [FEATURES.DATABASE_MANAGEMENT]: {
    highlights: '手动/自动备份、一键恢复、备份文件管理',
    details: '全方位保障数据安全，防止数据丢失：\n• 手动备份：一键导出SQL备份文件，适合重大操作前手动创建快照\n• 自动备份：可配置定时自动备份，支持每天/每12小时/每6小时/每周四种频率，自动执行无需人工干预\n• 自动清理：可设置保留备份数量（1-90份），超过后自动删除最旧的备份文件，节省磁盘空间\n• 数据库恢复：从备份文件一键还原数据库，操作前有二次确认防止误操作\n• 备份文件管理：列表查看所有备份文件（文件名、类型、大小、创建时间），支持下载到本地归档与删除无用备份\n• 立即执行：除定时备份外，还可随时手动触发一次备份任务',
  },
  [FEATURES.STUDENT_EVALUATION]: {
    highlights: '综合能力画像、单科能力画像、雷达图展示、自定义评价维度',
    details: '全方位学员能力评价与画像系统：\n• 综合能力画像：支持"学习态度/知识掌握/实践能力/创新思维/协作素养"和"德智体美劳"两种五维评价模式\n• 单科能力画像：按学科类型（语言/数学/理科/文科/艺术/体育/自定义）配置专属评价维度\n• 雷达图可视化：直观展示学员能力分布，支持历史趋势对比\n• 评价模板管理：内置6大学科类型预设模板，机构可自定义维度\n• 评价记录管理：支持按学员、科目、评价周期筛选，记录优势与待提升方面\n• 与科目管理、学员管理联动：评价数据关联学员与科目，形成完整能力档案',
  },
}

export const LICENSE_TYPES = {
  trialA:     { name: '试用授权', days: 3 },
  trialB:     { name: '试用授权', days: 7 },
  monthly:    { name: '月度订阅', days: 30 },
  quarterly:  { name: '季度订阅', days: 90 },
  semiannual: { name: '半年订阅', days: 180 },
  annual:     { name: '年度订阅', days: 365 },
  perpetual:  { name: '永久授权', days: null },
}

export const FEATURE_PRICES = {
  [FEATURES.FLOATING_SPHERE]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.SMART_COMMAND]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.DASHBOARD_VIEW]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.WECHAT_NOTIFY]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.GRADE_TREND]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.FEE_MANAGEMENT]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.SMART_SCHEDULING]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.DATABASE_MANAGEMENT]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
  [FEATURES.STUDENT_EVALUATION]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 96.99 },
}

export function calcTotalPrice(selectedFeatures, licenseType) {
  if (!selectedFeatures.length || !licenseType) return 0
  let total = 0
  for (const feat of selectedFeatures) {
    const priceTable = FEATURE_PRICES[feat]
    if (priceTable && priceTable[licenseType] !== undefined) {
      total += priceTable[licenseType]
    }
  }
  return total
}

export const licenseState = reactive({
  loaded: false,
  activated: false,
  licenseType: '',
  licenseTypeName: '',
  organizationName: '',
  features: {},
  expiryDate: null,
  issuedAt: null,
  machineCode: '',
  trialAvailable: true,
  deactivatedLicenses: [],
  licenseKey: '',
  referralCode: '',
  referralActivated: false,
  referralThreshold: 0,
  discountPercent: 0,
  rebatePercent: 0,
  totalSpending: 0,
  siteName: '',
  contactPerson: '',
  contactPhone: '',
  contactEmail: '',
  contactWechat: '',
})

export async function loadLicenseStatus() {
  try {
    const response = await api.get('/license/status')
    const d = response.data
    const mapped = {
      loaded: true,
      activated: d.activated,
      licenseType: d.license_type || '',
      licenseTypeName: d.license_type_name || '',
      organizationName: d.organization_name || '',
      features: d.features || {},
      expiryDate: d.expiry_date || null,
      issuedAt: d.issued_at || null,
      machineCode: d.machine_code || '',
      trialAvailable: d.trial_available ?? true,
      deactivatedLicenses: d.deactivated_licenses || [],
      licenseKey: d.license_key || '',
      referralCode: d.referral_code || '',
      referralActivated: d.referral_activated || false,
      referralThreshold: d.referral_threshold || 0,
      discountPercent: d.discount_percent != null ? d.discount_percent : 0,
      rebatePercent: d.rebate_percent != null ? d.rebate_percent : 0,
      totalSpending: d.total_spending || 0,
      siteName: d.site_name || '',
      contactPerson: d.contact_person || '',
      contactPhone: d.contact_phone || '',
      contactEmail: d.contact_email || '',
      contactWechat: d.contact_wechat || '',
    }
    Object.assign(licenseState, mapped)
  } catch (error) {
    console.error('加载 License 状态失败:', error)
    licenseState.loaded = true
  }
}

export function hasFeature(featureName) {
  if (!licenseState.activated) return false
  return !!licenseState.features[featureName]
}

export async function activateLicense(licenseKey, selectedFeatures = null, contactInfo = {}) {
  const body = { license_key: licenseKey }
  if (selectedFeatures && selectedFeatures.length) {
    body.selected_features = selectedFeatures
  }
  if (contactInfo.organization_name) body.organization_name = contactInfo.organization_name
  if (contactInfo.contact_person) body.contact_person = contactInfo.contact_person
  if (contactInfo.contact_phone) body.contact_phone = contactInfo.contact_phone
  if (contactInfo.contact_email) body.contact_email = contactInfo.contact_email
  if (contactInfo.contact_wechat) body.contact_wechat = contactInfo.contact_wechat
  if (contactInfo.remarks) body.remarks = contactInfo.remarks
  const response = await api.post('/license/activate', body)
  await loadLicenseStatus()
  return response.data
}

export async function applyLicense(contactInfo, selectedFeatures, applyType = 'new', licenseType = '', referralCode = '') {
  const body = {
    organization_name: contactInfo.organization_name || '',
    contact_person: contactInfo.contact_person || '',
    contact_phone: contactInfo.contact_phone || '',
    contact_email: contactInfo.contact_email || '',
    contact_wechat: contactInfo.contact_wechat || '',
    remarks: contactInfo.remarks || '',
    selected_features: selectedFeatures || [],
    license_type: licenseType || '',
    apply_type: applyType,
    referral_code: referralCode || '',
  }
  const response = await api.post('/license/apply', body)
  return response.data
}

export async function previewAddonLicense(licenseKey) {
  const response = await api.post('/license/preview-addon', { license_key: licenseKey })
  return response.data
}

export async function deactivateLicense() {
  const response = await api.post('/license/deactivate')
  await loadLicenseStatus()
  return response.data
}

export async function deactivateFeature(featureName) {
  const response = await api.post(`/license/deactivate-feature/${featureName}`)
  await loadLicenseStatus()
  return response.data
}

export async function getMachineCode() {
  const response = await api.get('/license/machine-code')
  return response.data.machine_code
}

export async function notifySupplierView(data) {
  const response = await api.post('/license/notify-supplier-view', data)
  return response.data
}

export async function submitFeedback(data) {
  const response = await api.post('/license/feedback', data)
  return response.data
}

export async function requestReplaceLicense(data) {
  const response = await api.post('/license/request-replace', data)
  return response.data
}