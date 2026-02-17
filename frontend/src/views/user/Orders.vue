<template>
  <div class="orders">
    <div class="page-header">
      <h1>주문/배송 조회</h1>
    </div>

    <div class="status-tabs">
      <button :class="['tab', { active: activeStatus === 'all' }]" @click="activeStatus = 'all'">전체</button>
      <button :class="['tab', { active: activeStatus === 'confirmed' }]" @click="activeStatus = 'confirmed'">주문확인</button>
      <button :class="['tab', { active: activeStatus === 'shipped' }]" @click="activeStatus = 'shipped'">배송중</button>
      <button :class="['tab', { active: activeStatus === 'delivered' }]" @click="activeStatus = 'delivered'">완료</button>
      <button :class="['tab', { active: activeStatus === 'cancelled' }]" @click="activeStatus = 'cancelled'">취소</button>
    </div>

    <div v-if="loading" class="loading">조회 중...</div>

    <div v-else class="order-list">
      <div v-for="order in filteredOrders" :key="order.id" class="order-card" @click="toggleDetail(order)">
        <div class="order-main">
          <div class="order-left">
            <div class="order-meta">
              <span class="order-date">{{ formatDate(order.ordered_at) }}</span>
              <span :class="['status', order.status]">{{ getStatusLabel(order.status) }}</span>
              <span :class="['delivery-type', order.delivery?.delivery_type]">
                {{ order.delivery?.delivery_type === 'parcel' ? '택배' : '직접수령' }}
              </span>
            </div>
            <div class="order-items-preview">
              <template v-for="(item, idx) in order.items.slice(0, 2)" :key="item.id">
                <span>{{ item.item_name || `품목#${item.item_id}` }}</span>
                <span v-if="item.spec_size" class="size">[{{ item.spec_size }}]</span>
                <span v-if="idx < Math.min(order.items.length, 2) - 1">, </span>
              </template>
              <span v-if="order.items.length > 2"> 외 {{ order.items.length - 2 }}건</span>
            </div>
          </div>
          <div class="order-right">
            <div class="order-total">{{ order.total_amount?.toLocaleString() }}P</div>
            <div class="expand-icon">{{ expandedId === order.id ? '▲' : '▼' }}</div>
          </div>
        </div>

        <div v-if="expandedId === order.id" class="order-detail" @click.stop>
          <div class="detail-section">
            <div class="detail-title">주문 정보</div>
            <div class="detail-row">
              <span>주문번호</span>
              <span>{{ order.order_number }}</span>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-title">주문 상품</div>
            <div v-for="item in order.items" :key="item.id" class="item-row">
              <span class="item-name">{{ item.item_name || `품목#${item.item_id}` }}<span v-if="item.spec_size"> [{{ item.spec_size }}]</span></span>
              <span class="item-qty">×{{ item.quantity }}</span>
              <span class="item-price">{{ item.total_price?.toLocaleString() }}P</span>
            </div>
            <div class="item-total-row">
              <span>합계</span>
              <span>{{ order.total_amount?.toLocaleString() }}P</span>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-title">배송 정보</div>
            <template v-if="order.delivery?.delivery_type === 'parcel'">
              <div class="detail-row">
                <span>받는 분</span>
                <span>{{ order.delivery?.recipient_name }} / {{ order.delivery?.recipient_phone }}</span>
              </div>
              <div class="detail-row">
                <span>주소</span>
                <span>{{ order.delivery?.shipping_address }}</span>
              </div>
            </template>
            <template v-else>
              <div class="detail-row">
                <span>수령 장소</span>
                <span>{{ order.delivery?.delivery_location?.name }}</span>
              </div>
              <div class="detail-row">
                <span>주소</span>
                <span>{{ order.delivery?.delivery_location?.address }}</span>
              </div>
            </template>
            <div class="detail-row">
              <span>배송 상태</span>
              <span>{{ getDeliveryStatusLabel(order.delivery?.status) }}</span>
            </div>
            <div v-if="order.delivery?.tracking_number" class="detail-row">
              <span>송장번호</span>
              <span class="tracking">{{ order.delivery.tracking_number }}</span>
            </div>
          </div>

          <div class="detail-actions">
            <button v-if="canCancel(order)" class="btn-cancel" @click="cancelOrder(order)">주문 취소</button>
          </div>
        </div>
      </div>

      <div v-if="filteredOrders.length === 0" class="empty-state">
        주문 내역이 없습니다.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const orders = ref([])
