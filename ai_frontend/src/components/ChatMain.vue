<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
// 引入图标：确保你安装了 @element-plus/icons-vue
import { Cpu, User, Delete, Top } from '@element-plus/icons-vue'

// --- 数据接口 ---
interface ChatMessage {
  role: 'user' | 'ai'
  content: string
}

// --- 状态变量 ---
const sessionId = ref(localStorage.getItem('session_id') || '')
const userInput = ref('')
const isLoading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)
const messageList = ref<ChatMessage[]>([
  { 
    role: 'ai', 
    content: '你好！我是 DeepSeek AI 助手。有什么我可以帮你的吗？' 
  }
])

// --- 核心逻辑 ---
const handleSend = async () => {
  const content = userInput.value.trim()
  if (!content || isLoading.value) return

  // 1. 用户消息上屏
  messageList.value.push({ role: 'user', content })
  userInput.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    // 2. 发送请求 (根据你的后端地址修改)
    const res = await axios.post('http://127.0.0.1:8000/api/v1/chat', {
      message: content,
      session_id: sessionId.value ? sessionId.value : null
    })
    
    // 3. 接收响应
    if (res.data && res.data.answer) {
      sessionId.value = res.data.session_id
      messageList.value.push({ role: 'ai', content: res.data.answer })
      localStorage.setItem('session_id', sessionId.value)
    }
  } catch (error) {
    ElMessage.error('服务连接失败')
    messageList.value.push({ role: 'ai', content: '🔴 网络连接异常，请检查后端服务。' })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

watch(sessionId, (newSid) => {
    localStorage.setItem('session_id', newSid)
}, { deep: true })

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    scrollRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

// 清空历史
const clearHistory = () => {
  ElMessageBox.confirm('确认清空对话记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    messageList.value = []
    ElMessage.success('已清空')
  }).catch(() => {})
}
</script>

<template>
  <div class="flex flex-col h-screen w-full bg-white overflow-hidden font-sans">
    
    <header class="shrink-0  bg-white border-b border-gray-100 flex items-center justify-center px-6 relative z-1 py-4">
      <div class="max-w-4xl w-full flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-50/50 rounded-xl flex items-center justify-center border border-blue-100">
             <el-icon :size="22" class="text-blue-600"><Cpu /></el-icon>
          </div>
          <div class="flex flex-col">
            <h1 class="text-xl font-bold text-gray-800 tracking-tight leading-none">DeepSeek AI</h1>
            <div class="flex items-center gap-1.5 mt-1">
              <span class="w-2 h-2 rounded-full bg-green-500"></span>
              <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Online</span>
            </div>
          </div>
        </div>

        <el-button circle plain size="small" class="!border-gray-200 hover:!bg-red-50 hover:!text-red-500 hover:!border-red-200 transition-colors" @click="clearHistory">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </header>

    <main class="flex-1 min-h-0 overflow-y-auto bg-[#f8f9fa] scroll-smooth">
      <div class="max-w-3xl mx-auto px-4 py-8 flex flex-col gap-6">
        
        <div 
          v-for="(msg, index) in messageList" 
          :key="index"
          class="flex w-full"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div 
            class="flex items-start gap-3 max-w-[85%] md:max-w-[75%]"
            :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
          >
            <div 
              class="shrink-0 w-9 h-9 rounded-lg flex items-center justify-center border shadow-sm select-none"
              :class="msg.role === 'user' ? 'bg-gray-900 border-gray-900' : 'bg-white border-gray-200'"
            >
              <el-icon :size="18" :class="msg.role === 'user' ? 'text-white' : 'text-blue-600'">
                <component :is="msg.role === 'user' ? User : Cpu" />
              </el-icon>
            </div>

            <div class="flex flex-col" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
              <div 
                class="px-4 py-3 rounded-2xl text-[15px] leading-7 shadow-[0_2px_8px_rgba(0,0,0,0.04)] break-words whitespace-pre-wrap text-left"
                :class="msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'"
              >
                {{ msg.content }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="isLoading" class="flex justify-start w-full">
           <div class="flex items-start gap-3">
             <div class="shrink-0 w-9 h-9 rounded-lg bg-white border border-gray-200 flex items-center justify-center">
               <el-icon :size="18" class="text-blue-600"><Cpu /></el-icon>
             </div>
             <div class="bg-white border border-gray-100 px-5 py-4 rounded-2xl rounded-tl-none shadow-sm">
                <div class="flex space-x-1.5">
                   <div class="w-2 h-2 bg-gray-300 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                   <div class="w-2 h-2 bg-gray-300 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                   <div class="w-2 h-2 bg-gray-300 rounded-full animate-bounce"></div>
                </div>
             </div>
           </div>
        </div>

        <div ref="scrollRef" class="h-4"></div>
      </div>
    </main>

    <footer class="shrink-0 bg-white pt-2 pb-6 px-4">
      <div class="max-w-3xl mx-auto w-full">
        <div class="relative flex items-end gap-2 bg-gray-100/50 hover:bg-gray-100 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-100 border border-transparent focus-within:border-blue-500 rounded-[24px] px-2 py-2 transition-all duration-200">
          
          <el-input
            v-model="userInput"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            resize="none"
            placeholder="给 DeepSeek 发送消息..."
            class="w-full !bg-transparent"
            :disabled="isLoading"
            @keydown.enter.prevent="handleSend"
          />
          
          <el-button 
            type="primary" 
            circle 
            class="!w-9 !h-9 !min-h-[36px] !bg-blue-600 border-none hover:!bg-blue-700 shadow-md mb-[2px] mr-[2px]"
            :loading="isLoading"
            :disabled="!userInput.trim()"
            @click="handleSend"
          >
            <el-icon v-if="!isLoading" :size="16"><Top /></el-icon>
          </el-button>
        </div>

        <p class="text-center text-[11px] text-gray-400 mt-3">
          Powered by DeepSeek V3 · Generated content may be inaccurate
        </p>
      </div>
    </footer>

  </div>
</template>

<style scoped>
/* --- 样式覆盖：处理 Element Plus 默认丑陋样式 --- */

/* 1. 穿透修改 Input 样式，使其透明 */
:deep(.el-textarea__inner) {
  box-shadow: none !important;
  background-color: transparent !important;
  border: none !important;
  padding: 10px 12px !important;
  font-size: 15px !important;
  color: #1f2937 !important; /* gray-800 */
}

/* 2. 隐藏 Textarea 的右下角 resize 图标 */
:deep(.el-textarea .el-input__count) {
  background: transparent !important;
}

/* 3. 美化滚动条 (Webkit) */
main::-webkit-scrollbar {
  width: 6px;
}
main::-webkit-scrollbar-track {
  background: transparent;
}
main::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 20px;
}
main::-webkit-scrollbar-thumb:hover {
  background-color: #d1d5db;
}
</style>