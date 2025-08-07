<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 页面头部 -->
    <div class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">我的知识库</h1>
            <p class="text-gray-600 mt-1">管理您的知识库和协作内容</p>
          </div>
          <el-button 
            type="primary" 
            size="default"
            @click="showCreateDialog = true"
            class="flex items-center gap-2"
          >
            <span>+</span>
            新建知识库
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 搜索和筛选区 -->
      <div class="mb-6">
        <div class="flex items-center gap-4">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索知识库名称"
            size="default"
            style="width: 300px"
            clearable
            @change="handleSearch"
            class="flex-shrink-0"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="accessTypeFilter"
            placeholder="访问权限"
            clearable
            @change="handleSearch"
            style="width: 150px"
          >
            <el-option label="协作者可访问" value="collaborators" />
            <el-option label="所有人可访问" value="public" />
          </el-select>
        </div>
      </div>

      <!-- 知识库列表 -->
      <div v-loading="loading">
        <div v-if="namespaces.length === 0 && !loading" class="text-center py-12">
          <div class="text-gray-400 text-lg mb-4">暂无知识库</div>
          <el-button type="primary" @click="showCreateDialog = true">
            创建您的第一个知识库
          </el-button>
        </div>
        
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="namespace in namespaces"
            :key="namespace.id"
            class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200 cursor-pointer"
            @click="handleEnterKnowledge(namespace)"
          >
            <!-- 知识库封面 -->
            <div class="relative h-32 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-t-lg overflow-hidden">
              <img
                v-if="namespace.cover"
                :src="namespace.cover"
                :alt="namespace.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="flex items-center justify-center h-full">
                <span class="text-3xl">📚</span>
              </div>
              
              <!-- 操作菜单 -->
              <div class="absolute top-3 right-3">
                <el-dropdown @command="handleAction" trigger="click">
                  <el-button 
                    size="small" 
                    circle 
                    :icon="MoreFilled" 
                    class="bg-white/80 hover:bg-white border-0 shadow-sm"
                    @click.stop
                  />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <!-- 只有有编辑权限的用户才能看到编辑相关选项 -->
                      <template v-if="namespace.can_edit">
                        <el-dropdown-item :command="{action: 'edit', data: namespace}">
                          <el-icon><Edit /></el-icon>
                          重命名
                        </el-dropdown-item>
                        <el-dropdown-item :command="{action: 'permission', data: namespace}">
                          <el-icon><User /></el-icon>
                          权限
                        </el-dropdown-item>
                        <el-dropdown-item :command="{action: 'settings', data: namespace}">
                          <el-icon><Setting /></el-icon>
                          更多设置
                        </el-dropdown-item>
                        <!-- 只有创建者才能删除知识库 -->
                        <el-dropdown-item 
                          v-if="isCreator(namespace)"
                          :command="{action: 'delete', data: namespace}"
                          divided
                          class="text-red-600"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </template>
                      
                      <!-- 只读权限用户只能查看基本信息 -->
                      <template v-else>
                        <el-dropdown-item disabled>
                          <el-icon><View /></el-icon>
                          只读权限
                        </el-dropdown-item>
                      </template>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- 知识库信息 -->
            <div class="p-4">
              <div class="flex items-start justify-between mb-2">
                <h3 class="text-lg font-semibold text-gray-900 line-clamp-1">
                  {{ namespace.name }}
                </h3>
                <div class="flex items-center text-xs text-gray-500 ml-2">
                  <el-icon class="mr-1">
                    <span v-if="namespace.access_type === 'public'">🌍</span>
                    <span v-else>🔒</span>
                  </el-icon>
                  {{ namespace.access_type === 'public' ? '公开' : '私有' }}
                </div>
              </div>
              
              <p class="text-gray-600 text-sm mb-3 line-clamp-2">
                {{ namespace.description || '暂无描述' }}
              </p>
              
              <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                <div class="flex items-center">
                  <el-icon class="mr-1"><User /></el-icon>
                  {{ namespace.collaborator_count }} 位协作者
                </div>
                <span>{{ formatDate(namespace.updated_at) }}</span>
              </div>

            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="total > pageSize" class="flex justify-center mt-8">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next, jumper"
            @current-change="loadNamespaces"
          />
        </div>
      </div>
    </div>

    <!-- 新建知识库对话框 -->
    <CreateNamespaceDialog 
      v-model="showCreateDialog"
      @success="handleCreateSuccess"
    />

    <!-- 知识库设置对话框 -->
    <NamespaceSettingsDialog
      v-model="showSettingsDialog"
      :namespace="selectedNamespace"
      @success="handleUpdateSuccess"
    />

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="showRenameDialog"
      title="重命名知识库"
      width="400px"
    >
      <el-form @submit.prevent="handleRename">
        <el-form-item label="知识库名称">
          <el-input
            v-model="newName"
            placeholder="请输入知识库名称"
            maxlength="255"
            show-word-limit
            @keyup.enter="handleRename"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRenameDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRename" :loading="renaming">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Edit, User, Setting, Delete, MoreFilled, View } from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api.js'
