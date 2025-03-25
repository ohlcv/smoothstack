declare module 'vue' {
    import { DefineComponent } from '@vue/runtime-dom';

    export const createApp: any;
    export const defineComponent: any;
    export const ref: any;
    export const reactive: any;
    export const computed: any;
    export const watch: any;
    export const onMounted: any;
    export const nextTick: any;

    // 其他可能需要的Vue导出
    export * from '@vue/runtime-dom';
} 