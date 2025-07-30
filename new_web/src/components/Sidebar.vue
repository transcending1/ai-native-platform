<template>
  <div 
    class="sidebar h-screen bg-white shadow-lg border-r border-gray-200 fixed left-0 top-0 transition-all duration-300 ease-in-out"
    :class="isCollapsed ? 'w-16' : 'w-64'"
    style="z-index: 1000;"
  >
    <!-- Logo 区域 -->
    <div class="p-4 border-b border-gray-200">
      <div class="flex items-center">
        <!-- 用户头像区域，点击可跳转 -->
        <div 
          class="w-8 h-8 rounded-full flex items-center justify-center cursor-pointer hover:ring-2 hover:ring-blue-400 transition overflow-hidden"
          :class="isCollapsed ? 'mr-0' : 'mr-3'"
          @click="goToUserInfo"
          :title="'点击进入个人信息'"
        >
          <!-- 如果有头像则显示头像，否则显示默认图标 -->
          <img 
            v-if="currentUserAvatar"
            :src="currentUserAvatar" 
            :alt="currentUserName + '的头像'"
            :key="currentUserAvatar"
            class="w-full h-full object-cover rounded-full"
          />
          <div v-else class="w-full h-full bg-blue-600 rounded-full flex items-center justify-center">
            <span class="text-white text-sm">💧</span>
          </div>
        </div>
        <div v-if="!isCollapsed" class="flex-1">
          <h1 class="text-xl font-bold text-gray-800">{{ appConfig.appName }}</h1>
          <div 
            @click="goToUserInfo"
            class="flex items-center text-xs text-gray-500 mt-1 cursor-pointer hover:text-blue-600 transition-colors"
            :title="'点击进入个人信息'"
          >
            {{ currentUserName }}
          </div>
        </div>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="mt-4 overflow-y-auto h-full pb-20">
      <div class="px-4">
        <!-- 首页 -->
        <router-link 
          to="/"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md hover:bg-gray-100 mb-1"
          :class="{'bg-blue-50 text-blue-600': $route.path === '/', 'justify-center': isCollapsed}"
          :title="isCollapsed ? '首页' : ''"
        >
          <span :class="isCollapsed ? 'mr-0' : 'mr-3'">🏠</span>
          <span v-if="!isCollapsed">首页</span>
        </router-link>

        <!-- 系统管理 - 仅管理员可见 -->
        <div v-if="isAdmin" class="mb-2 relative">
          <div 
            @click.stop="toggleSystemMenu()"
            class="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 cursor-pointer"
            :class="{'justify-center': isCollapsed, 'justify-between': !isCollapsed}"
            :title="isCollapsed ? '系统管理' : ''"
          >
            <div class="flex items-center">
              <span :class="isCollapsed ? 'mr-0' : 'mr-3'">⚙️</span>
              <span v-if="!isCollapsed">系统管理</span>
            </div>
            <span v-if="!isCollapsed" class="text-gray-400" :class="{'transform rotate-180': systemMenuOpen}">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </span>
          </div>
          
          <!-- 展开状态下的子菜单 -->
          <div v-show="systemMenuOpen && !isCollapsed" class="ml-6 mt-1 space-y-1">
            <router-link 
              to="/user-management"
              class="flex items-center px-3 py-2 text-sm text-gray-600 rounded-md hover:bg-blue-50 hover:text-blue-600"
              :class="{'bg-blue-50 text-blue-600': $route.path === '/user-management'}"
            >
              <span class="mr-3">👤</span>
              用户管理
            </router-link>
            
            <div class="flex items-center px-3 py-2 text-sm text-gray-600 rounded-md hover:bg-blue-50 hover:text-blue-600">
              <span class="mr-3">👥</span>
              部门管理
            </div>
            
          </div>

          <!-- 折叠状态下的浮动子菜单 -->
          <div 
            v-show="systemMenuOpen && isCollapsed" 
            class="absolute left-16 top-0 bg-white shadow-xl border border-gray-200 rounded-md py-2 min-w-48"
            style="z-index: 9999;"
            @click.stop
          >
            <router-link 
              to="/user-management"
              class="flex items-center px-4 py-2 text-sm text-gray-600 hover:bg-blue-50 hover:text-blue-600"
              :class="{'bg-blue-50 text-blue-600': $route.path === '/user-management'}"
            >
              <span class="mr-3">👤</span>
              用户管理
            </router-link>
            
            <div class="flex items-center px-4 py-2 text-sm text-gray-600 hover:bg-blue-50 hover:text-blue-600 cursor-pointer">
              <span class="mr-3">👥</span>
              部门管理
            </div>
            
          </div>
        </div>

        <!-- 知识管理 -->
        <router-link 
          to="/knowledge-namespace"
          class="flex items-center px-3 py-2 text-sm font-medium rounded-md hover:bg-gray-100 mb-1"
          :class="{'bg-blue-50 text-blue-600': $route.path.startsWith('/knowledge'), 'justify-center': isCollapsed}"
          :title="isCollapsed ? '知识管理' : ''"
        >
          <span :class="isCollapsed ? 'mr-0' : 'mr-3'">📚</span>
          <span v-if="!isCollapsed">知识管理</span>
        </router-link>

      </div>
    </nav>

    <!-- 底部折叠按钮 -->
    <div class="absolute bottom-4 left-4">
      <button 
        @click="toggleCollapse"
        class="p-2 rounded-md hover:bg-gray-100 text-gray-600"
        :title="isCollapsed ? '展开侧边栏' : '折叠侧边栏'"
      >
        <svg 
          class="w-4 h-4 transition-transform duration-300" 
          :class="{'rotate-180': isCollapsed}"
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"></path>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
import appConfig from '@/config/app.js'

