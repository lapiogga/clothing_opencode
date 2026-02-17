<template>
  <div class="order-item">
    <div class="item-image">
      <img v-if="item.product?.imageUrl" :src="item.product.imageUrl" />
      <span v-else>📷</span>
    </div>
    <div class="item-info">
      <div class="item-name">{{ item.product?.name }}</div>
      <div class="item-meta">
        <span v-if="item.size">사이즈: {{ item.size }}</span>
        <span>수량: {{ item.quantity }}</span>
      </div>
      <div class="item-price">
        {{ (item.price * item.quantity)?.toLocaleString() }}원
      </div>
    </div>
    <div v-if="showStatus" class="item-status">
      <span :class="['status-badge', item.status]">
        {{ getStatusLabel(item.status) }}
      </span>
    </div>
    <div v-if="showActions" class="item-actions">
      <button
        v-if="canRefund"
        class="btn btn-sm btn-outline"
        @click="$emit('refund', item)"
      >
        반품신청
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  showStatus: {
    type: Boolean,
    default: false
  },
  showActions: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refund'])

const canRefund = computed(() => {
  return props.item.status === 'delivered'
})

function getStatusLabel(status) {
  const labels = {
    pending: '주문대기',
    confirmed: '주문확인',
    preparing: '상품준비중',
    shipped: '배송중',
    delivered: '배송완료',
    cancelled: '주문취소',
    refunded: '반품완료'
  }
  return labels[status] || status
}
</script>

<style scoped>
.order-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  margin-bottom: 12px;
}

.item-image {
  width: 80px;
  height: 80px;
  background: #f3f4f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.item-info {
  flex: 1;
}

.item-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.item-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.item-price {
  font-weight: 600;
}

.item-status {
  margin-left: 16px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
}

.status-badge.delivered { background: #d1fae5; color: #065f46; }
.status-badge.shipped { background: #dcfce7; color: #166534; }
.status-badge.cancelled { background: #fee2e2; color: #dc2626; }
.status-badge.refunded { background: #fce7f3; color: #9d174d; }

.item-actions {
  margin-left: 16px;
}
</style>
