<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 页面头部 -->
    <div class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Provider管理</h1>
            <p class="text-gray-600 mt-1">管理AI模型提供商和配置</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex gap-6">
        <!-- 左侧菜单 -->
        <div class="w-64 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">管理选项</h3>
          <nav class="space-y-2">
            <button
              v-for="menu in menuItems"
              :key="menu.key"
              @click="selectMenu(menu.key)"
              class="w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors"
              :class="activeMenu === menu.key 
                ? 'bg-blue-50 text-blue-600' 
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
            >
              <span class="mr-3">{{ menu.icon }}</span>
              {{ menu.name }}
            </button>
          </nav>
        </div>

        <!-- 右侧内容区域 -->
        <div class="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <!-- 全局配置 -->
          <div v-if="activeMenu === 'global-config'">
            <GlobalConfigPanel />
          </div>

          <!-- LLM模型 -->
          <div v-else-if="activeMenu === 'llm'">
            <LLMModelPanel />
          </div>

          <!-- 默认显示 -->
          <div v-else class="text-center py-12">
            <div class="text-gray-400 text-lg mb-4">请选择管理选项</div>
            <p class="text-gray-500">从左侧菜单选择要管理的模型类型</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
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

// 选择菜单
const selectMenu = (menuKey) => {
  activeMenu.value = menuKey
}
</script>

<style scoped>
/* 可以添加一些自定义样式 */
</style>
