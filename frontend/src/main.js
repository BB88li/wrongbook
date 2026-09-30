import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as Icons from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册全部 Element Plus 图标（骨架阶段图省事，正式版按需引入）
for (const [name, comp] of Object.entries(Icons)) {
  app.component(name, comp)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')

