<template>
  <div class="page">
    <h1>체척권 현황</h1>
    
    <div class="filter-bar">
      <div class="filter-tabs">
        <button :class="['tab', { active: statusFilter === '' }]" @click="statusFilter = ''">전체</button>
        <button :class="['tab', { active: statusFilter === 'issued' }]" @click="statusFilter = 'issued'">발급</button>
        <button :class="['tab', { active: statusFilter === 'registered' }]" @click="statusFilter = 'registered'">등록</button>
        <button :class="['tab', { active: statusFilter === 'used' }]" @click="statusFilter = 'used'">사용</button>
        <button :class="['tab', { active: statusFilter === 'cancelled' }]" @click="statusFilter = 'cancelled'">취소</button>
      </div>
      <div class="search-section">
        <input v-model="keyword" type="text" placeholder="군번, 이름 검색" class="search-input" @keyup.enter="fetchVouchers" />
        <button v-if="isAdmin" class="btn-search" @click="fetchVouchers">검색</button>
      </div>
    </div>

    <div v-if="loading" class="loading">조회 중...</div>

    <div v-else class="voucher-list">
      <div v-for="v in vouchers" :key="v.id" class="voucher-row" @click="toggleDetail(v)">
        <div class="voucher-main">
          <div class="voucher-left">
            <div class="voucher-meta">
              <span class="voucher-number">{{ v.voucher_number }}</span>
              <span :class="['status', v.status]">{{ getStatusLabel(v.status) }}</span>
            </div>
            <div class="voucher-user">
              {{ v.user?.name }} ({{ v.user?.service_number }}) - {{ v.user?.unit || '-' }}
            </div>
            <div class="voucher-item">
              {{ v.item?.name }} - {{ v.amount?.toLocaleString() }}P
            </div>
          </div>
          <div class="voucher-right">
            <span class="voucher-date">{{ formatDate(v.issued_at) }}</span>
            <span class="expand-icon">{{ expandedId === v.id ? '▲' : '▼' }}</span>
          </div>
        </div>

        <div v-if="expandedId === v.id" class="voucher-detail" @click.stop>
          <div class="detail-section">
            <div class="detail-title">사용자 정보</div>
            <div class="detail-row">
              <span>이름</span>
              <span>{{ v.user?.name }}</span>
            </div>
            <div class="detail-row">
              <span>군번</span>
              <span>{{ v.user?.service_number }}</span>
            </div>
            <div class="detail-row">
              <span>계급</span>
              <span>{{ v.user?.rank?.name || '-' }}</span>
            </div>
            <div class="detail-row">
              <span>소속</span>
              <span>{{ v.user?.unit || '-' }}</span>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-title">체척권 정보</div>
            <div class="detail-row">
              <span>발급일</span>
              <span>{{ formatDateTime(v.issued_at) }}</span>
            </div>
            <div class="detail-row" v-if="v.registered_at">
              <span>등록일</span>
              <span>{{ formatDateTime(v.registered_at) }}</span>
            </div>
            <div class="detail-row" v-if="v.expires_at">
              <span>만료일</span>
              <span>{{ v.expires_at }}</span>
            </div>
            <div class="detail-row" v-if="v.notes">
              <span>비고</span>
              <span>{{ v.notes }}</span>
            </div>
          </div>

          <div class="detail-section" v-if="v.status === 'issued'">
            <div class="detail-actions">
              <button class="btn-cancel" @click="cancelVoucher(v)">취소요청</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="vouchers.length === 0" class="empty">
        체척권 내역이 없습니다.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()
const vouchers = ref([])
const loading = ref(false)
const statusFilter = ref('')
const keyword = ref('')
const expandedId = ref(null)

const isAdmin = computed(() => authStore.userRole === 'admin')

const statusLabels = {
  issued: '발급',
  registered: '등록',
  used: '사용',
  cancelled: '취소',
  expired: '만료'
}

onMounted(() => {
  fetchVouchers()
})

watch(statusFilter, () => {
  fetchVouchers()
})

async function fetchVouchers() {
  loading.value = true
  try {
    const params = { page: 1, page_size: 50 }
    if (statusFilter.value) params.status = statusFilter.value
    if (keyword.value) params.keyword = keyword.value
    
    const response = await api.get('/tailor-vouchers', { params })
    vouchers.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch vouchers:', error)
    vouchers.value = []
  } finally {
    loading.value = false
  }
}

function toggleDetail(v) {
  expandedId.value = expandedId.value === v.id ? null : v.id
}

function getStatusLabel(status) {
  return statusLabels[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function cancelVoucher(v) {
  const reason = prompt('취소 사유를 입력하세요:')
  if (!reason) return
  
  try {
    await api.post(`/tailor-vouchers/${v.id}/cancel-request`, { reason })
    alert('취소 요청되었습니다.')
    fetchVouchers()
  } catch (error) {
    alert(error.response?.data?.detail || '취소 요청에 실패했습니다.')
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

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.filter-tabs {
  display: flex;
  gap: 6px;
  overflow-x: auto;
}

.tab {
  padding: 6px 14px;
  border: none;
  border-radius: 16px;
  background: #f3f4f6;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}

.tab.active {
  background: #7c3aed;
  color: white;
}

.search-input {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 16px;
  font-size: 13px;
  width: 180px;
}

.search-section {
  display: flex;
  gap: 8px;
}

.btn-search {
  padding: 8px 16px;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.voucher-list {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.voucher-row {
  border-bottom: 1px solid #f3f4f6;
}

.voucher-row:last-child {
  border-bottom: none;
}

.voucher-main {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
}

.voucher-main:hover {
  background: #fafafa;
}

.voucher-left {
  flex: 1;
}

.voucher-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.voucher-number {
  font-size: 12px;
  color: #6b7280;
  font-family: monospace;
}

.status {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.status.issued { background: #fef3c7; color: #92400e; }
.status.registered { background: #dbeafe; color: #1d4ed8; }
.status.used { background: #dcfce7; color: #166534; }
.status.cancelled { background: #fee2e2; color: #dc2626; }
.status.expired { background: #f3f4f6; color: #6b7280; }

.voucher-user {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 2px;
}

.voucher-item {
  font-size: 13px;
  color: #6b7280;
}

.voucher-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.voucher-date {
  font-size: 12px;
  color: #9ca3af;
}

.expand-icon {
  font-size: 12px;
  color: #9ca3af;
}

.voucher-detail {
  border-top: 1px solid #f3f4f6;
  padding: 14px 16px;
  background: #fafafa;
}

.detail-section {
  margin-bottom: 14px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-title {
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.detail-row {
  display: flex;
  font-size: 13px;
  padding: 4px 0;
}

.detail-row span:first-child {
  color: #6b7280;
  min-width: 60px;
}

.detail-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  cursor: pointer;
}

.empty {
  text-align: center;
  padding: 60px;
  color: #9ca3af;
}
</style>
