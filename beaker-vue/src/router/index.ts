import { createRouter, createWebHistory } from 'vue-router'

export interface Route {
    name: string;
    path: string;
    component: any;
}

export type Routes = { [key: string]: Route }

const routeMap: Routes = {
    "/": {
      "path": "/",
      "name": "home",
      "component": () => import('../pages/NotebookInterface.vue')
    },
    "/notebook": {
      "path": "/notebook",
      "name": "notebook",
      "component": () => import('../pages/NotebookInterface.vue')
    },
    "/chat": {
      "path": "/chat",
      "name": "chat",
      "component": () => import('../pages/ChatInterface.vue')
    },
    "/dev": {
      "path": "/dev",
      "name": "dev",
      "component": () => import('../pages/DevInterface.vue')
    },
    "/admin": {
      "path": "/admin",
      "name": "admin",
      "component": () => import('../pages/BeakerAdmin.vue')
    }
}

const routes = Object.values(routeMap);

const router = createRouter({
  history: createWebHistory(import.meta.env?.BASE_URL),
  routes,
});

export default router;
