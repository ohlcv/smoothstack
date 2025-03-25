import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';
import './assets/main.css';
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';

const app = createApp(App);
const pinia = createPinia();

app.use(router);
app.use(pinia);
app.use(Antd);

app.mount('#app');