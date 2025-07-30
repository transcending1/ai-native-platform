<template>
  <div class="document-tree">
    <div v-loading="loading" class="tree-content">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :expand-on-click-node="false"
        :default-expand-all="false"
        :check-on-click-node="false"
        node-key="id"
        :filter-node-method="filterNode"
        @node-click="handleNodeClick"
        @node-expand="handleNodeExpand"
        @node-collapse="handleNodeCollapse"
        class="custom-tree"
      >
        <template #default="{ node, data }">
          <div class="tree-node flex items-center justify-between w-full pr-2">
            <div class="node-content flex items-center flex-1 min-w-0">
              <!-- 展开/收起箭头（仅文件夹显示） -->
              <div 
                v-if="data.doc_type === 'folder'" 
                class="expand-icon mr-1 cursor-pointer flex items-center justify-center w-4 h-4"
                @click.stop="toggleFolder(node, data)"
              >
                <el-icon class="text-gray-400 text-xs transition-transform" :class="{ 'rotate-90': node.expanded }">
                  <ArrowRight />
                </el-icon>
              </div>
              <div v-else class="w-5"></div> <!-- 占位符，保持对齐 -->
              
              <!-- 文档类型图标 -->
              <el-icon class="mr-2 text-gray-500">
                <Folder v-if="data.doc_type === 'folder'" />
                <Document v-else-if="data.doc_type === 'document'" />
                <Setting v-else-if="data.doc_type === 'tool'" />
                <Grid v-else-if="data.doc_type === 'form'" />
                <Document v-else />
              </el-icon>
              
              <!-- 标题 -->
              <span 
                class="node-title text-sm text-gray-700 truncate flex-1"
                :class="{ 
                  'font-medium': data.doc_type === 'folder',
                  'text-blue-600': data.doc_type === 'tool',
                  'text-green-600': data.doc_type === 'form'
                }"
              >
                {{ data.title }}
              </span>
              
              <!-- 文档类型标签 -->
              <span v-if="data.doc_type !== 'folder'" class="text-xs text-gray-400 ml-1">
                {{ getDocTypeLabel(data.doc_type) }}
              </span>
              
              <!-- 子项数量（文件夹） -->
              <span v-if="data.doc_type === 'folder' && data.children && data.children.length > 0" 
                    class="text-xs text-gray-400 ml-1">
                ({{ data.children.length }})
              </span>
            </div>
            
            <!-- 操作按钮 -->
            <div class="node-actions flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
              <el-dropdown @command="(cmd) => handleNodeAction(cmd, data)" trigger="click" size="small">
                <el-button 
                  size="small" 
                  text 
                  circle 
                  :icon="MoreFilled"
                  class="hover:bg-gray-100"
                  @click.stop
                />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item 
                      v-if="data.doc_type === 'folder'"
                      :command="{ action: 'add-child', data }"
                    >
                      <el-icon><Plus /></el-icon>
                      添加子项
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'rename', data }">
                      <el-icon><Edit /></el-icon>
                      重命名
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'move', data }" divided>
                      <el-icon><Rank /></el-icon>
                      移动
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'copy', data }">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-dropdown-item>
                    <el-dropdown-item 
                      :command="{ action: 'delete', data }"
                      class="text-red-600"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>
      </el-tree>
      
      <!-- 空状态 -->
      <div v-if="!loading && treeData.length === 0" class="empty-state text-center py-8">
        <div class="text-gray-400 text-4xl mb-3">📄</div>
        <p class="text-gray-500 text-sm mb-3">暂无文档</p>
        <el-button type="primary" size="small" @click="handleCreateRoot">
          创建第一个文档
        </el-button>
      </div>
    </div>
    
    <!-- 移动文档对话框 -->
    <MoveDocumentDialog
      v-model="showMoveDialog"
      :document="moveDocument"
      :tree-data="treeData"
      :namespace-id="namespaceId"
      @confirm="handleMoveConfirm"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Folder, Document, Edit, Plus, Rank, CopyDocument, Delete, MoreFilled, Setting, Grid, ArrowRight
} from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api.js'
import MoveDocumentDialog from './MoveDocumentDialog.vue'

const props = defineProps({
  namespaceId: {
    type: [String, Number],
    required: true
  },
  searchKeyword: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'select', 'create', 'edit', 'delete', 'move'
])

// 响应式数据
const loading = ref(false)
const treeData = ref([])
const treeRef = ref(null)
const showMoveDialog = ref(false)
const moveDocument = ref(null)

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'title',
  isLeaf: (data, node) => {
    // 如果明确是文件夹类型，则不是叶子节点（即使暂时没有子项也可以展开）
    if (data.doc_type === 'folder') {
      return false
    }
    // 如果有children数组且长度大于0，则不是叶子节点
    if (data.children && Array.isArray(data.children) && data.children.length > 0) {
      return false
    }
    // 其他情况（document、tool、form等）视为叶子节点
    return true
  }
}

