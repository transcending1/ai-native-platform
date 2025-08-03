<template>
  <div class="w-full max-w-md mx-auto">
    <!-- Logo和标题 -->
    <div class="text-center mb-8">
      <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
        <div class="text-2xl text-white">💧</div>
      </div>
      <h1 class="text-3xl font-bold text-gray-800">{{ appConfig.appName }}</h1>
    </div>

    <!-- 登录表单 -->
    <form @submit.prevent="handleLogin" class="space-y-4">
      <!-- 账号输入框 -->
      <div>
        <el-input
          v-model="loginForm.username"
          placeholder="账号"
          size="large"
          :prefix-icon="User"
          class="w-full"
        />
      </div>

      <!-- 密码输入框 -->
      <div>
        <el-input
          v-model="loginForm.password"
          type="password"
          placeholder="密码"
          size="large"
          :prefix-icon="Lock"
          show-password
          class="w-full"
        />
      </div>

      <!-- 记住登录和忘记密码 -->
      <div class="flex items-center justify-between text-sm">
        <el-checkbox v-model="loginForm.rememberMe">
          15天内免登录
        </el-checkbox>
      </div>

      <!-- 登录按钮 -->
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        @click="handleLogin"
        class="w-full bg-blue-600 hover:bg-blue-700 border-blue-600 hover:border-blue-700"
      >
        登录
      </el-button>

      <!-- 返回链接 -->
      <div class="text-center">
        <router-link to="/" class="text-gray-600 hover:text-gray-800 text-sm">
          返回
        </router-link>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authAPI } from '@/api'
import appConfig from '@/config/app.js'

const router = useRouter()
const userStore = useUserStore()

// 加载状态
const loading = ref(false)

// 表单数据
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

// 处理登录
const handleLogin = async () => {
  // 简单的表单验证
  if (!loginForm.username.trim()) {
    ElMessage.warning('请输入账号')
    return
  }
  
  if (!loginForm.password.trim()) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  
  try {
    // 调用登录API
    const response = await authAPI.login({
      username: loginForm.username,
      password: loginForm.password,
      remember_me: loginForm.rememberMe
    })
    
    // 处理登录成功的响应
    if (response.data.code === 200) {
      const { data } = response.data
      const { access, refresh, user } = data
      
      // 保存登录状态到store（包含refresh token）
      userStore.login(user, access, refresh, loginForm.rememberMe)
      
      ElMessage.success('登录成功!')
      
      // 跳转到首页
      router.push('/')
    } else {
      ElMessage.error(response.data.message || '登录失败')
    }
    
  } catch (error) {
    console.error('登录错误:', error)
    
    // 处理不同的错误情况
    if (error.response) {
      const { data, status } = error.response
      if (status === 400) {
        if (data.errors && data.errors.non_field_errors) {
          ElMessage.error(data.errors.non_field_errors[0])
        } else {
          ElMessage.error(data.message || '用户名或密码错误')
        }
      } else if (status === 401) {
        ElMessage.error('用户名或密码错误')
      } else if (status === 403) {
        ElMessage.error('账号已被禁用')
      } else {
        ElMessage.error('登录失败，服务器错误')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('登录超时，请检查网络连接')
    } else {
      ElMessage.error('网络连接失败，请检查网络设置')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 自定义样式 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}
</style> 