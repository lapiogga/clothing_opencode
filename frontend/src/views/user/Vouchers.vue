<template>
  <div class="vouchers">
    <div class="page-header">
      <h1>체척권 조회</h1>
    </div>

    <!-- 상태 필터 -->
    <div class="tabs">
      <button :class="['tab', { active: activeStatus === null }]" @click="changeStatus(null)">
        전체
      </button>
      <button :class="['tab', { active: activeStatus === 'issued' }]" @click="changeStatus('issued')">
        발행됨
      </button>
      <button :class="['tab', { active: activeStatus === 'registered' }]" @click="changeStatus('registered')">
        등록됨
      </button>
      <button :class="['tab', { active: activeStatus === 'used' }]" @click="changeStatus('used')">
        사용완료
      </button>
      <button :class="['tab', { active: activeStatus === 'cancelled' }]" @click="changeStatus('cancelled')">
        취소됨
      </button>
    </div>

    <!-- 체척권 목록 -->
    <div class="voucher-list">
      <div v-if="loading" class="loading">로딩 중...</div>
      
      <div v-else-if="vouchers.length === 0" class="empty-state">
        <p>발행된 체척권이 없습니다.</p>
        <router-link to="/user/shop" class="btn btn-primary">쇼핑하러 가기</router-link>
      </div>

      <div v-else>
        <div v-for="voucher in vouchers" :key="voucher.id" class="voucher-card">
          <div class="voucher-header">
            <div class="voucher-number">
              <span class="label">체척권 번호</span>
              <strong>{{ voucher.voucher_number }}</strong>
            </div>
            <div :class="['voucher-status', voucher.status]">
              {{ getStatusLabel(voucher.status) }}
            </div>
          </div>
          
          <div class="voucher-body">
            <div class="info-row">
              <span class="label">품목</span>
              <span class="value">{{ voucher.item?.name || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">수량</span>
              <span class="value">{{ voucher.amount }}장</span>
            </div>
            <div class="info-row">
              <span class="label">발행일</span>
              <span class="value">{{ formatDate(voucher.issued_at) }}</span>
            </div>
            <div class="info-row">
              <span class="label">만료일</span>
              <span class="value">{{ formatDate(voucher.expires_at) }}</span>
            </div>
            <div v-if="voucher.registered_at" class="info-row">
              <span class="label">등록일</span>
              <span class="value">{{ formatDate(voucher.registered_at) }}</span>
            </div>
            <div v-if="voucher.used_at" class="info-row">
              <span class="label">사용일</span>
              <span class="value">{{ formatDate(voucher.used_at) }}</span>
            </div>
            <div v-if="voucher.notes" class="info-row">
              <span class="label">비고</span>
              <span class="value">{{ voucher.notes }}</span>
            </div>
          </div>

          <div v-if="voucher.status === 'issued'" class="voucher-footer">
            <p class="usage-guide">
              체척업체에 체척권 번호를 제시하여 맞춤 제작을 받으시기 바랍니다.
            </p>
            <button class="btn btn-outline btn-sm" @click="showCancelModal(voucher)">
              취소 요청
            </button>
          </div>
        </div>
      </div>
    </div>

    <Pagination
      v-if="vouchers.length > 0"
      :current-page="pagination.page"
      :total-pages="totalPages"
      @page-change="handlePageChange"
    />

    <!-- 취소 요청 모달 -->
    <div v-if="showCancelDialog" class="modal-overlay" @click.self="closeCancelModal">
      <div class="modal-content modal-small">
        <div class="modal-header">
          <h3>체척권 취소 요청</h3>
          <button class="close-btn" @click="closeCancelModal">×</button>
        </div>
        <div class="modal-body">
          <p class="voucher-info">
            체척권 번호: <strong>{{ selectedVoucher?.voucher_number }}</strong>
          </p>
          <div class="form-group">
            <label>취소 사유</label>
            <textarea v-model="cancelReason" rows="3" placeholder="취소 사유를 입력해주세요."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeCancelModal">취소</button>
          <button class="btn btn-danger" @click="requestCancel" :disabled="!cancelReason.trim() || canceling">
            {{ canceling ? '처리 중...' : '취소 요청' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 사용 안내 -->
    <div class="usage-info">
      <h3>체척권 사용 안내</h3>
      <ul>
        <li>체척권은 맞춤피복 구매 시 자동 발행됩니다.</li>
        <li>체척권 번호를 체척업체에 제시하면 맞춤 제작을 받을 수 있습니다.</li>
        <li>체척권은 발행일로부터 1년간 유효합니다.</li>
        <li>사용하지 않은 체척권은 취소 요청 후 환불 처리됩니다.</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import Pagination from '@/components/common/Pagination.vue'

const loading = ref(false)
const vouchers = ref([])
const activeStatus = ref(null)

const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0
})

// 취소 요청 관련
const showCancelDialog = ref(false)
const selectedVoucher = ref(null)
const cancelReason = ref('')
const canceling = ref(false)

const totalPages = computed(() => {
  return Math.ceil(pagination.value.total / pagination.value.pageSize)
})

onMounted(() => {
  fetchVouchers()
})

async function fetchVouchers() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    }
    if (activeStatus.value) {
      params.status = activeStatus.value
    }
    const res = await api.get('/tailor-vouchers', { params })
    vouchers.value = res.data.items || []
    pagination.value.total = res.data.total || 0
  } catch (error) {
    console.error('Failed to fetch vouchers:', error)
  } finally {
    loading.value = false
  }
}

