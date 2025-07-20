<!--<template>-->
<!--  <div class="editor-wrapper">-->
<!--    <div class="toolbar">-->
<!--      <button @click="triggerFileUpload" class="upload-button">-->
<!--        <input type="file" ref="fileInput" @change="handleFileUpload" hidden multiple>-->
<!--        上传文件-->
<!--      </button>-->
<!--    </div>-->
<!--    <div ref="editorEl"></div>-->
<!--    <button @click="handleGetMarkdown">获取Markdown</button>-->
<!--    <div class="output-area">-->
<!--      <h3>Markdown 输出：</h3>-->
<!--      <pre>{{ markdownContent }}</pre>-->
<!--    </div>-->
<!--  </div>-->
<!--</template>-->

<!--<script setup lang="ts">-->
<!--import { ref, shallowRef, onMounted, onBeforeUnmount } from 'vue'-->
<!--import Editor from '@toast-ui/editor'-->
<!--import '@toast-ui/editor/dist/toastui-editor.css'-->
<!--import '@toast-ui/editor/dist/theme/toastui-editor-dark.css'-->
<!--import colorSyntax from '@toast-ui/editor-plugin-color-syntax'-->
<!--import codeSyntaxHighlight from '@toast-ui/editor-plugin-code-syntax-highlight'-->
<!--import 'prismjs/themes/prism.css'-->

<!--type EditorInstance = InstanceType<typeof Editor>-->

<!--const editorEl = ref<HTMLElement | null>(null)-->
<!--const editor = shallowRef<EditorInstance | null>(null)-->
<!--const markdownContent = ref<string>('')-->
<!--const fileInput = ref<HTMLInputElement | null>(null)-->

<!--// 图片上传专用-->
<!--const uploadImage = async (file: File): Promise<string> => {-->
<!--  try {-->
<!--    const formData = new FormData()-->
<!--    formData.append('file', file)-->

<!--    const response = await fetch('api/upload_image', {-->
<!--      method: 'POST',-->
<!--      body: formData,-->
<!--      mode: 'cors'-->
<!--    })-->

<!--    if (!response.ok) throw new Error('图片上传失败')-->
<!--    const result = await response.json()-->
<!--    return result.url-->
<!--  } catch (error) {-->
<!--    console.error('图片上传失败:', error)-->
<!--    return 'image_upload_failed'-->
<!--  }-->
<!--}-->

<!--// 通用文件上传-->
<!--const uploadFile = async (file: File): Promise<string> => {-->
<!--  try {-->
<!--    const formData = new FormData()-->
<!--    formData.append('file', file)-->

<!--    const response = await fetch('/api/upload_file', {-->
<!--      method: 'POST',-->
<!--      body: formData,-->
<!--      mode: 'cors'-->
<!--    })-->

<!--    if (!response.ok) throw new Error('文件上传失败')-->
<!--    const result = await response.json()-->
<!--    return result.url-->
<!--  } catch (error) {-->
<!--    console.error('文件上传失败:', error)-->
<!--    return 'file_upload_failed'-->
<!--  }-->
<!--}-->

<!--// 图片上传处理（用于编辑器拖放/粘贴）-->
<!--const handleImageUpload = async (blob: Blob, callback: (url: string) => void) => {-->
<!--  const file = new File([blob], `image-${Date.now()}`, { type: blob.type })-->
<!--  const url = await uploadImage(file)-->
<!--  callback(url)-->
<!--}-->

<!--// 触发文件选择-->
<!--const triggerFileUpload = () => {-->
<!--  fileInput.value?.click()-->
<!--}-->

<!--// 处理工具栏文件上传-->
<!--const handleFileUpload = async (e: Event) => {-->
<!--  const input = e.target as HTMLInputElement-->
<!--  if (!input.files?.length) return-->

<!--  for (const file of Array.from(input.files)) {-->
<!--    try {-->
<!--      // 文件大小限制（保持10MB）-->
<!--      const MAX_SIZE = 10 * 1024 * 1024-->
<!--      if (file.size > MAX_SIZE) {-->
<!--        alert(`文件大小超过限制: ${file.name}`)-->
<!--        continue-->
<!--      }-->

<!--      // 根据文件类型选择上传接口-->
<!--      let url: string-->
<!--      if (file.type.startsWith('image/')) {-->
<!--        url = await uploadImage(file)-->
<!--      } else {-->
<!--        url = await uploadFile(file)-->
<!--      }-->

<!--      // 插入编辑器内容-->
<!--      if (file.type.startsWith('image/')) {-->
<!--        editor.value?.insertText(`![](${url})`)-->
<!--      } else {-->
<!--        editor.value?.insertText(`[${file.name}](${url})`)-->
<!--      }-->
<!--    } catch (error) {-->
<!--      console.error(`${file.name} 上传失败:`, error)-->
<!--    }-->
<!--  }-->

<!--  input.value = ''-->
<!--}-->

