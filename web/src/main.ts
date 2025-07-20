// // import { createApp } from 'vue'
// // import './style.css'
// // import App1 from './App1.vue'
// //
// // createApp(App1).mount('#app')
// import { createApp } from 'vue'
// import ElementPlus from 'element-plus'
// import 'element-plus/dist/index.css'
// // import "@tiptap/core/styles.css";
// import App1 from './App7.vue'
//
// const app = createApp(App1)
//
// app.use(ElementPlus)
// app.mount('#app')

// import { createApp } from 'vue'
// import { createPinia } from 'pinia'
// import App from './App.vue'
// import router from './router'
// import './assets/main.css'
//
// const app = createApp(App)
//
// app.use(createPinia())
// app.use(router)
//
// app.mount('#app
//
// ')
// import { createApp } from 'vue'
// import { createPinia } from 'pinia'
// import App from './App8.vue'
// import router from './router'
//
// // 引入Tailwind CSS
// import './index.css'
//
// const app = createApp(App)
//
// app.use(createPinia())
// app.use(router)
//
// app.mount('#app')

// import { createApp } from 'vue'
// import App from './App12.vue'
// import router from './router'
//
// const app = createApp(App)
// app.use(router)
// app.mount('#app')


// import { createApp } from 'vue';
// import App from './App11.vue';
// import ElementPlus from 'element-plus';
// import 'element-plus/dist/index.css';
//
// const app = createApp(App);
// app.use(ElementPlus);
// app.mount('#app');

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')