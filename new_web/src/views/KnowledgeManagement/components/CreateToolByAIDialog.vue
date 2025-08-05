<template>
  <el-dialog
    v-model="dialogVisible"
    title="AI智能生成工具"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="工具描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="6"
          placeholder="请详细描述您想要创建的工具功能，例如：&#10;请帮我生成一个请假的工具，输入请假天数和开始日期即可&#10;请帮我生成一个计算器工具，可以进行加减乘除运算&#10;请帮我生成一个天气查询工具，输入城市名称返回天气信息&#10;&#10;您可以提供更详细的描述，包括：&#10;- 工具的具体功能和使用场景&#10;- 输入参数的要求和格式&#10;- 输出结果的期望格式&#10;- 特殊的业务逻辑或规则"
          maxlength="30000"
          show-word-limit
        />
        <div class="text-xs text-gray-500 mt-1">
          描述越详细，AI生成的工具越准确
        </div>
      </el-form-item>
      
      <!-- AI生成提示 -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div class="flex items-start">
          <el-icon class="text-blue-500 mr-2 mt-0.5"><InfoFilled /></el-icon>
          <div class="text-sm text-blue-800">
            <div class="font-medium mb-1">AI生成提示</div>
            <ul class="list-disc list-inside space-y-1 text-xs">
              <li>AI生成工具需要1-3分钟时间，请耐心等待</li>
              <li>生成过程中请勿关闭页面或刷新浏览器</li>
              <li>描述支持最多30000个字符，可以详细描述工具功能</li>
              <li>如果生成失败，请检查描述是否清晰，或稍后重试</li>
              <li>生成完成后可以继续编辑和调整工具配置</li>
            </ul>
          </div>
        </div>
      </div>
      

      
      <el-form-item label="父级目录" v-if="parentFolder">
        <div class="text-sm text-gray-600">
          将在 "{{ parentFolder.title }}" 下创建
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="flex justify-end space-x-2">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="generating" 
          @click="handleGenerate"
        >
          {{ generating ? 'AI生成中，请耐心等待...' : '开始AI生成' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
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
const generating = ref(false)

// 表单数据
const form = ref({
  description: ''
})

// 表单验证规则
const rules = {
  description: [
    { required: true, message: '请输入工具功能描述', trigger: 'blur' },
    { min: 10, message: '描述至少需要10个字符', trigger: 'blur' },
    { max: 30000, message: '描述不能超过30000个字符', trigger: 'blur' }
  ]
}

// 对话框可见性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 处理关闭
const handleClose = () => {
  if (!generating.value) {
    dialogVisible.value = false
    resetForm()
  }
}

// 重置表单
const resetForm = () => {
  form.value = {
    description: ''
  }
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 处理生成
const handleGenerate = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  generating.value = true
  
  // 显示开始生成的提示
  ElMessage.info('AI开始生成工具，请耐心等待1-3分钟...')
  
  try {
    const data = {
      description: form.value.description.trim(),
      parent_id: props.parentFolder?.id
    }

    const response = await knowledgeAPI.generateToolByAI(props.namespaceId, data)
    
    ElMessage.success('AI生成工具成功！')
    dialogVisible.value = false
    emit('success', response.data)
    
  } catch (error) {
    console.error('AI生成工具失败:', error)
    let errorMessage = 'AI生成工具失败，请稍后重试'
    
    if (error.code === 'ECONNABORTED') {
      errorMessage = 'AI生成超时，请检查网络连接或稍后重试'
    } else if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    }
    
    ElMessage.error(errorMessage)
  } finally {
    generating.value = false
  }
}

// 监听对话框打开，重置表单
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    resetForm()
  }
})
</script>

<style scoped>
.el-textarea__inner {
  font-family: inherit;
}
</style> 