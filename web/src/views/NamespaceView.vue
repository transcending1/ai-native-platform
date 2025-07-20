<template>
  <div class="namespace-view">
    <header class="app-header">
      <h1>{{ currentNamespace?.name || '笔记管理系统' }}</h1>
      <div class="user-info">
        <span>欢迎，{{ username }}</span>
        <el-button type="text" @click="goHome">返回首页</el-button>
        <el-button type="text" @click="logout">退出</el-button>
      </div>
    </header>

    <div class="main-layout">
      <!-- 左侧目录树 -->
      <div class="directory-panel">
        <div class="panel-header">
          <h3>目录结构</h3>
          <el-button
            type="primary"
            size="small"
            :icon="Plus"
            @click="showCreateRootDirectoryDialog"
          >
            添加根目录
          </el-button>
        </div>
        
        <div class="tree-container">
          <directory-tree
            :tree-data="treeData"
            :selected-note-id="currentNote?.id || null"
            :selected-directory-id="currentDirectory?.id || null"
            @select="handleSelectItem"
            @create-directory="showCreateDirectoryDialog"
            @create-note="showCreateNoteDialog"
            @edit="showEditDialog"
            @delete="showDeleteConfirm"
            @move="showMoveDialog"
          />
        </div>
      </div>

      <!-- 右侧笔记内容区域 -->
      <div class="content-panel">
        <!-- 笔记编辑器 -->
        <div v-if="currentNote" class="editor-container">
          <!-- 根据笔记内容判断类型 -->
          <div v-if="isMarkdownNote(currentNote)">
            <new-editor
              :note="currentNote"
              @save="saveNote"
              @cancel="deselectNote"
            />
          </div>
          <div v-else>
            <database-editor
              :note="currentNote"
              @save="saveNote"
              @cancel="deselectNote"
            />
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <el-icon :size="48" color="#909399">
            <Document />
          </el-icon>
          <p>请选择一个笔记开始编辑</p>
        </div>
      </div>
    </div>

    <!-- 创建目录对话框 -->
    <el-dialog
      title="新建目录"
      v-model="createDirectoryDialogVisible"
      width="400px"
    >
      <el-form :model="directoryForm" label-width="80px">
        <el-form-item label="目录名称" required>
          <el-input
            v-model="directoryForm.name"
            placeholder="请输入目录名称"
            @keyup.enter="createDirectory"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDirectoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createDirectory">确认</el-button>
      </template>
    </el-dialog>

    <!-- 创建笔记对话框 -->
    <el-dialog
      title="新建笔记"
      v-model="createNoteDialogVisible"
      width="500px"
    >
      <el-form :model="noteForm" label-width="80px">
        <el-form-item label="笔记标题" required>
          <el-input
            v-model="noteForm.title"
            placeholder="请输入笔记标题"
            @keyup.enter="createNote"
          ></el-input>
        </el-form-item>
        <el-form-item label="笔记类型" required>
          <el-radio-group v-model="noteForm.type">
            <el-radio label="md">
              <el-icon><Document /></el-icon>
              Markdown 笔记
            </el-radio>
            <el-radio label="db">
              <el-icon><Document /></el-icon>
              数据库表
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createNoteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createNote">确认</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      :title="`编辑${selectedItem?.children ? '目录' : '笔记'}`"
      v-model="editDialogVisible"
      width="400px"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item :label="selectedItem?.children ? '目录名称' : '笔记标题'" required>
          <el-input
            v-model="editForm.name"
            :placeholder="`请输入${selectedItem?.children ? '目录名称' : '笔记标题'}`"
            @keyup.enter="confirmEdit"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmEdit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 移动对话框 -->
    <el-dialog
      title="选择目标位置"
      v-model="moveDialogVisible"
      width="400px"
    >
      <el-tree
        :data="moveOptions"
        :props="treeProps"
        node-key="id"
        ref="moveTree"
        :default-expand-all="true"
        :highlight-current="true"
        @node-click="handleMoveTargetSelect"
      ></el-tree>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmMove">确认移动</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document } from '@element-plus/icons-vue'
