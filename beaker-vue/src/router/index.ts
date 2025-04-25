import { createRouter, createWebHistory } from 'vue-router'
// import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'notebook',
      component: () => import('../pages/NotebookInterface.vue')
    },
    {
      path: '/notebook',
      name: 'notebook',
      component: () => import('../pages/NotebookInterface.vue')
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../pages/ChatInterface.vue')
    },
    {
      path: '/dev',
      name: 'dev',
      component: () => import('../pages/DevInterface.vue')
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../pages/BeakerAdmin.vue')
    },
  ],
})

export default router
