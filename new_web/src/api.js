import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 180000, // 3分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(config => {
  // 从localStorage获取token
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  return config
}, error => {
  return Promise.reject(error)
})

// 响应拦截器 - 处理401错误自动跳转登录页
apiClient.interceptors.response.use(res => {
  return res
}, async error => {
  const originalRequest = error.config
  
  // 处理401未授权错误 - Token过期或无效
  if (error.response?.status === 401 && !originalRequest._retry) {
    originalRequest._retry = true
    
    // 尝试使用refresh token刷新
    const refreshToken = localStorage.getItem('refreshToken')
    const rememberLogin = localStorage.getItem('rememberLogin')
    
    if (refreshToken && rememberLogin === 'true') {
      try {
        console.log('Token已过期，尝试刷新...')
        
        // 调用刷新token接口
        const refreshResponse = await apiClient.post('/user/refresh/', {
          refresh: refreshToken
        })
        
        if (refreshResponse.data.access) {
          // 更新token
          const newToken = refreshResponse.data.access
          const newRefreshToken = refreshResponse.data.refresh
          
          // 更新localStorage
          localStorage.setItem('token', newToken)
          if (newRefreshToken) {
            localStorage.setItem('refreshToken', newRefreshToken)
          }
          
          // 更新请求头
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          
          // 更新Pinia store（异步导入避免循环依赖）
          import('@/stores/user').then(({ useUserStore }) => {
            const userStore = useUserStore()
            userStore.updateToken(newToken, newRefreshToken)
          }).catch(err => {
            console.error('更新用户状态失败:', err)
          })
          
          console.log('Token刷新成功，重试原请求')
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        console.error('Token刷新失败:', refreshError)
        // 刷新失败，清除用户状态并跳转登录页
      }
    }
    
    // 如果刷新失败或没有refresh token，清除用户状态并跳转登录页
    console.warn('JWT Token已过期或无效，正在清除用户状态并跳转到登录页')
    
    // 清除本地存储的用户信息
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('rememberLogin')
    
    // 显示错误提示
    ElMessage.error('登录已过期，请重新登录')
    
    // 更新Pinia store状态（异步导入避免循环依赖）
    import('@/stores/user').then(({ useUserStore }) => {
      const userStore = useUserStore()
      userStore.logout()
    }).catch(err => {
      console.error('清除用户状态失败:', err)
    })
    
    // 如果当前不在登录页，则跳转到登录页
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }
  
  return Promise.reject(error)
})

// 用户认证相关API
export const authAPI = {
  // 用户登录
  login: (data) => {
    return apiClient.post('/user/login/', {
      username: data.username,
      password: data.password,
      remember_me: data.remember_me || false
    })
  },
  
  // 刷新token
  refreshToken: (refreshToken) => {
    return apiClient.post('/user/refresh/', {
      refresh: refreshToken
    })
  }
}

// 用户信息相关API
export const userAPI = {
  // 获取当前用户信息
  getProfile: () => {
    return apiClient.get('/user/profile/')
  },

  // 更新用户信息
  updateProfile: (data) => {
    return apiClient.put('/user/update_profile/', data)
  },

  // 用户登出
  logout: (refreshToken) => {
    return apiClient.post('/user/logout/', {
      refresh: refreshToken
    })
  },

  // 上传头像
  uploadAvatar: (avatarFile) => {
    const formData = new FormData()
    formData.append('avatar', avatarFile)
    return apiClient.post('/user/upload_avatar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除头像
  deleteAvatar: () => {
    return apiClient.delete('/user/delete_avatar/')
  }
}

// 用户管理相关API（管理员权限）
export const userManagementAPI = {
  // 获取用户列表
  getUserList: (params = {}) => {
    return apiClient.get('/user/admin/management/', { params })
  },

  // 获取用户详情
  getUserDetail: (id) => {
    return apiClient.get(`/user/admin/management/${id}/`)
  },

  // 创建用户
  createUser: (data) => {
    return apiClient.post('/user/admin/management/', data)
  },

  // 更新用户信息
  updateUser: (id, data) => {
    return apiClient.put(`/user/admin/management/${id}/`, data)
  },

  // 删除用户
  deleteUser: (id) => {
    return apiClient.delete(`/user/admin/management/${id}/`)
  },

  // 切换用户状态（启用/禁用）
  toggleUserStatus: (id) => {
    return apiClient.post(`/user/admin/management/${id}/toggle_status/`)
  },

  // 重置用户密码
  resetUserPassword: (id, data) => {
    return apiClient.post(`/user/admin/management/${id}/reset_password/`, data)
  },

  // 上传用户头像
  uploadUserAvatar: (id, avatarFile) => {
    const formData = new FormData()
    formData.append('avatar', avatarFile)
    return apiClient.post(`/user/admin/management/${id}/upload_avatar/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除用户头像
  deleteUserAvatar: (id) => {
    return apiClient.delete(`/user/admin/management/${id}/delete_avatar/`)
  }
}

// 知识库管理相关API
export const knowledgeAPI = {
  // 获取知识库列表
  getNamespaces: (params = {}) => {
    return apiClient.get('/knowledge/namespaces/', { params })
  },

  // 获取知识库详情
  getNamespace: (id) => {
    return apiClient.get(`/knowledge/namespaces/${id}/`)
  },

  // 创建知识库
  createNamespace: (data) => {
    return apiClient.post('/knowledge/namespaces/', data)
  },

  // 更新知识库
  updateNamespace: (id, data) => {
    return apiClient.put(`/knowledge/namespaces/${id}/`, data)
  },

  // 部分更新知识库
  patchNamespace: (id, data) => {
    return apiClient.patch(`/knowledge/namespaces/${id}/`, data)
  },

  // 删除知识库
  deleteNamespace: (id) => {
    return apiClient.delete(`/knowledge/namespaces/${id}/`)
  },

  // 更新知识库基本信息
  updateBasicInfo: (id, data) => {
    return apiClient.patch(`/knowledge/namespaces/${id}/update_basic/`, data)
  },

  // 添加协作者
  addCollaborator: (id, data) => {
    return apiClient.post(`/knowledge/namespaces/${id}/add_collaborator/`, data)
  },

  // 更新协作者权限
  updateCollaborator: (id, userId, data) => {
    return apiClient.patch(`/knowledge/namespaces/${id}/collaborators/${userId}/`, data)
  },

  // 移除协作者
  removeCollaborator: (id, userId) => {
    return apiClient.delete(`/knowledge/namespaces/${id}/collaborators/${userId}/`)
  },

  // 文档管理相关API
  // 获取文档列表
  getDocuments: (namespaceId, params = {}) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/documents/`, { params })
  },

  // 获取文档详情
  getDocument: (namespaceId, documentId) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/`)
  },

  // 创建文档
  createDocument: (namespaceId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/documents/`, data)
  },

  // 更新文档
  updateDocument: (namespaceId, documentId, data) => {
    return apiClient.put(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/`, data)
  },

  // 删除文档
  deleteDocument: (namespaceId, documentId) => {
    return apiClient.delete(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/`)
  },

  // 移动文档
  moveDocument: (namespaceId, documentId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/move/`, data)
  },

  // 获取文档树
  getDocumentTree: (namespaceId) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/documents/tree/`)
  },

  // 分类管理相关API
  // 获取分类列表
  getCategories: (namespaceId, params = {}) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/categories/`, { params })
  },

  // 创建分类
  createCategory: (namespaceId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/categories/`, data)
  },

  // 更新分类
  updateCategory: (namespaceId, categoryId, data) => {
    return apiClient.put(`/knowledge/namespaces/${namespaceId}/categories/${categoryId}/`, data)
  },

  // 删除分类
  deleteCategory: (namespaceId, categoryId) => {
    return apiClient.delete(`/knowledge/namespaces/${namespaceId}/categories/${categoryId}/`)
  },

  // 标签管理相关API
  // 获取标签列表
  getTags: (namespaceId, params = {}) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/tags/`, { params })
  },

  // 创建标签
  createTag: (namespaceId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/tags/`, data)
  },

  // 评论相关API
  // 获取评论列表
  getComments: (namespaceId, documentId, params = {}) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/comments/`, { params })
  },

  // 创建评论
  createComment: (namespaceId, documentId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/comments/`, data)
  },

  // 版本管理相关API
  // 获取版本列表
  getVersions: (namespaceId, documentId, params = {}) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/versions/`, { params })
  },

  // 创建版本
  createVersion: (namespaceId, documentId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/versions/`, data)
  },

  // 工具知识相关API
  // 执行工具
  executeTool: (namespaceId, documentId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/execute_tool/`, data)
  },

  // 获取工具执行历史
  getToolExecutions: (namespaceId, documentId, params = {}) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/tool_executions/`, { params })
  },

  // AI智能生成工具
  generateToolByAI: (namespaceId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/documents/generate_tool_by_ai/`, data)
  },

  // 表单知识相关API
  // 提交表单数据
  submitFormData: (namespaceId, documentId, data) => {
    return apiClient.post(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/submit_form_data/`, data)
  },

  // 获取表单数据
  getFormData: (namespaceId, documentId, params = {}) => {
    return apiClient.get(`/knowledge/namespaces/${namespaceId}/documents/${documentId}/form_data/`, { params })
  }
}

