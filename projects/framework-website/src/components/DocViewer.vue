<template>
  <div class="doc-viewer">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <div class="loading-text">加载中...</div>
    </div>
    <div v-else-if="error" class="error">
      <div class="error-message">{{ error }}</div>
    </div>
    <div v-else class="markdown-body" v-html="content"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import 'github-markdown-css/github-markdown.css'

const route = useRoute()
const content = ref('')
const loading = ref(true)
const error = ref('')
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 避免重复加载同一文档
let lastPath = '';

async function loadDoc() {
  const path = route.params.path as string || '';
  
  // 如果路径相同并且已有内容，避免重复加载
  if (path === lastPath && content.value) {
    return;
  }
  
  lastPath = path;
  loading.value = true;
  error.value = '';
  
  try {
    if (!path) {
      throw new Error('无效的文档路径');
    }
    
    console.log(`加载文档: /docs/${path}`);
    const response = await fetch(`/docs/${path}`, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`文档加载失败: ${response.status}`);
    }
    
    const text = await response.text();
    
    // 检查返回内容是否是JSON格式错误信息
    try {
      const jsonData = JSON.parse(text);
      if (jsonData.error) {
        throw new Error(jsonData.error);
      }
    } catch (jsonError) {
      // 不是JSON，继续处理为Markdown
    }
    
    // 渲染Markdown
    content.value = md.render(text);
  } catch (e) {
    console.error('文档加载错误:', e);
    error.value = e instanceof Error ? e.message : '未知错误';
    content.value = ''; // 清空内容避免闪烁
  } finally {
    loading.value = false;
  }
}

// 使用immediate确保首次渲染时加载
watch(() => route.params.path, loadDoc, { immediate: true });

// 组件挂载时加载文档
onMounted(() => {
  if (!content.value) {
    loadDoc();
  }
});
</script>

<style scoped>
.doc-viewer {
  padding: 20px;
  min-height: 400px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #666;
}

.loading-text {
  margin-top: 16px;
  font-size: 16px;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #1890ff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error {
  padding: 20px;
}

.error-message {
  color: #ff4d4f;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  padding: 8px 12px;
  border-radius: 2px;
}

:deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  word-wrap: break-word;
}

:deep(.markdown-body h1) {
  padding-bottom: 0.3em;
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
}

:deep(.markdown-body h2) {
  padding-bottom: 0.3em;
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
}

:deep(.markdown-body code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
}

:deep(.markdown-body pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 3px;
}
</style> 