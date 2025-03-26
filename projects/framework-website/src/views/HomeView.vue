<template>
    <div class="home-view">
      <!-- 英雄区块 -->
      <ARow>
        <ACol :span="24">
          <div class="hero-section">
            <div class="hero-content">
              <ATypography.Title :level="1" class="hero-title">构建现代化应用的新范式</ATypography.Title>
              <ATypography.Title :level="3" class="hero-subtitle">Smoothstack 为开发者提供直观、高效的全栈应用开发体验</ATypography.Title>
              <ATypography.Paragraph class="hero-description">
                一个专注于开发体验的框架，结合 Vue 3、FastAPI 和 Docker，帮助开发者专注于业务逻辑而非环境配置
              </ATypography.Paragraph>
              <ASpace class="hero-buttons">
                <AButton type="primary" size="large">
                  <template #icon><RocketOutlined /></template>
                  快速开始
                </AButton>
                <AButton size="large">
                  <template #icon><BookOutlined /></template>
                  查看文档
                </AButton>
              </ASpace>
            </div>
            <div class="hero-image">
              <img src="@/assets/hero-image.svg" alt="Smoothstack 架构图" />
            </div>
          </div>
        </ACol>
      </ARow>
  
      <!-- 特性区块 -->
      <ARow>
        <ACol :span="24" class="features-section">
          <ATypography.Title :level="2" class="section-title">为什么选择 Smoothstack</ATypography.Title>
          <div class="features-grid">
            <ACard v-for="(feature, index) in features" :key="index" class="feature-card" :bordered="false">
              <template #cover>
                <div class="feature-icon-container">
                  <component :is="feature.icon" class="feature-icon" />
                </div>
              </template>
              <ATypography.Title :level="4">{{ feature.title }}</ATypography.Title>
              <ATypography.Paragraph>{{ feature.description }}</ATypography.Paragraph>
            </ACard>
          </div>
        </ACol>
      </ARow>
  
      <!-- 核心功能区块 -->
      <ARow>
        <ACol :span="24" class="core-features-section">
          <div class="section-header">
            <ATypography.Title :level="2" class="section-title">核心功能</ATypography.Title>
            <ATypography.Paragraph class="section-description">
              Smoothstack 提供了全面的功能集，帮助开发者构建现代化应用
            </ATypography.Paragraph>
          </div>
  
          <div class="core-features-container">
            <div class="core-features-content">
              <div class="core-feature-item" v-for="(item, index) in coreFeatures" :key="index">
                <div class="core-feature-icon">
                  <component :is="item.icon" />
                </div>
                <div class="core-feature-text">
                  <ATypography.Title :level="5">{{ item.title }}</ATypography.Title>
                  <ATypography.Paragraph>{{ item.description }}</ATypography.Paragraph>
                </div>
              </div>
            </div>
            <div class="core-features-image">
              <img src="@/assets/workflow.svg" alt="Smoothstack 工作流程" />
            </div>
          </div>
        </ACol>
      </ARow>
  
      <!-- 技术栈区块 -->
      <ARow>
        <ACol :span="24" class="tech-stack-section">
          <ATypography.Title :level="2" class="section-title">技术栈</ATypography.Title>
          <ATypography.Paragraph class="section-description">
            Smoothstack 集成了现代化的技术栈，为开发者提供强大的功能支持
          </ATypography.Paragraph>
  
          <ATabs class="tech-stack-tabs" centered>
            <ATabPane key="frontend" tab="前端技术栈">
              <div class="tech-list">
                <ARow :gutter="[16, 16]">
                  <ACol :xs="24" :sm="12" :md="8" v-for="(tech, index) in frontendTech" :key="index">
                    <div class="tech-item">
                      <component :is="tech.icon" class="tech-icon" />
                      <div class="tech-info">
                        <ATypography.Text strong>{{ tech.name }}</ATypography.Text>
                        <ATypography.Text type="secondary">{{ tech.description }}</ATypography.Text>
                      </div>
                    </div>
                  </ACol>
                </ARow>
              </div>
            </ATabPane>
            <ATabPane key="backend" tab="后端技术栈">
              <div class="tech-list">
                <ARow :gutter="[16, 16]">
                  <ACol :xs="24" :sm="12" :md="8" v-for="(tech, index) in backendTech" :key="index">
                    <div class="tech-item">
                      <component :is="tech.icon" class="tech-icon" />
                      <div class="tech-info">
                        <ATypography.Text strong>{{ tech.name }}</ATypography.Text>
                        <ATypography.Text type="secondary">{{ tech.description }}</ATypography.Text>
                      </div>
                    </div>
                  </ACol>
                </ARow>
              </div>
            </ATabPane>
            <ATabPane key="devops" tab="容器化与环境管理">
              <div class="tech-list">
                <ARow :gutter="[16, 16]">
                  <ACol :xs="24" :sm="12" :md="8" v-for="(tech, index) in devopsTech" :key="index">
                    <div class="tech-item">
                      <component :is="tech.icon" class="tech-icon" />
                      <div class="tech-info">
                        <ATypography.Text strong>{{ tech.name }}</ATypography.Text>
                        <ATypography.Text type="secondary">{{ tech.description }}</ATypography.Text>
                      </div>
                    </div>
                  </ACol>
                </ARow>
              </div>
            </ATabPane>
          </ATabs>
        </ACol>
      </ARow>
  
      <!-- 快速开始区块 -->
      <ARow>
        <ACol :span="24" class="quick-start-section">
          <ATypography.Title :level="2" class="section-title">快速开始</ATypography.Title>
          <ATypography.Paragraph class="section-description">
            只需几个简单步骤，即可开始使用 Smoothstack 构建应用
          </ATypography.Paragraph>
  
          <ASteps class="quick-start-steps">
            <AStep title="克隆项目" description="从GitHub克隆Smoothstack项目">
              <template #icon>
                <GithubOutlined />
              </template>
              <template #description>
                <ATypography.Paragraph>
                  <ATypography.Text code>git clone https://github.com/yourusername/smoothstack.git</ATypography.Text>
                </ATypography.Paragraph>
                <ATypography.Paragraph>
                  <ATypography.Text code>cd smoothstack</ATypography.Text>
                </ATypography.Paragraph>
              </template>
            </AStep>
            <AStep title="环境初始化" description="一键设置所有开发环境依赖">
              <template #icon>
                <SettingOutlined />
              </template>
              <template #description>
                <ATypography.Paragraph>
                  <ATypography.Text code>./start.sh setup</ATypography.Text>
                </ATypography.Paragraph>
                <ATypography.Paragraph>
                  使用中国镜像源加速依赖下载(可选):
                  <ATypography.Text code>./start.sh setup --cn</ATypography.Text>
                </ATypography.Paragraph>
              </template>
            </AStep>
            <AStep title="启动开发环境" description="启动开发模式(支持热重载)">
              <template #icon>
                <PlayCircleOutlined />
              </template>
              <template #description>
                <ATypography.Paragraph>
                  <ATypography.Text code>./start.sh run</ATypography.Text>
                </ATypography.Paragraph>
                <ATypography.Paragraph>
                  查看系统状态:
                  <ATypography.Text code>./start.sh status</ATypography.Text>
                </ATypography.Paragraph>
              </template>
            </AStep>
            <AStep title="访问应用" description="通过浏览器访问应用">
              <template #icon>
                <GlobalOutlined />
              </template>
              <template #description>
                <ATypography.Paragraph>
                  前端开发服务器: <ATypography.Link href="http://localhost:3000" target="_blank">http://localhost:3000</ATypography.Link>
                </ATypography.Paragraph>
                <ATypography.Paragraph>
                  API服务: <ATypography.Link href="http://localhost:5000" target="_blank">http://localhost:5000</ATypography.Link>
                </ATypography.Paragraph>
              </template>
            </AStep>
          </ASteps>
        </ACol>
      </ARow>
  
      <!-- 应用场景区块 -->
      <ARow>
        <ACol :span="24" class="use-cases-section">
          <ATypography.Title :level="2" class="section-title">使用场景</ATypography.Title>
          <ATypography.Paragraph class="section-description">
            Smoothstack 适用于多种应用场景，满足不同开发需求
          </ATypography.Paragraph>
  
          <ARow :gutter="[24, 24]" class="use-cases-container">
            <ACol :xs="24" :sm="12" :md="8" v-for="(useCase, index) in useCases" :key="index">
              <ACard class="use-case-card" :bordered="false">
                <template #cover>
                  <div class="use-case-icon-container">
                    <component :is="useCase.icon" class="use-case-icon" />
                  </div>
                </template>
                <ATypography.Title :level="4">{{ useCase.title }}</ATypography.Title>
                <ATypography.Paragraph>{{ useCase.description }}</ATypography.Paragraph>
              </ACard>
            </ACol>
          </ARow>
        </ACol>
      </ARow>
  
      <!-- 号召性用语区块 -->
      <ARow>
        <ACol :span="24">
          <div class="cta-section">
            <div class="cta-content">
              <ATypography.Title :level="2" class="cta-title">开始使用 Smoothstack</ATypography.Title>
              <ATypography.Paragraph class="cta-description">
                立即体验更高效、更流畅的开发方式
              </ATypography.Paragraph>
              <ASpace class="cta-buttons">
                <AButton type="primary" size="large">
                  快速开始
                </AButton>
                <AButton class="secondary-btn" size="large">
                  查看示例项目
                </AButton>
              </ASpace>
            </div>
          </div>
        </ACol>
      </ARow>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import {
    RocketOutlined,
    BookOutlined,
    CloudOutlined,
    CodeOutlined,
    LockOutlined,
    ApartmentOutlined,
    DatabaseOutlined,
    ApiOutlined,
    GithubOutlined,
    SettingOutlined,
    PlayCircleOutlined,
    GlobalOutlined,
    ToolOutlined,
    TeamOutlined,
    ExperimentOutlined,
    DeploymentUnitOutlined
  } from '@ant-design/icons-vue';
  import {
    Typography as ATypography,
    Button as AButton,
    Card as ACard,
    Tabs as ATabs,
    TabPane as ATabPane,
    Steps as ASteps,
    Step as AStep,
    Row as ARow,
    Col as ACol,
    Space as ASpace
  } from 'ant-design-vue';
  
  // 为什么选择Smoothstack的特性卡片
  const features = ref([
    {
      title: '一键式环境部署',
      description: '10分钟内完成从零到可用的全栈开发环境搭建',
      icon: RocketOutlined
    },
    {
      title: 'Docker 容器化管理',
      description: '隔离的开发环境确保"我这能运行"就是"到处能运行"',
      icon: CloudOutlined
    },
    {
      title: '跨平台兼容',
      description: 'Windows、macOS、Linux 全平台支持，消除环境差异问题',
      icon: GlobalOutlined
    },
    {
      title: '自动化依赖管理',
      description: '前后端依赖统一管理，版本锁定与冲突检测',
      icon: ApartmentOutlined
    },
    {
      title: '多环境支持',
      description: '开发、测试、预发布、生产环境配置分离与一键切换',
      icon: DeploymentUnitOutlined
    },
    {
      title: '双语言整合',
      description: '无缝集成 JavaScript/TypeScript 前端与 Python 后端的开发体验',
      icon: CodeOutlined
    },
    {
      title: '模块化架构',
      description: '可插拔组件设计，按需引入所需功能',
      icon: ApiOutlined
    },
    {
      title: '开发体验优先',
      description: '热重载、智能日志、调试工具链一应俱全',
      icon: ToolOutlined
    },
    {
      title: '企业级安全',
      description: '内置安全最佳实践，包括身份验证、授权和数据加密',
      icon: LockOutlined
    }
  ]);
  
  // 核心功能列表
  const coreFeatures = ref([
    {
      title: '一键式环境部署',
      description: '10分钟内完成从零到可用的全栈开发环境搭建',
      icon: RocketOutlined
    },
    {
      title: '多环境支持',
      description: '开发、测试、预发布、生产环境配置分离与一键切换',
      icon: ApartmentOutlined
    },
    {
      title: '自动化依赖管理',
      description: '前后端依赖统一管理，版本锁定与冲突检测',
      icon: DatabaseOutlined
    },
    {
      title: '开发体验优先',
      description: '热重载、智能日志、调试工具链一应俱全',
      icon: ApiOutlined
    }
  ]);
  
  // 前端技术栈
  const frontendTech = ref([
    { name: 'Vue 3', description: '核心前端框架', icon: CodeOutlined },
    { name: 'TypeScript', description: '类型安全', icon: CodeOutlined },
    { name: 'Vite', description: '快速的开发服务器', icon: RocketOutlined },
    { name: 'Ant Design Vue', description: 'UI 框架', icon: RocketOutlined },
    { name: 'Pinia', description: '状态管理', icon: DatabaseOutlined },
    { name: 'Vue Router', description: '路由管理', icon: ApartmentOutlined }
  ]);
  
  // 后端技术栈
  const backendTech = ref([
    { name: 'Python 3.8+', description: '核心语言', icon: CodeOutlined },
    { name: 'FastAPI', description: '高性能API框架', icon: ApiOutlined },
    { name: 'SQLite', description: '默认数据库', icon: DatabaseOutlined },
    { name: 'SQLAlchemy', description: '可选ORM', icon: DatabaseOutlined },
    { name: 'Celery', description: '可选异步任务', icon: ApiOutlined },
    { name: 'Python-JavaScript 桥接', description: '跨语言通信', icon: ApartmentOutlined }
  ]);
  
  // DevOps技术栈
  const devopsTech = ref([
    { name: 'Docker', description: '容器技术', icon: CloudOutlined },
    { name: 'docker-compose', description: '容器编排', icon: CloudOutlined },
    { name: 'VS Code Dev Containers', description: '容器化开发', icon: CodeOutlined },
    { name: 'Python 虚拟环境', description: '环境管理', icon: ApartmentOutlined },
    { name: 'Node.js 版本管理', description: '环境管理', icon: ApartmentOutlined },
    { name: 'GitHub Actions', description: 'CI/CD 支持', icon: GithubOutlined }
  ]);
  
  // 使用场景
  const useCases = ref([
    {
      title: '全栈应用开发',
      description: '集成前端Vue和后端Python的项目',
      icon: CodeOutlined
    },
    {
      title: '数据分析应用',
      description: '需要强大数据处理和可视化能力的应用',
      icon: DatabaseOutlined
    },
    {
      title: '桌面应用程序',
      description: '通过Electron实现跨平台桌面软件',
      icon: ToolOutlined
    },
    {
      title: '中小型团队项目',
      description: '需要统一开发环境和标准化流程',
      icon: TeamOutlined
    },
    {
      title: '快速原型开发',
      description: '需要迅速搭建功能完整的应用原型',
      icon: ExperimentOutlined
    },
    {
      title: '多平台部署项目',
      description: '需要在不同环境中保持一致性',
      icon: DeploymentUnitOutlined
    }
  ]);
  </script>
  
  <style scoped>
  /* 全局变量 */
  :root {
    --primary-color: #1677ff;
    --primary-hover: #4096ff;
    --secondary-color: #52c41a;
    --accent-color: #722ed1;
    --danger-color: #ff4d4f;
    --warning-color: #faad14;
    --text-color: #000000d9;
    --text-secondary: #00000073;
    --bg-color: #ffffff;
    --bg-secondary: #f5f5f5;
    --border-color: #d9d9d9;
    --border-radius: 8px;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    --shadow-md: 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 9px 28px 8px rgba(0, 0, 0, 0.05);
    --shadow-lg: 0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05);
    --transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
  }
  
  /* 公共样式 */
  .section-title {
    text-align: center !important;
    margin-bottom: 24px !important;
  }
  
  .section-description {
    text-align: center !important;
    max-width: 800px;
    margin: 0 auto 48px !important;
    color: rgba(0, 0, 0, 0.65);
    font-size: 16px;
  }
  
  /* 英雄区块样式 */
  .hero-section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 48px;
    padding: 64px 24px;
    background: linear-gradient(135deg, #e6f7ff, #f0f5ff);
    border-radius: 12px;
    margin: 24px 24px 64px;
  }
  
  .hero-content {
    flex: 1;
  }
  
  .hero-title {
    font-size: 42px !important;
    font-weight: 800 !important;
    color: #1677ff !important;
    margin-bottom: 16px !important;
    line-height: 1.2 !important;
  }
  
  .hero-subtitle {
    font-size: 24px !important;
    color: #1677ff !important;
    margin-bottom: 16px !important;
    font-weight: 500 !important;
  }
  
  .hero-description {
    color: rgba(0, 0, 0, 0.65) !important;
    margin-bottom: 32px !important;
    line-height: 1.6 !important;
    font-size: 16px !important;
  }
  
  .hero-buttons {
    display: flex;
    gap: 16px;
  }
  
  .hero-image {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    animation: float 6s ease-in-out infinite;
  }
  
  .hero-image img {
    max-width: 100%;
    height: auto;
  }
  
  /* 特性区块样式 */
  .features-section {
    padding: 64px 24px;
    margin: 0 24px 64px;
  }
  
  .features-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .feature-card {
    border-radius: 12px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    height: 100%;
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
  }
  
  .feature-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-md);
  }
  
  .feature-icon-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100px;
    background: linear-gradient(135deg, #e6f7ff, #f0f5ff);
    border-radius: 12px 12px 0 0;
  }
  
  .feature-icon {
    font-size: 40px;
    color: #1677ff;
  }
  
  /* 核心功能区块样式 */
  .core-features-section {
    padding: 64px 24px;
    margin: 0 24px 64px;
    background-color: #f5f5f5;
    border-radius: 12px;
  }
  
  .section-header {
    margin-bottom: 48px;
  }
  
  .core-features-container {
    display: flex;
    gap: 64px;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .core-features-content {
    flex: 1;
  }
  
  .core-feature-item {
    display: flex;
    margin-bottom: 32px;
    gap: 16px;
  }
  
  .core-feature-icon {
    font-size: 28px;
    color: #1677ff;
    padding: 12px;
    background-color: #e6f7ff;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 56px;
    height: 56px;
  }
  
  .core-feature-text {
    flex: 1;
  }
  
  .core-features-image {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .core-features-image img {
    max-width: 100%;
    height: auto;
    border-radius: 12px;
    box-shadow: var(--shadow-md);
  }
  
  /* 技术栈区块样式 */
  .tech-stack-section {
    padding: 64px 24px;
    margin: 0 24px 64px;
  }
  
  .tech-stack-tabs {
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .tech-list {
    padding: 32px 0;
  }
  
  .tech-item {
    display: flex;
    gap: 16px;
    align-items: center;
    padding: 16px;
    border-radius: 8px;
    transition: background-color 0.3s ease;
  }
  
  .tech-item:hover {
    background-color: #f0f5ff;
  }
  
  .tech-icon {
    font-size: 24px;
    color: #1677ff;
  }
  
  .tech-info {
    display: flex;
    flex-direction: column;
  }
  
  /* 快速开始区块样式 */
  .quick-start-section {
    padding: 64px 24px;
    margin: 0 24px 64px;
    background-color: #f5f5f5;
    border-radius: 12px;
  }
  
  .quick-start-steps {
    max-width: 1000px;
    margin: 0 auto;
  }
  
  /* 使用场景区块样式 */
  .use-cases-section {
    padding: 64px 24px;
    margin: 0 24px 64px;
  }
  
  .use-cases-container {
    max-width: 1200px;
    margin: 0 auto;
  }
  
  .use-case-card {
    height: 100%;
    border-radius: 12px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    box-shadow: var(--shadow-sm);
  }
  
  .use-case-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-md);
  }
  
  .use-case-icon-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 120px;
    background: linear-gradient(135deg, #f0f5ff, #e6f7ff);
    border-radius: 12px 12px 0 0;
  }
  
  .use-case-icon {
    font-size: 48px;
    color: #1677ff;
  }
  
  /* 号召性用语区块样式 */
  .cta-section {
    padding: 64px 24px;
    background: linear-gradient(135deg, #1677ff, #69c0ff);
    border-radius: 12px;
    margin: 0 24px 64px;
  }
  
  .cta-content {
    text-align: center;
    max-width: 800px;
    margin: 0 auto;
  }
  
  .cta-title {
    font-size: 36px !important;
    font-weight: 700 !important;
    color: white !important;
    margin-bottom: 16px !important;
  }
  
  .cta-description {
    color: rgba(255, 255, 255, 0.9) !important;
    margin-bottom: 32px !important;
    font-size: 18px !important;
  }
  
  .cta-buttons {
    display: flex;
    gap: 16px;
    justify-content: center;
  }
  
  .secondary-btn {
    background: rgba(255, 255, 255, 0.2) !important;
    color: white !important;
    border: 1px solid white !important;
  }
  
  .secondary-btn:hover {
    background: rgba(255, 255, 255, 0.3) !important;
  }
  
  /* 动画 */
  @keyframes float {
    0% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-10px);
    }
    100% {
      transform: translateY(0px);
    }
  }
  
  /* 响应式样式 */
  @media (max-width: 1200px) {
    .features-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  @media (max-width: 992px) {
    .hero-section {
      flex-direction: column;
      text-align: center;
      padding: 48px 24px;
    }
  
    .hero-buttons {
      justify-content: center;
    }
  
    .features-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  
    .core-features-container {
      flex-direction: column;
    }
  
    .core-features-image {
      order: -1; /* 图片在移动设备上显示在前面 */
    }
  }
  
  @media (max-width: 768px) {
    .features-grid {
      grid-template-columns: 1fr;
    }
  }
  
  @media (max-width: 576px) {
    .hero-title {
      font-size: 32px !important;
    }
  
    .hero-subtitle {
      font-size: 20px !important;
    }
  
    .section-title {
      font-size: 28px !important;
    }
  
    .cta-title {
      font-size: 28px !important;
    }
  
    .cta-buttons {
      flex-direction: column;
    }
  }
  </style>