<template>
  <div>

    <!-- 配置卡片 - 垂直排列 -->
    <div class="space-y-4">
      <!-- LLM配置卡片 -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200">
        <!-- 卡片头部 - 可点击折叠 -->
        <div 
          class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
          @click="toggleLLMConfig"
        >
          <div class="flex items-center space-x-3">
            <el-icon class="text-gray-400 transition-transform" :class="{ 'rotate-90': !llmConfigCollapsed }">
              <ArrowRight />
            </el-icon>
            <div>
              <h3 class="text-lg font-semibold text-gray-900">LLM 编码模型</h3>
              <p class="text-sm text-gray-500">配置全局LLM模型参数</p>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <el-tag :type="llmConfigStatus" size="small">
              {{ llmConfigStatus === 'success' ? '已配置' : '未配置' }}
            </el-tag>
          </div>
        </div>

        <!-- LLM配置内容 - 可折叠 -->
        <div v-show="!llmConfigCollapsed" class="border-t border-gray-100">
          <div class="p-4">
            <!-- LLM配置表单 -->
            <el-form ref="llmFormRef" :model="llmForm" :rules="llmRules" label-width="100px">
              <el-form-item label="模型名称" prop="model">
                <el-input v-model="llmForm.model" placeholder="请输入模型名称" />
              </el-form-item>
              
              <el-form-item label="模型提供商" prop="model_provider">
                <el-select v-model="llmForm.model_provider" placeholder="请选择模型提供商" style="width: 100%">
                  <el-option label="OpenAI" value="openai" />
                  <el-option label="Anthropic" value="anthropic" />
                  <el-option label="Qwen" value="qwen" />
                  <el-option label="LocalAI" value="localai" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="API基础URL" prop="base_url">
                <el-input v-model="llmForm.base_url" placeholder="请输入API基础URL" />
              </el-form-item>
              
              <el-form-item label="API密钥" prop="api_key">
                <el-input v-model="llmForm.api_key" type="password" placeholder="请输入API密钥" show-password />
              </el-form-item>
              
              <el-form-item label="温度参数" prop="temperature">
                <el-slider
                  v-model="llmForm.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  show-input
                  :show-input-controls="false"
                  style="width: 100%"
                />
              </el-form-item>
              
              <el-form-item label="最大Token数" prop="max_tokens">
                <el-input-number
                  v-model="llmForm.max_tokens"
                  :min="1"
                  style="width: 100%"
                />
              </el-form-item>
            </el-form>

            <!-- LLM操作按钮 -->
            <div class="flex gap-3 mt-6">
              <el-button type="primary" @click="saveLLMConfig" :loading="llmSaving">
                保存配置
              </el-button>
              <el-button @click="testLLMConfig" :loading="llmTesting">
                测试连接
              </el-button>
            </div>

            <!-- LLM测试结果 -->
            <div v-if="llmTestResult" class="mt-4 p-3 rounded" :class="llmTestResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
              <div class="text-sm font-medium" :class="llmTestResult.success ? 'text-green-800' : 'text-red-800'">
                {{ llmTestResult.message }}
              </div>
              <div v-if="llmTestResult.response" class="mt-2 text-sm text-gray-600">
                <div class="font-medium">响应内容：</div>
                <div class="mt-1 p-2 bg-gray-100 rounded">{{ llmTestResult.response }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Embedding配置卡片 -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200">
        <!-- 卡片头部 - 可点击折叠 -->
        <div 
          class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
          @click="toggleEmbeddingConfig"
        >
          <div class="flex items-center space-x-3">
            <el-icon class="text-gray-400 transition-transform" :class="{ 'rotate-90': !embeddingConfigCollapsed }">
              <ArrowRight />
            </el-icon>
            <div>
              <h3 class="text-lg font-semibold text-gray-900">Embedding 模型</h3>
              <p class="text-sm text-gray-500">配置全局Embedding模型参数</p>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <el-tag :type="embeddingConfigStatus" size="small">
              {{ embeddingConfigStatus === 'success' ? '已配置' : '未配置' }}
            </el-tag>
          </div>
        </div>

        <!-- Embedding配置内容 - 可折叠 -->
        <div v-show="!embeddingConfigCollapsed" class="border-t border-gray-100">
          <div class="p-4">
            <!-- 已集成的Embedding代码展示 -->
            <div v-if="hasEmbeddingCode" class="space-y-4">
              <div class="flex items-center justify-between">
                <h4 class="font-medium text-gray-900">已集成的Embedding代码</h4>
                <div class="flex gap-2">
                  <el-button size="small" @click="editEmbeddingCode">
                    编辑代码
                  </el-button>
                  <el-button size="small" type="primary" @click="testCurrentEmbedding" :loading="testingCurrent">
                    测试代码
                  </el-button>
                </div>
              </div>
              
              <div>
                <CodeHighlight 
                  :code="currentEmbeddingCode" 
                  language="python"
                  :rows="15"
                />
              </div>
              
              <!-- 当前代码测试结果 -->
              <div v-if="currentTestResult" class="mt-4 p-3 rounded" :class="currentTestResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
                <div class="text-sm font-medium" :class="currentTestResult.success ? 'text-green-800' : 'text-red-800'">
                  {{ currentTestResult.message }}
                </div>
                <div v-if="currentTestResult.data" class="mt-2 text-sm text-gray-600">
                  <div class="font-medium">测试结果：</div>
                  <div class="mt-1 p-2 bg-gray-100 rounded font-mono text-xs">
                    {{ JSON.stringify(currentTestResult.data, null, 2) }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 未集成时的提示 -->
            <div v-else class="text-center py-8">
              <el-icon class="text-4xl text-gray-300 mb-4">
                <InfoFilled />
              </el-icon>
              <div class="text-lg font-medium text-gray-700 mb-2">尚未集成Embedding模型</div>
              <div class="text-sm text-gray-500 mb-4">点击下方按钮开始集成您的Embedding模型</div>
            </div>

            <!-- Embedding操作按钮 -->
            <div class="flex gap-3 mt-6">
              <el-button type="success" @click="showEmbeddingWizard = true">
                {{ hasEmbeddingCode ? '持续集成' : '集成Embedding模型' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Embedding模型集成向导对话框 -->
    <el-dialog
      v-model="showEmbeddingWizard"
      title="集成Embedding模型"
      width="80%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="space-y-6">
        <!-- 步骤指示器 -->
        <el-steps :active="currentStep" finish-status="success" class="mb-6">
          <el-step title="输入需求" description="描述您的Embedding模型需求" />
          <el-step title="AI生成" description="AI解析并生成代码" />
          <el-step title="测试验证" description="测试生成的代码" />
          <el-step title="完成集成" description="确认并保存配置" />
        </el-steps>

        <!-- 步骤1: 输入需求 -->
        <div v-if="currentStep === 0" class="space-y-4">
          <div class="text-gray-700">
            <h4 class="font-medium mb-2">请描述您的Embedding模型需求</h4>
            <p class="text-sm text-gray-500 mb-4">
              请详细描述您的Embedding模型接口信息，包括：
            </p>
            <ul class="text-sm text-gray-600 space-y-1 mb-4">
              <li>• API接口地址</li>
              <li>• 请求头信息（如Authorization Token）</li>
              <li>• 请求体格式</li>
              <li>• 响应格式</li>
              <li>• 其他特殊要求</li>
            </ul>
          </div>
          
          <el-input
            v-model="userDemand"
            type="textarea"
            :rows="8"
            placeholder="例如：
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your_token_here'
}
请求体：inputs 内嵌套文本 ['文本1','文本2']
接口：http://your-api-endpoint/embed

请实现Embedding的请求示例"
          />
          
          <div class="flex justify-between items-center">
            <div class="text-sm text-gray-500">
              <el-icon class="mr-1"><InfoFilled /></el-icon>
              AI生成代码可能需要1-2分钟，请耐心等待
            </div>
            <div class="flex gap-2">
              <el-button @click="showEmbeddingWizard = false">取消</el-button>
              <el-button type="primary" @click="generateEmbeddingCode" :loading="generatingCode">
                {{ generatingCode ? 'AI生成中...' : '开始AI生成' }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤2: AI生成结果 -->
        <div v-if="currentStep === 1" class="space-y-4">
          <div v-if="generatingCode" class="text-center py-8">
            <el-icon class="text-4xl text-blue-500 mb-4 animate-spin">
              <Loading />
            </el-icon>
            <div class="text-lg font-medium text-gray-700 mb-2">AI正在生成代码...</div>
            <div class="text-sm text-gray-500">这可能需要1-2分钟，请耐心等待</div>
          </div>
          
          <div v-else-if="generationResult" class="space-y-4">
            <div class="flex items-center justify-between">
              <h4 class="font-medium text-gray-900">AI生成结果</h4>
              <el-tag :type="generationResult.is_success ? 'success' : 'danger'">
                {{ generationResult.is_success ? '生成成功' : '生成失败' }}
              </el-tag>
            </div>
            
            <div v-if="generationResult.is_success" class="space-y-4">
              <div>
                <h5 class="font-medium text-gray-700 mb-2">生成的代码（可编辑）：</h5>
                <CodeHighlight 
                  v-model:code="generationResult.generated_code"
                  language="python"
                  :editable="true"
                  :rows="15"
                />
              </div>
            </div>
            
            <div v-else class="p-4 bg-red-50 border border-red-200 rounded">
              <p class="text-red-800">{{ generationResult.message }}</p>
            </div>
          </div>
          
          <!-- 测试结果展示 -->
          <div v-if="testResult" class="mt-4 p-4 rounded" :class="testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
            <div class="font-medium" :class="testResult.success ? 'text-green-800' : 'text-red-800'">
              {{ testResult.message }}
            </div>
            <div v-if="testResult.success && testResult.data" class="mt-3 space-y-2">
              <div class="text-sm text-gray-600">
                <span class="font-medium">测试结果：</span> {{ testResult.data.test_result }}
              </div>
              <div class="text-sm text-gray-600">
                <span class="font-medium">查询向量：</span>
                <div class="mt-1 p-2 bg-gray-100 rounded font-mono text-xs">
                  [{{ testResult.data.embedding?.slice(0, 10).join(', ') }}{{ testResult.data.embedding?.length > 10 ? '...' : '' }}]
                </div>
              </div>
              <div class="text-sm text-gray-600">
                <span class="font-medium">文档向量数量：</span> {{ testResult.data.documents_embedding?.length || 0 }}
              </div>
            </div>
          </div>
          
          <div class="flex justify-between">
            <el-button @click="currentStep = 0">上一步</el-button>
            <div class="flex gap-2">
              <el-button 
                v-if="generationResult?.is_success" 
                @click="testGeneratedEmbedding" 
                :loading="testingGenerated"
              >
                测试代码
              </el-button>
              <el-button 
                v-if="generationResult?.is_success" 
                type="primary" 
                @click="currentStep = 2"
              >
                下一步：测试验证
              </el-button>
              <el-button v-else type="primary" @click="generateEmbeddingCode" :loading="generatingCode">
                重新生成
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤3: 测试验证 -->
        <div v-if="currentStep === 2" class="space-y-4">
          <div class="text-gray-700">
            <h4 class="font-medium mb-2">测试生成的代码</h4>
            <p class="text-sm text-gray-500">点击测试按钮验证生成的代码是否能正常工作</p>
          </div>
          
          <div class="flex justify-center">
            <el-button type="primary" @click="testGeneratedEmbedding" :loading="testingGenerated" size="large">
              测试生成的代码
            </el-button>
          </div>
          
          <div v-if="testResult" class="space-y-4">
            <div class="p-4 rounded" :class="testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
              <div class="font-medium" :class="testResult.success ? 'text-green-800' : 'text-red-800'">
                {{ testResult.message }}
              </div>
              
              <div v-if="testResult.success && testResult.data" class="mt-3 space-y-2">
                <div class="text-sm text-gray-600">
                  <span class="font-medium">测试结果：</span> {{ testResult.data.test_result }}
                </div>
                <div class="text-sm text-gray-600">
                  <span class="font-medium">查询向量：</span>
                  <div class="mt-1 p-2 bg-gray-100 rounded font-mono text-xs">
                    [{{ testResult.data.embedding?.slice(0, 10).join(', ') }}{{ testResult.data.embedding?.length > 10 ? '...' : '' }}]
                  </div>
                </div>
                <div class="text-sm text-gray-600">
                  <span class="font-medium">文档向量数量：</span> {{ testResult.data.documents_embedding?.length || 0 }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="flex justify-between">
            <el-button @click="currentStep = 1">上一步</el-button>
            <el-button 
              v-if="testResult?.success" 
              type="primary" 
              @click="currentStep = 3"
            >
              下一步：完成集成
            </el-button>
            <el-button v-else type="primary" @click="testGeneratedEmbedding" :loading="testingGenerated">
              重新测试
            </el-button>
          </div>
        </div>

        <!-- 步骤4: 完成集成 -->
        <div v-if="currentStep === 3" class="space-y-4">
          <div class="text-center space-y-4">
            <el-icon class="text-6xl text-green-500">
              <CircleCheckFilled />
            </el-icon>
            <div>
              <h4 class="font-medium text-gray-900 mb-2">集成成功！</h4>
              <p class="text-gray-600">您的Embedding模型已成功集成到系统中</p>
            </div>
          </div>
          
          <div class="bg-gray-50 p-4 rounded">
            <h5 class="font-medium text-gray-700 mb-2">集成信息：</h5>
            <ul class="text-sm text-gray-600 space-y-1">
              <li>• 代码已生成并存储到Redis缓存</li>
              <li>• 测试验证通过</li>
              <li>• 可以通过统一的API接口调用</li>
              <li>• 支持embed_documents和embed_query方法</li>
            </ul>
          </div>
          
          <div class="flex justify-center">
            <el-button type="primary" @click="completeIntegration">
              完成集成
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 代码编辑对话框 -->
    <el-dialog
      v-model="showCodeEditor"
      title="编辑Embedding代码"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="space-y-4">
        <div class="text-gray-700">
          <h4 class="font-medium mb-2">编辑您的Embedding代码</h4>
          <p class="text-sm text-gray-500 mb-4">
            您可以修改已生成的代码，然后保存并测试。修改后请确保代码格式正确。
          </p>
        </div>
        
        <div>
          <CodeHighlight 
            v-model:code="editingCode"
            language="python"
            :editable="true"
            :rows="20"
          />
        </div>
        
        <div class="flex justify-end gap-2">
          <el-button @click="showCodeEditor = false">取消</el-button>
          <el-button type="primary" @click="saveEditedCode">
            保存代码
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowRight, InfoFilled, Loading } from '@element-plus/icons-vue'
import { providerAPI } from '@/api.js'
import { CircleCheckFilled } from '@element-plus/icons-vue'
import CodeHighlight from '@/components/CodeHighlight.vue'

// 响应式数据
const llmFormRef = ref()
const embeddingFormRef = ref()

// 折叠状态
const llmConfigCollapsed = ref(true)
const embeddingConfigCollapsed = ref(true)

// LLM表单数据
const llmForm = ref({
  model: '',
  model_provider: '',
  base_url: '',
  api_key: '',
  temperature: 0.1,
  max_tokens: 1024
})

// Embedding表单数据
const embeddingForm = ref({
  model: '',
  model_provider: '',
  base_url: '',
  token: ''
})

// 表单验证规则
const llmRules = {
  model: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  model_provider: [
    { required: true, message: '请选择模型提供商', trigger: 'change' }
  ]
}

const embeddingRules = {
  model: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  model_provider: [
    { required: true, message: '请选择模型提供商', trigger: 'change' }
  ]
}

// 加载状态
const llmSaving = ref(false)
const llmTesting = ref(false)
const embeddingSaving = ref(false)
const embeddingTesting = ref(false)

// 测试结果
const llmTestResult = ref(null)
const embeddingTestResult = ref(null)

// 配置状态
const llmConfigStatus = computed(() => {
  return llmForm.value.model && llmForm.value.model_provider ? 'success' : 'warning'
})

const embeddingConfigStatus = computed(() => {
  // 检查是否有Embedding代码配置
  return hasEmbeddingCode.value ? 'success' : 'warning'
})

// 检查是否有Embedding代码
const hasEmbeddingCode = ref(false)

// 当前Embedding代码
const currentEmbeddingCode = ref({
  embed_documents: '',
  embed_query: ''
})

// 折叠/展开功能
const toggleLLMConfig = () => {
  llmConfigCollapsed.value = !llmConfigCollapsed.value
}

const toggleEmbeddingConfig = () => {
  embeddingConfigCollapsed.value = !embeddingConfigCollapsed.value
}

// 加载配置
const loadConfigs = async () => {
  try {
    const response = await providerAPI.getGlobalConfigCache()
    const { llm_config, embedding_config } = response.data.data
    
    // 加载LLM配置
    if (llm_config) {
      llmForm.value = {
        model: llm_config.global_model || '',
        model_provider: llm_config.global_model_provider || '',
        base_url: llm_config.global_base_url || '',
        api_key: llm_config.global_api_key || '',
        temperature: llm_config.global_temperature || 0.1,
        max_tokens: llm_config.global_max_tokens || 1024
      }
    }
    
    // 检查Embedding代码配置
    if (embedding_config && embedding_config.__raw_code__) {
      hasEmbeddingCode.value = true
      // 保存当前的Embedding代码用于编辑
      currentEmbeddingCode.value = embedding_config.__raw_code__ || ''
    }
  } catch (error) {
    console.error('获取全局配置失败:', error)
    ElMessage.error('获取全局配置失败')
  }
}

// 保存LLM配置
const saveLLMConfig = async () => {
  try {
    await llmFormRef.value.validate()
    
    llmSaving.value = true
    await providerAPI.updateLLMConfig(llmForm.value)
    
    ElMessage.success('LLM配置保存成功')
    llmTestResult.value = null
  } catch (error) {
    console.error('保存LLM配置失败:', error)
    ElMessage.error('保存LLM配置失败')
  } finally {
    llmSaving.value = false
  }
}

// 保存Embedding配置
const saveEmbeddingConfig = async () => {
  try {
    await embeddingFormRef.value.validate()
    
    embeddingSaving.value = true
    await providerAPI.updateEmbeddingConfig(embeddingForm.value)
    
    ElMessage.success('Embedding配置保存成功')
    embeddingTestResult.value = null
  } catch (error) {
    console.error('保存Embedding配置失败:', error)
    ElMessage.error('保存Embedding配置失败')
  } finally {
    embeddingSaving.value = false
  }
}

// 测试LLM配置
const testLLMConfig = async () => {
  try {
    llmTesting.value = true
    const response = await providerAPI.testLLMConfig()
    
    llmTestResult.value = {
      success: true,
      message: response.data.message,
      response: response.data.data?.response
    }
  } catch (error) {
    console.error('测试LLM配置失败:', error)
    llmTestResult.value = {
      success: false,
      message: error.response?.data?.message || '测试LLM配置失败'
    }
  } finally {
    llmTesting.value = false
  }
}

// 测试Embedding配置
const testEmbeddingConfig = async () => {
  try {
    embeddingTesting.value = true
    const response = await providerAPI.testEmbeddingConfig()
    
    embeddingTestResult.value = {
      success: true,
      message: response.data.message,
      embedding: response.data.data?.embedding
    }
  } catch (error) {
    console.error('测试Embedding配置失败:', error)
    embeddingTestResult.value = {
      success: false,
      message: error.response?.data?.message || '测试Embedding配置失败'
    }
  } finally {
    embeddingTesting.value = false
  }
}

// Embedding模型集成向导状态
const showEmbeddingWizard = ref(false)
const currentStep = ref(0)
const userDemand = ref('')
const generationResult = ref(null)
const generatingCode = ref(false)
const testingGenerated = ref(false)
const testResult = ref(null)

// 当前代码测试状态
const testingCurrent = ref(false)
const currentTestResult = ref(null)

// 代码编辑状态
const showCodeEditor = ref(false)
const editingCode = ref('')

// 生成Embedding代码
const generateEmbeddingCode = async () => {
  if (!userDemand.value) {
    ElMessage.warning('请先描述您的Embedding模型需求')
    return
  }
  
  // 显示等待提示
  ElMessage.info('AI正在分析您的需求并生成代码，请耐心等待（可能需要1-2分钟）...')
  generatingCode.value = true
  
  try {
    const response = await providerAPI.generateEmbeddingCode(userDemand.value)
    generationResult.value = response.data.data
    if (generationResult.value.is_success) {
      currentStep.value = 1
      ElMessage.success('代码生成成功！')
    } else {
      ElMessage.error('代码生成失败，请检查需求描述')
    }
  } catch (error) {
    console.error('生成Embedding代码失败:', error)
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，AI生成代码需要较长时间，请稍后重试')
    } else {
      ElMessage.error(error.response?.data?.message || '生成Embedding代码失败')
    }
    generationResult.value = {
      is_success: false,
      message: error.response?.data?.message || '生成Embedding代码失败'
    }
  } finally {
    generatingCode.value = false
  }
}

// 测试生成的Embedding代码
const testGeneratedEmbedding = async () => {
  testingGenerated.value = true
  try {
    // 先保存编辑后的代码
    if (generationResult.value?.generated_code) {
      await providerAPI.saveEditedEmbeddingCode(generationResult.value.generated_code)
    }
    
    // 然后测试代码
    const response = await providerAPI.testGeneratedEmbedding()
    testResult.value = {
      success: true,
      message: response.data.message,
      data: response.data.data
    }
  } catch (error) {
    console.error('测试生成的Embedding代码失败:', error)
    testResult.value = {
      success: false,
      message: error.response?.data?.message || '测试生成的Embedding代码失败'
    }
  } finally {
    testingGenerated.value = false
  }
}

// 完成Embedding模型集成
const completeIntegration = () => {
  ElMessage.success('Embedding模型集成成功！')
  showEmbeddingWizard.value = false
  currentStep.value = 0
  userDemand.value = ''
  generationResult.value = null
  testResult.value = null
  // 重新加载配置以更新状态
  loadConfigs()
}

// 编辑Embedding代码
const editEmbeddingCode = () => {
  editingCode.value = currentEmbeddingCode.value
  showCodeEditor.value = true
}

// 保存编辑的代码
const saveEditedCode = async () => {
  try {
    await providerAPI.saveEditedEmbeddingCode(editingCode.value)
    currentEmbeddingCode.value = editingCode.value
    showCodeEditor.value = false
    ElMessage.success('代码保存成功！')
  } catch (error) {
    console.error('保存代码失败:', error)
    ElMessage.error(error.response?.data?.message || '保存代码失败')
  }
}

// 测试当前Embedding代码
const testCurrentEmbedding = async () => {
  testingCurrent.value = true
  try {
    const response = await providerAPI.testGeneratedEmbedding()
    currentTestResult.value = {
      success: true,
      message: response.data.message,
      data: response.data.data
    }
  } catch (error) {
    console.error('测试当前Embedding代码失败:', error)
    currentTestResult.value = {
      success: false,
      message: error.response?.data?.message || '测试当前Embedding代码失败'
    }
  } finally {
    testingCurrent.value = false
  }
}

// 页面加载时获取数据
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.el-slider {
  margin-top: 8px;
}

/* 折叠动画 */
.el-icon {
  transition: transform 0.3s ease;
}

.rotate-90 {
  transform: rotate(90deg);
}
</style> 