// Provider管理相关API
export const providerAPI = {
  // 全局配置缓存
  getGlobalConfigCache: () => apiClient.get('/provider/global-config-cache/get_configs/'),
  updateLLMConfig: (data) => apiClient.post('/provider/global-config-cache/update_llm_config/', data),
  updateEmbeddingConfig: (data) => apiClient.post('/provider/global-config-cache/update_embedding_config/', data),
  testLLMConfig: () => apiClient.post('/provider/global-config-cache/test_llm_config/'),
  testEmbeddingConfig: () => apiClient.post('/provider/global-config-cache/test_embedding_config/'),
  
  // Embedding代码生成和测试
  generateEmbeddingCode: (userDemand) => apiClient.post('/provider/global-config-cache/generate_embedding_code/', { user_demand: userDemand }, { timeout: 180000 }), // 3分钟超时
  testGeneratedEmbedding: () => apiClient.post('/provider/global-config-cache/test_generated_embedding/'),
  saveEditedEmbeddingCode: (code) => apiClient.post('/provider/global-config-cache/save_edited_embedding_code/', { code }),

  // LLM模型
  getLLMModels: (params) => apiClient.get('/provider/llm-models/', { params }),
  getLLMModel: (id) => apiClient.get(`/provider/llm-models/${id}/`),
  createLLMModel: (data) => apiClient.post('/provider/llm-models/', data),
  updateLLMModel: (id, data) => apiClient.put(`/provider/llm-models/${id}/`, data),
  deleteLLMModel: (id) => apiClient.delete(`/provider/llm-models/${id}/`),
  testLLMModel: (id) => apiClient.post(`/provider/llm-models/${id}/test_model/`),
  getLLMProviders: () => apiClient.get('/provider/llm-models/get_providers/'),
}

