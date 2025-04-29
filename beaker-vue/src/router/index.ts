import { createRouter, createWebHistory } from 'vue-router'

const routesMap = {
    "/": {
      "path": "/",
      "name": "home",
      "component": () => import("@/pages/NotebookInterface.vue")
    },
    "/notebook": {
      "path": "/notebook",
      "name": "notebook",
      "component": () => import("@/pages/NotebookInterface.vue")
    },
    "/chat": {
      "path": "/chat",
      "name": "chat",
      "component": () => import("@/pages/ChatInterface.vue")
    },
    "/dev": {
      "path": "/dev",
      "name": "dev",
      "component": () => import("@/pages/DevInterface.vue")
    },
    "/admin": {
      "path": "/admin",
      "name": "admin",
      "component": () => import("@/pages/BeakerAdmin.vue")
    }
}
const routes = Object.values(routesMap);

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
