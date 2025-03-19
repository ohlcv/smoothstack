<template>
  <div class="app-container">
    <header class="app-header">
      <img src="./assets/logo.png" alt="Smoothstack Logo" class="app-logo" />
      <h1>Smoothstack</h1>
    </header>
    <main>
      <router-view />
    </main>
    <footer class="app-footer">
      <p>&copy; {{ currentYear }} Smoothstack - Modern Full-Stack Application Development Framework</p>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';

export default defineComponent({
  name: 'App',
  setup() {
    const currentYear = computed(() => new Date().getFullYear());
    
    return {
      currentYear
    };
  }
});
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  padding: 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.app-logo {
  height: 40px;
  margin-right: 1rem;
}

main {
  flex: 1;
  padding: 2rem;
}

.app-footer {
  padding: 1rem;
  background-color: #f8f9fa;
  border-top: 1px solid #e9ecef;
  text-align: center;
  font-size: 0.9rem;
  color: #6c757d;
}
</style> 