import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import './assets/main.css' // 引入 Tailwind 

import ElementPlus from 'element-plus' // 引入 Element Plus 组件库
import 'element-plus/dist/index.css'   // 引入 Element Plus 样式文件
import * as ElementPlusIconsVue from '@element-plus/icons-vue' // 引入所有图标

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册 Element Plus 并配置中文语言
app.use(ElementPlus)

app.mount('#app')
