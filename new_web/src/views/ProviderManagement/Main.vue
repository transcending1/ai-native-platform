<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 页面头部 -->
    <div class="bg-white shadow-sm border-b border-gray-200">
      <div class="px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16">
        <div class="flex justify-between items-center py-4">
          <div>
            <h1 class="text-xl sm:text-2xl font-bold text-gray-900">Provider管理</h1>
            <p class="text-gray-600 mt-1 text-sm sm:text-base">管理AI模型提供商和配置</p>
          </div>
          <!-- 移动端菜单按钮 -->
          <button
            @click="toggleMobileMenu"
            class="lg:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          >
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4 sm:py-6 lg:py-8">
      <div class="flex flex-col lg:flex-row gap-4 lg:gap-6">
        
        <!-- 移动端侧边栏遮罩 -->
        <div
          v-if="isMobileMenuOpen"
          class="fixed inset-0 z-40 lg:hidden"
          @click="closeMobileMenu"
        >
          <div class="absolute inset-0 bg-black bg-opacity-50"></div>
        </div>

        <!-- 左侧菜单 -->
        <div 
          :class="[
            'bg-white rounded-lg shadow-sm border border-gray-200',
            // 移动端样式
            'fixed lg:static inset-y-0 left-0 z-50 w-64 lg:w-64 xl:w-72 2xl:w-80',
            'transform lg:transform-none transition-transform duration-300 ease-in-out',
            isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
            // 桌面端样式
            'lg:flex-shrink-0'
          ]"
        >
          <!-- 移动端关闭按钮 -->
          <div class="flex justify-between items-center p-4 border-b border-gray-200 lg:hidden">
            <h3 class="text-lg font-semibold text-gray-900">管理选项</h3>
            <button
              @click="closeMobileMenu"
              class="p-2 rounded-md text-gray-400 hover:text-gray-600"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- 菜单内容 -->
          <div class="p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-4 hidden lg:block">管理选项</h3>
            <nav class="space-y-2">
              <button
                v-for="menu in menuItems"
                :key="menu.key"
                @click="selectMenu(menu.key)"
                class="w-full flex items-center px-3 py-3 lg:py-2 text-sm font-medium rounded-md transition-colors"
                :class="activeMenu === menu.key 
                  ? 'bg-blue-50 text-blue-600' 
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
              >
                <span class="mr-3 text-base lg:text-sm">{{ menu.icon }}</span>
                <span class="text-base lg:text-sm">{{ menu.name }}</span>
              </button>
            </nav>
          </div>
        </div>

        <!-- 右侧内容区域 -->
        <div class="flex-1 min-w-0 bg-white rounded-lg shadow-sm border border-gray-200">
          <div class="p-4 sm:p-6 lg:p-8">
            <!-- 全局配置 -->
            <div v-if="activeMenu === 'global-config'">
              <div class="mb-6">
                <h2 class="text-lg sm:text-xl font-semibold text-gray-900 mb-2">全局配置</h2>
                <p class="text-gray-600 text-sm sm:text-base">配置全局Provider参数</p>
              </div>
              <GlobalConfigPanel />
            </div>

            <!-- LLM模型 -->
            <div v-else-if="activeMenu === 'llm'">
              <div class="mb-6">
                <h2 class="text-lg sm:text-xl font-semibold text-gray-900 mb-2">LLM 编码模型</h2>
                <p class="text-gray-600 text-sm sm:text-base">配置全部LLM编码参数</p>
              </div>
              <LLMModelPanel />
            </div>

            <!-- 默认显示 -->
            <div v-else class="text-center py-12 lg:py-20">
              <div class="text-gray-400 text-lg sm:text-xl mb-4">请选择管理选项</div>
              <p class="text-gray-500 text-sm sm:text-base">从左侧菜单选择要管理的模型类型</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import GlobalConfigPanel from './components/GlobalConfigPanel.vue'
import LLMModelPanel from './components/LLMModelPanel.vue'

// 菜单项配置
const menuItems = [
  {
    key: 'global-config',
    name: '全局配置',
    icon: '⚙️'
  },
  {
    key: 'llm',
    name: 'LLM模型',
    icon: '🤖'
  }
]

// 当前激活的菜单
const activeMenu = ref('global-config')

// 移动端菜单状态
const isMobileMenuOpen = ref(false)

// 选择菜单
const selectMenu = (menuKey) => {
  activeMenu.value = menuKey
  // 移动端选择菜单后自动关闭侧边栏
  if (window.innerWidth < 1024) {
    closeMobileMenu()
  }
}

// 切换移动端菜单
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

// 关闭移动端菜单
const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

// 监听窗口大小变化，桌面端自动关闭移动菜单
const handleResize = () => {
  if (window.innerWidth >= 1024) {
    isMobileMenuOpen.value = false
  }
}

// 监听ESC键关闭移动端菜单
const handleEscKey = (event) => {
  if (event.key === 'Escape') {
    closeMobileMenu()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleEscKey)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleEscKey)
})
</script>

<style scoped>
/* 可以添加一些自定义样式 */
</style>
