<template>
  <div class="h-screen bg-gray-50 flex flex-col">
    <!-- 页面头部 -->
    <div class="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
      <div class="w-full px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ botInfo.name || 'Assistant配置' }}</h1>
            <p class="text-gray-600 mt-1">配置您的AI助手行为和能力</p>
          </div>
          <el-button 
            type="primary" 
            size="default"
            @click="saveConfig"
            :loading="saving"
            class="flex items-center gap-2"
          >
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 - 三栏布局 -->
    <div class="flex-1 w-full px-4 sm:px-6 lg:px-8 py-6 overflow-hidden">
      <div class="grid grid-cols-1 lg:grid-cols-12 xl:grid-cols-12 2xl:grid-cols-16 gap-6 h-full">
        <!-- 左侧：Prompt配置 -->
        <div class="lg:col-span-3 xl:col-span-3 2xl:col-span-3 flex flex-col">
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
            <div class="p-4 border-b border-gray-200 flex-shrink-0">
              <h3 class="text-lg font-semibold text-gray-900">人设与回复逻辑</h3>
              <p class="text-sm text-gray-600 mt-1">定义Assistant的角色和行为方式</p>
            </div>
            <div class="p-4 flex-1 flex flex-col">
              <el-input
                v-model="config.prompt"
                type="textarea"
                placeholder="请输入Assistant的人设、角色定位和回复逻辑..."
                class="w-full h-full"
                resize="none"
                :autosize="{ minRows: 10 }"
                style="height: 100%;"
              />
            </div>
          </div>
        </div>

        <!-- 中间：配置面板 -->
        <div class="lg:col-span-6 xl:col-span-6 2xl:col-span-8 flex flex-col">
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
            <div class="p-4 border-b border-gray-200 flex-shrink-0">
              <h3 class="text-lg font-semibold text-gray-900">Assistant配置</h3>
              <p class="text-sm text-gray-600 mt-1">配置模型、记忆、知识库等各项参数</p>
            </div>
            <div class="p-4 space-y-4 flex-1 overflow-y-auto">
              
              <!-- 模型配置 -->
              <el-collapse v-model="activeCollapse">
                <!-- 问答模型配置 -->
                <el-collapse-item title="问答模型配置" name="chat_model">
                  <div class="space-y-4">
                    <el-form-item label="模型选择">
                      <el-select 
                        v-model="selectedChatModel" 
                        placeholder="请选择问答模型"
                        class="w-full"
                        @change="handleChatModelChange"
                      >
                        <el-option
                          v-for="model in availableModels"
                          :key="model.id"
                          :label="`${model.provider} - ${model.model_id}`"
                          :value="model.id"
                        />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="温度参数">
                      <el-slider
                        v-model="config.model_config.last_temperature"
                        :min="0"
                        :max="1"
                        :step="0.1"
                        show-input
                        :input-size="'small'"
                      />
                      <div class="text-xs text-gray-500 mt-1">控制回复的随机性，0为最确定，1为最随机</div>
                    </el-form-item>
                    
                    <el-form-item label="最大Token数">
                      <el-input-number
                        v-model="config.model_config.last_max_tokens"
                        :min="1"
                        :max="32000"
                        :step="100"
                        class="w-full"
                      />
                      <div class="text-xs text-gray-500 mt-1">控制单次回复的最大长度</div>
                    </el-form-item>
                  </div>
                </el-collapse-item>

                <!-- 知识精排模型配置 -->
                <el-collapse-item title="知识精排模型配置" name="rerank_model">
                  <div class="space-y-4">
                    <el-form-item label="模型选择">
                      <el-select 
                        v-model="selectedRerankModel" 
                        placeholder="请选择知识精排模型"
                        class="w-full"
                        @change="handleRerankModelChange"
                      >
                        <el-option
                          v-for="model in availableModels"
                          :key="model.id"
                          :label="`${model.provider} - ${model.model_id}`"
                          :value="model.id"
                        />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="温度参数">
                      <el-slider
                        v-model="config.model_config.knowledge_rerank_temperature"
                        :min="0"
                        :max="1"
                        :step="0.1"
                        show-input
                        :input-size="'small'"
                      />
                    </el-form-item>
                    
                    <el-form-item label="最大Token数">
                      <el-input-number
                        v-model="config.model_config.knowledge_rerank_max_tokens"
                        :min="1"
                        :max="32000"
                        :step="100"
                        class="w-full"
                      />
                    </el-form-item>
                  </div>
                </el-collapse-item>

                <!-- 记忆配置 -->
                <el-collapse-item title="记忆配置" name="memory">
                  <div class="space-y-4">
                    <el-form-item label="记忆最大Token数">
                      <el-input-number
                        v-model="config.memory_config.max_tokens"
                        :min="256"
                        :max="32000"
                        :step="256"
                        class="w-full"
                      />
                      <div class="text-xs text-gray-500 mt-1">多轮对话记忆中保留的最大Token数量</div>
                    </el-form-item>
                  </div>
                </el-collapse-item>

                <!-- 普通知识RAG配置 -->
                <el-collapse-item title="普通知识RAG配置" name="rag">
                  <div class="space-y-4">
                    <el-form-item label="启用RAG">
                      <el-switch v-model="config.rag_config.is_rag" />
                    </el-form-item>
                    
                    <template v-if="config.rag_config.is_rag">
                      <el-form-item label="召回文档数量">
                        <el-input-number
                          v-model="config.rag_config.retrieve_top_n"
                          :min="3"
                          :max="100"
                          class="w-full"
                        />
                      </el-form-item>
                      
                      <el-form-item label="召回文档阈值">
                        <el-slider
                          v-model="config.rag_config.retrieve_threshold"
                          :min="0"
                          :max="1"
                          :step="0.1"
                          show-input
                          :input-size="'small'"
                        />
                      </el-form-item>
                      
                      <el-form-item label="启用重排">
                        <el-switch v-model="config.rag_config.is_rerank" />
                      </el-form-item>
                      
                      <template v-if="config.rag_config.is_rerank">
                        <el-form-item label="重排数量">
                          <el-input-number
                            v-model="config.rag_config.rerank_top_n"
                            :min="3"
                            :max="100"
                            class="w-full"
                          />
                        </el-form-item>
                        
                        <el-form-item label="重排阈值">
                          <el-slider
                            v-model="config.rag_config.rerank_threshold"
                            :min="0"
                            :max="1"
                            :step="0.1"
                            show-input
                            :input-size="'small'"
                          />
                        </el-form-item>
                        
                        <el-form-item label="启用大模型重排">
                          <el-switch v-model="config.rag_config.is_llm_rerank" />
                        </el-form-item>
                      </template>
                      
                      <el-form-item label="选择知识库">
                        <el-select 
                          v-model="config.rag_config.namespace_list" 
                          multiple
                          placeholder="请选择知识库"
                          class="w-full"
                        >
                          <el-option
                            v-for="namespace in availableNamespaces"
                            :key="namespace.id"
                            :label="namespace.name"
                            :value="namespace.id.toString()"
                          />
                        </el-select>
                      </el-form-item>
                    </template>
                  </div>
                </el-collapse-item>

                <!-- 工具知识RAG配置 -->
                <el-collapse-item title="工具知识RAG配置" name="tool_rag">
                  <div class="space-y-4">
                    <el-form-item label="启用工具RAG">
                      <el-switch v-model="config.tool_config.is_rag" />
                    </el-form-item>
                    
                    <template v-if="config.tool_config.is_rag">
                      <el-form-item label="召回工具数量">
                        <el-input-number
                          v-model="config.tool_config.retrieve_top_n"
                          :min="3"
                          :max="100"
                          class="w-full"
                        />
                      </el-form-item>
                      
                      <el-form-item label="召回工具阈值">
                        <el-slider
                          v-model="config.tool_config.retrieve_threshold"
                          :min="0"
                          :max="1"
                          :step="0.1"
                          show-input
                          :input-size="'small'"
                        />
                      </el-form-item>
                      
                      <el-form-item label="启用重排">
                        <el-switch v-model="config.tool_config.is_rerank" />
                      </el-form-item>
                      
                      <template v-if="config.tool_config.is_rerank">
                        <el-form-item label="重排数量">
                          <el-input-number
                            v-model="config.tool_config.rerank_top_n"
                            :min="3"
                            :max="100"
                            class="w-full"
                          />
                        </el-form-item>
                        
                        <el-form-item label="重排阈值">
                          <el-slider
                            v-model="config.tool_config.rerank_threshold"
                            :min="0"
                            :max="1"
                            :step="0.1"
                            show-input
                            :input-size="'small'"
                          />
                        </el-form-item>
                        
                        <el-form-item label="启用大模型重排">
                          <el-switch v-model="config.tool_config.is_llm_rerank" />
                        </el-form-item>
                      </template>
                      
                      <el-form-item label="最大迭代次数">
                        <el-input-number
                          v-model="config.tool_config.max_iterations"
                          :min="1"
                          :max="10"
                          class="w-full"
                        />
                      </el-form-item>
                      
                      <el-form-item label="选择工具知识库">
                        <el-select 
                          v-model="config.tool_config.namespace_list" 
                          multiple
                          placeholder="请选择工具知识库"
                          class="w-full"
                        >
                          <el-option
                            v-for="namespace in availableNamespaces"
                            :key="namespace.id"
                            :label="namespace.name"
                            :value="namespace.id.toString()"
                          />
                        </el-select>
                      </el-form-item>
                    </template>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </div>

        <!-- 右侧：预览与调试 -->
        <div class="lg:col-span-3 xl:col-span-3 2xl:col-span-5 flex flex-col">
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-full">
            <div class="p-4 border-b border-gray-200 flex-shrink-0">
              <h3 class="text-lg font-semibold text-gray-900">预览与调试</h3>
              <p class="text-sm text-gray-600 mt-1">与Assistant进行对话测试</p>
            </div>
            <div class="flex flex-col h-full flex-1">
              <!-- 对话区域 -->
              <div class="flex-1 p-4 overflow-y-auto space-y-4 min-h-0">
                <div v-if="chatMessages.length === 0" class="text-center text-gray-500 mt-8">
                  <el-icon class="text-4xl mb-2"><ChatDotSquare /></el-icon>
                  <p>保存配置后开始与Assistant对话</p>
                </div>
                
                <div v-for="(message, index) in chatMessages" :key="index" class="flex flex-col space-y-2">
                  <!-- 用户消息 -->
                  <div v-if="message.type === 'user'" class="flex justify-end">
                    <div class="max-w-[80%] bg-blue-500 text-white rounded-lg px-3 py-2 text-sm">
                      {{ message.content }}
                    </div>
                  </div>
                  
                  <!-- AI回复 -->
                  <div v-if="message.type === 'assistant'" class="flex justify-start">
                    <div class="max-w-[80%] bg-gray-100 text-gray-900 rounded-lg px-3 py-2 text-sm">
                      {{ message.content }}
                    </div>
                  </div>
                </div>
                
                <!-- 加载中指示器 -->
                <div v-if="chatLoading" class="flex justify-start">
                  <div class="bg-gray-100 rounded-lg px-3 py-2 text-sm">
                    <el-icon class="animate-spin"><Loading /></el-icon>
                    思考中...
                  </div>
                </div>
              </div>
              
              <!-- 输入区域 -->
              <div class="p-4 border-t border-gray-200 flex-shrink-0">
                <div class="flex space-x-2">
                  <el-input
                    v-model="chatInput"
                    placeholder="输入消息与Assistant对话..."
                    @keyup.enter="sendMessage"
                    :disabled="!configSaved || chatLoading"
                  />
                  <el-button 
                    type="primary" 
                    @click="sendMessage"
                    :disabled="!configSaved || !chatInput.trim() || chatLoading"
                    :loading="chatLoading"
                  >
                    发送
                  </el-button>
                </div>
                <div v-if="!configSaved" class="text-xs text-gray-500 mt-2">
                  请先保存配置后再开始对话
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, ChatDotSquare, Loading } from '@element-plus/icons-vue'
import { botAPI } from '@/api.js'

