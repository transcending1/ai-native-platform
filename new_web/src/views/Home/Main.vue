<!-- src/views/Home.vue -->
<template>
  <div class="home-container">
    <div class="welcome-section">
      <h1 class="text-3xl font-bold text-gray-900 mb-4">
        欢迎使用 AI Native Platform
      </h1>
      <p class="text-gray-600 mb-8">
        这是一个基于 Vue 3 + Element Plus 的现代化管理平台
      </p>
    </div>

    <!-- 富文本编辑器测试区域 -->
    <div class="editor-test-section">
      <h2 class="text-2xl font-bold text-gray-900 mb-4">
        富文本编辑器高度适配测试
      </h2>
      <p class="text-gray-600 mb-4">
        测试编辑器在不同屏幕尺寸下的高度适配效果
      </p>
      
      <div class="editor-container" style="height: 70vh; min-height: 500px;">
        <RichTextEditor
          v-model="testContent"
          :disabled="false"
          :show-stats="true"
          placeholder="请在此测试富文本编辑器的内容输入..."
          @change="handleContentChange"
        />
      </div>
      
      <div class="test-info mt-4 p-4 bg-blue-50 rounded-lg">
        <h3 class="font-semibold text-blue-900 mb-2">测试说明：</h3>
        <ul class="text-sm text-blue-800 space-y-1">
          <li>• 尝试调整浏览器窗口大小，观察编辑器高度变化</li>
          <li>• 在不同设备上测试响应式效果</li>
          <li>• 验证编辑器是否充分利用可用空间</li>
          <li>• 检查工具栏、内容区域、统计信息的布局</li>
        </ul>
      </div>
    </div>

    <div class="features-section mt-12">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">平台特性</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="feature-card">
          <div class="feature-icon">🚀</div>
          <h3 class="feature-title">高性能</h3>
          <p class="feature-description">
            基于 Vue 3 的 Composition API 和现代构建工具，提供卓越的性能表现
          </p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">🎨</div>
          <h3 class="feature-title">现代化 UI</h3>
          <p class="feature-description">
            采用 Element Plus 组件库，提供美观且一致的用户界面
          </p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">📱</div>
          <h3 class="feature-title">响应式设计</h3>
          <p class="feature-description">
            完美适配各种设备尺寸，从手机到桌面都有良好的使用体验
          </p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">🔧</div>
          <h3 class="feature-title">易于扩展</h3>
          <p class="feature-description">
            模块化架构设计，便于功能扩展和维护
          </p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">🛡️</div>
          <h3 class="feature-title">安全可靠</h3>
          <p class="feature-description">
            内置安全机制，保护用户数据和系统安全
          </p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">📊</div>
          <h3 class="feature-title">数据驱动</h3>
          <p class="feature-description">
            强大的数据管理和分析能力，支持复杂的业务需求
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RichTextEditor from '@/components/RichTextEditor.vue'

// 测试内容
const testContent = ref('')

// 处理内容变化
const handleContentChange = (content) => {
  console.log('编辑器内容变化:', content)
}
</script>

<style scoped>
.home-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  text-align: center;
  margin-bottom: 3rem;
}

.editor-test-section {
  margin-bottom: 3rem;
}

.editor-container {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.test-info {
  border: 1px solid #dbeafe;
}

.features-section {
  margin-top: 3rem;
}

.feature-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.5rem;
}

.feature-description {
  color: #6b7280;
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home-container {
    padding: 1rem;
  }
  
  .editor-container {
    height: 60vh !important;
    min-height: 400px !important;
  }
}

@media (min-width: 1200px) {
  .editor-container {
    height: 80vh !important;
    min-height: 600px !important;
  }
}
</style>