// 加载文档树
const loadDocumentTree = async () => {
  loading.value = true
  try {
    console.log('开始加载文档树，namespaceId:', props.namespaceId) // 调试日志
    const response = await knowledgeAPI.getDocumentTree(props.namespaceId)
    console.log('文档树API响应:', response) // 调试日志
    
    // API可能返回不同的数据结构，我们需要适配
    let documents = []
    if (Array.isArray(response.data)) {
      documents = response.data
    } else if (response.data.results && Array.isArray(response.data.results)) {
      documents = response.data.results
    } else if (response.data.data && Array.isArray(response.data.data)) {
      documents = response.data.data
    } else {
      console.warn('未知的API响应格式:', response.data)
      documents = []
    }
    
    console.log('解析的文档数据:', documents) // 调试日志
    treeData.value = buildTreeData(documents)
  } catch (error) {
    console.error('加载文档树失败:', error)
    ElMessage.error('加载文档树失败')
  } finally {
    loading.value = false
  }
}

// 构建树形数据
const buildTreeData = (documents) => {
  console.log('构建树形数据，输入文档:', documents) // 调试日志
  
  if (!Array.isArray(documents) || documents.length === 0) {
    console.log('文档数组为空') // 调试日志
    return []
  }

  // 检查是否已经是树形结构（API可能直接返回树形数据）
  const hasChildren = documents.some(doc => doc.children && Array.isArray(doc.children))
  
  if (hasChildren) {
    console.log('API返回的已经是树形结构，直接使用') // 调试日志
    
    // 直接使用API返回的树形结构，只需要排序
    const sortNodes = (nodes) => {
      nodes.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      nodes.forEach(node => {
        if (node.children && Array.isArray(node.children) && node.children.length > 0) {
          sortNodes(node.children)
        }
      })
    }
    
    const result = [...documents]
    sortNodes(result)
    console.log('排序后的树形数据:', result) // 调试日志
    return result
  }

  // 如果不是树形结构，则需要构建
  console.log('需要重新构建树形结构') // 调试日志
  
  const map = new Map()
  const roots = []
  
  // 首先创建所有节点的映射
  documents.forEach((doc, index) => {
    const node = { 
      ...doc, 
      children: [],
      // 确保有id字段作为key，支持多种ID字段
      id: doc.id || doc.pk || doc.document_id || index
    }
    map.set(node.id, node)
    console.log(`节点 ${index}:`, {
      title: node.title, 
      id: node.id, 
      doc_type: doc.doc_type,
      parent: doc.parent,
      原始数据: doc
    }) // 调试日志
  })
  
  // 然后建立父子关系
  documents.forEach(doc => {
    const nodeId = doc.id || doc.pk || doc.document_id
    const node = map.get(nodeId)
    
    if (!node) {
      console.error('找不到节点:', nodeId, doc)
      return
    }
    
    // 检查是否有parent字段，支持多种可能的parent字段名
    const parentId = doc.parent || doc.parent_id || doc.parentId || doc.parent_document_id
    
    if (parentId && map.has(parentId)) {
      const parent = map.get(parentId)
      parent.children.push(node)
      console.log('添加子节点:', node.title, '到父节点:', parent.title) // 调试日志
    } else {
      // 如果没有parent字段或parent不存在，则作为根节点
      roots.push(node)
      console.log('添加根节点:', node.title, 'parent值:', parentId) // 调试日志
    }
  })
  
  // 按排序序号排序
  const sortNodes = (nodes) => {
    nodes.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    nodes.forEach(node => {
      if (node.children?.length) {
        sortNodes(node.children)
      }
    })
  }
  
  sortNodes(roots)
  console.log('最终树形数据:', roots) // 调试日志
  console.log('根节点数量:', roots.length) // 调试日志
  return roots
}

// 过滤节点
const filterNode = (value, data) => {
  if (!value) return true
  return data.title.toLowerCase().includes(value.toLowerCase())
}

// 处理节点点击
const handleNodeClick = (data, node) => {
  console.log('点击节点:', data.title, 'doc_type:', data.doc_type, 'node:', node) // 调试日志
  
  if (data.doc_type === 'folder') {
    // 如果是文件夹，切换展开/收起状态
    console.log('点击文件夹:', data.title, '切换展开状态') // 调试日志
    const isExpanded = node.expanded
    if (isExpanded) {
      treeRef.value.store.nodesMap[data.id].collapse()
    } else {
      treeRef.value.store.nodesMap[data.id].expand()
    }
  } else {
    // 文档类型：选中文档（包括document, tool, form等所有非folder类型）
    console.log('选中文档:', data.title, 'doc_type:', data.doc_type) // 调试日志
    emit('select', data)
  }
}

// 处理节点展开
const handleNodeExpand = (data, node) => {
  console.log('节点展开:', data.title) // 调试日志
}

