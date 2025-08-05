<template>
  <div class="tool-editor">
    <!-- 查看模式 -->
    <div v-if="!isEditing" class="space-y-6 relative">
      <!-- 基本信息 -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
        <div class="grid grid-cols-1 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">工具名称</label>
            <div class="p-3 bg-gray-50 rounded-lg text-gray-900">
              {{ toolData.name || '未设置' }}
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">工具描述</label>
            <div class="p-3 bg-gray-50 rounded-lg text-gray-900">
              {{ toolData.description || '未设置' }}
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">工具类型</label>
            <div class="p-3 bg-gray-50 rounded-lg text-gray-900">
              {{ toolData.tool_type || 'dynamic' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 输入参数 -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">输入参数</h3>
        <div v-if="inputParameters.length > 0" class="space-y-3">
          <div
            v-for="param in inputParameters"
            :key="param.name"
            class="p-4 bg-gray-50 rounded-lg border"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center space-x-2">
                  <span class="font-medium text-gray-900">{{ param.name }}</span>
                  <span 
                    class="px-2 py-1 text-xs rounded-full"
                    :class="param.required ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'"
                  >
                    {{ param.required ? '必填' : '可选' }}
                  </span>
                  <span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    {{ param.type }}
                  </span>
                </div>
                <p v-if="param.description" class="text-sm text-gray-600 mt-1">
                  {{ param.description }}
                </p>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-6 text-gray-500">
          <div class="text-2xl mb-2">📝</div>
          <p>暂未配置输入参数</p>
        </div>
      </div>

      <!-- 输出参数 -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">输出参数</h3>
        <div v-if="outputParameters.length > 0" class="space-y-3">
          <div
            v-for="param in outputParameters"
            :key="param.name"
            class="p-4 bg-gray-50 rounded-lg border"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center space-x-2">
                  <span class="font-medium text-gray-900">{{ param.name }}</span>
                  <span 
                    class="px-2 py-1 text-xs rounded-full"
                    :class="param.required ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'"
                  >
                    {{ param.required ? '必填' : '可选' }}
                  </span>
                  <span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                    {{ param.type }}
                  </span>
                </div>
                <p v-if="param.description" class="text-sm text-gray-600 mt-1">
                  {{ param.description }}
                </p>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-6 text-gray-500">
          <div class="text-2xl mb-2">📤</div>
          <p>暂未配置输出参数</p>
        </div>
      </div>

      <!-- 模板配置 -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">模板配置</h3>
        
        <!-- Jinja2模板 -->
        <div class="mb-6">
          <h4 class="text-base font-medium text-gray-900 mb-2">Jinja2模板</h4>
          <div v-if="toolData.output_schema_jinja2_template" class="p-3 bg-gray-50 rounded-lg font-mono text-sm">
            {{ toolData.output_schema_jinja2_template }}
          </div>
          <div v-else class="text-center py-4 text-gray-500">
            <p>暂未配置Jinja2模板</p>
          </div>
        </div>
        
        <!-- HTML模板 -->
        <div>
          <h4 class="text-base font-medium text-gray-900 mb-2">HTML模板</h4>
          <div v-if="toolData.html_template" class="p-3 bg-gray-50 rounded-lg font-mono text-sm max-h-32 overflow-y-auto">
            {{ toolData.html_template }}
          </div>
          <div v-else class="text-center py-4 text-gray-500">
            <p>暂未配置HTML模板</p>
          </div>
        </div>
      </div>

      <!-- 示例 -->
      <div class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">使用示例</h3>
        <div v-if="toolData.few_shots && toolData.few_shots.length > 0" class="space-y-3">
          <div
            v-for="(shot, index) in toolData.few_shots"
            :key="index"
            class="p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500"
          >
            <p class="text-gray-900">{{ shot }}</p>
          </div>
        </div>
        <div v-else class="text-center py-6 text-gray-500">
          <div class="text-2xl mb-2">💡</div>
          <p>暂未配置使用示例</p>
        </div>
      </div>

      <!-- 代码 -->
      <div v-if="toolData.tool_type === 'dynamic'" class="bg-white rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">工具代码</h3>
        <div v-if="toolCode" class="relative">
          <pre class="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto text-sm font-mono"><code>{{ toolCode }}</code></pre>
        </div>
        <div v-else class="text-center py-6 text-gray-500">
          <div class="text-2xl mb-2">💻</div>
          <p>暂未配置工具代码</p>
        </div>
      </div>

      <!-- 右上角执行按钮 -->
      <div class="absolute top-4 right-4 md:top-6 md:right-6 z-10">
        <el-button 
          @click="showExecuteDialog = true" 
          type="primary" 
          size="large"
          class="shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
        >
          <el-icon class="mr-1"><CaretRight /></el-icon>
          <span class="hidden sm:inline">执行工具</span>
          <span class="sm:hidden">执行</span>
        </el-button>
      </div>
    </div>

    <!-- 编辑模式 -->
    <div v-else class="space-y-6 relative">
      <!-- 右上角执行按钮 -->
      <div class="absolute top-4 right-4 md:top-6 md:right-6 z-10">
        <el-button 
          @click="showExecuteDialog = true" 
          type="primary" 
          size="large"
          class="shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
        >
          <el-icon class="mr-1"><CaretRight /></el-icon>
          <span class="hidden sm:inline">执行工具</span>
          <span class="sm:hidden">执行</span>
        </el-button>
      </div>
      <el-form
        ref="formRef"
        :model="editForm"
        :rules="formRules"
        label-width="120px"
      >
        <!-- 基本信息 -->
        <div class="bg-white rounded-lg border p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
          
          <el-form-item label="工具名称" prop="name">
            <el-input
              v-model="editForm.name"
              placeholder="请输入工具名称"
              maxlength="100"
            />
          </el-form-item>
          
          <el-form-item label="工具描述" prop="description">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="3"
              placeholder="描述工具的功能和用途"
              maxlength="500"
            />
          </el-form-item>
          
          <el-form-item label="工具类型">
            <el-select v-model="editForm.tool_type" style="width: 100%">
              <el-option label="动态工具" value="dynamic" />
            </el-select>
          </el-form-item>
        </div>

        <!-- 输入参数配置 -->
        <div class="bg-white rounded-lg border p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">输入参数</h3>
            <el-button @click="addInputParameter" type="primary" size="small">
              <el-icon><Plus /></el-icon>
              添加参数
            </el-button>
          </div>
          
          <div v-if="editForm.inputParameters.length > 0" class="space-y-4">
            <div
              v-for="(param, index) in editForm.inputParameters"
              :key="'input-' + index"
              class="p-4 bg-gray-50 rounded-lg border"
            >
              <div class="grid grid-cols-12 gap-4 items-start">
                <div class="col-span-3">
                  <label class="block text-sm font-medium text-gray-700 mb-1">参数名</label>
                  <el-input
                    v-model="param.name"
                    placeholder="参数名"
                    size="small"
                  />
                </div>
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-1">类型</label>
                  <el-select v-model="param.type" size="small" style="width: 100%">
                    <el-option label="string" value="string" />
                    <el-option label="int" value="integer" />
                    <el-option label="float" value="number" />
                    <el-option label="bool" value="boolean" />
                  </el-select>
                </div>
                <div class="col-span-5">
                  <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <el-input
                    v-model="param.description"
                    placeholder="参数描述"
                    size="small"
                  />
                </div>
                <div class="col-span-1">
                  <label class="block text-sm font-medium text-gray-700 mb-1">必填</label>
                  <el-switch
                    v-model="param.required"
                    size="small"
                  />
                </div>
                <div class="col-span-1">
                  <label class="block text-sm font-medium text-gray-700 mb-1">操作</label>
                  <el-button
                    @click="removeInputParameter(index)"
                    type="danger"
                    size="small"
                    :icon="Delete"
                    circle
                  />
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-6 text-gray-500">
            <p>点击"添加参数"开始配置输入参数</p>
          </div>
        </div>

        <!-- 输出参数配置 -->
        <div class="bg-white rounded-lg border p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">输出参数</h3>
            <el-button @click="addOutputParameter" type="primary" size="small">
              <el-icon><Plus /></el-icon>
              添加参数
            </el-button>
          </div>
          
          <div v-if="editForm.outputParameters.length > 0" class="space-y-4">
            <div
              v-for="(param, index) in editForm.outputParameters"
              :key="'output-' + index"
              class="p-4 bg-gray-50 rounded-lg border"
            >
              <div class="grid grid-cols-12 gap-4 items-start">
                <div class="col-span-3">
                  <label class="block text-sm font-medium text-gray-700 mb-1">参数名</label>
                  <el-input
                    v-model="param.name"
                    placeholder="参数名"
                    size="small"
                  />
                </div>
                <div class="col-span-2">
                  <label class="block text-sm font-medium text-gray-700 mb-1">类型</label>
                  <el-select v-model="param.type" size="small" style="width: 100%">
                    <el-option label="string" value="string" />
                    <el-option label="int" value="integer" />
                    <el-option label="float" value="number" />
                    <el-option label="bool" value="boolean" />
                  </el-select>
                </div>
                <div class="col-span-5">
                  <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                  <el-input
                    v-model="param.description"
                    placeholder="参数描述"
                    size="small"
                  />
                </div>
                <div class="col-span-1">
                  <label class="block text-sm font-medium text-gray-700 mb-1">必填</label>
                  <el-switch
                    v-model="param.required"
                    size="small"
                  />
                </div>
                <div class="col-span-1">
                  <label class="block text-sm font-medium text-gray-700 mb-1">操作</label>
                  <el-button
                    @click="removeOutputParameter(index)"
                    type="danger"
                    size="small"
                    :icon="Delete"
                    circle
                  />
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-6 text-gray-500">
            <p>点击"添加参数"开始配置输出参数</p>
          </div>
        </div>

        <!-- 模板配置 -->
        <div class="bg-white rounded-lg border p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">模板配置</h3>
          
          <el-form-item label="Jinja2模板" prop="jinja2_template">
            <el-input
              v-model="editForm.jinja2_template"
              type="textarea"
              :rows="3"
              placeholder="例如：{{ result }}处理完成，状态：{{ status }}"
              class="font-mono text-sm"
            />
            <div class="text-xs text-gray-500 mt-1">
              用于将输出参数渲染为人类可读的文本，支持Jinja2语法
            </div>
          </el-form-item>
          
          <el-form-item label="HTML模板" prop="html_template">
            <el-input
              v-model="editForm.html_template"
              type="textarea"
              :rows="6"
              placeholder="例如：<div class='result'>结果：{{ result }}</div>"
              class="font-mono text-sm"
            />
            <div class="text-xs text-gray-500 mt-1">
              用于在Web前端优雅展示工具结果，支持HTML和Jinja2语法
            </div>
          </el-form-item>
        </div>

        <!-- 使用示例 -->
        <div class="bg-white rounded-lg border p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-900">使用示例</h3>
            <el-button @click="addExample" type="primary" size="small">
              <el-icon><Plus /></el-icon>
              添加示例
            </el-button>
          </div>
          
          <div v-if="editForm.few_shots.length > 0" class="space-y-3">
            <div
              v-for="(shot, index) in editForm.few_shots"
              :key="index"
              class="flex items-center space-x-2"
            >
              <el-input
                v-model="editForm.few_shots[index]"
                placeholder="请输入使用示例"
                class="flex-1"
              />
              <el-button
                @click="removeExample(index)"
                type="danger"
                size="small"
                :icon="Delete"
                circle
              />
            </div>
          </div>
          <div v-else class="text-center py-6 text-gray-500">
            <p>点击"添加示例"开始配置使用示例</p>
          </div>
        </div>

        <!-- 代码编辑 -->
        <div v-if="editForm.tool_type === 'dynamic'" class="bg-white rounded-lg border p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">工具代码</h3>
          <div class="space-y-4">
            <div class="text-sm text-gray-600">
              <el-icon class="mr-1"><InfoFilled /></el-icon>
              编写Python代码来实现工具的功能。可以使用输入参数，抛出ToolException来处理错误。
            </div>
            <el-input
              v-model="editForm.code"
              type="textarea"
              :rows="12"
              placeholder="# 请输入Python代码&#10;# 示例：&#10;if not param.startswith('expected'):&#10;    raise ToolException('参数不符合要求')&#10;result = f'处理结果: {param}'"
              class="font-mono text-sm"
            />
          </div>
        </div>
      </el-form>
    </div>

    <!-- 工具执行对话框 -->
    <el-dialog
      v-model="showExecuteDialog"
      title="执行工具"
      width="900px"
      :close-on-click-modal="false"
      @close="resetExecuteForm"
    >
      <el-tabs v-model="activeExecuteTab" type="border-card">
        <!-- 输入参数配置 -->
        <el-tab-pane label="输入参数" name="input">
          <el-form
            ref="executeFormRef"
            :model="executeForm"
            label-width="120px"
          >
            <div v-if="inputParameters.length > 0">
              <el-form-item
                v-for="param in inputParameters"
                :key="param.name"
                :label="param.name"
                :prop="param.name"
                :rules="param.required ? [{ required: true, message: `请输入${param.name}` }] : []"
              >
                <el-input
                  v-model="executeForm[param.name]"
                  :placeholder="`请输入${param.description || param.name}`"
                  :type="param.type === 'number' || param.type === 'integer' ? 'number' : 'text'"
                />
                <div v-if="param.description" class="text-xs text-gray-500 mt-1">
                  {{ param.description }}
                </div>
              </el-form-item>
            </div>
            <div v-else class="text-center py-4 text-gray-500">
              此工具无需输入参数
            </div>
          </el-form>
        </el-tab-pane>

        <!-- 执行结果 -->
        <el-tab-pane label="执行结果" name="result">
          <div v-if="executeResult">
            <!-- 结果类型选择 -->
            <div class="mb-4">
              <el-radio-group v-model="resultDisplayType" size="small">
                <el-radio-button label="json">JSON结果</el-radio-button>
                <el-radio-button label="jinja2">文本渲染</el-radio-button>
                <el-radio-button label="html">HTML渲染</el-radio-button>
              </el-radio-group>
            </div>

            <!-- 显示结果 -->
            <div class="border rounded-lg overflow-hidden">
              <div v-if="resultDisplayType === 'json'" class="bg-gray-900 text-green-400 p-6 font-mono text-sm overflow-auto max-h-96">
                <pre>{{ JSON.stringify(executeResult.raw_data || executeResult.content, null, 2) }}</pre>
              </div>
              <div v-else-if="resultDisplayType === 'jinja2'" class="bg-gray-50 p-6 rounded-lg">
                <div class="text-gray-800 whitespace-pre-wrap">{{ executeResult.content }}</div>
              </div>
              <div v-else-if="resultDisplayType === 'html'" class="bg-white p-6 rounded-lg" v-html="executeResult.content">
              </div>
            </div>
          </div>
          <div v-else class="text-center py-12 text-gray-500">
            <div class="text-4xl mb-4">🔧</div>
            <p class="text-lg mb-2">等待执行结果</p>
            <p class="text-sm">请在左侧输入参数后点击执行按钮</p>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <div class="flex justify-between items-center">
          <div class="text-sm text-gray-600">
            <span class="mr-3">输出格式：</span>
            <el-radio-group v-model="executeOutputType" size="small">
              <el-radio label="json">JSON</el-radio>
              <el-radio label="jinja2">文本</el-radio>
              <el-radio label="html">HTML</el-radio>
            </el-radio-group>
          </div>
          <div class="space-x-2">
            <el-button @click="showExecuteDialog = false">取消</el-button>
            <el-button type="primary" :loading="executing" @click="executeToolAction">
              {{ executing ? '执行中...' : '执行工具' }}
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus, Delete, CaretRight, InfoFilled
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
const executeFormRef = ref(null)
const showExecuteDialog = ref(false)
const executing = ref(false)
const executeResult = ref(null)
const activeExecuteTab = ref('input')
const executeOutputType = ref('json')
const resultDisplayType = ref('json')

// 工具数据
const toolData = computed(() => {
  console.log('ToolEditor 接收到的document数据:', props.document) // 调试日志
  
  // 优先从 tool_data 字段获取数据，其次是 type_specific_data
  const data = props.document.tool_data || props.document.type_specific_data || {}
  
  console.log('ToolEditor 解析的工具数据:', data) // 调试日志
  
  return {
    name: data.name || '',
    description: data.description || '',
    input_schema: data.input_schema || { type: 'object', properties: {}, required: [] },
    output_schema: data.output_schema || { type: 'object', properties: {}, required: [] },
    output_schema_jinja2_template: data.output_schema_jinja2_template || '',
    html_template: data.html_template || '',
    few_shots: data.few_shots || [],
    tool_type: data.tool_type || 'dynamic',
    extra_params: data.extra_params || {}
  }
})

// 提取输入参数
const inputParameters = computed(() => {
  const schema = toolData.value.input_schema || {}
  const properties = schema.properties || {}
  const required = schema.required || []
  
  return Object.entries(properties).map(([name, config]) => ({
    name,
    type: config.type || 'string',
    description: config.description || '',
    required: required.includes(name)
  }))
})

// 提取输出参数
const outputParameters = computed(() => {
  const schema = toolData.value.output_schema || {}
  const properties = schema.properties || {}
  const required = schema.required || []
  
  return Object.entries(properties).map(([name, config]) => ({
    name,
    type: config.type || 'string',
    description: config.description || '',
    required: required.includes(name)
  }))
})

// 工具代码
const toolCode = computed(() => {
  return toolData.value.extra_params?.code || ''
})

// 编辑表单
const editForm = ref({
  name: '',
  description: '',
  tool_type: 'dynamic',
  inputParameters: [],
  outputParameters: [],
  jinja2_template: '',
  html_template: '',
  few_shots: [],
  code: ''
})

// 执行表单
const executeForm = ref({})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入工具名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入工具描述', trigger: 'blur' }
  ]
}

