// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <el-config-provider :locale="elementLocale">
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="site-title">
          <img v-if="siteLogo" :src="getFullLogoUrl(siteLogo)" class="site-logo" :alt="t('app.orgLogo')" />
          <span class="site-name">{{ siteName || '' }}</span>
          <span class="system-name">{{ t('app.systemName') }}</span>
        </div>
        <div class="header-buttons">
          <el-button type="success" @click="goBack">
            <el-icon><Monitor /></el-icon>
            <span class="btn-text">{{ t('app.adminPanel') }}</span>
          </el-button>
          <el-button type="primary" @click="goToScheduleView" class="nav-btn">
            <el-icon><Reading /></el-icon>
            <span class="btn-text">{{ t('app.courseView') }}</span>
          </el-button>
          <el-button v-if="canAccessDashboard" type="warning" @click="goToDashboardView" class="nav-btn">
            <el-icon><DataAnalysis /></el-icon>
            <span class="btn-text">{{ t('app.dashboardView') }}</span>
          </el-button>
          <el-tooltip v-else :content="t('app.dashboardViewTip')" placement="bottom">
            <el-button type="warning" class="nav-btn" disabled>
              <el-icon><Lock /></el-icon>
              <span class="btn-text">{{ t('app.dashboardView') }}</span>
            </el-button>
          </el-tooltip>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="goToAdmin" v-if="!isAdmin" class="action-btn">
            <el-icon><Lock /></el-icon>
            <span class="btn-text">{{ t('app.loginBackend') }}</span>
          </el-button>
          <div v-else class="user-info">
            <span class="user-text" :title="'ID: ' + (currentUser?.id || '') + ' ' + t('login.username') + ': ' + (currentUser?.username || '')">
              {{ currentUser?.username || t('app.user') }}
            </span>
            <el-dropdown trigger="click" @command="handleLanguageChange" style="margin-right: 8px;">
              <el-button size="small" circle>
                <el-icon><svg viewBox="0 0 24 24" fill="currentColor" width="1em" height="1em"><path d="M12.87 15.07l-2.54-2.51.03-.03A17.52 17.52 0 0014.07 6H17V4h-7V2H8v2H1v1.99h11.17C11.5 7.92 10.44 9.75 9 11.35 8.07 10.32 7.3 9.19 6.69 8h-2c.73 1.63 1.73 3.17 2.98 4.56l-5.09 5.02L4 19l5-5 3.11 3.11.76-2.04zM18.5 10h-2L12 22h2l1.12-3h4.75L21 22h2l-4.5-12zm-2.62 7l1.62-4.33L19.12 17h-3.24z"/></svg></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="zh-CN" :disabled="currentLocale === 'zh-CN'">中文</el-dropdown-item>
                  <el-dropdown-item command="en" :disabled="currentLocale === 'en'">English</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="danger" @click="logout" class="action-btn">
              <el-icon><Unlock /></el-icon>
              <span class="btn-text">{{ t('app.logoutFrontend') }}</span>
            </el-button>
          </div>
        </div>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
    <el-footer class="app-footer">
      <div class="footer-content">
        <div class="footer-left">
          ©{{ currentYear }} {{ siteName || '' }}
        </div>
        <div class="footer-right" v-if="organizationWebsite || wechatQrcode || workWechatQrcode">
          <a v-if="organizationWebsite" :href="organizationWebsite" target="_blank" class="footer-link" :title="t('app.orgWebsite')">
            <el-icon><Link /></el-icon> {{ t('app.orgWebsite') }}
          </a>
          <el-popover v-if="wechatQrcode" placement="top" trigger="click" width="220">
            <template #reference>
              <span class="footer-link clickable" :title="t('app.wechat')">
                <el-icon><ChatDotRound /></el-icon> {{ t('app.wechat') }}
              </span>
            </template>
            <div style="text-align: center;">
              <img :src="getFullLogoUrl(wechatQrcode)" :alt="t('app.wechat')" style="max-width: 200px; max-height: 200px;" />
              <p style="margin-top: 10px; color: #666;">{{ t('app.wechatTip') }}</p>
            </div>
          </el-popover>
          <el-popover v-if="workWechatQrcode" placement="top" trigger="click" width="220">
            <template #reference>
              <span class="footer-link clickable" :title="t('app.workWechat')">
                <el-icon><UserFilled /></el-icon> {{ t('app.workWechat') }}
              </span>
            </template>
            <div style="text-align: center;">
              <img :src="getFullLogoUrl(workWechatQrcode)" :alt="t('app.workWechat')" style="max-width: 200px; max-height: 200px;" />
              <p style="margin-top: 10px; color: #666;">{{ t('app.workWechatTip') }}</p>
            </div>
          </el-popover>
        </div>
      </div>
    </el-footer>
    <FloatingSphere v-if="currentUser" :licensed="hasFeature(licenseFeatures.FLOATING_SPHERE)" />
    <SmartCommand v-if="isLoggedIn" :licensed="hasFeature(licenseFeatures.SMART_COMMAND)" />
  </el-container>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Lock, Unlock, Reading, ArrowLeft, Monitor, DataAnalysis, Link, ChatDotRound, UserFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import api from '@/utils/api'
