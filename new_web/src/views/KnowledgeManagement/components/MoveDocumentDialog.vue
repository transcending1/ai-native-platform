<template>
  <el-dialog
    v-model="visible"
    title="移动文档"
    width="500px"
    :close-on-click-modal="false"
  >
    <div v-if="document" class="move-document-dialog">
      <div class="mb-4">
        <div class="text-sm text-gray-600 mb-2">将要移动的文档：</div>
        <div class="flex items-center p-3 bg-gray-50 rounded-lg">
          <el-icon class="mr-2 text-gray-500">
            <Folder v-if="document.doc_type === 'folder'" />
            <Document v-else />
          </el-icon>
          <span class="font-medium">{{ document.title }}</span>
        </div>
      </div>
      
      <div class="mb-4">
        <div class="text-sm text-gray-600 mb-2">选择目标位置：</div>
        <div class="border border-gray-200 rounded-lg max-h-80 overflow-auto">
          <!-- 根目录选项 -->
          <div 
            class="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100"
            :class="{ 'bg-blue-50 text-blue-600': selectedParent === null }"
            @click="selectedParent = null"
          >
            <el-icon class="mr-2">
              <House />
            </el-icon>
            <span class="font-medium">根目录</span>
            <el-icon v-if="selectedParent === null" class="ml-auto text-blue-600">
              <Check />
            </el-icon>
          </div>
          
          <!-- 文件夹树 -->
          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="treeProps"
            node-key="id"
            :expand-on-click-node="false"
            :default-expand-all="false"
            @node-click="handleNodeClick"
            class="folder-tree"
          >
            <template #default="{ node, data }">
              <div 
                class="flex items-center w-full py-1"
                :class="{ 
                  'text-blue-600 bg-blue-50': selectedParent?.id === data.id,
                  'text-gray-400': data.id === document.id || isDescendant(data.id)
                }"
              >
                <el-icon class="mr-2">
                  <Folder />
                </el-icon>
                <span class="flex-1">{{ data.title }}</span>
                <el-icon v-if="selectedParent?.id === data.id" class="ml-2 text-blue-600">
                  <Check />
                </el-icon>
                <span v-if="data.id === document.id || isDescendant(data.id)" class="text-xs text-gray-400 ml-2">
                  (不可选择)
                </span>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
      
      <div class="text-sm text-gray-500">
        <el-icon class="mr-1"><InfoFilled /></el-icon>
        不能将文档移动到自身或其子文件夹中
      </div>
    </div>
    
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button 
        type="primary" 
        :disabled="!canMove"
        @click="handleConfirm"
      >
        移动
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { House, Folder, Document, Check, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  document: {
    type: Object,
    default: null
  },
  treeData: {
    type: Array,
    default: () => []
  },
  namespaceId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

// 响应式数据
const selectedParent = ref(null)
const treeRef = ref(null)

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'title'
}

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 是否可以移动
const canMove = computed(() => {
  if (!props.document) return false
  
  // 如果选择的是当前文档的父级，则不需要移动
  const currentParentId = props.document.parent
  const selectedParentId = selectedParent.value?.id || null
  
  return currentParentId !== selectedParentId
})

// 过滤树数据，只显示文件夹
const filteredTreeData = computed(() => {
  return filterFolders(props.treeData)
})

// 递归过滤，只保留文件夹
const filterFolders = (nodes) => {
  return nodes
    .filter(node => node.doc_type === 'folder')
    .map(node => ({
      ...node,
      children: node.children ? filterFolders(node.children) : []
    }))
}

// 检查是否为子文档（递归检查）
const isDescendant = (nodeId) => {
  if (!props.document) return false
  
  const checkDescendant = (nodes, parentId) => {
    for (const node of nodes) {
      if (node.id === parentId) {
        return true
      }
      if (node.children && checkDescendant(node.children, parentId)) {
        return true
      }
    }
    return false
  }
  
  // 获取要移动文档的子树
  const findDocumentSubtree = (nodes) => {
    for (const node of nodes) {
      if (node.id === props.document.id) {
        return node.children || []
      }
      if (node.children) {
        const result = findDocumentSubtree(node.children)
        if (result) return result
      }
    }
    return null
  }
  
  const documentSubtree = findDocumentSubtree(props.treeData)
  if (!documentSubtree) return false
  
  return checkDescendant(documentSubtree, nodeId)
}

// 处理节点点击
const handleNodeClick = (data) => {
  // 不能选择自己或者子文档
  if (data.id === props.document?.id || isDescendant(data.id)) {
    return
  }
  
  // 只能选择文件夹
  if (data.doc_type !== 'folder') {
    return
  }
  
  selectedParent.value = data
}

// 处理确认
const handleConfirm = () => {
  emit('confirm', selectedParent.value)
}

// 处理取消
const handleCancel = () => {
  visible.value = false
  selectedParent.value = null
}

// 监听对话框打开
watch(visible, (newVisible) => {
  if (newVisible && props.document) {
    // 默认选择当前父级
    selectedParent.value = props.document.parent ? 
      findNodeById(props.treeData, props.document.parent) : null
  } else if (!newVisible) {
    selectedParent.value = null
  }
})

// 根据ID查找节点
const findNodeById = (nodes, id) => {
  for (const node of nodes) {
    if (node.id === id) {
      return node
    }
    if (node.children) {
      const result = findNodeById(node.children, id)
      if (result) return result
    }
  }
  return null
}

// 使用过滤后的数据
const treeData = computed(() => filteredTreeData.value)
</script>

<style scoped>
.move-document-dialog {
  min-height: 300px;
}

:deep(.folder-tree) {
  background: transparent;
}

:deep(.folder-tree .el-tree-node__content) {
  padding: 8px 12px;
  border-radius: 4px;
  margin: 2px 0;
}

:deep(.folder-tree .el-tree-node__content:hover) {
  background-color: #f5f7fa;
}

:deep(.folder-tree .el-tree-node.is-current > .el-tree-node__content) {
  background-color: #e6f7ff;
  color: #1890ff;
}
</style> 