// 初始化编辑表单
const initEditForm = () => {
  editForm.value = {
    name: toolData.value.name || '',
    description: toolData.value.description || '',
    tool_type: toolData.value.tool_type || 'dynamic',
    inputParameters: inputParameters.value.map(p => ({ ...p })),
    outputParameters: outputParameters.value.map(p => ({ ...p })),
    jinja2_template: toolData.value.output_schema_jinja2_template || '',
    html_template: toolData.value.html_template || '',
    few_shots: [...(toolData.value.few_shots || [])],
    code: toolCode.value
  }
}

// 添加输入参数
const addInputParameter = () => {
  editForm.value.inputParameters.push({
    name: '',
    type: 'string',
    description: '',
    required: false
  })
}

// 删除输入参数
const removeInputParameter = (index) => {
  editForm.value.inputParameters.splice(index, 1)
}

// 添加输出参数
const addOutputParameter = () => {
  editForm.value.outputParameters.push({
    name: '',
    type: 'string',
    description: '',
    required: false
  })
}

// 删除输出参数
const removeOutputParameter = (index) => {
  editForm.value.outputParameters.splice(index, 1)
}

// 添加示例
const addExample = () => {
  editForm.value.few_shots.push('')
}

// 删除示例
const removeExample = (index) => {
  editForm.value.few_shots.splice(index, 1)
}