// Bot管理相关API
export const botAPI = {
  // 获取Bot列表
  getBots: (params = {}) => {
    return apiClient.get('/bot/bots/', { params })
  },

  // 获取Bot详情
  getBot: (id) => {
    return apiClient.get(`/bot/bots/${id}/`)
  },

  // 创建Bot
  createBot: (data) => {
    return apiClient.post('/bot/bots/', data)
  },

  // 更新Bot
  updateBot: (id, data) => {
    return apiClient.put(`/bot/bots/${id}/`, data)
  },

  // 部分更新Bot
  patchBot: (id, data) => {
    return apiClient.patch(`/bot/bots/${id}/`, data)
  },

  // 删除Bot
  deleteBot: (id) => {
    return apiClient.delete(`/bot/bots/${id}/`)
  },

  // 更新Bot基本信息
  updateBasicInfo: (id, data) => {
    return apiClient.patch(`/bot/bots/${id}/update_basic/`, data)
  },

  // 添加协作者
  addCollaborator: (id, data) => {
    return apiClient.post(`/bot/bots/${id}/add_collaborator/`, data)
  },

  // 更新协作者权限
  updateCollaborator: (id, userId, data) => {
    return apiClient.patch(`/bot/bots/${id}/collaborators/${userId}/`, data)
  },

  // 移除协作者
  removeCollaborator: (id, userId) => {
    return apiClient.delete(`/bot/bots/${id}/collaborators/${userId}/`)
  },

  // 获取协作者列表
  getCollaborators: (id) => {
    return apiClient.get(`/bot/bots/${id}/collaborators/`)
  },

  // 从LangGraph同步Bots
  syncFromLangGraph: () => {
    return apiClient.post('/bot/bots/sync_from_langgraph/')
  },

  // 获取Bot配置
  getBotConfig: (id) => {
    return apiClient.get(`/bot/bots/${id}/get_config/`)
  },

  // 更新Bot配置
  updateBotConfig: (id, data) => {
    return apiClient.post(`/bot/bots/${id}/update_config/`, data)
  },

  // 获取可用模型列表
  getAvailableModels: () => {
    return apiClient.get('/bot/bots/available_models/')
  },

  // 获取可用知识库列表
  getAvailableNamespaces: () => {
    return apiClient.get('/bot/bots/available_namespaces/')
  },

  // 创建聊天线程
  createThread: (id) => {
    return apiClient.post(`/bot/bots/${id}/create_thread/`)
  },

  // 发送聊天消息（支持流式响应）
  chat: (id, data) => {
    return fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/bot/bots/${id}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(data)
    })
  }
}

export default apiClient;