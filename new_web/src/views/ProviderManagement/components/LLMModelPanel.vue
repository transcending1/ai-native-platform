<template>
  <div>
    <!-- 操作栏 -->
    <div class="flex justify-end items-center gap-4 mb-6">
      <!-- 搜索框 -->
      <el-input
        v-model="searchKeyword"
        placeholder="搜索模型ID"
        size="default"
        style="width: 250px"
        clearable
        @change="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <!-- 新建按钮 -->
      <el-button 
        type="primary" 
        size="default"
        @click="showCreateDialog = true"
        class="flex items-center gap-2"
      >
        <span>+</span>
        新建LLM模型
      </el-button>
    </div>

    <!-- 模型列表 -->
    <div v-loading="loading">
      <div v-if="models.length === 0 && !loading" class="text-center py-12">
        <div class="text-gray-400 text-lg mb-4">暂无LLM模型</div>
        <el-button type="primary" @click="showCreateDialog = true">
          创建您的第一个LLM模型
        </el-button>
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="model in models"
          :key="model.id"
          class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <!-- 模型封面 -->
          <div class="relative h-32 bg-gradient-to-br from-orange-50 to-red-100 rounded-t-lg overflow-hidden">
            <div class="flex items-center justify-center h-full">
              <span class="text-3xl">🤖</span>
            </div>
            
            <!-- 操作菜单 -->
            <div class="absolute top-3 right-3">
              <el-dropdown @command="handleAction" trigger="click">
                <el-button 
                  size="small" 
                  circle 
                  :icon="MoreFilled" 
                  class="bg-white/80 hover:bg-white border-0 shadow-sm"
                />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'edit', data: model}">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'delete', data: model}" divided class="text-red-600">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <!-- 模型信息 -->
          <div class="p-4">
            <div class="flex items-start justify-between mb-2">
              <h3 class="text-lg font-semibold text-gray-900 line-clamp-1">
                {{ model.model_id }}
              </h3>
            </div>
            
            <p class="text-gray-600 text-sm mb-3 line-clamp-2">
              {{ getProviderLabel(model.provider) }}
            </p>
            
            
            <!-- 状态标签 -->
            <div class="flex items-center justify-between mb-3">
              <el-tag 
                :type="model.is_active ? 'success' : 'info'"
                size="small"
              >
                {{ model.is_active ? '启用' : '禁用' }}
              </el-tag>
              <span class="text-xs text-gray-500">
                {{ formatDate(model.updated_at) }}
              </span>
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex justify-end gap-2">
              <el-button 
                type="success" 
                size="small"
                @click="handleTest(model)"
                :loading="testingModel === model.id"
              >
                测试模型
              </el-button>
              <el-button 
                type="primary" 
                size="small"
                @click="handleEdit(model)"
              >
                编辑模型
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="total > pageSize" class="flex justify-center mt-8">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, jumper"
          @current-change="loadModels"
        />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingModel ? '编辑LLM模型' : '创建LLM模型'"
      width="600px"
    >
      <el-form 
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="模型ID" prop="model_id">
          <el-input
            v-model="formData.model_id"
            placeholder="请输入模型ID"
            maxlength="100"
          />
        </el-form-item>
        
        <el-form-item label="提供商" prop="provider">
          <el-select
            v-model="formData.provider"
            placeholder="请选择提供商"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="provider in providers"
              :key="provider.value"
              :label="provider.label"
              :value="provider.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API密钥" prop="api_key">
          <el-input
            v-model="formData.api_key"
            type="password"
            placeholder="请输入API密钥"
            maxlength="255"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="API基础URL" prop="api_base">
          <el-input
            v-model="formData.api_base"
            placeholder="请输入API基础URL"
            maxlength="255"
          />
        </el-form-item>
        
        <el-form-item label="是否启用" prop="is_active">
          <el-switch
            v-model="formData.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingModel ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Setting, Edit, Delete, MoreFilled } from '@element-plus/icons-vue'
import { providerAPI } from '@/api.js'

// 响应式数据
const loading = ref(false)
const models = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const searchKeyword = ref('')

// 对话框控制
const showCreateDialog = ref(false)
const editingModel = ref(null)
const submitting = ref(false)

// 提供商列表
const providers = ref([])
const testingModel = ref(null)

// 表单数据
const formRef = ref()
const formData = ref({
  model_id: '',
  provider: '',
  api_key: '',
  api_base: '',
  is_active: true
})

// 表单验证规则
const formRules = {
  model_id: [
    { required: true, message: '请输入模型ID', trigger: 'blur' },
    { min: 1, max: 100, message: '模型ID长度在1到100个字符', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请选择提供商', trigger: 'change' }
  ]
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 获取提供商标签
const getProviderLabel = (providerValue) => {
  const provider = providers.value.find(p => p.value === providerValue)
  return provider ? provider.label : providerValue
}

// 加载模型列表
const loadModels = async (page = 1) => {
  loading.value = true
  try {
    const params = {
      page,
      model_id: searchKeyword.value || undefined
    }
    
    const response = await providerAPI.getLLMModels(params)
    // 根据后端返回的数据结构，数据在 response.data.data 中
    models.value = response.data.data.results || []
    total.value = response.data.data.count || 0
    currentPage.value = page
  } catch (error) {
    console.error('获取LLM模型列表失败:', error)
    ElMessage.error('获取LLM模型列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  loadModels(1)
}

// 处理操作菜单
const handleAction = ({ action, data }) => {
  switch (action) {
    case 'edit':
      handleEdit(data)
      break
    case 'delete':
      handleDelete(data)
      break
  }
}

// 处理编辑
const handleEdit = (model) => {
  editingModel.value = model
  formData.value = {
    model_id: model.model_id,
    provider: model.provider,
    api_key: model.api_key || '',
    api_base: model.api_base || '',
    is_active: model.is_active
  }
  showCreateDialog.value = true
}

// 处理删除
const handleDelete = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除LLM模型 "${model.model_id}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await providerAPI.deleteLLMModel(model.id)
    ElMessage.success('删除成功')
    loadModels(currentPage.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理表单提交
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    if (editingModel.value) {
      // 更新
      await providerAPI.updateLLMModel(editingModel.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      // 创建
      await providerAPI.createLLMModel(formData.value)
      ElMessage.success('创建成功')
    }
    
    showCreateDialog.value = false
    loadModels(currentPage.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交失败:', error)
      ElMessage.error('提交失败')
    }
  } finally {
    submitting.value = false
  }
}

// 加载提供商列表
const loadProviders = async () => {
  try {
    const response = await providerAPI.getLLMProviders()
    providers.value = response.data.data || []
  } catch (error) {
    console.error('获取提供商列表失败:', error)
    ElMessage.error('获取提供商列表失败')
  }
}

// 处理测试模型
const handleTest = async (model) => {
  try {
    testingModel.value = model.id
    
    const response = await providerAPI.testLLMModel(model.id)
    
    ElMessage.success('模型测试成功')
    
    // 显示测试结果
    ElMessageBox.alert(
      `测试时间: ${response.data.data.test_time}\n\n响应内容:\n${response.data.data.response}`,
      '测试结果',
      {
        confirmButtonText: '确定',
        type: 'success',
        dangerouslyUseHTMLString: false
      }
    )
  } catch (error) {
    console.error('测试模型失败:', error)
    ElMessage.error(error.response?.data?.message || '测试模型失败')
  } finally {
    testingModel.value = null
  }
}

// 页面加载时获取数据
onMounted(() => {
  loadModels()
  loadProviders()
})
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 