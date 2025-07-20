import axios from 'axios';

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_APP_BASE_API, // 从环境变量获取 API 地址
    timeout: 5000, // 设置超时时间
});

// 可以添加请求拦截器和响应拦截器
apiClient.interceptors.request.use(config => {
    // 例如 添加token
    //  const token = localStorage.getItem("token")
    //  if(token) {
    //    config.headers.Authorization = `Bearer ${token}`
    //  }
    return config;
}, error => {
    return Promise.reject(error)
})

apiClient.interceptors.response.use(res => {
    return res
}, error => {
    return Promise.reject(error)
})
export default apiClient;