import { namespaceApi, directoryApi, noteApi } from '../api/index'
import DirectoryTree from '../components/DirectoryTree.vue'
import NewEditor from '../components/NewEditor.vue'
import DatabaseEditor from '../components/DatabaseEditor.vue'

const route = useRoute()
const router = useRouter()
const namespaceId = ref<number>(parseInt(route.params.namespaceId as string))

const currentNamespace = ref<any>(null)
const treeData = ref<any[]>([])
const currentDirectory = ref<any>(null)
const currentNote = ref<any>(null)
const username = ref('管理员')

// 对话框状态
const createDirectoryDialogVisible = ref(false)
const createNoteDialogVisible = ref(false)
const editDialogVisible = ref(false)
const moveDialogVisible = ref(false)

// 表单数据
const directoryForm = ref({ name: '', parentId: null as number | null })
const noteForm = ref({ title: '', directoryId: null as number | null, type: 'md' })
const editForm = ref({ name: '' })

// 移动相关状态
const selectedItem = ref<any>(null)
const moveTargetId = ref<number | null>(null)
const moveOptions = computed(() => {
  if (!selectedItem.value) return treeData.value
  // 过滤掉被移动项及其子项
  const filterDescendants = (node: any) => {
    if (selectedItem.value.children) {
      // 移动目录时，不能移动到自己的子目录
      return node.id !== selectedItem.value.id &&
        !selectedItem.value.get_descendants?.().includes(node.id)
    }
    return true
  }
  return treeData.value.filter(filterDescendants)
})

const treeProps = {
  children: 'children',
  label: 'name'
}

// 加载数据
const loadNamespace = async () => {
  try {
    const response = await namespaceApi.list()
    const namespace = response.data.find((ns: any) => ns.id === namespaceId.value)
    currentNamespace.value = namespace
  } catch (error) {
    ElMessage.error('加载命名空间失败')
    console.error(error)
  }
}

const loadDirectoryTree = async () => {
  try {
    const response = await directoryApi.tree(namespaceId.value)
    console.log('目录树API返回数据:', response.data)
    treeData.value = response.data
  } catch (error) {
    ElMessage.error('加载目录树失败')
    console.error(error)
  }
}

// 监听路由变化
watch(
  () => route.params.namespaceId,
  (newId) => {
    if (newId) {
      namespaceId.value = parseInt(newId as string)
      loadNamespace()
      loadDirectoryTree()
    }
  },
  { immediate: true }
)

onMounted(() => {
  loadNamespace()
  loadDirectoryTree()
})

// 事件处理
const handleSelectItem = (item: any) => {
  if (item.children) {
    // 选择的是目录
    currentDirectory.value = item
    currentNote.value = null
  } else {
    // 选择的是笔记
    console.log('选择笔记:', item)
    currentNote.value = item
    currentDirectory.value = null
  }
}

// 创建根目录
const showCreateRootDirectoryDialog = () => {
  directoryForm.value = { name: '', parentId: null }
  createDirectoryDialogVisible.value = true
}

// 创建子目录
const showCreateDirectoryDialog = (parentId: number | null) => {
  directoryForm.value = { name: '', parentId }
  createDirectoryDialogVisible.value = true
}

const createDirectory = async () => {
  if (!directoryForm.value.name.trim()) {
    ElMessage.warning('目录名称不能为空')
    return
  }

  try {
    const createData: any = {
      name: directoryForm.value.name,
      namespace: namespaceId.value,
      parent: directoryForm.value.parentId  // 明确传入 parent 字段，根目录时为 null
    }
    await directoryApi.create(createData)

    await loadDirectoryTree()
    createDirectoryDialogVisible.value = false
    ElMessage.success('目录创建成功')
  } catch (error) {
    ElMessage.error('创建目录失败')
  }
}

