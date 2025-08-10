<template>
  <div class="home-dashboard">
    <!-- 顶部欢迎区域 -->
    <div class="welcome-header">
      <div class="welcome-content">
        <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          AI Native Platform
      </h1>
        <p class="text-lg text-gray-600 mt-2">
          智能原生平台 · 数据驱动未来
        </p>
        <div class="flex items-center gap-4 mt-4">
          <el-button type="primary" icon="Refresh" @click="refreshData" :loading="loading">
            刷新数据
          </el-button>
          <span class="text-sm text-gray-500">
            最后更新: {{ formatTime(lastUpdateTime) }}
          </span>
        </div>
      </div>
      <div class="welcome-decoration">
        <div class="floating-elements">
          <div class="floating-circle"></div>
          <div class="floating-square"></div>
          <div class="floating-triangle"></div>
        </div>
      </div>
    </div>

    <!-- 快速操作区域 -->
    <div class="quick-actions">
      <h3 class="section-title">快速操作</h3>
      <div class="actions-grid">
        <router-link to="/knowledge-namespace" class="action-card">
          <div class="action-icon">
            <i class="el-icon-folder-add"></i>
          </div>
          <div class="action-content">
            <div class="action-title">创建知识库</div>
            <div class="action-desc">构建你的知识体系</div>
          </div>
        </router-link>

        <router-link to="/bot-management" class="action-card">
          <div class="action-icon">
            <i class="el-icon-s-custom"></i>
          </div>
          <div class="action-content">
            <div class="action-title">创建机器人</div>
            <div class="action-desc">打造智能助手</div>
          </div>
        </router-link>
      </div>
    </div>

    <!-- 主要统计卡片 -->
    <div class="stats-grid">
      <div class="stats-card highlight-card">
        <div class="stats-icon-wrapper primary">
          <i class="el-icon-cpu"></i>
        </div>
        <div class="stats-content">
          <div class="stats-number" :class="{ 'skeleton': loading }">
            {{ loading ? '--' : dashboardData.user_stats?.total_llm_models || 0 }}
          </div>
          <div class="stats-label">接入大模型</div>
          <div class="stats-growth positive">
            <i class="el-icon-top"></i>
            +{{ dashboardData.growth_stats?.user_growth || 0 }}%
          </div>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon-wrapper success">
          <i class="el-icon-folder-opened"></i>
        </div>
        <div class="stats-content">
          <div class="stats-number" :class="{ 'skeleton': loading }">
            {{ loading ? '--' : dashboardData.user_stats?.total_namespaces || 0 }}
          </div>
          <div class="stats-label">知识库总数</div>
          <div class="stats-breakdown">
            创建: {{ dashboardData.user_stats?.created_namespaces || 0 }} / 
            协作: {{ dashboardData.user_stats?.collaborated_namespaces || 0 }}
          </div>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon-wrapper info">
          <i class="el-icon-document"></i>
        </div>
        <div class="stats-content">
          <div class="stats-number" :class="{ 'skeleton': loading }">
            {{ loading ? '--' : dashboardData.user_stats?.total_documents || 0 }}
          </div>
          <div class="stats-label">文档总数</div>
          <div class="stats-breakdown">
            普通: {{ dashboardData.user_stats?.normal_documents || 0 }} / 
            工具: {{ dashboardData.user_stats?.tool_documents || 0 }}
          </div>
        </div>
      </div>
      
      <div class="stats-card">
        <div class="stats-icon-wrapper warning">
          <i class="el-icon-s-custom"></i>
        </div>
        <div class="stats-content">
          <div class="stats-number" :class="{ 'skeleton': loading }">
            {{ loading ? '--' : dashboardData.user_stats?.created_bots || 0 }}
          </div>
          <div class="stats-label">创建的机器人</div>
          <div class="stats-growth positive">
            <i class="el-icon-top"></i>
            +{{ dashboardData.growth_stats?.bot_growth || 0 }}%
          </div>
        </div>
      </div>
    </div>

    <!-- 数据可视化区域 -->
    <div class="charts-section">
      <div class="chart-container">
        <div class="chart-header">
          <h3 class="chart-title">个人数据概览</h3>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-color primary"></span>
              知识库
            </span>
            <span class="legend-item">
              <span class="legend-color success"></span>
              文档
            </span>
            <span class="legend-item">
              <span class="legend-color warning"></span>
              机器人
            </span>
          </div>
        </div>
        <div class="chart-content">
          <canvas ref="userStatsChart" class="stats-chart"></canvas>
        </div>
        </div>
        
      <div class="chart-container">
        <div class="chart-header">
          <h3 class="chart-title">平台趋势分析</h3>
          <el-select v-model="selectedMetric" size="small" class="metric-selector">
            <el-option label="用户增长" value="users"></el-option>
            <el-option label="知识库增长" value="namespaces"></el-option>
            <el-option label="文档增长" value="documents"></el-option>
            <el-option label="机器人增长" value="bots"></el-option>
          </el-select>
        </div>
        <div class="chart-content">
          <canvas ref="platformTrendChart" class="trend-chart"></canvas>
        </div>
      </div>
        </div>
        
    <!-- 平台统计信息 -->
    <div class="platform-stats">
      <div class="platform-header">
        <h3 class="section-title">平台统计</h3>
        <div class="platform-date">
          {{ formatDate(dashboardData.platform_stats?.date) }}
        </div>
      </div>
      <div class="platform-grid">
        <div class="platform-item">
          <div class="platform-number">{{ dashboardData.platform_stats?.total_users || 0 }}</div>
          <div class="platform-label">总用户数</div>
        </div>
        <div class="platform-item">
          <div class="platform-number">{{ dashboardData.platform_stats?.active_users || 0 }}</div>
          <div class="platform-label">活跃用户</div>
        </div>
        <div class="platform-item">
          <div class="platform-number">{{ dashboardData.platform_stats?.total_namespaces || 0 }}</div>
          <div class="platform-label">平台知识库</div>
        </div>
        <div class="platform-item">
          <div class="platform-number">{{ dashboardData.platform_stats?.total_documents || 0 }}</div>
          <div class="platform-label">平台文档</div>
        </div>
        <div class="platform-item">
          <div class="platform-number">{{ dashboardData.platform_stats?.total_bots || 0 }}</div>
          <div class="platform-label">平台机器人</div>
        </div>
        <div class="platform-item">
          <div class="platform-number">{{ dashboardData.platform_stats?.total_llm_models || 0 }}</div>
          <div class="platform-label">大模型总数</div>
        </div>
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Chart, registerables } from 'chart.js'
import { summaryAPI } from '@/api.js'

