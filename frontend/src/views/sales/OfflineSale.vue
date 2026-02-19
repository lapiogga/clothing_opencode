<template>
  <div class="offline-sale">
    <div class="page-header">
      <h1>오프라인 판매</h1>
    </div>

    <!-- 사용자 선택 섹션 -->
    <div class="user-section">
      <div class="user-search">
        <label>구매자 검색:</label>
        <div class="search-input-wrapper">
          <input 
            type="text" 
            v-model="userSearchQuery" 
            @input="searchUsers"
            @focus="showUserPopup = true"
            placeholder="이름 또는 군번 입력"
          />
          <button class="btn btn-sm btn-outline" @click="openUserPopup">조회</button>
        </div>
        
        <!-- 사용자 검색 결과 팝업 -->
        <div v-if="showUserPopup && userSearchResults.length > 0" class="user-popup">
          <div 
            v-for="user in userSearchResults" 
            :key="user.id" 
            class="user-item"
            @click="selectUser(user)"
          >
            <div class="user-info">
              <span class="user-name">{{ user.name }}</span>
              <span class="user-rank">{{ user.rank?.name }}</span>
              <span class="user-unit">{{ user.unit }}</span>
            </div>
            <div class="user-meta">
              <span class="user-service-number">{{ user.service_number }}</span>
              <span class="user-points">{{ user.current_point?.toLocaleString() }}P</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 선택된 사용자 정보 -->
      <div v-if="selectedUser" class="selected-user">
        <div class="user-card">
          <div class="user-avatar">{{ selectedUser.name?.charAt(0) }}</div>
          <div class="user-details">
            <div class="user-name">{{ selectedUser.name }} ({{ selectedUser.rank?.name }})</div>
            <div class="user-meta">
              <span>{{ selectedUser.service_number }}</span>
              <span>{{ selectedUser.unit }}</span>
            </div>
            <div class="user-points">보유 포인트: <strong>{{ selectedUser.current_point?.toLocaleString() }}P</strong></div>
          </div>
          <button class="btn btn-sm btn-outline" @click="clearUser">변경</button>
        </div>
      </div>
    </div>

    <!-- 상품 그리드 -->
    <div class="products-section">
      <div class="section-header">
        <h3>판매 가능 품목</h3>
        <div class="filter-bar">
          <input 
            type="text" 
            v-model="productSearchQuery" 
            placeholder="품목명 검색"
            class="search-input"
          />
        </div>
      </div>

      <div v-if="loading" class="loading">상품을 불러오는 중...</div>

      <div v-else class="product-grid">
        <div 
          v-for="product in filteredProducts" 
          :key="product.inventory_id" 
          class="product-card"
          @click="addToCart(product)"
        >
          <div class="product-image">
            <img v-if="product.thumbnail_url || product.image_url" :src="product.thumbnail_url || product.image_url" />
            <span v-else class="no-image">📷</span>
          </div>
          <div class="product-info">
            <div class="product-name">{{ product.item_name }}</div>
            <div class="product-category">{{ product.category_name }}</div>
            <div class="product-spec" v-if="product.spec_size">[{{ product.spec_size }}]</div>
            <div class="product-price">{{ product.spec_price?.toLocaleString() }}P</div>
            <div class="product-stock">재고: {{ product.available_quantity }}개</div>
          </div>
        </div>

        <div v-if="filteredProducts.length === 0" class="no-products">
          표시할 상품이 없습니다.
        </div>
      </div>
    </div>

    <!-- 장바구니 패널 -->
    <div class="cart-section">
      <div class="cart-header">
        <h3>판매 목록</h3>
        <span class="cart-count">{{ cartItems.length }}개</span>
      </div>

      <div v-if="cartItems.length === 0" class="cart-empty">
        상품을 선택하세요
      </div>

      <div v-else class="cart-items">
        <div v-for="(item, index) in cartItems" :key="index" class="cart-item">
          <div class="item-info">
            <div class="item-name">{{ item.item_name }}</div>
            <div class="item-spec" v-if="item.spec_size">[{{ item.spec_size }}]</div>
          </div>
          <div class="item-quantity">
            <button @click="decreaseQuantity(index)">-</button>
            <span>{{ item.quantity }}</span>
            <button @click="increaseQuantity(index)">+</button>
          </div>
          <div class="item-price">{{ (item.spec_price * item.quantity)?.toLocaleString() }}P</div>
          <button class="item-remove" @click="removeFromCart(index)">×</button>
        </div>
      </div>

      <div class="cart-summary">
        <div class="summary-row">
          <span>총 상품 수</span>
          <span>{{ totalQuantity }}개</span>
        </div>
        <div class="summary-row total">
          <span>합계</span>
          <span>{{ totalPoints?.toLocaleString() }}P</span>
        </div>
      </div>

      <button 
        class="btn btn-primary btn-block checkout-btn"
        @click="checkout"
        :disabled="!canCheckout || submitting"
      >
        {{ submitting ? '처리 중...' : '판매 완료' }}
      </button>

      <div v-if="!selectedUser" class="warning">
        구매자를 선택하세요
      </div>
      <div v-else-if="totalPoints > selectedUser.current_point" class="warning">
        포인트 부족 ({{ (totalPoints - selectedUser.current_point)?.toLocaleString() }}P 부족)
      </div>
    </div>

    <!-- 수량 선택 모달 -->
    <div v-if="showQuantityModal" class="modal-overlay" @click.self="closeQuantityModal">
      <div class="modal-content modal-small">
        <div class="modal-header">
          <h3>{{ selectedProduct?.item_name }}</h3>
          <button class="close-btn" @click="closeQuantityModal">×</button>
        </div>
        
        <div class="modal-body">
          <div v-if="selectedProduct?.spec_size" class="spec-info">
            규격: {{ selectedProduct.spec_size }}
          </div>
          <div class="price-info">
            단가: {{ selectedProduct?.spec_price?.toLocaleString() }}P
          </div>
          
          <div class="form-group">
            <label>수량</label>
            <div class="quantity-input">
              <button @click="modalQuantity = Math.max(1, modalQuantity - 1)">-</button>
              <input type="number" v-model.number="modalQuantity" min="1" :max="selectedProduct?.available_quantity" />
              <button @click="modalQuantity = Math.min(selectedProduct?.available_quantity || 1, modalQuantity + 1)">+</button>
            </div>
            <span class="max-hint">최대 {{ selectedProduct?.available_quantity }}개</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeQuantityModal">취소</button>
          <button class="btn btn-primary" @click="confirmAddToCart">추가</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// State