import { useUserStore } from '@/stores/user.js'
import CreateNamespaceDialog from './components/CreateNamespaceDialog.vue'
import NamespaceSettingsDialog from './components/NamespaceSettingsDialog.vue'

// 路由和用户store
const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const namespaces = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const searchKeyword = ref('')
const accessTypeFilter = ref('')

// 对话框控制
const showCreateDialog = ref(false)
const showSettingsDialog = ref(false)
const showRenameDialog = ref(false)
const selectedNamespace = ref(null)

// 重命名相关
const newName = ref('')
const renaming = ref(false)

// 判断当前用户是否是指定知识库的创建者
const isCreator = (namespace) => {
  return namespace.creator && userStore.userInfo && 
         namespace.creator.id === userStore.userInfo.id
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 加载知识库列表
const loadNamespaces = async (page = 1) => {
  loading.value = true
  try {
    const params = {
      page,
      search: searchKeyword.value || undefined,
      access_type: accessTypeFilter.value || undefined
    }
    
    const response = await knowledgeAPI.getNamespaces(params)
    namespaces.value = response.data.results
    total.value = response.data.count
    currentPage.value = page
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    ElMessage.error('获取知识库列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  loadNamespaces(1)
}

// 处理操作菜单
const handleAction = ({ action, data }) => {
  selectedNamespace.value = data
  
  switch (action) {
    case 'edit':
      newName.value = data.name
      showRenameDialog.value = true
      break
    case 'permission':
      // 这里可以添加简单的权限切换，或者打开设置对话框
      showSettingsDialog.value = true
      break
    case 'settings':
      showSettingsDialog.value = true
      break
    case 'delete':
      handleDelete(data)
      break
  }
}

// 处理重命名
const handleRename = async () => {
  if (!newName.value.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  
  renaming.value = true
  try {
    await knowledgeAPI.updateBasicInfo(selectedNamespace.value.id, {
      name: newName.value.trim()
    })
    
    ElMessage.success('重命名成功')
    showRenameDialog.value = false
    loadNamespaces(currentPage.value)
  } catch (error) {
    console.error('重命名失败:', error)
    ElMessage.error('重命名失败')
  } finally {
    renaming.value = false
  }
}

// 处理删除
const handleDelete = async (namespace) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库 "${namespace.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await knowledgeAPI.deleteNamespace(namespace.id)
    ElMessage.success('删除成功')
    loadNamespaces(currentPage.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理创建成功
const handleCreateSuccess = () => {
  showCreateDialog.value = false
  loadNamespaces(1)
}

// 处理更新成功
const handleUpdateSuccess = () => {
  showSettingsDialog.value = false
  loadNamespaces(currentPage.value)
}

// 处理进入知识库
const handleEnterKnowledge = (namespace) => {
  router.push({
    name: 'KnowledgeManagement',
    params: {
      namespaceId: namespace.id
    }
  })
}

// 页面加载时获取数据
onMounted(() => {
  loadNamespaces()
})
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