// 注册Chart.js组件
Chart.register(...registerables)

// 响应式数据
const loading = ref(false)
const lastUpdateTime = ref(new Date())
const selectedMetric = ref('users')
const userStatsChart = ref(null)
const platformTrendChart = ref(null)
let userChart = null
let trendChart = null

// 仪表板数据
const dashboardData = reactive({
  user_stats: {},
  platform_stats: {},
  growth_stats: {}
})

// 获取仪表板数据
const fetchDashboardData = async () => {
  try {
    loading.value = true
    const response = await summaryAPI.getDashboard()
    
    Object.assign(dashboardData, response.data)
    lastUpdateTime.value = new Date()
    
    // 更新图表
    await nextTick()
    updateCharts()
    
  } catch (error) {
    console.error('获取仪表板数据失败:', error)
    ElMessage.error('获取数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  try {
    // 先刷新用户统计
    await summaryAPI.refreshUserStats()
    // 再获取最新数据
    await fetchDashboardData()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  }
}

// 更新图表
const updateCharts = () => {
  updateUserStatsChart()
  updatePlatformTrendChart()
}

// 更新用户统计图表
const updateUserStatsChart = () => {
  if (!userStatsChart.value) return
  
  const ctx = userStatsChart.value.getContext('2d')
  
  if (userChart) {
    userChart.destroy()
  }
  
  const data = dashboardData.user_stats || {}
  
  userChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['知识库', '文档', '机器人'],
      datasets: [{
        data: [
          data.total_namespaces || 0,
          data.total_documents || 0,
          data.created_bots || 0
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',   // blue-500
          'rgba(34, 197, 94, 0.8)',    // green-500
          'rgba(251, 191, 36, 0.8)',   // amber-500
        ],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      cutout: '60%'
    }
  })
}

