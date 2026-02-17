<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ user ? '사용자 수정' : '사용자 등록' }}</h2>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>

      <form @submit.prevent="handleSubmit" class="user-form">
        <div class="form-group">
          <label>아이디 <span class="required">*</span></label>
          <input
            v-model="form.username"
            type="text"
            placeholder="아이디 입력"
            :disabled="!!user"
            required
          />
        </div>

        <div class="form-group">
          <label>군번 <span class="required">*</span></label>
          <input
            v-model="form.service_number"
            type="text"
            placeholder="군번 입력 (예: 21-123456)"
            required
          />
        </div>

        <div class="form-group">
          <label>이름 <span class="required">*</span></label>
          <input v-model="form.name" type="text" placeholder="이름 입력" required />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>소속(부서)</label>
            <input v-model="form.unit" type="text" placeholder="소속 입력" />
          </div>
          <div class="form-group">
            <label>계급</label>
            <select v-model="form.rank_id">
              <option :value="null">선택하세요</option>
              <option v-for="rank in ranks" :key="rank.id" :value="rank.id">
                {{ rank.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>입대일</label>
            <input v-model="form.enlistment_date" type="date" placeholder="입대일" />
          </div>
          <div class="form-group">
            <label>전역예정일</label>
            <input v-model="form.retirement_date" type="date" placeholder="전역예정일" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>전화번호</label>
            <input v-model="form.phone" type="tel" placeholder="전화번호 입력" />
          </div>
          <div class="form-group">
            <label>이메일</label>
            <input v-model="form.email" type="email" placeholder="이메일 입력" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>권한 <span class="required">*</span></label>
            <select v-model="form.role" required>
              <option value="">선택하세요</option>
              <option value="admin">관리자</option>
              <option value="general">일반사용자</option>
              <option value="sales_office">판매소</option>
              <option value="tailor_company">체척업체</option>
            </select>
          </div>
          <div class="form-group">
            <label>상태</label>
            <select v-model="form.is_active">
              <option :value="true">활성</option>
              <option :value="false">비활성</option>
            </select>
          </div>
        </div>

        <div v-if="form.role === 'sales_office'" class="form-group">
          <label>소속 판매소</label>
          <select v-model="form.sales_office_id">
            <option :value="null">선택하세요</option>
            <option v-for="office in salesOffices" :key="office.id" :value="office.id">
              {{ office.name }}
            </option>
          </select>
        </div>

        <div v-if="form.role === 'tailor_company'" class="form-group">
          <label>소속 체척업체</label>
          <select v-model="form.tailor_company_id">
            <option :value="null">선택하세요</option>
            <option v-for="company in tailorCompanies" :key="company.id" :value="company.id">
              {{ company.name }}
            </option>
          </select>
        </div>

        <div v-if="!user" class="form-group">
          <label>초기 비밀번호 <span class="required">*</span></label>
          <input v-model="form.password" type="password" placeholder="비밀번호 입력" required />
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" @click="$emit('close')">취소</button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? '저장 중...' : '저장' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import api from '@/api'

const props = defineProps({
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

const loading = ref(false)
const salesOffices = ref([])
const tailorCompanies = ref([])
const ranks = ref([])

const form = reactive({
  username: '',
  service_number: '',
  name: '',
  unit: '',
  rank_id: null,
  enlistment_date: '',
  retirement_date: '',
  phone: '',
  email: '',
  role: '',
  is_active: true,
  sales_office_id: null,
  tailor_company_id: null,
  password: '',
})

watch(() => props.user, (newUser) => {
  if (newUser) {
    Object.assign(form, {
      username: newUser.username || '',
      service_number: newUser.service_number || '',
      name: newUser.name || '',
      unit: newUser.unit || '',
      rank_id: newUser.rank?.id || newUser.rank_id || null,
      enlistment_date: newUser.enlistment_date || '',
      retirement_date: newUser.retirement_date || '',
      phone: newUser.phone || '',
      email: newUser.email || '',
      role: newUser.role || '',
      is_active: newUser.is_active !== false,
      sales_office_id: newUser.sales_office_id || null,
      tailor_company_id: newUser.tailor_company_id || null,
      password: '',
    })
  } else {
    Object.assign(form, {
      username: '',
      service_number: '',
      name: '',
      unit: '',
      rank_id: null,
      enlistment_date: '',
      retirement_date: '',
      phone: '',
      email: '',
      role: '',
      is_active: true,
      sales_office_id: null,
      tailor_company_id: null,
      password: '',
    })
  }
}, { immediate: true })

onMounted(() => {
  fetchSalesOffices()
  fetchTailorCompanies()
  fetchRanks()
})

async function fetchSalesOffices() {
  try {
    const response = await api.get('/sales-offices')
    salesOffices.value = response.data
  } catch (error) {
    console.error('Failed to fetch sales offices:', error)
  }
}

async function fetchTailorCompanies() {
  try {
    const response = await api.get('/tailor-vouchers/companies')
    tailorCompanies.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch tailor companies:', error)
  }
}

async function fetchRanks() {
  try {
    const response = await api.get('/users/ranks')
    ranks.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch ranks:', error)
  }
}

async function handleSubmit() {
  loading.value = true
  try {
    const userData = { ...form }
    if (props.user) {
      delete userData.password
      delete userData.username
    }
    if (!userData.sales_office_id) delete userData.sales_office_id
    if (!userData.tailor_company_id) delete userData.tailor_company_id
    if (!userData.rank_id) delete userData.rank_id
    if (!userData.enlistment_date) delete userData.enlistment_date
    if (!userData.retirement_date) delete userData.retirement_date
    emit('save', userData)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
}

.user-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.required {
  color: #dc2626;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}
</style>