const loading = ref(false)
const submitting = ref(false)
const products = ref([])
const cartItems = ref([])
const userSearchQuery = ref('')
const userSearchResults = ref([])
const selectedUser = ref(null)
const showUserPopup = ref(false)
const productSearchQuery = ref('')

// Quantity modal
const showQuantityModal = ref(false)
const selectedProduct = ref(null)
const modalQuantity = ref(1)

// Computed
const filteredProducts = computed(() => {
  if (!productSearchQuery.value) return products.value
  const query = productSearchQuery.value.toLowerCase()
  return products.value.filter(p => 
    p.item_name?.toLowerCase().includes(query) ||
    p.category_name?.toLowerCase().includes(query)
  )
})

const totalQuantity = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
})

const totalPoints = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + (item.spec_price * item.quantity), 0)
})

const canCheckout = computed(() => {
  if (!selectedUser.value) return false
  if (cartItems.value.length === 0) return false
  if (totalPoints.value > selectedUser.value.current_point) return false
  return true
})

// Methods
onMounted(async () => {
  await fetchProducts()
})

async function fetchProducts() {
  const salesOfficeId = authStore.user?.sales_office_id
  if (!salesOfficeId) {
    alert('판매소 정보가 없습니다.')
    return
  }
  
  loading.value = true
  try {
    const res = await api.get('/inventory/available', {
      params: {
        sales_office_id: salesOfficeId,
        page_size: 100,
      }
    })
    // Filter only ready_made products (custom products don't have inventory)
    products.value = (res.data.items || []).filter(item => item.clothing_type === 'ready_made')
  } catch (error) {
    console.error('Failed to fetch products:', error)
    alert('상품을 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}

let searchTimeout = null
async function searchUsers() {
  if (searchTimeout) clearTimeout(searchTimeout)
  
  if (!userSearchQuery.value.trim()) {
    userSearchResults.value = []
    return
  }
  
  searchTimeout = setTimeout(async () => {
    try {
      const res = await api.get('/users/search', {
        params: {
          keyword: userSearchQuery.value,
          page_size: 10,
        }
      })
      userSearchResults.value = res.data.items || []
      showUserPopup.value = true
    } catch (error) {
      console.error('Failed to search users:', error)
      userSearchResults.value = []
    }
  }, 300)
}

function openUserPopup() {
  if (userSearchQuery.value.trim()) {
    searchUsers()
  }
}

function selectUser(user) {
  selectedUser.value = user
  showUserPopup.value = false
  userSearchQuery.value = ''
  userSearchResults.value = []
}

function clearUser() {
  selectedUser.value = null
}

function addToCart(product) {
  selectedProduct.value = product
  modalQuantity.value = 1
  showQuantityModal.value = true
}

function closeQuantityModal() {
  showQuantityModal.value = false
  selectedProduct.value = null
}

function confirmAddToCart() {
  if (!selectedProduct.value || modalQuantity.value < 1) return
  
  const existingIndex = cartItems.value.findIndex(
    item => item.inventory_id === selectedProduct.value.inventory_id
  )
  
  if (existingIndex >= 0) {
    cartItems.value[existingIndex].quantity += modalQuantity.value
  } else {
    cartItems.value.push({
      ...selectedProduct.value,
      quantity: modalQuantity.value,
    })
  }
  
  closeQuantityModal()
}

function increaseQuantity(index) {
  const item = cartItems.value[index]
  if (item.quantity < item.available_quantity) {
    item.quantity++
  }
}

function decreaseQuantity(index) {
  const item = cartItems.value[index]
  if (item.quantity > 1) {
    item.quantity--
  } else {
    removeFromCart(index)
  }
}

function removeFromCart(index) {
  cartItems.value.splice(index, 1)
}

async function checkout() {
  if (!canCheckout.value) return
  
  if (!confirm(`${selectedUser.value.name}님에게 ${totalPoints.value?.toLocaleString()}P 판매하시겠습니까?`)) {
    return
  }
  
  submitting.value = true
  try {
    const salesOfficeId = authStore.user?.sales_office_id
    
    const payload = {
      user_id: selectedUser.value.id,
      sales_office_id: salesOfficeId,
      items: cartItems.value.map(item => ({
        item_id: item.item_id,
        spec_id: item.spec_id,
        quantity: item.quantity,
        unit_price: item.spec_price,
        payment_method: 'point',
      })),
    }
    
    const res = await api.post('/sales/offline', payload)
    
    alert(`판매가 완료되었습니다.\n주문번호: ${res.data.order_id}`)
    
    // Reset
    cartItems.value = []
    selectedUser.value = null
    
    // Refresh products
    await fetchProducts()
  } catch (error) {
    alert(error.response?.data?.detail || '판매 처리에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.offline-sale {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

/* 사용자 선택 섹션 */
.user-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.user-search {
  position: relative;
}

.user-search label {
  display: block;
  font-weight: 500;
  margin-bottom: 8px;
  color: #374151;
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
}

.search-input-wrapper input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.user-popup {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 300px;
  overflow-y: auto;
  z-index: 100;
  margin-top: 4px;
}

.user-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
}

.user-item:hover {
  background: #f9fafb;
}

.user-item:last-child {
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.user-name {
  font-weight: 500;
}

.user-rank {
  font-size: 12px;
  color: #6b7280;
}

.user-unit {
  font-size: 12px;
  color: #9ca3af;
}

.user-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}

.user-points {
  color: #3b82f6;
  font-weight: 500;
}

.selected-user {
  margin-top: 16px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bae6fd;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.user-details {
  flex: 1;
}

.user-details .user-name {
  font-weight: 600;
  margin-bottom: 2px;
}

.user-details .user-meta {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.user-details .user-points {
  font-size: 13px;
}

/* 상품 섹션 */
.products-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.filter-bar {
  display: flex;
  gap: 8px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  width: 200px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.product-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #e5e7eb;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.product-image {
  height: 100px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.no-image {
  font-size: 36px;
  color: #9ca3af;
}

.product-info {
  padding: 10px;
}

.product-name {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 2px;
  color: #1f2937;
}

.product-category {
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 2px;
}

.product-spec {
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 2px;
}

.product-price {
  font-size: 13px;
  color: #3b82f6;
  font-weight: 500;
  margin-bottom: 2px;
}

.product-stock {
  font-size: 11px;
  color: #16a34a;
}

.no-products {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  color: #6b7280;
  background: white;
  border-radius: 8px;
}

/* 장바구니 섹션 */
.cart-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  position: sticky;
  bottom: 0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}

.cart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.cart-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.cart-count {
  background: #3b82f6;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.cart-empty {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
}

.cart-items {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.cart-item:last-child {
  border-bottom: none;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-info .item-name {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-info .item-spec {
  font-size: 11px;
  color: #6b7280;
}

.item-quantity {
  display: flex;
  align-items: center;
  gap: 4px;
}

.item-quantity button {
  width: 24px;
  height: 24px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.item-quantity span {
  min-width: 24px;
  text-align: center;
  font-size: 13px;
}

.item-price {
  font-size: 13px;
  font-weight: 500;
  min-width: 60px;
  text-align: right;
}

.item-remove {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  line-height: 1;
}

.item-remove:hover {
  color: #dc2626;
}

.cart-summary {
  background: #f9fafb;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}

.summary-row.total {
  font-weight: 600;
  font-size: 15px;
  color: #3b82f6;
  margin-bottom: 0;
  padding-top: 8px;
  border-top: 1px dashed #d1d5db;
}

.checkout-btn {
  padding: 12px;
  font-size: 15px;
}

.warning {
  background: #fef2f2;
  color: #dc2626;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  margin-top: 8px;
  text-align: center;
}

/* 모달 */
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
  max-width: 400px;
}

.modal-small {
  max-width: 320px;
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
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
}

.modal-body {
  padding: 16px;
}

.spec-info, .price-info {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.price-info {
  color: #3b82f6;
  font-weight: 500;
}

.form-group {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 6px;
}

.quantity-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quantity-input input {
  width: 60px;
  text-align: center;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
}

.quantity-input button {
  width: 32px;
  height: 32px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.max-hint {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  display: block;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

/* 버튼 */
.btn {
  padding: 8px 16px;
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

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline {
  background: white;
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-block {
  width: 100%;
}
</style>
