<template>
  <div class="cart">
    <div class="page-header">
      <h1>장바구니</h1>
      <div class="user-points">
        보유 포인트: <strong>{{ userPoints?.toLocaleString() }}P</strong>
      </div>
    </div>

    <div v-if="cartStore.items.length === 0" class="empty-state">
      <p>장바구니가 비어있습니다.</p>
      <router-link to="/user/shop" class="btn btn-primary">쇼핑하러 가기</router-link>
    </div>

    <div v-else class="cart-container">
      <div class="cart-items">
        <div class="select-all">
          <label>
            <input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
            전체 선택 ({{ selectedItems.length }}개)
          </label>
          <button class="btn btn-sm btn-outline" @click="removeSelected">선택 삭제</button>
        </div>

        <div v-for="item in cartStore.items" :key="item.id" class="cart-item">
          <input type="checkbox" v-model="selectedIds" :value="item.id" />
          <div class="item-image">
            <img v-if="item.product?.imageUrl" :src="item.product.imageUrl" />
            <span v-else>📷</span>
          </div>
          <div class="item-info">
            <div class="item-name">{{ item.product?.name }}</div>
            <div class="item-meta">
              <span v-if="item.size">사이즈: {{ item.size }}</span>
            </div>
            <div class="item-price">
              {{ (item.product?.salePrice || item.product?.price)?.toLocaleString() }}원
            </div>
          </div>
          <div class="item-quantity">
            <button @click="updateQuantity(item, item.quantity - 1)">-</button>
            <span>{{ item.quantity }}</span>
            <button @click="updateQuantity(item, item.quantity + 1)">+</button>
          </div>
          <div class="item-total">
            {{ ((item.product?.salePrice || item.product?.price) * item.quantity)?.toLocaleString() }}원
          </div>
          <button class="remove-btn" @click="removeItem(item.id)">×</button>
        </div>
      </div>

      <div class="cart-summary">
        <h3>주문 요약</h3>
        <div class="summary-row">
          <span>선택 상품</span>
          <span>{{ selectedItems.length }}개</span>
        </div>
        <div class="summary-row">
          <span>상품 금액</span>
          <span>{{ selectedAmount.toLocaleString() }}원</span>
        </div>
        <div class="summary-row">
          <span>포인트</span>
          <span>{{ selectedPoints.toLocaleString() }}P</span>
        </div>

        <div class="payment-method">
          <label>
            <input type="radio" v-model="paymentMethod" value="points" />
            포인트 결제
          </label>
          <label>
            <input type="radio" v-model="paymentMethod" value="cash" />
            현금 결제
          </label>
        </div>

        <div v-if="paymentMethod === 'points' && selectedPoints > userPoints" class="warning">
          포인트가 부족합니다. ({{ (selectedPoints - userPoints).toLocaleString() }}P 부족)
        </div>

        <div class="shipping-info">
          <h4>배송지 정보</h4>
          <div class="form-group">
            <label>수령인</label>
            <input v-model="shippingInfo.recipientName" type="text" />
          </div>
          <div class="form-group">
            <label>연락처</label>
            <input v-model="shippingInfo.recipientPhone" type="tel" />
          </div>
          <div class="form-group">
            <label>배송지 주소</label>
            <input v-model="shippingInfo.address" type="text" />
          </div>
          <div class="form-group">
            <label>배송 요청사항</label>
            <input v-model="shippingInfo.memo" type="text" placeholder="요청사항 입력" />
          </div>
        </div>

        <button
          class="btn btn-primary btn-block"
          @click="checkout"
          :disabled="selectedItems.length === 0 || (paymentMethod === 'points' && selectedPoints > userPoints) || ordering"
        >
          {{ ordering ? '주문 처리 중...' : '주문하기' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useCartStore } from '@/stores/cart'
import { useAuthStore } from '@/stores/auth'
import { useOrderStore } from '@/stores/order'
import { useRouter } from 'vue-router'

const cartStore = useCartStore()
const authStore = useAuthStore()
const orderStore = useOrderStore()
const router = useRouter()

const selectedIds = ref([])
const paymentMethod = ref('points')
const ordering = ref(false)

const shippingInfo = reactive({
  recipientName: '',
  recipientPhone: '',
  address: '',
  memo: ''
})

const userPoints = computed(() => authStore.user?.points || 0)

const selectAll = computed({
  get: () => selectedIds.value.length === cartStore.items.length,
  set: () => {}
})

const selectedItems = computed(() => {
  return cartStore.items.filter(item => selectedIds.value.includes(item.id))
})

const selectedAmount = computed(() => {
  return selectedItems.value.reduce((sum, item) => {
    const price = item.product?.salePrice || item.product?.price || 0
    return sum + (price * item.quantity)
  }, 0)
})

const selectedPoints = computed(() => {
  return selectedItems.value.reduce((sum, item) => {
    return sum + ((item.product?.pointPrice || 0) * item.quantity)
  }, 0)
})

onMounted(() => {
  cartStore.fetchCart()
  if (authStore.user) {
    shippingInfo.recipientName = authStore.user.name
    shippingInfo.recipientPhone = authStore.user.phone || ''
    shippingInfo.address = authStore.user.address || ''
  }
})

function toggleSelectAll() {
  if (selectAll.value) {
    selectedIds.value = cartStore.items.map(item => item.id)
  } else {
    selectedIds.value = []
  }
}

async function updateQuantity(item, newQuantity) {
  if (newQuantity < 1) {
    removeItem(item.id)
    return
  }
  await cartStore.updateCartItem(item.id, newQuantity)
}

async function removeItem(itemId) {
  await cartStore.removeFromCart(itemId)
  selectedIds.value = selectedIds.value.filter(id => id !== itemId)
}

async function removeSelected() {
  for (const id of selectedIds.value) {
    await cartStore.removeFromCart(id)
  }
  selectedIds.value = []
}

async function checkout() {
  if (selectedItems.value.length === 0) {
    alert('상품을 선택해주세요.')
    return
  }

  if (!shippingInfo.recipientName || !shippingInfo.recipientPhone || !shippingInfo.address) {
    alert('배송지 정보를 모두 입력해주세요.')
    return
  }

  ordering.value = true
  try {
    await orderStore.createOrder({
      items: selectedItems.value.map(item => ({
        productId: item.productId,
        quantity: item.quantity,
        size: item.size,
        price: item.product?.salePrice || item.product?.price
      })),
      paymentMethod: paymentMethod.value,
      shippingInfo: { ...shippingInfo }
    })
    
    for (const item of selectedItems.value) {
      await cartStore.removeFromCart(item.id)
    }
    
    alert('주문이 완료되었습니다.')
    router.push('/user/orders')
  } catch (error) {
    alert('주문에 실패했습니다.')
  } finally {
    ordering.value = false
  }
}
</script>

<style scoped>
.cart {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.user-points {
  color: #6b7280;
}

.user-points strong {
  color: #3b82f6;
  font-size: 18px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-state p {
  margin-bottom: 20px;
  color: #6b7280;
}

.cart-container {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

.cart-items {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.select-all {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 16px;
}

.select-all label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid #e5e7eb;
}

.cart-item:last-child {
  border-bottom: none;
}

.cart-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
}

.item-image {
  width: 80px;
  height: 80px;
  background: #f3f4f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
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
  font-size: 13px;
  color: #6b7280;
}

.item-price {
  font-size: 14px;
  color: #3b82f6;
  margin-top: 4px;
}

.item-quantity {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-quantity button {
  width: 28px;
  height: 28px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.item-quantity span {
  min-width: 30px;
  text-align: center;
}

.item-total {
  font-weight: 600;
  min-width: 100px;
  text-align: right;
}

.remove-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
}

.cart-summary {
  background: white;
  border-radius: 8px;
  padding: 24px;
  height: fit-content;
  position: sticky;
  top: 20px;
}

.cart-summary h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
}

.payment-method {
  display: flex;
  gap: 16px;
  margin: 20px 0;
  padding: 16px;
  background: #f9fafb;
  border-radius: 6px;
}

.payment-method label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.warning {
  background: #fef2f2;
  color: #dc2626;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 16px;
}

.shipping-info {
  margin-bottom: 20px;
}

.shipping-info h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
}

.btn-block {
  width: 100%;
  padding: 14px;
}
</style>
