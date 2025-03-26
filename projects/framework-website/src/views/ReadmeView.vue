<template>
  <div class="readme-view">
    <div class="readme-container">
      <div v-if="isLoading" class="readme-loading">
        <div class="loading-spinner"></div>
        <p>正在加载文档...</p>
      </div>
      <div v-else>
        <div class="readme-back-links">
          <router-link to="/" class="back-link">返回首页</router-link>
          <a href="https://github.com/ohlcv/smoothstack" target="_blank" class="github-link">GitHub 仓库</a>
        </div>
        <div class="readme-content" v-html="readmeHtml"></div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { marked } from 'marked';

export default defineComponent({
  name: 'ReadmeView',
  setup() {
    const readmeHtml = ref('');
    const isLoading = ref(true);
    const errorMessage = ref('');

    onMounted(async () => {
      try {
        // 使用正确的路径从public目录加载README.md
        const response = await fetch('/README.md');
        if (!response.ok) {
          throw new Error(`无法加载README.md文件: ${response.statusText}`);
        }
        
        const markdownText = await response.text();
        // 添加图片路径处理
        const processedMarkdown = markdownText.replace(
          /!\[([^\]]*)\]\((?!http|https)([^)]+)\)/g,
          '![$1](/assets/$2)'
        );
        readmeHtml.value = marked.parse(processedMarkdown);
        isLoading.value = false;
      } catch (error) {
        console.error('加载README.md文件失败:', error);
        errorMessage.value = error instanceof Error ? error.message : '加载文档时出错';
        isLoading.value = false;
      }
    });

    return {
      readmeHtml,
      isLoading,
      errorMessage
    };
  }
});
</script>

<style scoped>
.readme-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.readme-container {
  background-color: white;
  border-radius: var(--radius-lg);
  padding: 3rem;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-neutral-200);
}

.readme-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid var(--color-primary-100);
  border-top: 5px solid var(--color-primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.readme-back-links {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-neutral-200);
}

.back-link, .github-link {
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
}

.back-link {
  background-color: var(--color-primary-50);
  color: var(--color-primary-700);
  border: 1px solid var(--color-primary-200);
}

.back-link:hover {
  background-color: var(--color-primary-100);
}

.github-link {
  background-color: var(--color-neutral-900);
  color: white;
}

.github-link:hover {
  background-color: black;
}

/* 应用全局样式到Markdown内容，使用:deep选择器 */
:deep(.readme-content) {
  line-height: 1.6;
}

:deep(.readme-content h1) {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--color-primary-700);
}

:deep(.readme-content h2) {
  font-size: 1.8rem;
  font-weight: 600;
  margin: 2rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--color-primary-100);
  color: var(--color-primary-700);
}

:deep(.readme-content h3) {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 1.5rem 0 1rem;
  color: var(--color-primary-600);
}

:deep(.readme-content p) {
  margin-bottom: 1rem;
}

:deep(.readme-content a) {
  color: var(--color-primary-600);
  text-decoration: none;
  transition: color 0.2s;
}

:deep(.readme-content a:hover) {
  color: var(--color-primary-800);
  text-decoration: underline;
}

:deep(.readme-content blockquote) {
  background-color: var(--color-primary-50);
  border-left: 4px solid var(--color-primary-300);
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  border-radius: var(--radius-md);
}

:deep(.readme-content ul), :deep(.readme-content ol) {
  margin: 1rem 0 1.5rem 1.5rem;
}

:deep(.readme-content li) {
  margin-bottom: 0.5rem;
}

:deep(.readme-content pre) {
  background-color: var(--color-neutral-100);
  border-radius: var(--radius-md);
  padding: 1rem;
  margin: 1rem 0;
  overflow-x: auto;
  font-family: 'Fira Code', 'Courier New', Courier, monospace;
  font-size: 0.9rem;
}

:deep(.readme-content code) {
  font-family: 'Fira Code', 'Courier New', Courier, monospace;
  background-color: var(--color-neutral-100);
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
}

:deep(.readme-content pre code) {
  padding: 0;
  background-color: transparent;
}

:deep(.readme-content img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1.5rem auto;
}

:deep(.readme-content table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
}

:deep(.readme-content th), :deep(.readme-content td) {
  border: 1px solid var(--color-neutral-300);
  padding: 0.75rem;
  text-align: left;
}

:deep(.readme-content th) {
  background-color: var(--color-neutral-100);
  font-weight: 600;
}

:deep(.readme-content tr:nth-child(even)) {
  background-color: var(--color-neutral-50);
}

@media (max-width: 768px) {
  .readme-container {
    padding: 2rem 1.5rem;
  }
  
  :deep(.readme-content h1) {
    font-size: 2rem;
  }
  
  :deep(.readme-content h2) {
    font-size: 1.5rem;
  }
  
  .readme-back-links {
    flex-direction: column;
    gap: 1rem;
  }
  
  .back-link, .github-link {
    text-align: center;
  }
}
</style> 