// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div 
    ref="sphereContainer"
    class="floating-sphere-container"
    :class="{ 
      'collapsed': isCollapsed,
      'expanded': !isCollapsed,
      'hidden-half': isHiddenHalf,
      'unlicensed': !props.licensed
    }"
    :style="containerStyle"
    @mousedown="startDrag"
    @touchstart="startTouchDrag"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- 未授权状态：显示禁用的触发按钮 -->
    <el-tooltip v-if="!props.licensed && isCollapsed" :content="t('floatingSphere.licenseRequired')" placement="left" effect="light">
      <div class="collapsed-trigger unlicensed-trigger">
        <el-icon :size="24"><Lock /></el-icon>
      </div>
    </el-tooltip>

    <!-- 已授权状态的展开/收起 -->
    <template v-if="props.licensed">
      <!-- 展开状态的圆形按钮圈 -->
      <transition name="sphere-expand">
        <div v-if="!isCollapsed" class="sphere-circle" @mousedown.stop>
          <div 
            v-for="(item, index) in visibleMenuItems" 
            :key="item.key"
            class="menu-item"
            :class="{ 'menu-item-disabled': item.requiresLicense && item.licenseFeature && !hasFeature(item.licenseFeature) }"
            :style="getMenuItemPosition(index, visibleMenuItems.length)"
            @click="handleMenuClick(item)"
          >
            <el-tooltip 
              :content="getItemTooltip(item)" 
              placement="top"
              effect="light"
              :show-after="300"
              popper-class="floating-sphere-tooltip"
            >
              <div class="menu-button" :class="[item.color, { 'button-disabled': item.requiresLicense && item.licenseFeature && !hasFeature(item.licenseFeature) }]">
                <el-icon :size="20">
                  <component v-if="!(item.requiresLicense && item.licenseFeature && !hasFeature(item.licenseFeature))" :is="item.icon" />
                  <Lock v-else />
                </el-icon>
              </div>
            </el-tooltip>
          </div>
          
          <!-- 中心收起按钮 -->
          <div class="center-button" @click="toggleCollapse">
            <el-icon :size="24"><Close /></el-icon>
          </div>
        </div>
      </transition>

      <!-- 收起状态的触发按钮 -->
      <transition name="sphere-collapse">
        <div v-if="isCollapsed" class="collapsed-trigger" @click="toggleCollapse">
          <el-icon :size="28"><Menu /></el-icon>
        </div>
      </transition>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Menu, Close, Reading, UserFilled, Avatar, 
  OfficeBuilding, Calendar, Trophy, Money, Clock,
  DataAnalysis, View, Monitor, Lock
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { hasFeature, FEATURES, FEATURE_NAMES, licenseState } from '@/utils/license'
import { useI18n } from 'vue-i18n'


const { t } = useI18n()
const props = defineProps({
  licensed: {
    type: Boolean,
    default: true
  }
})

const router = useRouter()
const currentUser = ref(null)

