// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import Home from '../views/Home/Main.vue'
import Login from '../views/Login/Main.vue'
import UserManagement from "../views/UserManagement/Main.vue"
import UserInfo from "../views/UserInfo/Main.vue"
import KnowledgeNamespace from "../views/KnowledgeNamespace/Main.vue"
import KnowledgeManagement from "../views/KnowledgeManagement/Main.vue"

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: UserManagement,
    meta: { 
      requiresAuth: true,
      breadcrumb: [
        { name: '系统管理', path: '#' },
        { name: '用户管理', path: '/user-management' }
      ]
    }
  },
  {
    path: '/user-info',
    name: 'UserInfo',
    component: UserInfo,
    meta: { 
      requiresAuth: true,
      breadcrumb: [
        { name: '个人中心', path: '/user-info' }
      ]
    }
  },
  {
    path: '/knowledge-namespace',
    name: 'KnowledgeNamespace',
    component: KnowledgeNamespace,
    meta: { 
      requiresAuth: true,
      breadcrumb: [
        { name: '知识管理', path: '/knowledge-namespace' }
      ]
    }
  },
  {
    path: '/knowledge-management/:namespaceId',
    name: 'KnowledgeManagement',
    component: KnowledgeManagement,
    meta: { 
      requiresAuth: true,
      breadcrumb: [
        { name: '知识管理', path: '/knowledge-namespace' },
        { name: '知识库管理', path: '/knowledge-management' }
      ]
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 初始化用户状态（从localStorage恢复）
  userStore.initUserState()
  
  // 如果目标路由需要认证
  if (to.meta.requiresAuth) {
    // 检查是否有token和登录状态
    const token = localStorage.getItem('token')
    
    if (userStore.isLoggedIn && token) {
      next()
    } else {
      // 清除可能存在的无效状态
      userStore.logout()
      console.warn('访问受保护页面但未登录，跳转到登录页')
      next('/login')
    }
  } else {
    // 如果用户已登录且访问登录页，重定向到首页
    if (to.name === 'Login' && userStore.isLoggedIn) {
      next('/')
    } else {
      next()
    }
  }
})

export default router