// 路由参数
const route = useRoute()
const botId = route.params.botId

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const configSaved = ref(false)
const botInfo = ref({})
const availableModels = ref([])
const availableNamespaces = ref([])
const activeCollapse = ref([])

// 选中的模型
const selectedChatModel = ref('')
const selectedRerankModel = ref('')

// 配置数据
const config = reactive({
  prompt: '你是一个有用的AI助手',
  model_config: {
    last_model: '',
    last_model_provider: '',
    last_temperature: 0,
    last_max_tokens: 5120,
    knowledge_rerank_model: '',
    knowledge_rerank_model_provider: '',
    knowledge_rerank_temperature: 0,
    knowledge_rerank_max_tokens: 5120,
  },
  memory_config: {
    max_tokens: 2560
  },
  rag_config: {
    is_rag: true,
    retrieve_top_n: 5,
    retrieve_threshold: 0.2,
    is_rerank: true,
    rerank_top_n: 3,
    rerank_threshold: 0.4,
    is_llm_rerank: false,
    namespace_list: []
  },
  tool_config: {
    is_rag: true,
    retrieve_top_n: 5,
    retrieve_threshold: 0.2,
    is_rerank: true,
    rerank_top_n: 3,
    rerank_threshold: 0.4,
    is_llm_rerank: false,
    max_iterations: 3,
    namespace_list: []
  }
})