import FloatingSphere from '@/components/FloatingSphere.vue'
import SmartCommand from '@/components/SmartCommand.vue'
import { licenseState, hasFeature, loadLicenseStatus, FEATURES as licenseFeatures } from '@/utils/license'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()

const elementLocale = computed(() => locale.value === 'en' ? en : zhCn)
const currentLocale = computed(() => locale.value)

const handleLanguageChange = (lang) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
  document.documentElement.lang = lang === 'zh-CN' ? 'zh-CN' : 'en'
}

const currentUser = ref(null)
const isAdmin = computed(() => route.path.startsWith('/admin'))
const siteName = ref('')
const siteLogo = ref('')
const organizationWebsite = ref('')
const wechatQrcode = ref('')
const workWechatQrcode = ref('')
const currentYear = ref(new Date().getFullYear())
const operationManagers = ref([])

const isLoggedIn = computed(() => {
  return !!localStorage.getItem('token')
})

const canAccessDashboard = computed(() => {
  if (!currentUser.value) return false
  if (!hasFeature(licenseFeatures.DASHBOARD_VIEW)) return false
  
  if (['super_admin', 'system_admin'].includes(currentUser.value.role)) {
    return true
  }
  
  if (currentUser.value.role === 'course_admin' && currentUser.value.teacher_id) {
    return operationManagers.value.includes(currentUser.value.teacher_id)
  }
  
  return false
})

const handleUserLogin = (event) => {
  currentUser.value = event.detail
}

onMounted(async () => {
  siteName.value = localStorage.getItem('site_name') || ''
  siteLogo.value = localStorage.getItem('site_logo') || ''
  await loadPromotionInfo()
  await loadLicenseStatus()
  
  window.addEventListener('user-logged-in', handleUserLogin)
  
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const response = await api.get('/auth/me')
      currentUser.value = response.data
      
      await fetchOperationManagers()
    } catch (error) {
      if (error?.response?.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        currentUser.value = null
        if (route.path.startsWith('/admin') && route.path !== '/admin/login') {
          router.push('/admin/login')
        }
      }
    }
  }
})

const loadPromotionInfo = async () => {
  try {
    const response = await api.get('/settings')
    if (response.data) {
      siteName.value = response.data.site_name || ''
      siteLogo.value = response.data.site_logo || ''
      organizationWebsite.value = response.data.organization_website || ''
      wechatQrcode.value = response.data.wechat_qrcode || ''
      workWechatQrcode.value = response.data.work_wechat_qrcode || ''
      
      if (siteName.value) localStorage.setItem('site_name', siteName.value)
      if (siteLogo.value) localStorage.setItem('site_logo', siteLogo.value)
      if (organizationWebsite.value) localStorage.setItem('organization_website', organizationWebsite.value)
      if (wechatQrcode.value) localStorage.setItem('wechat_qrcode', wechatQrcode.value)
      if (workWechatQrcode.value) localStorage.setItem('work_wechat_qrcode', workWechatQrcode.value)
    }
  } catch (error) {
    window.logger.error('Failed to load promotion info:', error)
    siteName.value = localStorage.getItem('site_name') || ''
    siteLogo.value = localStorage.getItem('site_logo') || ''
    organizationWebsite.value = localStorage.getItem('organization_website') || ''
    wechatQrcode.value = localStorage.getItem('wechat_qrcode') || ''
    workWechatQrcode.value = localStorage.getItem('work_wechat_qrcode') || ''
  }
}

onUnmounted(() => {
  window.removeEventListener('user-logged-in', handleUserLogin)
})

const fetchOperationManagers = async () => {
  try {
    const response = await api.get('/settings')
    if (response.data && response.data.operation_managers) {
      operationManagers.value = response.data.operation_managers
      localStorage.setItem('operation_managers', JSON.stringify(operationManagers.value))
    }
  } catch (error) {
    window.logger.error('Failed to fetch operation managers:', error)
  }
}

