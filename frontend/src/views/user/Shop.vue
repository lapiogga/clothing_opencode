<template>
  <div class="shop">
    <div class="page-header">
      <h1>피복 쇼핑</h1>
      <div class="user-info">
        <span class="points">보유 포인트: <strong>{{ authStore.user?.current_point?.toLocaleString() }}P</strong></span>
      </div>
    </div>

    <!-- 판매소 선택 -->
    <div class="sales-office-select">
      <label>판매소 선택:</label>
      <select v-model="selectedSalesOfficeId" @change="fetchProducts">
        <option :value="null">판매소를 선택하세요</option>
        <option v-for="office in salesOffices" :key="office.id" :value="office.id">
          {{ office.name }}
        </option>
      </select>
    </div>

    <!-- 타입 필터 -->
    <div class="type-filter">
      <button :class="['filter-btn', { active: typeFilter === 'all' }]" @click="typeFilter = 'all'">전체</button>
      <button :class="['filter-btn', { active: typeFilter === 'ready_made' }]" @click="typeFilter = 'ready_made'">완제품</button>
      <button :class="['filter-btn', { active: typeFilter === 'custom' }]" @click="typeFilter = 'custom'">맞춤피복</button>
    </div>

    <div v-if="loading" class="loading">상품을 불러오는 중...</div>

    <div v-else-if="!selectedSalesOfficeId && typeFilter !== 'custom'" class="empty-state">
      <p>판매소를 선택하면 구매 가능한 상품이 표시됩니다.</p>
      <p class="hint">맞춤피복은 판매소 선택 없이도 조회 가능합니다.</p>
    </div>

    <div v-else class="product-grid">
      <div 
        v-for="product in filteredProducts" 
        :key="product.item_id" 
        class="product-card"
        @click="openProductModal(product)"
      >
        <div class="product-image">
          <img v-if="product.thumbnail_url || product.image_url" :src="product.thumbnail_url || product.image_url" />
          <span v-else class="no-image">📷</span>
        </div>
        <div class="product-info">
          <div class="product-type-badge" :class="product.clothing_type">
            {{ product.clothing_type === 'ready_made' ? '완제품' : '맞춤피복' }}
          </div>
          <div class="product-name">{{ product.item_name }}</div>
          <div class="product-category">{{ product.category_name }}</div>
          <div v-if="product.clothing_type === 'ready_made'" class="product-stock">
            재고: {{ product.total_stock }}개
          </div>
          <div v-else class="product-custom-hint">
            체척권 발행
          </div>
        </div>
      </div>

      <div v-if="filteredProducts.length === 0" class="no-products">
        표시할 상품이 없습니다.
      </div>
    </div>

    <!-- 완제품 주문 모달 -->
    <div v-if="showReadyMadeModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ selectedProduct?.item_name }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>규격 선택</label>
            <select v-model="orderForm.spec_id" @change="updateSpecInfo">
              <option :value="null">규격을 선택하세요</option>
              <option v-for="spec in availableSpecs" :key="spec.spec_id" :value="spec.spec_id">
                {{ spec.spec_size }} - {{ spec.spec_price?.toLocaleString() }}P (재고: {{ spec.available_quantity }}개)
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>수량</label>
            <div class="quantity-input">
              <button @click="orderForm.quantity = Math.max(1, orderForm.quantity - 1)">-</button>
              <input type="number" v-model.number="orderForm.quantity" min="1" :max="maxQuantity" />
              <button @click="orderForm.quantity = Math.min(maxQuantity, orderForm.quantity + 1)">+</button>
            </div>
            <span class="max-hint">최대 {{ maxQuantity }}개</span>
          </div>

          <div class="form-group">
            <label>배송 방법</label>
            <div class="delivery-options">
              <label class="radio-label">
                <input type="radio" v-model="orderForm.delivery_type" value="parcel" />
                택배 배송
              </label>
              <label class="radio-label">
                <input type="radio" v-model="orderForm.delivery_type" value="direct" />
                직접 배송
              </label>
            </div>
          </div>

          <!-- 택배 배송 -->
          <template v-if="orderForm.delivery_type === 'parcel'">
            <div class="form-group">
              <label>수령인</label>
              <input type="text" v-model="orderForm.recipient_name" />
            </div>
            <div class="form-group">
              <label>연락처</label>
              <input type="tel" v-model="orderForm.recipient_phone" />
            </div>
            <div class="form-group">
              <label>배송지 주소</label>
              <input type="text" v-model="orderForm.shipping_address" />
            </div>
          </template>

          <!-- 직접 배송 -->
          <template v-else-if="orderForm.delivery_type === 'direct'">
            <div v-if="deliveryLocations.length === 0" class="no-delivery-locations">
              <p>해당 판매소에 등록된 배송지가 없습니다.</p>
              <p class="hint">판매소 관리자에게 문의해주세요.</p>
            </div>
            <div v-else class="form-group">
              <label>배송지 선택</label>
              <select v-model="orderForm.delivery_location_id">
                <option :value="null">배송지를 선택하세요</option>
                <option v-for="loc in deliveryLocations" :key="loc.id" :value="loc.id">
                  {{ loc.name }} ({{ loc.address }})
                </option>
              </select>
            </div>
            <div v-if="selectedDeliveryLocation" class="delivery-location-info">
              <div class="info-item">
                <span class="label">주소:</span>
                <span>{{ selectedDeliveryLocation.address }}</span>
              </div>
              <div v-if="selectedDeliveryLocation.contact_person" class="info-item">
                <span class="label">담당자:</span>
                <span>{{ selectedDeliveryLocation.contact_person }}</span>
              </div>
              <div v-if="selectedDeliveryLocation.contact_phone" class="info-item">
                <span class="label">연락처:</span>
                <span>{{ selectedDeliveryLocation.contact_phone }}</span>
              </div>
            </div>
          </template>

          <div class="order-summary">
            <div class="summary-row">
              <span>상품 금액</span>
              <span>{{ (selectedSpecPrice * orderForm.quantity)?.toLocaleString() }}P</span>
            </div>
            <div class="summary-row total">
              <span>합계</span>
              <span>{{ orderTotal?.toLocaleString() }}P</span>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">취소</button>
          <button 
            class="btn btn-primary" 
            @click="submitOrder"
            :disabled="!canSubmitOrder || submitting"
          >
            {{ submitting ? '주문 처리 중...' : '주문하기' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 맞춤피복 체척권 발행 모달 -->
    <div v-if="showCustomModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content modal-small">
        <div class="modal-header">
          <h3>{{ selectedProduct?.item_name }} (맞춤피복)</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="custom-info">
            <p class="info-text">맞춤피복은 체척권 발행 후 체척업체에서 맞춤 제작합니다.</p>
            <p class="info-text">구매 즉시 체척권이 발행됩니다.</p>
          </div>

          <div class="form-group">
            <label>수량</label>
            <div class="quantity-input">
              <button @click="customForm.amount = Math.max(1, customForm.amount - 1)">-</button>
              <input type="number" v-model.number="customForm.amount" min="1" />
              <button @click="customForm.amount = customForm.amount + 1">+</button>
            </div>
          </div>

          <div class="voucher-preview">
            <span>체척권 발행 수량:</span>
            <strong>{{ customForm.amount }}장</strong>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">취소</button>
          <button 
            class="btn btn-primary" 
            @click="issueVoucher"
            :disabled="submitting"
          >
            {{ submitting ? '발행 중...' : '바로구매' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 체척권 발행 완료 모달 -->
    <div v-if="showVoucherResult" class="modal-overlay" @click.self="closeVoucherResult">
      <div class="modal-content modal-small">
        <div class="modal-header success">
          <h3>체척권 발행 완료</h3>
        </div>
        
        <div class="modal-body">
          <div class="voucher-result">
            <div class="voucher-icon">✓</div>
            <div class="voucher-number">
              <label>체척권 번호</label>
              <strong>{{ issuedVoucher?.voucher_number }}</strong>
            </div>
            <div class="voucher-info">
              <p>체척권이 발행되었습니다.</p>
              <p>체척업체에서 체척권 번호를 제시하여 맞춤 제작을 받으시기 바랍니다.</p>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-primary btn-block" @click="closeVoucherResult">확인</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// State
const loading = ref(false)
const submitting = ref(false)
const salesOffices = ref([])
const selectedSalesOfficeId = ref(null)
const typeFilter = ref('all')
const readyMadeProducts = ref([])
const customProducts = ref([])
const availableSpecs = ref([])
const deliveryLocations = ref([])

// Modal state
const showReadyMadeModal = ref(false)
const showCustomModal = ref(false)
const showVoucherResult = ref(false)
const selectedProduct = ref(null)

// Order form for ready-made
const orderForm = ref({
  spec_id: null,
  quantity: 1,
  delivery_type: 'parcel',
  recipient_name: '',
  recipient_phone: '',
  shipping_address: '',
  delivery_location_id: null,
})

// Custom clothing form
const customForm = ref({
  amount: 1,
})

// Issued voucher result
const issuedVoucher = ref(null)

// Computed
const filteredProducts = computed(() => {
  const allProducts = [...readyMadeProducts.value, ...customProducts.value]
  
  // Group by item_id
  const groupedMap = new Map()
  allProducts.forEach(item => {
    if (!groupedMap.has(item.item_id)) {
      groupedMap.set(item.item_id, {
        item_id: item.item_id,
        item_name: item.item_name,
        category_id: item.category_id,
        category_name: item.category_name,
        clothing_type: item.clothing_type,
        description: item.description,
        image_url: item.image_url,
        thumbnail_url: item.thumbnail_url,
        specs: [],
        total_stock: 0,
      })
    }
    const product = groupedMap.get(item.item_id)
    product.specs.push(item)
    if (item.clothing_type === 'ready_made') {
      product.total_stock += item.available_quantity || 0
    }
  })

  let products = Array.from(groupedMap.values())
  
  if (typeFilter.value !== 'all') {
    products = products.filter(p => p.clothing_type === typeFilter.value)
  }
  
  return products
})

const selectedSpecPrice = computed(() => {
  const spec = availableSpecs.value.find(s => s.spec_id === orderForm.value.spec_id)
  return spec?.spec_price || 0
})

const maxQuantity = computed(() => {
  const spec = availableSpecs.value.find(s => s.spec_id === orderForm.value.spec_id)
  return spec?.available_quantity || 1
})

const orderTotal = computed(() => {
  return selectedSpecPrice.value * orderForm.value.quantity
})

const selectedDeliveryLocation = computed(() => {
  if (!orderForm.value.delivery_location_id) return null
  return deliveryLocations.value.find(loc => loc.id === orderForm.value.delivery_location_id)
})

const canSubmitOrder = computed(() => {
  if (!orderForm.value.spec_id || orderForm.value.quantity < 1) return false
  if (orderForm.value.quantity > maxQuantity.value) return false
  if (orderTotal.value > (authStore.user?.current_point || 0)) return false
  if (orderForm.value.delivery_type === 'parcel') {
    if (!orderForm.value.recipient_name || !orderForm.value.recipient_phone || !orderForm.value.shipping_address) {
      return false
    }
  } else if (orderForm.value.delivery_type === 'direct') {
    if (!orderForm.value.delivery_location_id) return false
  }
  return true
})

// Methods
onMounted(async () => {
  await Promise.all([
    fetchSalesOffices(),
    fetchCustomProducts(),
  ])
  
  // Initialize form with user data
  if (authStore.user) {
    orderForm.value.recipient_name = authStore.user.name || ''
    orderForm.value.recipient_phone = authStore.user.phone || ''
    orderForm.value.shipping_address = authStore.user.address || ''
  }
})

async function fetchSalesOffices() {
  try {
    const res = await api.get('/sales-offices', { params: { is_active: true } })
    salesOffices.value = res.data
  } catch (error) {
    console.error('Failed to fetch sales offices:', error)
  }
}

async function fetchProducts() {
  if (!selectedSalesOfficeId.value) {
    readyMadeProducts.value = []
    return
  }
  
  loading.value = true
  try {
    const res = await api.get('/inventory/available', {
      params: {
        sales_office_id: selectedSalesOfficeId.value,
        page_size: 100,
      }
    })
    readyMadeProducts.value = res.data.items || []
  } catch (error) {
    console.error('Failed to fetch products:', error)
  } finally {
    loading.value = false
  }
}

async function fetchCustomProducts() {
  try {
    const res = await api.get('/clothings/custom/available')
    customProducts.value = res.data.items || []
  } catch (error) {
    console.error('Failed to fetch custom products:', error)
  }
}

async function fetchDeliveryLocations() {
  if (!selectedSalesOfficeId.value) {
    deliveryLocations.value = []
    return
  }
  try {
    const res = await api.get('/delivery-locations', {
      params: { sales_office_id: selectedSalesOfficeId.value }
    })
    deliveryLocations.value = res.data || []
  } catch (error) {
    console.error('Failed to fetch delivery locations:', error)
    deliveryLocations.value = []
  }
}

function openProductModal(product) {
  selectedProduct.value = product
  
  if (product.clothing_type === 'custom') {
    // 맞춤피복: 간단한 모달
    customForm.value.amount = 1
    showCustomModal.value = true
  } else {
    // 완제품: 규격 선택 모달
    availableSpecs.value = product.specs.filter(s => s.available_quantity > 0)
    orderForm.value.spec_id = null
    orderForm.value.quantity = 1
    orderForm.value.delivery_type = 'parcel'
    orderForm.value.delivery_location_id = null
    // 배송지 목록 가져오기
    fetchDeliveryLocations()
    showReadyMadeModal.value = true
  }
}

function closeModal() {
  showReadyMadeModal.value = false
  showCustomModal.value = false
  selectedProduct.value = null
}

function updateSpecInfo() {
  // Reset quantity when spec changes
  orderForm.value.quantity = 1
}

async function submitOrder() {
  if (!canSubmitOrder.value) return
  
  submitting.value = true
  try {
    const orderData = {
      sales_office_id: selectedSalesOfficeId.value,
      order_type: 'online',
      items: [{
        item_id: selectedProduct.value.item_id,
        spec_id: orderForm.value.spec_id,
        quantity: orderForm.value.quantity,
      }],
      delivery_type: orderForm.value.delivery_type,
      recipient_name: orderForm.value.delivery_type === 'parcel' ? orderForm.value.recipient_name : null,
      recipient_phone: orderForm.value.delivery_type === 'parcel' ? orderForm.value.recipient_phone : null,
      shipping_address: orderForm.value.delivery_type === 'parcel' ? orderForm.value.shipping_address : null,
      delivery_location_id: orderForm.value.delivery_type === 'direct' ? orderForm.value.delivery_location_id : null,
    }
    
    await api.post('/orders', orderData)
    alert('주문이 완료되었습니다.')
    closeModal()
    
    // Refresh user data for updated points
    await authStore.fetchUser()
    
    // Redirect to orders
    router.push('/user/orders')
  } catch (error) {
    alert(error.response?.data?.detail || '주문에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function issueVoucher() {
  submitting.value = true
  try {
    const res = await api.post('/tailor-vouchers/issue-direct', {
      user_id: authStore.user.id,
      item_id: selectedProduct.value.item_id,
      amount: customForm.value.amount,
      sales_office_id: selectedSalesOfficeId.value,
      notes: '맞춤피복 쇼핑에서 발행',
    })
    
    issuedVoucher.value = res.data
    closeModal()
    showVoucherResult.value = true
    
    // Refresh user data
    await authStore.fetchUser()
  } catch (error) {
    alert(error.response?.data?.detail || '체척권 발행에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

function closeVoucherResult() {
  showVoucherResult.value = false
  issuedVoucher.value = null
}
</script>

<style scoped>
.shop {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.user-info {
  color: #6b7280;
}

.user-info .points strong {
  color: #3b82f6;
  font-size: 18px;
}

.sales-office-select {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
}

.sales-office-select label {
  font-weight: 500;
  color: #374151;
}

.sales-office-select select {
  flex: 1;
  max-width: 300px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.type-filter {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.filter-btn {
  padding: 8px 20px;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.filter-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
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
  color: #6b7280;
  margin-bottom: 8px;
}

.empty-state .hint {
  font-size: 13px;
  color: #9ca3af;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
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
  height: 140px;
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
  font-size: 48px;
  color: #9ca3af;
}

.product-info {
  padding: 12px;
}

.product-type-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  margin-bottom: 6px;
}

.product-type-badge.ready_made {
  background: #dbeafe;
  color: #1e40af;
}

.product-type-badge.custom {
  background: #fef3c7;
  color: #92400e;
}

.product-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
  color: #1f2937;
}

.product-category {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.product-stock {
  font-size: 12px;
  color: #16a34a;
}

.product-custom-hint {
  font-size: 12px;
  color: #92400e;
}

.no-products {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

/* Modal styles */
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
  max-height: 90vh;
  overflow-y: auto;
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

.modal-header.success {
  background: #dcfce7;
  border-radius: 12px 12px 0 0;
}

.modal-header.success h3 {
  color: #166534;
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

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.quantity-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quantity-input input {
  width: 60px;
  text-align: center;
}

.quantity-input button {
  width: 32px;
  height: 32px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 16px;
}

.max-hint {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
  display: block;
}

.delivery-options {
  display: flex;
  gap: 16px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.no-delivery-locations {
  background: #fef3c7;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}

.no-delivery-locations p {
  color: #92400e;
  margin-bottom: 4px;
}

.no-delivery-locations .hint {
  font-size: 12px;
  color: #b45309;
}

.delivery-location-info {
  background: #f0fdf4;
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 8px;
}

.delivery-location-info .info-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 4px;
}

.delivery-location-info .info-item:last-child {
  margin-bottom: 0;
}

.delivery-location-info .label {
  color: #6b7280;
  min-width: 60px;
}

.order-summary {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  margin-top: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.summary-row.total {
  font-weight: 600;
  font-size: 16px;
  color: #3b82f6;
  margin-bottom: 0;
  padding-top: 8px;
  border-top: 1px dashed #d1d5db;
}

.custom-info {
  background: #fef3c7;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.info-text {
  font-size: 13px;
  color: #92400e;
  margin-bottom: 4px;
}

.voucher-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.voucher-preview strong {
  color: #3b82f6;
  font-size: 18px;
}

/* Voucher result */
.voucher-result {
  text-align: center;
  padding: 20px;
}

.voucher-icon {
  width: 60px;
  height: 60px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto 16px;
}

.voucher-number {
  margin-bottom: 16px;
}

.voucher-number label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.voucher-number strong {
  font-size: 20px;
  color: #1f2937;
}

.voucher-info {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.voucher-info p {
  margin-bottom: 4px;
}

/* Buttons */
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

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
}

.btn-block {
  width: 100%;
}
</style>
