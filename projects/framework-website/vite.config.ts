import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import fs from 'fs';

// 文档目录配置
const docsDir = resolve(__dirname, '../../docs');
const docsWatchDir = resolve(__dirname, '../../docs/**/*.md');

// 自动生成文档路由
function generateDocsRoutes() {
    const routes: { path: string; title: string }[] = [];

    function scanDir(dir: string, basePath: string = '') {
        try {
            const files = fs.readdirSync(dir);

            for (const file of files) {
                const fullPath = resolve(dir, file);
                const stat = fs.statSync(fullPath);

                if (stat.isDirectory()) {
                    scanDir(fullPath, `${basePath}/${file}`);
                } else if (file.endsWith('.md')) {
                    const content = fs.readFileSync(fullPath, 'utf-8');
                    const titleMatch = content.match(/^#\s+(.+)$/m);
                    const title = titleMatch ? titleMatch[1] : file.replace('.md', '');
                    const path = `${basePath}/${file.replace('.md', '')}`;
                    routes.push({ path, title });
                }
            }
        } catch (err) {
            console.error('Error scanning docs directory:', err);
            // 返回空路由，不中断程序
            return routes;
        }
    }

    scanDir(docsDir);
    return routes;
}

// 创建文档API处理器
function createDocumentationMiddleware() {
    return (req, res, next) => {
        // 只处理/docs路径下的请求
        if (!req.url.startsWith('/docs')) {
            return next();
        }

        // 添加CORS头和缓存控制
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
        res.setHeader('Cache-Control', 'max-age=300'); // 5分钟缓存

        // 移除前缀'/docs'获取文档路径
        let docPath = req.url.replace(/^\/docs\/?/, '');

        // 处理文档列表请求
        if (!docPath || docPath === '/') {
            const routes = generateDocsRoutes();
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            return res.end(JSON.stringify(routes));
        }

        // 如果路径包含查询参数，移除它们
        docPath = docPath.split('?')[0];

        // 确保路径以.md结尾
        if (!docPath.endsWith('.md')) {
            docPath += '.md';
        }

        // 构建完整的文件路径
        const filePath = resolve(docsDir, docPath);

        try {
            // 检查文件是否存在
            if (fs.existsSync(filePath)) {
                const content = fs.readFileSync(filePath, 'utf-8');
                res.statusCode = 200;
                res.setHeader('Content-Type', 'text/markdown; charset=utf-8');
                return res.end(content);
            } else {
                console.log(`文档不存在: ${filePath}`);
                res.statusCode = 404;
                res.setHeader('Content-Type', 'application/json');
                return res.end(JSON.stringify({ error: '文档不存在' }));
            }
        } catch (error) {
            console.error('文档服务错误:', error);
            res.statusCode = 500;
            res.setHeader('Content-Type', 'application/json');
            return res.end(JSON.stringify({ error: '内部服务器错误' }));
        }
    };
}

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
        // 临时禁用文档监听功能
        /*
        {
            name: 'docs-watcher',
            configureServer(server) {
                // 添加本地文档中间件
                server.middlewares.use(createDocumentationMiddleware());
                
                // 监听文档变化
                server.watcher.add(docsWatchDir);

                // 文档变化时重新生成路由
                server.watcher.on('change', (path) => {
                    if (path.endsWith('.md')) {
                        const routes = generateDocsRoutes();
                        // 通知客户端更新路由
                        server.ws.send({
                            type: 'custom',
                            event: 'docs-update',
                            data: routes
                        });
                    }
                });
            }
        }
        */
    ],
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
            '@docs': docsDir
        }
    },
    server: {
        port: 3000,
        host: '0.0.0.0',
        watch: {
            usePolling: true,
            interval: 5000, // 降低轮询频率，减少不必要的刷新
            ignored: [
                '**/node_modules/**',
                '**/dist/**',
                '../../docs/**/*.md', // 忽略markdown文件变更
                resolve(__dirname, '../../docs') // 忽略整个docs目录
            ]
        },
        hmr: {
            overlay: true,
            clientPort: 3000
        },
        proxy: {
            '/api': {
                target: 'http://localhost:5000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '')
            }
            // 移除了对/docs的代理配置
        },
        fs: {
            allow: ['..']
        }
    },
    build: {
        outDir: 'dist',
        minify: 'terser',
        terserOptions: {
            compress: {
                drop_console: process.env.NODE_ENV === 'production'
            }
        }
    }
}); 