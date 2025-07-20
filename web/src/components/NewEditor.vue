<template>
  <div class="editor-wrapper">
    <div class="toolbar">
      <el-button @click="triggerFileUpload" type="primary" size="small">
        <el-icon><Upload /></el-icon>
        上传文件
      </el-button>
      <input type="file" ref="fileInput" @change="handleFileUpload" hidden multiple>
    </div>
    <div ref="editorEl" class="editor-container"></div>
    <div class="editor-actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import Editor from '@toast-ui/editor'
import '@toast-ui/editor/dist/toastui-editor.css'
import '@toast-ui/editor/dist/theme/toastui-editor-dark.css'
import colorSyntax from '@toast-ui/editor-plugin-color-syntax'
import codeSyntaxHighlight from '@toast-ui/editor-plugin-code-syntax-highlight'
import 'prismjs/themes/prism.css'

// 类型定义
type EditorInstance = any // 临时修复类型问题

interface Note {
  id: number
  title: string
  content: string
  type?: string
  directory?: number
}

// Props
const props = defineProps<{
  note?: Note | null
}>()

// Emits
const emit = defineEmits<{
  save: [noteData: { id: number; title: string; content: string }]
  cancel: []
}>()

// DOM 元素引用
const editorEl = ref<HTMLElement | null>(null)
const editor = shallowRef<EditorInstance | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

// 初始化编辑器
const initEditor = () => {
  if (!editorEl.value) return

  console.log('初始化 Toast UI Editor...')
  console.log('编辑器容器元素:', editorEl.value)

  try {
    editor.value = new Editor({
      el: editorEl.value,
      initialEditType: 'markdown', // 改为 markdown 模式
      previewStyle: 'vertical',
      height: '100%', // 使用百分比高度
      plugins: [colorSyntax, codeSyntaxHighlight],
      theme: 'light',
      usageStatistics: false,
      hooks: {
        addImageBlobHook: (blob, callback) => {
          handleImageUpload(blob, callback)
          return false
        }
      }
    })

    console.log('编辑器初始化成功:', editor.value)

    // 如果有笔记内容，加载到编辑器
    if (props.note?.content) {
      editor.value.setMarkdown(props.note.content)
      console.log('加载笔记内容:', props.note.content)
    }
  } catch (error) {
    console.error('编辑器初始化失败:', error)
  }
}

// 通用文件上传处理
const uploadFile = async (file: File): Promise<string> => {
  try {
    const formData = new FormData()
    formData.append('file', file)

    // 这里应该使用你的实际上传API
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) throw new Error('上传失败')

    const result = await response.json()
    return result.url
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('文件上传失败')
    return ''
  }
}

// 图片上传专用处理
const handleImageUpload = async (blob: any, callback: any) => {
  const file = new File([blob], `image-${Date.now()}`, { type: blob.type })
  const url = await uploadFile(file)
  if (url) {
    callback(url)
  }
}

// 触发文件选择
const triggerFileUpload = () => {
  fileInput.value?.click()
}

// 处理文件上传
const handleFileUpload = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return

  for (const file of Array.from(input.files)) {
    try {
      // 文件大小限制（10MB）
      const MAX_SIZE = 10 * 1024 * 1024
      if (file.size > MAX_SIZE) {
        ElMessage.error(`文件大小超过限制: ${file.name}`)
        continue
      }

      const url = await uploadFile(file)
      if (url) {
        // 根据文件类型插入不同内容
        if (file.type.startsWith('image/')) {
          editor.value?.insertText(`![](${url})`)
        } else {
          editor.value?.insertText(`[${file.name}](${url})`)
        }
      }
    } catch (error) {
      console.error(`${file.name} 上传失败:`, error)
    }
  }

  // 清空选择
  input.value = ''
}

// 保存笔记
const handleSave = () => {
  if (!editor.value || !props.note) return

  const content = editor.value.getMarkdown()
  const noteData = {
    id: props.note.id,
    title: props.note.title,
    content: content
  }

  emit('save', noteData)
  ElMessage.success('笔记保存成功')
}

// 取消编辑
const handleCancel = () => {
  emit('cancel')
}

// 监听笔记变化
watch(() => props.note, (newNote) => {
  if (newNote && editor.value) {
    editor.value.setMarkdown(newNote.content || '')
  }
}, { immediate: true })

onMounted(() => {
  // 延迟初始化，确保 DOM 完全准备好
  setTimeout(() => {
    initEditor()
  }, 100)
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
.editor-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  padding: 10px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.editor-container {
  flex: 1;
  min-height: 400px; /* 设置最小高度 */
  height: 100%;
  position: relative;
}

.editor-actions {
  padding: 10px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.toastui-editor-defaultUI) {
  height: 100% !important;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

:deep(.toastui-editor-defaultUI-toolbar) {
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

:deep(.toastui-editor-main) {
  height: calc(100% - 50px) !important;
}

:deep(.toastui-editor-md-container) {
  height: 100% !important;
}

:deep(.toastui-editor-md-vertical-style .toastui-editor-md-preview) {
  height: 100% !important;
}
</style>