// 创建笔记
const showCreateNoteDialog = (directoryId: number) => {
  noteForm.value = { title: '', directoryId, type: 'md' }
  createNoteDialogVisible.value = true
}

const createNote = async () => {
  if (!noteForm.value.title.trim()) {
    ElMessage.warning('笔记标题不能为空')
    return
  }

  if (!noteForm.value.directoryId) {
    ElMessage.warning('请选择目录')
    return
  }

  try {
    let content = ''
    if (noteForm.value.type === 'db') {
      // 数据库表类型的默认内容
      const defaultDbData = {
        tableName: noteForm.value.title,
        tableDescription: '数据表描述',
        queryMode: 'single',
        fields: [
          { name: 'id', description: '数据的唯一标识（主键）', dataType: 'Integer', required: true },
          { name: 'sys_platform', description: '数据库生成使用的渠道', dataType: 'String', required: true },
          { name: 'uuid', description: '用户唯一标识，由系统生成', dataType: 'String', required: true },
          { name: 'bstudio_create_time', description: '数据插入的时间', dataType: 'Time', required: true },
          { name: 'name', description: '笔记名称', dataType: 'String', required: true },
          { name: 'section', description: '章节', dataType: 'Integer', required: true },
          { name: 'note', description: '笔记内容', dataType: 'String', required: true }
        ]
      }
      content = JSON.stringify(defaultDbData, null, 2)
    } else {
      // Markdown 类型的默认内容
      content = '## 这是新笔记的内容'
    }

    // 尝试不同的 category 值
    const markdownCategory = 'md' // 如果不行，可以尝试 'text', 'note', 'markdown'
    
    const response = await noteApi.create({
      title: noteForm.value.title,
      content: content,
      directory: noteForm.value.directoryId as number,
      category: noteForm.value.type === 'db' ? 'database' : markdownCategory
    })

    console.log('创建笔记响应:', response.data)
    console.log('笔记内容:', content)
    console.log('笔记类型:', noteForm.value.type)
    console.log('笔记内容类型:', typeof content)
    console.log('笔记内容长度:', content.length)

    // 设置当前笔记
    currentNote.value = response.data
    
    // 立即刷新目录树，但保持当前笔记选择
    const noteId = currentNote.value.id
    await loadDirectoryTree()
    
    // 确保当前笔记仍然被选中
    if (currentNote.value && currentNote.value.id === noteId) {
      // 当前笔记选择状态正常
    } else {
      // 尝试从新的目录树中找到对应的笔记
      const findNote = (nodes: any[]): any => {
        for (const node of nodes) {
          if (node.notes) {
            const note = node.notes.find((n: any) => n.id === noteId)
            if (note) return note
          }
          if (node.children) {
            const found = findNote(node.children)
            if (found) return found
          }
        }
        return null
      }
      const updatedNote = findNote(treeData.value)
      if (updatedNote) {
        currentNote.value = updatedNote
      } else {
        currentNote.value = response.data
      }
    }
    
    createNoteDialogVisible.value = false
    ElMessage.success('笔记创建成功')
  } catch (error) {
    ElMessage.error('创建笔记失败')
  }
}

// 编辑
const showEditDialog = (item: any) => {
  selectedItem.value = item
  editDialogVisible.value = true
  editForm.value.name = item.children ? item.name : item.title
}

