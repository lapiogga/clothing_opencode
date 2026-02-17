<template>
  <div class="page">
    <h1>반품 처리</h1>
    
    <div class="tabs">
      <button :class="['tab', { active: tab === 'orders' }]" @click="tab = 'orders'">
        반품 가능 주문 ({{ refundableOrders.length }})
      </button>
      <button :class="['tab', { active: tab === 'history' }]" @click="tab = 'history'">
        반품 완료 ({{ refundedOrders.length }})
      </button>
    </div>
    
    <div v-if="tab === 'orders'" class="panel">
      <div class="order-list">
        <div v-for="order in refundableOrders" :key="order.id" class="order-row">
          <div class="order-info">
            <span class="order-number">{{ order.order_number }}</span>
            <span class="user">{{ order.user?.name }} ({{ order.user?.service_number }})</span>
            <span class="date">{{ formatDate(order.ordered_at) }}</span>
          </div>
          <div class="order-items">
            <span v-for="item in order.items" :key="item.id" class="item-tag">
              {{ item.item_name }} x{{ item.quantity }}
            </span>
          </div>
          <div class="order-meta">
            <span class="amount">{{ order.total_amount?.toLocaleString() }}P</span>
            <span class="status delivered">배송완료</span>
          </div>
          <button class="btn-sm btn-primary" @click="openRefundModal(order)">반품</button>
        </div>
        <div v-if="refundableOrders.length === 0" class="empty">반품 가능한 주문이 없습니다</div>
      </div>
    </div>
    
    <div v-else class="panel">
      <div class="order-list">
        <div v-for="order in refundedOrders" :key="order.id" class="order-row">
          <div class="order-info">
            <span class="order-number">{{ order.order_number }}</span>
            <span class="user">{{ order.user?.name }}</span>
            <span class="date">{{ formatDate(order.ordered_at) }}</span>
          </div>
          <div class="order-meta">
            <span class="amount">{{ order.total_amount?.toLocaleString() }}P</span>
            <span class="status refunded">반품완료</span>
          </div>
        </div>
        <div v-if="refundedOrders.length === 0" class="empty">반품 완료된 주문이 없습니다</div>
      </div>
    </div>
    
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>반품 처리</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <label>주문번호</label>
            <span>{{ selectedOrder?.order_number }}</span>
          </div>
          <div class="info-row">
            <label>구매자</label>
            <span>{{ selectedOrder?.user?.name }} ({{ selectedOrder?.user?.service_number }})</span>
          </div>
          
          <div class="refund-items">
            <label>반품할 상품 선택</label>
            <div v-for="item in selectedOrder?.items" :key="item.id" class="refund-item">
              <label class="checkbox">
                <input type="checkbox" v-model="refundItems[item.id]" />
                <span>{{ item.item_name }} ({{ item.spec_size }}) x{{ item.quantity }}</span>
              </label>
              <span class="item-amount">{{ item.total_price?.toLocaleString() }}P</span>
            </div>
          </div>
          
          <div class="form-group">
            <label>반품 사유</label>
            <select v-model="refundReason">
              <option value="">선택하세요</option>
              <option value="defect">제품 불량</option>
              <option value="wrong">오배송</option>
              <option value="size">사이즈 불만</option>
              <option value="other">기타</option>
            </select>
          </div>
          
          <div class="refund-summary">
            <span>환불 예정 포인트</span>
            <span class="refund-amount">{{ refundAmount.toLocaleString() }}P</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-outline" @click="closeModal">취소</button>
          <button class="btn-primary" :disabled="!canRefund || processing" @click="processRefund">
            {{ processing ? '처리 중...' : '반품 처리' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const auth = useAuthStore()
const tab = ref('orders')
const orders = ref([])
const showModal = ref(false)
const selectedOrder = ref(null)
const refundItems = ref({})
const refundReason = ref('')
const processing = ref(false)

const refundableOrders = computed(() => {
  return orders.value.filter(o => o.status === 'delivered' || o.status === 'shipped')
})

const refundedOrders = computed(() => {
  return orders.value.filter(o => o.status === 'refunded')
})

const refundAmount = computed(() => {
  if (!selectedOrder.value) return 0
  return selectedOrder.value.items
    .filter(item => refundItems.value[item.id])
    .reduce((sum, item) => sum + item.total_price, 0)
})

const canRefund = computed(() => {
  return Object.values(refundItems.value).some(v => v) && refundReason.value
})

onMounted(() => {
  fetchOrders()
})

async function fetchOrders() {
  try {
    const res = await api.get('/sales/orders', {
      params: { sales_office_id: auth.user?.sales_office_id }
    })
    orders.value = res.data.items || res.data
  } catch (e) {
    console.error('Failed to fetch orders:', e)
  }
}

function openRefundModal(order) {
  selectedOrder.value = order
  refundItems.value = {}
  refundReason.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  selectedOrder.value = null
}

async function processRefund() {
  if (!canRefund.value || processing.value) return
  
  const items = selectedOrder.value.items
    .filter(item => refundItems.value[item.id])
    .map(item => ({
      order_item_id: item.id,
      quantity: item.quantity,
      reason: refundReason.value
    }))
  
  if (items.length === 0) {
    alert('반품할 상품을 선택하세요.')
    return
  }
  
  processing.value = true
  try {
    await api.post('/sales/refund', {
      order_id: selectedOrder.value.id,
      items
    })
    alert('반품이 처리되었습니다.')
    closeModal()
    fetchOrders()
  } catch (e) {
    alert('반품 처리에 실패했습니다.')
  } finally {
    processing.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
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

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
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

.panel {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.order-list {
  max-height: 600px;
  overflow-y: auto;
}

.order-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.order-info {
  flex: 1;
}

.order-number {
  font-weight: 500;
  font-size: 14px;
}

.user {
  color: #6b7280;
  font-size: 13px;
  margin-left: 8px;
}

.date {
  color: #9ca3af;
  font-size: 12px;
  margin-left: 8px;
}

.order-items {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.item-tag {
  font-size: 11px;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
  color: #6b7280;
}

.order-meta {
  text-align: right;
}

.amount {
  font-weight: 500;
  font-size: 14px;
  color: #3b82f6;
}

.status {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.status.delivered {
  background: #dcfce7;
  color: #166534;
}

.status.refunded {
  background: #fee2e2;
  color: #dc2626;
}

.empty {
  text-align: center;
  color: #9ca3af;
  padding: 32px;
  font-size: 14px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: white;
  border-radius: 8px;
  width: 480px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #6b7280;
}

.modal-body {
  padding: 16px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row label {
  width: 80px;
  color: #6b7280;
  font-size: 13px;
}

.refund-items {
  margin: 16px 0;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.refund-items > label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
  display: block;
}

.refund-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
}

.refund-item:last-child {
  border-bottom: none;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox input {
  width: 16px;
  height: 16px;
}

.item-amount {
  font-weight: 500;
  font-size: 13px;
}

.form-group {
  margin-bottom: 16px;
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

.refund-summary {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #eff6ff;
  border-radius: 6px;
  margin-top: 16px;
}

.refund-amount {
  font-weight: 600;
  font-size: 16px;
  color: #3b82f6;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}
</style>
