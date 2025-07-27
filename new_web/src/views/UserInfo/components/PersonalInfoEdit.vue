<template>
  <div class="personal-info-edit">
    <!-- 个人信息卡片 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200">
      <!-- 头部 -->
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-medium text-gray-900">个人信息编辑</h2>
            <p class="text-sm text-gray-500 mt-1">更新您的个人信息</p>
          </div>
          <div class="text-sm text-red-500" v-if="hasChanges">
            * 表示必填项
          </div>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="p-6">
        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="text-gray-500">加载中...</div>
        </div>

        <div class="max-w-2xl mx-auto">
          <!-- 用户头像区域 -->
          <div class="text-center mb-8">
            <!-- 头像显示 -->
            <div class="relative mx-auto w-24 h-24 mb-4 group">
              <!-- 如果有头像则显示头像，否则显示默认图标 -->
              <div v-if="userInfo.avatar" class="w-24 h-24 rounded-full overflow-hidden border-2 border-gray-200">
                <img 
                  :src="userInfo.avatar" 
                  :alt="displayName + '的头像'"
                  class="w-full h-full object-cover"
                />
              </div>
              <div v-else class="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center border-2 border-gray-200">
                <svg class="w-12 h-12 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"></path>
                </svg>
              </div>
              
              <!-- 头像悬浮操作按钮 -->
              <div class="absolute inset-0 bg-black bg-opacity-50 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <div class="flex space-x-2">
                  <!-- 上传/更换头像按钮 -->
                  <button
                    @click="triggerFileInput"
                    class="p-2 bg-white rounded-full shadow-lg hover:bg-gray-50 transition-colors"
                    title="上传头像"
                    :disabled="uploading"
                  >
                    <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                    </svg>
                  </button>
                  
                  <!-- 删除头像按钮（仅在有头像时显示） -->
                  <button
                    v-if="userInfo.avatar"
                    @click="handleDeleteAvatar"
                    class="p-2 bg-red-500 rounded-full shadow-lg hover:bg-red-600 transition-colors"
                    title="删除头像"
                    :disabled="deleting"
                  >
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            
            <!-- 隐藏的文件输入框 -->
            <input 
              ref="fileInput"
              type="file" 
              accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
              @change="handleFileChange"
              class="hidden"
            />
            
            <!-- 头像上传提示 -->
            <div class="text-xs text-gray-500 mb-2">
              <p>支持 JPG、PNG、GIF、WEBP 格式</p>
              <p>文件大小不超过 5MB</p>
            </div>
            
            <!-- 上传进度提示 -->
            <div v-if="uploading" class="text-sm text-blue-600 mb-2">
              <div class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                正在上传头像...
              </div>
            </div>
            
            <h3 class="text-lg font-medium text-gray-900">{{ displayName }}</h3>
          </div>

          <!-- 编辑表单 -->
          <form @submit.prevent="handleSubmit" class="space-y-6">
            <!-- 用户名 -->
            <div>
              <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
                用户名 <span class="text-red-500">*</span>
              </label>
              <input
                id="username"
                v-model="formData.username"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="请输入用户名"
                maxlength="150"
                required
              />
            </div>

            <!-- 邮箱 -->
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
                邮箱 <span class="text-red-500">*</span>
              </label>
              <input
                id="email"
                v-model="formData.email"
                type="email"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="请输入邮箱地址"
                maxlength="254"
                required
              />
            </div>

            <!-- 手机号 -->
            <div>
              <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">
                手机号
              </label>
              <input
                id="phone"
                v-model="formData.phone"
                type="tel"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="请输入手机号"
                maxlength="20"
              />
            </div>

            <!-- 操作按钮 -->
            <div class="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                @click="resetForm"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                :disabled="submitting"
              >
                重置
              </button>
              <button
                type="submit"
                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="submitting || !hasChanges"
              >
                {{ submitting ? '保存中...' : '保存更改' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 成功提示 -->
    <div 
      v-if="showSuccessMessage" 
      class="fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-md shadow-lg z-50"
    >
      <div class="flex items-center">
        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        </svg>
        个人信息更新成功！
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useUserStore } from '@/stores/user.js'
import { userAPI } from '@/api.js'

const userStore = useUserStore()

// 响应式数据
const loading = ref(true)
const submitting = ref(false)
const showSuccessMessage = ref(false)

// 用户信息
const userInfo = ref({})

// 表单数据
const formData = reactive({
  username: '',
  email: '',
  phone: ''
})

// 原始数据 (用于重置)
const originalData = ref({})

// 显示名称
const displayName = computed(() => {
  return userInfo.value.username || '用户'
})

// 是否有变更
const hasChanges = computed(() => {
  return Object.keys(formData).some(key => 
    formData[key] !== originalData.value[key]
  )
})

// 文件输入框引用
const fileInput = ref(null)

// 上传状态
const uploading = ref(false)
const deleting = ref(false)

// 头像上传
const handleFileChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  try {
    uploading.value = true
    const response = await userAPI.uploadAvatar(file)

    if (response.data.code === 200) {
      // 修复API响应字段：使用 avatar_url 而不是 avatar
      const avatarUrl = response.data.data.avatar_url
      // 添加时间戳避免浏览器缓存问题
      const avatarUrlWithTimestamp = avatarUrl + (avatarUrl.includes('?') ? '&' : '?') + 't=' + Date.now()
      
      // 更新本地状态
      userInfo.value.avatar = avatarUrlWithTimestamp
      
      // 更新全局用户状态，确保导航栏等其他组件也能同步更新
      userStore.updateUserInfo({ avatar: avatarUrlWithTimestamp })
      
      // 强制刷新所有使用头像的组件
      nextTick(() => {
        // 触发响应式更新
        userStore.userInfo.avatar = avatarUrlWithTimestamp
      })
      
      showSuccessMessage.value = true
      setTimeout(() => {
        showSuccessMessage.value = false
      }, 3000)
    } else {
      alert('上传头像失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('上传头像出错:', error)
    alert('上传头像失败，请稍后重试')
  } finally {
    uploading.value = false
    event.target.value = null // 清空文件输入框
  }
}

// 触发文件输入框
const triggerFileInput = () => {
  fileInput.value.click()
}

// 删除头像
const handleDeleteAvatar = async () => {
  if (confirm('确定要删除头像吗？')) {
    try {
      deleting.value = true
      const response = await userAPI.deleteAvatar()

      if (response.data.code === 200) {
        // 更新本地状态
        userInfo.value.avatar = null
        
        // 更新全局用户状态，确保导航栏等其他组件也能同步更新
        userStore.updateUserInfo({ avatar: null })
        
        // 强制刷新所有使用头像的组件
        nextTick(() => {
          // 触发响应式更新
          userStore.userInfo.avatar = null
        })
        
        showSuccessMessage.value = true
        setTimeout(() => {
          showSuccessMessage.value = false
        }, 3000)
      } else {
        alert('删除头像失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('删除头像出错:', error)
      alert('删除头像失败，请稍后重试')
    } finally {
      deleting.value = false
    }
  }
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    loading.value = true
    const response = await userAPI.getProfile()
    
    if (response.data.code === 200) {
      userInfo.value = response.data.data
      
      // 填充表单数据
      formData.username = userInfo.value.username || ''
      formData.email = userInfo.value.email || ''
      formData.phone = userInfo.value.phone || ''
      
      // 保存原始数据
      originalData.value = { ...formData }
    } else {
      console.error('获取用户信息失败:', response.data.message)
    }
  } catch (error) {
    console.error('获取用户信息出错:', error)
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  Object.keys(originalData.value).forEach(key => {
    formData[key] = originalData.value[key]
  })
}

// 提交表单
const handleSubmit = async () => {
  try {
    submitting.value = true
    
    // 准备提交数据
    const submitData = {
      username: formData.username.trim(),
      email: formData.email.trim(),
      phone: formData.phone.trim()
    }
    
    const response = await userAPI.updateProfile(submitData)
    
    if (response.data.code === 200) {
      // 更新用户信息
      userInfo.value = response.data.data
      
      // 更新用户store中的信息
      userStore.updateUserInfo(response.data.data)
      
      // 更新原始数据
      originalData.value = { ...formData }
      
      // 显示成功消息
      showSuccessMessage.value = true
      setTimeout(() => {
        showSuccessMessage.value = false
      }, 3000)
    } else {
      console.error('更新用户信息失败:', response.data.message)
      alert('更新失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('更新用户信息出错:', error)
    alert('更新失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 组件挂载时获取用户信息
onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
/* 组件样式 */
</style> 