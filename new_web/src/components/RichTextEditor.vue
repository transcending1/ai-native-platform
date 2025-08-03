<template>
  <div class="rich-text-editor" :style="editorStyle">
    <!-- 编辑器工具栏 -->
    <div class="editor-toolbar" v-if="!disabled">
      <div class="toolbar-left">
        <span class="toolbar-label"></span>
      </div>
      
      <div class="toolbar-right">
        
        <!-- Word上传按钮 -->
        <el-button 
          size="small" 
          type="success" 
          @click="triggerWordUpload"
          :icon="Document"
        >
          上传Word
        </el-button>
        
        <!-- PDF上传按钮 -->
        <el-button 
          size="small" 
          type="primary" 
          @click="triggerPdfUpload"
          :icon="Files"
        >
          上传PDF
        </el-button>
        
        <!-- 导出下拉菜单 -->
        <el-dropdown @command="handleExport" trigger="click">
          <el-button size="small" type="warning" :icon="Download">
            导出
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="word">导出Word</el-dropdown-item>
              <el-dropdown-item command="pdf">导出PDF</el-dropdown-item>
              <el-dropdown-item command="html">导出HTML</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      
      <!-- 隐藏的文件输入 -->
      <input 
        ref="imageInputRef" 
        type="file" 
        accept="image/*" 
        multiple 
        style="display: none;"
        @change="handleImageUpload"
      />
      <input 
        ref="wordInputRef" 
        type="file" 
        accept=".docx,.doc" 
        style="display: none;"
        @change="handleWordUpload"
      />
      <input 
        ref="pdfInputRef" 
        type="file" 
        accept=".pdf" 
        style="display: none;"
        @change="handlePdfUpload"
      />
    </div>
    
    <!-- 编辑器主体 -->
    <div 
      class="editor-wrapper"
      @dragover.prevent="!disabled && handleDragOver" 
      @drop.prevent="!disabled && handleDrop"
      @paste="!disabled && handlePaste"
      :class="{ 'drag-over': isDragOver && !disabled }"
    >
      <ckeditor
        v-model="editorData"
        :editor="ClassicEditor"
        :config="editorConfig"
        :disabled="disabled"
        @ready="onEditorReady"
        @focus="onEditorFocus"
        @blur="onEditorBlur"
        @input="onEditorInput"
        class="main-editor"
      />
    </div>
    
    <!-- 功能提示 -->
    <div class="feature-hints" v-if="!disabled">
      <div class="hint-item">
        <el-icon><DocumentCopy /></el-icon>
        <span>支持Ctrl+V直接粘贴图片和富文本内容</span>
      </div>
      <div class="hint-item">
        <el-icon><Upload /></el-icon>
        <span>支持拖拽图片、Word文档和PDF文件</span>
      </div>
      <div class="hint-item">
        <el-icon><Download /></el-icon>
        <span>支持导出为Word文档和PDF格式</span>
      </div>
    </div>
    
    <!-- 统计信息 -->
    <div class="stats-info" v-if="showStats && !disabled">
      <div class="stat-item">
        <span class="stat-label">字符数:</span>
        <span class="stat-value">{{ wordCount?.characters || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">单词数:</span>
        <span class="stat-value">{{ wordCount?.words || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">图片数:</span>
        <span class="stat-value">{{ imageCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">表格数:</span>
        <span class="stat-value">{{ tableCount }}</span>
      </div>
    </div>
    
    <!-- PDF预览模态框 -->
    <el-dialog 
      v-model="showPdfPreview" 
      title="PDF预览" 
      width="800px"
      :before-close="closePdfPreview"
    >
      <div class="pdf-info">
        <p><strong>文件名：</strong>{{ currentPdfName }}</p>
        <p><strong>页数：</strong>{{ pdfPageCount }}</p>
      </div>
      <div class="pdf-content">
        <div v-for="(pageText, index) in pdfTextContent" :key="index" class="pdf-page">
          <h4>第 {{ index + 1 }} 页</h4>
          <pre>{{ pageText }}</pre>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closePdfPreview">取消</el-button>
          <el-button type="primary" @click="insertPdfContent">插入到编辑器</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Word预览模态框 -->
    <el-dialog 
      v-model="showWordPreview" 
      title="Word预览" 
      width="800px"
      :before-close="closeWordPreview"
    >
      <div class="word-info">
        <p><strong>文件名：</strong>{{ currentWordName }}</p>
        <p><strong>大小：</strong>{{ formatFileSize(currentWordSize) }}</p>
      </div>
      <div class="word-content">
        <div v-html="wordHtmlContent"></div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeWordPreview">取消</el-button>
          <el-button type="primary" @click="insertWordContent">插入到编辑器</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 上传进度提示 -->
    <el-dialog 
      v-model="isUploading" 
      title="处理中" 
      width="400px"
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="upload-progress">
        <el-progress 
          :percentage="uploadProgress" 
          :format="() => uploadMessage"
          status="success"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Picture, Document, Files, Download, ArrowDown, 
  DocumentCopy, Upload
} from '@element-plus/icons-vue'
import { 
  ClassicEditor, 
  Essentials, 
  Paragraph, 
  Bold, 
  Italic, 
  Underline,
  Strikethrough,
  Heading,
  Font,
  FontSize,
  FontFamily,
  FontColor,
  FontBackgroundColor,
  Link,
  List,
  ListProperties,
  TodoList,
  Indent,
  IndentBlock,
  Alignment,
  BlockQuote,
  Table,
  TableToolbar,
  TableProperties,
  TableCellProperties,
  MediaEmbed,
  PasteFromOffice,
  WordCount,
  SourceEditing,
  GeneralHtmlSupport,
  CodeBlock,
  Code,
  HorizontalLine,
  PageBreak,
  SpecialCharacters,
  SpecialCharactersEssentials,
  SpecialCharactersArrows,
  SpecialCharactersMathematical,
  RemoveFormat,
  FindAndReplace,
  Highlight,
  Mention,
  AutoLink,
  TextTransformation,
  Image,
  ImageCaption,
  ImageStyle,
  ImageToolbar,
  ImageUpload,
  ImageResize,
  LinkImage
} from 'ckeditor5'

import { Ckeditor } from '@ckeditor/ckeditor5-vue'

// 引入样式
import 'ckeditor5/ckeditor5.css'

// 为浏览器环境添加polyfill
import { Buffer } from 'buffer'
window.Buffer = Buffer

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  showStats: {
    type: Boolean,
    default: true
  },
  placeholder: {
    type: String,
    default: '在此输入您的内容，或拖拽文件、粘贴图片...'
  },
  height: {
    type: String,
    default: 'auto'
  },
  minHeight: {
    type: String,
    default: '600px'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 响应式数据
const editorData = ref(props.modelValue)
const wordCount = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadMessage = ref('')

// 文件输入引用
const imageInputRef = ref(null)
const wordInputRef = ref(null)
const pdfInputRef = ref(null)

// PDF相关
const showPdfPreview = ref(false)
const currentPdfName = ref('')
const pdfPageCount = ref(0)
const pdfTextContent = ref([])

// Word相关
const showWordPreview = ref(false)
const currentWordName = ref('')
const currentWordSize = ref(0)
const wordHtmlContent = ref('')

let editorInstance = null

// 编辑器样式计算
const editorStyle = computed(() => {
  const style = {}
  
  if (props.height !== 'auto') {
    style.height = props.height
  }
  
  if (props.minHeight !== '600px') {
    style.minHeight = props.minHeight
  }
  
  // 添加CSS自定义属性用于动态计算
  if (props.disabled) {
    // 禁用模式下，没有工具栏和统计信息，编辑器可以占用更多空间
    style['--editor-min-height'] = `calc(100vh - 200px)`
    style['--editor-max-height'] = `calc(100vh - 100px)`
  } else {
    style['--editor-min-height'] = `calc(100vh - 300px)`
    style['--editor-max-height'] = `calc(100vh - 200px)`
  }
  
  return style
})

// 统计信息
const imageCount = computed(() => {
  const imgMatches = editorData.value.match(/<img[^>]*>/g)
  return imgMatches ? imgMatches.length : 0
})

const tableCount = computed(() => {
  const tableMatches = editorData.value.match(/<table[^>]*>/g)
  return tableMatches ? tableMatches.length : 0
})

// 自定义图片上传适配器
class CustomUploadAdapter {
  constructor(loader) {
    this.loader = loader
  }

  upload() {
    return this.loader.file.then(file => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          resolve({
            default: reader.result
          })
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
    })
  }

  abort() {
    // Abort upload process
  }
}

function CustomUploadAdapterPlugin(editor) {
  editor.plugins.get('FileRepository').createUploadAdapter = (loader) => {
    return new CustomUploadAdapter(loader)
  }
}

// 编辑器配置
const editorConfig = computed(() => {
  return {
    licenseKey: 'GPL',
    plugins: [
      Essentials,
      Paragraph,
      Bold,
      Italic,
      Underline,
      Strikethrough,
      Heading,
      Font,
      FontSize,
      FontFamily,
      FontColor,
      FontBackgroundColor,
      Link,
      List,
      ListProperties,
      TodoList,
      Indent,
      IndentBlock,
      Alignment,
      BlockQuote,
      Table,
      TableToolbar,
      TableProperties,
      TableCellProperties,
      MediaEmbed,
      PasteFromOffice,
      WordCount,
      SourceEditing,
      GeneralHtmlSupport,
      CodeBlock,
      Code,
      HorizontalLine,
      PageBreak,
      SpecialCharacters,
      SpecialCharactersEssentials,
      SpecialCharactersArrows,
      SpecialCharactersMathematical,
      RemoveFormat,
      FindAndReplace,
      Highlight,
      Mention,
      AutoLink,
      TextTransformation,
      Image,
      ImageCaption,
      ImageStyle,
      ImageToolbar,
      ImageUpload,
      ImageResize,
      LinkImage,
      CustomUploadAdapterPlugin
    ],
    toolbar: props.disabled ? false : {
      items: [
        'findAndReplace',
        '|',
        'heading',
        '|',
        'fontSize',
        'fontFamily',
        'fontColor',
        'fontBackgroundColor',
        '|',
        'bold',
        'italic',
        'underline',
        'strikethrough',
        'removeFormat',
        '|',
        'link',
        'highlight',
        'code',
        '|',
        'alignment',
        '|',
        'bulletedList',
        'numberedList',
        'todoList',
        '|',
        'outdent',
        'indent',
        '|',
        'blockQuote',
        'codeBlock',
        '|',
        'insertTable',
        'imageUpload',
        'mediaEmbed',
        '|',
        'horizontalLine',
        'pageBreak',
        'specialCharacters',
        '|',
        'sourceEditing',
        '|',
        'undo',
        'redo'
      ],
      shouldNotGroupWhenFull: true
    },
    image: {
      toolbar: props.disabled ? false : [
        'imageStyle:inline',
        'imageStyle:block',
        'imageStyle:side',
        '|',
        'toggleImageCaption',
        'imageTextAlternative',
        '|',
        'linkImage'
      ]
    },
    fontSize: {
      options: [9, 10, 11, 12, 'default', 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
    },
    fontFamily: {
      options: [
        'default',
        'Arial, Helvetica, sans-serif',
        'Courier New, Courier, monospace',
        'Georgia, serif',
        'Lucida Sans Unicode, Lucida Grande, sans-serif',
        'Tahoma, Geneva, sans-serif',
        'Times New Roman, Times, serif',
        'Trebuchet MS, Helvetica, sans-serif',
        'Verdana, Geneva, sans-serif',
        'Microsoft YaHei, 微软雅黑, sans-serif',
        'SimSun, 宋体, serif',
        'SimHei, 黑体, sans-serif'
      ]
    },
    heading: {
      options: [
        { model: 'paragraph', title: '段落', class: 'ck-heading_paragraph' },
        { model: 'heading1', view: 'h1', title: '标题 1', class: 'ck-heading_heading1' },
        { model: 'heading2', view: 'h2', title: '标题 2', class: 'ck-heading_heading2' },
        { model: 'heading3', view: 'h3', title: '标题 3', class: 'ck-heading_heading3' },
        { model: 'heading4', view: 'h4', title: '标题 4', class: 'ck-heading_heading4' }
      ]
    },
    table: {
      contentToolbar: props.disabled ? false : [
        'tableColumn',
        'tableRow',
        'mergeTableCells',
        'tableProperties',
        'tableCellProperties'
      ]
    },
    link: {
      decorators: {
        openInNewTab: {
          mode: 'manual',
          label: '在新标签页打开',
          attributes: {
            target: '_blank',
            rel: 'noopener noreferrer'
          }
        }
      }
    },
    mention: {
      feeds: [
        {
          marker: '@',
          feed: ['@张三', '@李四', '@王五', '@赵六'],
          minimumCharacters: 1
        }
      ]
    },
    wordCount: {
      onUpdate: (stats) => {
        wordCount.value = stats
      }
    },
    placeholder: props.placeholder,
    language: 'zh-cn'
  }
})

// 触发文件上传
const triggerImageUpload = () => {
  imageInputRef.value?.click()
}

const triggerWordUpload = () => {
  wordInputRef.value?.click()
}

const triggerPdfUpload = () => {
  pdfInputRef.value?.click()
}

// 图片上传处理
const handleImageUpload = async (event) => {
  const files = Array.from(event.target.files)
  if (!files.length) return
  
  for (const file of files) {
    if (!file.type.startsWith('image/')) {
      ElMessage.error(`文件 ${file.name} 不是图片格式`)
      continue
    }
    
    await insertImageFromFile(file)
  }
  
  event.target.value = ''
}

const insertImageFromFile = async (file) => {
  try {
    const reader = new FileReader()
    reader.onload = (e) => {
      if (editorInstance) {
        const imageUrl = e.target.result
        const viewFragment = editorInstance.data.processor.toView(
          `<figure class="image"><img src="${imageUrl}" alt="${file.name}"><figcaption>图片: ${file.name}</figcaption></figure>`
        )
        const modelFragment = editorInstance.data.toModel(viewFragment)
        editorInstance.model.insertContent(modelFragment)
      }
    }
    reader.readAsDataURL(file)
  } catch (error) {
    console.error('图片插入失败:', error)
    ElMessage.error('图片插入失败: ' + error.message)
  }
}

// Word文档处理
const handleWordUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (!file.name.toLowerCase().match(/\.(docx|doc)$/)) {
    ElMessage.error('请选择Word文档文件 (.docx 或 .doc)')
    return
  }
  
  await processWordFile(file)
  event.target.value = ''
}

const processWordFile = async (file) => {
  try {
    isUploading.value = true
    uploadProgress.value = 0
    uploadMessage.value = '正在读取Word文档...'
    
    // 动态导入mammoth
    const mammoth = await import('mammoth')
    
    uploadProgress.value = 30
    uploadMessage.value = '正在解析文档内容...'
    
    const arrayBuffer = await file.arrayBuffer()
    uploadProgress.value = 60
    
    uploadMessage.value = '正在转换格式...'
    const result = await mammoth.convertToHtml({
      arrayBuffer,
      options: {
        styleMap: [
          "p[style-name='Special'] => p.special",
          "p[style-name='Heading1'] => h1",
          "p[style-name='Heading2'] => h2",
          "p[style-name='Heading3'] => h3"
        ]
      }
    })
    
    uploadProgress.value = 90
    uploadMessage.value = '处理完成，准备预览...'
    
    currentWordName.value = file.name
    currentWordSize.value = file.size
    wordHtmlContent.value = result.value
    
    uploadProgress.value = 100
    uploadMessage.value = 'Word文档处理成功！'
    
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
      uploadMessage.value = ''
      showWordPreview.value = true
    }, 1000)
    
  } catch (error) {
    console.error('Word文档处理失败:', error)
    ElMessage.error('Word文档处理失败: ' + error.message)
    isUploading.value = false
    uploadProgress.value = 0
    uploadMessage.value = ''
  }
}

const insertWordContent = () => {
  if (editorInstance && wordHtmlContent.value) {
    const contentWithHeader = `<h2>📄 ${currentWordName.value}</h2>${wordHtmlContent.value}`
    const viewFragment = editorInstance.data.processor.toView(contentWithHeader)
    const modelFragment = editorInstance.data.toModel(viewFragment)
    editorInstance.model.insertContent(modelFragment)
  }
  showWordPreview.value = false
}

const closeWordPreview = () => {
  showWordPreview.value = false
}

// PDF处理功能
const handlePdfUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    ElMessage.error('请选择PDF文档文件')
    return
  }
  
  await processPdfFile(file)
  event.target.value = ''
}

const processPdfFile = async (file) => {
  try {
    isUploading.value = true
    uploadProgress.value = 0
    uploadMessage.value = '正在读取PDF文档...'
    
    const pdfjsLib = await import('pdfjs-dist')
    
    // 修复worker配置问题
    if (typeof pdfjsLib.GlobalWorkerOptions !== 'undefined') {
      // 设置正确的worker路径
      pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
        'pdfjs-dist/build/pdf.worker.min.mjs',
        import.meta.url
      ).toString()
    }
    
    uploadProgress.value = 20
    uploadMessage.value = '正在解析PDF内容...'
    
    const arrayBuffer = await file.arrayBuffer()
    uploadProgress.value = 40
    
    const pdf = await pdfjsLib.getDocument(arrayBuffer).promise
    uploadProgress.value = 60
    uploadMessage.value = '正在提取文本内容...'
    
    const textContent = []
    const numPages = pdf.numPages
    
    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
      const page = await pdf.getPage(pageNum)
      const text = await page.getTextContent()
      const pageText = text.items.map(item => item.str).join(' ')
      textContent.push(pageText)
      uploadProgress.value = 60 + (pageNum / numPages) * 30
    }
    
    uploadProgress.value = 95
    uploadMessage.value = '处理完成，准备预览...'
    
    currentPdfName.value = file.name
    pdfPageCount.value = numPages
    pdfTextContent.value = textContent
    
    uploadProgress.value = 100
    uploadMessage.value = 'PDF处理成功！'
    
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
      uploadMessage.value = ''
      showPdfPreview.value = true
    }, 1000)
    
  } catch (error) {
    console.error('PDF处理失败:', error)
    ElMessage.error('PDF文档处理失败: ' + error.message)
    isUploading.value = false
    uploadProgress.value = 0
    uploadMessage.value = ''
  }
}