const getFullLogoUrl = (logoPath) => {
  if (!logoPath) return ''
  if (logoPath.startsWith('http')) return logoPath
  return logoPath
}

const goBack = () => {
  router.push('/admin/dashboard')
}

const goToAdmin = () => {
  router.push('/admin/login')
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  window.dispatchEvent(new CustomEvent('user-logged-out'))
  router.push('/')
}

const goToScheduleView = () => {
  router.push('/') 
}

const goToDashboardView = () => {
  router.push('/admin/dashboard-view')
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
  transition: all 0.3s ease;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  gap: 15px;
  flex-wrap: wrap;
}

.site-title {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 1 auto;
  min-width: 0;
}

.site-logo {
  height: 40px;
  width: auto;
  object-fit: contain;
  transition: height 0.3s ease;
}

.site-name {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  transition: font-size 0.3s ease;
  white-space: nowrap;
}

.system-name {
  font-size: 18px;
  color: #666;
  transition: font-size 0.3s ease;
  white-space: nowrap;
}

.header-buttons {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  align-items: center;
}

.nav-btn, .action-btn {
  white-space: nowrap;
}

.btn-text {
  transition: display 0.3s ease;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-text {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 平板尺寸优化 */
@media (max-width: 1024px) {
  .header-content {
    gap: 10px;
  }
  
  .site-name {
    font-size: 18px;
  }
  
  .system-name {
    font-size: 16px;
  }
}

/* 中等屏幕优化 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 15px;
  }
  
  .header-content {
    gap: 8px;
  }
  
  .site-logo {
    height: 35px;
  }
  
  .site-name {
    font-size: 16px;
  }
  
  .system-name {
    font-size: 14px;
  }
  
  .header-buttons, .header-actions {
    gap: 8px;
  }
  
  .nav-btn, .action-btn {
    padding: 8px 12px;
    font-size: 13px;
  }
  
  .user-text {
    max-width: 150px;
    font-size: 13px;
  }
}

/* 小屏幕优化 - 垂直布局 */
@media (max-width: 480px) {
  .app-header {
    padding: 10px 12px;
    height: auto !important;
    min-height: auto;
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .site-title {
    width: 100%;
    justify-content: center;
    order: 1;
    gap: 8px;
  }
  
  .header-buttons {
    width: 100%;
    justify-content: center;
    order: 2;
    flex-wrap: wrap;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
    order: 3;
    flex-wrap: wrap;
  }
  
  .site-logo {
    height: 30px;
  }
  
  .site-name {
    font-size: 15px;
  }
  
  .system-name {
    font-size: 13px;
  }
  
  .nav-btn, .action-btn {
    padding: 6px 10px;
    font-size: 12px;
    flex: 1;
    min-width: 80px;
    max-width: 120px;
  }
  
  .user-info {
    width: 100%;
    justify-content: center;
    gap: 10px;
  }
  
  .user-text {
    max-width: 120px;
    font-size: 12px;
  }
}

/* 极小屏幕优化 - 只显示图标 */
@media (max-width: 360px) {
  .app-header {
    padding: 8px 10px;
  }
  
  .site-logo {
    height: 26px;
  }
  
  .site-name {
    font-size: 13px;
  }
  
  .system-name {
    font-size: 11px;
  }
  
  .nav-btn, .action-btn {
    padding: 6px 8px;
    font-size: 11px;
    min-width: 40px;
    max-width: none;
  }
  
  /* 隐藏按钮文字，只显示图标 */
  .btn-text {
    display: none;
  }
  
  .nav-btn .el-icon, .action-btn .el-icon {
    margin-right: 0;
    font-size: 16px;
  }
  
  .user-text {
    display: none;
  }
}

.app-main {
  padding: 6px;
  flex: 1;
}

.app-footer {
  background: rgba(255, 255, 255, 0.95);
  padding: 10px 20px;
  text-align: center;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
}

.footer-content {
  color: #666;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.footer-left {
  flex: 1;
  text-align: left;
}

.footer-right {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.footer-link {
  color: #409eff;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: color 0.3s;
  cursor: pointer;
}

.footer-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.footer-link.clickable {
  cursor: pointer;
}

@media (max-width: 768px) {
  .footer-content {
    font-size: 13px;
    flex-direction: column;
    align-items: center;
  }
  
  .footer-left {
    text-align: center;
  }
  
  .footer-right {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .footer-content {
    font-size: 12px;
  }
  
  .footer-link {
    font-size: 12px;
  }
}
</style>