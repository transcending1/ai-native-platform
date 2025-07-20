<template>
  <div class="home-view">
    <header class="app-header">
      <h1>项目开发</h1>
      <div class="user-info">
        <span>欢迎，{{ username }}</span>
        <el-button type="text" @click="logout">退出</el-button>
      </div>
    </header>

    <div class="main-content">
      <!-- 筛选和搜索区域 -->
      <div class="filter-section">
        <div class="filter-controls">
          <el-select v-model="filterType" placeholder="全部" class="filter-select">
          </el-select>
          
          <el-select v-model="filterUser" placeholder="所有人" class="filter-select">
          </el-select>
          
          <el-select v-model="filterStatus" placeholder="全部" class="filter-select">
          </el-select>
        </div>
        
        <div class="search-section">
          <el-input
            v-model="searchQuery"
            placeholder="搜索项目"
            class="search-input"
            prefix-icon="el-icon-search"
            clearable
          ></el-input>
          <el-button type="primary" @click="createNamespace" class="create-btn">
            <i class="el-icon-plus"></i> 创建
          </el-button>
        </div>
      </div>

      <!-- 项目卡片网格 -->
      <div class="projects-grid">
        <div
          v-for="ns in filteredNamespaces"
          :key="ns.id"
          class="project-card"
          @click="selectNamespace(ns)"
        >
          <div class="card-header">
            <div class="project-title">
              <span class="title-text">{{ ns.name }}</span>
              <i class="el-icon-check status-icon" v-if="ns.status === 'active'"></i>
            </div>
            <div class="project-subtitle">{{ ns.description || '项目描述' }}</div>
          </div>
          
          <div class="card-content">
            <div class="project-image">
              <img :src="ns.imageUrl || '/placeholder-image.svg'" alt="项目图片" />
            </div>
            <div class="project-tag">
              <el-tag size="small" type="info">{{ ns.type || '智能体' }}</el-tag>
            </div>
          </div>
          
          <div class="card-footer">
            <div class="last-edited">
              {{ ns.lastEditor || '管理员' }}·最近编辑 {{ formatDate(ns.updatedAt || ns.createdAt) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑命名空间对话框 -->
    <el-dialog
      :title="editMode ? '编辑项目' : '新建项目'"
      v-model="dialogVisible"
      width="40%"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="项目名称" required>
          <el-input v-model="formData.name" placeholder="请输入项目名称"></el-input>
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            rows="3"
            placeholder="请输入项目描述"
          ></el-input>
        </el-form-item>
        <el-form-item label="项目类型">
          <el-select v-model="formData.type" placeholder="请选择项目类型">
            <el-option label="应用" value="app"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="项目图片">
          <el-input v-model="formData.imageUrl" placeholder="图片URL（可选）"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitNamespace">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { namespaceApi } from '../api/index'

const router = useRouter()
const namespaces = ref<any[]>([])
const username = ref('管理员')

// 筛选和搜索状态
const filterType = ref('all')
const filterUser = ref('all')
const filterStatus = ref('all')
const searchQuery = ref('')

// 对话框状态
const dialogVisible = ref(false)
const editMode = ref(false)
const currentEditingId = ref<number | null>(null)
const formData = ref({
  name: '',
  description: '',
  type: '知识',
  imageUrl: ''
})

// 计算筛选后的命名空间
const filteredNamespaces = computed(() => {
  let filtered = namespaces.value

  // 搜索过滤
  if (searchQuery.value) {
    filtered = filtered.filter(ns => 
      ns.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (ns.description && ns.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
    )
  }

  // 类型过滤
  if (filterType.value !== 'all') {
    filtered = filtered.filter(ns => ns.type === filterType.value)
  }

  // 用户过滤
  if (filterUser.value !== 'all') {
    filtered = filtered.filter(ns => ns.lastEditor === filterUser.value)
  }

  // 状态过滤
  if (filterStatus.value !== 'all') {
    filtered = filtered.filter(ns => ns.status === filterStatus.value)
  }

  return filtered
})

onMounted(async () => {
  try {
    const response = await namespaceApi.list()
    // 为每个命名空间添加模拟数据
    namespaces.value = response.data.map((ns: any) => ({
      ...ns,
      type: ns.type || '知识',
      status: ns.status || 'active',
      lastEditor: ns.lastEditor || '管理员',
      imageUrl: ns.imageUrl || '/placeholder-image.svg'
    }))
  } catch (err) {
    ElMessage.error('加载项目失败')
    console.error(err)
  }
})

const selectNamespace = (namespace: any) => {
  router.push({
    name: 'Namespace',
    params: { namespaceId: namespace.id }
  })
}

const createNamespace = () => {
  editMode.value = false
  formData.value = { 
    name: '', 
    description: '', 
    type: 'agent',
    imageUrl: ''
  }
  dialogVisible.value = true
}

const submitNamespace = async () => {
  if (!formData.value.name.trim()) {
    ElMessage.warning('项目名称不能为空')
    return
  }

  try {
    if (editMode.value && currentEditingId.value) {
      const updated = await namespaceApi.update(currentEditingId.value, formData.value)
      const index = namespaces.value.findIndex(n => n.id === currentEditingId.value)
      if (index !== -1) {
        namespaces.value[index] = { ...namespaces.value[index], ...updated.data }
      }
      ElMessage.success('项目更新成功')
    } else {
      const created = await namespaceApi.create(formData.value)
      namespaces.value.push({
        ...created.data,
        type: formData.value.type,
        status: 'active',
        lastEditor: username.value,
        imageUrl: formData.value.imageUrl || '/placeholder-image.svg'
      })
      ElMessage.success('项目创建成功')
    }
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error(editMode.value ? '更新失败' : '创建失败')
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

const logout = () => {
  console.log('用户退出')
}
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  background-color: #ffffff;
  color: #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid #e4e7ed;
}

.app-header h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 0;
}

.filter-controls {
  display: flex;
  gap: 12px;
}

.filter-select {
  width: 120px;
}

.search-section {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 0;
}

.project-card {
  background: #ffffff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: #409eff;
}

.card-header {
  margin-bottom: 16px;
}

.project-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-icon {
  color: #67c23a;
  font-size: 16px;
}

.project-subtitle {
  font-size: 14px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.project-image {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  background-color: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.project-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.project-tag {
  display: flex;
  gap: 8px;
}

.card-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.last-edited {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-section {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-controls {
    justify-content: center;
  }
  
  .search-section {
    justify-content: center;
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
  }
}
</style>