<template>
  <el-dialog title="选择笔记类型" v-model="visible" width="400px">
    <div class="type-selector">
      <div
          v-for="type in noteTypes"
          :key="type.value"
          class="type-card"
          @click="selectType(type.value)"
      >
        <div class="type-icon">
          <i :class="type.icon"></i>
        </div>
        <h3>{{ type.label }}</h3>
        <p>{{ type.description }}</p>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue';
import { CategoryType } from '../types';

const emit = defineEmits(['select']);

const visible = ref(false);
const noteTypes = [
  {
    value: CategoryType.NORMAL,
    label: '普通笔记',
    icon: 'el-icon-document',
    description: '标准Markdown格式的笔记'
  },
  {
    value: CategoryType.DATABASE,
    label: '数据库笔记',
    icon: 'el-icon-s-grid',
    description: '表格形式的结构化数据'
  },
  {
    value: CategoryType.TOOL,
    label: '工具笔记',
    icon: 'el-icon-cpu',
    description: '集成计算工具和可视化'
  }
];

const open = () => visible.value = true;
const selectType = (type: NoteType) => {
  emit('select', type);
  visible.value = false;
};

defineExpose({ open });
</script>

<style scoped>
.type-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
}

.type-card {
  width: 160px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.type-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.type-icon {
  font-size: 32px;
  margin-bottom: 12px;
  color: #409eff;
}

.type-card h3 {
  margin: 0;
  font-size: 16px;
}

.type-card p {
  margin: 8px 0 0;
  font-size: 12px;
  color: #909399;
}
</style>