<!--// 以下部分保持原有逻辑不变-->
<!--onMounted(() => {-->
<!--  if (!editorEl.value) return-->

<!--  editor.value = new Editor({-->
<!--    el: editorEl.value,-->
<!--    initialEditType: 'wysiwyg',-->
<!--    previewStyle: 'vertical',-->
<!--    height: '500px',-->
<!--    plugins: [colorSyntax, codeSyntaxHighlight],-->
<!--    theme: 'light',-->
<!--    usageStatistics: false,-->
<!--    hooks: {-->
<!--      addImageBlobHook: (blob, callback) => {-->
<!--        handleImageUpload(blob, callback)-->
<!--        return false-->
<!--      }-->
<!--    }-->
<!--  })-->
<!--})-->

<!--const handleGetMarkdown = () => {-->
<!--  if (!editor.value) return-->
<!--  markdownContent.value = editor.value.getMarkdown()-->
<!--}-->

<!--onBeforeUnmount(() => {-->
<!--  editor.value?.destroy()-->
<!--})-->
<!--</script>-->

<!--<style scoped>-->
<!--.editor-wrapper {-->
<!--  max-width: 1000px;-->
<!--  margin: 20px auto;-->
<!--  padding: 20px;-->
<!--}-->

<!--.toolbar {-->
<!--  margin-bottom: 10px;-->
<!--}-->

<!--.upload-button {-->
<!--  position: relative;-->
<!--  padding: 8px 16px;-->
<!--  background: #28a745;-->
<!--  color: white;-->
<!--  border: none;-->
<!--  border-radius: 4px;-->
<!--  cursor: pointer;-->
<!--}-->

<!--.upload-button:hover {-->
<!--  background: #218838;-->
<!--}-->

<!--.output-area {-->
<!--  margin-top: 20px;-->
<!--  padding: 15px;-->
<!--  background: #f5f5f5;-->
<!--  border-radius: 4px;-->
<!--}-->

<!--pre {-->
<!--  white-space: pre-wrap;-->
<!--  word-wrap: break-word;-->
<!--}-->

<!--button {-->
<!--  margin-top: 10px;-->
<!--  padding: 8px 16px;-->
<!--  background: #007bff;-->
<!--  color: white;-->
<!--  border: none;-->
<!--  border-radius: 4px;-->
<!--  cursor: pointer;-->
<!--}-->

<!--button:hover {-->
<!--  background: #0056b3;-->
<!--}-->
<!--</style>-->

<template>
  <div class="note-editor">
    <el-form :model="form" label-width="60px" v-loading="saving">
      <el-form-item label="标题">
        <el-input v-model="form.title"></el-input>
      </el-form-item>
      <el-form-item label="内容">
        <el-input type="textarea" v-model="form.content" :rows="20"></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="save">保存</el-button>
        <el-button @click="cancel">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  note: any;
}>();

const emit = defineEmits(['save', 'cancel']);

const form = ref({
  id: 0,
  title: '',
  content: ''
});

const saving = ref(false);

// 当传入的note变化时，更新表单
watch(() => props.note, (newVal) => {
  if (newVal) {
    form.value = {
      id: newVal.id,
      title: newVal.title,
      content: newVal.content
    };
  } else {
    form.value = { id: 0, title: '', content: '' };
  }
}, { immediate: true });

const save = () => {
  saving.value = true;
  emit('save', form.value);
  saving.value = false;
};

const cancel = () => {
  emit('cancel');
};
</script>

<style scoped>
.note-editor {
  padding: 16px;
  height: 100%;
  background-color: #fff;
}
</style>