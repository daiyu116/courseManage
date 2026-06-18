// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 CourseArrange Contributors
<template>
  <div 
    class="smart-command-container"
    :style="containerStyle"
    :class="{ 'unlicensed': !props.licensed }"
  >
    <!-- 未授权状态：显示禁用的悬浮按钮 -->
    <el-tooltip v-if="!props.licensed" content="智能指令管理为授权功能，请在系统授权管理中激活" placement="left" effect="light">
      <div class="smart-command-btn-wrapper unlicensed-btn-wrapper">
        <el-button
          type="info"
          circle
          size="large"
          class="smart-command-btn unlicensed-btn"
          :icon="Lock"
          disabled
        >
        </el-button>
      </div>
    </el-tooltip>

    <!-- 已授权状态：正常功能 -->
    <template v-if="props.licensed">
      <!-- 悬浮按钮 -->
      <div
        class="smart-command-btn-wrapper"
        @mousedown="startDrag"
        @touchstart="startTouchDrag"
      >
        <el-button
          type="primary"
          circle
          size="large"
          class="smart-command-btn"
          :class="{ 'is-dragging': isDragging }"
          :icon="Microphone"
        >
        </el-button>
      </div>

      <!-- 对话框 -->
      <el-dialog
      v-model="showDialog"
      title="智能指令助手"
      :width="dialogWidth"
      :close-on-click-modal="false"
      draggable
    >
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success" simple style="margin-bottom: 20px">
        <el-step title="输入新指令" />
        <el-step title="解析并预览" />
        <el-step title="确认并调用" />
      </el-steps>

      <!-- 步骤1：输入指令 -->
      <div v-if="currentStep === 0" class="input-section">
        <!-- 帮助信息（移至顶部，始终显示） -->
        <el-collapse v-model="activeHelpCollapse" class="help-section">
          <el-collapse-item title="查看支持的指令" name="1">
            <div v-for="(category, catIndex) in helpData.supported_commands" :key="catIndex" class="help-category">
              <h4>{{ category.category }}</h4>
              <div v-for="(cmd, cmdIndex) in category.commands" :key="cmdIndex" class="help-command">
                <h5>{{ cmd.action }}</h5>
                <ul>
                  <li v-for="(example, exIdx) in cmd.examples" :key="exIdx" class="example-item">
                    <span class="example-text">{{ example }}</span>
                    <el-button 
                      type="primary" 
                      size="small" 
                      circle 
                      :icon="DocumentCopy" 
                      @click="copyExample(example)"
                      class="copy-btn"
                      title="复制到输入框"
                    />
                  </li>
                </ul>
              </div>
            </div>
          </el-collapse-item>
          <!-- 解析模式说明 -->
          <el-collapse-item title="解析模式说明" name="2">
            <div class="parse-mode-info">
              <h4>🤖 AI解析模式（推荐）</h4>
              <ul>
                <li><strong>优势：</strong>理解能力强，支持自然语言表达，准确率高</li>
                <li><strong>适用场景：</strong>复杂指令、多样化表达、模糊意图识别</li>
                <li><strong>响应时间：</strong>约3-9秒（需调用AI服务）</li>
                <li><strong>注意事项：</strong>需要在系统设置中配置AI API密钥</li>
              </ul>
              
              <h4 style="margin-top: 15px;">⚙️ 规则解析模式</h4>
              <ul>
                <li><strong>优势：</strong>响应速度快（毫秒级），无需外部依赖</li>
                <li><strong>适用场景：</strong>标准格式指令、高频简单操作</li>
                <li><strong>局限性：</strong>只能识别预设的固定格式，灵活性较低</li>
                <li><strong>建议：</strong>作为AI解析失败时的备用方案</li>
              </ul>
              
              <el-alert
                title="💡 使用建议"
                type="info"
                :closable="false"
                style="margin-top: 10px"
              >
                默认启用AI解析，当AI服务不可用或解析失败时，系统会自动切换到规则解析作为兜底方案。您可以根据实际需求随时切换解析模式。
              </el-alert>
            </div>
          </el-collapse-item>
        </el-collapse>
        
        <el-input
          v-model="commandText"
          type="textarea"
          :rows="4"
          placeholder="请输入您的指令，例如：添加科目数学，导师张老师；也可参考上方支持的指令示例列表"
          @keyup.enter.ctrl="previewCommand"
        />
        
        <!-- 语音输入按钮 -->
        <div class="voice-input">
          <el-button
            :type="isRecording ? 'danger' : 'primary'"
            @click="toggleRecording"
            :disabled="!speechRecognitionSupported"
            :loading="isProcessing"
          >
            <el-icon v-if="!isRecording"><Microphone /></el-icon>
            <el-icon v-else><VideoPause /></el-icon>
            {{ isRecording ? '停止录音' : '语音输入' }}
          </el-button>
          
          <el-tooltip v-if="!speechRecognitionSupported" content="您的浏览器不支持语音识别，请使用Chrome或Edge浏览器" placement="top">
            <el-icon style="margin-left: 5px; color: #E6A23C;"><WarningFilled /></el-icon>
          </el-tooltip>
          
          <el-switch
            v-model="useAI"
            active-text="使用AI解析"
            inactive-text="规则解析"
            style="margin-left: 20px"
          />
        </div>
        
        <!-- 语音识别状态提示 -->
        <div v-if="isRecording" class="recording-status">
          <el-icon class="is-loading"><Microphone /></el-icon>
          <span>{{ recognitionStatus }}</span>
        </div>
        <!-- AI解析加载提示 -->
        <el-alert
          v-if="isProcessing && useAI"
          title="正在使用AI解析您的指令..."
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 15px"
        >
          <template #default>
            <div style="display: flex; align-items: center; gap: 10px;">
              <el-icon class="is-loading" style="font-size: 18px;"><Loading /></el-icon>
              <span>AI正在理解您的意图，请稍候（预计5-9秒）</span>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- 步骤2：预览确认 -->
      <div v-if="currentStep === 1" class="preview-section">
        <el-alert
          title="请确认以下信息是否正确"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 15px"
        />
        
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{ previewData.action_name }}</span>
              <el-tag :type="previewData.has_warning ? 'warning' : 'success'">
                {{ previewData.has_warning ? '需要注意' : '可以执行' }}
              </el-tag>
            </div>
          </template>
          
          <el-descriptions :column="1" border>
            <el-descriptions-item
              v-for="(field, index) in previewData.fields"
              :key="index"
              :label="field.label"
            >
              <span :style="{ color: field.warning ? '#E6A23C' : 'inherit' }">
                {{ field.value }}
              </span>
              <el-tooltip v-if="field.warning" :content="field.warning" placement="top">
                <el-icon style="color: #E6A23C; margin-left: 5px;"><WarningFilled /></el-icon>
              </el-tooltip>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <div v-if="previewData.recognized_text" class="recognized-text">
          <el-divider content-position="left">识别文本</el-divider>
          <p>{{ previewData.recognized_text }}</p>
        </div>
        
        <!-- 如果是排课操作，显示特殊提示 -->
        <el-alert
          v-if="previewData.needs_manual_confirmation"
          title="后续操作将打开手动排课界面"
          description="系统将自动填充已识别的信息，在后续界面您可以修改信息确认后再保存"
          type="warning"
          :closable="false"
          show-icon
          style="margin-top: 15px"
        />
      </div>

      <!-- 步骤3：执行结果 -->
      <div v-if="currentStep === 2" class="result-section">
        <el-alert
          :title="executionResult.success ? '执行成功' : '执行失败'"
          :type="executionResult.success ? 'success' : 'error'"
          :closable="false"
          show-icon
        >
          <div class="result-message">{{ executionResult.message }}</div>
        </el-alert>
        
        <!-- 解析详情 -->
        <div v-if="executionResult.parsed_intent" class="parsed-detail">
          <el-divider content-position="left">解析详情</el-divider>
          <pre>{{ JSON.stringify(executionResult.parsed_intent, null, 2) }}</pre>
        </div>
      </div>

      <!-- 底部按钮 -->
      <template #footer>
        <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
        <el-button @click="resetDialog">关闭</el-button>
        
        <el-button 
          v-if="currentStep === 0" 
          type="primary" 
          @click="previewCommand" 
          :loading="isProcessing"
        >
          下一步：预览
        </el-button>
        
        <el-button 
          v-if="currentStep === 1 && previewData?.action === 'navigate'" 
          type="success" 
          @click="confirmExecution" 
          :loading="isProcessing"
        >
          打开页面
        </el-button>
        
        <el-button 
          v-if="currentStep === 1 && previewData?.action === 'error'" 
          type="warning" 
          @click="confirmExecution" 
          :loading="isProcessing"
        >
          查看详情
        </el-button>
        
        <el-button 
          v-if="currentStep === 1 && !previewData?.action && !previewData?.needs_manual_confirmation" 
          type="success" 
          @click="confirmExecution" 
          :loading="isProcessing"
        >
          确认执行
        </el-button>
        
        <el-button 
          v-if="currentStep === 1 && previewData?.needs_manual_confirmation" 
          type="success" 
          @click="openManualSchedule" 
          :loading="isProcessing"
        >
          打开排课界面
        </el-button>
        
        <el-button 
          v-if="currentStep === 2" 
          type="primary" 
          @click="resetToInput"
        >
          新的指令
        </el-button>
      </template>
    </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed  } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, VideoPause, WarningFilled, Loading, DocumentCopy, Lock } from '@element-plus/icons-vue'
