<template>
  <div class="user-management">
    <!-- 页面标题和操作区域 -->
    <div class="bg-white p-6 rounded-lg shadow-sm mb-6">
      <div class="flex justify-between items-center mb-4">
        <h1 class="text-2xl font-bold text-gray-900">用户管理</h1>
        <div class="flex space-x-2">
          <el-button type="primary" icon="Plus" @click="handleAdd">新增</el-button>
          <el-button icon="Download">导出</el-button>
          <el-button icon="Upload">导入</el-button>
          <el-button type="success" icon="Select">全部推送</el-button>
          <el-button icon="Refresh" @click="handleRefresh">刷新</el-button>
          <el-button icon="Setting">设置</el-button>
          <el-button icon="FullScreen">全屏</el-button>
        </div>
      </div>

      <!-- 搜索筛选区域 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <el-input
          v-model="searchForm.name"
          placeholder="请输入用户名"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-input
          v-model="searchForm.email"
          placeholder="请输入邮箱"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select
          v-model="searchForm.status"
          placeholder="请选择状态"
          clearable
        >
          <el-option label="启用" value="active" />
          <el-option label="禁用" value="inactive" />
        </el-select>
        <div class="flex space-x-2">
          <el-button type="primary" @click="handleSearch" icon="Search">搜索</el-button>
          <el-button @click="handleReset" icon="Refresh">重置</el-button>
        </div>
      </div>
    </div>

    <!-- 用户列表表格 -->
    <div class="bg-white rounded-lg shadow-sm">
      <el-table
        :data="userList"
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="avatar" label="头像" width="80">
          <template #default="scope">
            <el-avatar :src="scope.row.avatar" :size="40">
              {{ scope.row.name?.charAt(0) }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="department" label="部门" />
        <el-table-column prop="role" label="角色" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag
              :type="scope.row.status === 'active' ? 'success' : 'danger'"
            >
              {{ scope.row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="handleEdit(scope.row)"
              icon="Edit"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(scope.row)"
              icon="Delete"
            >
              删除
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="handleView(scope.row)"
              icon="View"
            >
              查看
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="handlePush(scope.row)"
              icon="Position"
            >
              推送书籍
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="p-4 flex justify-between items-center">
        <div class="text-sm text-gray-500">
          共 {{ total }} 条
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[15, 30, 50, 100]"
          :total="total"
          layout="sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 响应式数据
const loading = ref(false)
const userList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)
const selectedUsers = ref([])

// 搜索表单
const searchForm = ref({
  name: '',
  email: '',
  status: ''
})

// 模拟用户数据
const mockUserData = [
  {
    id: 1,
    name: '张三',
    email: 'zhangsan@example.com',
    avatar: '',
    department: '技术部',
    role: '开发工程师',
    status: 'active',
    createTime: '2023-01-15 10:30:00'
  },
  {
    id: 2,
    name: '李四',
    email: 'lisi@example.com',
    avatar: '',
    department: '产品部',
    role: '产品经理',
    status: 'active',
    createTime: '2023-02-20 14:15:00'
  },
  {
    id: 3,
    name: '王五',
    email: 'wangwu@example.com',
    avatar: '',
    department: '设计部',
    role: 'UI设计师',
    status: 'inactive',
    createTime: '2023-03-10 09:45:00'
  }
]

// 获取用户列表
const getUserList = async () => {
  loading.value = true
  try {
    // 这里应该调用真实的API
    await new Promise(resolve => setTimeout(resolve, 500)) // 模拟API延迟
    userList.value = mockUserData
    total.value = mockUserData.length
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 处理函数
const handleAdd = () => {
  ElMessage.info('新增用户功能')
}

const handleEdit = (row) => {
  ElMessage.info(`编辑用户: ${row.name}`)
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.name}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    ElMessage.success('删除成功')
  } catch {
    // 用户取消操作
  }
}

const handleView = (row) => {
  ElMessage.info(`查看用户: ${row.name}`)
}

const handlePush = (row) => {
  ElMessage.info(`推送书籍给用户: ${row.name}`)
}

const handleSearch = () => {
  currentPage.value = 1
  getUserList()
}

const handleReset = () => {
  searchForm.value = {
    name: '',
    email: '',
    status: ''
  }
  handleSearch()
}

const handleRefresh = () => {
  getUserList()
}

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const handleSizeChange = (val) => {
  pageSize.value = val
  getUserList()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  getUserList()
}

// 初始化
onMounted(() => {
  getUserList()
})
</script>

<style scoped>
.user-management {
  /* 用户管理页面样式 */
}
</style> 