const insertPdfContent = () => {
  if (editorInstance && pdfTextContent.value.length > 0) {
    let htmlContent = `<h2>📑 ${currentPdfName.value}</h2>`
    
    pdfTextContent.value.forEach((pageText, index) => {
      if (pageText.trim()) {
        htmlContent += `<h3>第 ${index + 1} 页</h3>`
        const paragraphs = pageText.split(/\n\s*\n/).filter(p => p.trim())
        paragraphs.forEach(paragraph => {
          if (paragraph.trim()) {
            htmlContent += `<p>${paragraph.trim()}</p>`
          }
        })
      }
    })
    
    const viewFragment = editorInstance.data.processor.toView(htmlContent)
    const modelFragment = editorInstance.data.toModel(viewFragment)
    editorInstance.model.insertContent(modelFragment)
  }
  
  showPdfPreview.value = false
}

const closePdfPreview = () => {
  showPdfPreview.value = false
}

// 粘贴处理
const handlePaste = async (event) => {
  const clipboardData = event.clipboardData || window.clipboardData
  const items = clipboardData.items
  
  // 检查是否有图片
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) {
        await insertImageFromFile(file)
      }
      return
    }
  }
  
  // 检查HTML内容（富文本粘贴）
  const htmlData = clipboardData.getData('text/html')
  if (htmlData && htmlData.includes('<img')) {
    // 处理包含图片的HTML内容
    setTimeout(() => {
      // 让CKEditor先处理粘贴，然后我们处理图片
      processInlineImages()
    }, 100)
  }
}