import api from '@/utils/api'

const props = defineProps({
  licensed: {
    type: Boolean,
    default: true
  }
})

const showDialog = ref(false)
const currentStep = ref(0)
const commandText = ref('')
const isRecording = ref(false)
const isProcessing = ref(false)
const useAI = ref(true)
const previewData = ref(null)
const executionResult = ref(null)
const helpData = ref({})
const speechRecognitionSupported = ref(false)
const recognitionStatus = ref('正在聆听...')
const activeHelpCollapse = ref([])

// 对话框宽度（响应式）
const dialogWidth = ref('700px')

// 拖拽相关变量
const spherePosition = ref({ x: 30, y: 30 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const dragOffset = ref({ x: 0, y: 0 })
const hasDragged = ref(false)
let touchStartTime = 0
let touchStartPos = { x: 0, y: 0 }
let timeoutTimer = null

// Web Speech API相关变量
let recognition = null

// 容器样式
const containerStyle = computed(() => ({
  position: 'fixed',
  right: `${spherePosition.value.x}px`,
  bottom: `${spherePosition.value.y}px`,
  zIndex: 9999,
  cursor: isDragging.value ? 'grabbing' : 'grab',
  transition: isDragging.value ? 'none' : 'right 0.2s ease, bottom 0.2s ease'
}))

// 检查浏览器是否支持语音识别
const checkSpeechRecognitionSupport = () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (SpeechRecognition) {
    speechRecognitionSupported.value = true
    recognition = new SpeechRecognition()
    recognition.lang = 'zh-CN'
    recognition.continuous = false
    recognition.interimResults = true
    
    recognition.onstart = () => {
      isRecording.value = true
      recognitionStatus.value = '正在聆听...'
    }
    
    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''
      
      if (!event.results || !event.results.length) {
        return
      }
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }
      
      // 显示临时结果
      if (interimTranscript) {
        recognitionStatus.value = `识别中: ${interimTranscript}`
      }
      
      // 最终结果
      if (finalTranscript) {
        commandText.value = finalTranscript
        recognitionStatus.value = '识别完成'
        stopRecording()
        
        // 自动预览
        setTimeout(() => {
          previewCommand()
        }, 500)
      }
    }
    
    recognition.onerror = (event) => {
      window.logger.error('语音识别错误:', event.error)
      let errorMessage = '语音识别失败'
      
      switch(event.error) {
        case 'no-speech':
          errorMessage = '未检测到语音，请重试'
          break
        case 'audio-capture':
          errorMessage = '无法访问麦克风'
          break
        case 'not-allowed':
          errorMessage = '麦克风权限被拒绝'
          break
        case 'network':
          errorMessage = '网络连接错误'
          break
        default:
          errorMessage = `识别错误: ${event.error}`
      }
      
      ElMessage.error(errorMessage)
      stopRecording()
    }
    
    recognition.onend = () => {
      if (isRecording.value) {
        recognitionStatus.value = '识别结束'
        isRecording.value = false
      }
    }
  } else {
    speechRecognitionSupported.value = false
  }
}

