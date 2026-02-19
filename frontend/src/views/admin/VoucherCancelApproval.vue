<template>
  <div class="voucher-approval">
    <div class="page-header">
      <h1>체척권 취소 승인</h1>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>데이터 로딩 중...</span>
    </div>

    <div v-else-if="vouchers.length === 0" class="empty-state">
      <p>승인 대기 중인 취소 요청이 없습니다.</p>
    </div>

    <div v-else class="voucher-list">
      <div v-for="v in vouchers" :key="v.id" class="voucher-card">
        <div class="voucher-header">
          <div class="voucher-number">{{ v.voucher_number }}</div>
          <span class="status-badge pending">승인 대기</span>
        </div>
        
        <div class="voucher-body">
          <div class="info-grid">
            <div class="info-item">
              <label>신청자</label>
              <span>{{ v.user?.name }} ({{ v.user?.service_number }})</span>
            </div>
            <div class="info-item">
              <label>소속</label>
              <span>{{ v.user?.unit || '-' }}</span>
            </div>
            <div class="info-item">
              <label>품목</label>
              <span>{{ v.item?.name }}</span>
            </div>
            <div class="info-item">
              <label>금액</label>
              <span class="amount">{{ v.amount?.toLocaleString() }}원</span>
            </div>
            <div class="info-item full">
              <label>취소 사유</label>
              <span>{{ v.cancel_reason || '-' }}</span>
            </div>
            <div class="info-item">
              <label>발행일</label>
              <span>{{ formatDate(v.issued_at) }}</span>
            </div>
          </div>
        </div>

        <div class="voucher-footer">
          <div class="refund-info">
            <strong>환불 예정 포인트:</strong> {{ v.amount?.toLocaleString() }}P
          </div>
          <div class="action-buttons">
            <button class="btn btn-reject" @click="handleReject(v)" :disabled="processing">
              반려
            </button>
            <button class="btn btn-approve" @click="handleApprove(v)" :disabled="processing">
              승인
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 반려 사유 모달 -->
    <div v-if="showRejectModal" class="modal-overlay" @click.self="closeRejectModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>취소 요청 반려</h3>
          <button class="close-btn" @click="closeRejectModal">&times;</button>
        </div>
        <div class="modal-body">
          <p><strong>{{ selectedVoucher?.voucher_number }}</strong></p>
          <div class="form-group">
            <label>반려 사유</label>
            <textarea v-model="rejectReason" rows="3" placeholder="반려 사유를 입력하세요"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeRejectModal">취소</button>
          <button class="btn btn-reject" @click="confirmReject" :disabled="!rejectReason.trim() || processing">
            반려 확인
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const processing = ref(false)
const vouchers = ref([])
const showRejectModal = ref(false)
const selectedVoucher = ref(null)
const rejectReason = ref('')

onMounted(() => {
  fetchVouchers()
})

async function fetchVouchers() {
  loading.value = true
  try {
    const res = await api.get('/tailor-vouchers', {
      params: { status: 'cancel_requested', page_size: 50 }
    })
    vouchers.value = res.data.items || []
  } catch (e) {
    console.error('Failed to fetch vouchers:', e)
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

async function handleApprove(voucher) {
  if (!confirm(`${voucher.voucher_number} 체척권 취소를 승인하시겠습니까?\n환불 포인트: ${voucher.amount?.toLocaleString()}P`)) {
    return
  }
  
  processing.value = true
  try {
    await api.post(`/tailor-vouchers/${voucher.id}/approve-cancel`, null, {
      params: { approved: true }
    })
    alert('취소가 승인되었습니다.')
    fetchVouchers()
  } catch (e) {
    alert(e.response?.data?.detail || '승인 처리에 실패했습니다.')
  } finally {
    processing.value = false
  }
}

function handleReject(voucher) {
  selectedVoucher.value = voucher
  rejectReason.value = ''
  showRejectModal.value = true
}

function closeRejectModal() {
  showRejectModal.value = false
  selectedVoucher.value = null
  rejectReason.value = ''
}

async function confirmReject() {
  if (!rejectReason.value.trim()) return
  
  processing.value = true
  try {
    await api.post(`/tailor-vouchers/${selectedVoucher.value.id}/approve-cancel`, null, {
      params: { approved: false }
    })
    alert('취소 요청이 반려되었습니다.')
    closeRejectModal()
    fetchVouchers()
  } catch (e) {
    alert(e.response?.data?.detail || '반려 처리에 실패했습니다.')
  } finally {
    processing.value = false
  }
}
</script>

<style scoped>
.voucher-approval {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.voucher-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.voucher-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.voucher-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fef3c7;
  border-bottom: 1px solid #fde68a;
}

.voucher-number {
  font-weight: 600;
  font-size: 15px;
  font-family: monospace;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.voucher-body {
  padding: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full {
  grid-column: span 2;
}

.info-item label {
  font-size: 12px;
  color: #6b7280;
}

.info-item span {
  font-size: 14px;
  color: #111;
}

.info-item .amount {
  font-weight: 600;
  color: #3b82f6;
}

.voucher-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.refund-info {
  font-size: 14px;
  color: #374151;
}

.refund-info strong {
  color: #dc2626;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-approve {
  background: #3b82f6;
  color: white;
}

.btn-approve:hover:not(:disabled) {
  background: #2563eb;
}

.btn-reject {
  background: #fee2e2;
  color: #dc2626;
}

.btn-reject:hover:not(:disabled) {
  background: #fecaca;
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
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 400px;
  margin: 20px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  font-size: 16px;
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

.modal-body p {
  margin-bottom: 16px;
  font-size: 14px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}
</style>
