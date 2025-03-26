<template>
  <div class="docs-container">
    <div class="docs-sidebar">
      <h2>文档目录</h2>
      <ul>
        <li v-for="doc in docs" :key="doc.path">
          <router-link :to="'/docs' + doc.path">{{ doc.title }}</router-link>
        </li>
      </ul>
    </div>
    <div class="docs-content">
      <router-view v-slot="{ Component }">
        <component :is="Component" />
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

interface DocRoute {
  path: string
  title: string
}

const router = useRouter()
const docs = ref<DocRoute[]>([])

// 处理文档更新
function handleDocsUpdate(event: MessageEvent) {
  if (event.data.type === 'docs-update') {
    docs.value = event.data.data
  }
}

onMounted(() => {
  // 监听文档更新
  window.addEventListener('message', handleDocsUpdate)
  
  // 初始化文档列表
  fetch('/api/docs').then(res => res.json()).then(data => {
    docs.value = data
  })
})

onUnmounted(() => {
  window.removeEventListener('message', handleDocsUpdate)
})
</script>

<style scoped>
.docs-container {
  display: flex;
  height: 100vh;
}

.docs-sidebar {
  width: 250px;
  padding: 20px;
  border-right: 1px solid #eee;
  overflow-y: auto;
}

.docs-sidebar h2 {
  margin-bottom: 20px;
  font-size: 1.5em;
}

.docs-sidebar ul {
  list-style: none;
  padding: 0;
}

.docs-sidebar li {
  margin-bottom: 10px;
}

.docs-sidebar a {
  color: #333;
  text-decoration: none;
  display: block;
  padding: 8px;
  border-radius: 4px;
}

.docs-sidebar a:hover {
  background-color: #f5f5f5;
}

.docs-sidebar a.router-link-active {
  background-color: #e6f7ff;
  color: #1890ff;
}

.docs-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

:deep(.markdown-body) {
  max-width: 800px;
  margin: 0 auto;
}
</style> 