// 聊天相关
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const currentThreadId = ref('')

// 处理模型选择变化
const handleChatModelChange = (modelId) => {
  const model = availableModels.value.find(m => m.id === modelId)
  if (model) {
    config.model_config.last_model = model.model_id
    config.model_config.last_model_provider = model.provider
  }
}

const handleRerankModelChange = (modelId) => {
  const model = availableModels.value.find(m => m.id === modelId)
  if (model) {
    config.model_config.knowledge_rerank_model = model.model_id
    config.model_config.knowledge_rerank_model_provider = model.provider
  }
}

// 加载Bot信息
const loadBotInfo = async () => {
  try {
    loading.value = true
    const response = await botAPI.getBot(botId)
    botInfo.value = response.data
  } catch (error) {
    console.error('获取Bot信息失败:', error)
    ElMessage.error('获取Bot信息失败')
  } finally {
    loading.value = false
  }
}

// 加载Bot配置
const loadBotConfig = async () => {
  try {
    const response = await botAPI.getBotConfig(botId)
    const configData = response.data.config.configurable || {}
    
    // 更新配置数据
    if (configData.chat_bot_config?.prompt) {
      config.prompt = configData.chat_bot_config.prompt
    }
    
    if (configData.memory_config?.max_tokens) {
      config.memory_config.max_tokens = configData.memory_config.max_tokens
    }
    
    if (configData.rag_config) {
      Object.assign(config.rag_config, configData.rag_config)
    }
    
    if (configData.tool_config) {
      Object.assign(config.tool_config, configData.tool_config)
    }
    
    // 更新模型配置
    if (configData.last_model) {
      config.model_config.last_model = configData.last_model
      // 根据模型名找到对应的ID
      const model = availableModels.value.find(m => m.model_id === configData.last_model)
      if (model) {
        selectedChatModel.value = model.id
      }
    }
    
    if (configData.last_model_provider) {
      config.model_config.last_model_provider = configData.last_model_provider
    }
    
    if (configData.last_temperature !== undefined) {
      config.model_config.last_temperature = configData.last_temperature
    }
    
    if (configData.last_max_tokens) {
      config.model_config.last_max_tokens = configData.last_max_tokens
    }
    
    if (configData.knowledge_rerank_model) {
      config.model_config.knowledge_rerank_model = configData.knowledge_rerank_model
      // 根据模型名找到对应的ID
      const model = availableModels.value.find(m => m.model_id === configData.knowledge_rerank_model)
      if (model) {
        selectedRerankModel.value = model.id
      }
    }
    
    if (configData.knowledge_rerank_model_provider) {
      config.model_config.knowledge_rerank_model_provider = configData.knowledge_rerank_model_provider
    }
    
    if (configData.knowledge_rerank_temperature !== undefined) {
      config.model_config.knowledge_rerank_temperature = configData.knowledge_rerank_temperature
    }
    
    if (configData.knowledge_rerank_max_tokens) {
      config.model_config.knowledge_rerank_max_tokens = configData.knowledge_rerank_max_tokens
    }
    
  } catch (error) {
    console.error('获取Bot配置失败:', error)
    ElMessage.error('获取Bot配置失败')
  }
}