const processInlineImages = async () => {
  // 这个函数可以用来处理粘贴的HTML中的图片
  // 例如将base64图片或外部链接图片进行处理
  console.log('处理粘贴的图片内容')
}

// 拖拽处理
const handleDragOver = (event) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDrop = async (event) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = Array.from(event.dataTransfer.files)
  
  for (const file of files) {
    if (file.type.startsWith('image/')) {
      await insertImageFromFile(file)
    } else if (file.name.toLowerCase().endsWith('.pdf')) {
      await processPdfFile(file)
    } else if (file.name.toLowerCase().match(/\.(docx|doc)$/)) {
      await processWordFile(file)
    } else {
      ElMessage.warning(`不支持的文件类型: ${file.name}`)
    }
  }
}

// 导出功能
const handleExport = async (command) => {
  switch (command) {
    case 'word':
      await exportToWord()
      break
    case 'pdf':
      await exportToPdf()
      break
    case 'html':
      exportToHtml()
      break
  }
}

const exportToWord = async () => {
  try {
    // 动态导入所需库
    const { Document, Paragraph, TextRun, HeadingLevel, Packer } = await import('docx')
    const { saveAs } = await import('file-saver')
    
    // 解析HTML内容为更好的Word文档结构
    const htmlContent = editorData.value
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = htmlContent
    
    const children = []
    
    // 添加标题
    children.push(new Paragraph({
      text: "从富文本编辑器导出的文档",
      heading: HeadingLevel.TITLE,
    }))
    
    children.push(new Paragraph({
      children: [
        new TextRun({
          text: "导出时间: " + new Date().toLocaleString(),
          italics: true,
        }),
      ],
    }))
    
    children.push(new Paragraph({ text: "" })) // 空行
    
    // 解析HTML内容
    const parseElement = (element) => {
      const tagName = element.tagName?.toLowerCase()
      const text = element.textContent || ''
      
      switch (tagName) {
        case 'h1':
          return new Paragraph({
            text: text,
            heading: HeadingLevel.HEADING_1,
          })
        case 'h2':
          return new Paragraph({
            text: text,
            heading: HeadingLevel.HEADING_2,
          })
        case 'h3':
          return new Paragraph({
            text: text,
            heading: HeadingLevel.HEADING_3,
          })
        case 'p':
          return new Paragraph({
            text: text,
          })
        default:
          if (text.trim()) {
            return new Paragraph({
              text: text,
            })
          }
          return null
      }
    }
    
    // 处理所有元素
    const elements = tempDiv.querySelectorAll('h1, h2, h3, p')
    for (const element of elements) {
      const paragraph = parseElement(element)
      if (paragraph) {
        children.push(paragraph)
      }
    }
    
    // 如果没有解析到内容，添加原始文本
    if (children.length <= 3) {
      const plainText = tempDiv.textContent || editorData.value.replace(/<[^>]*>/g, '')
      if (plainText.trim()) {
        children.push(new Paragraph({
          text: plainText,
        }))
      }
    }
    
    // 创建Word文档
    const doc = new Document({
      sections: [{
        properties: {},
        children: children,
      }],
    })
    
    // 生成文档 - 使用Blob直接处理，避免buffer兼容性问题
    const blob = await Packer.toBlob(doc)
    
    saveAs(blob, `富文本导出_${new Date().toISOString().slice(0, 10)}.docx`)
    
  } catch (error) {
    console.error('Word导出失败:', error)
    ElMessage.error('Word导出失败: ' + error.message)
  }
}

