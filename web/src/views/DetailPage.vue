<template>
  <div class="detail-page" v-if="article">
    <h1>{{ article.title }}</h1>
    <p>{{ article.content }}</p>
    <router-link to="/">返回列表</router-link>
  </div>
  <div v-else>
    <p>加载中...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

interface Article {
  id: number
  title: string
  content: string
}

const route = useRoute()
const article = ref<Article | null>(null)

// 模拟数据源
const mockArticles: Article[] = [
  { id: 1, title: 'Vue 3 新特性', content: 'Composition API, Teleport, Fragments...' },
  { id: 2, title: 'TypeScript 入门', content: '类型系统、接口、泛型...' },
  { id: 3, title: '前端工程化实践', content: 'Webpack, Vite, Rollup...' }
]

onMounted(() => {
  // 模拟异步请求
  setTimeout(() => {
    const id = Number(route.params.id)
    article.value = mockArticles.find(art => art.id === id) || null
  }, 500)
})
</script>

<style scoped>
.detail-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  border: 1px solid #eee;
  border-radius: 8px;
  background-color: #f9f9f9;
}

h1 {
  color: #2c3e50;
  border-bottom: 2px solid #42b983;
  padding-bottom: 10px;
}

p {
  font-size: 16px;
  line-height: 1.6;
  color: #34495e;
}

a {
  display: inline-block;
  margin-top: 20px;
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.3s;
}

a:hover {
  background-color: #349b6f;
}
</style>