// 加载可用模型
const loadAvailableModels = async () => {
  try {
    const response = await botAPI.getAvailableModels()
    availableModels.value = response.data.models || []
  } catch (error) {
    console.error('获取模型列表失败:', error)
    ElMessage.error('获取模型列表失败')
  }
}

// 加载可用知识库
const loadAvailableNamespaces = async () => {
  try {
    const response = await botAPI.getAvailableNamespaces()
    availableNamespaces.value = response.data.namespaces || []
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    ElMessage.error('获取知识库列表失败')
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    saving.value = true
    await botAPI.updateBotConfig(botId, config)
    configSaved.value = true
    ElMessage.success('配置保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 发送消息（实际聊天功能）
const sendMessage = async () => {
  if (!chatInput.value.trim()) return
  
  const userMessage = {
    type: 'user',
    content: chatInput.value
  }
  
  chatMessages.value.push(userMessage)
  const currentInput = chatInput.value
  chatInput.value = ''
  chatLoading.value = true
  
  try {
    // 创建Assistant回复消息对象
    const assistantMessage = {
      type: 'assistant',
      content: ''
    }
    chatMessages.value.push(assistantMessage)
    
    // 调用聊天API
    const response = await botAPI.chat(botId, {
      message: currentInput,
      thread_id: currentThreadId.value || undefined
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    // 读取流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            // 更新线程ID
            if (data.thread_id && !currentThreadId.value) {
              currentThreadId.value = data.thread_id
            }
            
            // 处理流式消息
            if (data.is_partial && data.message) {
              // 更新当前助手消息的内容
              const lastMessage = chatMessages.value[chatMessages.value.length - 1]
              if (lastMessage.type === 'assistant') {
                lastMessage.content = data.message
              }
            }
            
            // 检查是否完成
            if (data.is_completed) {
              chatLoading.value = false
              break
            }
            
            // 处理错误
            if (data.error) {
              throw new Error(data.error)
            }
          } catch (parseError) {
            console.warn('解析流式数据失败:', parseError)
          }
        }
      }
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error(`发送消息失败: ${error.message}`)
    
    // 移除最后的空白助手消息
    if (chatMessages.value.length > 0 && 
        chatMessages.value[chatMessages.value.length - 1].type === 'assistant' &&
        !chatMessages.value[chatMessages.value.length - 1].content) {
      chatMessages.value.pop()
    }
  } finally {
    chatLoading.value = false
  }
}

// 页面加载时初始化数据
onMounted(async () => {
  await Promise.all([
    loadBotInfo(),
    loadAvailableModels(),
    loadAvailableNamespaces()
  ])
  
  // 加载完模型列表后再加载配置
  await loadBotConfig()
})
</script>

<style scoped>
/* 确保textarea在flex容器中正确填充高度 */
:deep(.el-textarea) {
  height: 100%;
}

:deep(.el-textarea__inner) {
  height: 100% !important;
  min-height: 100% !important;
  resize: none !important;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* 响应式布局调整 */
@media (max-width: 1024px) {
  .grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .lg\:col-span-3,
  .lg\:col-span-6 {
    grid-column: span 1;
  }
}

/* 超大屏幕布局优化 */
@media (min-width: 1536px) {
  .grid {
    grid-template-columns: repeat(16, minmax(0, 1fr));
  }
}

/* 确保在小屏幕上也有合适的高度 */
@media (max-height: 600px) {
  .flex-1 {
    min-height: 300px;
  }
}

/* 大屏幕下的最小宽度优化 */
@media (min-width: 1280px) {
  .w-full {
    min-width: 100%;
  }
}

/* 响应式字体和间距调整 */
@media (min-width: 1920px) {
  .px-4 {
    padding-left: 2rem;
    padding-right: 2rem;
  }
  
  .gap-6 {
    gap: 2rem;
  }
}
</style>