import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
// import AutoImport from 'unplugin-auto-import/vite'
// import Components from 'unplugin-vue-components/vite'
// import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
// export default defineConfig({
//   plugins: [
//       vue()
//     // AutoImport({
//     //   resolvers: [ElementPlusResolver()],
//     // }),
//     // Components({
//     //   resolvers: [ElementPlusResolver()],
//     // }),
//   ],
// })

import AutoImport from 'unplugin-auto-import/vite';
import Components from 'unplugin-vue-components/vite';
import {ElementPlusResolver} from 'unplugin-vue-components/resolvers';

export default defineConfig({
    plugins: [
        vue(),
        AutoImport({
            resolvers: [ElementPlusResolver()],
        }),
        Components({
            resolvers: [ElementPlusResolver()],
        }),
    ],
    server: {
        proxy: {
            '/api': {
                target: 'http://localhost:8000', // Django后端地址
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '') // 移除/api前缀，因为Django路由已有/api
            }
        }
    }
});

