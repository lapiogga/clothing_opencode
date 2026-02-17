<template>
  <div class="order-list">
    <div class="page-header">
      <h1>주문 관리</h1>
    </div>

    <div class="filter-bar">
      <div class="filter-tabs">
        <button :class="['tab', { active: statusFilter === null }]" @click="statusFilter = null">전체</button>
        <button :class="['tab', { active: statusFilter === 'confirmed' }]" @click="statusFilter = 'confirmed'">주문확인</button>
        <button :class="['tab', { active: statusFilter === 'processing' }]" @click="statusFilter = 'processing'">준비중</button>
        <button :class="['tab', { active: statusFilter === 'shipped' }]" @click="statusFilter = 'shipped'">배송중</button>
        <button :class="['tab', { active: statusFilter === 'delivered' }]" @click="statusFilter = 'delivered'">완료</button>
      </div>
      <input v-model="keyword" type="text" placeholder="주문번호 검색" class="search-input" @keyup.enter="fetchOrders" />
    </div>

    <div v-if="loading" class="loading">조회 중...</div>

    <div v-else class="orders">
      <div v-for="order in orders" :key="order.id" class="order-card" @click="viewOrder(order)">
        <div class="order-main">
          <div class="order-left">
            <div class="order-meta">
              <span class="order-number">{{ order.order_number }}</span>
              <span :class="['status', order.status]">{{ getStatusLabel(order.status) }}</span>
              <span :class="['type', order.order_type]">{{ order.order_type === 'online' ? '온라인' : '방문' }}</span>
            </div>
            <div class="order-user">
              {{ order.user?.name }} ({{ order.user?.service_number }}) - {{ order.user?.rank }}
            </div>
            <div class="order-items">
              {{ getItemSummary(order) }}
            </div>
          </div>
          <div class="order-right">
            <div class="order-amount">{{ order.total_amount?.toLocaleString() }}P</div>
            <div class="order-date">{{ formatDate(order.ordered_at) }}</div>
          </div>
        </div>

        <div v-if="expandedId === order.id" class="order-detail" @click.stop>
          <div class="detail-section">
            <div class="detail-title">주문 상품</div>
            <div v-for="item in order.items" :key="item.id" class="item-row">
              <span>{{ item.item_name }}<span v-if="item.spec_size"> [{{ item.spec_size }}]</span></span>
              <span>×{{ item.quantity }}</span>
              <span>{{ item.total_price?.toLocaleString() }}P</span>
            </div>
          </div>

          <div class="detail-section" v-if="order.delivery">
            <div class="detail-title">배송 정보</div>
            <div class="detail-row">
              <span>배송 방법</span>
              <span>{{ order.delivery.delivery_type === 'parcel' ? '택배' : '직접수령' }}</span>
            </div>
            <template v-if="order.delivery.delivery_type === 'parcel'">
              <div class="detail-row">
                <span>수령인</span>
                <span>{{ order.delivery.recipient_name }} / {{ order.delivery.recipient_phone }}</span>
              </div>
              <div class="detail-row">
                <span>주소</span>
                <span>{{ order.delivery.shipping_address }}</span>
              </div>
            </template>
            <template v-else>
              <div class="detail-row">
                <span>수령 장소</span>
                <span>{{ order.delivery.delivery_location?.name }}</span>
              </div>
            </template>
            <div class="detail-row" v-if="order.delivery.tracking_number">
              <span>송장번호</span>
              <span class="tracking">{{ order.delivery.tracking_number }}</span>
            </div>
          </div>

          <div class="detail-actions">
            <template v-if="order.status === 'confirmed'">
              <button class="btn-primary" @click="updateStatus(order, 'processing')">상품 준비</button>
            </template>
            <template v-if="order.status === 'processing'">
              <button class="btn-primary" @click="startShipping(order)">배송 시작</button>
            </template>
            <template v-if="order.status === 'shipped'">
              <button class="btn-primary" @click="updateStatus(order, 'delivered')">배송 완료</button>
            </template>
          </div>
        </div>
      </div>

      <div v-if="orders.length === 0" class="empty">
        주문 내역이 없습니다.
      </div>
    </div>

    <div v-if="showTracking" class="modal-overlay" @click.self="closeTracking">
      <div class="modal-content">
        <div class="modal-header">
          <h2>송장번호 등록</h2>
          <button class="close-btn" @click="closeTracking">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>송장번호</label>
            <input v-model="trackingNumber" type="text" placeholder="송장번호 입력" />
          </div>
          <div class="form-actions">
            <button class="btn-outline" @click="closeTracking">취소</button>
            <button class="btn-primary" @click="submitTracking">등록</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/api'

