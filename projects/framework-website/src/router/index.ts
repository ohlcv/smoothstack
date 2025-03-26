import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import Docs from '../views/Docs.vue';
import DocViewer from '../components/DocViewer.vue';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView
        },
        // 临时禁用文档功能，重定向到首页
        {
            path: '/docs',
            redirect: '/'
        },
        // 原文档路由配置，暂时注释
        /*
        {
            path: '/docs',
            component: Docs,
            children: [
                {
                    path: '',
                    redirect: '/docs/使用指南'
                },
                {
                    path: ':path*',
                    name: 'doc',
                    component: DocViewer
                }
            ]
        }
        */
    ]
});

export default router; 