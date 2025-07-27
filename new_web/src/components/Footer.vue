<template>
  <footer class="bg-white border-t border-gray-200 py-4 px-6">
    <div class="text-center text-sm text-gray-500">
      {{ footerText }}
    </div>
  </footer>
</template>

<script setup>
import { ref } from 'vue'
import appConfig from '@/config/app.js'

// 从配置文件中读取底部文字
const footerText = ref(appConfig.footerText)
</script>

<style scoped>
/* 底部样式 */
</style> 