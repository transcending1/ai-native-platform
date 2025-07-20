// import axios from 'axios';
//
// const api = axios.create({
//     baseURL: '/api',
//     headers: {
//         'Content-Type': 'application/json',
//         'Authorization': 'Token 7000681fbe8b77553aa419bad5c96c5e56528eec'
//     }
// });
//
// // 命名空间API
// export const namespaceApi = {
//     list: () => api.get('/api/namespaces/'),
//     create: (data: { name: string; description?: string }) => api.post('/api/namespaces/', data),
//     update: (id: number, data: Partial<{ name: string; description: string }>) =>
//         api.patch(`/api/namespaces/${id}/`, data),
//     delete: (id: number) => api.delete(`/api/namespaces/${id}/`)
// };
//
// // 目录API
// export const directoryApi = {
//     list: (namespaceId?: number) =>
//         api.get('/api/directories/', { params: namespaceId ? { namespace: namespaceId } : {} }),
//     create: (data: { name: string; namespace: number; parent?: number | null }) =>
//         api.post('/api/directories/', data),
//     update: (id: number, data: Partial<{ name: string; parent: number | null }>) =>
//         api.patch(`/api/directories/${id}/`, data),
//     delete: (id: number) => api.delete(`/api/directories/${id}/`),
//     tree: (namespaceId: number) => api.get(`/api/directories/tree/${namespaceId}/`),
//     move: (id: number, parentId: number | null) =>
//         api.post(`/api/directories/${id}/move/`, { parent_id: parentId })
// };
//
// // 笔记API
// export const noteApi = {
//     list: (directoryId?: number) =>
//         api.get('/api/notes/', { params: directoryId ? { directory: directoryId } : {} }),
//     create: (data: { title: string; content: string; directory: number }) =>
//         api.post('/api/notes/', data),
//     update: (id: number, data: Partial<{ title: string; content: string; directory: number }>) =>
//         api.patch(`/api/notes/${id}/`, data),
//     delete: (id: number) => api.delete(`/api/notes/${id}/`),
//     move: (id: number, directoryId: number) =>
//         api.post(`/api/notes/${id}/move/`, { directory_id: directoryId })
// };
//
// export default api;

import axios from 'axios';
import { ElMessage } from 'element-plus';

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token 7000681fbe8b77553aa419bad5c96c5e56528eec'
    }
});

// 错误处理拦截器
api.interceptors.response.use(
    response => response,
    error => {
        const message = error.response?.data?.error || error.message || '请求失败';
        ElMessage.error(message);
        return Promise.reject(error);
    }
);

// 命名空间API
export const namespaceApi = {
    list: () => api.get('/api/namespaces/'),
    create: (data: { name: string; description?: string }) =>
        api.post('/api/namespaces/', data),
    update: (id: number, data: Partial<{ name: string; description: string }>) =>
        api.patch(`/api/namespaces/${id}/`, data),
    delete: (id: number) => api.delete(`/api/namespaces/${id}/`)
};

// 目录API
export const directoryApi = {
    list: (namespaceId?: number) =>
        api.get('/api/directories/', { params: namespaceId ? { namespace: namespaceId } : {} }),
    create: (data: { name: string; namespace: number; parent?: number | null }) =>
        api.post('/api/directories/', data),
    update: (id: number, data: Partial<{ name: string; parent: number | null }>) =>
        api.patch(`/api/directories/${id}/`, data),
    delete: (id: number) => api.delete(`/api/directories/${id}/`),
    tree: (namespaceId: number) => api.get(`/api/directories/tree/${namespaceId}/`),
    move: (id: number, parentId: number | null) =>
        api.post(`/api/directories/${id}/move/`, { parent_id: parentId })
};

// 笔记API
export const noteApi = {
    list: (directoryId?: number) =>
        api.get('/api/notes/', { params: directoryId ? { directory: directoryId } : {} }),
    create: (data: { title: string; content: string; directory: number; category?: string }) =>
        api.post('/api/notes/', data),
    update: (id: number, data: Partial<{ title: string; content: string; directory?: number; category?: string }>) =>
        api.patch(`/api/notes/${id}/`, data),
    delete: (id: number) => api.delete(`/api/notes/${id}/`),
    move: (id: number, directoryId: number) =>
        api.post(`/api/notes/${id}/move/`, { directory_id: directoryId })
};

export default api;