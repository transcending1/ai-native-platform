<template>
  <div class="container mx-auto p-4">
    <h1 class="text-3xl mb-4">书籍列表</h1>
    <el-table :data="books" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="price" label="价格" width="100" />
      <el-table-column prop="bookstore" label="书店" width="150" />
    </el-table>
    <el-pagination
      class="mt-4 flex justify-center"
      @current-change="handlePageChange"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api.js'

const books = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const fetchBooks = async () => {
  try {
    const response = await apiClient.get('/user/book/', {
      params: {
        page: currentPage.value,
      },
    })
    books.value = response.data.results
    total.value = response.data.count
  } catch (error) {
    console.error('Failed to fetch books:', error)
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchBooks()
}

onMounted(fetchBooks)
</script>