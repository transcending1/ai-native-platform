// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home/Main.vue'
import About from '../views/About/Main.vue'
import Login from '../views/Login/Main.vue'
import Page1 from "../views/Page1/Main.vue"

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/about',
    name: 'About',
    component: About
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/page1',
    name: 'Page1',
    component: Page1
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router