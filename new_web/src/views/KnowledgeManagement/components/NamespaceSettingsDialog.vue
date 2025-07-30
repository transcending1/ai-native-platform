<template>
  <el-dialog
    v-model="visible"
    title="知识库管理"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-tabs v-model="activeTab" class="namespace-settings-tabs">
      <!-- 知识库信息 -->
      <el-tab-pane label="知识库信息" name="info">
        <div class="p-4">
          <!-- 只读权限提示 -->
          <div v-if="!canEdit" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="flex items-center text-blue-600">
              <el-icon class="mr-2"><InfoFilled /></el-icon>
              <span class="text-sm">您当前拥有只读权限，无法编辑知识库设置。如需编辑权限，请联系知识库管理员。</span>
            </div>
          </div>
          <el-form
            ref="infoFormRef"
            :model="infoForm"
            :rules="infoRules"
            label-width="100px"
            :disabled="!canEdit"
          >
            <el-form-item label="图标和名称" prop="name" required>
              <div class="flex items-center gap-4">
                <!-- 封面上传区域 -->
                <div class="flex-shrink-0">
                  <el-upload
                    class="cover-uploader"
                    :show-file-list="false"
                    :before-upload="beforeCoverUpload"
                    :on-success="handleCoverSuccess"
                    :on-error="handleCoverError"
                    action="#"
                    :auto-upload="false"
                    :on-change="handleCoverChange"
                  >
                    <div class="cover-preview">
                      <img
                        v-if="infoForm.cover"
                        :src="infoForm.cover"
                        class="cover-image"
                        alt="知识库封面"
                      />
                      <div v-else class="cover-placeholder">
                        <el-icon><Plus /></el-icon>
                        <span class="text-xs">上传封面</span>
                      </div>
                    </div>
                  </el-upload>
                  <!-- <div class="text-xs text-gray-500 mt-1 text-center">
                    <el-button 
                      v-if="infoForm.cover" 
                      type="text" 
                      size="small"
                      @click="clearCover"
                      class="text-red-500"
                    >
                      清除
                    </el-button>
                  </div> -->
                </div>
                
                <!-- 名称输入 -->
                <div class="flex-1">
                  <el-input
                    v-model="infoForm.name"
                    placeholder="请输入知识库名称"
                    maxlength="255"
                    show-word-limit
                  />
                </div>
              </div>
            </el-form-item>

            <el-form-item label="简介">
              <el-input
                v-model="infoForm.description"
                type="textarea"
                placeholder="描述知识库的用途和内容"
                :rows="3"
                maxlength="1000"
                show-word-limit
              />
            </el-form-item>



            <el-form-item label="访问权限">
              <el-radio-group v-model="infoForm.access_type">
                <div class="space-y-2">
                  <el-radio value="collaborators">
                    <div class="flex items-center">
                      <span class="text-lg mr-2">🔒</span>
                      <span>仅协作者可访问</span>
                    </div>
                  </el-radio>
                  <el-radio value="public">
                    <div class="flex items-center">
                      <span class="text-lg mr-2">👥</span>
                      <span>所有人可访问</span>
                      <el-tag size="small" class="ml-2" type="warning">公开</el-tag>
                    </div>
                  </el-radio>
                </div>
              </el-radio-group>
            </el-form-item>
          </el-form>

          <div v-if="canEdit" class="flex justify-end mt-6">
            <el-button type="primary" @click="updateBasicInfo" :loading="updating">
              更新信息
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 权限管理 - 仅管理员可见 -->
      <el-tab-pane v-if="canEdit" label="权限" name="permissions">
        <div class="p-4">
          <div class="mb-4">
            <h3 class="text-lg font-medium text-gray-900 mb-2">协作者</h3>
            <p class="text-gray-600 text-sm">可以添加协作用户，让对应的用户进入协同编辑模式</p>
          </div>

          <!-- 添加协作者 -->
          <div class="mb-6 p-4 bg-gray-50 rounded-lg">
            <div class="flex items-center gap-3">
              <el-input
                v-model="newCollaboratorUsername"
                placeholder="请输入用户名"
                class="flex-1"
                @keyup.enter="addCollaborator"
              />
              <el-checkbox v-model="newCollaboratorCanEdit">
                可管理
              </el-checkbox>
              <el-button 
                type="primary" 
                @click="addCollaborator"
                :loading="addingCollaborator"
              >
                添加
              </el-button>
            </div>
          </div>

          <!-- 协作者列表 -->
          <div class="space-y-3">
            <div
              v-for="collaborator in collaborators"
              :key="collaborator.id"
              class="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
            >
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <span class="text-sm text-blue-600">{{ collaborator.user.username.charAt(0).toUpperCase() }}</span>
                </div>
                <div>
                  <div class="font-medium">{{ collaborator.user.username }}</div>
                  <div class="text-sm text-gray-500">
                    {{ collaborator.can_edit ? '可管理' : '只读' }}
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <el-dropdown @command="handleCollaboratorAction" trigger="click">
                  <el-button size="small" type="text">
                    权限
                    <el-icon class="ml-1"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item 
                        :command="{action: 'permission', data: collaborator}"
                        :disabled="collaborator.can_edit"
                      >
                        设为可管理
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{action: 'readonly', data: collaborator}"
                        :disabled="!collaborator.can_edit"
                      >
                        设为只读
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{action: 'remove', data: collaborator}"
                        divided
                        class="text-red-600"
                      >
                        移除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <div v-if="collaborators.length === 0" class="text-center text-gray-500 py-8">
              暂无协作者
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowDown, InfoFilled } from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api.js'

