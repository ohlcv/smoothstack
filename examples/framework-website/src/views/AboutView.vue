<template>
  <div class="about">
    <h1>关于 Smoothstack</h1>
    <div class="content">
      <h2>项目愿景</h2>
      <p>
        Smoothstack 致力于解决全栈开发中的环境配置痛点，让开发者将精力集中在业务逻辑实现上，而非繁琐的环境搭建与依赖管理。
        通过 Docker 容器化技术和自动化脚本，提供一键式开发环境部署，实现「<strong>配置即代码</strong>」的开发理念。
      </p>
      
      <h2>核心理念</h2>
      <blockquote>
        环境搭建不应成为开发瓶颈，依赖管理不应消耗创造力。
      </blockquote>
      
      <h2>技术栈</h2>
      <div class="tech-stacks">
        <div class="tech-stack">
          <h3>前端技术栈</h3>
          <ul>
            <li>核心框架：Vue 3 + TypeScript</li>
            <li>构建工具：Vite</li>
            <li>UI 框架：Ant Design Vue</li>
            <li>状态管理：Pinia</li>
            <li>路由管理：Vue Router</li>
            <li>桌面应用框架：Electron</li>
          </ul>
        </div>
        <div class="tech-stack">
          <h3>后端技术栈</h3>
          <ul>
            <li>核心语言：Python 3.8+</li>
            <li>数据库：SQLite (默认)</li>
            <li>API 框架：FastAPI</li>
            <li>ORM：SQLAlchemy</li>
          </ul>
        </div>
        <div class="tech-stack">
          <h3>容器化与环境管理</h3>
          <ul>
            <li>容器技术：Docker + docker-compose</li>
            <li>容器化开发：VS Code Dev Containers</li>
            <li>环境管理：Python 虚拟环境 + Node.js 版本管理</li>
          </ul>
        </div>
      </div>
      
      <h2>贡献指南</h2>
      <p>
        我们欢迎各种形式的贡献，无论是功能请求、bug 报告还是代码贡献。
      </p>
      <ol>
        <li>Fork 本仓库</li>
        <li>创建特性分支 (<code>git checkout -b feature/amazing-feature</code>)</li>
        <li>提交更改 (<code>git commit -m 'Add some amazing feature'</code>)</li>
        <li>推送到分支 (<code>git push origin feature/amazing-feature</code>)</li>
        <li>创建 Pull Request</li>
      </ol>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'AboutView'
});
</script>

<style scoped>
.about {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.content {
  margin-top: 2rem;
  line-height: 1.6;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 2rem;
  color: #333;
  text-align: center;
}

h2 {
  font-size: 1.8rem;
  margin: 2rem 0 1rem;
  color: #444;
  border-bottom: 2px solid #eee;
  padding-bottom: 0.5rem;
}

blockquote {
  background-color: #f8f9fa;
  border-left: 4px solid #4361ee;
  padding: 1rem;
  margin: 1.5rem 0;
  font-style: italic;
  color: #555;
}

.tech-stacks {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.tech-stack {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.tech-stack h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #333;
}

.tech-stack ul {
  padding-left: 1.2rem;
}

.tech-stack li {
  margin-bottom: 0.5rem;
}

ol {
  padding-left: 1.2rem;
}

ol li {
  margin-bottom: 0.5rem;
}

code {
  background-color: #f1f1f1;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
}

@media (max-width: 768px) {
  .tech-stacks {
    grid-template-columns: 1fr;
  }
}
</style> 