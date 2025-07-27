<!-- src/views/Home.vue -->
<template>
  <div class="home-page">
    <!-- 顶部用户信息和登出 -->
    <div class="bg-white p-4 rounded-lg shadow-sm mb-6">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-900">仪表板</h2>
        <div class="flex items-center space-x-4">
          <div class="text-sm text-gray-700">
            欢迎回来，{{ userStore.userInfo?.username || '用户' }}
          </div>
          <el-button 
            type="danger" 
            size="small"
            @click="handleLogout"
            :loading="logoutLoading"
          >
            登出
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="bg-white overflow-hidden shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <!-- 用户信息卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <div class="bg-blue-50 rounded-lg p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span class="text-white text-sm">👤</span>
                </div>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">用户ID</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ userStore.userInfo?.id || '-' }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-green-50 rounded-lg p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                  <span class="text-white text-sm">📧</span>
                </div>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">邮箱</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ userStore.userInfo?.email || '-' }}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div class="bg-purple-50 rounded-lg p-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                  <span class="text-white text-sm">🔑</span>
                </div>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">登录状态</dt>
                  <dd class="text-lg font-medium text-gray-900">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      已登录
                    </span>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <!-- Token过期测试区域 -->
        <div class="mt-8 p-6 bg-yellow-50 rounded-lg border border-yellow-200">
          <h3 class="text-lg font-medium text-yellow-800 mb-4">🔧 Token过期测试工具</h3>
          <p class="text-sm text-yellow-700 mb-4">
            这个功能用于测试JWT Token过期的处理机制。点击下面的按钮会模拟token过期的情况。
          </p>
          <div class="flex space-x-4">
            <el-button 
              type="warning" 
              size="small"
              @click="simulateTokenExpiry"
            >
              模拟Token过期
            </el-button>
            <el-button 
              type="info" 
              size="small"
              @click="testProtectedAPI"
              :loading="apiTestLoading"
            >
              测试受保护API
            </el-button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { userAPI } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const input = ref('')
const logoutLoading = ref(false)
const apiTestLoading = ref(false)

const handleClick = () => {
  input.value = '按钮已点击！'
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    logoutLoading.value = true
    
    // 执行登出操作
    userStore.logout()
    
    ElMessage.success('已成功登出')
    
    // 跳转到登录页
    router.push('/login')
    
  } catch {
    // 用户取消操作
  } finally {
    logoutLoading.value = false
  }
}

// 模拟Token过期的测试功能
const simulateTokenExpiry = () => {
  ElMessageBox.confirm(
    '这将清除当前的Token来模拟token过期，你将会被自动登出。确定继续吗？',
    '模拟Token过期',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // 手动清除token模拟过期
    localStorage.removeItem('token')
    ElMessage.info('Token已清除，现在尝试访问任何API都会触发过期处理')
  }).catch(() => {
    // 用户取消
  })
}

// 测试受保护的API来验证401处理
const testProtectedAPI = async () => {
  apiTestLoading.value = true
  
  try {
    const response = await userAPI.getProfile()
    ElMessage.success('API调用成功，Token仍然有效')
    console.log('用户信息:', response.data)
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.warning('检测到401错误，Token过期处理机制将自动触发')
    } else {
      ElMessage.error('API调用失败: ' + (error.message || '未知错误'))
    }
    console.error('API测试错误:', error)
  } finally {
    apiTestLoading.value = false
  }
}

// 检查登录状态
onMounted(() => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
  }
})
</script>