// 更新平台趋势图表
const updatePlatformTrendChart = () => {
  if (!platformTrendChart.value) return
  
  const ctx = platformTrendChart.value.getContext('2d')
  
  if (trendChart) {
    trendChart.destroy()
  }
  
  // 模拟趋势数据（实际应用中应该从API获取历史数据）
  const labels = ['7天前', '6天前', '5天前', '4天前', '3天前', '2天前', '昨天', '今天']
  const growthData = dashboardData.growth_stats || {}
  
  // 根据选择的指标生成模拟数据
  const getMetricData = (metric) => {
    const baseValue = {
      users: dashboardData.platform_stats?.total_users || 100,
      namespaces: dashboardData.platform_stats?.total_namespaces || 50,
      documents: dashboardData.platform_stats?.total_documents || 200,
      bots: dashboardData.platform_stats?.total_bots || 30
    }[metric] || 100
    
    const growth = growthData[`${metric === 'users' ? 'user' : metric.slice(0, -1)}_growth`] || 5
    
    return labels.map((_, index) => {
      const dayProgress = (index + 1) / labels.length
      const randomVariation = (Math.random() - 0.5) * 10
      return Math.round(baseValue * (1 - growth / 100 * (1 - dayProgress)) + randomVariation)
    })
  }
  
  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: selectedMetric.value === 'users' ? '用户数' : 
               selectedMetric.value === 'namespaces' ? '知识库数' :
               selectedMetric.value === 'documents' ? '文档数' : '机器人数',
        data: getMetricData(selectedMetric.value),
        borderColor: 'rgba(59, 130, 246, 1)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: false,
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          }
        },
        x: {
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  })
}

// 时间格式化
const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

const formatDate = (date) => {
  if (!date) return '今天'
  return new Date(date).toLocaleDateString('zh-CN')
}

// 监听指标选择变化
watch(selectedMetric, () => {
  updatePlatformTrendChart()
})

// 组件挂载时获取数据
onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.home-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 2rem;
}

/* 欢迎区域 */
.welcome-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
  position: relative;
  overflow: hidden;
}

.welcome-content {
  flex: 1;
}

.welcome-decoration {
  position: relative;
  width: 200px;
  height: 150px;
}

.floating-elements {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.floating-circle,
.floating-square,
.floating-triangle {
  position: absolute;
  opacity: 0.3;
  animation: floating 6s ease-in-out infinite;
}

.floating-circle {
  width: 60px;
  height: 60px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  border-radius: 50%;
  top: 20px;
  right: 40px;
  animation-delay: 0s;
}

.floating-square {
  width: 40px;
  height: 40px;
  background: linear-gradient(45deg, #f093fb, #f5576c);
  border-radius: 8px;
  top: 80px;
  right: 100px;
  animation-delay: 2s;
}

.floating-triangle {
  width: 0;
  height: 0;
  border-left: 25px solid transparent;
  border-right: 25px solid transparent;
  border-bottom: 43px solid #4facfe;
  top: 40px;
  right: 20px;
  animation-delay: 4s;
}

@keyframes floating {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stats-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stats-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.stats-card.highlight-card {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1));
  border: 2px solid rgba(59, 130, 246, 0.3);
}

.stats-icon-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  flex-shrink: 0;
}

.stats-icon-wrapper.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stats-icon-wrapper.success {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.stats-icon-wrapper.info {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.stats-icon-wrapper.warning {
  background: linear-gradient(135deg, #fa709a, #fee140);
}

.stats-content {
  flex: 1;
}

.stats-number {
  font-size: 2rem;
  font-weight: bold;
  color: #1f2937;
  margin-bottom: 0.25rem;
  transition: all 0.3s ease;
}

.stats-number.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  height: 2rem;
  width: 60px;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.stats-label {
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.stats-breakdown {
  font-size: 0.75rem;
  color: #9ca3af;
}

.stats-growth {
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.stats-growth.positive {
  color: #10b981;
}

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.chart-legend {
  display: flex;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.primary { background-color: rgba(59, 130, 246, 0.8); }
.legend-color.success { background-color: rgba(34, 197, 94, 0.8); }
.legend-color.warning { background-color: rgba(251, 191, 36, 0.8); }

.chart-content {
  height: 300px;
  position: relative;
}

.stats-chart,
.trend-chart {
  width: 100% !important;
  height: 100% !important;
}

.metric-selector {
  width: 120px;
}

/* 平台统计 */
.platform-stats {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.platform-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.platform-date {
  color: #6b7280;
  font-size: 0.875rem;
}

.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.platform-item {
  text-align: center;
  padding: 1rem;
  border-radius: 8px;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.1);
}

.platform-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #3b82f6;
  margin-bottom: 0.5rem;
}

.platform-label {
  color: #6b7280;
  font-size: 0.875rem;
}

/* 快速操作 */
.quick-actions {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-top: 1rem;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.7));
  border: 1px solid rgba(0, 0, 0, 0.05);
  text-decoration: none;
  color: inherit;
  transition: all 0.3s ease;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0.9));
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  flex-shrink: 0;
}

.action-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.action-desc {
  font-size: 0.75rem;
  color: #6b7280;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home-dashboard {
    padding: 1rem;
  }
  
  .welcome-header {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }
  
  .welcome-decoration {
    display: none;
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .platform-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .platform-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>