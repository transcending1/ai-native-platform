<template>
  <div class="tool-editor">
    <div class="editor-header">
      <el-input v-model="noteTitle" placeholder="工具名称" />
      <div class="tool-select">
        <el-select v-model="selectedTool" placeholder="选择工具">
          <el-option
              v-for="tool in availableTools"
              :key="tool.value"
              :label="tool.label"
              :value="tool.value"
          />
        </el-select>
      </div>
      <div class="editor-actions">
        <el-button type="primary" @click="handleSave">保存</el-button>
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </div>

    <div class="tool-container">
      <!-- 计算器工具 -->
      <div v-if="selectedTool === 'calculator'" class="calculator">
        <div class="calculator-display">{{ displayValue }}</div>
        <div class="calculator-buttons">
          <button v-for="btn in calculatorButtons" :key="btn" @click="handleCalculatorInput(btn)">
            {{ btn }}
          </button>
        </div>
      </div>

      <!-- 绘图工具 -->
      <div v-if="selectedTool === 'drawing'" class="drawing-board">
        <canvas ref="canvas" width="600" height="400"></canvas>
        <div class="drawing-controls">
          <el-color-picker v-model="drawingColor" />
          <el-slider v-model="drawingSize" :min="1" :max="20" />
          <el-button @click="clearCanvas">清空</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import type { Note } from './types';

const props = defineProps<{
  note: Note;
}>();

const emit = defineEmits(['save', 'cancel']);

const noteTitle = ref(props.note.title);
const selectedTool = ref(props.note.toolConfig?.type || 'calculator');
const availableTools = [
  { label: '计算器', value: 'calculator' },
  { label: '绘图板', value: 'drawing' },
  { label: '单位转换器', value: 'converter' }
];

// 计算器状态
const displayValue = ref('0');
const calculatorButtons = [
  '7', '8', '9', '/',
  '4', '5', '6', '*',
  '1', '2', '3', '-',
  '0', '.', '=', '+',
  'C'
];

// 绘图板状态
const canvas = ref<HTMLCanvasElement | null>(null);
const drawingColor = ref('#000000');
const drawingSize = ref(5);
let isDrawing = false;
let lastX = 0;
let lastY = 0;

// 计算器逻辑
const handleCalculatorInput = (btn: string) => {
  if (btn === 'C') {
    displayValue.value = '0';
  } else if (btn === '=') {
    try {
      displayValue.value = eval(displayValue.value);
    } catch (error) {
      displayValue.value = 'Error';
    }
  } else {
    if (displayValue.value === '0' || displayValue.value === 'Error') {
      displayValue.value = btn;
    } else {
      displayValue.value += btn;
    }
  }
};

// 绘图板逻辑
onMounted(() => {
  if (canvas.value && selectedTool.value === 'drawing') {
    initCanvas();
  }
});

watch(selectedTool, (newVal) => {
  if (newVal === 'drawing' && canvas.value) {
    initCanvas();
  }
});

const initCanvas = () => {
  const ctx = canvas.value?.getContext('2d');
  if (!ctx) return;

  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  canvas.value?.addEventListener('mousedown', startDrawing);
  canvas.value?.addEventListener('mousemove', draw);
  canvas.value?.addEventListener('mouseup', stopDrawing);
  canvas.value?.addEventListener('mouseout', stopDrawing);
};

const startDrawing = (e: MouseEvent) => {
  isDrawing = true;
  const rect = canvas.value!.getBoundingClientRect();
  [lastX, lastY] = [e.clientX - rect.left, e.clientY - rect.top];
};

const draw = (e: MouseEvent) => {
  if (!isDrawing || !canvas.value) return;

  const ctx = canvas.value.getContext('2d');
  if (!ctx) return;

  const rect = canvas.value.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(x, y);
  ctx.strokeStyle = drawingColor.value;
  ctx.lineWidth = drawingSize.value;
  ctx.stroke();

  [lastX, lastY] = [x, y];
};

const stopDrawing = () => {
  isDrawing = false;
};

const clearCanvas = () => {
  const ctx = canvas.value?.getContext('2d');
  if (ctx && canvas.value) {
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
  }
};

// 保存工具笔记
const handleSave = () => {
  let content = '';
  if (selectedTool.value === 'calculator') {
    content = displayValue.value;
  } else if (selectedTool.value === 'drawing' && canvas.value) {
    content = canvas.value.toDataURL();
  }

  emit('save', {
    id: props.note.id,
    title: noteTitle.value,
    content: content,
    type: 'tool',
    toolConfig: {
      type: selectedTool.value,
      color: drawingColor.value,
      size: drawingSize.value
    }
  });
};

const handleCancel = () => {
  emit('cancel');
};
</script>

<style scoped>
.tool-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  background-color: #fff;
}

.editor-header {
  display: flex;
  margin-bottom: 16px;
  gap: 16px;
}

.tool-select {
  flex: 1;
}

.tool-container {
  flex: 1;
  overflow: auto;
}

.calculator {
  max-width: 300px;
  margin: 0 auto;
}

.calculator-display {
  background: #f0f0f0;
  padding: 10px;
  text-align: right;
  font-size: 24px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.calculator-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
}

.calculator-buttons button {
  padding: 15px;
  font-size: 18px;
  border: 1px solid #ddd;
  background: #f9f9f9;
  cursor: pointer;
}

.calculator-buttons button:hover {
  background: #e9e9e9;
}

.drawing-board {
  display: flex;
  flex-direction: column;
  align-items: center;
}

canvas {
  border: 1px solid #ddd;
  background: white;
  margin-bottom: 16px;
}

.drawing-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}
</style>