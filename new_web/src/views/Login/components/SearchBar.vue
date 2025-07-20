<template>
  <div class="container mx-auto p-4">
    <h1 class="text-3xl mb-6">关键字查询</h1>
    
    <div class="flex mb-4">
      <el-input v-model="keyword" placeholder="请输入关键字" class="w-64 mr-4"></el-input>
      <el-button type="primary" @click="search">查询</el-button>
    </div>
    
    <div v-if="results.length" class="mt-4">
      <el-table :data="results" style="width: 100%">
        <el-table-column prop="id" label="ID" width="50"></el-table-column>
        <el-table-column prop="name" label="名称"></el-table-column>
        <el-table-column prop="description" label="描述"></el-table-column>
      </el-table>
    </div>
    <div v-else class="mt-4 text-gray-500">暂无数据</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const keyword = ref('')
const results = ref([])

const mockData = [
  { id: 1, name: '示例1', description: '这是第一个示例' },
  { id: 2, name: '示例2', description: '这是第二个示例' },
  { id: 3, name: '测试', description: '用于测试的示例' },
  { id: 4, name: '示例3', description: '这是第三个示例' },
  { id: 5, name: '示例4', description: '这是第四个示例' }
]

const search = () => {
  if (keyword.value.trim() === '') {
    results.value = []
  } else {
    results.value = mockData.filter(item => item.name.includes(keyword.value))
    // 如果没有找到匹配项，展示一些测试数据
    if (results.value.length === 0) {
      results.value = mockData.slice(0, 2) // 展示前两个示例作为测试数据
    }
  }
}
</script>