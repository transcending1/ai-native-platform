<template>
  <div class="user-info">
    <div v-if="userStore.isLoggedIn" class="flex items-center space-x-4">
      <!-- 用户头像 -->
      <div class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
        <span class="text-white font-medium">
          {{ userStore.userInfo?.nickname?.charAt(0) || 'U' }}
        </span>
      </div>
      
      <!-- 用户信息 -->
      <div class="flex-1">
        <div class="text-sm font-medium text-gray-900">
          {{ userStore.userInfo?.nickname || userStore.userInfo?.username }}
        </div>
        <div class="text-xs text-gray-500">
          {{ userStore.userInfo?.email }}
        </div>
      </div>
      
      <!-- 下拉菜单 -->
      <el-dropdown @command="handleCommand">
        <el-button type="text" class="p-0">
          <el-icon><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人资料</el-dropdown-item>
            <el-dropdown-item command="settings">设置</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
    
    <!-- 未登录状态 -->
    <div v-else>
      <el-button type="primary" @click="$router.push('/login')">
        登录
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()

// 处理下拉菜单命令
const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人资料功能开发中...')
      break
    case 'settings':
      ElMessage.info('设置功能开发中...')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 处理退出登录
const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.user-info {
  min-width: 200px;
}
</style> 