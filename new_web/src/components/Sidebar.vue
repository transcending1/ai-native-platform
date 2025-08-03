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

    <!-- 导航菜单 - 使用Element Plus Menu组件 -->
    <div class="mt-4 overflow-y-auto h-full pb-20">
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        :collapse="isCollapsed"
        :collapse-transition="false"
        @open="handleOpen"
        @close="handleClose"
        @select="handleSelect"
        background-color="#ffffff"
        text-color="#374151"
        active-text-color="#3b82f6"
      >
        <!-- 首页 -->
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <!-- 系统管理 - 仅管理员可见 -->
        <el-sub-menu v-if="isAdmin" index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/user-management">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          <el-menu-item index="/provider-management">
            <el-icon><Tools /></el-icon>
            <template #title>Provider管理</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 知识管理 -->
        <el-menu-item index="/knowledge-namespace">
          <el-icon><Document /></el-icon>
          <template #title>知识管理</template>
        </el-menu-item>
      </el-menu>
    </div>

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
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
import appConfig from '@/config/app.js'
import { House, Setting, User, Tools, Document } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 折叠状态
const isCollapsed = ref(appConfig.sidebar.collapsed)

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})

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

// Element Plus Menu 事件处理
const handleOpen = (key, keyPath) => {
  console.log('菜单展开:', key, keyPath)
}

const handleClose = (key, keyPath) => {
  console.log('菜单关闭:', key, keyPath)
}

const handleSelect = (key, keyPath) => {
  console.log('菜单选择:', key, keyPath)
  // 路由跳转
  if (key && key !== route.path) {
    router.push(key)
  }
}

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 跳转到用户信息页面
const goToUserInfo = () => {
  router.push('/user-info')
}

// 暴露折叠状态，供其他组件使用
defineExpose({
  isCollapsed
})
</script>

<style scoped>
.sidebar {
  transition: all 0.3s ease;
}

/* Element Plus Menu 样式定制 */
.el-menu-vertical {
  border-right: none;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 100%;
}

.el-menu--collapse {
  width: 100%;
}

/* 菜单项样式定制 */
:deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 0 8px;
  border-radius: 6px;
}

:deep(.el-menu-item:hover) {
  background-color: #f3f4f6 !important;
}

:deep(.el-menu-item.is-active) {
  background-color: #eff6ff !important;
  color: #3b82f6 !important;
}

/* 子菜单样式定制 */
:deep(.el-sub-menu__title) {
  height: 48px;
  line-height: 48px;
  margin: 0 8px;
  border-radius: 6px;
}

:deep(.el-sub-menu__title:hover) {
  background-color: #f3f4f6 !important;
}

/* 子菜单项样式 */
:deep(.el-menu--inline .el-menu-item) {
  height: 40px;
  line-height: 40px;
  margin: 0 8px 0 16px;
  border-radius: 6px;
}

/* 图标样式 */
:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title .el-icon) {
  margin-right: 8px;
  font-size: 16px;
}

/* 折叠状态下的图标居中 */
:deep(.el-menu--collapse .el-menu-item .el-icon),
:deep(.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0;
  margin-left: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 16px !important;
  width: auto;
  min-width: 16px;
}

/* 折叠状态下的菜单项内容居中 */
:deep(.el-menu--collapse .el-menu-item),
:deep(.el-menu--collapse .el-sub-menu__title) {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 12px !important;
  min-height: 48px;
}

/* 折叠状态下的菜单项文字隐藏 */
:deep(.el-menu--collapse .el-menu-item span),
:deep(.el-menu--collapse .el-sub-menu__title span) {
  display: none;
}
</style> 