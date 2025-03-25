declare module '*.vue' {
    import type { DefineComponent } from 'vue';
    const component: DefineComponent<{}, {}, any>;
    export default component;
}

declare module '*.svg' {
    const content: string;
    export default content;
}

declare module '@ant-design/icons-vue' {
    import type { DefineComponent } from 'vue';
    export const HomeOutlined: DefineComponent;
    export const BookOutlined: DefineComponent;
    export const AppstoreOutlined: DefineComponent;
    export const CodeOutlined: DefineComponent;
    export const SearchOutlined: DefineComponent;
    export const RocketOutlined: DefineComponent;
} 