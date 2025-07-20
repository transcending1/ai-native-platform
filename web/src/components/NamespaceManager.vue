<template>
  <div class="namespace-manager">
    <div class="header">
      <h2>命名空间</h2>
      <el-button type="primary" size="small" @click="createNamespace">
        <i class="el-icon-plus"></i> 新建
      </el-button>
    </div>

    <div class="namespace-list">
      <div
          v-for="ns in namespaces"
          :key="ns.id"
          class="namespace-item"
          :class="{ active: currentNamespaceId === ns.id }"
          @click="selectNamespace(ns)"
      >
        <div class="namespace-info">
          <i class="el-icon-folder-opened"></i>
          <span class="name">{{ ns.name }}</span>
        </div>
        <div class="namespace-actions">
          <el-button
              type="warning"
              size="small"
              icon="el-icon-edit"
              @click.stop="editNamespace(ns)"
          >编辑</el-button>
          <el-button
              type="danger"
              size="small"
              icon="el-icon-delete"
              @click.stop="deleteNamespace(ns.id)"
          >删除</el-button>
        </div>
      </div>
    </div>

    <el-dialog
        :title="editMode ? '编辑命名空间' : '新建命名空间'"
        v-model="dialogVisible"
        width="30%"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="formData.name"></el-input>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
              v-model="formData.description"
              type="textarea"
              rows="3"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitNamespace">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue';
import { namespaceApi } from '../api/index';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  namespaces: any[];
  currentNamespaceId: number | null;
}>();

const emit = defineEmits(['select', 'created', 'updated', 'deleted']);

const dialogVisible = ref(false);
const editMode = ref(false);
const currentEditingId = ref<number | null>(null);
const formData = ref({
  name: '',
  description: ''
});

const selectNamespace = (ns: any) => {
  emit('select', ns);
};

const createNamespace = () => {
  editMode.value = false;
  formData.value = { name: '', description: '' };
  dialogVisible.value = true;
};

const editNamespace = (ns: any) => {
  editMode.value = true;
  currentEditingId.value = ns.id;
  formData.value = {
    name: ns.name,
    description: ns.description || ''
  };
  dialogVisible.value = true;
};

const deleteNamespace = async (id: number) => {
  try {
    await namespaceApi.delete(id);
    emit('deleted', id);
    ElMessage.success('命名空间删除成功');
  } catch (error) {
    ElMessage.error('命名空间删除失败');
  }
};

const submitNamespace = async () => {
  if (!formData.value.name.trim()) {
    ElMessage.warning('名称不能为空');
    return;
  }

  try {
    if (editMode.value && currentEditingId.value) {
      const updated = await namespaceApi.update(
          currentEditingId.value,
          formData.value
      );
      emit('updated', updated.data);
      ElMessage.success('命名空间更新成功');
    } else {
      const created = await namespaceApi.create(formData.value);
      emit('created', created.data);
      ElMessage.success('命名空间创建成功');
    }
    dialogVisible.value = false;
  } catch (error) {
    ElMessage.error(editMode.value ? '更新失败' : '创建失败');
  }
};
</script>

<style scoped>
.namespace-manager {
  padding: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.namespace-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.namespace-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 6px;
  background-color: #f9fafc;
  border: 1px solid #ebeef5;
  cursor: pointer;
  transition: all 0.3s;
}

.namespace-item:hover {
  background-color: #ecf5ff;
  border-color: #d9ecff;
}

.namespace-item.active {
  background-color: #ecf5ff;
  border-color: #409eff;
}

.namespace-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.namespace-info i {
  font-size: 18px;
  color: #409eff;
}

.name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.namespace-actions {
  opacity: 0;
  transition: opacity 0.3s;
}

.namespace-item:hover .namespace-actions {
  opacity: 1;
}
</style>