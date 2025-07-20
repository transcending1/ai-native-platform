<template>
  <div class="p-4">
    <el-table :data="books" stripe class="w-full mb-4">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="书名" />
      <el-table-column prop="price" label="价格" />
      <el-table-column prop="bookstore" label="书店" />
      <el-table-column label="操作" width="120" class="text-right">
        <template #default="{ row }">
          <el-popover
            placement="top"
            width="160"
            trigger="click"
          >
            <p>确定删除书籍 "<strong>{{ row.title }}</strong>" 吗？</p>
            <div style="text-align: right; margin: 0">
              <el-button size="mini" type="text" @click="popoverVisible[row.id] = false">取消</el-button>
              <el-button type="primary" size="mini" @click="deleteBook(row)">确定</el-button>
            </div>
            <el-button type="danger" size="mini" slot="reference">删除</el-button>
          </el-popover>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      @current-change="fetchBooks"
      :current-page="page"
      :page-size="pageSize"
      layout="prev, pager, next"
      :total="total"
      class="flex justify-center mt-4"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import apiClient from '@/api.js';
import { ElMessage } from 'element-plus';

const books = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const popoverVisible = ref({});

const fetchBooks = async (currentPage = page.value) => {
  try {
    const response = await apiClient.get('/user/book/', {
      params: {
        page: currentPage,
        page_size: pageSize.value,
      },
    });
    books.value = response.data.results;
    total.value = response.data.count;
    page.value = currentPage;
  } catch (error) {
    ElMessage.error('获取书籍失败。');
  }
};

const deleteBook = async (book) => {
  try {
    await apiClient.delete(`/user/book/${book.id}/`);
    ElMessage.success('书籍删除成功。');
    fetchBooks(page.value);
  } catch (error) {
    ElMessage.error('删除书籍失败。');
  }
};

onMounted(() => {
  fetchBooks();
});
</script>