// 处理节点收起
const handleNodeCollapse = (data, node) => {
  console.log('节点收起:', data.title) // 调试日志
}

// 切换文件夹展开状态
const toggleFolder = (node, data) => {
  console.log('切换文件夹状态:', data.title, '当前expanded:', node.expanded) // 调试日志
  
  if (node.expanded) {
    treeRef.value.store.nodesMap[data.id].collapse()
  } else {
    treeRef.value.store.nodesMap[data.id].expand()
  }
}

// 处理节点操作
const handleNodeAction = async ({ action, data }) => {
  switch (action) {
    case 'rename':
      await handleRename(data)
      break
    case 'add-child':
      emit('create', data)
      break
    case 'move':
      moveDocument.value = data
      showMoveDialog.value = true
      break
    case 'copy':
      await handleCopy(data)
      break
    case 'delete':
      await handleDelete(data)
      break
  }
}

// 处理重命名
const handleRename = async (document) => {
  try {
    const { value: newTitle } = await ElMessageBox.prompt(
      '请输入新的标题',
      '重命名',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: document.title,
        inputValidator: (value) => {
          if (!value || value.trim() === '') {
            return '标题不能为空'
          }
          if (value.length > 100) {
            return '标题长度不能超过100个字符'
          }
          return true
        }
      }
    )
    
    if (newTitle && newTitle.trim() !== document.title) {
      await knowledgeAPI.updateDocument(props.namespaceId, document.id, {
        title: newTitle.trim()
      })
      ElMessage.success('重命名成功')
      loadDocumentTree()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重命名失败:', error)
      ElMessage.error('重命名失败')
    }
  }
}

// 处理复制
const handleCopy = async (document) => {
  try {
    await ElMessageBox.confirm(
      `确定要复制 "${document.title}" 吗？`,
      '复制确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    const copyData = {
      title: `${document.title} - 副本`,
      content: document.content,
      doc_type: document.doc_type,
      parent: document.parent,
      is_public: document.is_public
    }
    
    await knowledgeAPI.createDocument(props.namespaceId, copyData)
    ElMessage.success('复制成功')
    loadDocumentTree()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('复制失败:', error)
      ElMessage.error('复制失败')
    }
  }
}

// 处理删除
const handleDelete = async (document) => {
  try {
    const message = document.doc_type === 'folder' 
      ? `确定要删除文件夹 "${document.title}" 及其所有内容吗？此操作不可恢复。`
      : `确定要删除文档 "${document.title}" 吗？此操作不可恢复。`
      
    await ElMessageBox.confirm(message, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
    
    // 只发出删除事件，由父组件处理实际的删除操作
    emit('delete', document)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除确认失败:', error)
    }
  }
}

// 处理移动确认
const handleMoveConfirm = (targetParent) => {
  emit('move', moveDocument.value, targetParent)
  showMoveDialog.value = false
  moveDocument.value = null
  loadDocumentTree()
}

// 处理创建根文档
const handleCreateRoot = () => {
  emit('create', null)
}

// 获取文档类型标签
const getDocTypeLabel = (docType) => {
  const labels = {
    'document': '文档',
    'tool': '工具',
    'form': '表单',
    'folder': '文件夹'
  }
  return labels[docType] || '文档'
}

// 监听搜索关键词变化
watch(() => props.searchKeyword, (newVal) => {
  if (treeRef.value) {
    treeRef.value.filter(newVal)
  }
})

// 监听命名空间变化
watch(() => props.namespaceId, () => {
  loadDocumentTree()
})

// 页面加载时初始化
onMounted(() => {
  loadDocumentTree()
})

// 暴露刷新方法
defineExpose({
  refresh: loadDocumentTree
})
</script>

<style scoped>
.document-tree {
  height: 100%;
}

.tree-content {
  height: 100%;
  overflow: auto;
}

:deep(.custom-tree) {
  background: transparent;
}

:deep(.custom-tree .el-tree-node) {
  margin-bottom: 2px;
}

:deep(.custom-tree .el-tree-node__content) {
  height: 36px;
  border-radius: 6px;
  transition: all 0.2s;
  padding: 0 8px;
}

:deep(.custom-tree .el-tree-node__content:hover) {
  background-color: #f5f7fa;
}

:deep(.custom-tree .el-tree-node.is-current > .el-tree-node__content) {
  background-color: #e6f7ff;
  color: #1890ff;
}

.tree-node:hover .node-actions {
  opacity: 1 !important;
}

.empty-state {
  padding: 2rem 1rem;
}

/* 展开箭头动画 */
.expand-icon {
  transition: all 0.2s ease;
}

.expand-icon:hover {
  background-color: rgba(0, 0, 0, 0.04);
  border-radius: 2px;
}

/* 旋转动画 */
.rotate-90 {
  transform: rotate(90deg);
}
</style> 