function changeStatus(status) {
  activeStatus.value = status
  pagination.value.page = 1
  fetchVouchers()
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchVouchers()
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

function getStatusLabel(status) {
  const labels = {
    issued: '발행됨',
    registered: '등록됨',
    used: '사용완료',
    cancelled: '취소됨'
  }
  return labels[status] || status
}

function showCancelModal(voucher) {
  selectedVoucher.value = voucher
  cancelReason.value = ''
  showCancelDialog.value = true
}

function closeCancelModal() {
  showCancelDialog.value = false
  selectedVoucher.value = null
  cancelReason.value = ''
}

async function requestCancel() {
  if (!cancelReason.value.trim()) return
  
  canceling.value = true
  try {
    await api.post(`/tailor-vouchers/${selectedVoucher.value.id}/cancel-request`, {
      reason: cancelReason.value.trim()
    })
    alert('취소 요청이 완료되었습니다.')
    closeCancelModal()
    fetchVouchers()
  } catch (error) {
    alert(error.response?.data?.detail || '취소 요청에 실패했습니다.')
  } finally {
    canceling.value = false
  }
}
</script>

<style scoped>
.vouchers {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tab {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.tab.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
}

.empty-state p {
  margin-bottom: 20px;
  color: #6b7280;
}

.voucher-list {
  margin-bottom: 20px;
}

.voucher-card {
  background: white;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.voucher-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.voucher-number .label {
  font-size: 12px;
  color: #6b7280;
  display: block;
  margin-bottom: 2px;
}

.voucher-number strong {
  font-size: 18px;
  color: #1f2937;
  font-family: monospace;
}

.voucher-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.voucher-status.issued {
  background: #dbeafe;
  color: #1e40af;
}

.voucher-status.registered {
  background: #fef3c7;
  color: #92400e;
}

.voucher-status.used {
  background: #dcfce7;
  color: #166534;
}

.voucher-status.cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.voucher-body {
  padding: 16px 20px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  width: 80px;
  font-size: 13px;
  color: #6b7280;
  flex-shrink: 0;
}

.info-row .value {
  font-size: 14px;
  color: #1f2937;
}

.voucher-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.usage-guide {
  font-size: 13px;
  color: #6b7280;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline:hover {
  background: #f9fafb;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: none;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.usage-info {
  background: #f9fafb;
  padding: 20px;
  border-radius: 8px;
  margin-top: 24px;
}

.usage-info h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.usage-info ul {
  list-style: disc;
  padding-left: 20px;
  font-size: 13px;
  color: #6b7280;
}

.usage-info li {
  margin-bottom: 6px;
}

/* Modal */
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
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
}

.modal-small {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
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

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}

.voucher-info {
  background: #f3f4f6;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}
</style>
