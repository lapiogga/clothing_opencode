<template>
  <div class="profile">
    <div class="page-header">
      <h1>프로필</h1>
    </div>

    <div class="profile-container">
      <div class="profile-card">
        <div class="profile-header">
          <div class="avatar">
            {{ userInfo.name?.charAt(0) }}
          </div>
          <div class="profile-info">
            <h2>{{ userInfo.name }}</h2>
            <p>{{ userInfo.rank?.name || '-' }} / {{ userInfo.unit || '-' }}</p>
          </div>
        </div>

        <div class="info-section">
          <h3>기본 정보</h3>
          <div class="info-list">
            <div class="info-item">
              <label>아이디</label>
              <span>{{ userInfo.username }}</span>
            </div>
            <div class="info-item">
              <label>군번</label>
              <span>{{ userInfo.service_number || '-' }}</span>
            </div>
            <div class="info-item">
              <label>계급</label>
              <span>{{ userInfo.rank?.name || '-' }}</span>
            </div>
            <div class="info-item">
              <label>소속</label>
              <span>{{ userInfo.unit || '-' }}</span>
            </div>
            <div class="info-item">
              <label>이메일</label>
              <span>{{ userInfo.email || '-' }}</span>
            </div>
            <div class="info-item">
              <label>연락처</label>
              <span>{{ userInfo.phone || '-' }}</span>
            </div>
            <div class="info-item">
              <label>복무년수</label>
              <span>{{ userInfo.service_years || 0 }}년</span>
            </div>
            <div class="info-item">
              <label>입대일</label>
              <span>{{ formatDate(userInfo.enlistment_date) }}</span>
            </div>
            <div class="info-item">
              <label>전역예정일</label>
              <span>{{ formatDate(userInfo.retirement_date) }}</span>
            </div>
          </div>
        </div>

        <div class="info-section">
          <h3>포인트 정보</h3>
          <div class="point-cards">
            <div class="point-card main">
              <div class="point-label">보유 포인트</div>
              <div class="point-amount">{{ userInfo.current_point?.toLocaleString() }}P</div>
            </div>
            <div class="point-card sub">
              <div class="point-label">예약 포인트</div>
              <div class="point-amount">{{ userInfo.reserved_point?.toLocaleString() }}P</div>
            </div>
            <div class="point-card sub">
              <div class="point-label">사용 가능</div>
              <div class="point-amount">{{ userInfo.available_point?.toLocaleString() }}P</div>
            </div>
          </div>
        </div>
      </div>

      <div class="edit-section">
        <h3>정보 수정</h3>
        <form @submit.prevent="updateProfile" class="edit-form">
          <div class="form-group">
            <label>연락처</label>
            <input v-model="form.phone" type="tel" placeholder="연락처 입력" />
          </div>

          <div class="form-group">
            <label>이메일</label>
            <input v-model="form.email" type="email" placeholder="이메일 입력" />
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? '저장 중...' : '저장' }}
            </button>
          </div>
        </form>

        <h3>비밀번호 변경</h3>
        <form @submit.prevent="changePassword" class="edit-form">
          <div class="form-group">
            <label>현재 비밀번호</label>
            <input v-model="passwordForm.currentPassword" type="password" />
          </div>
          <div class="form-group">
            <label>새 비밀번호</label>
            <input v-model="passwordForm.newPassword" type="password" />
          </div>
          <div class="form-group">
            <label>새 비밀번호 확인</label>
            <input v-model="passwordForm.confirmPassword" type="password" />
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="changingPassword">
              {{ changingPassword ? '변경 중...' : '비밀번호 변경' }}
            </button>
          </div>
        </form>

        <div class="size-info-section">
          <h3>체척 정보</h3>
          <div v-if="userInfo.sizeInfo" class="size-display">
            <div class="size-item" v-for="(value, key) in userInfo.sizeInfo" :key="key">
              <span class="size-label">{{ getSizeLabel(key) }}</span>
              <span class="size-value">{{ value }}cm</span>
            </div>
          </div>
          <div v-else class="no-size">
            <p>등록된 체척 정보가 없습니다.</p>
            <p class="hint">체척업체에서 체척권 등록 후 확인 가능합니다.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()

const saving = ref(false)
const changingPassword = ref(false)

const userInfo = computed(() => authStore.user || {})

const form = reactive({
  phone: '',
  email: ''
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

onMounted(() => {
  form.phone = userInfo.value.phone || ''
  form.email = userInfo.value.email || ''
})

async function updateProfile() {
  saving.value = true
  try {
    await api.put('/users/me', form)
    await authStore.fetchUser()
    alert('정보가 수정되었습니다.')
  } catch (error) {
    alert('수정에 실패했습니다.')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (!passwordForm.currentPassword || !passwordForm.newPassword) {
    alert('비밀번호를 모두 입력해주세요.')
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    alert('새 비밀번호가 일치하지 않습니다.')
    return
  }

  if (passwordForm.newPassword.length < 6) {
    alert('비밀번호는 6자 이상이어야 합니다.')
    return
  }

  changingPassword.value = true
  try {
    await api.put('/users/me/password', {
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword
    })
    alert('비밀번호가 변경되었습니다.')
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    alert('비밀번호 변경에 실패했습니다. 현재 비밀번호를 확인해주세요.')
  } finally {
    changingPassword.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

function getSizeLabel(key) {
  const labels = {
    height: '신장',
    weight: '체중',
    chest: '가슴둘레',
    waist: '허리둘레',
    hip: '엉덩이둘레',
    shoulder: '어깨너비',
    arm: '팔길이',
    leg: '다리길이'
  }
  return labels[key] || key
}
</script>

<style scoped>
.profile {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.profile-container {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 24px;
}

.profile-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 20px;
}

.avatar {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
}

.profile-info h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 4px;
}

.profile-info p {
  color: #6b7280;
  font-size: 14px;
}

.info-section {
  margin-bottom: 24px;
}

.info-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 12px;
}

.info-list {
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #e5e7eb;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item label {
  color: #6b7280;
  font-size: 14px;
}

.info-item span {
  font-size: 14px;
}

.point-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.point-card {
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.point-card.main {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.point-card.sub {
  background: #f3f4f6;
}

.point-label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.point-amount {
  font-size: 24px;
  font-weight: 700;
}

.point-card.sub .point-amount {
  font-size: 20px;
  color: #1f2937;
}

.edit-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
}

.edit-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.edit-form {
  margin-bottom: 32px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.size-info-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.size-display {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.size-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.size-label {
  color: #6b7280;
  font-size: 13px;
}

.size-value {
  font-weight: 500;
}

.no-size {
  text-align: center;
  padding: 24px;
  color: #9ca3af;
}

.no-size .hint {
  font-size: 13px;
  margin-top: 8px;
}
</style>
