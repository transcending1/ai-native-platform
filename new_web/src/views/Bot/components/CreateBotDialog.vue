<template>
  <el-dialog
    v-model="visible"
    title="新建Assistant"
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
            placeholder="请输入Assistant名称"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="简介">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="选填，描述Assistant的用途和功能"
            :rows="3"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <!-- 头像上传 -->
        <el-form-item label="头像">
          <div class="flex items-center gap-4">
            <div class="relative">
              <div 
                class="w-20 h-20 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center bg-gray-50 overflow-hidden cursor-pointer hover:border-blue-400 transition-colors"
                @click="triggerFileInput"
              >
                <img 
                  v-if="avatarPreview" 
                  :src="avatarPreview" 
                  alt="头像预览" 
                  class="w-full h-full object-cover"
                />
                <div v-else class="text-center">
                  <el-icon class="text-gray-400 text-2xl mb-1"><Plus /></el-icon>
                  <div class="text-xs text-gray-400">上传头像</div>
                </div>
              </div>
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                @change="handleAvatarChange"
                class="hidden"
              />
            </div>
            <div class="flex-1">
              <div class="text-sm text-gray-600 mb-2">
                支持 JPG、PNG、GIF、WebP 格式，最大 5MB
              </div>
              <div class="flex gap-2">
                <el-button size="small" @click="triggerFileInput">
                  选择文件
                </el-button>
                <el-button 
                  v-if="avatarPreview" 
                  size="small" 
                  type="danger" 
                  @click="clearAvatar"
                >
                  清除
                </el-button>
              </div>
            </div>
          </div>
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
                  只有您添加的协作者可以查看和编辑此Assistant
                </p>
              </div>

              <div 
                class="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                :class="{'border-blue-500 bg-blue-50': form.access_type === 'public'}"
                @click="form.access_type = 'public'"
              >
                <el-radio value="public" class="mb-2">
                  <div class="flex items-center">
                    <span class="text-lg mr-2">🌍</span>
                    <span class="font-medium">所有人可访问</span>
                    <el-tag size="small" class="ml-2" type="warning">公开</el-tag>
                  </div>
                </el-radio>
                <p class="text-sm text-gray-600 ml-6">
                  系统中的所有已激活用户都可以查看此Assistant
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
import { Check, Plus } from '@element-plus/icons-vue'
import { botAPI } from '@/api.js'

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
const fileInput = ref(null)
const avatarPreview = ref('')

// 表单数据
const form = reactive({
  name: '',
  description: '',
  access_type: 'collaborators',
  avatar: null
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入Assistant名称', trigger: 'blur' },
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
  form.avatar = null
  avatarPreview.value = ''
  
  // 清除验证错误
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 触发文件输入
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理头像选择
const handleAvatarChange = (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('请选择 JPG、PNG、GIF 或 WebP 格式的图片')
    return
  }

  // 验证文件大小（5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 5MB')
    return
  }

  // 读取文件并生成预览
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
    form.avatar = e.target.result // base64格式
  }
  reader.readAsDataURL(file)
}

// 清除头像
const clearAvatar = () => {
  form.avatar = null
  avatarPreview.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
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

    // 如果有头像则添加
    if (form.avatar) {
      submitData.avatar = form.avatar
    }

    // 调用 API 创建Bot
    await botAPI.createBot(submitData)
    
    ElMessage.success('Assistant创建成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('创建Assistant失败:', error)
    
    // 处理服务器返回的错误信息
    if (error.response?.data) {
      const errorData = error.response.data
      if (errorData.name) {
        ElMessage.error(`名称错误: ${errorData.name[0]}`)
      } else if (errorData.detail) {
        ElMessage.error(errorData.detail)
      } else if (errorData.error) {
        ElMessage.error(errorData.error)
      } else {
        ElMessage.error('创建Assistant失败，请稍后重试')
      }
    } else {
      ElMessage.error('创建Assistant失败，请稍后重试')
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