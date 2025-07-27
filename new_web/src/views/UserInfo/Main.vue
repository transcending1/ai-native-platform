<template>
  <div class="user-info-container flex h-screen bg-gray-50">
    <!-- 左侧导航栏 -->
    <div class="w-64 bg-white shadow-lg border-r border-gray-200">
      <UserInfoSidebar 
        :active-menu="activeMenu" 
        @menu-change="handleMenuChange"
      />
    </div>

    <!-- 右侧内容区域 -->
    <div class="flex-1 flex flex-col">
      <!-- 返回按钮 -->
      <div class="p-4 bg-white border-b border-gray-200">
        <button 
          @click="goBack"
          class="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
          </svg>
          返回
        </button>
      </div>

      <!-- 主要内容区域 -->
      <div class="flex-1 p-6 overflow-y-auto">
        <div class="max-w-4xl mx-auto">


          <!-- 个人信息编辑组件 -->
          <PersonalInfoEdit v-if="activeMenu === 'personal'" />
          
          <!-- 其他菜单的占位符 -->
          <div v-else class="text-center py-12">
            <div class="text-gray-400 text-lg">{{ activeMenu }} 功能开发中...</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import UserInfoSidebar from './components/UserInfoSidebar.vue'
import PersonalInfoEdit from './components/PersonalInfoEdit.vue'

const router = useRouter()
const activeMenu = ref('personal') // 默认显示个人信息

const handleMenuChange = (menu) => {
  activeMenu.value = menu
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.user-info-container {
  min-height: 100vh;
}
</style> 