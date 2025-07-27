<template>
  <div class="breadcrumb bg-white border-b border-gray-200 px-6 py-3">
    <nav class="flex" aria-label="Breadcrumb">
      <ol class="inline-flex items-center space-x-1 md:space-x-3">
        <li class="inline-flex items-center">
          <router-link 
            to="/" 
            class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-blue-600"
          >
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path>
            </svg>
            首页
          </router-link>
        </li>
        
        <li v-for="(item, index) in breadcrumbItems" :key="index">
          <div class="flex items-center">
            <svg class="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
            </svg>
            <span 
              v-if="index === breadcrumbItems.length - 1"
              class="ml-1 text-sm font-medium text-gray-500 md:ml-2"
            >
              {{ item.name }}
            </span>
            <router-link
              v-else
              :to="item.path"
              class="ml-1 text-sm font-medium text-gray-700 hover:text-blue-600 md:ml-2"
            >
              {{ item.name }}
            </router-link>
          </div>
        </li>
      </ol>
    </nav>

    <!-- 右侧操作区域 -->
    <div class="flex items-center space-x-4 ml-auto">
      <div class="text-sm text-gray-500">
        {{ appConfig.breadcrumb.rightText }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import appConfig from '@/config/app.js'

const route = useRoute()

// 根据当前路由生成面包屑导航
const breadcrumbItems = computed(() => {
  const items = []
  
  // 根据路由路径生成面包屑
  switch (route.path) {
    case '/':
      break // 首页不需要额外的面包屑
    case '/about':
      items.push({ name: '关于', path: '/about' })
      break
    case '/user-management':
      items.push({ name: '系统管理', path: '#' })
      items.push({ name: '用户管理', path: '/user-management' })
      break
    case '/page1':
      items.push({ name: '页面1', path: '/page1' })
      break
    default:
      // 可以根据路由的 meta 信息或者其他逻辑来生成面包屑
      if (route.meta && route.meta.breadcrumb) {
        items.push(...route.meta.breadcrumb)
      }
  }
  
  return items
})
</script>

<style scoped>
.breadcrumb {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style> 