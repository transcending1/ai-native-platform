import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const userInfo = ref(null)
  
  // 登录状态
  const isLoggedIn = ref(false)
  
  // 登录Token
  const token = ref('')
  
  // Refresh Token
  const refreshToken = ref('')

  // 初始化用户状态（从localStorage恢复）
  const initUserState = () => {
    const savedToken = localStorage.getItem('token')
    const savedRefreshToken = localStorage.getItem('refreshToken')
    const savedUserInfo = localStorage.getItem('userInfo')
    const rememberLogin = localStorage.getItem('rememberLogin')
    
    if (savedToken && savedRefreshToken && rememberLogin === 'true') {
      token.value = savedToken
      refreshToken.value = savedRefreshToken
      isLoggedIn.value = true
      
      if (savedUserInfo) {
        try {
          userInfo.value = JSON.parse(savedUserInfo)
        } catch (error) {
          console.error('解析用户信息失败:', error)
          logout() // 清除无效数据
        }
      }
    } else if (savedToken || savedRefreshToken || savedUserInfo || rememberLogin) {
      // 如果数据不完整，清除所有相关数据
      logout()
    }
  }

  // 检查Token是否可能过期（简单的本地检查）
  const isTokenLikelyExpired = () => {
    if (!token.value || !isLoggedIn.value) {
      return true
    }
    // 这里可以添加更复杂的token过期检查逻辑
    // 比如解析JWT token的过期时间
    return false
  }

  // 登录
  const login = (userData, authToken, refreshTokenValue, rememberMe = false) => {
    userInfo.value = userData
    token.value = authToken
    refreshToken.value = refreshTokenValue
    isLoggedIn.value = true
    
    // 保存到localStorage
    localStorage.setItem('token', authToken)
    localStorage.setItem('refreshToken', refreshTokenValue)
    localStorage.setItem('userInfo', JSON.stringify(userData))
    
    // 保存记住登录状态
    if (rememberMe) {
      localStorage.setItem('rememberLogin', 'true')
    } else {
      localStorage.removeItem('rememberLogin')
    }
  }

  // 更新token（用于token刷新）
  const updateToken = (newToken, newRefreshToken) => {
    token.value = newToken
    if (newRefreshToken) {
      refreshToken.value = newRefreshToken
      localStorage.setItem('refreshToken', newRefreshToken)
    }
    localStorage.setItem('token', newToken)
  }

  // 登出
  const logout = () => {
    userInfo.value = null
    token.value = ''
    refreshToken.value = ''
    isLoggedIn.value = false
    
    // 清除localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('rememberLogin')
  }

  // 更新用户信息
  const updateUserInfo = (newUserInfo) => {
    userInfo.value = { ...userInfo.value, ...newUserInfo }
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
  }

  return {
    userInfo,
    isLoggedIn,
    token,
    refreshToken,
    initUserState,
    login,
    logout,
    updateToken,
    updateUserInfo,
    isTokenLikelyExpired
  }
}) 