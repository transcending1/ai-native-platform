<template>
  <div class="code-highlight-container">
    <div class="code-header" v-if="showHeader">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-red-500 rounded-full"></div>
          <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
          <div class="w-3 h-3 bg-green-500 rounded-full"></div>
        </div>
        <div class="text-xs text-gray-500">{{ language }}</div>
      </div>
    </div>
    <div class="code-content" :class="{ 'with-header': showHeader }">
      <pre v-if="!editable" class="code-block"><code :class="`language-${language}`" ref="codeElement"></code></pre>
      <el-input
        v-else
        v-model="editableCode"
        type="textarea"
        :rows="rows"
        class="code-editor"
        @input="handleCodeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-json'

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  language: {
    type: String,
    default: 'python'
  },
  editable: {
    type: Boolean,
    default: false
  },
  rows: {
    type: Number,
    default: 8
  },
  showHeader: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:code'])

const codeElement = ref(null)
const editableCode = ref(props.code)

// 高亮代码
const highlightCode = () => {
  if (codeElement.value) {
    codeElement.value.textContent = props.code
    Prism.highlightElement(codeElement.value)
  }
}

// 处理代码变化
const handleCodeChange = (value) => {
  emit('update:code', value)
}

// 监听代码变化
watch(() => props.code, (newCode) => {
  editableCode.value = newCode
  if (!props.editable) {
    nextTick(() => {
      highlightCode()
    })
  }
}, { immediate: true })

onMounted(() => {
  if (!props.editable) {
    nextTick(() => {
      highlightCode()
    })
  }
})
</script>

<style scoped>
.code-highlight-container {
  border-radius: 8px;
  overflow: hidden;
  background: #1e1e1e;
  border: 1px solid #333;
}

.code-header {
  background: #2d2d2d;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
}

.code-content {
  position: relative;
}

.code-content.with-header {
  border-top: none;
}

.code-block {
  margin: 0;
  padding: 16px;
  background: transparent;
  overflow-x: auto;
}

.code-block code {
  font-family: 'Fira Code', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
}

.code-editor {
  border: none;
  background: transparent;
}

.code-editor :deep(.el-textarea__inner) {
  background: #1e1e1e;
  border: 1px solid #333;
  color: #d4d4d4;
  font-family: 'Fira Code', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  padding: 16px;
  resize: vertical;
  border-radius: 0;
}

.code-editor :deep(.el-textarea__inner:focus) {
  box-shadow: none;
  border: none;
}

/* 滚动条样式 */
.code-block::-webkit-scrollbar,
.code-editor :deep(.el-textarea__inner)::-webkit-scrollbar {
  height: 8px;
}

.code-block::-webkit-scrollbar-track,
.code-editor :deep(.el-textarea__inner)::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.code-block::-webkit-scrollbar-thumb,
.code-editor :deep(.el-textarea__inner)::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.code-block::-webkit-scrollbar-thumb:hover,
.code-editor :deep(.el-textarea__inner)::-webkit-scrollbar-thumb:hover {
  background: #777;
}
</style> 