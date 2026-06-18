// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="site-title">
          <img v-if="siteLogo" :src="getFullLogoUrl(siteLogo)" class="site-logo" alt="机构LOGO" />
          <span class="site-name">{{ siteName || '' }}</span>
          <span class="system-name">课程信息系统</span>
        </div>
        <div class="header-buttons">
          <el-button type="success" @click="goBack">
            <el-icon><Monitor /></el-icon>
            <span class="btn-text">管理面板</span>
          </el-button>
          <el-button type="primary" @click="goToScheduleView" class="nav-btn">
            <el-icon><Reading /></el-icon>
            <span class="btn-text">课程视图</span>
          </el-button>
          <el-button v-if="canAccessDashboard" type="warning" @click="goToDashboardView" class="nav-btn">
            <el-icon><DataAnalysis /></el-icon>
            <span class="btn-text">运营大屏</span>
          </el-button>
          <el-tooltip v-else content="运营大屏为授权功能，请在系统授权管理中激活" placement="bottom">
            <el-button type="warning" class="nav-btn" disabled>
              <el-icon><Lock /></el-icon>
              <span class="btn-text">运营大屏</span>
            </el-button>
          </el-tooltip>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="goToAdmin" v-if="!isAdmin" class="action-btn">
            <el-icon><Lock /></el-icon>
            <span class="btn-text">登陆·进入后台</span>
          </el-button>
          <div v-else class="user-info">
            <span class="user-text" :title="'ID: ' + (currentUser?.id || '') + ' 用户名: ' + (currentUser?.username || '')">
              {{ currentUser?.username || '用户' }}
            </span>
            <el-button type="danger" @click="logout" class="action-btn">
              <el-icon><Unlock /></el-icon>
              <span class="btn-text">退出·返回前台</span>
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
          <a v-if="organizationWebsite" :href="organizationWebsite" target="_blank" class="footer-link" title="访问机构官网">
            <el-icon><Link /></el-icon> 机构官网
          </a>
          <el-popover v-if="wechatQrcode" placement="top" trigger="click" width="220">
            <template #reference>
              <span class="footer-link clickable" title="关注公众号">
                <el-icon><ChatDotRound /></el-icon> 公众号
              </span>
            </template>
            <div style="text-align: center;">
              <img :src="getFullLogoUrl(wechatQrcode)" alt="公众号二维码" style="max-width: 200px; max-height: 200px;" />
              <p style="margin-top: 10px; color: #666;">扫码关注微信公众号</p>
            </div>
          </el-popover>
          <el-popover v-if="workWechatQrcode" placement="top" trigger="click" width="220">
            <template #reference>
              <span class="footer-link clickable" title="添加企业微信">
                <el-icon><UserFilled /></el-icon> 企业微信
              </span>
            </template>
            <div style="text-align: center;">
              <img :src="getFullLogoUrl(workWechatQrcode)" alt="企业微信二维码" style="max-width: 200px; max-height: 200px;" />
              <p style="margin-top: 10px; color: #666;">扫码添加企业微信</p>
            </div>
          </el-popover>
        </div>
      </div>
    </el-footer>
    <!-- 浮动球形常用功能组件 -->
    <!-- <FloatingSphere v-if="isAdmin && currentUser" /> -->
    <FloatingSphere v-if="currentUser" :licensed="hasFeature(licenseFeatures.FLOATING_SPHERE)" />
    <SmartCommand v-if="isLoggedIn" :licensed="hasFeature(licenseFeatures.SMART_COMMAND)" />
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Lock, Unlock, Reading, ArrowLeft, Monitor, DataAnalysis, Link, ChatDotRound, UserFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'
import FloatingSphere from '@/components/FloatingSphere.vue'
import SmartCommand from '@/components/SmartCommand.vue'
import { licenseState, hasFeature, loadLicenseStatus, FEATURES as licenseFeatures } from '@/utils/license'

const router = useRouter()
const route = useRoute()

const currentUser = ref(null)
const isAdmin = computed(() => route.path.startsWith('/admin'))
const siteName = ref('')
const siteLogo = ref('')
const organizationWebsite = ref('')
const wechatQrcode = ref('')
const workWechatQrcode = ref('')
const currentYear = ref(new Date().getFullYear())
const operationManagers = ref([])

