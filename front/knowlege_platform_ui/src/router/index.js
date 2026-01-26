import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layout/index.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/knowledge',
    children: [
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue'),
        meta: { title: '知识库管理', icon: 'Files' }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue'),
        meta: { title: '智能问答', icon: 'ChatDotRound' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
