<template>
  <el-dialog
    v-model="visible"
    title="Assistant设置"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="bot">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form
            ref="basicFormRef"
            :model="basicForm"
            :rules="basicRules"
            label-width="100px"
            class="mt-4"
          >
            <el-form-item label="Assistant名称" prop="name">
              <el-input
                v-model="basicForm.name"
                placeholder="请输入Assistant名称"
                maxlength="255"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="简介">
              <el-input
                v-model="basicForm.description"
                type="textarea"
                placeholder="描述Assistant的用途和功能"
                :rows="4"
                maxlength="1000"
                show-word-limit
              />
            </el-form-item>

            <!-- 头像上传 -->
            <el-form-item label="头像">
              <div class="flex items-center gap-4">
                <div class="relative">
                  <div 
                    class="w-24 h-24 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center bg-gray-50 overflow-hidden cursor-pointer hover:border-blue-400 transition-colors"
                    @click="triggerFileInput"
                  >
                    <img 
                      v-if="avatarPreview || bot.avatar" 
                      :src="avatarPreview || bot.avatar" 
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
                      v-if="avatarPreview || bot.avatar" 
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

            <el-form-item label="访问权限" prop="access_type">
              <el-radio-group v-model="basicForm.access_type">
                <div class="space-y-2">
                  <div>
                    <el-radio value="collaborators">
                      <span class="mr-2">🔒</span>
                      仅协作者可访问
                    </el-radio>
                    <div class="text-sm text-gray-500 ml-6">
                      只有您添加的协作者可以查看和编辑此Assistant
                    </div>
                  </div>
                  <div>
                    <el-radio value="public">
                      <span class="mr-2">🌍</span>
                      所有人可访问
                      <el-tag size="small" class="ml-2" type="warning">公开</el-tag>
                    </el-radio>
                    <div class="text-sm text-gray-500 ml-6">
                      系统中的所有已激活用户都可以查看此Assistant
                    </div>
                  </div>
                </div>
              </el-radio-group>
            </el-form-item>

            <div class="flex justify-end">
              <el-button 
                type="primary" 
                @click="handleSaveBasic"
                :loading="savingBasic"
              >
                保存基本信息
              </el-button>
            </div>
          </el-form>
        </el-tab-pane>

        <!-- 协作者管理 -->
        <el-tab-pane label="协作者管理" name="collaborators">
          <div class="mt-4">
            <!-- 添加协作者 -->
            <div class="mb-6">
              <h4 class="text-lg font-medium mb-4">添加协作者</h4>
              <el-form
                ref="collaboratorFormRef"
                :model="collaboratorForm"
                :rules="collaboratorRules"
                inline
              >
                <el-form-item label="用户名" prop="username">
                  <el-input
                    v-model="collaboratorForm.username"
                    placeholder="请输入用户名"
                    style="width: 200px"
                  />
                </el-form-item>
                <el-form-item label="权限" prop="role">
                  <el-select v-model="collaboratorForm.role" style="width: 150px">
                    <el-option label="管理权限" value="admin" />
                    <el-option label="只读权限" value="readonly" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="handleAddCollaborator"
                    :loading="addingCollaborator"
                  >
                    添加
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 协作者列表 -->
            <div>
              <h4 class="text-lg font-medium mb-4">协作者列表</h4>
              <div v-loading="loadingCollaborators">
                <div v-if="collaborators.length === 0" class="text-gray-500 text-center py-8">
                  暂无协作者
                </div>
                <div v-else class="space-y-3">
                  <div
                    v-for="collaborator in collaborators"
                    :key="collaborator.id"
                    class="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                  >
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                        {{ collaborator.user.username.charAt(0).toUpperCase() }}
                      </div>
                      <div>
                        <div class="font-medium">{{ collaborator.user.username }}</div>
                        <div class="text-sm text-gray-500">
                          {{ collaborator.user.first_name }} {{ collaborator.user.last_name }}
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center gap-3">
                      <el-select
                        :model-value="collaborator.role"
                        @change="(value) => handleUpdateCollaboratorRole(collaborator, value)"
                        size="small"
                        style="width: 120px"
                      >
                        <el-option label="管理权限" value="admin" />
                        <el-option label="只读权限" value="readonly" />
                      </el-select>
                      <el-button
                        size="small"
                        type="danger"
                        @click="handleRemoveCollaborator(collaborator)"
                      >
                        移除
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Assistant信息 -->
        <el-tab-pane label="Assistant信息" name="info">
          <div class="mt-4 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Assistant ID</label>
                <div class="font-mono text-sm p-3 bg-gray-100 rounded border">
                  {{ bot.assistant_id || '未分配' }}
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Graph ID</label>
                <div class="font-mono text-sm p-3 bg-gray-100 rounded border">
                  {{ bot.graph_id || 'agent' }}
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">创建者</label>
                <div class="p-3 bg-gray-100 rounded border">
                  {{ bot.creator?.username }}
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">协作者数量</label>
                <div class="p-3 bg-gray-100 rounded border">
                  {{ bot.collaborator_count }} 位
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">创建时间</label>
                <div class="p-3 bg-gray-100 rounded border">
                  {{ formatDateTime(bot.created_at) }}
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">更新时间</label>
                <div class="p-3 bg-gray-100 rounded border">
                  {{ formatDateTime(bot.updated_at) }}
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { botAPI } from '@/api.js'

