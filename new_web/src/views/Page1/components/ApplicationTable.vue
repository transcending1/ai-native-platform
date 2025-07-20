<template>
  <div class="container mx-auto p-4">
    <h1 class="text-3xl mb-4">书籍管理</h1>
    <el-table :data="books" class="w-full" style="margin-bottom: 20px;">
      <el-table-column prop="title" label="书名" width="200"></el-table-column>
      <el-table-column prop="price" label="价格" width="100"></el-table-column>
      <el-table-column prop="bookstore" label="书店" width="150"></el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button type="link" size="small">查看</el-button>
          <el-button type="link" size="small">编辑</el-button>
          <el-button type="link" size="small" @click="deleteBook(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      @current-change="fetchBooks"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      class="flex justify-center"
    ></el-pagination>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api.js'
import { ElMessage } from 'element-plus'

const books = ref([])
const currentPage = ref(1)
const pageSize = 10
const total = ref(0)

const fetchBooks = async (page = 1) => {
  try {
    const response = await apiClient.get('/user/book/', {
      params: { page, page_size: pageSize }
    })
    books.value = response.data.results
    total.value = response.data.count
    currentPage.value = page
  } catch (error) {
    ElMessage.error('获取书籍列表失败')
    console.error(error)
  }
}

const deleteBook = async (id) => {
  try {
    await apiClient.delete(`/user/book/${id}/`)
    ElMessage.success('删除成功')
    fetchBooks(currentPage.value)
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

onMounted(() => {
  fetchBooks()
})
</script>