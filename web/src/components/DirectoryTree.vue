<template>
  <div class="directory-tree">
    <div class="tree-container">
      <directory-node
        v-for="node in treeData"
        :key="node.id"
        :node="node"
        :depth="0"
        :selected-note-id="selectedNoteId"
        :selected-directory-id="selectedDirectoryId"
        @select="handleSelect"
        @create-directory="handleCreateDirectory"
        @create-note="handleCreateNote"
        @edit="handleEdit"
        @delete="handleDelete"
        @move="handleMove"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';
import DirectoryNode from './DirectoryNode.vue';

const props = defineProps<{
  treeData: any[];
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

const handleSelect = (item: any) => {
  emit('select', item);
};

const handleCreateDirectory = (parentId: number | null) => {
  emit('create-directory', parentId);
};

const handleCreateNote = (directoryId: number) => {
  emit('create-note', directoryId);
};

const handleEdit = (item: any) => {
  emit('edit', item);
};

const handleDelete = (item: any) => {
  emit('delete', item);
};

const handleMove = (item: any) => {
  emit('move', item);
};
</script>

<style scoped>
.directory-tree {
  padding: 10px;
}

.tree-container {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}
</style>