const sphereContainer = ref(null)
const isCollapsed = ref(true)
const isHiddenHalf = ref(false)
const spherePosition = ref({ x: 100, y: 100 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const dragOffset = ref({ x: 0, y: 0 })
let hideTimer = null
let touchStartTime = 0
let touchStartPos = { x: 0, y: 0 }

// 菜单项配置
const menuItems = [
  { 
    key: 'dashboard', 
    label: t('nav.dashboard'), 
    icon: DataAnalysis, 
    path: '/admin/dashboard',
    color: 'color-indigo',
    requiresRole: ['super_admin', 'course_admin', 'system_admin', 'system_audit']
  },
  { 
    key: 'scheduleview', 
    label: t('app.courseView'), 
    icon: View, 
    path: '/',
    color: 'color-teal',
    requiresRole: ['super_admin', 'course_admin']
  },
  { 
    key: 'dashboardview', 
    label: t('app.dashboardView'), 
    icon: Monitor, 
    path: '/admin/dashboard-view',
    color: 'color-magenta',
    requiresRole: ['super_admin', 'course_admin'],
    requiresOperationManager: true,
    requiresLicense: true,
    licenseFeature: 'dashboard_view'
  },
  { 
    key: 'courses', 
    label: t('courses.addCourse'), 
    icon: Reading, 
    path: '/admin/courses',
    color: 'color-blue',
    requiresRole: ['super_admin', 'course_admin']
  },
  { 
    key: 'teachers', 
    label: t('teachers.addTeacher'), 
    icon: UserFilled, 
    path: '/admin/teachers',
    color: 'color-green',
    requiresRole: ['super_admin', 'course_admin']
  },
  { 
    key: 'students', 
    label: t('students.addStudent'), 
    icon: Avatar, 
    path: '/admin/students',
    color: 'color-orange',
    requiresRole: ['super_admin', 'course_admin']
  },
  { 
    key: 'classes', 
    label: t('classes.addClass'), 
    icon: OfficeBuilding, 
    path: '/admin/classes',
    color: 'color-purple',
    requiresRole: ['super_admin', 'course_admin']
  },
  { 
    key: 'schedules', 
    label: t('schedules.addSchedule'), 
    icon: Calendar, 
    path: '/admin/schedules',
    color: 'color-red',
    requiresRole: ['super_admin', 'course_admin']
  },
  { 
    key: 'grades', 
    label: t('grade.addGrade'), 
    icon: Trophy, 
    path: '/admin/grades',
    color: 'color-yellow',
    requiresRole: ['super_admin', 'course_admin', 'grade_manager_placeholder']
  },
  { 
    key: 'leaves', 
    label: t('leaves.addLeave'), 
    icon: Clock, 
    path: '/admin/leaves',
    color: 'color-cyan',
    requiresRole: ['super_admin', 'course_admin']
  },
  { 
    key: 'fees', 
    label: t('fee.title'), 
    icon: Money, 
    path: '/admin/feemanagement',
    color: 'color-pink',
    requiresRole: ['super_admin', 'system_admin', 'fee_manager_placeholder'],
    requiresLicense: true,
    licenseFeature: 'fee_management'
  }
]

// 获取当前用户信息
const getCurrentUser = () => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}

// 根据权限过滤可见的菜单项
const visibleMenuItems = computed(() => {
  const user = currentUser.value
  if (!user || !user.role) {
    return []
  }
  
  return menuItems.filter(item => {
    // 特殊处理运营大屏模块
    if (item.key === 'dashboardview') {
      console.log('[FloatingSphere] 运营大屏可见性检查:', {
        role: user.role,
        isAdmin: ['super_admin', 'system_admin'].includes(user.role),
        teacher_id: user.teacher_id,
        hasOperationManagers: !!localStorage.getItem('operation_managers')
      })
      // 1. 超级管理员和系统管理员直接拥有权限
      if (['super_admin', 'system_admin'].includes(user.role)) {
        console.log('[FloatingSphere] 运营大屏按钮: 可见 (管理员)')
        return true
      }
      // 2. 检查是否是运营管理导师
      const operationManagersStr = localStorage.getItem('operation_managers')
      if (operationManagersStr && user.teacher_id) {
        try {
          const operationManagers = JSON.parse(operationManagersStr)
          if (Array.isArray(operationManagers) && operationManagers.includes(user.teacher_id)) {
            return true
          }
        } catch (e) {
          window.logger.error('解析运营管理导师列表失败:', e)
        }
      }
      return false
    }
    // 特殊处理费用管理模块
    if (item.key === 'fees') {
      // 1. 超级管理员直接拥有权限
      if (['super_admin'].includes(user.role)) {
        return true
      }
      // 2. 检查是否是费用管理导师
      const feeManagersStr = localStorage.getItem('fee_managers')
      if (feeManagersStr && user.teacher_id) {
        try {
          const feeManagers = JSON.parse(feeManagersStr)
          if (Array.isArray(feeManagers) && feeManagers.includes(user.teacher_id)) {
            return true
          }
        } catch (e) {
          window.logger.error('解析费用管理导师列表失败:', e)
        }
      }
      return false
    }
    // 特殊处理成绩管理模块
    if (item.key === 'grades') {
      // 先检查授权
      if (!hasFeature('grade_trend')) {
        return false
      }
      // 1. 超级管理员直接拥有权限
      if (['super_admin'].includes(user.role)) {
        return true
      }
      // 2. 检查是否是成绩管理导师
      const gradeManagersStr = localStorage.getItem('grade_managers')
      if (gradeManagersStr && user.teacher_id) {
        try {
          const gradeManagers = JSON.parse(gradeManagersStr)
          if (Array.isArray(gradeManagers) && gradeManagers.includes(user.teacher_id)) {
            return true
          }
        } catch (e) {
          window.logger.error('解析成绩管理导师列表失败:', e)
        }
      }
      return false
    }
    // 其他模块按原有角色逻辑判断
    return item.requiresRole.includes(user.role)
  })
})

// 计算菜单项的环形位置
const getMenuItemPosition = (index, total) => {
  const radius = 120
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2
  const x = Math.cos(angle) * radius
  const y = Math.sin(angle) * radius
  
  return {
    transform: `translate(${x}px, ${y}px)`
  }
}

// 容器样式
const containerStyle = computed(() => {
  const baseStyle = {
    position: 'fixed',
    right: `${spherePosition.value.x}px`,
    bottom: `${spherePosition.value.y}px`,
    zIndex: 9999,
    cursor: isDragging.value ? 'grabbing' : 'grab'
  }
  
  if (isHiddenHalf.value) {
    baseStyle.right = '-60px'
  }
  
  return baseStyle
})

// 切换展开/收起状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  if (isCollapsed.value) {
    clearTimeout(hideTimer)
    isHiddenHalf.value = false
  }
}

