<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 页面头部 -->
    <div class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">我的Assistants</h1>
            <p class="text-gray-600 mt-1">管理您的AI助手和协作内容</p>
          </div>
          <el-button 
            type="primary" 
            size="default"
            @click="showCreateDialog = true"
            class="flex items-center gap-2"
          >
            <span>+</span>
            新建Assistant
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 搜索和筛选区 -->
      <div class="mb-6">
        <div class="flex items-center gap-4">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索Assistant名称 (Ctrl+K)"
            size="default"
            style="width: 300px"
            clearable
            @input="handleSearch"
            @clear="handleSearch"
            class="flex-shrink-0"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="accessTypeFilter"
            placeholder="访问权限"
            clearable
            @change="handleSearch"
            style="width: 150px"
          >
            <el-option label="协作者可访问" value="collaborators" />
            <el-option label="所有人可访问" value="public" />
          </el-select>

          <el-button 
            type="info" 
            size="default"
            @click="handleSyncFromLangGraph"
            :loading="syncing"
            class="flex items-center gap-2"
          >
            <el-icon><Refresh /></el-icon>
            同步Assistant
          </el-button>
        </div>
        
        <!-- 搜索结果统计 -->
        <div v-if="searchKeyword || accessTypeFilter" class="mt-3 flex items-center justify-between">
          <div class="text-sm text-gray-500">
            <span v-if="searchKeyword">搜索关键词: "{{ searchKeyword }}"</span>
            <span v-if="accessTypeFilter" class="ml-2">权限过滤: {{ accessTypeFilter === 'public' ? '所有人可访问' : '协作者可访问' }}</span>
            <span class="ml-2">共找到 {{ total }} 个Assistant</span>
          </div>
          <el-button 
            size="small" 
            type="info" 
            @click="clearFilters"
            class="flex items-center gap-1"
          >
            <el-icon><Delete /></el-icon>
            清空筛选
          </el-button>
        </div>
      </div>

      <!-- Bot列表 -->
      <div v-loading="loading" element-loading-text="加载中...">
        <div v-if="bots.length === 0 && !loading" class="text-center py-12">
          <div v-if="searchKeyword || accessTypeFilter" class="text-gray-400 text-lg mb-4">
            没有找到匹配的Assistant
          </div>
          <div v-else class="text-gray-400 text-lg mb-4">
            暂无Assistant
          </div>
          <el-button v-if="!searchKeyword && !accessTypeFilter" type="primary" @click="showCreateDialog = true">
            创建您的第一个Assistant
          </el-button>
          <el-button v-else type="info" @click="clearFilters">
            清空筛选条件
          </el-button>
        </div>
        
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="bot in bots"
            :key="bot.id"
            class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
          >
            <!-- Bot头像 -->
            <div class="relative h-32 bg-gradient-to-br from-purple-50 to-indigo-100 rounded-t-lg overflow-hidden">
              <img
                v-if="bot.avatar"
                :src="bot.avatar"
                :alt="bot.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="flex items-center justify-center h-full">
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
                      <!-- 只有有编辑权限的用户才能看到编辑相关选项 -->
                      <template v-if="bot.can_edit">
                        <el-dropdown-item :command="{action: 'edit', data: bot}">
                          <el-icon><Edit /></el-icon>
                          重命名
                        </el-dropdown-item>
                        <el-dropdown-item :command="{action: 'permission', data: bot}">
                          <el-icon><User /></el-icon>
                          权限
                        </el-dropdown-item>
                        <el-dropdown-item :command="{action: 'settings', data: bot}">
                          <el-icon><Setting /></el-icon>
                          更多设置
                        </el-dropdown-item>
                        <!-- 只有创建者才能删除Bot -->
                        <el-dropdown-item 
                          v-if="isCreator(bot)"
                          :command="{action: 'delete', data: bot}"
                          divided
                          class="text-red-600"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </template>
                      
                      <!-- 只读权限用户只能查看基本信息 -->
                      <template v-else>
                        <el-dropdown-item disabled>
                          <el-icon><View /></el-icon>
                          只读权限
                        </el-dropdown-item>
                      </template>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- Bot信息 -->
            <div class="p-4">
              <div class="flex items-start justify-between mb-2">
                <h3 class="text-lg font-semibold text-gray-900 line-clamp-1">
                  {{ bot.name }}
                </h3>
                <div class="flex items-center text-xs text-gray-500 ml-2">
                  <el-icon class="mr-1">
                    <span v-if="bot.access_type === 'public'">🌍</span>
                    <span v-else>🔒</span>
                  </el-icon>
                  {{ bot.access_type === 'public' ? '公开' : '私有' }}
                </div>
              </div>
              
              <p class="text-gray-600 text-sm mb-3 line-clamp-2">
                {{ bot.description || '暂无描述' }}
              </p>
              
              <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                <div class="flex items-center">
                  <el-icon class="mr-1"><User /></el-icon>
                  {{ bot.collaborator_count }} 位协作者
                </div>
                <span>{{ formatDate(bot.updated_at) }}</span>
              </div>
              

              
              <!-- 操作按钮 -->
              <div class="flex justify-end">
                <el-button 
                  type="primary" 
                  size="small"
                  @click.stop="handleEnterBot(bot)"
                >
                  进入Assistant
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
            layout="total, sizes, prev, pager, next, jumper"
            :page-sizes="[12, 24, 36, 48]"
            @current-change="loadBots"
            @size-change="handlePageSizeChange"
          />
        </div>
      </div>
    </div>

    <!-- 新建Bot对话框 -->
    <CreateBotDialog 
      v-model="showCreateDialog"
      @success="handleCreateSuccess"
    />

    <!-- Bot设置对话框 -->
    <BotSettingsDialog
      v-model="showSettingsDialog"
      :bot="selectedBot"
      @success="handleUpdateSuccess"
    />

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="showRenameDialog"
      title="重命名Assistant"
      width="400px"
    >
      <el-form @submit.prevent="handleRename">
        <el-form-item label="Assistant名称">
          <el-input
            v-model="newName"
            placeholder="请输入Assistant名称"
            maxlength="255"
            show-word-limit
            @keyup.enter="handleRename"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRenameDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRename" :loading="renaming">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Edit, User, Setting, Delete, MoreFilled, View, Refresh } from '@element-plus/icons-vue'
