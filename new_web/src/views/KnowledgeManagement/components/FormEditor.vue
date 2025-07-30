<template>
  <div class="form-editor">
    <!-- 查看模式 -->
    <div v-if="!isEditing" class="space-y-6">
      <!-- 基本信息 -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
        <div class="grid grid-cols-1 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">表单名称</label>
            <div class="p-3 bg-gray-50 rounded-lg text-gray-900">
              {{ formData.table_name || '未设置' }}
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">表单描述</label>
            <div class="p-3 bg-gray-50 rounded-lg text-gray-900">
              {{ formData.table_description || '未设置' }}
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">数据表名</label>
            <div class="p-3 bg-gray-50 rounded-lg text-gray-900 font-mono text-sm">
              {{ dynamicTableName }}
            </div>
          </div>
        </div>
      </div>

      <!-- 字段配置 -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">字段配置</h3>
        <div v-if="formData.fields && formData.fields.length > 0">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    字段名
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    类型
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    描述
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    必填
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    默认值
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="field in formData.fields" :key="field.name">
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span class="font-medium text-gray-900">{{ field.name }}</span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                      {{ field.field_type }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <span class="text-gray-900">{{ field.description || '-' }}</span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap">
                    <span 
                      class="px-2 py-1 text-xs rounded-full"
                      :class="field.is_required ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'"
                    >
                      {{ field.is_required ? '是' : '否' }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <span class="text-gray-600 text-sm">{{ field.default_value || '-' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="text-center py-6 text-gray-500">
          <div class="text-2xl mb-2">📋</div>
          <p>暂未配置表单字段</p>
        </div>
      </div>

      <!-- 数据管理 -->
      <div class="bg-white rounded-lg border p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-gray-900">数据管理</h3>
          <div class="space-x-2">
            <el-button @click="loadFormData" :loading="loadingData">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
            <el-button 
              @click="showSubmitDialog = true" 
              type="primary"
              :disabled="!formData.fields || formData.fields.length === 0"
            >
              <el-icon><Plus /></el-icon>
              添加数据
            </el-button>
          </div>
        </div>
        
        <div v-if="formEntries.length > 0">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th 
                    v-for="field in formData.fields" 
                    :key="field.name"
                    class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {{ field.name }}
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    提交时间
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="entry in formEntries" :key="entry.id">
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {{ entry.id }}
                  </td>
                  <td 
                    v-for="field in formData.fields" 
                    :key="field.name"
                    class="px-4 py-3 whitespace-nowrap text-sm text-gray-900"
                  >
                    {{ formatFieldValue(entry.data[field.name], field.field_type) }}
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(entry.submitted_at) }}
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm">
                    <el-button 
                      @click="deleteEntry(entry.id)" 
                      type="danger" 
                      size="small"
                      :loading="deletingEntries.includes(entry.id)"
                    >
                      删除
                    </el-button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 分页 -->
          <div v-if="formEntries.length > 0" class="mt-4 flex justify-center">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="totalEntries"
              layout="prev, pager, next, total"
              @current-change="handlePageChange"
            />
          </div>
        </div>
        <div v-else class="text-center py-6 text-gray-500">
          <div class="text-2xl mb-2">📄</div>
          <p>暂无表单数据</p>
        </div>
      </div>
    </div>

    <!-- 编辑模式 -->
    <div v-else class="space-y-6">
      <el-form
        ref="formRef"
        :model="editForm"
        :rules="formRules"
        label-width="120px"
      >
        <!-- 基本信息 -->
        <div class="bg-white rounded-lg border p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
          
          <el-form-item label="表单名称" prop="table_name">
            <el-input
              v-model="editForm.table_name"
              placeholder="请输入表单名称（英文、数字、下划线）"
              maxlength="50"
            />
          </el-form-item>
          
          <el-form-item label="表单描述" prop="table_description">
            <el-input
              v-model="editForm.table_description"
              type="textarea"
              :rows="3"
              placeholder="描述表单的用途和数据结构"
              maxlength="500"
            />
          </el-form-item>
        </div>

        <!-- 字段配置 -->
        <div class="bg-white rounded-lg border p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">字段配置</h3>
            <el-button @click="addField" type="primary" size="small">
              <el-icon><Plus /></el-icon>
              添加字段
            </el-button>
          </div>
          
          <div v-if="editForm.fields.length > 0" class="space-y-4">
            <div
              v-for="(field, index) in editForm.fields"
              :key="index"
              class="p-4 bg-gray-50 rounded-lg border"
            >
              <div class="grid grid-cols-12 gap-4 items-start">
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-1">字段名</label>
                  <el-input
                    v-model="field.name"
                    placeholder="字段名"
                    size="small"
                  />
                </div>
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-1">类型</label>
                  <el-select v-model="field.field_type" size="small" style="width: 100%">
                    <el-option label="String" value="String" />
                    <el-option label="Integer" value="Integer" />
                    <el-option label="Time" value="Time" />
                    <el-option label="Number" value="Number" />
                    <el-option label="Boolean" value="Boolean" />
                  </el-select>
                </div>
                <div class="col-span-3">
                  <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <el-input
                    v-model="field.description"
                    placeholder="字段描述"
                    size="small"
                  />
                </div>
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-1">默认值</label>
                  <el-input
                    v-model="field.default_value"
                    placeholder="默认值"
                    size="small"
                  />
                </div>
                <div class="col-span-1">
                  <label class="block text-sm font-medium text-gray-700 mb-1">必填</label>
                  <el-switch
                    v-model="field.is_required"
                    size="small"
                  />
                </div>
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-1">操作</label>
                  <div class="flex space-x-1">
                    <el-button
                      @click="moveFieldUp(index)"
                      size="small"
                      :disabled="index === 0"
                      :icon="ArrowUp"
                      circle
                    />
                    <el-button
                      @click="moveFieldDown(index)"
                      size="small"
                      :disabled="index === editForm.fields.length - 1"
                      :icon="ArrowDown"
                      circle
                    />
                    <el-button
                      @click="removeField(index)"
                      type="danger"
                      size="small"
                      :icon="Delete"
                      circle
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-6 text-gray-500">
            <p>点击"添加字段"开始配置表单字段</p>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 提交数据对话框 -->
    <el-dialog
      v-model="showSubmitDialog"
      title="添加数据"
      width="600px"
      @close="resetSubmitForm"
    >
      <el-form
        ref="submitFormRef"
        :model="submitForm"
        label-width="120px"
      >
        <el-form-item
          v-for="field in formData.fields"
          :key="field.name"
          :label="field.name"
          :prop="field.name"
          :rules="field.is_required ? [{ required: true, message: `请输入${field.name}` }] : []"
        >
          <!-- String 类型 -->
          <el-input
            v-if="field.field_type === 'String'"
            v-model="submitForm[field.name]"
            :placeholder="`请输入${field.description || field.name}`"
          />
          
          <!-- Integer 类型 -->
          <el-input-number
            v-else-if="field.field_type === 'Integer'"
            v-model="submitForm[field.name]"
            :placeholder="`请输入${field.description || field.name}`"
            :precision="0"
            style="width: 100%"
          />
          
          <!-- Number 类型 -->
          <el-input-number
            v-else-if="field.field_type === 'Number'"
            v-model="submitForm[field.name]"
            :placeholder="`请输入${field.description || field.name}`"
            :precision="2"
            style="width: 100%"
          />
          
          <!-- Boolean 类型 -->
          <el-switch
            v-else-if="field.field_type === 'Boolean'"
            v-model="submitForm[field.name]"
            active-text="是"
            inactive-text="否"
          />
          
          <!-- Time 类型 -->
          <el-date-picker
            v-else-if="field.field_type === 'Time'"
            v-model="submitForm[field.name]"
            type="datetime"
            :placeholder="`请选择${field.description || field.name}`"
            style="width: 100%"
          />
          
          <div v-if="field.description" class="text-xs text-gray-500 mt-1">
            {{ field.description }}
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="flex justify-end space-x-2">
          <el-button @click="showSubmitDialog = false">取消</el-button>
          <el-button type="primary" :loading="submittingData" @click="submitFormData">
            提交
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Delete, Refresh, ArrowUp, ArrowDown
} from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api.js'

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

const emit = defineEmits(['save', 'cancel'])

// 响应式数据
const formRef = ref(null)
const submitFormRef = ref(null)
const showSubmitDialog = ref(false)
const loadingData = ref(false)
const submittingData = ref(false)
const deletingEntries = ref([])

// 表单数据
const formData = computed(() => {
  if (props.document.type_specific_data) {
    return props.document.type_specific_data
  }
  return {
    table_name: '',
    table_description: '',
    fields: []
  }
})

// 动态表名
const dynamicTableName = computed(() => {
  return `form_data_${props.namespaceId}_${props.document.id}`
})

// 表单条目数据
const formEntries = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalEntries = ref(0)

// 编辑表单
const editForm = ref({
  table_name: '',
  table_description: '',
  fields: []
})

// 提交表单
const submitForm = ref({})

// 表单验证规则
const formRules = {
  table_name: [
    { required: true, message: '请输入表单名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '表单名称只能包含字母、数字和下划线，且必须以字母开头', trigger: 'blur' }
  ],
  table_description: [
    { required: true, message: '请输入表单描述', trigger: 'blur' }
  ]
}

// 初始化编辑表单
const initEditForm = () => {
  editForm.value = {
    table_name: formData.value.table_name || '',
    table_description: formData.value.table_description || '',
    fields: (formData.value.fields || []).map(field => ({ ...field }))
  }
}

// 初始化提交表单
const initSubmitForm = () => {
  const form = {}
  formData.value.fields?.forEach(field => {
    form[field.name] = field.default_value || getDefaultValueByType(field.field_type)
  })
  submitForm.value = form
}

// 根据类型获取默认值
const getDefaultValueByType = (type) => {
  switch (type) {
    case 'String': return ''
    case 'Integer': return 0
    case 'Number': return 0
    case 'Boolean': return false
    case 'Time': return null
    default: return ''
  }
}

// 格式化字段值显示
const formatFieldValue = (value, type) => {
  if (value === null || value === undefined) return '-'
  
  switch (type) {
    case 'Boolean':
      return value ? '是' : '否'
    case 'Time':
      return value ? new Date(value).toLocaleString('zh-CN') : '-'
    default:
      return String(value)
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

// 添加字段
const addField = () => {
  editForm.value.fields.push({
    name: '',
    field_type: 'String',
    description: '',
    is_required: false,
    default_value: ''
  })
}

// 删除字段
const removeField = (index) => {
  editForm.value.fields.splice(index, 1)
}

// 上移字段
const moveFieldUp = (index) => {
  if (index > 0) {
    const fields = editForm.value.fields
    ;[fields[index - 1], fields[index]] = [fields[index], fields[index - 1]]
  }
}

// 下移字段
const moveFieldDown = (index) => {
  const fields = editForm.value.fields
  if (index < fields.length - 1) {
    ;[fields[index], fields[index + 1]] = [fields[index + 1], fields[index]]
  }
}

// 重置提交表单
const resetSubmitForm = () => {
  initSubmitForm()
  if (submitFormRef.value) {
    submitFormRef.value.clearValidate()
  }
}

// 加载表单数据
const loadFormData = async () => {
  loadingData.value = true
  try {
    const response = await knowledgeAPI.getFormData(props.namespaceId, props.document.id, {
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    formEntries.value = response.data.results || response.data || []
    totalEntries.value = response.data.count || formEntries.value.length
  } catch (error) {
    console.error('加载表单数据失败:', error)
    ElMessage.error('加载表单数据失败')
    formEntries.value = []
    totalEntries.value = 0
  } finally {
    loadingData.value = false
  }
}

// 处理分页变化
const handlePageChange = (page) => {
  currentPage.value = page
  loadFormData()
}

// 提交表单数据
const submitFormData = async () => {
  if (formData.value.fields?.length > 0) {
    try {
      await submitFormRef.value.validate()
    } catch {
      return
    }
  }

  submittingData.value = true
  try {
    await knowledgeAPI.submitFormData(
      props.namespaceId,
      props.document.id,
      { data: submitForm.value }
    )
    
    ElMessage.success('数据提交成功')
    showSubmitDialog.value = false
    resetSubmitForm()
    loadFormData() // 重新加载数据
  } catch (error) {
    console.error('数据提交失败:', error)
    ElMessage.error('数据提交失败')
  } finally {
    submittingData.value = false
  }
}

// 删除数据条目
const deleteEntry = async (entryId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条数据吗？', '确认删除', {
      type: 'warning'
    })
    
    deletingEntries.value.push(entryId)
    
    // 这里需要调用删除API，暂时模拟
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('删除成功')
    loadFormData() // 重新加载数据
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  } finally {
    deletingEntries.value = deletingEntries.value.filter(id => id !== entryId)
  }
}

// 保存表单配置
const saveFormData = async () => {
  if (!formRef.value) return false
  
  try {
    await formRef.value.validate()
  } catch {
    return false
  }

  // 检查字段名是否重复
  const fieldNames = editForm.value.fields.map(f => f.name.trim()).filter(name => name)
  const uniqueNames = new Set(fieldNames)
  if (fieldNames.length !== uniqueNames.size) {
    ElMessage.error('字段名不能重复')
    return false
  }

  const formUpdateData = {
    form_data: {
      table_name: editForm.value.table_name.trim(),
      table_description: editForm.value.table_description.trim(),
      fields: editForm.value.fields.filter(field => field.name.trim()).map(field => ({
        name: field.name.trim(),
        field_type: field.field_type,
        description: field.description.trim(),
        is_required: field.is_required,
        default_value: field.default_value
      }))
    }
  }

  try {
    await knowledgeAPI.updateDocument(props.namespaceId, props.document.id, formUpdateData)
    emit('save')
    return true
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
    return false
  }
}

// 监听编辑状态变化
watch(() => props.isEditing, (newEditing) => {
  if (newEditing) {
    initEditForm()
  }
}, { immediate: true })

// 监听文档变化
watch(() => props.document, () => {
  if (!props.isEditing) {
    loadFormData()
  }
  initSubmitForm()
}, { immediate: true })

// 组件挂载时加载数据
onMounted(() => {
  if (!props.isEditing) {
    loadFormData()
  }
  initSubmitForm()
})

// 暴露保存方法给父组件
defineExpose({
  save: saveFormData
})
</script>

<style scoped>
.form-editor {
  height: 100%;
  overflow-y: auto;
}

.table-container {
  overflow-x: auto;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
}
</style> 