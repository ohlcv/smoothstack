/// <reference types="vite/client" />
/// <reference types="vue/macros-global" />

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

declare module 'ant-design-vue' {
    import type { DefineComponent } from 'vue';

    export const Layout: {
        new(): DefineComponent;
        Header: DefineComponent;
        Content: DefineComponent;
        Footer: DefineComponent;
    };

    export const Menu: {
        new(): DefineComponent;
        Item: DefineComponent;
    };

    export const Button: DefineComponent;
    export const Space: DefineComponent;
    export const Modal: DefineComponent;

    export const Input: {
        new(): DefineComponent;
        Search: DefineComponent;
    };

    export const List: {
        new(): DefineComponent;
        Item: DefineComponent;
    };

    export const Row: DefineComponent;
    export const Col: DefineComponent;
}

declare module 'vue' {
    interface ComponentCustomProperties {
        $router: Router;
    }

    interface ComponentCustomProps {
        selectedKeys?: string[];
        searchModalVisible?: boolean;
        searchQuery?: string;
        currentYear?: number;
        resources?: Array<{ title: string; path: string }>;
        community?: Array<{ title: string; url: string }>;
        support?: Array<{ title: string; path: string }>;
        showSearchModal?: () => void;
        onSearch?: (value: string) => void;
        startUsing?: () => void;
    }
}

export { }; 