// 重置执行表单
const resetExecuteForm = () => {
  executeForm.value = {}
  executeResult.value = null
  activeExecuteTab.value = 'input'
  if (executeFormRef.value) {
    executeFormRef.value.clearValidate()
  }
}

// 执行工具
const executeToolAction = async () => {
  if (inputParameters.value.length > 0) {
    try {
      await executeFormRef.value.validate()
    } catch {
      return
    }
  }

  executing.value = true
  try {
    const response = await knowledgeAPI.executeTool(
      props.namespaceId,
      props.document.id,
      { 
        input_data: executeForm.value,
        output_type: executeOutputType.value
      }
    )
    
    executeResult.value = response.data
    activeExecuteTab.value = 'result'
    resultDisplayType.value = executeOutputType.value
    
    ElMessage.success('工具执行成功')
    
    // 可以显示执行结果
    console.log('执行结果:', response.data)
  } catch (error) {
    console.error('工具执行失败:', error)
    ElMessage.error('工具执行失败')
  } finally {
    executing.value = false
  }
}

// 保存工具配置
const saveToolData = async () => {
  if (!formRef.value) return false
  
  try {
    await formRef.value.validate()
  } catch {
    return false
  }

  // 构建输入schema
  const inputProperties = {}
  const inputRequired = []
  
  editForm.value.inputParameters.forEach(param => {
    if (param.name.trim()) {
      inputProperties[param.name.trim()] = {
        type: param.type,
        description: param.description.trim()
      }
      if (param.required) {
        inputRequired.push(param.name.trim())
      }
    }
  })

  // 构建输出schema
  const outputProperties = {}
  const outputRequired = []
  
  editForm.value.outputParameters.forEach(param => {
    if (param.name.trim()) {
      outputProperties[param.name.trim()] = {
        type: param.type,
        description: param.description.trim()
      }
      if (param.required) {
        outputRequired.push(param.name.trim())
      }
    }
  })

  const toolUpdateData = {
    tool_data: {
      name: editForm.value.name.trim(),
      description: editForm.value.description.trim(),
      input_schema: {
        type: 'object',
        properties: inputProperties,
        required: inputRequired
      },
      output_schema: {
        type: 'object',
        properties: outputProperties,
        required: outputRequired
      },
      output_schema_jinja2_template: editForm.value.jinja2_template.trim(),
      html_template: editForm.value.html_template.trim(),
      few_shots: editForm.value.few_shots.filter(shot => shot.trim()),
      tool_type: editForm.value.tool_type,
      extra_params: {
        code: editForm.value.code
      }
    }
  }

  try {
    await knowledgeAPI.updateDocument(props.namespaceId, props.document.id, toolUpdateData)
    // 不需要 emit('save')，因为保存是通过 DocumentViewer.handleSave 流程触发的
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

// 监听文档数据变化，确保数据更新后编辑表单也同步更新
watch(() => props.document, (newDocument) => {
  console.log('ToolEditor 监听到文档数据变化:', newDocument)
  if (props.isEditing) {
    // 如果当前处于编辑状态，重新初始化编辑表单
    initEditForm()
  }
}, { deep: true })

// 暴露保存方法给父组件
defineExpose({
  save: saveToolData
})
</script>

<style scoped>
.tool-editor {
  height: 100%;
  overflow-y: auto;
}

:deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

pre code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  line-height: 1.5;
}
</style> 