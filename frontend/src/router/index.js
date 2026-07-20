import { createRouter, createWebHistory } from 'vue-router'
import i18n from '@/locales'

const { t } = i18n.global

function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (!payload.exp) return false
    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

function clearAuthAndRedirect(loginPath) {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  window.location.href = loginPath
}

const routes = [
  {
    path: '/',
    name: 'ScheduleView',
    component: () => import('@/views/ScheduleView.vue')
  },
  {
    path: '/admin',
    redirect: '/admin/login'
  },
  {
    path: '/admin/login',
    name: 'Login',
    component: () => import('@/views/admin/Login.vue')
  },
  {
    path: '/admin/users',
    name: 'Users',
    component: () => import('@/views/admin/Users.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/admin/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/conditions',
    name: 'Conditions',
    component: () => import('@/views/admin/Conditions.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/courses',
    name: 'Courses',
    component: () => import('@/views/admin/Courses.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/teachers',
    name: 'Teachers',
    component: () => import('@/views/admin/Teachers.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/classes',
    name: 'Classes',
    component: () => import('@/views/admin/Classes.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/students',
    name: 'Students',
    component: () => import('@/views/admin/Students.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/rooms',
    name: 'Rooms',
    component: () => import('@/views/admin/Rooms.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/leaves',
    name: 'Leaves',
    component: () => import('@/views/admin/Leaves.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/schedules',
    name: 'Schedules',
    component: () => import('@/views/admin/Schedules.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/database',
    name: 'Database',
    component: () => import('@/views/admin/Database.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, requiresLicense: true, licenseFeature: 'database_management' }
  },
  {
    path: '/admin/feemanagement',
    name: 'FeeManagement',
    component: () => import('@/views/admin/FeeManagement.vue'),
    meta: { requiresAuth: true, requiresLicense: true, licenseFeature: 'fee_management' }
  },
  {
    path: '/admin/grades',
    name: 'GradeManagement',
    component: () => import('@/views/admin/GradeManagement.vue'),
    meta: { requiresAuth: true, requiresLicense: true, licenseFeature: 'grade_trend' }
  },
  {
    path: '/admin/evaluations',
    name: 'StudentEvaluation',
    component: () => import('@/views/admin/StudentEvaluation.vue'),
    meta: { requiresAuth: true, requiresLicense: true, licenseFeature: 'student_evaluation' }
  },
  {
    path: '/admin/daily-words',
    name: 'DailyWords',
    component: () => import('@/views/admin/DailyWords.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/holidays',
    name: 'Holidays',
    component: () => import('@/views/admin/Holidays.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/dashboard-view',
    name: 'DashboardView',
    component: () => import('@/views/admin/DashboardView.vue'),
    meta: { requiresAuth: true, requiresOperationManager: true, requiresLicense: true, licenseFeature: 'dashboard_view' }
  },
  {
    path: '/admin/license',
    name: 'License',
    component: () => import('@/views/admin/License.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : null
  
  if (to.meta.requiresAuth && !token) {
    next('/admin/login')
  } else if (to.meta.requiresAuth && token && isTokenExpired(token)) {
    clearAuthAndRedirect('/admin/login')
  } else if (to.meta.requiresLicense) {
    import('@/utils/license.js').then(async ({ licenseState, FEATURE_NAMES, loadLicenseStatus }) => {
      if (!licenseState.loaded) {
        await loadLicenseStatus()
      }
      if (!licenseState.activated || !licenseState.features[to.meta.licenseFeature]) {
        const featureName = FEATURE_NAMES[to.meta.licenseFeature] || t('common.licenseRequiredShort')
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.warning(t('router.licenseFeatureRequired', { feature: featureName }))
        })
        next('/admin/dashboard')
      } else if (to.meta.requiresAdmin && (!user || !['super_admin', 'system_admin'].includes(user.role))) {
        next('/admin/dashboard')
      } else if (to.path === '/admin/feemanagement' && user && user.teacher_id && !['super_admin', 'system_admin'].includes(user.role)) {
        const feeManagersStr = localStorage.getItem('fee_managers')
        if (feeManagersStr) {
          try {
            const feeManagers = JSON.parse(feeManagersStr)
            if (Array.isArray(feeManagers) && feeManagers.includes(user.teacher_id)) {
              next()
              return
            }
          } catch (e) {
            window.logger.error('Failed to parse fee managers:', e)
          }
        }
        next('/admin/dashboard')
      } else if (to.path === '/admin/grades' && user && user.teacher_id && !['super_admin', 'system_admin'].includes(user.role)) {
        const gradeManagersStr = localStorage.getItem('grade_managers')
        if (gradeManagersStr) {
          try {
            const gradeManagers = JSON.parse(gradeManagersStr)
            if (Array.isArray(gradeManagers) && gradeManagers.includes(user.teacher_id)) {
              next()
              return
            }
          } catch (e) {
            window.logger.error('Failed to parse grade managers:', e)
          }
        }
        next('/admin/dashboard')
      } else if (to.path === '/admin/dashboard-view' && user && user.teacher_id && !['super_admin', 'system_admin'].includes(user.role)) {
        const operationManagersStr = localStorage.getItem('operation_managers')
        if (operationManagersStr) {
          try {
            const operationManagers = JSON.parse(operationManagersStr)
            if (Array.isArray(operationManagers) && operationManagers.includes(user.teacher_id)) {
              next()
              return
            }
          } catch (e) {
            window.logger.error('Failed to parse operation managers:', e)
          }
        }
        next('/admin/dashboard')
      } else {
        next()
      }
    }).catch(() => {
      next('/admin/dashboard')
    })
  } else if (to.meta.requiresAdmin && (!user || !['super_admin', 'system_admin'].includes(user.role))) {
    next('/admin/dashboard')
  } else if (to.path === '/admin/login' && token) {
    if (isTokenExpired(token)) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      next()
    } else {
      next('/admin/dashboard')
    }
  } else if (to.path === '/admin/login') {
    next()
  } else {
    next()
  }
})

export default router