// 应用配置文件
export default {
  // 应用名称
  appName: 'Robot管理系统',
  
  // 底部版权信息
  footerText: 'Copyright © 2025 Robot',
  
  // 侧边栏配置
  sidebar: {
    // 是否默认折叠
    collapsed: false,
    // 宽度
    width: '256px',
    // 折叠后宽度
    collapsedWidth: '64px'
  },
  
  // 面包屑配置
  breadcrumb: {
    // 是否显示首页图标
    showHomeIcon: true,
    // 分隔符
    separator: '/',
    // 右侧提示文字
    rightText: ''
  },
  
  // 用户头像配置
  userAvatar: {
    // 默认头像
    defaultAvatar: '',
    // 头像尺寸
    size: 40
  },
  
  // 页面配置
  page: {
    // 默认页面大小
    defaultPageSize: 15,
    // 可选页面大小
    pageSizes: [15, 30, 50, 100]
  }
} 