<template>
    <ALayout class="app-container">
      <ALayoutHeader class="app-header">
        <div class="header-content">
          <div class="logo">
            <img src="@/assets/logo.svg" alt="Smoothstack Logo" class="logo-img" />
            <span class="logo-text">
              <span class="logo-part-1">Smooth</span><span class="logo-part-2">stack</span>
            </span>
          </div>
          
          <AMenu
            v-model:selectedKeys="selectedKeys"
            mode="horizontal"
            class="main-nav"
          >
            <AMenuItem key="home">
              <router-link to="/">
                <HomeOutlined />
                <span>首页</span>
              </router-link>
            </AMenuItem>
            <!-- 临时禁用文档功能 -->
            <AMenuItem key="docs" disabled>
              <span>
                <BookOutlined />
                <span>文档 (维护中)</span>
              </span>
            </AMenuItem>
            <AMenuItem key="components">
              <router-link to="/components">
                <AppstoreOutlined />
                <span>组件</span>
              </router-link>
            </AMenuItem>
            <AMenuItem key="tutorial">
              <router-link to="/tutorial">
                <CodeOutlined />
                <span>教程</span>
              </router-link>
            </AMenuItem>
          </AMenu>
  
          <div class="header-right">
            <ASpace>
              <AButton class="header-btn" @click="showSearchModal">
                <template #icon><SearchOutlined /></template>
                搜索
              </AButton>
              <AButton type="primary" class="header-btn get-started-btn" @click="startUsing">
                <template #icon><RocketOutlined /></template>
                开始使用
              </AButton>
            </ASpace>
          </div>
        </div>
      </ALayoutHeader>
  
      <ALayoutContent class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </ALayoutContent>
  
      <ALayoutFooter class="app-footer">
        <div class="footer-content">
          <ARow :gutter="[32, 32]">
            <ACol :xs="24" :sm="12" :md="6">
              <ACard :bordered="false" class="footer-card">
                <template #title>
                  <div class="footer-title-container">
                    <ATypography.Title :level="4" class="footer-title">Smoothstack</ATypography.Title>
                  </div>
                </template>
                <ATypography.Paragraph class="footer-paragraph">
                  现代化全栈应用开发框架
                </ATypography.Paragraph>
                <ATypography.Paragraph class="footer-paragraph">
                  © {{ currentYear }} 版权所有
                </ATypography.Paragraph>
              </ACard>
            </ACol>
            
            <ACol :xs="24" :sm="12" :md="6">
              <ACard :bordered="false" class="footer-card">
                <template #title>
                  <div class="footer-title-container">
                    <ATypography.Title :level="4" class="footer-title">资源</ATypography.Title>
                  </div>
                </template>
                <AList :data-source="resources" :bordered="false" class="footer-list" size="small">
                  <template #renderItem="{ item }">
                    <AListItem>
                      <router-link :to="item.path">
                        <ATypography.Text class="footer-link">{{ item.title }}</ATypography.Text>
                      </router-link>
                    </AListItem>
                  </template>
                </AList>
              </ACard>
            </ACol>
            
            <ACol :xs="24" :sm="12" :md="6">
              <ACard :bordered="false" class="footer-card">
                <template #title>
                  <div class="footer-title-container">
                    <ATypography.Title :level="4" class="footer-title">社区</ATypography.Title>
                  </div>
                </template>
                <AList :data-source="community" :bordered="false" class="footer-list" size="small">
                  <template #renderItem="{ item }">
                    <AListItem>
                      <a :href="item.url" target="_blank" rel="noopener noreferrer">
                        <ATypography.Text class="footer-link">{{ item.title }}</ATypography.Text>
                      </a>
                    </AListItem>
                  </template>
                </AList>
              </ACard>
            </ACol>
            
            <ACol :xs="24" :sm="12" :md="6">
              <ACard :bordered="false" class="footer-card">
                <template #title>
                  <div class="footer-title-container">
                    <ATypography.Title :level="4" class="footer-title">支持</ATypography.Title>
                  </div>
                </template>
                <AList :data-source="support" :bordered="false" class="footer-list" size="small">
                  <template #renderItem="{ item }">
                    <AListItem>
                      <router-link :to="item.path">
                        <ATypography.Text class="footer-link">{{ item.title }}</ATypography.Text>
                      </router-link>
                    </AListItem>
                  </template>
                </AList>
              </ACard>
            </ACol>
          </ARow>
          <ADivider style="background-color: #1e3a5c; margin: 24px 0;" />
          <ARow justify="center" align="middle" style="padding: 16px 0;">
            <ACol>
              <ASpace>
                <ATypography.Link style="color: #fff;">隐私政策</ATypography.Link>
                <ADivider type="vertical" style="background-color: #1e3a5c;" />
                <ATypography.Link style="color: #fff;">服务条款</ATypography.Link>
                <ADivider type="vertical" style="background-color: #1e3a5c;" />
                <ATypography.Link style="color: #fff;">Cookie偏好</ATypography.Link>
              </ASpace>
            </ACol>
          </ARow>
        </div>
      </ALayoutFooter>
  
      <!-- 搜索模态框 -->
      <AModal
        v-model:visible="searchModalVisible"
        title="搜索"
        :footer="null"
        width="600px"
        class="search-modal"
      >
        <AInputSearch
          v-model:value="searchQuery"
          placeholder="搜索文档、组件、教程..."
          size="large"
          class="search-input"
          @search="onSearch"
          @keyup.enter="onSearch(searchQuery)"
        >
          <template #enterButton>
            <AButton type="primary">
              <template #icon><SearchOutlined /></template>
              搜索
            </AButton>
          </template>
        </AInputSearch>
  
        <div v-if="searchQuery.length > 0" class="search-results">
          <p>正在搜索 "{{ searchQuery }}"...</p>
        </div>
      </AModal>
    </ALayout>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted, watch } from 'vue';
  import { useRouter, useRoute } from 'vue-router';
  import {
    HomeOutlined,
    BookOutlined,
    AppstoreOutlined,
    CodeOutlined,
    SearchOutlined,
    RocketOutlined
  } from '@ant-design/icons-vue';
  
  import {
    Layout as ALayout,
    Menu as AMenu,
    Button as AButton,
    Space as ASpace,
    Modal as AModal,
    Input as AInput,
    List as AList,
    Row as ARow,
    Col as ACol,
    Card as ACard,
    Typography as ATypography,
    Divider as ADivider
  } from 'ant-design-vue';
  
  const ALayoutHeader = ALayout.Header;
  const ALayoutContent = ALayout.Content;
  const ALayoutFooter = ALayout.Footer;
  const AMenuItem = AMenu.Item;
  const AInputSearch = AInput.Search;
  const AListItem = AList.Item;
  
  // 类型定义
  interface Resource {
    title: string;
    path: string;
  }
  
  interface Community {
    title: string;
    url: string;
  }
  
  interface Support {
    title: string;
    path: string;
  }
  
  // 响应式数据
  const router = useRouter();
  const route = useRoute();
  const currentYear = computed(() => new Date().getFullYear());
  const selectedKeys = ref<string[]>(['home']);
  const searchModalVisible = ref<boolean>(false);
  const searchQuery = ref<string>('');
  
  // 数据源
  const resources: Resource[] = [
    { title: '文档', path: '/docs' },
    { title: '组件', path: '/components' },
    { title: '模板', path: '/templates' },
    { title: '示例', path: '/examples' }
  ];
  
  const community: Community[] = [
    { title: 'GitHub', url: 'https://github.com/ohlcv/smoothstack' },
    { title: 'Discord', url: 'https://discord.gg/smoothstack' },
    { title: 'Twitter', url: 'https://twitter.com/smoothstack' }
  ];
  
  const support: Support[] = [
    { title: '常见问题', path: '/faq' },
    { title: '支持渠道', path: '/support' },
    { title: '服务状态', path: '/status' },
    { title: '联系我们', path: '/contact' }
  ];
  
  // 方法
  const showSearchModal = () => {
    searchModalVisible.value = true;
    setTimeout(() => {
      const input = document.querySelector('.search-input input') as HTMLInputElement;
      if (input) {
        input.focus();
      }
    }, 100);
  };
  
  const onSearch = (value: string) => {
    if (!value.trim()) return;
    
    // 实现搜索逻辑
    console.log('Searching for:', value);
    
    // 这里可以添加实际的搜索实现
    // 例如: router.push({ path: '/search', query: { q: value } });
  };
  
  const startUsing = () => {
    router.push('/docs/getting-started');
  };
  
  // 监听路由变化更新选中菜单项
  onMounted(() => {
    updateSelectedKeys();
  });
  
  watch(() => route.path, updateSelectedKeys);
  
  function updateSelectedKeys() {
    const path = route.path;
    if (path === '/') {
      selectedKeys.value = ['home'];
    } else if (path.startsWith('/docs')) {
      selectedKeys.value = ['docs'];
    } else if (path.startsWith('/components')) {
      selectedKeys.value = ['components'];
    } else if (path.startsWith('/tutorial')) {
      selectedKeys.value = ['tutorial'];
    }
  }
  
  // 清除搜索框当模态框关闭时
  watch(searchModalVisible, (newVal) => {
    if (!newVal) {
      setTimeout(() => {
        searchQuery.value = '';
      }, 300);
    }
  });
  </script>
  
  <style>
  /* 基础样式 */
  .app-container {
    min-height: 100vh;
    background: #f5f7fa;
  }
  
  /* 顶部导航栏 */
  .app-header {
    position: fixed;
    width: 100%;
    z-index: 1000;
    padding: 0;
    background: linear-gradient(135deg, #1677ff, #7a38e0);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  }
  
  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  /* Logo样式 */
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .logo-img {
    height: 32px;
    width: auto;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
    transition: transform 0.3s ease;
  }
  
  .logo:hover .logo-img {
    transform: rotate(10deg);
  }
  
  .logo-text {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", "Helvetica Neue", Arial, sans-serif;
  }
  
  .logo-part-1, .logo-part-2 {
    background: linear-gradient(to right, #ffffff, #f0f0f0);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .logo-part-2 {
    color: rgba(255, 255, 255, 0.9);
    background: linear-gradient(to right, #f0f0f0, #e6e6e6);
    -webkit-background-clip: text;
    background-clip: text;
  }
  
  /* 导航菜单 */
  .main-nav {
    flex: 1;
    margin: 0 48px;
    background: transparent;
    border-bottom: none;
  }
  
  .app-container .main-nav .ant-menu-item {
    font-size: 15px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.95) !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    margin: 0 4px;
    transition: all 0.3s ease;
  }
  
  .app-container .main-nav .ant-menu-item:hover {
    color: #fff !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
  }
  
  .app-container .main-nav .ant-menu-item-selected {
    color: #fff !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    background: rgba(255, 255, 255, 0.15) !important;
    border-radius: 4px;
  }
  
  .app-container .main-nav .ant-menu-item::after {
    display: none;
  }
  
  .app-container .main-nav a {
    color: inherit;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  /* 右侧按钮 */
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .header-btn {
    font-weight: 500;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(4px);
    height: 38px;
    color: white !important;
    display: flex;
    align-items: center;
    border-radius: 6px;
    transition: all 0.25s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .header-btn:hover {
    background: rgba(255, 255, 255, 0.25);
    border-color: rgba(255, 255, 255, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }
  
  .get-started-btn {
    background: linear-gradient(135deg, #ff6b6b, #ff9e4a) !important;
    border: none !important;
  }
  
  .get-started-btn:hover {
    background: linear-gradient(135deg, #ff5252, #ff8b3d) !important;
  }
  
  /* 主内容区 */
  .main-content {
    padding: 88px 24px 24px;
    min-height: calc(100vh - 64px - 280px);
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
  }
  
  /* 页面过渡动画 */
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.3s ease, transform 0.3s ease;
  }
  
  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
    transform: translateY(10px);
  }
  
  /* 特性卡片样式 */
  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
    margin: 48px 0;
  }
  
  .feature-card {
    background: #fff;
    border-radius: 12px;
    padding: 28px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border: 1px solid rgba(0, 0, 0, 0.06);
  }
  
  .feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }
  
  .feature-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
    background: linear-gradient(135deg, #e6f7ff, #e6fffb);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }
  
  .feature-title {
    font-size: 20px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 12px;
  }
  
  .feature-description {
    color: #4b5563;
    line-height: 1.6;
    font-size: 15px;
  }
  
  /* 底部样式 */
  .app-footer {
    background: #001529 !important;
    padding: 56px 24px 24px;
    position: relative;
    z-index: 1;
    margin-top: 64px;
    box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .footer-content {
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .footer-card {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  
  .footer-card .ant-card-head {
    border-bottom: none !important;
    padding: 0 !important;
    min-height: auto !important;
    margin-bottom: 16px !important;
    background-color: transparent !important;
    color: #fff !important;
  }
  
  .footer-card .ant-card-body {
    padding: 0 !important;
  }
  
  .footer-title-container {
    padding-bottom: 10px;
    border-bottom: 3px solid #1890ff;
    display: inline-block;
  }
  
  .footer-title {
    color: #fff !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    text-shadow: 0 2px 3px rgba(0, 0, 0, 0.3) !important;
    letter-spacing: 0.5px !important;
    margin: 0 !important;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", "Helvetica Neue", Arial, sans-serif !important;
  }
  
  .footer-paragraph {
    color: #fff !important;
    margin-bottom: 12px !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2) !important;
    font-weight: 400 !important;
  }
  
  .footer-list {
    background: transparent !important;
  }
  
  .footer-list .ant-list-item {
    padding: 8px 0 !important;
    border-bottom: none !important;
    background: transparent !important;
  }
  
  .footer-link {
    color: #fff !important;
    font-size: 15px !important;
    transition: all 0.3s ease !important;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2) !important;
    display: inline-block !important;
    font-weight: 400 !important;
  }
  
  .footer-link:hover {
    color: #40a9ff !important;
    text-shadow: 0 0 8px rgba(24, 144, 255, 0.6) !important;
    transform: translateX(4px) !important;
    text-decoration: none !important;
  }
  
  .footer-divider {
    background-color: rgba(255, 255, 255, 0.1) !important;
    margin: 24px 0 !important;
  }
  
  .footer-bottom {
    padding: 16px 0 !important;
  }
  
  .footer-bottom-link {
    color: rgba(255, 255, 255, 0.7) !important;
    font-size: 14px !important;
    transition: all 0.3s ease !important;
  }
  
  .footer-bottom-link:hover {
    color: #4fc3f7 !important;
  }
  
  /* 搜索弹窗 */
  .search-modal .ant-modal-content {
    border-radius: 8px;
    overflow: hidden;
  }
  
  .search-modal .ant-modal-header {
    background: #f8fafc;
    border-bottom: 1px solid #eaeaea;
    padding: 16px 24px;
  }
  
  .search-modal .ant-modal-body {
    padding: 24px;
  }
  
  .search-input {
    width: 100%;
  }
  
  .search-input .ant-input {
    height: 50px;
    border-radius: 8px 0 0 8px;
    font-size: 16px;
    padding-left: 16px;
  }
  
  .search-input .ant-btn {
    height: 50px;
    border-radius: 0 8px 8px 0;
    width: 80px;
  }
  
  .search-results {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #eaeaea;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .header-content {
      padding: 0 16px;
    }
  
    .main-nav {
      display: none;
    }
  
    .header-right {
      gap: 8px;
    }
  
    .main-content {
      padding: 88px 16px 24px;
    }
  
    .app-footer {
      padding: 40px 16px;
    }
  }
  
  @media (max-width: 576px) {
    .get-started-btn span:last-child {
      display: none;
    }
    
    .header-btn {
      padding: 0 12px;
    }
  }
  </style>