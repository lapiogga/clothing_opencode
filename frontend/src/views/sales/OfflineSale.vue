<template>
  <div class="page">
    <h1>오프라인 판매</h1>
    
    <div class="content-grid">
      <div class="panel product-panel">
        <div class="panel-header">
          <span>품목 선택</span>
          <input v-model="search" placeholder="품목명 검색..." class="search-input" />
        </div>
        <div class="product-list">
          <div
            v-for="item in filteredItems"
            :key="item.id"
            class="product-row"
            @click="addToCart(item)"
          >
            <div class="product-info">
              <span class="name">{{ item.name }}</span>
              <span class="code">{{ item.code }}</span>
            </div>
            <div class="product-meta">
              <span class="price">{{ item.points }}P</span>
              <span class="stock">재고: {{ item.available_qty }}</span>
            </div>
          </div>
          <div v-if="filteredItems.length === 0" class="empty">품목이 없습니다</div>
        </div>
      </div>
      
      <div class="panel cart-panel">
        <div class="panel-header">
          <span>장바구니 ({{ cart.length }})</span>
          <button class="btn-text" @click="cart = []">비우기</button>
        </div>
        
        <div class="cart-list">
          <div v-for="(item, idx) in cart" :key="idx" class="cart-row">
            <div class="cart-info">
              <span class="name">{{ item.name }}</span>
              <span class="spec" v-if="item.spec_size">{{ item.spec_size }}</span>
            </div>
            <div class="cart-qty">
              <button @click="item.qty = Math.max(1, item.qty - 1)">-</button>
              <span>{{ item.qty }}</span>
              <button @click="item.qty++">+</button>
            </div>
            <span class="cart-total">{{ item.points * item.qty }}P</span>
            <button class="btn-remove" @click="cart.splice(idx, 1)">×</button>
          </div>
          <div v-if="cart.length === 0" class="empty">장바구니가 비어있습니다</div>
        </div>
        
        <div class="customer-section">
          <label>구매자 군번</label>
          <div class="customer-input">
            <input v-model="serviceNumber" placeholder="군번 입력" @keyup.enter="fetchCustomer" />
            <button class="btn-sm" @click="fetchCustomer">조회</button>
          </div>
          <div v-if="customer" class="customer-info">
            <span>{{ customer.name }} ({{ customer.unit || '소속없음' }})</span>
            <span class="points">보유: {{ customer.current_point?.toLocaleString() }}P</span>
          </div>
        </div>
        
        <div class="summary">
          <div class="row">
            <span>총 포인트</span>
            <span class="total-points">{{ totalPoints.toLocaleString() }}P</span>
          </div>
        </div>
        
        <button
          class="btn-primary btn-block"
          :disabled="cart.length === 0 || !customer || loading"
          @click="processSale"
        >
          {{ loading ? '처리 중...' : '판매 완료' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const auth = useAuthStore()
const search = ref('')
const items = ref([])
const cart = ref([])
const serviceNumber = ref('')
const customer = ref(null)
const loading = ref(false)

const filteredItems = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter(i => 
    i.name.toLowerCase().includes(q) || 
    i.code?.toLowerCase().includes(q)
  )
})

const totalPoints = computed(() => {
  return cart.value.reduce((sum, i) => sum + i.points * i.qty, 0)
})

onMounted(() => {
  fetchInventory()
})

async function fetchInventory() {
  try {
    const res = await api.get('/inventory/available', {
      params: { sales_office_id: auth.user?.sales_office_id }
    })
    items.value = (res.data.items || res.data).map(i => ({
      id: i.item_id,
      name: i.item_name,
      code: i.item_code,
      points: i.points,
      available_qty: i.available_quantity,
      spec_id: i.spec_id,
      spec_size: i.spec_size,
    }))
  } catch (e) {
    console.error('Failed to fetch inventory:', e)
  }
}

async function fetchCustomer() {
  if (!serviceNumber.value) {
    customer.value = null
    return
  }
  try {
    const res = await api.get(`/users/by-service-number/${serviceNumber.value}`)
    customer.value = res.data
  } catch (e) {
    customer.value = null
    alert('사용자를 찾을 수 없습니다')
  }
}

function addToCart(item) {
  const existing = cart.value.find(c => c.id === item.id && c.spec_id === item.spec_id)
  if (existing) {
    if (existing.qty < item.available_qty) existing.qty++
  } else {
    cart.value.push({ ...item, qty: 1 })
  }
}

async function processSale() {
  if (cart.value.length === 0 || !customer.value) return
  
  if (customer.value.current_point < totalPoints.value) {
    alert('포인트가 부족합니다.')
    return
  }
  
  loading.value = true
  try {
    await api.post('/sales/offline', {
      user_id: customer.value.id,
      sales_office_id: auth.user?.sales_office_id,
      items: cart.value.map(i => ({
        item_id: i.id,
        spec_id: i.spec_id,
        quantity: i.qty,
        unit_price: i.points,
      }))
    })
    alert('판매가 완료되었습니다.')
    cart.value = []
    customer.value = null
    serviceNumber.value = ''
    fetchInventory()
  } catch (e) {
    alert('판매 처리에 실패했습니다.')
  } finally {
    loading.value = false
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
  grid-template-columns: 1fr 380px;
  gap: 16px;
}

.panel {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 500;
}

.search-input {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
}

.product-panel {
  min-height: 500px;
}

.product-list {
  max-height: 450px;
  overflow-y: auto;
}

.product-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
}

.product-row:hover {
  background: #f9fafb;
}

.product-info .name {
  font-weight: 500;
  font-size: 14px;
}

.product-info .code {
  font-size: 12px;
  color: #9ca3af;
  margin-left: 8px;
}

.product-meta {
  text-align: right;
}

.product-meta .price {
  color: #3b82f6;
  font-weight: 500;
  font-size: 14px;
}

.product-meta .stock {
  font-size: 12px;
  color: #6b7280;
  display: block;
}

.cart-panel {
  display: flex;
  flex-direction: column;
}

.cart-list {
  flex: 1;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px 0;
}

.cart-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.cart-info {
  flex: 1;
}

.cart-info .name {
  font-size: 13px;
  font-weight: 500;
}

.cart-info .spec {
  font-size: 11px;
  color: #6b7280;
  margin-left: 4px;
}

.cart-qty {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cart-qty button {
  width: 22px;
  height: 22px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.cart-qty span {
  min-width: 24px;
  text-align: center;
  font-size: 13px;
}

.cart-total {
  font-weight: 500;
  font-size: 13px;
  min-width: 60px;
  text-align: right;
}

.btn-remove {
  background: none;
  border: none;
  color: #dc2626;
  font-size: 16px;
  cursor: pointer;
}

.empty {
  text-align: center;
  color: #9ca3af;
  padding: 24px;
  font-size: 13px;
}

.customer-section {
  padding: 12px 16px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.customer-section label {
  font-size: 12px;
  color: #6b7280;
}

.customer-input {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.customer-input input {
  flex: 1;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
}

.customer-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 13px;
}

.customer-info .points {
  color: #16a34a;
  font-weight: 500;
}

.summary {
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
}

.summary .row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.total-points {
  font-weight: 600;
  font-size: 16px;
  color: #3b82f6;
}

.btn-block {
  margin: 12px 16px;
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

.btn-text {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 13px;
}

.btn-sm {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 13px;
}
</style>
