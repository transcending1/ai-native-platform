<template>
  <div class="document-viewer h-full flex flex-col bg-white">
    <!-- 文档头部 -->
    <div class="document-header p-6 border-b border-gray-200">
      <div class="flex items-start justify-between">
        <div class="flex-1 min-w-0">
          <!-- 文档标题 - 始终只读显示 -->
          <div class="mb-2">
            <div class="flex items-center space-x-2 mb-2">
              <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                {{ getDocTypeLabel(document.doc_type) }}
              </span>
              <h1 class="text-2xl font-bold text-gray-900">{{ document.title }}</h1>
            </div>
            <div class="flex items-center text-sm text-gray-500 space-x-4">
              <span>创建者：{{ document.creator?.username || '未知' }}</span>
              <span>更新时间：{{ formatDate(document.updated_at) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex items-center space-x-2 ml-4">
          <template v-if="!isEditing">
            <el-button 
              type="primary" 
              :icon="Edit" 
              @click="handleEdit"
            >
              编辑
            </el-button>
            <el-dropdown @command="handleAction" trigger="click">
              <el-button :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="share">
                    <el-icon><Share /></el-icon>
                    分享
                  </el-dropdown-item>
                  <el-dropdown-item command="export">
                    <el-icon><Download /></el-icon>
                    导出
                  </el-dropdown-item>
                  <el-dropdown-item command="print">
                    <el-icon><Printer /></el-icon>
                    打印
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          
          <template v-else>
            <el-button @click="handleCancel">取消</el-button>
            <el-button 
              type="primary" 
              :loading="saving" 
              @click="handleSave"
            >
              保存
            </el-button>
          </template>
        </div>
      </div>
    </div>
    
    <!-- 文档内容 -->
    <div class="document-content flex-1 overflow-auto">
      <!-- 文档知识类型 -->
      <template v-if="document.doc_type === 'document' || !document.doc_type">
        <!-- 查看模式 -->
        <div v-if="!isEditing" class="h-full flex flex-col">
          
          <!-- 有内容时使用富文本编辑器显示 -->
          <div v-if="document.content && document.content.trim()" class="flex-1">
            <RichTextEditor
              v-model="document.content"
              :disabled="true"
              :show-stats="false"
              placeholder=""
            />
          </div>
          
          <!-- 如果内容为空，显示提示 -->
          <div v-else class="text-center py-8 text-gray-500">
            <div class="text-4xl mb-3">📝</div>
            <p>此文档暂无内容</p>
            <el-button type="primary" @click="handleEdit" class="mt-3">
              开始编辑
            </el-button>
          </div>
        </div>
        
        <!-- 编辑模式 -->
        <div v-else class="h-full flex flex-col">
          
          <!-- 富文本编辑器 -->
          <div class="flex-1">
            <RichTextEditor
              v-model="editForm.content"
              :disabled="false"
              :show-stats="true"
              placeholder="请输入文档内容，支持富文本格式..."
              @change="handleContentChange"
            />
          </div>
        </div>
      </template>
      
      <!-- 工具知识类型 -->
      <template v-else-if="document.doc_type === 'tool'">
        <ToolEditor
          ref="toolEditorRef"
          :namespace-id="namespaceId"
          :document="document"
          :is-editing="isEditing"
        />
      </template>
      
      <!-- 表单知识类型 -->
      <template v-else-if="document.doc_type === 'form'">
        <FormEditor
          ref="formEditorRef"
          :namespace-id="namespaceId"
          :document="document"
          :is-editing="isEditing"
          @save="handleFormSave"
        />
      </template>
      
      <!-- 文件夹类型 -->
      <template v-else-if="document.doc_type === 'folder'">
        <div class="p-6 text-center text-gray-500">
          <div class="text-4xl mb-3">📁</div>
          <p>这是一个文件夹，用于组织其他知识</p>
        </div>
      </template>
      
      <!-- 未知类型 -->
      <template v-else>
        <div class="p-6 text-center text-gray-500">
          <div class="text-4xl mb-3">❓</div>
          <p>未知的知识类型：{{ document.doc_type }}</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Edit, MoreFilled, Share, Download, Printer
} from '@element-plus/icons-vue'
// 移除marked导入，因为不再需要Markdown处理
import { knowledgeAPI } from '@/api.js'
import ToolEditor from './ToolEditor.vue'
import FormEditor from './FormEditor.vue'
import RichTextEditor from '@/components/RichTextEditor.vue'

const props = defineProps({
  namespaceId: {
    type: [String, Number],
    required: true
  },
  document: {
    type: Object,
    required: true
  },
  isEditing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit', 'save', 'cancel'])

// 响应式数据
const saving = ref(false)

// 组件引用
const toolEditorRef = ref(null)
const formEditorRef = ref(null)

// 编辑表单
const editForm = ref({
  content: '',
  summary: ''
})

// 获取文档类型标签
const getDocTypeLabel = (docType) => {
  const labels = {
    document: '文档知识',
    tool: '工具知识', 
    form: '表单知识',
    folder: '文件夹'
  }
  return labels[docType] || '未知类型'
}

// 移除renderedContent计算属性，因为现在直接使用RichTextEditor显示内容

// 移除previewContent计算属性，因为不再需要Markdown预览

// 处理内容变化
const handleContentChange = (content) => {
  editForm.value.content = content
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 初始化编辑表单
const initEditForm = () => {
  // 直接使用文档内容，因为现在统一使用HTML格式
  editForm.value = {
    content: props.document.content || '',
    summary: props.document.summary || ''
  }
}

// 处理编辑
const handleEdit = () => {
  if (props.document.doc_type === 'document' || !props.document.doc_type) {
    initEditForm()
  }
  emit('edit')
}

// 处理保存
const handleSave = async () => {
  const docType = props.document.doc_type || 'document'
  
  if (docType === 'document') {
    await handleDocumentSave()
  } else if (docType === 'tool') {
    await handleToolSave()
  } else if (docType === 'form') {
    await handleFormSave()
  }
}

// 处理文档保存
const handleDocumentSave = async () => {
  saving.value = true
  try {
    // 直接保存HTML内容，保持富文本格式
    const content = editForm.value.content || ''
    
    const updateData = {
      title: props.document.title, // 保持原有标题
      content: content, // 直接保存HTML内容
      summary: editForm.value.summary
    }
    
    await knowledgeAPI.updateDocument(props.namespaceId, props.document.id, updateData)
    emit('save')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 处理工具保存
const handleToolSave = async () => {
  if (toolEditorRef.value) {
    const success = await toolEditorRef.value.save()
    if (success) {
      emit('save')
    }
  }
}

// 处理表单保存
const handleFormSave = async () => {
  if (formEditorRef.value) {
    const success = await formEditorRef.value.save()
    if (success) {
      emit('save')
    }
  }
}

// 处理取消
const handleCancel = () => {
  emit('cancel')
}

// 处理其他操作
const handleAction = (command) => {
  switch (command) {
    case 'share':
      // 实现分享功能
      ElMessage.info('分享功能开发中')
      break
    case 'export':
      // 实现导出功能
      exportDocument()
      break
    case 'print':
      // 实现打印功能
      window.print()
      break
  }
}

// 导出文档
const exportDocument = () => {
  const content = props.document.content || ''
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.document.title}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 监听文档变化
watch(() => props.document, (newDocument) => {
  console.log('DocumentViewer 接收到新文档:', newDocument) // 调试日志
  if (props.isEditing && (newDocument.doc_type === 'document' || !newDocument.doc_type)) {
    initEditForm()
  }
}, { immediate: true })
</script>

<style scoped>
.document-viewer {
  background: #ffffff;
}
</style> 