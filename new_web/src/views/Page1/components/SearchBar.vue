<template>
  <div class="container mx-auto p-4">
    <h1 class="text-3xl mb-4">关键词查询</h1>
    <div class="flex mb-4">
      <el-input v-model="keyword" placeholder="请输入关键字" class="w-64"></el-input>
      <el-button type="primary" class="ml-2" @click="search">查询</el-button>
    </div>
    <el-table :data="filteredData" style="width: 100%">
      <el-table-column prop="id" label="ID" width="50"></el-table-column>
      <el-table-column prop="name" label="名称"></el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const keyword = ref('')

const data = ref([
  { id: 1, name: '苹果' },
  { id: 2, name: '香蕉' },
  { id: 3, name: '橘子' },
  { id: 4, name: '梨子' }
])

const filteredData = computed(() => {
  if (!keyword.value) return data.value
  return data.value.filter(item => item.name.includes(keyword.value))
})

const search = () => {
  // 搜索功能由计算属性处理
}
</script>