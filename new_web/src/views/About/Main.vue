<!-- src/views/About.vue -->
<template>
  <div class="container mx-auto">
    <Carousel />
    <div class="flex gap-8 mt-8">
      <div class="flex-1">
        <h2 class="text-xl mb-4">登录</h2>
        <Login />
      </div>
      <div class="flex-1">
        <h2 class="text-xl mb-4">注册</h2>
        <Register />
      </div>
    </div>

    <div class="mt-8">
      <el-button type="success" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
//导入组件的方式必然是从 components 文件夹下导入
import Login from './components/Login.vue'
import Register from './components/Register.vue'
import Carousel from '@/components/carouse.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>
