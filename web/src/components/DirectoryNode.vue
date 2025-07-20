<template>
  <div class="directory-node">
    <div
      class="node-header"
      :class="{ 
        active: isSelected,
        'directory-selected': isDirectorySelected,
        'note-selected': isNoteSelected
      }"
      :style="{ paddingLeft: `${16 + depth * 20}px` }"
      @click="toggle"
    >
      <i :class="isExpanded ? 'el-icon-folder-opened' : 'el-icon-folder'"></i>
      <span class="node-name">{{ node.name }}</span>
      
      <!-- +号按钮和下拉菜单 -->
      <div class="node-actions">
        <el-dropdown @command="handleCommand" trigger="click">
          <el-button
            type="primary"
            size="small"
            :icon="Plus"
            circle
            @click.stop
          ></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="create-directory">
                <i class="el-icon-folder-add"></i> 新建目录
              </el-dropdown-item>
              <el-dropdown-item command="create-note">
                <i class="el-icon-document-add"></i> 新建笔记
              </el-dropdown-item>
              <el-dropdown-item divided command="edit">
                <i class="el-icon-edit"></i> 编辑
              </el-dropdown-item>
              <el-dropdown-item command="move">
                <i class="el-icon-rank"></i> 移动
              </el-dropdown-item>
              <el-dropdown-item divided command="delete" class="danger-item">
                <i class="el-icon-delete"></i> 删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div v-if="isExpanded">
      <directory-node
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :selected-note-id="selectedNoteId"
        :selected-directory-id="selectedDirectoryId"
        @select="$emit('select', $event)"
        @create-directory="$emit('create-directory', $event)"
        @create-note="$emit('create-note', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
        @move="$emit('move', $event)"
      />

      <div
        v-if="node.notes && node.notes.length"
        class="notes-section"
        :style="{ paddingLeft: `${36 + depth * 20}px` }"
      >
        <div
          v-for="note in node.notes"
          :key="note.id"
          class="note-item"
          :class="{ 
            active: isNoteSelectedFn(note),
            'note-selected': isNoteSelectedFn(note)
          }"
          @click="selectNote(note)"
        >
          <i class="el-icon-document"></i>
          <span class="note-title">{{ note.title }}</span>
          
          <!-- 笔记的+号按钮和下拉菜单 -->
          <div class="note-actions">
            <el-dropdown @command="(command: any) => handleNoteCommand(command, note)" trigger="click">
              <el-button
                type="success"
                size="small"
                :icon="Plus"
                circle
                @click.stop
              ></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">
                    <i class="el-icon-edit"></i> 编辑
                  </el-dropdown-item>
                  <el-dropdown-item command="move">
                    <i class="el-icon-rank"></i> 移动
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete" class="danger-item">
                    <i class="el-icon-delete"></i> 删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, ref, defineEmits, computed } from 'vue';
import { Plus } from '@element-plus/icons-vue';

const props = defineProps<{
  node: any;
  depth: number;
  selectedNoteId?: number | null;
  selectedDirectoryId?: number | null;
}>();

const emit = defineEmits([
  'select',
  'create-directory',
  'create-note',
  'edit',
  'delete',
  'move'
]);

const isExpanded = ref(true);

const isSelected = computed(() => {
  if (props.node.children) {
    return props.selectedDirectoryId === props.node.id;
  } else {
    return props.selectedNoteId === props.node.id;
  }
});

const isDirectorySelected = computed(() => {
  return props.node.children && props.selectedDirectoryId === props.node.id;
});

const isNoteSelected = computed(() => {
  return !props.node.children && props.selectedNoteId === props.node.id;
});

const isNoteSelectedFn = (note: any) => {
  return props.selectedNoteId === note.id;
};

const toggle = () => {
  isExpanded.value = !isExpanded.value;
  emit('select', props.node);
};

const selectNote = (note: any) => {
  emit('select', note);
};

const handleCommand = (command: any) => {
  switch (command) {
    case 'create-directory':
      emit('create-directory', props.node.id);
      break;
    case 'create-note':
      emit('create-note', props.node.id);
      break;
    case 'edit':
      emit('edit', props.node);
      break;
    case 'move':
      emit('move', props.node);
      break;
    case 'delete':
      emit('delete', props.node);
      break;
  }
};

const handleNoteCommand = (command: any, note: any) => {
  switch (command) {
    case 'edit':
      emit('edit', note);
      break;
    case 'move':
      emit('move', note);
      break;
    case 'delete':
      emit('delete', note);
      break;
  }
};
</script>

<style scoped>
.directory-node {
  margin-bottom: 4px;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
  position: relative;
}

.node-header:hover {
  background-color: #f5f7fa;
}

.node-header.active {
  background-color: #ecf5ff;
  color: #409eff;
}

.node-header.directory-selected {
  background-color: #e6f7ff;
  border-left: 3px solid #409eff;
}

.node-header.note-selected {
  background-color: #f0f9ff;
  border-left: 3px solid #67c23a;
}

.node-header i {
  margin-right: 8px;
  font-size: 16px;
  color: #409eff;
}

.node-name {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-actions {
  opacity: 0.6;
  transition: opacity 0.3s;
  margin-left: 8px;
  display: flex;
  align-items: center;
  min-width: 24px;
  justify-content: center;
}

.node-header:hover .node-actions {
  opacity: 1;
}

.node-actions .el-button {
  background-color: #409eff;
  border-color: #409eff;
  color: white;
  font-weight: bold;
}

.notes-section {
  margin-top: 4px;
}

.note-item {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  margin-bottom: 2px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
  position: relative;
}

.note-item:hover {
  background-color: #f5f7fa;
}

.note-item.active {
  background-color: #e6f7ff;
  color: #409eff;
}

.note-item.note-selected {
  background-color: #f0f9ff;
  border-left: 3px solid #67c23a;
}

.note-item i {
  margin-right: 8px;
  font-size: 14px;
  color: #67c23a;
}

.note-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-actions {
  opacity: 0.6;
  transition: opacity 0.3s;
  margin-left: 8px;
  display: flex;
  align-items: center;
  min-width: 24px;
  justify-content: center;
}

.note-item:hover .note-actions {
  opacity: 1;
}

.note-actions .el-button {
  background-color: #67c23a;
  border-color: #67c23a;
  color: white;
  font-weight: bold;
}

.danger-item {
  color: #f56c6c !important;
}

.danger-item:hover {
  background-color: #fef0f0 !important;
}
</style>