<template>
  <div class="note-list">
    <div class="list-header">
      <h3>{{ directory.name }} 中的笔记</h3>
      <el-button
          type="primary"
          size="small"
          icon="el-icon-document-add"
          @click="createNote"
      >
        新建笔记
      </el-button>
    </div>

    <div class="notes-container">
      <div
          v-for="note in notes"
          :key="note.id"
          class="note-item"
          :class="{ active: selectedNoteId === note.id }"
          @click="selectNote(note)"
      >
        <div class="note-content">
          <i class="el-icon-document"></i>
          <div class="note-info">
            <div class="note-title">{{ note.title }}</div>
            <div class="note-meta">
              <span>更新于: {{ formatDate(note.updated_at) }}</span>
            </div>
          </div>
        </div>
        <div class="note-actions">
          <el-button
              type="warning"
              size="small"
              icon="el-icon-edit"
              circle
              @click.stop="editNote(note)"
          ></el-button>
          <el-button
              type="danger"
              size="small"
              icon="el-icon-delete"
              circle
              @click.stop="deleteNote(note.id)"
          ></el-button>
          <el-button
              type="success"
              size="small"
              icon="el-icon-rank"
              circle
              @click.stop="moveNote(note)"
          ></el-button>
        </div>
      </div>

      <div v-if="notes.length === 0" class="empty-notes">
        <i class="el-icon-document"></i>
        <p>此目录下还没有笔记</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';

const props = defineProps<{
  notes: any[];
  directory: any;
  selectedNoteId?: number | null;
}>();

const emit = defineEmits(['select', 'create', 'edit', 'delete', 'move']);

// 替换 date-fns 的日期格式化函数
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-');
};

const selectNote = (note: any) => {
  emit('select', note);
};

const createNote = () => {
  emit('create');
};

const editNote = (note: any) => {
  emit('edit', note);
};

const deleteNote = (id: number) => {
  emit('delete', id);
};

const moveNote = (note: any) => {
  emit('move', note);
};
</script>

<style scoped>
.note-list {
  padding: 10px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.notes-container {
  max-height: calc(100vh - 250px);
  overflow-y: auto;
}

.note-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  margin-bottom: 8px;
  border-radius: 4px;
  background-color: #f9fafc;
  cursor: pointer;
  transition: all 0.3s;
}

.note-item:hover {
  background-color: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.note-item.active {
  background-color: #e6f7ff;
  border-left: 3px solid #409eff;
}

.note-content {
  display: flex;
  align-items: center;
  flex: 1;
}

.note-content i {
  font-size: 24px;
  margin-right: 12px;
  color: #409eff;
}

.note-info {
  flex: 1;
}

.note-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.note-meta {
  font-size: 12px;
  color: #909399;
}

.note-actions {
  opacity: 0;
  transition: opacity 0.3s;
}

.note-item:hover .note-actions {
  opacity: 1;
}

.empty-notes {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.empty-notes i {
  font-size: 48px;
  margin-bottom: 15px;
  display: block;
}
</style>