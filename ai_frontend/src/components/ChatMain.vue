<script setup lang="ts">
import { ref, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Cpu, User, Delete, Top } from '@element-plus/icons-vue'

// --- 1. 定义数据结构 ---
interface ChatMessage {
  role: 'user' | 'ai'
  content: string
}

// --- 2. 状态变量 ---
const userInput = ref('')
const isLoading = ref(false)
const messageList = ref<ChatMessage[]>([
  // 放一条默认的欢迎语，让界面不那么空
  { role: 'ai', content: '你好！我是 DeepSeek AI 助手。有什么我可以帮你的吗？' }
])
const scrollRef = ref<HTMLElement | null>(null) // 滚动锚点

// --- 3. 核心发送逻辑 ---
const handleSend = async () => {
  const content = userInput.value.trim()
  if (!content || isLoading.value) return

  // 1. 用户消息上屏
  messageList.value.push({ role: 'user', content: content })
  userInput.value = ''
  isLoading.value = true

  // 2. 自动滚动到底部
  scrollToBottom()

  try {
    // 3. 发送请求
    const res = await axios.post('http://127.0.0.1:8000/api/v1/chat', {
      message: content
    })

    // 4. AI 消息上屏
    messageList.value.push({ role: 'ai', content: res.data.answer })
  } catch (error) {
    console.error(error)
    ElMessage.error('网络开小差了，请检查后端服务')
    messageList.value.push({ role: 'ai', content: '🔴 出错了：无法连接到 AI 大脑。' })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// --- 4. 辅助函数：滚动到底部 ---
const scrollToBottom = () => {
  nextTick(() => {
    scrollRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

//清空历史记录
const clearHistory = () => {
    // 1. 先弹窗询问
  ElMessageBox.confirm(
    '确定要清空所有聊天记录吗？此操作无法撤销。',
    '警告',
    {
      confirmButtonText: '狠心删除',
      cancelButtonText: '手滑了',
      type: 'warning',
    }
  )
    .then(() => {
      // 2. 用户点了“确定”才执行删除
      messageList.value = [
        { role: 'ai', content: '你好！我是 DeepSeek AI 助手。有什么我可以帮你的吗？' }
      ]
      ElMessage.success('记忆已清除')
    })
    .catch(() => {
      // 3. 用户点了“取消”，什么都不做
      ElMessage.info('操作已取消')
    })
}
</script>

<template>
  <div class="flex flex-col h-screen bg-gray-50">

    <header class="shrink-0 bg-white border-b border-gray-200">
      <div class="max-w-2xl mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <el-icon :size="24" class="text-blue-500"><Cpu /></el-icon>
          <div>
            <h1 class="text-lg font-semibold text-gray-800 tracking-tight">DeepSeek AI</h1>
            <div class="flex items-center gap-1.5">
               <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span class="text-xs text-gray-500 font-medium">Online</span>
            </div>
          </div>
        </div>
        <!-- <el-button circle plain size="small"><el-icon><MoreFilled /></el-icon></el-button> -->
         <el-button circle plain size="small" @click="clearHistory"><el-icon><Delete /></el-icon></el-button>
      </div>
    </header>

    <main class="flex-1 overflow-y-auto scroll-smooth p-6">
      <div class="max-w-2xl mx-auto w-full space-y-8">
        
        <div 
          v-for="(msg, index) in messageList" 
          :key="index"
          class="flex items-start gap-4"
          :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
        >
          <div 
            class="shrink-0 p-1.5 rounded-lg border shadow-sm"
            :class="msg.role === 'user' ? 'bg-gray-900 border-gray-900' : 'bg-white border-gray-200'"
          >
             <el-icon :size="18" :class="msg.role === 'user' ? 'text-white' : 'text-blue-600'">
               <component :is="msg.role === 'user' ? User : Cpu" />
             </el-icon>
          </div>

          <div 
            class="space-y-1.5 flex flex-col"
            :class="msg.role === 'user' ? 'items-end' : 'items-start'"
          >
              <span class="text-xs text-gray-400 mx-1">{{ msg.role === 'user' ? 'You' : 'DeepSeek' }}</span>
              
              <div 
                class="px-5 py-3.5 rounded-2xl shadow-sm leading-7 text-[15px] max-w-[85%] w-fit break-words"
                :class="msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none shadow-md' 
                    : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'"
                >
                {{ msg.content }}
                </div>
          </div>
        </div>

        <div v-if="isLoading" class="flex items-start gap-4">
           <div class="shrink-0 p-1.5 rounded-lg bg-white border border-gray-200 shadow-sm">
             <el-icon :size="18" class="text-blue-600"><Cpu /></el-icon>
           </div>
           <div class="bg-gray-100 border border-gray-200 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-1">
               <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
               <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
               <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
           </div>
        </div>

        <div ref="scrollRef" class="h-4"></div>
      </div>
    </main>

    <footer class="shrink-0 bg-white border-t border-gray-100">
      <div class="max-w-2xl mx-auto w-full px-6 py-5">
        <div class="relative rounded-2xl shadow-sm ring-1 ring-gray-200 bg-gray-50 focus-within:ring-2 focus-within:ring-blue-500 focus-within:bg-white transition-all overflow-hidden">
          
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 4 }"
            resize="none"
            placeholder="给 DeepSeek 发送消息..."
            class="!border-none !shadow-none w-full !bg-transparent custom-input py-3 px-4 text-gray-700 placeholder-gray-400 leading-6"
            input-style="background: transparent; box-shadow: none;"
            :disabled="isLoading"
            @keydown.enter.prevent="handleSend"
          />
          
          <div class="absolute bottom-2 right-2">
             <el-button 
                type="primary" 
                size="small" 
                circle 
                class="!w-8 !h-8 !bg-blue-600 border-none hover:!bg-blue-700 transition-transform active:scale-90"
                :loading="isLoading"
                :disabled="!userInput.trim() && !isLoading"
                @click="handleSend"
             >
                <el-icon v-if="!isLoading" class="text-white"><Top /></el-icon>
             </el-button>
          </div>
        </div>
        <p class="text-center text-[10px] text-gray-300 mt-3 select-none">
           DeepSeek Model V3 · Generated content may be inaccurate
        </p>
      </div>
    </footer>

  </div>
</template>

<style scoped>
/* 针对 Element Input 的深度样式覆盖，确保背景透明 */
:deep(.el-textarea__inner) {
    box-shadow: none !important;
    background-color: transparent !important;
    padding-right: 40px; /* 给右下角的按钮留位置 */
}
</style>

<style scoped>
/* 30k 细节：自定义滚动条样式 (兼容 Chrome/Safari/Edge) */
/* 让滚动条看起来更现代，不那么粗糙 */
main::-webkit-scrollbar {
  width: 8px;
}

main::-webkit-scrollbar-track {
  background: transparent;
}

main::-webkit-scrollbar-thumb {
  background-color: #e5e7eb; /* gray-200 */
  border-radius: 20px;
  border: 3px solid transparent; /* 增加 padding 效果 */
  background-clip: content-box;
}

main::-webkit-scrollbar-thumb:hover {
    background-color: #d1d5db; /* gray-300 */
}

/* 输入框的自定义滚动条 */
.custom-scrollbar :deep(textarea::-webkit-scrollbar) {
 width: 6px;
}
.custom-scrollbar :deep(textarea::-webkit-scrollbar-thumb) {
  background-color: #e5e7eb;
  border-radius: 10px;
}
</style>