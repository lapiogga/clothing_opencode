<template>
  <div class="login-box">
    <h1>피복 구매관리 시스템</h1>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>아이디</label>
        <input 
          v-model="username" 
          type="text" 
          placeholder="아이디를 입력하세요"
          required
        />
      </div>
      <div class="form-group">
        <label>비밀번호</label>
        <input 
          v-model="password" 
          type="password" 
          placeholder="비밀번호를 입력하세요"
          required
        />
      </div>
      <p v-if="error" class="error-message">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? '로그인 중...' : '로그인' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true

  const result = await authStore.login(username.value, password.value)
  
  loading.value = false

  if (result.success) {
    router.push({ name: 'Dashboard' })
  } else {
    error.value = result.message
  }
}
</script>

<style scoped>
.login-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h1 {
  font-size: 24px;
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

input:focus {
  outline: none;
  border-color: #4a90d9;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
  margin-bottom: 15px;
}

button {
  width: 100%;
  padding: 12px;
  background-color: #4a90d9;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

button:hover:not(:disabled) {
  background-color: #357abd;
}

button:disabled {
  background-color: #a0c4e8;
  cursor: not-allowed;
}
</style>
