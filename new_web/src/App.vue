<!-- src/App.vue -->
<template>
  <Header />
  <div id="app">
    <el-main class="p-4">
      <router-view />
    </el-main>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from './components/header.vue'

const route = useRoute()
const router = useRouter()
const activeMenu = ref(route.path)

watch(
  () => route.path,
  (newPath) => {
    activeMenu.value = newPath
  }
)

const handleSelect = (key) => {
  router.push(key)
}
</script>
