<template>
  <div class="list-page">
    <h1>文章列表</h1>
    <ul>
      <li v-for="article in articles" :key="article.id">
        <router-link :to="{ name: 'DetailPage', params: { id: article.id } }">
          {{ article.title }}
        </router-link>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Article {
  id: number
  title: string
  content: string
}

const articles = ref<Article[]>([
  { id: 1, title: 'Vue 3 新特性', content: 'Composition API, Teleport, Fragments...' },
  { id: 2, title: 'TypeScript 入门', content: '类型系统、接口、泛型...' },
  { id: 3, title: '前端工程化实践', content: 'Webpack, Vite, Rollup...' }
])
</script>

<style scoped>
.list-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

ul {
  list-style: none;
  padding: 0;
}

li {
  margin: 10px 0;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
}

a {
  text-decoration: none;
  color: #2c3e50;
  font-size: 18px;
}

a:hover {
  color: #42b983;
}
</style>