const copyExample = (example) => {
  commandText.value = example
  ElMessage.success('已复制到输入框')
}

// 加载帮助信息
onMounted(async () => {
  checkSpeechRecognitionSupport()
  
  // 从localStorage恢复位置
  const savedPosition = localStorage.getItem('smartCommandPosition')
  if (savedPosition) {
    try {
      spherePosition.value = JSON.parse(savedPosition)
    } catch (e) {
      spherePosition.value = { x: 30, y: 30 }
    }
  }
  
  // 根据屏幕宽度设置对话框宽度
  updateDialogWidth()
  window.addEventListener('resize', updateDialogWidth)
  
  try {
    const response = await api.get('/smart-command/help')
    helpData.value = response.data
    window.logger.log('[DEBUG] 帮助数据加载成功:', helpData.value)
    window.logger.log('[DEBUG] supported_commands:', helpData.value.supported_commands)
  } catch (error) {
    window.logger.error('加载帮助信息失败:', error)
    ElMessage.error('加载帮助信息失败')
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

// 更新对话框宽度
const updateDialogWidth = () => {
  const screenWidth = window.innerWidth
  if (screenWidth < 768) {
    // 手机端：使用屏幕宽度的 90%
    dialogWidth.value = '90%'
  } else if (screenWidth < 1024) {
    // 平板端：使用屏幕宽度的 80%
    dialogWidth.value = '80%'
  } else {
    // PC端：固定宽度
    dialogWidth.value = '700px'
  }
}

// 组件卸载时清理
onUnmounted(() => {
  if (recognition) {
    recognition.abort()
  }
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', handleTouchDrag)
  document.removeEventListener('touchend', stopTouchDrag)
  window.removeEventListener('resize', handleResize)
})

// 开始触摸拖拽
const startTouchDrag = (e) => {
  const touch = e.touches[0]
  
  touchStartTime = Date.now()
  touchStartPos = {
    x: touch.clientX,
    y: touch.clientY
  }
  
  isDragging.value = true
  hasDragged.value = false
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

// 开始拖拽
const startDrag = (e) => {
  isDragging.value = true
  hasDragged.value = false
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
}


// 处理触摸拖拽
const handleTouchDrag = (e) => {
  if (!isDragging.value) return
  
  const touch = e.touches?.[0]
  if (!touch) return
  
  const deltaX = dragStart.value.x - touch.clientX
  const deltaY = touch.clientY - dragStart.value.y
  
  updatePosition(deltaX, deltaY)
  e.preventDefault()
}

// 处理鼠标拖拽
const handleDrag = (e) => {
  if (!isDragging.value) return
  
  const deltaX = dragStart.value.x - e.clientX
  const deltaY = e.clientY - dragStart.value.y
  
  updatePosition(deltaX, deltaY)
}

// 更新位置的通用函数
const updatePosition = (deltaX, deltaY) => {
  if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
    hasDragged.value = true
  }
  
  let newX = dragOffset.value.x + deltaX
  let newY = dragOffset.value.y + deltaY
  
  const maxX = window.innerWidth - 80
  const maxY = window.innerHeight - 80
  
  newX = Math.max(0, Math.min(newX, maxX))
  newY = Math.max(0, Math.min(newY, maxY))
  
  spherePosition.value = { x: newX, y: newY }
}

// 停止鼠标拖拽
const stopDrag = () => {
  const dragEndTime = Date.now()
  
  // 如果没有发生明显的拖拽，认为是点击
  if (!hasDragged.value) {
    showDialog.value = true
  }
  
  isDragging.value = false
  hasDragged.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// 停止触摸拖拽
const stopTouchDrag = (e) => {
  const touchEndTime = Date.now()
  const touchDuration = touchEndTime - touchStartTime
  
  // 从事件参数中获取最后一个触摸位置
  const lastTouch = e?.changedTouches?.[0]
  if (lastTouch) {
    const deltaX = Math.abs(lastTouch.clientX - touchStartPos.x)
    const deltaY = Math.abs(lastTouch.clientY - touchStartPos.y)
    
    // 如果触摸时间很短且移动距离很小，认为是点击而非拖拽
    if (touchDuration < 200 && deltaX < 10 && deltaY < 10) {
      showDialog.value = true
    }
  } else {
    // 如果没有触摸信息，但有拖拽标志，则不打开对话框
    if (!hasDragged.value) {
      showDialog.value = true
    }
  }
  
  isDragging.value = false
  hasDragged.value = false
  document.removeEventListener('touchmove', handleTouchDrag)
  document.removeEventListener('touchend', stopTouchDrag)
}

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
  localStorage.setItem('smartCommandPosition', JSON.stringify(spherePosition.value))
}

// 监听位置变化并保存
watch(spherePosition, (newVal) => {
  localStorage.setItem('smartCommandPosition', JSON.stringify(newVal))
}, { deep: true })

// 预览指令
const previewCommand = async () => {
  if (!commandText.value.trim()) {
    ElMessage.warning('请输入指令')
    return
  }

  isProcessing.value = true
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
  previewData.value = null
  
  // 设置超时提示定时器
  if (useAI.value) {
    timeoutTimer = setTimeout(() => {
      if (isProcessing.value) {
        ElMessage.info({
          message: 'AI解析耗时较长，请耐心等待...',
          duration: 5000 // 5秒后自动关闭
        })
      }
    }, 5000) // 5秒后显示等待提示
  }

  try {
    const response = await api.post('/smart-command/preview', {
      text: commandText.value,
      use_ai: useAI.value
    }, {
      timeout: 30000
    })
    
    // 清除超时提示
    if (timeoutTimer) {
      clearTimeout(timeoutTimer)
      timeoutTimer = null
    }

    if (response.data.success) {
      previewData.value = {
        ...response.data.parsed_intent,
        ...response.data.preview_data,
        person_names: response.data.parsed_intent.person_names,
        class_name: response.data.parsed_intent.class_name,
        course_name: response.data.parsed_intent.course_name,
        teacher_name: response.data.parsed_intent.teacher_name,
        room_name: response.data.parsed_intent.room_name,
        day_of_week: response.data.parsed_intent.day_of_week,
        start_time: response.data.parsed_intent.start_time,
        end_time: response.data.parsed_intent.end_time,
        start_date: response.data.parsed_intent.start_date,
        end_date: response.data.parsed_intent.end_date,
        needs_manual_confirmation: response.data.parsed_intent.needs_manual_confirmation
      }
      currentStep.value = 1
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    // 清除超时提示
    if (timeoutTimer) {
      clearTimeout(timeoutTimer)
      timeoutTimer = null
    }
    
    let errorMessage = '解析指令失败'
    if (error.code === 'ECONNABORTED') {
      errorMessage = '请求超时，请检查网络连接或尝试简化指令'
      if (useAI.value) {
        errorMessage += '。如果AI服务响应较慢，可以尝试切换到规则解析模式'
      }
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.message) {
      errorMessage = error.message
    }
    ElMessage.error(errorMessage)
  } finally {
    isProcessing.value = false
  }
}

// 确认执行
const confirmExecution = async () => {
  isProcessing.value = true

  try {
    const response = await api.post('/smart-command/execute', {
      parsed_intent: previewData.value,
      confirmed: true
    }, {
      timeout: 30000
    })

    executionResult.value = response.data
    
    // 检查是否为导航操作
    if (response.data.success && response.data.parsed_intent?.action === 'navigate') {
      // 执行导航
      handleNavigation(response.data.parsed_intent)
      currentStep.value = 2
      ElMessage.success(response.data.message || '正在打开页面...')
    } else if (response.data.success && response.data.parsed_intent?.action === 'error') {
      // 显示错误信息
      currentStep.value = 2
      ElMessage.error(response.data.message || '解析失败')
    } else {
      // 传统执行方式（保留兼容性）
      currentStep.value = 2
      if (response.data.success) {
        ElMessage.success(response.data.message)
      } else {
        ElMessage.error(response.data.message)
      }
    }
  } catch (error) {
    let errorMessage = '执行指令失败'
    if (error.code === 'ECONNABORTED') {
      errorMessage = '请求超时，请检查网络连接'
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.message) {
      errorMessage = error.message
    }
    ElMessage.error(errorMessage)
  } finally {
    isProcessing.value = false
  }
}

// 处理导航操作
const handleNavigation = (navigationData) => {
  // 关闭对话框
  showDialog.value = false
  
  window.logger.log('[DEBUG] 导航数据:', navigationData)
  
  // 关键修复：同时保存到两个key，确保兼容性
  const dataToSave = navigationData.storage_data || {}
  
  // 对于排课操作，需要转换为Schedules页面期望的格式
  if (navigationData.path && navigationData.path.includes('/schedules')) {
    const scheduleData = {
      studentNames: dataToSave.studentNames || dataToSave.person_names || [],
      className: dataToSave.className || dataToSave.class_name || '',
      courseName: dataToSave.courseName || dataToSave.course_name || '',
      teacherName: dataToSave.teacherName || dataToSave.teacher_name || '',
      roomName: dataToSave.roomName || dataToSave.room_name || '',
      dayOfWeek: dataToSave.dayOfWeek || dataToSave.day_of_week || null,
      startTime: dataToSave.startTime || dataToSave.start_time || '',
      endTime: dataToSave.endTime || dataToSave.end_time || '',
      startDate: dataToSave.startDate || dataToSave.start_date || '',
      endDate: dataToSave.endDate || dataToSave.end_date || ''
    }
    
    window.logger.log('[DEBUG] 转换后的排课数据:', scheduleData)
    
    // 保存到 smartCommandScheduleData（Schedules页面读取的key）
    sessionStorage.setItem('smartCommandScheduleData', JSON.stringify(scheduleData))
    window.logger.log('[DEBUG] 已保存到 smartCommandScheduleData')
  }
  
  // 同时也保存到 smartCommandData（其他页面可能使用）
  sessionStorage.setItem('smartCommandData', JSON.stringify(dataToSave))
  window.logger.log('[DEBUG] 已保存到 smartCommandData')
  
  // 构建URL
  let url = navigationData.path
  if (navigationData.query && Object.keys(navigationData.query).length > 0) {
    // 过滤掉null和undefined的值
    const validQuery = {}
    Object.keys(navigationData.query).forEach(key => {
      if (navigationData.query[key] !== null && navigationData.query[key] !== undefined) {
        validQuery[key] = navigationData.query[key]
      }
    })
    
    if (Object.keys(validQuery).length > 0) {
      url += '?' + new URLSearchParams(validQuery)
    }
  }
  
  window.logger.log('[DEBUG] 跳转URL:', url)
  
  // 执行跳转
  window.location.href = url
}

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 重置到输入状态
const resetToInput = () => {
  currentStep.value = 0
  commandText.value = ''
  previewData.value = null
  executionResult.value = null
  // 清除超时定时器
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
}

// 重置对话框
const resetDialog = () => {
  // 立即清除超时定时器
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
  
  showDialog.value = false
  setTimeout(() => {
    resetToInput()
  }, 300)
}

// 打开手动排课界面（保留兼容性）
const openManualSchedule = () => {
  // 关闭对话框
  showDialog.value = false
  
  window.logger.log('[DEBUG] previewData.value:', previewData.value)
  
  // 准备排课数据 - 兼容两种命名方式
  const scheduleData = {
    studentNames: previewData.value.person_names || previewData.value.student_names || [],
    className: previewData.value.class_name || previewData.value.className || '',
    courseName: previewData.value.course_name || previewData.value.courseName || '',
    teacherName: previewData.value.teacher_name || previewData.value.teacherName || '',
    roomName: previewData.value.room_name || previewData.value.roomName || '',
    dayOfWeek: previewData.value.day_of_week || previewData.value.dayOfWeek || null,
    startTime: previewData.value.start_time || previewData.value.startTime || '',
    endTime: previewData.value.end_time || previewData.value.endTime || '',
    startDate: previewData.value.start_date || previewData.value.startDate || '',
    endDate: previewData.value.end_date || previewData.value.endDate || ''
  }
  
  window.logger.log('[DEBUG] 保存到sessionStorage的scheduleData:', scheduleData)
  
  // 存储到sessionStorage，供Schedules页面读取
  sessionStorage.setItem('smartCommandScheduleData', JSON.stringify(scheduleData))
  
  // 跳转到排课页面
  window.location.href = '/admin/schedules?action=add'
  
  ElMessage.info('正在打开排课界面，已自动填充识别的信息')
}

// 切换录音状态
const toggleRecording = () => {
  if (!speechRecognitionSupported.value) {
    ElMessage.warning('您的浏览器不支持语音识别功能，请使用Chrome或Edge浏览器')
    return
  }
  
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

// 开始录音
const startRecording = () => {
  if (!recognition) {
    ElMessage.error('语音识别未初始化')
    return
  }
  
  try {
    recognition.start()
    ElMessage.info('请开始说话...')
  } catch (error) {
    ElMessage.error('启动语音识别失败: ' + error.message)
  }
}

// 停止录音
const stopRecording = () => {
  if (recognition) {
    try {
      recognition.stop()
    } catch (error) {
      window.logger.error('停止语音识别失败:', error)
    }
  }
  isRecording.value = false
}
</script>

<style scoped>
.smart-command-container {
  user-select: none;
  touch-action: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.smart-command-container.unlicensed {
  pointer-events: auto;
}

.unlicensed-btn-wrapper {
  cursor: not-allowed !important;
}

.unlicensed-btn {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

.smart-command-btn-wrapper {
  cursor: grab;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  display: inline-block;
  position: relative;
  padding: 10px;
  margin: -10px;
}

.smart-command-btn-wrapper:active {
  cursor: grabbing;
}

.smart-command-btn {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s;
  pointer-events: auto;
}

.smart-command-btn.is-dragging {
  opacity: 0.8;
  transform: scale(1.15);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.4);
  pointer-events: none;
}

.smart-command-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.input-section {
  margin-bottom: 20px;
}

.voice-input {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.recording-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border-radius: 4px;
  color: #409eff;
  font-size: 14px;
}

.preview-section {
  margin-top: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recognized-text {
  margin-top: 15px;
}

.recognized-text p {
  margin: 10px 0 0 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-style: italic;
}

.result-section {
  margin-top: 10px;
}

.result-message {
  margin-top: 10px;
}

.parsed-detail {
  margin-top: 15px;
}

.parsed-detail pre {
  margin: 0;
  font-size: 12px;
  overflow-x: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.example-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  margin: 4px 0;
  background-color: #f5f7fa;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.example-item:hover {
  background-color: #ecf5ff;
}

.example-text {
  flex: 1;
  margin-right: 10px;
  color: #606266;
  line-height: 1.6;
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
}

.copy-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  padding: 0;
  min-height: 24px;
}

.copy-btn :deep(.el-icon) {
  font-size: 12px;
}

.help-section {
  margin-top: 0;
  margin-bottom: 15px;
}

.help-section :deep(.el-collapse-item__header) {
  background-color: #ecf5ff;
  padding: 8px 15px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 14px;
}

.help-section :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.help-section :deep(.el-collapse-item__content) {
  padding-bottom: 10px;
  padding-top: 10px;
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
}

.help-section :deep(.el-collapse-item__content)::-webkit-scrollbar {
  width: 6px;
}

.help-section :deep(.el-collapse-item__content)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.help-section :deep(.el-collapse-item__content)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.help-section :deep(.el-collapse-item__content)::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.help-category {
  margin-bottom: 20px;
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
  cursor: text;
}

.help-category h4 {
  margin: 0 0 12px 0;
  color: #409eff;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 2px solid #ecf5ff;
  padding-bottom: 8px;
}

.help-command {
  margin-bottom: 12px;
  padding-left: 10px;
}

.help-command:last-child {
  margin-bottom: 0;
}

.help-command h5 {
  margin: 8px 0 6px 0;
  color: #67c23a;
  font-size: 14px;
  font-weight: 600;
}

.help-command ul {
  margin: 0;
  padding-left: 20px;
}

.help-command li {
  margin: 4px 0;
  color: #606266;
  line-height: 1.6;
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
  cursor: text;
}

/* 解析模式说明样式 */
.parse-mode-info {
  padding: 10px;
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
  cursor: text;
}

.parse-mode-info h4 {
  margin: 0 0 10px 0;
  color: #409eff;
  font-size: 15px;
  font-weight: bold;
}

.parse-mode-info ul {
  margin: 8px 0;
  padding-left: 20px;
}

.parse-mode-info li {
  margin: 6px 0;
  color: #606266;
  line-height: 1.8;
  font-size: 13px;
}

.parse-mode-info strong {
  color: #303133;
  font-weight: 600;
}
</style>