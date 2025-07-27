<template>
  <div class="user-info-sidebar h-full">
    <!-- 用户头像和基本信息 -->
    <div class="p-6 border-b border-gray-200">
      <div class="flex flex-col items-center">
        <div class="text-center">
          <h3 class="text-lg font-medium text-gray-900">{{ currentUserName }}</h3>
          <p class="text-sm text-gray-500">{{ currentUserRole }}</p>
        </div>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="p-4">
      <div class="space-y-2">
        <!-- 个人信息 -->
        <div 
          @click="selectMenu('personal')"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md cursor-pointer transition-colors"
          :class="activeMenu === 'personal' 
            ? 'bg-blue-50 text-blue-600 border border-blue-200' 
            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'"
        >
          <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
          </svg>
          个人信息
        </div>

        <!-- 偏好设置 (暂时不实现) -->
        <div 
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-400 cursor-not-allowed"
        >
          <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          偏好设置
        </div>

        <!-- 消息订阅 (暂时不实现) -->
        <div 
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-400 cursor-not-allowed"
        >
          <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 7.89a2 2 0 002.83 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
          </svg>
          消息订阅
        </div>

        <!-- 安全日志 (暂时不实现) -->
        <div 
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-400 cursor-not-allowed"
        >
          <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          安全日志
        </div>

        <!-- 退出登录 -->
        <div 
          @click="handleLogout"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md text-red-600 hover:bg-red-50 hover:text-red-700 cursor-pointer"
        >
          <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
          </svg>
          退出登录
        </div>
      </div>
    </nav>

  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
import { userAPI } from '@/api.js'

const router = useRouter()
const userStore = useUserStore()

const props = defineProps({
  activeMenu: {
    type: String,
    default: 'personal'
  }
})

const emit = defineEmits(['menu-change'])

// 当前用户名
const currentUserName = computed(() => {
  if (userStore.userInfo && userStore.userInfo.username) {
    return userStore.userInfo.username
  }
  return '用户名'
})

// 当前用户角色
const currentUserRole = computed(() => {
  // 这里可以根据实际业务逻辑判断用户角色
  return '用户'
})

const selectMenu = (menu) => {
  emit('menu-change', menu)
}

// 退出登录
const handleLogout = async () => {
  if (confirm('确定要退出登录吗？')) {
    try {
      // 获取refresh token
      const refreshToken = localStorage.getItem('refreshToken')
      
      if (refreshToken) {
        // 调用登出API
        await userAPI.logout(refreshToken)
      }
      
      // 清除用户状态
      userStore.logout()
      
      // 跳转到登录页
      router.push('/login')
    } catch (error) {
      console.error('登出失败:', error)
      // 即使API调用失败，也要清除本地状态
      userStore.logout()
      router.push('/login')
    }
  }
}
</script>

<style scoped>
.user-info-sidebar {
  position: relative;
}
</style> 