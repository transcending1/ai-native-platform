<template>
  <div class="knowledge-management h-full flex">
    <!-- 左侧文档树区域 -->
    <div class="left-panel w-80 bg-white border-r border-gray-200 flex flex-col">
      <!-- 顶部工具栏 -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-gray-900">{{ namespaceInfo.name }}</h2>
          <el-dropdown @command="handleCommand" trigger="click">
            <el-button size="small" circle :icon="Plus" type="primary" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="new-folder">
                  <el-icon><Folder /></el-icon>
                  新建文件夹
                </el-dropdown-item>
                <el-dropdown-item command="new-document">
                  <el-icon><Document /></el-icon>
                  新建文档
                </el-dropdown-item>
                <el-dropdown-item divided>
                  <el-dropdown @command="handleToolCommand" trigger="hover" placement="right-start">
                    <span class="flex items-center justify-between w-full cursor-pointer">
                      <span class="flex items-center">
                        <el-icon class="mr-2"><Tools /></el-icon>
                        工具
                      </span>
                      <el-icon class="text-gray-400"><ArrowRight /></el-icon>
                    </span>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="new-tool-manual">
                          <el-icon class="mr-2"><Tools /></el-icon>
                          手动创建工具
                        </el-dropdown-item>
                        <el-dropdown-item command="new-tool-ai">
                          <el-icon class="mr-2"><Star /></el-icon>
                          AI生成工具
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </el-dropdown-item>
                <el-dropdown-item command="new-form">
                  <el-icon><Grid /></el-icon>
                  新建表单
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <!-- 搜索框 -->
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文档..."
          size="small"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <!-- 文档树 -->
      <div class="flex-1 overflow-auto">
        <DocumentTree 
          ref="documentTreeRef"
          :namespace-id="namespaceId"
          :search-keyword="searchKeyword"
          @select="handleDocumentSelect"
          @create="handleCreateDocument"
          @edit="handleEditDocument"
          @delete="handleDeleteDocument"
          @move="handleMoveDocument"
        />
      </div>
    </div>
    
    <!-- 右侧内容区域 -->
    <div class="right-panel flex-1 flex flex-col bg-gray-50">
      <!-- 内容区域 -->
      <div class="flex-1 overflow-hidden">
        <!-- 欢迎页面 -->
        <div v-if="!selectedDocument" class="h-full flex items-center justify-center">
          <div class="text-center">
            <div class="text-6xl mb-4">📚</div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2">欢迎来到知识库</h3>
            <p class="text-gray-600 mb-4">选择左侧文档开始查看，或创建新的文档</p>
            <el-button type="primary" @click="handleCommand('new-document')">
              创建第一个文档
            </el-button>
          </div>
        </div>
        
        <!-- 文档查看器/编辑器 -->
        <DocumentViewer 
          v-else
          :namespace-id="namespaceId"
          :document="selectedDocument"
          :is-editing="isEditing"
          @edit="handleEditMode"
          @save="handleSaveDocument"
          @cancel="handleCancelEdit"
        />
      </div>
    </div>
    
    <!-- 各种创建对话框 -->
    <CreateFolderDialog
      v-model="showCreateFolderDialog"
      :namespace-id="namespaceId"
      :parent-folder="createParentFolder"
      @success="handleCreateSuccess"
    />
    
    <CreateDocumentDialog
      v-model="showCreateDocumentDialog"
      :namespace-id="namespaceId"
      :parent-folder="createParentFolder"
      @success="handleCreateSuccess"
    />
    
    <CreateToolDialog
      v-model="showCreateToolDialog"
      :namespace-id="namespaceId"
      :parent-folder="createParentFolder"
      @success="handleCreateSuccess"
    />
    
    <CreateFormDialog
      v-model="showCreateFormDialog"
      :namespace-id="namespaceId"
      :parent-folder="createParentFolder"
      @success="handleCreateSuccess"
    />
    
    <CreateToolByAIDialog
      v-model="showCreateToolByAIDialog"
      :namespace-id="namespaceId"
      :parent-folder="createParentFolder"
      @success="handleCreateSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Plus, Search, Document, Folder, Tools, Grid, Star, ArrowRight
} from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api.js'
import DocumentTree from './components/DocumentTree.vue'
import DocumentViewer from './components/DocumentViewer.vue'
import CreateFolderDialog from './components/CreateFolderDialog.vue'
import CreateDocumentDialog from './components/CreateDocumentDialog.vue'
import CreateToolDialog from './components/CreateToolDialog.vue'
import CreateFormDialog from './components/CreateFormDialog.vue'
import CreateToolByAIDialog from './components/CreateToolByAIDialog.vue'

const route = useRoute()
const router = useRouter()

// 基础数据
const namespaceId = ref(route.params.namespaceId)
const namespaceInfo = ref({})
const searchKeyword = ref('')

// 文档相关
const selectedDocument = ref(null)
const isEditing = ref(false)

// 对话框控制
const showCreateFolderDialog = ref(false)
const showCreateDocumentDialog = ref(false)
const showCreateToolDialog = ref(false)
const showCreateFormDialog = ref(false)
const showCreateToolByAIDialog = ref(false)
const createParentFolder = ref(null)

// 文档树组件引用
const documentTreeRef = ref(null)

// 加载知识库信息
const loadNamespaceInfo = async () => {
  try {
    const response = await knowledgeAPI.getNamespace(namespaceId.value)
    namespaceInfo.value = response.data
  } catch (error) {
    console.error('加载知识库信息失败:', error)
    ElMessage.error('加载知识库信息失败')
    router.push('/knowledge-namespace')
  }
}