const exportToPdf = async () => {
  try {
    // 动态导入所需库
    const { jsPDF } = await import('jspdf')
    const html2canvas = await import('html2canvas')
    
    // 创建一个临时div来渲染内容
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = editorData.value
    tempDiv.style.position = 'absolute'
    tempDiv.style.left = '-9999px'
    tempDiv.style.top = '-9999px'
    tempDiv.style.width = '800px'
    tempDiv.style.padding = '20px'
    tempDiv.style.fontFamily = 'Arial, sans-serif'
    tempDiv.style.fontSize = '14px'
    tempDiv.style.lineHeight = '1.6'
    tempDiv.style.color = '#000'
    tempDiv.style.backgroundColor = '#fff'
    
    document.body.appendChild(tempDiv)
    
    try {
      // 将HTML转换为Canvas
      const canvas = await html2canvas.default(tempDiv, {
        width: 800,
        height: tempDiv.scrollHeight,
        scale: 2,
        useCORS: true,
        allowTaint: true
      })
      
      // 创建PDF
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('p', 'mm', 'a4')
      
      const imgWidth = 210 // A4 width in mm
      const pageHeight = 295 // A4 height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      let heightLeft = imgHeight
      
      let position = 0
      
      // 添加第一页
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
      
      // 如果内容超过一页，添加更多页面
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }
      
      // 保存PDF
      pdf.save(`富文本导出_${new Date().toISOString().slice(0, 10)}.pdf`)
      
    } finally {
      // 清理临时元素
      document.body.removeChild(tempDiv)
    }
    
  } catch (error) {
    console.error('PDF导出失败:', error)
    ElMessage.error('PDF导出失败: ' + error.message)
  }
}