const loading = ref(false)
const activeStatus = ref('all')
const expandedId = ref(null)

const statusLabels = {
  pending: '대기',
  confirmed: '확인',
  processing: '준비중',
  shipped: '배송중',
  delivered: '완료',
  cancelled: '취소',
  returned: '반품',
  refunded: '환불'
}

const deliveryStatusLabels = {
  preparing: '배송준비',
  in_transit: '배송중',
  delivered: '배송완료',
  failed: '배송실패'
}

const filteredOrders = computed(() => {
  if (activeStatus.value === 'all') return orders.value
  if (activeStatus.value === 'cancelled') {
    return orders.value.filter(o => ['cancelled', 'returned', 'refunded'].includes(o.status))
  }
  return orders.value.filter(o => o.status === activeStatus.value)
})

onMounted(() => {
  fetchOrders()
})

async function fetchOrders() {
  loading.value = true
  try {
    const response = await api.get('/orders')
    orders.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch orders:', error)
  } finally {
    loading.value = false
  }
}

function getStatusLabel(status) {
  return statusLabels[status] || status
}

function getDeliveryStatusLabel(status) {
  return deliveryStatusLabels[status] || status || '-'
}

function toggleDetail(order) {
  expandedId.value = expandedId.value === order.id ? null : order.id
}

function canCancel(order) {
  return ['pending', 'confirmed'].includes(order.status)
}

async function cancelOrder(order) {
  if (!confirm('주문을 취소하시겠습니까?')) return
  try {
    await api.post(`/orders/${order.id}/cancel`, { reason: '사용자 취소' })
    alert('주문이 취소되었습니다.')
    expandedId.value = null
    fetchOrders()
  } catch (error) {
    alert(error.response?.data?.detail || '취소에 실패했습니다.')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.orders {
  padding: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.status-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.tab {
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  background: #f3f4f6;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}

.tab.active {
  background: #3b82f6;
  color: white;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.order-card {
  background: white;
  border-radius: 10px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.order-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  cursor: pointer;
}

.order-left {
  flex: 1;
  min-width: 0;
}

.order-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.order-date {
  font-size: 12px;
  color: #6b7280;
}

.status {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.status.confirmed { background: #dbeafe; color: #1e40af; }
.status.processing { background: #e0e7ff; color: #4338ca; }
.status.shipped { background: #dcfce7; color: #166534; }
.status.delivered { background: #d1fae5; color: #065f46; }
.status.cancelled { background: #fee2e2; color: #dc2626; }
.status.pending { background: #fef3c7; color: #92400e; }

.delivery-type {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.delivery-type.parcel { background: #eff6ff; color: #2563eb; }
.delivery-type.direct { background: #f0fdf4; color: #16a34a; }

.order-items-preview {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.order-items-preview .size {
  color: #9ca3af;
  font-size: 12px;
}

.order-right {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 16px;
}

.order-total {
  font-size: 16px;
  font-weight: 600;
  color: #3b82f6;
}

.expand-icon {
  font-size: 12px;
  color: #9ca3af;
}

.order-detail {
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
  letter-spacing: 0.5px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 6px 0;
}

.detail-row span:first-child {
  color: #6b7280;
  min-width: 70px;
}

.item-row {
  display: flex;
  align-items: center;
  padding: 6px 0;
  font-size: 13px;
}

.item-name {
  flex: 1;
}

.item-name .size {
  color: #9ca3af;
}

.item-qty {
  color: #6b7280;
  margin: 0 12px;
}

.item-price {
  font-weight: 500;
}

.item-total-row {
  display: flex;
  justify-content: space-between;
  padding-top: 8px;
  margin-top: 8px;
  border-top: 1px dashed #e5e7eb;
  font-size: 13px;
  font-weight: 500;
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

.btn-cancel {
  padding: 8px 16px;
  border: 1px solid #dc2626;
  border-radius: 6px;
  background: white;
  color: #dc2626;
  font-size: 13px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #fef2f2;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
  background: white;
  border-radius: 10px;
}
</style>