const orders = ref([])
const loading = ref(false)
const statusFilter = ref(null)
const keyword = ref('')
const expandedId = ref(null)
const showTracking = ref(false)
const trackingNumber = ref('')
const selectedOrder = ref(null)

const statusLabels = {
  pending: '대기',
  confirmed: '확인',
  processing: '준비중',
  shipped: '배송중',
  delivered: '완료',
  cancelled: '취소',
}

onMounted(() => {
  fetchOrders()
})

watch(statusFilter, () => {
  fetchOrders()
})

async function fetchOrders() {
  loading.value = true
  try {
    const params = { page: 1, page_size: 50 }
    if (statusFilter.value) params.status = statusFilter.value
    if (keyword.value) params.keyword = keyword.value
    
    const response = await api.get('/sales/orders', { params })
    orders.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch orders:', error)
  } finally {
    loading.value = false
  }
}

function viewOrder(order) {
  expandedId.value = expandedId.value === order.id ? null : order.id
}

function getStatusLabel(status) {
  return statusLabels[status] || status
}

function getItemSummary(order) {
  if (!order.items?.length) return ''
  const first = order.items[0].item_name || '상품'
  if (order.items.length === 1) return `${first} ×${order.items[0].quantity}`
  return `${first} 외 ${order.items.length - 1}건`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function updateStatus(order, newStatus) {
  if (!confirm(`주문 상태를 '${getStatusLabel(newStatus)}'(으)로 변경하시겠습니까?`)) return
  
  try {
    await api.put(`/sales/orders/${order.id}/status`, { status: newStatus })
    alert('상태가 변경되었습니다.')
    fetchOrders()
  } catch (error) {
    alert(error.response?.data?.detail || '변경에 실패했습니다.')
  }
}

function startShipping(order) {
  if (order.delivery?.delivery_type === 'parcel') {
    selectedOrder.value = order
    trackingNumber.value = ''
    showTracking.value = true
  } else {
    updateStatus(order, 'shipped')
  }
}

async function submitTracking() {
  if (!trackingNumber.value.trim()) {
    alert('송장번호를 입력해주세요.')
    return
  }
  
  try {
    await api.put(`/sales/orders/${selectedOrder.value.id}/status`, {
      status: 'shipped',
      tracking_number: trackingNumber.value
    })
    alert('배송이 시작되었습니다.')
    closeTracking()
    fetchOrders()
  } catch (error) {
    alert(error.response?.data?.detail || '등록에 실패했습니다.')
  }
}

function closeTracking() {
  showTracking.value = false
  selectedOrder.value = null
  trackingNumber.value = ''
}
</script>

<style scoped>
.order-list {
  padding: 16px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 600;
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
  background: #3b82f6;
  color: white;
}

.search-input {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 16px;
  font-size: 13px;
  width: 180px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.orders {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.order-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.order-main {
  display: flex;
  justify-content: space-between;
  padding: 12px 14px;
  cursor: pointer;
}

.order-main:hover {
  background: #fafafa;
}

.order-left {
  flex: 1;
}

.order-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.order-number {
  font-weight: 500;
  font-size: 13px;
}

.status {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.status.confirmed { background: #dbeafe; color: #1e40af; }
.status.processing { background: #e0e7ff; color: #4338ca; }
.status.shipped { background: #fef3c7; color: #92400e; }
.status.delivered { background: #dcfce7; color: #166534; }

.type {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  background: #f3f4f6;
  color: #6b7280;
}

.type.offline { background: #fce7f3; color: #9d174d; }

.order-user {
  font-size: 13px;
  color: #374151;
  margin-bottom: 2px;
}

.order-items {
  font-size: 12px;
  color: #6b7280;
}

.order-right {
  text-align: right;
}

.order-amount {
  font-weight: 600;
  color: #3b82f6;
  font-size: 14px;
}

.order-date {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
}

.order-detail {
  border-top: 1px solid #f3f4f6;
  padding: 14px;
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

.item-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 4px 0;
}

.item-row span:first-child {
  flex: 1;
}

.item-row span:nth-child(2) {
  color: #6b7280;
  margin: 0 12px;
}

.detail-row {
  display: flex;
  font-size: 13px;
  padding: 4px 0;
}

.detail-row span:first-child {
  color: #6b7280;
  min-width: 80px;
}

.tracking {
  color: #3b82f6;
  font-weight: 500;
}

.detail-actions {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-primary {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-outline {
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
  background: white;
  border-radius: 8px;
}

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
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
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

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  margin-bottom: 6px;
  color: #6b7280;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