const exportToHtml = () => {
  try {
    const blob = new Blob([editorData.value], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `富文本导出_${new Date().toISOString().slice(0, 10)}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('HTML导出成功')
  } catch (error) {
    console.error('HTML导出失败:', error)
    ElMessage.error('HTML导出失败: ' + error.message)
  }
}

// 工具函数
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 事件处理函数
const onEditorReady = (editor) => {
  console.log('编辑器已就绪:', editor)
  editorInstance = editor
}

const onEditorFocus = () => {
  console.log('编辑器获得焦点')
}

const onEditorBlur = () => {
  console.log('编辑器失去焦点')
  isDragOver.value = false
}

const onEditorInput = () => {
  console.log('编辑器内容已更改')
  emit('update:modelValue', editorData.value)
  emit('change', editorData.value)
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== editorData.value) {
    editorData.value = newValue
  }
})

// 监听编辑器数据变化
watch(editorData, (newValue) => {
  emit('update:modelValue', newValue)
  emit('change', newValue)
})

// 窗口大小变化处理
const handleResize = () => {
  // 触发编辑器重新计算尺寸
  if (editorInstance) {
    nextTick(() => {
      editorInstance.editing.view.focus()
    })
  }
}

// 组件挂载时添加窗口大小监听
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

// 组件卸载时移除监听器
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.rich-text-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 600px;
  max-height: 100vh;
  background: #ffffff;
  position: relative;
  box-sizing: border-box;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
}

.toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.editor-wrapper {
  flex: 1;
  min-height: calc(100vh - 200px);
  max-height: calc(100vh - 120px);
  border: 1px solid #e9ecef;
  border-top: none;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
  transition: all 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.editor-wrapper.drag-over {
  border: 2px dashed #409eff;
  background-color: rgba(64, 158, 255, 0.1);
  transform: scale(1.01);
}

.main-editor {
  height: 100%;
  flex: 1;
  min-height: 0;
}

.feature-hints {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-top: 1px solid #e9ecef;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.hint-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #409eff;
}

.stats-info {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #6c757d;
}

.stat-value {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
}

.pdf-info,
.word-info {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid #e9ecef;
}

.pdf-info p,
.word-info p {
  margin: 6px 0;
  color: #495057;
  font-weight: 500;
}

.pdf-content,
.word-content {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}

.pdf-page {
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 16px;
  margin-bottom: 16px;
}

.pdf-page:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.pdf-page h4 {
  color: #409eff;
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.pdf-page pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  color: #333;
  margin: 0;
  background: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.upload-progress {
  text-align: center;
}

/* CKEditor 样式调整 */
:deep(.ck-editor__editable) {
  min-height: var(--editor-min-height, calc(100vh - 300px));
  max-height: var(--editor-max-height, calc(100vh - 200px));
  height: 100%;
  font-size: 14px;
  line-height: 1.6;
  padding: 16px;
  overflow-y: auto;
  box-sizing: border-box;
}

/* 禁用模式下的编辑器样式 */
.rich-text-editor:has(.ck-editor--disabled) .editor-wrapper {
  border: none;
  border-radius: 0;
}

:deep(.ck-editor--disabled .ck-editor__editable) {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

:deep(.ck-toolbar) {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  border-bottom: 1px solid #e9ecef;
}

:deep(.ck-editor__editable) {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

:deep(.ck-editor__editable:focus) {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

/* 标题样式优化 - 让标题层级更加明显 */
:deep(.ck-editor__editable h1) {
  font-size: 2.5rem !important;
  font-weight: 700 !important;
  color: #1a202c !important;
  margin: 2rem 0 1.5rem 0 !important;
  line-height: 1.2 !important;
  letter-spacing: -0.025em !important;
}

:deep(.ck-editor__editable h2) {
  font-size: 2rem !important;
  font-weight: 600 !important;
  color: #2d3748 !important;
  margin: 1.75rem 0 1.25rem 0 !important;
  line-height: 1.3 !important;
  letter-spacing: -0.02em !important;
}

:deep(.ck-editor__editable h3) {
  font-size: 1.5rem !important;
  font-weight: 600 !important;
  color: #4a5568 !important;
  margin: 1.5rem 0 1rem 0 !important;
  line-height: 1.4 !important;
}

:deep(.ck-editor__editable h4) {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #718096 !important;
  margin: 1.25rem 0 0.75rem 0 !important;
  line-height: 1.4 !important;
}

:deep(.ck-editor__editable h5) {
  font-size: 1.125rem !important;
  font-weight: 600 !important;
  color: #a0aec0 !important;
  margin: 1rem 0 0.5rem 0 !important;
  line-height: 1.4 !important;
}

:deep(.ck-editor__editable h6) {
  font-size: 1rem !important;
  font-weight: 600 !important;
  color: #cbd5e0 !important;
  margin: 0.75rem 0 0.5rem 0 !important;
  line-height: 1.4 !important;
}

/* 段落样式优化 */
:deep(.ck-editor__editable p) {
  margin: 0.75rem 0 !important;
  line-height: 1.7 !important;
  color: #2d3748 !important;
}

/* 列表样式优化 */
:deep(.ck-editor__editable ul),
:deep(.ck-editor__editable ol) {
  margin: 0.75rem 0 !important;
  padding-left: 1.5rem !important;
}

:deep(.ck-editor__editable li) {
  margin: 0.25rem 0 !important;
  line-height: 1.6 !important;
}

/* 引用样式优化 */
:deep(.ck-editor__editable blockquote) {
  border-left: 4px solid #4299e1 !important;
  padding: 1rem 1.5rem !important;
  margin: 1.5rem 0 !important;
  background: linear-gradient(90deg, rgba(66, 153, 225, 0.1) 0%, rgba(66, 153, 225, 0.05) 100%) !important;
  border-radius: 0 8px 8px 0 !important;
  font-style: italic !important;
  color: #4a5568 !important;
}

/* 代码样式优化 */
:deep(.ck-editor__editable code) {
  background: #f7fafc !important;
  padding: 0.125rem 0.25rem !important;
  border-radius: 4px !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
  font-size: 0.875rem !important;
  color: #e53e3e !important;
  border: 1px solid #e2e8f0 !important;
}

:deep(.ck-editor__editable pre) {
  background: #2d3748 !important;
  color: #e2e8f0 !important;
  padding: 1.5rem !important;
  border-radius: 8px !important;
  overflow-x: auto !important;
  margin: 1.5rem 0 !important;
  border: 1px solid #4a5568 !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
  font-size: 0.875rem !important;
  line-height: 1.6 !important;
}

/* 表格样式优化 */
:deep(.ck-editor__editable table) {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 1.5rem 0 !important;
  border-radius: 8px !important;
  overflow: hidden !important;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
}

:deep(.ck-editor__editable th) {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
  color: white !important;
  padding: 0.75rem 1rem !important;
  font-weight: 600 !important;
  text-align: left !important;
  border: none !important;
}

:deep(.ck-editor__editable td) {
  padding: 0.75rem 1rem !important;
  border: 1px solid #e2e8f0 !important;
  background: white !important;
}

:deep(.ck-editor__editable tr:nth-child(even) td) {
  background: #f7fafc !important;
}

/* 链接样式优化 */
:deep(.ck-editor__editable a) {
  color: #3182ce !important;
  text-decoration: none !important;
  border-bottom: 1px solid transparent !important;
  transition: all 0.2s ease !important;
}

:deep(.ck-editor__editable a:hover) {
  color: #2c5282 !important;
  border-bottom-color: #2c5282 !important;
}

/* 强调文本样式 */
:deep(.ck-editor__editable strong) {
  font-weight: 700 !important;
  color: #2d3748 !important;
}

:deep(.ck-editor__editable em) {
  font-style: italic !important;
  color: #4a5568 !important;
}

/* 高亮文本样式 */
:deep(.ck-editor__editable mark) {
  background: linear-gradient(120deg, #fef5e7 0%, #fed7aa 100%) !important;
  padding: 0.125rem 0.25rem !important;
  border-radius: 3px !important;
  color: #744210 !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .rich-text-editor {
    height: 100vh;
    min-height: 500px;
  }
  
  .editor-wrapper {
    min-height: calc(100vh - 180px);
    max-height: calc(100vh - 100px);
  }
  
  .editor-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .toolbar-right {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .feature-hints {
    flex-direction: column;
    gap: 8px;
  }
  
  .stats-info {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  :deep(.ck-editor__editable) {
    min-height: calc(100vh - 250px);
    max-height: calc(100vh - 150px);
    padding: 12px;
    font-size: 13px;
  }
}

/* 大屏幕优化 */
@media (min-width: 1200px) {
  .rich-text-editor {
    height: 100vh;
    min-height: 800px;
  }
  
  .editor-wrapper {
    min-height: calc(100vh - 150px);
    max-height: calc(100vh - 80px);
  }
  
  :deep(.ck-editor__editable) {
    min-height: calc(100vh - 250px);
    max-height: calc(100vh - 120px);
    font-size: 15px;
    line-height: 1.7;
  }
}

/* 超大屏幕优化 */
@media (min-width: 1920px) {
  .rich-text-editor {
    height: 100vh;
    min-height: 1000px;
  }
  
  .editor-wrapper {
    min-height: calc(100vh - 120px);
    max-height: calc(100vh - 60px);
  }
  
  :deep(.ck-editor__editable) {
    min-height: calc(100vh - 200px);
    max-height: calc(100vh - 100px);
    font-size: 16px;
    line-height: 1.8;
  }
}
</style> 