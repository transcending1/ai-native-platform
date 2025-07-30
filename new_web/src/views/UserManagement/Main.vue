<template>
  <div class="user-management min-h-screen bg-gray-50">
    <!-- 页面标题和操作区域 -->
    <div class="bg-white p-4 lg:p-6 rounded-lg shadow-sm mb-6">
      <div class="flex flex-col lg:flex-row lg:justify-between lg:items-center mb-4 gap-4">
        <h1 class="text-xl lg:text-2xl font-bold text-gray-900">用户管理</h1>
        <div class="flex flex-wrap gap-3">
          <el-button 
            type="primary" 
            icon="Plus" 
            @click="handleAdd"
            class="px-4 py-2 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 flex items-center justify-center"
          >
            新增
          </el-button>
          <el-button 
            icon="Refresh" 
            @click="handleRefresh"
            class="px-4 py-2 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 flex items-center justify-center"
          >
            刷新
          </el-button>
        </div>
      </div>

      <!-- 搜索筛选区域 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-4">
        <el-input
          v-model="searchForm.username"
          placeholder="请输入用户名"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
          class="w-full"
        />
        <el-input
          v-model="searchForm.phone"
          placeholder="请输入手机号"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
          class="w-full"
        />
        <el-input
          v-model="searchForm.email"
          placeholder="请输入邮箱"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
          class="w-full"
        />
        <el-input
          v-model="searchForm.id"
          placeholder="请输入用户ID"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
          class="w-full"
        />
        <el-select
          v-model="searchForm.gender"
          placeholder="请选择性别"
          clearable
          @change="handleSearch"
          class="w-full"
        >
          <el-option label="男性" value="male" />
          <el-option label="女性" value="female" />
          <el-option label="未知" value="unknown" />
        </el-select>
        <el-select
          v-model="searchForm.is_active"
          placeholder="请选择状态"
          clearable
          @change="handleSearch"
          class="w-full"
        >
          <el-option label="有效" :value="true" />
          <el-option label="无效" :value="false" />
        </el-select>
      </div>

      <!-- 搜索和排序按钮 -->
      <div class="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4">
        <div class="flex flex-wrap gap-3">
          <el-button 
            type="primary" 
            @click="handleSearch" 
            icon="Search"
            class="px-4 py-2 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 flex items-center justify-center"
          >
                        
          搜索
          </el-button>
          <el-button 
            @click="handleReset" 
            icon="Refresh"
            class="px-4 py-2 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 flex items-center justify-center"
          >
            重置
          </el-button>
        </div>
        <div class="flex flex-wrap gap-3">
          <el-select v-model="sortField" placeholder="排序字段" @change="handleSearch" class="w-32 lg:w-40">
            <el-option label="创建时间" value="created_at" />
            <el-option label="上次登录" value="last_login" />
          </el-select>
          <el-select v-model="sortOrder" placeholder="排序方式" @change="handleSearch" class="w-24 lg:w-32">
            <el-option label="升序" value="asc" />
            <el-option label="降序" value="desc" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 用户列表表格 -->
    <div class="bg-white rounded-lg shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <el-table
          :data="userList"
          style="width: 100%; min-width: 1200px;"
          v-loading="loading"
          @selection-change="handleSelectionChange"
          :row-style="{ height: '70px' }"
          class="responsive-table"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80" sortable />
          <el-table-column prop="avatar" label="头像" width="80">
            <template #default="scope">
              <div class="flex justify-center">
                <el-avatar :src="scope.row.avatar" :size="45" class="shadow-sm">
                  {{ scope.row.username?.charAt(0) }}
                </el-avatar>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="用户信息" min-width="200">
            <template #default="scope">
              <div class="space-y-1">
                <div class="font-medium text-gray-900 text-sm">{{ scope.row.username }}</div>
                <div class="text-gray-500 text-xs">{{ scope.row.phone || '未绑定手机' }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="gender" label="性别" width="80">
            <template #default="scope">
              <el-tag 
                :type="scope.row.gender === 'male' ? '' : scope.row.gender === 'female' ? 'warning' : 'info'" 
                size="small"
                class="rounded-full px-2"
              >
                {{ getGenderText(scope.row.gender) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="login_locked" label="登录状态" width="100">
            <template #default="scope">
              <el-tag 
                :type="scope.row.login_locked ? 'danger' : 'success'" 
                size="small"
                class="rounded-full px-2"
              >
                {{ scope.row.login_locked ? '已锁定' : '正常' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="有效" width="80">
            <template #default="scope">
              <el-switch
                v-model="scope.row.is_active"
                @change="handleToggleStatus(scope.row)"
                :loading="scope.row.statusLoading"
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160">
            <template #default="scope">
              <div class="text-sm text-gray-600">
                {{ formatDateTime(scope.row.created_at) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="role" label="角色" width="100">
            <template #default="scope">
              <el-tag 
                :type="scope.row.role === 'admin' ? 'danger' : 'primary'" 
                size="small"
                class="rounded-full px-2"
              >
                {{ getRoleText(scope.row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="80" fixed="right">
            <template #default="scope">
              <div class="flex justify-center">
                <!-- 操作下拉菜单 -->
                <el-dropdown 
                  @command="(command) => handleDropdownCommand(command, scope.row)"
                  placement="bottom-end"
                  trigger="click"
                >
                  <el-button 
                    type="primary" 
                    size="small" 
                    circle
                    class="w-8 h-8"
                  >
                    <el-icon class="el-icon--right">
                      <MoreFilled />
                    </el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit" :icon="Edit">
                        编辑用户
                      </el-dropdown-item>
                      <el-dropdown-item command="view" :icon="View">
                        查看详情
                      </el-dropdown-item>
                      <el-dropdown-item command="avatar" :icon="Avatar" divided>
                        修改头像
                      </el-dropdown-item>
                      <el-dropdown-item command="password" :icon="Lock">
                        重置密码
                      </el-dropdown-item>
                      <el-dropdown-item 
                        command="delete" 
                        :icon="Delete"
                        style="color: #f56565"
                        divided
                      >
                        删除用户
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="p-4 flex flex-col lg:flex-row lg:justify-between lg:items-center border-t border-gray-100 gap-4">
        <div class="text-sm text-gray-500">
          共 {{ pagination.count }} 条
        </div>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[15, 30, 50, 100]"
          :total="pagination.count"
          layout="sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          class="pagination-custom"
        />
      </div>
    </div>

    <!-- 新增/编辑用户对话框 -->
    <el-dialog
      v-model="userDialog.visible"
      :title="userDialog.mode === 'add' ? '新增用户' : '编辑用户'"
      width="90%"
      :max-width="600"
      :close-on-click-modal="false"
    >
      <el-form
        ref="userFormRef"
        :model="userDialog.form"
        :rules="userDialog.rules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userDialog.form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userDialog.form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userDialog.form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="userDialog.mode === 'add'">
          <el-input v-model="userDialog.form.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userDialog.form.role" placeholder="请选择角色" class="w-full">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="userDialog.form.gender" placeholder="请选择性别" class="w-full">
            <el-option label="男性" value="male" />
            <el-option label="女性" value="female" />
            <el-option label="未知" value="unknown" />
          </el-select>
        </el-form-item>
        <el-form-item label="生日" prop="birthday">
          <el-date-picker
            v-model="userDialog.form.birthday"
            type="date"
            placeholder="请选择生日"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="是否有效" prop="is_active">
          <el-switch v-model="userDialog.form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer flex gap-3 justify-end">
          <el-button @click="userDialog.visible = false" class="flex items-center justify-center">取消</el-button>
          <el-button type="primary" @click="handleSaveUser" :loading="userDialog.loading" class="flex items-center justify-center">
            {{ userDialog.mode === 'add' ? '新增' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看用户详情对话框 -->
    <el-dialog
      v-model="viewDialog.visible"
      title="用户详情"
      width="90%"
      :max-width="600"
    >
      <div v-if="viewDialog.userInfo">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">{{ viewDialog.userInfo.id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ viewDialog.userInfo.username }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ viewDialog.userInfo.email }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ viewDialog.userInfo.phone }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ getRoleText(viewDialog.userInfo.role) }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ getGenderText(viewDialog.userInfo.gender) }}</el-descriptions-item>
          <el-descriptions-item label="生日">{{ viewDialog.userInfo.birthday || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="年龄">{{ viewDialog.userInfo.age || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="有效状态">
            <el-tag :type="viewDialog.userInfo.is_active ? 'success' : 'danger'">
              {{ viewDialog.userInfo.is_active ? '有效' : '无效' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上次登录">{{ formatDateTime(viewDialog.userInfo.last_login) }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(viewDialog.userInfo.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(viewDialog.userInfo.updated_at) }}</el-descriptions-item>
        </el-descriptions>
        <div class="mt-4" v-if="viewDialog.userInfo.avatar">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="头像">
              <el-image :src="viewDialog.userInfo.avatar" style="width: 100px; height: 100px" />
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>

    <!-- 头像上传对话框 -->
    <el-dialog
      v-model="avatarDialog.visible"
      title="修改头像"
      width="90%"
      :max-width="400"
    >
      <div class="text-center">
        <div class="mb-4">
          <el-avatar :src="avatarDialog.currentAvatar" :size="100">
            {{ avatarDialog.username?.charAt(0) }}
          </el-avatar>
        </div>
        <el-upload
          ref="uploadRef"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleAvatarChange"
          accept="image/*"
        >
          <el-button type="primary" icon="Upload" class="flex items-center justify-center">选择新头像</el-button>
        </el-upload>
        <div class="mt-2 text-sm text-gray-500">
          支持 jpg、png、gif、webp 格式，最大 5MB
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer flex gap-3 justify-end flex-wrap">
          <el-button @click="avatarDialog.visible = false" class="flex items-center justify-center">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleUploadAvatar" 
            :loading="avatarDialog.loading"
            :disabled="!avatarDialog.file"
            class="flex items-center justify-center"
          >
            上传
          </el-button>
          <el-button 
            type="danger" 
            @click="handleDeleteAvatar"
            v-if="avatarDialog.currentAvatar"
            :loading="avatarDialog.deleteLoading"
            class="flex items-center justify-center"
          >
            删除头像
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="passwordDialog.visible"
      title="重置密码"
      width="90%"
      :max-width="400"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordDialog.form"
        :rules="passwordDialog.rules"
        label-width="100px"
      >
        <el-form-item label="新密码" prop="new_password">
          <el-input 
            v-model="passwordDialog.form.new_password" 
            type="password" 
            placeholder="请输入新密码（最少8位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input 
            v-model="passwordDialog.form.confirm_password" 
            type="password" 
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer flex gap-3 justify-end">
          <el-button @click="passwordDialog.visible = false" class="flex items-center justify-center">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleResetPassword" 
            :loading="passwordDialog.loading"
            class="flex items-center justify-center"
          >
            重置密码
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userManagementAPI } from '@/api.js'
import { Edit, View, Avatar, Lock, Delete, MoreFilled } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const userList = ref([])
const selectedUsers = ref([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 15,
  count: 0
})

// 搜索表单
const searchForm = reactive({
  username: '',
  phone: '',
  email: '',
  id: '',
  gender: '',
  is_active: ''
})

// 排序
const sortField = ref('created_at')
const sortOrder = ref('desc')

// 用户对话框
const userDialog = reactive({
  visible: false,
  mode: 'add', // add | edit
  loading: false,
  form: {
    username: '',
    email: '',
    phone: '',
    password: '',
    role: 'user',
    gender: '',
    birthday: '',
    is_active: true
  },
  rules: {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 1, max: 150, message: '用户名长度应在1-150字符之间', trigger: 'blur' }
    ],
    email: [
      { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 8, message: '密码最少8位', trigger: 'blur' }
    ],
    role: [
      { required: true, message: '请选择角色', trigger: 'change' }
    ]
  },
  editingUserId: null
})

// 查看对话框
const viewDialog = reactive({
  visible: false,
  userInfo: null
})

// 头像对话框
const avatarDialog = reactive({
  visible: false,
  loading: false,
  deleteLoading: false,
  userId: null,
  username: '',
  currentAvatar: '',
  file: null
})

// 密码对话框
const passwordDialog = reactive({
  visible: false,
  loading: false,
  userId: null,
  form: {
    new_password: '',
    confirm_password: ''
  },
  rules: {
    new_password: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 8, message: '密码最少8位', trigger: 'blur' }
    ],
    confirm_password: [
      { required: true, message: '请确认密码', trigger: 'blur' },
      { 
        validator: (rule, value, callback) => {
          if (value !== passwordDialog.form.new_password) {
            callback(new Error('两次输入的密码不一致'))
          } else {
            callback()
          }
        }, 
        trigger: 'blur' 
      }
    ]
  }
})

// 表单引用
const userFormRef = ref(null)
const passwordFormRef = ref(null)
const uploadRef = ref(null)

// 获取用户列表
const getUserList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    // 添加搜索参数
    if (searchForm.username) params.username = searchForm.username
    if (searchForm.phone) params.phone = searchForm.phone
    if (searchForm.email) params.email = searchForm.email
    if (searchForm.id) params.id = searchForm.id
    if (searchForm.gender) params.gender = searchForm.gender
    if (searchForm.is_active !== '') params.is_active = searchForm.is_active

    // 添加排序参数
    if (sortField.value && sortOrder.value) {
      params.ordering = sortOrder.value === 'desc' ? `-${sortField.value}` : sortField.value
    }

    const response = await userManagementAPI.getUserList(params)
    userList.value = response.data.data.results.map(user => ({
      ...user,
      statusLoading: false
    }))
    pagination.count = response.data.data.count
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 切换用户状态
const handleToggleStatus = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.is_active ? '禁用' : '启用'}用户 "${user.username}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    user.statusLoading = true
    await userManagementAPI.toggleUserStatus(user.id)
    ElMessage.success(`用户状态${user.is_active ? '禁用' : '启用'}成功`)
    await getUserList() // 重新获取列表更新状态
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换用户状态失败:', error)
      ElMessage.error('切换用户状态失败')
      // 恢复开关状态
      user.is_active = !user.is_active
    } else {
      // 用户取消，恢复开关状态
      user.is_active = !user.is_active
    }
  } finally {
    user.statusLoading = false
  }
}

// 新增用户
const handleAdd = () => {
  userDialog.mode = 'add'
  userDialog.editingUserId = null
  userDialog.form = {
    username: '',
    email: '',
    phone: '',
    password: '',
    role: 'user',
    gender: '',
    birthday: '',
    is_active: true
  }
  userDialog.visible = true
  nextTick(() => {
    userFormRef.value?.clearValidate()
  })
}

// 编辑用户
const handleEdit = async (user) => {
  try {
    const response = await userManagementAPI.getUserDetail(user.id)
    const userInfo = response.data.data
    
    userDialog.mode = 'edit'
    userDialog.editingUserId = user.id
    userDialog.form = {
      username: userInfo.username || '',
      email: userInfo.email || '',
      phone: userInfo.phone || '',
      role: userInfo.role || 'user',
      gender: userInfo.gender || '',
      birthday: userInfo.birthday ? new Date(userInfo.birthday) : '',
      is_active: userInfo.is_active !== undefined ? userInfo.is_active : true
    }
    userDialog.visible = true
    nextTick(() => {
      userFormRef.value?.clearValidate()
    })
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.error('获取用户详情失败')
  }
}

// 保存用户
const handleSaveUser = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    userDialog.loading = true

    const formData = { ...userDialog.form }
    
    // 处理生日格式
    if (formData.birthday) {
      if (formData.birthday instanceof Date) {
        formData.birthday = formData.birthday.toISOString().split('T')[0]
      }
    } else {
      delete formData.birthday
    }

    // 清理空字段
    Object.keys(formData).forEach(key => {
      if (formData[key] === '' || formData[key] === null) {
        delete formData[key]
      }
    })

    if (userDialog.mode === 'add') {
      await userManagementAPI.createUser(formData)
      ElMessage.success('用户创建成功')
    } else {
      delete formData.password // 编辑时不传密码
      await userManagementAPI.updateUser(userDialog.editingUserId, formData)
      ElMessage.success('用户更新成功')
    }

    userDialog.visible = false
    await getUserList()
  } catch (error) {
    console.error('保存用户失败:', error)
    if (error.response?.data?.message) {
      ElMessage.error(`保存用户失败: ${error.response.data.message}`)
    } else {
      ElMessage.error('保存用户失败')
    }
  } finally {
    userDialog.loading = false
  }
}

// 删除用户
const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await userManagementAPI.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    await getUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败')
    }
  }
}

// 查看用户详情
const handleView = async (user) => {
  try {
    const response = await userManagementAPI.getUserDetail(user.id)
    viewDialog.userInfo = response.data.data
    viewDialog.visible = true
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.error('获取用户详情失败')
  }
}

// 头像上传
const handleAvatarUpload = (user) => {
  avatarDialog.userId = user.id
  avatarDialog.username = user.username
  avatarDialog.currentAvatar = user.avatar
  avatarDialog.file = null
  avatarDialog.visible = true
}

// 头像文件变化
const handleAvatarChange = (file) => {
  const isImage = file.raw.type.startsWith('image/')
  const isLt5M = file.raw.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
    return false
  }

  avatarDialog.file = file.raw
}

// 上传头像
const handleUploadAvatar = async () => {
  if (!avatarDialog.file) {
    ElMessage.error('请选择头像文件')
    return
  }

  try {
    avatarDialog.loading = true
    await userManagementAPI.uploadUserAvatar(avatarDialog.userId, avatarDialog.file)
    ElMessage.success('头像上传成功')
    avatarDialog.visible = false
    await getUserList()
  } catch (error) {
    console.error('头像上传失败:', error)
    ElMessage.error('头像上传失败')
  } finally {
    avatarDialog.loading = false
  }
}

// 删除头像
const handleDeleteAvatar = async () => {
  try {
    await ElMessageBox.confirm('确定要删除用户头像吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    avatarDialog.deleteLoading = true
    await userManagementAPI.deleteUserAvatar(avatarDialog.userId)
    ElMessage.success('头像删除成功')
    avatarDialog.visible = false
    await getUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('头像删除失败:', error)
      ElMessage.error('头像删除失败')
    }
  } finally {
    avatarDialog.deleteLoading = false
  }
}

// 重置密码
const handlePasswordReset = (user) => {
  passwordDialog.userId = user.id
  passwordDialog.form = {
    new_password: '',
    confirm_password: ''
  }
  passwordDialog.visible = true
  nextTick(() => {
    passwordFormRef.value?.clearValidate()
  })
}

// 执行重置密码
const handleResetPassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    passwordDialog.loading = true

    await userManagementAPI.resetUserPassword(passwordDialog.userId, {
      new_password: passwordDialog.form.new_password
    })
    ElMessage.success('密码重置成功')
    passwordDialog.visible = false
  } catch (error) {
    console.error('重置密码失败:', error)
    ElMessage.error('重置密码失败')
  } finally {
    passwordDialog.loading = false
  }
}

// 处理下拉菜单命令
const handleDropdownCommand = async (command, user) => {
  if (command === 'edit') {
    await handleEdit(user)
  } else if (command === 'view') {
    await handleView(user)
  } else if (command === 'avatar') {
    await handleAvatarUpload(user)
  } else if (command === 'password') {
    await handlePasswordReset(user)
  } else if (command === 'delete') {
    await handleDelete(user)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  getUserList()
}

// 重置搜索
const handleReset = () => {
  Object.assign(searchForm, {
    username: '',
    phone: '',
    email: '',
    id: '',
    gender: '',
    is_active: ''
  })
  sortField.value = 'created_at'
  sortOrder.value = 'desc'
  handleSearch()
}

// 刷新
const handleRefresh = () => {
  getUserList()
}

// 表格选择变化
const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

// 分页大小变化
const handleSizeChange = (val) => {
  pagination.pageSize = val
  pagination.page = 1
  getUserList()
}

// 当前页变化
const handleCurrentChange = (val) => {
  pagination.page = val
  getUserList()
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '未知'
  const date = new Date(dateTime)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 获取角色文本
const getRoleText = (role) => {
  const roleMap = {
    'admin': '管理员',
    'user': '普通用户'
  }
  return roleMap[role] || role
}

// 获取性别文本
const getGenderText = (gender) => {
  const genderMap = {
    'male': '男性',
    'female': '女性',
    'unknown': '未知'
  }
  return genderMap[gender] || '未知'
}

// 初始化
onMounted(() => {
  getUserList()
})
</script>

<style scoped>
.user-management {
  padding: 1rem;
}

@media (min-width: 1024px) {
  .user-management {
    padding: 1.5rem;
  }
}

:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table__header-wrapper) {
  background-color: #f8fafc;
}

:deep(.el-table th) {
  background-color: #f8fafc !important;
  color: #374151;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-table td) {
  border-bottom: 1px solid #f3f4f6;
}

:deep(.el-table__row:hover) {
  background-color: #f9fafb !important;
}

:deep(.pagination-custom .el-pagination__total),
:deep(.pagination-custom .el-pagination__sizes),
:deep(.pagination-custom .el-pagination__jump) {
  color: #6b7280;
}

/* 按钮样式优化 */
:deep(.el-button) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

:deep(.el-button--primary.is-plain) {
  border-color: #3b82f6;
  color: #3b82f6;
  background-color: #eff6ff;
}

:deep(.el-button--primary.is-plain:hover) {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
}

:deep(.el-button--danger.is-plain) {
  border-color: #ef4444;
  color: #ef4444;
  background-color: #fef2f2;
}

:deep(.el-button--danger.is-plain:hover) {
  background-color: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}

:deep(.el-button--info.is-plain) {
  border-color: #6b7280;
  color: #6b7280;
  background-color: #f9fafb;
}

:deep(.el-button--info.is-plain:hover) {
  background-color: #6b7280;
  border-color: #6b7280;
  color: #ffffff;
}

:deep(.el-button--warning.is-plain) {
  border-color: #f59e0b;
  color: #f59e0b;
  background-color: #fffbeb;
}

:deep(.el-button--warning.is-plain:hover) {
  background-color: #f59e0b;
  border-color: #f59e0b;
  color: #ffffff;
}

:deep(.el-button--success.is-plain) {
  border-color: #10b981;
  color: #10b981;
  background-color: #ecfdf5;
}

:deep(.el-button--success.is-plain:hover) {
  background-color: #10b981;
  border-color: #10b981;
  color: #ffffff;
}

:deep(.el-tag) {
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

/* 响应式表格 */
.responsive-table {
  width: 100%;
}

@media (max-width: 1200px) {
  :deep(.responsive-table .el-table__body-wrapper) {
    overflow-x: auto;
  }
}

/* 对话框响应式 */
:deep(.el-dialog) {
  margin: 5vh auto;
}

@media (max-width: 768px) {
  :deep(.el-dialog) {
    margin: 2vh auto;
    width: 95% !important;
    max-width: none !important;
  }
}

/* 操作列下拉菜单样式优化 */
:deep(.el-dropdown-menu__item) {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: #f3f4f6;
}

:deep(.el-dropdown-menu__item.is-divided) {
  border-top: 1px solid #e5e7eb;
  margin-top: 4px;
  padding-top: 8px;
}

/* 操作按钮样式优化 */
.operation-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-button.is-circle) {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

:deep(.el-button.is-circle:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style> 