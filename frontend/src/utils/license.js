// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
/**
 * License 状态管理
 * 前端全局单例
 */
import { reactive } from 'vue'
import api from './api'
import i18n from '@/locales'

const { t } = i18n.global

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
  [FEATURES.GRADE_TREND]: 'license.featureGradeTrend',
  [FEATURES.FEE_MANAGEMENT]: 'license.featureFeeManagement',
  [FEATURES.SMART_SCHEDULING]: 'license.featureSmartScheduling',
  [FEATURES.WECHAT_NOTIFY]: 'license.featureWechatNotify',
  [FEATURES.SMART_COMMAND]: 'license.featureSmartCommand',
  [FEATURES.DASHBOARD_VIEW]: 'license.featureDashboardView',
  [FEATURES.FLOATING_SPHERE]: 'license.featureFloatingSphere',
  [FEATURES.DATABASE_MANAGEMENT]: 'license.featureDatabaseManagement',
  [FEATURES.STUDENT_EVALUATION]: 'license.featureStudentEvaluation',
}

export const FEATURE_DESCRIPTIONS = {
  [FEATURES.GRADE_TREND]: {
    highlights: 'license.featureGradeTrendHighlights',
    details: 'license.featureGradeTrendDetails',
  },
  [FEATURES.FEE_MANAGEMENT]: {
    highlights: 'license.featureFeeManagementHighlights',
    details: 'license.featureFeeManagementDetails',
  },
  [FEATURES.SMART_SCHEDULING]: {
    highlights: 'license.featureSmartSchedulingHighlights',
    details: 'license.featureSmartSchedulingDetails',
  },
  [FEATURES.WECHAT_NOTIFY]: {
    highlights: 'license.featureWechatNotifyHighlights',
    details: 'license.featureWechatNotifyDetails',
  },
  [FEATURES.SMART_COMMAND]: {
    highlights: 'license.featureSmartCommandHighlights',
    details: 'license.featureSmartCommandDetails',
  },
  [FEATURES.DASHBOARD_VIEW]: {
    highlights: 'license.featureDashboardViewHighlights',
    details: 'license.featureDashboardViewDetails',
  },
  [FEATURES.FLOATING_SPHERE]: {
    highlights: 'license.featureFloatingSphereHighlights',
    details: 'license.featureFloatingSphereDetails',
  },
  [FEATURES.DATABASE_MANAGEMENT]: {
    highlights: 'license.featureDatabaseManagementHighlights',
    details: 'license.featureDatabaseManagementDetails',
  },
  [FEATURES.STUDENT_EVALUATION]: {
    highlights: 'license.featureStudentEvaluationHighlights',
    details: 'license.featureStudentEvaluationDetails',
  },
}

export const LICENSE_TYPES = {
  trialA:     { name: 'license.trialLicense', days: 3 },
  trialB:     { name: 'license.trialLicense', days: 7 },
  monthly:    { name: 'license.monthlyLicense', days: 30 },
  quarterly:  { name: 'license.quarterlyLicense', days: 90 },
  semiannual: { name: 'license.semiannualLicense', days: 180 },
  annual:     { name: 'license.annualLicense', days: 365 },
  perpetual:  { name: 'license.perpetualLicense', days: null },
}

export const FEATURE_PRICES = {
  [FEATURES.FLOATING_SPHERE]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.SMART_COMMAND]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.DASHBOARD_VIEW]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.WECHAT_NOTIFY]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.GRADE_TREND]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.FEE_MANAGEMENT]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.SMART_SCHEDULING]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.DATABASE_MANAGEMENT]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
  [FEATURES.STUDENT_EVALUATION]: { trialA: 1.99, trialB: 2.99, monthly: 6.99, quarterly: 17.99, semiannual: 29.99, annual: 49.99, perpetual: 196.99 },
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