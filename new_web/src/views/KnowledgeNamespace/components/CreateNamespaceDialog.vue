<template>
  <el-dialog
    v-model="visible"
    title="新建知识库"
    width="500px"
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
      <!-- 基本信息 -->
      <div class="mb-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">基本信息</h3>
        
        <el-form-item label="名称" prop="name" required>
          <el-input
            v-model="form.name"
            placeholder="请输入知识库名称"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="简介">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="选填，描述知识库的用途和内容"
            :rows="3"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </div>

      <!-- 访问权限设置 -->
      <div class="mb-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">新建至</h3>
        
        <el-form-item label="" prop="access_type">
          <el-radio-group v-model="form.access_type" class="w-full">
            <div class="space-y-3">
              <div 
                class="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                :class="{'border-blue-500 bg-blue-50': form.access_type === 'collaborators'}"
                @click="form.access_type = 'collaborators'"
              >
                <el-radio value="collaborators" class="mb-2">
                  <div class="flex items-center">
                    <span class="text-lg mr-2">👥</span>
                    <span class="font-medium">仅协作者可访问</span>
                    <el-icon class="ml-auto text-green-500"><Check /></el-icon>
                  </div>
                </el-radio>
                <p class="text-sm text-gray-600 ml-6">
                  只有您添加的协作者可以查看和编辑此知识库
                </p>
              </div>

              <div 
                class="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                :class="{'border-blue-500 bg-blue-50': form.access_type === 'public'}"
                @click="form.access_type = 'public'"
              >
                <el-radio value="public" class="mb-2">
                  <div class="flex items-center">
                    <span class="text-lg mr-2">👥</span>
                    <span class="font-medium">所有人可访问</span>
                    <el-tag size="small" class="ml-2" type="warning">公开</el-tag>
                  </div>
                </el-radio>
                <p class="text-sm text-gray-600 ml-6">
                  系统中的所有已激活用户都可以查看此知识库
                </p>
              </div>
            </div>
          </el-radio-group>
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <div class="flex justify-end gap-3">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
        >
          新建
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api.js'

// Props 和 Emits
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

// 响应式数据
const visible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

// 表单数据
const form = reactive({
  name: '',
  description: '',
  access_type: 'collaborators'
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 1, max: 255, message: '长度在 1 到 255 个字符', trigger: 'blur' }
  ],
  access_type: [
    { required: true, message: '请选择访问权限', trigger: 'change' }
  ]
}

// 监听父组件传递的 modelValue
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    resetForm()
  }
})

// 监听 visible 变化，更新父组件
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 重置表单
const resetForm = () => {
  form.name = ''
  form.description = ''
  form.access_type = 'collaborators'
  
  // 清除验证错误
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}

// 提交表单
const handleSubmit = async () => {
  try {
    // 验证表单
    const valid = await formRef.value.validate()
    if (!valid) {
      return
    }

    submitting.value = true

    // 准备提交数据
    const submitData = {
      name: form.name.trim(),
      access_type: form.access_type
    }

    // 如果有描述则添加
    if (form.description.trim()) {
      submitData.description = form.description.trim()
    }

    // 调用 API 创建知识库
    await knowledgeAPI.createNamespace(submitData)
    
    ElMessage.success('知识库创建成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('创建知识库失败:', error)
    
    // 处理服务器返回的错误信息
    if (error.response?.data) {
      const errorData = error.response.data
      if (errorData.name) {
        ElMessage.error(`名称错误: ${errorData.name[0]}`)
      } else if (errorData.detail) {
        ElMessage.error(errorData.detail)
      } else {
        ElMessage.error('创建知识库失败，请稍后重试')
      }
    } else {
      ElMessage.error('创建知识库失败，请稍后重试')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* 自定义单选框样式 */
:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #409eff;
  border-color: #409eff;
}

:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #409eff;
}

/* 卡片样式 */
.el-radio-group .el-radio {
  margin-right: 0;
  margin-bottom: 0;
}
</style> 