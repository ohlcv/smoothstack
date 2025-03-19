<template>
  <div class="not-found">
    <h1>404</h1>
    <h2>页面未找到</h2>
    <p>抱歉，您访问的页面不存在。</p>
    <router-link to="/" class="back-button">返回首页</router-link>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'NotFoundView'
});
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 70vh;
  text-align: center;
}

h1 {
  font-size: 6rem;
  margin: 0;
  color: #4361ee;
  line-height: 1;
}

h2 {
  font-size: 2rem;
  margin: 1rem 0;
  color: #333;
}

p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  color: #666;
}

.back-button {
  background-color: #4361ee;
  color: white;
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.back-button:hover {
  background-color: #3a56d4;
}
</style>