import { botAPI } from '@/api.js'
import { useUserStore } from '@/stores/user.js'
import CreateBotDialog from './components/CreateBotDialog.vue'
import BotSettingsDialog from './components/BotSettingsDialog.vue'

// 防抖函数
const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 路由和用户store
const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const syncing = ref(false)
const bots = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const searchKeyword = ref('')
const accessTypeFilter = ref('')
const showSearchSuggestions = ref(false)

// 对话框控制
const showCreateDialog = ref(false)
const showSettingsDialog = ref(false)
const showRenameDialog = ref(false)
const selectedBot = ref(null)

// 重命名相关
const newName = ref('')
const renaming = ref(false)

// 判断当前用户是否是指定Bot的创建者
const isCreator = (bot) => {
  return bot.creator && userStore.userInfo && 
         bot.creator.id === userStore.userInfo.id
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 加载Bot列表
const loadBots = async (page = 1) => {
  loading.value = true
  try {
    const params = {
      page,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      access_type: accessTypeFilter.value || undefined
    }
    
    // 移除undefined的参数
    Object.keys(params).forEach(key => {
      if (params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await botAPI.getBots(params)
    bots.value = response.data.results
    total.value = response.data.count
    currentPage.value = page
  } catch (error) {
    console.error('获取Bot列表失败:', error)
    ElMessage.error('获取Assistant列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理（防抖）
const handleSearch = debounce(() => {
  currentPage.value = 1
  loadBots(1)
}, 500)

// 处理页面大小变化
const handlePageSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadBots(1)
}

// 清空筛选条件
const clearFilters = () => {
  searchKeyword.value = ''
  accessTypeFilter.value = ''
  currentPage.value = 1
  loadBots(1)
}

// 同步LangGraph中的Assistants
const handleSyncFromLangGraph = async () => {
  syncing.value = true
  try {
    const response = await botAPI.syncFromLangGraph()
    ElMessage.success(`同步成功！新增 ${response.data.synced_count} 个Assistant`)
    loadBots(currentPage.value)
  } catch (error) {
    console.error('同步Assistant失败:', error)
    ElMessage.error('同步Assistant失败')
  } finally {
    syncing.value = false
  }
}

// 处理操作菜单
const handleAction = ({ action, data }) => {
  selectedBot.value = data
  
  switch (action) {
    case 'edit':
      newName.value = data.name
      showRenameDialog.value = true
      break
    case 'permission':
      // 这里可以添加简单的权限切换，或者打开设置对话框
      showSettingsDialog.value = true
      break
    case 'settings':
      showSettingsDialog.value = true
      break
    case 'delete':
      handleDelete(data)
      break
  }
}

// 处理重命名
const handleRename = async () => {
  if (!newName.value.trim()) {
    ElMessage.warning('请输入Assistant名称')
    return
  }
  
  renaming.value = true
  try {
    await botAPI.updateBasicInfo(selectedBot.value.id, {
      name: newName.value.trim()
    })
    
    ElMessage.success('重命名成功')
    showRenameDialog.value = false
    loadBots(currentPage.value)
  } catch (error) {
    console.error('重命名失败:', error)
    ElMessage.error('重命名失败')
  } finally {
    renaming.value = false
  }
}

// 处理删除
const handleDelete = async (bot) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除Assistant "${bot.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await botAPI.deleteBot(bot.id)
    ElMessage.success('删除成功')
    loadBots(currentPage.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理创建成功
const handleCreateSuccess = () => {
  showCreateDialog.value = false
  loadBots(1)
}

// 处理更新成功
const handleUpdateSuccess = () => {
  showSettingsDialog.value = false
  loadBots(currentPage.value)
}

// 处理进入Bot
const handleEnterBot = (bot) => {
  // 这里可以根据需要跳转到Bot的详情页面或调试界面
  ElMessage.info(`即将进入Assistant: ${bot.name}`)
  // router.push({
  //   name: 'BotDetail',
  //   params: {
  //     botId: bot.id
  //   }
  // })
}

// 页面加载时获取数据
onMounted(() => {
  loadBots()
  
  // 添加快捷键支持
  const handleKeydown = (event) => {
    // Ctrl/Cmd + K 聚焦搜索框
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
      event.preventDefault()
      const searchInput = document.querySelector('input[placeholder="搜索Assistant名称"]')
      if (searchInput) {
        searchInput.focus()
      }
    }
  }
  
  document.addEventListener('keydown', handleKeydown)
  
  // 清理事件监听器
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })
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
