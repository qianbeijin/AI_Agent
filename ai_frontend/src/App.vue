<script setup lang="ts">
// 引入刚才创建的聊天组件
import ChatMain from './components/ChatMain.vue'
</script>

<template>
  <div class="h-full w-full overflow-hidden bg-gray-100">
    <ChatMain />
  </div>
</template>

<style>
/* 确保根环境不溢出 */
html, body, #app {
  margin: 0 auto;
  padding: 0;
  overflow: hidden; /* 禁止全局滚动 */
}

/* 统一盒模型，防止 padding 撑开宽高 */
* {
  box-sizing: border-box;
}
</style>