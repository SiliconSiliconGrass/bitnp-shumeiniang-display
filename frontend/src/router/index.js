// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import App from '@/App.vue'
import FaceCap from '@/components/temp/FaceCap.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: App
  },
  {
    path: '/test',
    name: 'Test',
    component: FaceCap
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router