// 检查用户是否登录
const isLoggedIn = computed(() => {
  return !!localStorage.getItem('token')
})

// 检查是否可以访问运营大屏
const canAccessDashboard = computed(() => {
  if (!currentUser.value) return false
  if (!hasFeature(licenseFeatures.DASHBOARD_VIEW)) return false
  
  // 超级管理员和系统管理员可以访问
  if (['super_admin', 'system_admin'].includes(currentUser.value.role)) {
    return true
  }
  
  // 课程管理员需要是运营管理导师
  if (currentUser.value.role === 'course_admin' && currentUser.value.teacher_id) {
    return operationManagers.value.includes(currentUser.value.teacher_id)
  }
  
  return false
})

// 定义用户登录事件处理函数（需要在顶层定义，以便onUnmounted可以访问）
const handleUserLogin = (event) => {
  currentUser.value = event.detail
}

onMounted(async () => {
  siteName.value = localStorage.getItem('site_name') || ''
  siteLogo.value = localStorage.getItem('site_logo') || ''
  // 加载宣传信息
  await loadPromotionInfo()
  // 加载 License 状态
  await loadLicenseStatus()
  
  // 监听用户登录事件
  window.addEventListener('user-logged-in', handleUserLogin)
  
  // 检查用户是否已登录
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const response = await api.get('/auth/me')
      currentUser.value = response.data
      
      // 获取运营管理导师列表
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

// 加载宣传信息
const loadPromotionInfo = async () => {
  try {
    const response = await api.get('/settings')
    if (response.data) {
      siteName.value = response.data.site_name || ''
      siteLogo.value = response.data.site_logo || ''
      organizationWebsite.value = response.data.organization_website || ''
      wechatQrcode.value = response.data.wechat_qrcode || ''
      workWechatQrcode.value = response.data.work_wechat_qrcode || ''
      
      // 保存到localStorage以便快速访问
      if (siteName.value) {
        localStorage.setItem('site_name', siteName.value)
      }
      if (siteLogo.value) {
        localStorage.setItem('site_logo', siteLogo.value)
      }
      if (organizationWebsite.value) {
        localStorage.setItem('organization_website', organizationWebsite.value)
      }
      if (wechatQrcode.value) {
        localStorage.setItem('wechat_qrcode', wechatQrcode.value)
      }
      if (workWechatQrcode.value) {
        localStorage.setItem('work_wechat_qrcode', workWechatQrcode.value)
      }
    }
  } catch (error) {
    window.logger.error('加载宣传信息失败:', error)
    // 从localStorage读取缓存
    siteName.value = localStorage.getItem('site_name') || ''
    siteLogo.value = localStorage.getItem('site_logo') || ''
    organizationWebsite.value = localStorage.getItem('organization_website') || ''
    wechatQrcode.value = localStorage.getItem('wechat_qrcode') || ''
    workWechatQrcode.value = localStorage.getItem('work_wechat_qrcode') || ''
  }
}

// ✅ 正确：onUnmounted 应该在顶层独立调用
onUnmounted(() => {
  window.removeEventListener('user-logged-in', handleUserLogin)
})

// 获取运营管理导师列表
const fetchOperationManagers = async () => {
  try {
    const response = await api.get('/settings')
    if (response.data && response.data.operation_managers) {
      operationManagers.value = response.data.operation_managers
      localStorage.setItem('operation_managers', JSON.stringify(operationManagers.value))
    }
  } catch (error) {
    window.logger.error('获取运营管理导师列表失败:', error)
  }
}

const getFullLogoUrl = (logoPath) => {
  if (!logoPath) return ''
  if (logoPath.startsWith('http')) {
    return logoPath
  }
  // 直接使用相对路径，让浏览器自动处理域名和端口
  return logoPath
}

const goBack = () => {
  //router.back()    //返回上一页面
  router.push('/admin/dashboard')   //跳转到后台首页-面板
}

const goToAdmin = () => {
  router.push('/admin/login')
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  // 触发自定义登出事件
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