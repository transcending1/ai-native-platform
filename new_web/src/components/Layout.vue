<template>
  <div class="app-layout flex h-screen">
    <!-- 侧边栏 -->
    <Sidebar ref="sidebarRef" />
    
    <!-- 主内容区域 -->
    <div 
      class="main-content flex-1 flex flex-col transition-all duration-300 ease-in-out"
      :style="{ marginLeft: sidebarRef?.isCollapsed ? '64px' : '256px' }"
    >
      <!-- 面包屑导航 -->
      <Breadcrumb />
      
      <!-- 页面内容 -->
      <main class="flex-1 overflow-auto bg-gray-50 p-6">
        <router-view />
      </main>
      
      <!-- 底部 -->
      <Footer />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import Breadcrumb from './Breadcrumb.vue'
import Footer from './Footer.vue'

const sidebarRef = ref(null)
</script>

<style scoped>
.app-layout {
  background-color: #f8fafc;
}

.main-content {
  min-height: 100vh;
}
</style> 