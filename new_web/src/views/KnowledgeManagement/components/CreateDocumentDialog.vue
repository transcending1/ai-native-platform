<template>
  <el-dialog
    v-model="visible"
    title="新建文档"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="标题" prop="title">
        <el-input
          v-model="form.title"
          placeholder="请输入文档标题"
          maxlength="255"
          show-word-limit
          :prefix-icon="Document"
        />
      </el-form-item>
      
      <el-form-item label="摘要">
        <el-input
          v-model="form.summary"
          type="textarea"
          :rows="3"
          placeholder="请输入文档摘要（可选）"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="内容">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="8"
          placeholder="请输入文档内容，支持 Markdown 格式（可选）"
        />
      </el-form-item>
      
      <el-form-item v-if="parentFolder" label="父级目录">
        <el-input :value="parentFolder.title" readonly>
          <template #prepend>
            <el-icon><Folder /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      
      <el-form-item label="权限">
        <el-radio-group v-model="form.is_public">
          <el-radio :value="true">
            <div class="flex items-center">
              <el-icon class="mr-1"><View /></el-icon>
              公开 - 知识库内所有成员可见
            </div>
          </el-radio>
          <el-radio :value="false">
            <div class="flex items-center">
              <el-icon class="mr-1"><Lock /></el-icon>
              私有 - 仅自己可见
            </div>
          </el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="flex justify-end">
        <div class="space-x-2">
          <el-button @click="handleClose">取消</el-button>
          <el-button type="primary" :loading="creating" @click="handleSubmit">
            创建文档
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Folder, View, Lock } from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api.js'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  namespaceId: {
    type: [String, Number],
    required: true
  },
  parentFolder: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

// 响应式数据
const formRef = ref(null)
const creating = ref(false)

// 表单数据
const form = ref({
  title: '',
  content: '',
  summary: '',
  doc_type: 'document',
  parent: null,
  is_public: true
})

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入文档标题', trigger: 'blur' },
    { min: 1, max: 255, message: '标题长度在 1 到 255 个字符', trigger: 'blur' }
  ]
}

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 重置表单
const resetForm = () => {
  form.value = {
    title: '',
    content: '',
    summary: '',
    doc_type: 'document',
    parent: props.parentFolder?.id || null,
    is_public: true
  }
  
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  
  creating.value = true
  try {
    const createData = {
      title: form.value.title.trim(),
      content: form.value.content,
      summary: form.value.summary,
      doc_type: 'document',
      parent: form.value.parent,
      is_public: form.value.is_public
    }
    
    const response = await knowledgeAPI.createDocument(props.namespaceId, createData)
    
    ElMessage.success('文档创建成功')
    emit('success', response.data)
    handleClose()
  } catch (error) {
    console.error('创建文档失败:', error)
    ElMessage.error('创建文档失败')
  } finally {
    creating.value = false
  }
}

// 处理关闭
const handleClose = () => {
  visible.value = false
  resetForm()
}

// 监听父级文件夹变化
watch(() => props.parentFolder, (newParent) => {
  form.value.parent = newParent?.id || null
}, { immediate: true })

// 监听对话框打开
watch(visible, (newVisible) => {
  if (newVisible) {
    resetForm()
  }
})
</script>

<style scoped>
:deep(.el-radio) {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

:deep(.el-radio__label) {
  padding-left: 8px;
}
</style> 