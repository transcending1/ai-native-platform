<!-- src/views/Home.vue -->
<template>
  <div class="container mx-auto">
    <h1 class="text-3xl mb-4">首页</h1>

    <div class="mb-4">
      <el-input v-model="input" placeholder="请输入内容" class="w-64"></el-input>
    </div>

    <div class="mb-4">
      <el-button type="primary" @click="handleClick">点击我</el-button>
    </div>

    <p class="text-lg">输入内容: {{ input }}</p>

    <div class="mt-6">
      <el-card class="w-96">
        <h3 slot="header">Element Plus 卡片</h3>
        <p>这是一个使用 Element Plus 的卡片组件。</p>
      </el-card>
    </div>

    <div class="mt-6">
      <router-link to="/about" class="text-blue-500 underline">前往关于我们页面</router-link>
      <br>
      <router-link to="/login" class="text-blue-500 underline">前往login页面</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const input = ref('')

const handleClick = () => {
  input.value = '按钮已点击！'
}
</script>

