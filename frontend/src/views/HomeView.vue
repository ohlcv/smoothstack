<template>
  <div class="home">
    <h1>Smoothstack</h1>
    <p class="subtitle">现代化全栈应用开发框架</p>
    <p class="description">
      一键式环境部署，Docker 容器化管理，跨平台兼容性，自动化依赖管理
    </p>
    <div class="feature-grid">
      <div class="feature-card">
        <h3>一键式环境部署</h3>
        <p>5分钟内完成从零到可用的全栈开发环境搭建</p>
      </div>
      <div class="feature-card">
        <h3>Docker 容器化管理</h3>
        <p>隔离的开发环境确保"我这能运行"就是"到处能运行"</p>
      </div>
      <div class="feature-card">
        <h3>跨平台兼容</h3>
        <p>Windows、macOS、Linux 全平台支持</p>
      </div>
      <div class="feature-card">
        <h3>自动化依赖管理</h3>
        <p>前后端依赖统一管理，版本锁定与冲突检测</p>
      </div>
    </div>
    <div class="cta-container">
      <button class="cta-button">快速开始</button>
      <button class="cta-button secondary">查看文档</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'HomeView'
});
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #333;
}

.subtitle {
  font-size: 1.5rem;
  margin-bottom: 2rem;
  color: #666;
}

.description {
  font-size: 1.2rem;
  max-width: 800px;
  margin: 0 auto 3rem;
  line-height: 1.6;
  color: #555;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.feature-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-card h3 {
  margin-top: 0;
  color: #333;
}

.cta-container {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.cta-button {
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.cta-button:hover {
  background-color: #3a56d4;
}

.cta-button.secondary {
  background-color: transparent;
  border: 1px solid #4361ee;
  color: #4361ee;
}

.cta-button.secondary:hover {
  background-color: rgba(67, 97, 238, 0.1);
}
</style> 