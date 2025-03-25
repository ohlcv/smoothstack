import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue({
            template: {
                compilerOptions: {
                    isCustomElement: (tag) => tag.startsWith('a-')
                }
            }
        })
    ],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
            'vue': path.resolve(__dirname, './node_modules/vue')
        }
    },
    server: {
        host: '0.0.0.0',
        port: 3000,
        watch: {
            usePolling: true,
            interval: 1000,
            ignored: ['**/node_modules/**', '**/dist/**']
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