// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 CourseArrange Contributors
/**
 * 前端日志工具
 * 根据站点配置决定是否输出console日志
 */

// 缓存日志启用状态，避免每次都读取localStorage
let cachedLogEnabled = null

// 从localStorage获取前端日志启用状态
const isFrontendLogEnabled = () => {
  // 如果缓存为空，从localStorage读取
  if (cachedLogEnabled === null) {
    const enabled = localStorage.getItem('frontend_log_enabled')
    // 默认启用，除非明确设置为false
    cachedLogEnabled = enabled !== 'false'
  }
  return cachedLogEnabled
}

// 提供刷新缓存的方法，用于配置更改后立即生效
const refreshLogConfig = () => {
  cachedLogEnabled = null
  // 立即重新读取
  return isFrontendLogEnabled()
}

// 监听storage事件，实现跨标签页同步
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === 'frontend_log_enabled') {
      // 清除缓存，下次使用时会重新读取
      cachedLogEnabled = null
      console.log('[Logger] 检测到日志配置变更，新状态:', event.newValue)
    }
  })
}

// 日志工具对象
const logger = {
  /**
   * 输出普通日志
   * @param {...any} args - 要输出的内容
   */
  log(...args) {
    if (isFrontendLogEnabled()) {
      console.log(...args)
    }
  },

  /**
   * 输出警告日志
   * @param {...any} args - 要输出的内容
   */
  warn(...args) {
    if (isFrontendLogEnabled()) {
      console.warn(...args)
    }
  },

  /**
   * 输出错误日志
   * @param {...any} args - 要输出的内容
   */
  error(...args) {
    if (isFrontendLogEnabled()) {
      console.error(...args)
    }
  },

  /**
   * 输出信息日志
   * @param {...any} args - 要输出的内容
   */
  info(...args) {
    if (isFrontendLogEnabled()) {
      console.info(...args)
    }
  },

  /**
   * 输出调试日志
   * @param {...any} args - 要输出的内容
   */
  debug(...args) {
    if (isFrontendLogEnabled()) {
      console.debug(...args)
    }
  },

  /**
   * 输出表格日志
   * @param {...any} args - 要输出的内容
   */
  table(...args) {
    if (isFrontendLogEnabled()) {
      console.table(...args)
    }
  },

  /**
   * 分组开始
   * @param {...any} args - 分组标签
   */
  group(...args) {
    if (isFrontendLogEnabled()) {
      console.group(...args)
    }
  },

  /**
   * 分组结束
   */
  groupEnd() {
    if (isFrontendLogEnabled()) {
      console.groupEnd()
    }
  },

  /**
   * 计时开始
   * @param {string} label - 计时器标签
   */
  time(label) {
    if (isFrontendLogEnabled()) {
      console.time(label)
    }
  },

  /**
   * 计时结束
   * @param {string} label - 计时器标签
   */
  timeEnd(label) {
    if (isFrontendLogEnabled()) {
      console.timeEnd(label)
    }
  },

  /**
   * 刷新日志配置缓存
   * 在更改配置后调用此方法以立即生效
   */
  refreshConfig() {
    return refreshLogConfig()
  }
}

export default logger