// Props 和 Emits
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  namespace: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

// 响应式数据
const visible = ref(false)
const activeTab = ref('info')
const updating = ref(false)
const addingCollaborator = ref(false)
const infoFormRef = ref(null)

// 知识库数据
const namespaceData = ref(null)
const collaborators = ref([])

// 基本信息表单
const infoForm = reactive({
  name: '',
  description: '',
  cover: '',
  access_type: 'collaborators'
})

// 新协作者
const newCollaboratorUsername = ref('')
const newCollaboratorCanEdit = ref(true)

// 表单验证规则
const infoRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 1, max: 255, message: '长度在 1 到 255 个字符', trigger: 'blur' }
  ]
}

// 计算属性：判断当前用户是否有编辑权限
const canEdit = computed(() => {
  return namespaceData.value?.can_edit === true || namespaceData.value?.can_edit === 'true'
})

// 监听父组件传递的 modelValue
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal && props.namespace) {
    loadNamespaceData()
  }
})

// 监听 visible 变化，更新父组件
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 加载知识库数据
const loadNamespaceData = async () => {
  if (!props.namespace) return
  
  try {
    const response = await knowledgeAPI.getNamespace(props.namespace.id)
    namespaceData.value = response.data
    
    // 填充表单数据
    infoForm.name = response.data.name || ''
    infoForm.description = response.data.description || ''
    infoForm.cover = response.data.cover || ''
    infoForm.access_type = response.data.access_type || 'collaborators'
    
    // 加载协作者列表
    collaborators.value = response.data.collaborators || []
  } catch (error) {
    console.error('获取知识库详情失败:', error)
    ElMessage.error('获取知识库详情失败')
  }
}

// 处理封面上传
const beforeCoverUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('上传图片大小不能超过 5MB!')
    return false
  }
  return true
}

const handleCoverChange = (file) => {
  // 创建预览URL
  if (file.raw) {
    const reader = new FileReader()
    reader.onload = (e) => {
      infoForm.cover = e.target.result
    }
    reader.readAsDataURL(file.raw)
  }
}

const handleCoverSuccess = (response) => {
  ElMessage.success('封面上传成功')
}

const handleCoverError = () => {
  ElMessage.error('封面上传失败')
}

const clearCover = () => {
  infoForm.cover = ''
}

// 复制路径
const copyPath = () => {
  const path = `https://www.yuque.com/zongjunyi/${namespaceData.value.slug}`
  navigator.clipboard.writeText(path).then(() => {
    ElMessage.success('路径已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 更新基本信息
const updateBasicInfo = async () => {
  try {
    const valid = await infoFormRef.value.validate()
    if (!valid) return

    updating.value = true

    const updateData = {
      name: infoForm.name.trim(),
      access_type: infoForm.access_type
    }

    if (infoForm.description.trim()) {
      updateData.description = infoForm.description.trim()
    }

    if (infoForm.cover) {
      updateData.cover = infoForm.cover
    }

    await knowledgeAPI.updateBasicInfo(namespaceData.value.id, updateData)
    
    ElMessage.success('更新成功')
    emit('success')
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error('更新失败')
  } finally {
    updating.value = false
  }
}

// 添加协作者
const addCollaborator = async () => {
  if (!newCollaboratorUsername.value.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }

  addingCollaborator.value = true
  try {
    await knowledgeAPI.addCollaborator(namespaceData.value.id, {
      username: newCollaboratorUsername.value.trim(),
      can_edit: newCollaboratorCanEdit.value
    })

    ElMessage.success('添加协作者成功')
    newCollaboratorUsername.value = ''
    newCollaboratorCanEdit.value = true
    
    // 重新加载数据
    loadNamespaceData()
  } catch (error) {
    console.error('添加协作者失败:', error)
    if (error.response?.data?.username) {
      ElMessage.error(`用户名错误: ${error.response.data.username[0]}`)
    } else {
      ElMessage.error('添加协作者失败')
    }
  } finally {
    addingCollaborator.value = false
  }
}

// 处理协作者操作
const handleCollaboratorAction = async ({ action, data }) => {
  try {
    switch (action) {
      case 'permission':
        await knowledgeAPI.updateCollaborator(namespaceData.value.id, data.user.id, {
          can_edit: true
        })
        ElMessage.success('权限更新成功')
        loadNamespaceData()
        break
      
      case 'readonly':
        await knowledgeAPI.updateCollaborator(namespaceData.value.id, data.user.id, {
          can_edit: false
        })
        ElMessage.success('权限更新成功')
        loadNamespaceData()
        break
      
      case 'remove':
        await ElMessageBox.confirm(
          `确定要移除协作者 "${data.user.username}" 吗？`,
          '移除确认',
          {
            confirmButtonText: '确定移除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await knowledgeAPI.removeCollaborator(namespaceData.value.id, data.user.id)
        ElMessage.success('移除成功')
        loadNamespaceData()
        break
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  activeTab.value = 'info'
}
</script>

<style scoped>
.namespace-settings-tabs :deep(.el-tabs__header) {
  margin: 0;
  border-bottom: 1px solid #e4e7ed;
}

.namespace-settings-tabs :deep(.el-tabs__content) {
  padding: 0;
}

.cover-uploader {
  display: block;
}

.cover-preview {
  width: 80px;
  height: 80px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.3s;
  overflow: hidden;
}

.cover-preview:hover {
  border-color: #409eff;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c939d;
  text-align: center;
}

.cover-placeholder .el-icon {
  font-size: 24px;
  margin-bottom: 4px;
}
</style> 