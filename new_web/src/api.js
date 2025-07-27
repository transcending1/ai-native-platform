import axios from 'axios';

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_APP_BASE_API, // 从环境变量获取 API 地址
    timeout: 5000, // 设置超时时间
});

// 可以添加请求拦截器和响应拦截器
apiClient.interceptors.request.use(config => {
    // 添加token
    const token = localStorage.getItem("token")
    if(token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config;
}, error => {
    return Promise.reject(error)
})

// 响应拦截器 - 处理401错误自动跳转登录页
apiClient.interceptors.response.use(res => {
    return res
}, error => {
    // 处理401未授权错误 - Token过期或无效
    if (error.response?.status === 401) {
        console.warn('JWT Token已过期或无效，正在清除用户状态并跳转到登录页')
        
        // 清除本地存储的用户信息
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        localStorage.removeItem('rememberLogin')
        
        // 显示错误提示（异步导入避免循环依赖）
        import('element-plus').then(({ ElMessage }) => {
            ElMessage.error('登录已过期，请重新登录')
        }).catch(() => {
            // 如果ElMessage加载失败，使用原生alert
            alert('登录已过期，请重新登录')
        })
        
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

export default apiClient;