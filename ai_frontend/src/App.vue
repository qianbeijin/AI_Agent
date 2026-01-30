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
/* 全局样式重置 (可选，防止某些默认边距) */
body, html {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}
</style>