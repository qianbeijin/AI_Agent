<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// 引入图标：确保你安装了 @element-plus/icons-vue
import { Cpu, User, Delete, Top } from '@element-plus/icons-vue'

// --- 数据接口 ---
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// --- 状态变量 ---
const sessionId = ref(localStorage.getItem('session_id') || '')
const userInput = ref('')
const isLoading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)
const messageList = ref<ChatMessage[]>([
  { 
    role: 'assistant', 
    content: '你好！我是 DeepSeek AI 助手。有什么我可以帮你的吗？' 
  }
])

// 核心逻辑
const handleSend = async () => {
  const content = userInput.value.trim()
  if (!content || isLoading.value) return

  // 1. 用户消息立即上屏
  messageList.value.push({ role: 'user', content: content })
  userInput.value = ''
  isLoading.value = true
  scrollToBottom() // 滚到底部

  try {
    // --- 关键变化 1: 放弃 axios，改用原生 fetch ---
    const response = await fetch('http://127.0.0.1:8000/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: content,
        // 如果有 session_id 就带上，没有传 null
        session_id: sessionId.value ? sessionId.value : null 
      })
    })

    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
    isLoading.value = false

    // --- 关键变化 2: 从响应头里抓取 Session ID ---
    // 因为流式响应体里全是乱码，ID 只能藏在 Header 里
    const newSessionId = response.headers.get('X-Session-Id')
    if (newSessionId) {
      sessionId.value = newSessionId
    }

    // --- 关键变化 3: 创建流式读取器 ---
    const reader = response.body?.getReader()
    const decoder = new TextDecoder() // 解码器：把二进制转成中文

    if (!reader) return

    // 先放一个空的 AI 消息占位，准备接收文字
    messageList.value.push({ role: 'assistant', content: '' })
    // 获取刚刚 push 进去的那条消息的引用 (指针)
    const currentAiMessage = messageList.value[messageList.value.length - 1]

    // --- 关键变化 4: 死循环读取流 ---
    while (true) {
      // read() 会返回两个值：done (是否结束), value (这一段二进制数据)
      const { done, value } = await reader.read()
      
      if (done) break // 如果流结束了，跳出循环

      // 解码并拼接到当前消息上
      const text = decoder.decode(value, { stream: true })
      currentAiMessage.content += text

      // 每蹦出一个字，就自动滚到底部
      scrollToBottom() 
    }

  } catch (error) {
    console.error(error)
    messageList.value.push({ role: 'assistant', content: '🔴 网络连接异常，请稍后重试。' })
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
    
    <header class="shrink-0 bg-white border-b border-gray-100 flex items-center justify-center px-6 relative z-1 py-4">
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

    <main class="flex-1 overflow-y-auto bg-[#f8f9fa] scroll-smooth">
      <div class="w-2xl mx-auto px-4 py-8 flex flex-col gap-6">
        
        <div 
          v-for="(msg, index) in messageList" 
          :key="index"
          class="flex w-full"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div 
            class="flex items-start gap-3 max-w-[85%] md:max-w-[75%] min-w-0"
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

            <div class="flex flex-col min-w-0" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
              
              <div 
                class="px-4 py-3 rounded-2xl text-[15px] leading-7 shadow-[0_2px_8px_rgba(0,0,0,0.04)] break-words whitespace-pre-wrap text-left max-w-full overflow-hidden"
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