// 处理顶部菜单命令
const handleCommand = (command) => {
  createParentFolder.value = null
  
  switch (command) {
    case 'new-folder':
      showCreateFolderDialog.value = true
      break
    case 'new-document':
      showCreateDocumentDialog.value = true
      break
    case 'new-form':
      showCreateFormDialog.value = true
      break
  }
}

// 处理工具子菜单命令
const handleToolCommand = (command) => {
  createParentFolder.value = null
  
  switch (command) {
    case 'new-tool-manual':
      showCreateToolDialog.value = true
      break
    case 'new-tool-ai':
      showCreateToolByAIDialog.value = true
      break
  }
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑由DocumentTree组件处理
}

// 处理文档选择
const handleDocumentSelect = async (document) => {
  console.log('Main.vue 接收到文档选择:', document) // 调试日志
  
  // 如果是文件夹类型，不处理
  if (document.doc_type === 'folder') {
    console.log('点击的是文件夹，不加载内容')
    return
  }
  
  try {
    // 文档树API返回的可能是简化数据，需要获取完整的文档详情
    // 对于不同类型的知识，检查相应的数据字段是否存在
    const needsFullData = document.id && (
      (document.doc_type === 'document' && !document.content) ||
      (document.doc_type === 'tool' && !document.tool_data) ||
      (document.doc_type === 'form' && !document.form_data) ||
      (!document.doc_type && !document.content) // 兼容旧数据
    )
    
    if (needsFullData) {
      console.log('文档数据不完整，尝试加载完整详情...')
      const response = await knowledgeAPI.getDocument(namespaceId.value, document.id)
      console.log('加载的文档详情:', response.data)
      selectedDocument.value = response.data
    } else {
      selectedDocument.value = document
    }
    isEditing.value = false
  } catch (error) {
    console.error('加载文档详情失败:', error)
    // 如果加载失败，还是显示原始文档
    selectedDocument.value = document
    isEditing.value = false
  }
}

// 处理创建文档（从文档树触发）
const handleCreateDocument = (parentFolder) => {
  createParentFolder.value = parentFolder
  showCreateDocumentDialog.value = true
}

// 处理编辑文档
const handleEditDocument = (document) => {
  selectedDocument.value = document
  isEditing.value = true
}

// 处理删除文档
const handleDeleteDocument = async (document) => {
  try {
    await knowledgeAPI.deleteDocument(namespaceId.value, document.id)
    ElMessage.success('删除成功')
    
    // 如果删除的是当前选中的文档，清空选择
    if (selectedDocument.value?.id === document.id) {
      selectedDocument.value = null
      isEditing.value = false
    }
    
    // 刷新文档树
    documentTreeRef.value?.refresh()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// 处理移动文档
const handleMoveDocument = async (document, targetParent) => {
  try {
    await knowledgeAPI.moveDocument(namespaceId.value, document.id, {
      target_parent_id: targetParent?.id || null
    })
    ElMessage.success('移动成功')
  } catch (error) {
    console.error('移动失败:', error)
    ElMessage.error('移动失败')
  }
}

// 处理编辑模式
const handleEditMode = () => {
  isEditing.value = true
}

// 处理保存文档
const handleSaveDocument = async () => {
  // 先关闭编辑模式并显示成功消息
  isEditing.value = false
  ElMessage.success('保存成功')
  
  try {
    // 重新获取最新的文档数据
    if (selectedDocument.value?.id) {
      console.log('保存成功，重新加载文档数据...')
      const response = await knowledgeAPI.getDocument(namespaceId.value, selectedDocument.value.id)
      console.log('重新加载的文档数据:', response.data)
      selectedDocument.value = response.data
    }
    
    // 刷新文档树以更新可能变化的标题等信息
    documentTreeRef.value?.refresh()
  } catch (error) {
    console.error('重新加载文档数据失败:', error)
    // 重新加载失败不影响用户体验，数据已经保存成功了
  }
}

// 处理取消编辑
const handleCancelEdit = () => {
  isEditing.value = false
}

// 处理创建成功
const handleCreateSuccess = (newDocument) => {
  // 关闭所有对话框
  showCreateFolderDialog.value = false
  showCreateDocumentDialog.value = false
  showCreateToolDialog.value = false
  showCreateToolByAIDialog.value = false
  showCreateFormDialog.value = false
  
  // 如果创建的不是文件夹，选中新文档
  if (newDocument.doc_type !== 'folder') {
    selectedDocument.value = newDocument
    isEditing.value = false
  }
  
  // 刷新文档树以显示新创建的文档
  documentTreeRef.value?.refresh()
}

// 监听路由参数变化
watch(() => route.params.namespaceId, (newId) => {
  if (newId) {
    namespaceId.value = newId
    loadNamespaceInfo()
    selectedDocument.value = null
    isEditing.value = false
  }
})

// 页面加载时初始化
onMounted(() => {
  loadNamespaceInfo()
})
</script>

<style scoped>
.knowledge-management {
  height: calc(100vh - 120px); /* 减去头部和底部的高度 */
}

.left-panel {
  min-width: 320px;
  max-width: 480px;
  resize: horizontal;
  overflow: auto;
}

.right-panel {
  min-width: 0; /* 允许flex收缩 */
}

/* 嵌套下拉菜单样式 */
:deep(.el-dropdown-menu__item) {
  padding: 8px 16px;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: #f0f9ff;
  color: #1890ff;
}

/* 工具子菜单样式 */
:deep(.el-dropdown-menu .el-dropdown-menu) {
  margin-left: 4px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.el-dropdown-menu .el-dropdown-menu .el-dropdown-menu__item) {
  padding: 8px 12px;
  font-size: 14px;
}

:deep(.el-dropdown-menu .el-dropdown-menu .el-dropdown-menu__item:hover) {
  background-color: #e6f7ff;
  color: #1890ff;
}
</style>
