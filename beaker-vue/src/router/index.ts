import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router';

const leftPanel = () => import('../pages/notebook/Left.vue');
const rightPanel = () => import('../pages/notebook/Right.vue');

const routeMap: RouteRecordRaw[] = [
  {
    path: '',
    name: 'home',
    component: () => import('../pages/BaseRouteInterface.vue'),
    children: [
      {
        path: '/notebook',
        name: 'notebook',
        components: {
          centerPanel: () => import('../pages/notebook/Main.vue'),
          leftPanel,
          rightPanel,
        }
      },
      {
        path: '/chat',
        name: 'chat',
        components: {
          centerPanel: () => import('../pages/ChatInterface.vue'),
          leftPanel,
          rightPanel,
        }
      },
      {
        path: '/dev',
        name: 'dev',
        component: () => import('../pages/DevInterface.vue')
      },
      {
        path: '/integrations',
        name: 'integrations',
        component: () => import('../pages/IntegrationsInterface.vue')
      }
    ]
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../pages/BeakerAdmin.vue')
  },
];

const routes = Object.values(routeMap);

const router = createRouter({
  history: createWebHistory(import.meta.env?.BASE_URL),
  routes,
});

export default router;
