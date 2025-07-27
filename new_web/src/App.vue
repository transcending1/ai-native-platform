<!-- src/App.vue -->
<template>
  <div id="app">
    <!-- 登录页面不使用布局 -->
    <router-view v-if="$route.name === 'Login'" />
    
    <!-- 其他页面使用统一布局 -->
    <Layout v-else>
      <router-view />
    </Layout>
  </div>
</template>

<script setup>
// 应用入口组件
import Layout from './components/Layout.vue'
</script>

<style>
/* 全局样式可以在这里定义 */
#app {
  min-height: 100vh;
}
</style>