// 开始拖拽
const startDrag = (e) => {
  if (e.target.closest('.menu-button') || e.target.closest('.center-button')) {
    return
  }
  
  isDragging.value = true
  dragStart.value = {
    x: e.clientX,
    y: e.clientY
  }
  dragOffset.value = {
    x: spherePosition.value.x,
    y: spherePosition.value.y
  }
  
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', stopDrag)
  e.preventDefault()
}

// 开始触摸拖拽（移动端）
const startTouchDrag = (e) => {
  if (e.target.closest('.menu-button') || e.target.closest('.center-button')) {
    return
  }
  
  const touch = e.touches[0]
  touchStartTime = Date.now()
  touchStartPos = {
    x: touch.clientX,
    y: touch.clientY
  }
  
  isDragging.value = true
  dragStart.value = {
    x: touch.clientX,
    y: touch.clientY
  }
  dragOffset.value = {
    x: spherePosition.value.x,
    y: spherePosition.value.y
  }
  
  document.addEventListener('touchmove', handleTouchDrag, { passive: false })
  document.addEventListener('touchend', stopTouchDrag)
}

// 处理拖拽
const handleDrag = (e) => {
  if (!isDragging.value) return
  
  const deltaX = dragStart.value.x - e.clientX
  const deltaY = e.clientY - dragStart.value.y
  
  let newX = dragOffset.value.x + deltaX
  let newY = dragOffset.value.y + deltaY
  
  // 限制边界
  const maxX = window.innerWidth - 80
  const maxY = window.innerHeight - 80
  
  newX = Math.max(0, Math.min(newX, maxX))
  newY = Math.max(0, Math.min(newY, maxY))
  
  spherePosition.value = { x: newX, y: newY }
}


// 处理触摸拖拽（移动端）
const handleTouchDrag = (e) => {
  if (!isDragging.value) return
  
  const touch = e.touches[0]
  const deltaX = dragStart.value.x - touch.clientX
  const deltaY = touch.clientY - dragStart.value.y
  
  let newX = dragOffset.value.x + deltaX
  let newY = dragOffset.value.y + deltaY
  
  // 限制边界
  const maxX = window.innerWidth - 80
  const maxY = window.innerHeight - 80
  
  newX = Math.max(0, Math.min(newX, maxX))
  newY = Math.max(0, Math.min(newY, maxY))
  
  spherePosition.value = { x: newX, y: newY }
  
  // 阻止页面滚动
  e.preventDefault()
}

