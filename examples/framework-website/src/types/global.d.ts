// 全局类型声明

// Vue相关
declare module 'vue' {
    export * from '@vue/runtime-dom'
}

// Pinia相关
declare module 'pinia' { }

// Ant Design Vue相关
declare module 'ant-design-vue' {
    const antd: any
    export default antd
} 