const confirmEdit = async () => {
  if (!editForm.value.name.trim()) {
    ElMessage.warning('名称不能为空')
    return
  }

  try {
    if (selectedItem.value.children) {
      // 编辑目录
      await directoryApi.update(selectedItem.value.id, { name: editForm.value.name })
      await loadDirectoryTree()
      
      // 更新当前目录名称
      if (currentDirectory.value?.id === selectedItem.value.id) {
        currentDirectory.value.name = editForm.value.name
      }
    } else {
      // 编辑笔记 - 必须包含目录ID
      console.log('编辑笔记对象:', selectedItem.value)
      console.log('笔记对象的所有属性:', Object.keys(selectedItem.value))
      
      // 尝试多种方式获取目录ID
      let noteDirectoryId = selectedItem.value.directory || selectedItem.value.directory_id
      
      // 如果笔记对象中没有目录ID，尝试从当前选中的目录获取
      if (!noteDirectoryId && currentDirectory.value) {
        noteDirectoryId = currentDirectory.value.id
        console.log('从当前目录获取ID:', noteDirectoryId)
      }
      
      // 如果还是没有，尝试从目录树中查找笔记所属的目录
      if (!noteDirectoryId) {
        const findNoteDirectory = (nodes: any[]): number | null => {
          for (const node of nodes) {
            if (node.notes && node.notes.some((note: any) => note.id === selectedItem.value.id)) {
              return node.id
            }
            if (node.children) {
              const found = findNoteDirectory(node.children)
              if (found) return found
            }
          }
          return null
        }
        noteDirectoryId = findNoteDirectory(treeData.value)
        console.log('从目录树查找目录ID:', noteDirectoryId)
      }
      
      console.log('最终获取的目录ID:', noteDirectoryId)
      
      if (!noteDirectoryId) {
        ElMessage.error('无法获取笔记所属目录，请重新选择笔记')
        return
      }
      // 保持原有的 category
      const currentCategory = selectedItem.value.category || 'md'
      
      await noteApi.update(selectedItem.value.id, { 
        title: editForm.value.name,
        directory: noteDirectoryId as number,
        category: currentCategory
      })
      
      if (currentNote.value?.id === selectedItem.value.id) {
        currentNote.value.title = editForm.value.name
      }
      
      await loadDirectoryTree()
    }

    editDialogVisible.value = false
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 移动
const showMoveDialog = (item: any) => {
  selectedItem.value = item
  moveDialogVisible.value = true
  moveTargetId.value = null
}

const handleMoveTargetSelect = (data: any) => {
  moveTargetId.value = data.id
}

const confirmMove = async () => {
  if (!moveTargetId.value) {
    ElMessage.warning('请选择目标位置')
    return
  }

  try {
    if (selectedItem.value.children) {
      // 移动目录
      await directoryApi.move(selectedItem.value.id, moveTargetId.value)
      await loadDirectoryTree()
      
      // 如果移动的是当前目录，清空选择
      if (currentDirectory.value?.id === selectedItem.value.id) {
        currentDirectory.value = null
        currentNote.value = null
      }
    } else {
      // 移动笔记
      await noteApi.move(selectedItem.value.id, moveTargetId.value)
      await loadDirectoryTree()
      
      // 如果移动的是当前笔记，清空选择
      if (currentNote.value?.id === selectedItem.value.id) {
        currentNote.value = null
      }
    }

    moveDialogVisible.value = false
    ElMessage.success('移动成功')
  } catch (error) {
    ElMessage.error('移动失败')
  }
}

// 删除
const showDeleteConfirm = async (item: any) => {
  selectedItem.value = item
  
  try {
    const itemType = item.children ? '目录' : '笔记'
    const message = item.children ? 
      '确定要删除此目录及其所有内容吗？' : '确定要删除此笔记吗？'
    
    await ElMessageBox.confirm(message, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (item.children) {
      // 删除目录
      await directoryApi.delete(item.id)
      await loadDirectoryTree()
      
      // 如果删除的是当前目录，清空选择
      if (currentDirectory.value?.id === item.id) {
        currentDirectory.value = null
        currentNote.value = null
      }
    } else {
      // 删除笔记
      await noteApi.delete(item.id)
      await loadDirectoryTree()
      
      // 如果删除的是当前笔记，清空选择
      if (currentNote.value?.id === item.id) {
        currentNote.value = null
      }
    }

    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 保存笔记
const saveNote = async (noteData: { id: number; title: string; content: string }) => {
  try {
    // 获取当前笔记的目录ID
    console.log('保存笔记 - 当前笔记对象:', currentNote.value)
    console.log('当前笔记对象的所有属性:', Object.keys(currentNote.value || {}))
    
    // 尝试多种方式获取目录ID
    let noteDirectoryId = currentNote.value?.directory || currentNote.value?.directory_id
    
    // 如果笔记对象中没有目录ID，尝试从当前选中的目录获取
    if (!noteDirectoryId && currentDirectory.value) {
      noteDirectoryId = currentDirectory.value.id
      console.log('从当前目录获取ID:', noteDirectoryId)
    }
    
    // 如果还是没有，尝试从目录树中查找笔记所属的目录
    if (!noteDirectoryId) {
      const findNoteDirectory = (nodes: any[]): number | null => {
        for (const node of nodes) {
          if (node.notes && node.notes.some((note: any) => note.id === currentNote.value?.id)) {
            return node.id
          }
          if (node.children) {
            const found = findNoteDirectory(node.children)
            if (found) return found
          }
        }
        return null
      }
      noteDirectoryId = findNoteDirectory(treeData.value)
      console.log('从目录树查找目录ID:', noteDirectoryId)
    }
    
    console.log('最终获取的目录ID:', noteDirectoryId)
    
    if (!noteDirectoryId) {
      ElMessage.error('无法获取笔记所属目录，请重新选择笔记')
      return
    }
    
    // 根据内容判断笔记类型
    let category = 'md'
    try {
      const data = JSON.parse(noteData.content)
      const hasTableName = typeof data.tableName === 'string' && data.tableName.length > 0
      const hasFields = Array.isArray(data.fields) && data.fields.length > 0
      const hasQueryMode = typeof data.queryMode === 'string'
      
      if (hasTableName && hasFields && hasQueryMode) {
        category = 'database'
      }
    } catch (error) {
      // 如果解析失败，保持为 md
    }
    
    const response = await noteApi.update(noteData.id, {
      title: noteData.title,
      content: noteData.content,
      directory: noteDirectoryId as number,
      category: category
    })

    currentNote.value = response.data
    await loadDirectoryTree()
    ElMessage.success('笔记保存成功')
  } catch (error) {
    ElMessage.error('保存笔记失败')
  }
}

const deselectNote = () => {
  currentNote.value = null
}

const goHome = () => {
  router.push('/')
}

// 判断是否为 Markdown 笔记
const isMarkdownNote = (note: any) => {
  if (!note) {
    return true // 默认为 Markdown
  }
  
  // 优先使用 category 字段判断
  if (note.category) {
    return note.category === 'markdown' || note.category === 'md'
  }
  
  // 如果没有 category 字段，则通过内容判断（向后兼容）
  if (!note.content) {
    return true // 默认为 Markdown
  }
  
  try {
    // 尝试解析为 JSON
    const data = JSON.parse(note.content)
    
    // 检查是否为数据库表格式
    const hasTableName = typeof data.tableName === 'string' && data.tableName.length > 0
    const hasFields = Array.isArray(data.fields) && data.fields.length > 0
    const hasQueryMode = typeof data.queryMode === 'string'
    
    const isDb = hasTableName && hasFields && hasQueryMode
    return !isDb // 如果不是数据库表，就是 Markdown
  } catch (error) {
    // 如果解析失败，认为是 Markdown 笔记
    return true
  }
}

const logout = () => {
  console.log('用户退出')
}
</script>

<style scoped>
.namespace-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  background-color: #ffffff;
  color: #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid #e4e7ed;
}

.app-header h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.directory-panel {
  width: 300px;
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.content-panel {
  flex: 1;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #fafafa;
  gap: 12px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.tree-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.editor-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
  font-size: 16px;
}

.empty-state .el-icon {
  margin-bottom: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-layout {
    flex-direction: column;
  }
  
  .directory-panel {
    width: 100%;
    height: 200px;
  }
  
  .content-panel {
    flex: 1;
  }
}
</style>