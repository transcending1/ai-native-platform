// // import { createRouter, createWebHistory } from 'vue-router'
// // import type { RouteRecordRaw } from 'vue-router'
// // import ListPage from '../views/ListPage.vue'
// // import DetailPage from '../views/DetailPage.vue'
// //
// // const routes: Array<RouteRecordRaw> = [
// //     {
// //         path: '/',
// //         name: 'ListPage',
// //         component: ListPage
// //     },
// //     {
// //         path: '/detail/:id',
// //         name: 'DetailPage',
// //         component: DetailPage,
// //         props: true
// //     }
// // ]
// //
// // const router = createRouter({
// //     history: createWebHistory(),
// //     routes
// // })
// //
// // export default router
// import { createRouter, createWebHistory } from 'vue-router'
// import HomeView from '../views/HomeView.vue'
// import NamespaceView from '../views/NamespaceView.vue'
//
// const routes = [
//     {
//         path: '/',
//         name: 'Home',
//         component: HomeView
//     },
//     {
//         path: '/namespace/:namespaceId',
//         name: 'Namespace',
//         component: NamespaceView,
//         props: true
//     }
// ]
//
// const router = createRouter({
//     history: createWebHistory(),
//     routes
// })
//
// export default router

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import NamespaceView from '../views/NamespaceView.vue'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: HomeView
    },
    {
        path: '/namespace/:namespaceId',
        name: 'Namespace',
        component: NamespaceView,
        props: true // 启用路由参数自动传递
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router