// 停止拖拽
const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// 停止触摸拖拽（移动端）
const stopTouchDrag = () => {
  const touchEndTime = Date.now()
  const touchDuration = touchEndTime - touchStartTime
  
  // 获取最后一个触摸位置（如果有的话）
  const lastTouch = event.changedTouches?.[0]
  if (lastTouch) {
    const deltaX = Math.abs(lastTouch.clientX - touchStartPos.x)
    const deltaY = Math.abs(lastTouch.clientY - touchStartPos.y)
    
    // 如果触摸时间很短且移动距离很小，认为是点击而非拖拽
    if (touchDuration < 200 && deltaX < 10 && deltaY < 10) {
      toggleCollapse()
    }
  }
  
  isDragging.value = false
  document.removeEventListener('touchmove', handleTouchDrag)
  document.removeEventListener('touchend', stopTouchDrag)
}

// 鼠标进入处理
const handleMouseEnter = () => {
  clearTimeout(hideTimer)
  isHiddenHalf.value = false
}

// 鼠标离开处理
const handleMouseLeave = () => {
  if (!isCollapsed.value && !isDragging.value) {
    hideTimer = setTimeout(() => {
      isHiddenHalf.value = true
    }, 2000)
  }
}

// 获取菜单项的tooltip内容
const getItemTooltip = (item) => {
  if (item.requiresLicense && item.licenseFeature && !hasFeature(item.licenseFeature)) {
    const featureName = FEATURE_NAMES[item.licenseFeature] ? t(FEATURE_NAMES[item.licenseFeature]) : t('floatingSphere.thisFeature')
    return t('floatingSphere.licenseRequired', { feature: featureName })
  }
  return item.label
}

// 菜单项点击处理
const handleMenuClick = (item) => {
  console.log('[FloatingSphere] 菜单项点击:', item.key, item.label)
  // 超级管理员和系统管理员可以绕过license功能检查
  const isAdmin = currentUser.value && ['super_admin', 'system_admin'].includes(currentUser.value.role)
  if (item.requiresLicense && item.licenseFeature && !isAdmin && !hasFeature(item.licenseFeature)) {
    const featureName = FEATURE_NAMES[item.licenseFeature] ? t(FEATURE_NAMES[item.licenseFeature]) : t('floatingSphere.thisFeature')
    console.log('[FloatingSphere] License功能检查失败:', {
      feature: item.licenseFeature,
      activated: licenseState.activated,
      features: licenseState.features,
      hasFeature: hasFeature(item.licenseFeature),
      isAdmin: isAdmin
    })
    ElMessage.warning(t('floatingSphere.licenseRequired', { feature: featureName }))
    return
  }
  // '课费管理\仪表盘\课程视图\运营大屏'直接跳转，不自动打开新增对话框
  if (item.key === 'fees' || item.key === 'dashboard'|| item.key === 'scheduleview' || item.key === 'dashboardview') {
    console.log('[FloatingSphere] 跳转到:', item.path)
    router.push(item.path)
    ElMessage.success(t('floatingSphere.jumpingTo', { label: item.label }))
  } else {
    // 其他按钮跳转到对应页面，并携带参数表示要打开新增对话框
    // 添加时间戳确保每次点击都能触发路由变化
    router.push({
      path: item.path,
      query: { 
        action: 'add',
        _t: Date.now()  // 添加时间戳确保路由变化能被检测到
      }
    })
    ElMessage.success(t('floatingSphere.opening', { label: item.label }))
  }
  isCollapsed.value = true
  isHiddenHalf.value = false
}

// 初始化
onMounted(() => {
  // 从localStorage恢复位置
  const savedPosition = localStorage.getItem('floatingSpherePosition')
  if (savedPosition) {
    try {
      spherePosition.value = JSON.parse(savedPosition)
    } catch (e) {
      spherePosition.value = { x: 100, y: 100 }
    }
  }
  // 初始化当前用户信息
  currentUser.value = getCurrentUser()
  // 监听用户登录事件以更新权限
  window.addEventListener('user-logged-in', handleUserLogin)
  window.addEventListener('storage', handleStorageChange) // 监听 localStorage 变化
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  // 监听用户登录/登出事件
  window.addEventListener('user-logged-in', handleUserLogin)
  window.addEventListener('user-logged-out', handleUserLogout)
})

