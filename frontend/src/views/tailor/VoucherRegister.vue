<template>
  <div class="page">
    <h1>체척권 등록</h1>
    
    <div class="content-grid">
      <div class="panel">
        <div class="panel-header">
          <span>사용자 검색</span>
        </div>
        <div class="search-section">
          <input
            v-model="searchQuery"
            placeholder="군번 또는 이름으로 검색..."
            @input="searchUsers"
          />
          <div v-if="searchResults.length > 0" class="search-results">
            <div
              v-for="user in searchResults"
              :key="user.id"
              class="search-item"
              @click="selectUser(user)"
            >
              <div class="user-main">
                <span class="name">{{ user.name }}</span>
                <span class="service-number">{{ user.service_number }}</span>
                <span class="unit">{{ user.unit || '-' }}</span>
              </div>
              <span class="rank">{{ user.rank?.name || '-' }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="selectedUser" class="selected-card">
          <h3>선택된 사용자</h3>
          <div class="user-detail">
            <div class="row">
              <label>이름</label>
              <span>{{ selectedUser.name }}</span>
            </div>
            <div class="row">
              <label>군번</label>
              <span>{{ selectedUser.service_number }}</span>
            </div>
            <div class="row">
              <label>소속</label>
              <span>{{ selectedUser.unit || '-' }}</span>
            </div>
            <div class="row">
              <label>계급</label>
              <span>{{ selectedUser.rank?.name || '-' }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="panel" v-if="selectedUser">
        <div class="panel-header">
          <span>체척권 선택</span>
        </div>
        <div class="voucher-list">
          <div
            v-for="voucher in pendingVouchers"
            :key="voucher.id"
            :class="['voucher-row', { selected: selectedVoucher?.id === voucher.id }]"
            @click="selectedVoucher = voucher"
          >
            <div class="voucher-info">
              <span class="number">{{ voucher.voucher_number }}</span>
              <span class="item">{{ voucher.item?.name || `품목 #${voucher.item_id}` }}</span>
            </div>
            <div class="voucher-meta">
              <span class="amount">{{ voucher.amount?.toLocaleString() }}P</span>
              <span class="status">미등록</span>
            </div>
          </div>
          <div v-if="pendingVouchers.length === 0" class="empty">등록 가능한 체척권이 없습니다</div>
        </div>
        
        <div v-if="selectedVoucher" class="form-section">
          <div class="form-group">
            <label>체척업체</label>
            <select v-model="tailorCompanyId">
              <option value="">선택하세요</option>
              <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          
          <button
            class="btn-primary btn-block"
            :disabled="!tailorCompanyId || submitting"
            @click="registerVoucher"
          >
            {{ submitting ? '등록 중...' : '체척권 등록' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const searchQuery = ref('')
const searchResults = ref([])
const selectedUser = ref(null)
const pendingVouchers = ref([])
const selectedVoucher = ref(null)
const companies = ref([])
const tailorCompanyId = ref('')
const submitting = ref(false)

let searchTimeout

onMounted(() => {
  fetchCompanies()
})

async function fetchCompanies() {
  try {
    const res = await api.get('/tailor-vouchers/companies')
    companies.value = res.data
  } catch (e) {
    console.error('Failed to fetch companies:', e)
  }
}

async function searchUsers() {
  clearTimeout(searchTimeout)
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  
  searchTimeout = setTimeout(async () => {
    try {
      const res = await api.get('/users/search', {
        params: { keyword: searchQuery.value, page_size: 10 }
      })
      searchResults.value = res.data.items || res.data
    } catch (e) {
      console.error('Search failed:', e)
      searchResults.value = []
    }
  }, 300)
}

async function selectUser(user) {
  selectedUser.value = user
  searchQuery.value = ''
  searchResults.value = []
  selectedVoucher.value = null
  
  try {
    const res = await api.get('/tailor-vouchers', {
      params: { user_id: user.id, status: 'issued', clothing_type: 'custom' }
    })
    pendingVouchers.value = res.data.items || res.data
  } catch (e) {
    console.error('Failed to fetch vouchers:', e)
    pendingVouchers.value = []
  }
}

async function registerVoucher() {
  if (!selectedVoucher.value || !tailorCompanyId.value) return
  
  submitting.value = true
  try {
    await api.post('/tailor-vouchers/register', {
      voucher_id: selectedVoucher.value.id,
      tailor_company_id: tailorCompanyId.value
    })
    alert('체척권이 등록되었습니다.')
    selectUser(selectedUser.value)
  } catch (e) {
    alert('등록에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page {
  padding: 20px;
}

.page h1 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.panel {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 500;
}

.search-section {
  padding: 12px 16px;
  position: relative;
}

.search-section input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.search-results {
  position: absolute;
  left: 16px;
  right: 16px;
  top: 100%;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  max-height: 250px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
}

.search-item:hover {
  background: #f9fafb;
}

.user-main .name {
  font-weight: 500;
}

.user-main .service-number {
  color: #6b7280;
  font-size: 13px;
  margin-left: 8px;
}

.user-main .unit {
  color: #9ca3af;
  font-size: 12px;
  margin-left: 8px;
}

.rank {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
}

.selected-card {
  margin: 12px 16px;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
}

.selected-card h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.user-detail .row {
  display: flex;
  margin-bottom: 6px;
}

.user-detail label {
  width: 60px;
  color: #6b7280;
  font-size: 13px;
}

.user-detail span {
  font-size: 13px;
}

.voucher-list {
  max-height: 300px;
  overflow-y: auto;
}

.voucher-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
}

.voucher-row:hover {
  background: #f9fafb;
}

.voucher-row.selected {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
}

.voucher-info .number {
  font-weight: 500;
  font-size: 13px;
}

.voucher-info .item {
  font-size: 12px;
  color: #6b7280;
  margin-left: 8px;
}

.voucher-meta .amount {
  font-weight: 500;
  color: #3b82f6;
  font-size: 13px;
}

.voucher-meta .status {
  font-size: 11px;
  color: #f59e0b;
  background: #fef3c7;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 8px;
}

.empty {
  text-align: center;
  color: #9ca3af;
  padding: 24px;
  font-size: 13px;
}

.form-section {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.btn-block {
  width: 100%;
  padding: 12px;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>
