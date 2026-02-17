<template>
  <div v-if="authStore.isLoggedIn" class="app-container">
    <Header />
    <div class="main-wrapper">
      <Sidebar />
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
  <div v-else class="login-container">
    <router-view />
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import Header from '@/components/layout/Header.vue'
import Sidebar from '@/components/layout/Sidebar.vue'

const authStore = useAuthStore()
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: #f5f7fa;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-wrapper {
  display: flex;
  flex: 1;
}

.content {
  flex: 1;
  padding: 20px;
  margin-left: 250px;
  margin-top: 60px;
}

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
