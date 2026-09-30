import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/mistakes' },
  { path: '/mistakes', name: 'mistakes', component: () => import('../views/MistakeList.vue'), meta: { title: '错题列表' } },
  { path: '/mistakes/new', name: 'mistake-new', component: () => import('../views/MistakeCreate.vue'), meta: { title: '录入错题' } },
  { path: '/review', name: 'review', component: () => import('../views/Review.vue'), meta: { title: '今日复习' } },
  { path: '/report', name: 'report', component: () => import('../views/Report.vue'), meta: { title: '学习报告' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
