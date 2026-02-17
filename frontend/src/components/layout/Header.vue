<template>
  <header class="header">
    <div class="header-left">
      <h1>피복 구매관리 시스템</h1>
    </div>
    <div class="header-right">
      <span class="user-info">
        {{ authStore.user?.name }} ({{ roleLabel }})
      </span>
      <button @click="handleLogout" class="logout-btn">로그아웃</button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const roleLabel = computed(() => {
  const roles = {
    admin: '군수담당자',
    sales_office: '피복판매소',
    tailor_company: '체척업체',
    general: '일반사용자'
  }
  return roles[authStore.userRole] || '사용자'
})

function handleLogout() {
  authStore.logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #2c3e50;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 1000;
}

.header-left h1 {
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  font-size: 14px;
}

.logout-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid white;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}
</style>