const router = useRouter()
const userStore = useUserStore()
const systemMenuOpen = ref(true) // 默认展开系统管理
const permissionMenuOpen = ref(false)

// 折叠状态
const isCollapsed = ref(appConfig.sidebar.collapsed)

// 当前用户名
const currentUserName = computed(() => {
  if (userStore.userInfo && userStore.userInfo.username) {
    return userStore.userInfo.username
  }
  return '用户名'
})

// 当前用户头像（添加时间戳确保缓存刷新）
const currentUserAvatar = computed(() => {
  if (userStore.userInfo && userStore.userInfo.avatar) {
    const avatar = userStore.userInfo.avatar
    // 如果已经有时间戳参数，直接返回；否则添加时间戳
    if (avatar.includes('?t=') || avatar.includes('&t=')) {
      return avatar
    }
    return avatar + (avatar.includes('?') ? '&' : '?') + 't=' + Date.now()
  }
  return null
})

// 检查当前用户是否为管理员
const isAdmin = computed(() => {
  return userStore.userInfo && (userStore.userInfo.role === 'admin' || userStore.userInfo.role === 'administrator')
})

const toggleSystemMenu = () => {
  systemMenuOpen.value = !systemMenuOpen.value
  // 在折叠状态下，如果打开了系统菜单，则关闭其他菜单
  if (isCollapsed.value && systemMenuOpen.value) {
    permissionMenuOpen.value = false
  }
}


const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  // 当展开侧边栏时，恢复系统管理的默认展开状态
  if (!isCollapsed.value) {
    systemMenuOpen.value = true
    permissionMenuOpen.value = false
  }
}

// 跳转到用户信息页面
const goToUserInfo = () => {
  router.push('/user-info')
}

// 点击外部区域关闭浮动菜单
const handleClickOutside = (event) => {
  // 如果不是折叠状态，不需要处理
  if (!isCollapsed.value) return
  
  // 检查点击是否在侧边栏内或浮动菜单内
  const sidebar = event.target.closest('.sidebar')
  const floatingMenu = event.target.closest('[style*="z-index: 9999"]')
  
  if (!sidebar && !floatingMenu) {
    systemMenuOpen.value = false
    permissionMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 暴露折叠状态，供其他组件使用
defineExpose({
  isCollapsed
})
</script>

<style scoped>
.sidebar {
  transition: all 0.3s ease;
}
</style> 