// Props 和 Emits
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  bot: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

// 响应式数据
const visible = ref(false)
const activeTab = ref('basic')
const basicFormRef = ref(null)
const collaboratorFormRef = ref(null)
const fileInput = ref(null)
const avatarPreview = ref('')

const savingBasic = ref(false)
const addingCollaborator = ref(false)
const loadingCollaborators = ref(false)
const collaborators = ref([])

// 基本信息表单
const basicForm = reactive({
  name: '',
  description: '',
  access_type: 'collaborators',
  avatar: null
})

// 协作者表单
const collaboratorForm = reactive({
  username: '',
  role: 'readonly'
})

// 验证规则
const basicRules = {
  name: [
    { required: true, message: '请输入Assistant名称', trigger: 'blur' },
    { min: 1, max: 255, message: '长度在 1 到 255 个字符', trigger: 'blur' }
  ],
  access_type: [
    { required: true, message: '请选择访问权限', trigger: 'change' }
  ]
}

const collaboratorRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择权限', trigger: 'change' }
  ]
}

// 监听父组件传递的 modelValue
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal && props.bot) {
    initForm()
    loadCollaborators()
  }
})

// 监听 visible 变化，更新父组件
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 初始化表单
const initForm = () => {
  if (props.bot) {
    basicForm.name = props.bot.name
    basicForm.description = props.bot.description || ''
    basicForm.access_type = props.bot.access_type
    basicForm.avatar = null
    avatarPreview.value = ''
  }
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
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
    basicForm.avatar = e.target.result // base64格式
  }
  reader.readAsDataURL(file)
}

// 清除头像
const clearAvatar = () => {
  basicForm.avatar = ''
  avatarPreview.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 保存基本信息
const handleSaveBasic = async () => {
  try {
    const valid = await basicFormRef.value.validate()
    if (!valid) return

    savingBasic.value = true

    const updateData = {
      name: basicForm.name.trim(),
      description: basicForm.description.trim(),
      access_type: basicForm.access_type
    }

    if (basicForm.avatar) {
      updateData.avatar = basicForm.avatar
    }

    await botAPI.updateBasicInfo(props.bot.id, updateData)
    
    ElMessage.success('基本信息保存成功')
    emit('success')
  } catch (error) {
    console.error('保存基本信息失败:', error)
    ElMessage.error('保存基本信息失败')
  } finally {
    savingBasic.value = false
  }
}

// 加载协作者列表
const loadCollaborators = async () => {
  if (!props.bot) return

  loadingCollaborators.value = true
  try {
    const response = await botAPI.getCollaborators(props.bot.id)
    collaborators.value = response.data
  } catch (error) {
    console.error('获取协作者列表失败:', error)
    ElMessage.error('获取协作者列表失败')
  } finally {
    loadingCollaborators.value = false
  }
}

// 添加协作者
const handleAddCollaborator = async () => {
  try {
    const valid = await collaboratorFormRef.value.validate()
    if (!valid) return

    addingCollaborator.value = true

    await botAPI.addCollaborator(props.bot.id, {
      username: collaboratorForm.username.trim(),
      role: collaboratorForm.role
    })

    ElMessage.success('协作者添加成功')
    
    // 重置表单
    collaboratorForm.username = ''
    collaboratorForm.role = 'readonly'
    collaboratorFormRef.value.clearValidate()
    
    // 重新加载协作者列表
    loadCollaborators()
  } catch (error) {
    console.error('添加协作者失败:', error)
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('添加协作者失败')
    }
  } finally {
    addingCollaborator.value = false
  }
}

// 更新协作者权限
const handleUpdateCollaboratorRole = async (collaborator, newRole) => {
  try {
    await botAPI.updateCollaborator(props.bot.id, collaborator.user.id, {
      role: newRole
    })

    ElMessage.success('权限更新成功')
    
    // 更新本地数据
    const index = collaborators.value.findIndex(c => c.id === collaborator.id)
    if (index !== -1) {
      collaborators.value[index].role = newRole
    }
  } catch (error) {
    console.error('更新协作者权限失败:', error)
    ElMessage.error('更新协作者权限失败')
    // 重新加载列表以恢复原状态
    loadCollaborators()
  }
}

// 移除协作者
const handleRemoveCollaborator = async (collaborator) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除协作者 "${collaborator.user.username}" 吗？`,
      '移除确认',
      {
        confirmButtonText: '确定移除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await botAPI.removeCollaborator(props.bot.id, collaborator.user.id)
    
    ElMessage.success('协作者移除成功')
    loadCollaborators()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除协作者失败:', error)
      ElMessage.error('移除协作者失败')
    }
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  activeTab.value = 'basic'
}
</script>

<style scoped>
:deep(.el-tabs--border-card > .el-tabs__content) {
  padding: 20px;
}

:deep(.el-radio-group .el-radio) {
  margin-right: 0;
  margin-bottom: 8px;
  width: 100%;
}
</style>