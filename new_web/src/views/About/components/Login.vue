<template>
    <el-form @submit.prevent="onSubmit" class="space-y-4">
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="username"
          placeholder="请输入用户名"
          class="w-full"
        />
      </el-form-item>
  
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="password"
          type="password"
          placeholder="请输入密码"
          class="w-full"
        />
      </el-form-item>
  
      <el-button type="primary" native-type="submit" class="w-full">
        登录
      </el-button>
    </el-form>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  
  // 定义表单数据
  const username = ref('')
  const password = ref('')
  
  // 表单提交处理
  const onSubmit = () => {
    // 在这里处理登录逻辑
    console.log('用户名:', username.value)
    console.log('密码:', password.value)
  }
  </script>