// 处理 localStorage 变化（当管理员修改了费用管理导师配置后）
const handleStorageChange = (e) => {
  if (e.key === 'fee_managers') {
    // 强制重新计算 visibleMenuItems
    currentUser.value = { ...currentUser.value }
  }
}

// 处理用户登录事件
const handleUserLogin = (event) => {
  currentUser.value = event.detail
}

// 处理用户登出事件
const handleUserLogout = () => {
  currentUser.value = null
}

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  clearTimeout(hideTimer)
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', handleTouchDrag)
  document.removeEventListener('touchend', stopTouchDrag)
  window.removeEventListener('user-logged-in', handleUserLogin)
  window.removeEventListener('user-logged-out', handleUserLogout)
})

// 窗口大小变化处理
const handleResize = () => {
  const maxX = window.innerWidth - 80
  const maxY = window.innerHeight - 80
  
  if (spherePosition.value.x > maxX) {
    spherePosition.value.x = maxX
  }
  if (spherePosition.value.y > maxY) {
    spherePosition.value.y = maxY
  }
  
  // 保存位置
  localStorage.setItem('floatingSpherePosition', JSON.stringify(spherePosition.value))
}

// 监听位置变化并保存
watch(spherePosition, (newVal) => {
  localStorage.setItem('floatingSpherePosition', JSON.stringify(newVal))
}, { deep: true })
</script>

<style>
/* 全局样式 - 提高 Tooltip 层级 */
.floating-sphere-tooltip {
  z-index: 99999 !important;
}
</style>

<style scoped>
.floating-sphere-container {
  transition: right 0.3s ease;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  touch-action: none;
  -webkit-touch-callout: none;
}

.sphere-circle {
  position: relative;
  width: 300px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-item {
  position: absolute;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.menu-item:hover {
  transform: scale(1.15);
  z-index: 20;
}

.menu-button {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  cursor: pointer;
  font-weight: bold;
}

.menu-button:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
  transform: translateY(-3px) scale(1.1);
}

.color-blue { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.color-green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
.color-orange { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.color-purple { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.color-red { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
.color-yellow { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); }
.color-pink { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
.color-cyan { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }
.color-indigo { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.color-teal { background: linear-gradient(135deg, #134E5E 0%, #71B280 100%); }
.color-magenta { background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%); }

.center-button {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
}

.center-button:hover {
  transform: scale(1.15);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.collapsed-trigger {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.3s ease;
}

.collapsed-trigger:hover {
  transform: scale(1.15);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

/* 动画效果 */
.sphere-expand-enter-active,
.sphere-expand-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.sphere-expand-enter-from,
.sphere-expand-leave-to {
  opacity: 0;
  transform: scale(0.5);
}

.sphere-collapse-enter-active,
.sphere-collapse-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sphere-collapse-enter-from,
.sphere-collapse-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 隐藏一半的状态 */
.hidden-half {
  transition: right 0.3s ease;
}

/* 未授权状态样式 */
.unlicensed-trigger {
  background: linear-gradient(135deg, #909399 0%, #b1b3b8 100%) !important;
  cursor: not-allowed !important;
  opacity: 0.7;
}

.unlicensed-trigger:hover {
  transform: none !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

.menu-item-disabled {
  cursor: not-allowed !important;
}

.menu-item-disabled:hover {
  transform: none !important;
  z-index: 1 !important;
}

.menu-button.button-disabled {
  background: linear-gradient(135deg, #909399 0%, #b1b3b8 100%) !important;
  cursor: not-allowed !important;
  opacity: 0.6;
}

.menu-button.button-disabled:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  transform: none !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sphere-circle {
    width: 250px;
    height: 250px;
  }
  
  .menu-button {
    width: 45px;
    height: 45px;
  }
  
  .center-button,
  .collapsed-trigger {
    width: 50px;
    height: 50px;
  }
}

@media (max-width: 480px) {
  .sphere-circle {
    width: 200px;
    height: 200px;
  }
  
  .menu-button {
    width: 40px;
    height: 40px;
  }
  
  .center-button,
  .collapsed-trigger {
    width: 45px;
    height: 45px;
  }
}
</style>