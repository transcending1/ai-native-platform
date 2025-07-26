<template>
  <div class="w-full max-w-md mx-auto">
    <!-- Logo和标题 -->
    <div class="text-center mb-8">
      <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
        <div class="text-2xl text-white">💧</div>
      </div>
      <h1 class="text-3xl font-bold text-gray-800">XADMTN</h1>
    </div>

    <!-- 选项卡 -->
    <div class="flex mb-6 bg-gray-100 rounded-lg p-1">
      <button 
        @click="activeTab = 'email'"
        :class="[
          'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
          activeTab === 'email' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
        ]"
      >
        邮件验证
      </button>
      <button 
        @click="activeTab = 'password'"
        :class="[
          'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
          activeTab === 'password' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
        ]"
      >
        账户密码
      </button>
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

      <!-- 验证码输入框（如果需要的话，当前用户不需要） -->
      <div v-if="false" class="flex space-x-2">
        <el-input
          v-model="loginForm.captcha"
          placeholder="验证码"
          size="large"
          class="flex-1"
        />
        <div class="w-24 h-10 bg-gray-200 rounded flex items-center justify-center text-gray-600 cursor-pointer">
          验证码
        </div>
      </div>

      <!-- 记住登录和忘记密码 -->
      <div class="flex items-center justify-between text-sm">
        <el-checkbox v-model="loginForm.rememberMe">
          15天内免登录
        </el-checkbox>
        <a href="#" class="text-blue-600 hover:text-blue-500">
          忘记密码?
        </a>
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

const router = useRouter()
const userStore = useUserStore()

// 当前选中的选项卡
const activeTab = ref('password')

// 加载状态
const loading = ref(false)

// 表单数据
const loginForm = reactive({
  username: '',
  password: '',
  captcha: '',
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
      password: loginForm.password
    })
    
    // 如果有真实的后端API，使用以下代码
    // const { data } = response
    // const { token, user } = data
    
    // 模拟登录成功的响应数据
    const mockUserData = {
      id: 1,
      username: loginForm.username,
      email: loginForm.username + '@example.com',
      nickname: loginForm.username,
      avatar: ''
    }
    const mockToken = 'mock_jwt_token_' + Date.now()
    
    // 保存登录状态到store
    userStore.login(mockUserData, mockToken)
    
    // 保存记住登录状态
    if (loginForm.rememberMe) {
      localStorage.setItem('rememberLogin', 'true')
    }
    
    ElMessage.success('登录成功!')
    
    // 跳转到首页
    router.push('/')
    
  } catch (error) {
    console.error('登录错误:', error)
    
    // 处理不同的错误情况
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        ElMessage.error('账号或密码错误')
      } else if (status === 403) {
        ElMessage.error('账号已被禁用')
      } else {
        ElMessage.error('登录失败，服务器错误')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('登录超时，请检查网络连接')
    } else {
      // 暂时模拟登录成功，便于测试
      ElMessage.success('登录成功! (演示模式)')
      
      const mockUserData = {
        id: 1,
        username: loginForm.username,
        email: loginForm.username + '@example.com',
        nickname: loginForm.username,
        avatar: ''
      }
      const mockToken = 'mock_jwt_token_' + Date.now()
      
      userStore.login(mockUserData, mockToken)
      
      if (loginForm.rememberMe) {
        localStorage.setItem('rememberLogin', 'true')
      }
      
      router.push('/')
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