<template>
  <div class="shop">
    <div class="shop-header">
      <div class="tabs">
        <button :class="['tab', { active: activeType === 'ready_made' }]" @click="activeType = 'ready_made'; selectedCategory = null">
          완제품
        </button>
        <button :class="['tab', { active: activeType === 'custom' }]" @click="activeType = 'custom'; selectedCategory = null">
          맞춤피복
        </button>
      </div>
      <div class="user-points">
        보유 포인트: <strong>{{ availablePoint?.toLocaleString() }}P</strong>
      </div>
    </div>

    <div class="sales-office-section" v-if="!selectedOffice">
      <div class="office-header">
        <h2>피복판매소 선택</h2>
        <p>구매하실 피복판매소를 선택해주세요.</p>
      </div>
      <div class="office-grid">
        <div
          v-for="office in salesOffices"
          :key="office.id"
          class="office-card"
          @click="selectOffice(office)"
        >
          <div class="office-name">{{ office.name }}</div>
          <div class="office-address">{{ office.address }}</div>
          <div class="office-phone">{{ office.phone }}</div>
        </div>
      </div>
    </div>

    <div v-else class="shop-content">
      <div class="selected-office">
        <span class="office-label">선택된 판매소:</span>
        <span class="office-name">{{ selectedOffice.name }}</span>
        <button class="btn-change" @click="changeOffice">변경</button>
      </div>

      <div class="filter-bar">
        <div class="categories">
          <button
            :class="['cat-btn', { active: selectedCategory === null }]"
            @click="selectedCategory = null"
          >
            전체
          </button>
          <button
            v-for="cat in filteredCategories"
            :key="cat.id"
            :class="['cat-btn', { active: selectedCategory === cat.id }]"
            @click="selectedCategory = cat.id"
          >
            {{ cat.name }}
          </button>
        </div>
        <div class="search">
          <input v-model="searchQuery" type="text" placeholder="상품 검색..." />
        </div>
      </div>

      <div v-if="loading" class="loading">상품을 불러오는 중...</div>

      <div v-else-if="filteredProducts.length === 0" class="empty-state">
        재고가 있는 상품이 없습니다.
      </div>

      <div v-else class="product-grid">
        <div
          v-for="product in filteredProducts"
          :key="`${product.item_id}-${product.spec_id}`"
          class="product-card"
          @click="viewProduct(product)"
        >
          <div class="product-image">
            <div v-if="!product.image_url" class="placeholder">📷</div>
            <img v-else :src="product.image_url" />
          </div>
          <div class="product-info">
            <div class="product-category">{{ product.category_name }}</div>
            <div class="product-name">
              {{ product.item_name }}
              <span class="product-spec" v-if="product.spec_size">[{{ product.spec_size }}]</span>
            </div>
          </div>
          <div class="product-right">
            <div class="product-price">{{ product.spec_price?.toLocaleString() }}P</div>
            <div class="product-stock" :class="{ 'low-stock': product.available_quantity <= 5 }">
              재고 {{ product.available_quantity }}
            </div>
          </div>
        </div>
      </div>

      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-items="totalItems"
        @page-change="handlePageChange"
      />
    </div>

    <div v-if="showDetail && selectedProduct" class="modal-overlay" @click.self="closeDetail">
      <div class="modal-content modal-large">
        <button class="close-btn" @click="closeDetail">&times;</button>
        
        <div class="product-detail">
          <div class="detail-image">
            <div v-if="!selectedProduct.image_url" class="placeholder">📷</div>
            <img v-else :src="selectedProduct.image_url" />
          </div>

          <div class="detail-info">
            <div class="category-tag">{{ selectedProduct.category_name }}</div>
            <h2>{{ selectedProduct.item_name }}</h2>
            <p class="spec-info" v-if="selectedProduct.spec_size">사이즈: {{ selectedProduct.spec_size }}</p>
            <p class="description">{{ selectedProduct.description || '설명 없음' }}</p>

            <div class="price-section">
              <div class="point-price">{{ selectedProduct.spec_price?.toLocaleString() }}P</div>
            </div>

            <div class="stock-info">
              <span class="stock-label">가용 재고:</span>
              <span class="stock-value">{{ selectedProduct.available_quantity }}개</span>
              <span class="stock-note">(예약: {{ selectedProduct.reserved_quantity }}개)</span>
            </div>

            <div class="options-section">
              <div class="option-group">
                <label>수량</label>
                <div class="quantity-selector">
                  <button @click="quantity = Math.max(1, quantity - 1)">-</button>
                  <span>{{ quantity }}</span>
                  <button @click="quantity = Math.min(selectedProduct.available_quantity, quantity + 1)">+</button>
                </div>
              </div>

              <div class="option-group">
                <label>배송 방법 <span class="required">*</span></label>
                <div class="delivery-options">
                  <label class="delivery-radio" :class="{ active: deliveryType === 'parcel' }">
                    <input type="radio" v-model="deliveryType" value="parcel" />
                    <span>택배 배송</span>
                  </label>
                  <label class="delivery-radio" :class="{ active: deliveryType === 'direct' }">
                    <input type="radio" v-model="deliveryType" value="direct" />
                    <span>직접 수령</span>
                  </label>
                </div>
              </div>

              <div v-if="deliveryType === 'parcel'" class="option-group">
                <label>받는 분 <span class="required">*</span></label>
                <input v-model="recipientName" type="text" placeholder="이름 입력" />
              </div>

              <div v-if="deliveryType === 'parcel'" class="option-group">
                <label>연락처 <span class="required">*</span></label>
                <input v-model="recipientPhone" type="tel" placeholder="010-0000-0000" />
              </div>

              <div v-if="deliveryType === 'parcel'" class="option-group">
                <label>배송 주소 <span class="required">*</span></label>
                <input v-model="shippingAddress" type="text" placeholder="주소 입력" />
              </div>

              <div v-if="deliveryType === 'direct'" class="option-group">
                <label>수령 장소 <span class="required">*</span></label>
                <select v-model="deliveryLocationId">
                  <option value="">선택하세요</option>
                  <option v-for="loc in deliveryLocations" :key="loc.id" :value="loc.id">
                    {{ loc.name }} ({{ loc.address }})
                  </option>
                </select>
              </div>
            </div>

            <div class="total-section">
              <span>합계:</span>
              <strong>{{ (selectedProduct.spec_price * quantity)?.toLocaleString() }}P</strong>
            </div>

            <div class="action-buttons">
              <button class="btn btn-primary btn-lg" @click="buyNow" :disabled="submitting">
                {{ submitting ? '처리 중...' : '바로 구매' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import api from '@/api'
import Pagination from '@/components/common/Pagination.vue'

const authStore = useAuthStore()
const router = useRouter()

const salesOffices = ref([])
const selectedOffice = ref(null)
const inventory = ref([])
const categories = ref([])
const loading = ref(false)
const submitting = ref(false)

const activeType = ref('ready_made')
const selectedCategory = ref(null)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = 12
const totalItems = ref(0)

const showDetail = ref(false)
const selectedProduct = ref(null)
const quantity = ref(1)
const deliveryType = ref('parcel')
const recipientName = ref('')
const recipientPhone = ref('')
const shippingAddress = ref('')
const deliveryLocationId = ref('')
const deliveryLocations = ref([])

const availablePoint = computed(() => {
  const user = authStore.user
  return (user?.current_point || 0) - (user?.reserved_point || 0)
})

const filteredCategories = computed(() => {
  return categories.value.filter(cat => {
    if (activeType.value === 'ready_made') {
      return cat.type !== 'custom'
    }
    return cat.type !== 'ready_made'
  })
})

const filteredProducts = computed(() => {
  let products = inventory.value.filter(p => {
    if (activeType.value === 'ready_made') {
      return p.clothing_type === 'ready_made'
    }
    return p.clothing_type === 'custom'
  })
  
  if (selectedCategory.value) {
    products = products.filter(p => p.category_id === selectedCategory.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    products = products.filter(p =>
      p.item_name?.toLowerCase().includes(query)
    )
  }
  
  return products
})

const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))

onMounted(async () => {
  await fetchSalesOffices()
  await fetchCategories()
})

async function fetchSalesOffices() {
  try {
    const response = await api.get('/sales-offices')
    salesOffices.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch sales offices:', error)
  }
}

async function fetchCategories() {
  try {
    const response = await api.get('/categories/tree')
    const flatList = []
    flattenCategories(response.data, flatList)
    categories.value = flatList
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

function flattenCategories(cats, result) {
  for (const cat of cats) {
    if (cat.level === 'large' || cat.level === 'medium') {
      result.push({
        id: cat.id,
        name: cat.name,
        level: cat.level,
        type: cat.name.includes('맞춤') ? 'custom' : 'ready_made'
      })
    }
    if (cat.children && cat.children.length > 0) {
      flattenCategories(cat.children, result)
    }
  }
}

async function selectOffice(office) {
  selectedOffice.value = office
  await fetchInventory()
  await fetchDeliveryLocations()
}

function changeOffice() {
  selectedOffice.value = null
  inventory.value = []
  deliveryLocations.value = []
}

async function fetchDeliveryLocations() {
  if (!selectedOffice.value) return
  try {
    const response = await api.get('/delivery-locations', {
      params: { sales_office_id: selectedOffice.value.id }
    })
    deliveryLocations.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch delivery locations:', error)
  }
}

async function fetchInventory() {
  if (!selectedOffice.value) return
  
  loading.value = true
  try {
    const response = await api.get('/inventory/available', {
      params: {
        sales_office_id: selectedOffice.value.id,
        page: currentPage.value,
        page_size: 100
      }
    })
    
    const items = response.data.items || []
    totalItems.value = response.data.total || 0
    
    inventory.value = items.filter(item => item.available_quantity > 0)
  } catch (error) {
    console.error('Failed to fetch inventory:', error)
    alert('재고 조회에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

watch([activeType, selectedCategory, searchQuery], () => {
  currentPage.value = 1
})

function handlePageChange(page) {
  currentPage.value = page
}

function viewProduct(product) {
  selectedProduct.value = product
  quantity.value = 1
  deliveryType.value = 'parcel'
  recipientName.value = ''
  recipientPhone.value = ''
  shippingAddress.value = ''
  deliveryLocationId.value = ''
  showDetail.value = true
}

function closeDetail() {
  showDetail.value = false
  selectedProduct.value = null
}

async function buyNow() {
  if (!selectedProduct.value) return
  
  const totalPoints = selectedProduct.value.spec_price * quantity.value
  
  if (totalPoints > availablePoint.value) {
    alert('포인트가 부족합니다.')
    return
  }
  
  if (quantity.value > selectedProduct.value.available_quantity) {
    alert('재고가 부족합니다.')
    return
  }
  
  if (deliveryType.value === 'parcel') {
    if (!recipientName.value.trim()) {
      alert('받는 분 이름을 입력해주세요.')
      return
    }
    if (!recipientPhone.value.trim()) {
      alert('연락처를 입력해주세요.')
      return
    }
    if (!shippingAddress.value.trim()) {
      alert('배송 주소를 입력해주세요.')
      return
    }
  } else if (deliveryType.value === 'direct') {
    if (!deliveryLocationId.value) {
      alert('수령 장소를 선택해주세요.')
      return
    }
  }
  
  submitting.value = true
  try {
    const orderData = {
      sales_office_id: selectedOffice.value.id,
      order_type: 'online',
      delivery_type: deliveryType.value,
      items: [{
        item_id: selectedProduct.value.item_id,
        spec_id: selectedProduct.value.spec_id,
        quantity: quantity.value,
        payment_method: 'point'
      }]
    }
    
    if (deliveryType.value === 'parcel') {
      orderData.recipient_name = recipientName.value
      orderData.recipient_phone = recipientPhone.value
      orderData.shipping_address = shippingAddress.value
    } else {
      orderData.delivery_location_id = parseInt(deliveryLocationId.value)
    }
    
    await api.post('/orders', orderData)
    
    alert('주문이 완료되었습니다.')
    closeDetail()
    await authStore.fetchUser()
    await fetchInventory()
    router.push('/user/orders')
  } catch (error) {
    alert(error.response?.data?.detail || '주문에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.shop {
  padding: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.shop-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tabs {
  display: flex;
  gap: 6px;
}

.tab {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #f3f4f6;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}

.tab.active {
  background: #3b82f6;
  color: white;
}

.user-points {
  font-size: 13px;
  color: #6b7280;
}

.user-points strong {
  color: #3b82f6;
  font-size: 14px;
}

.sales-office-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.office-header {
  text-align: center;
  margin-bottom: 16px;
}

.office-header h2 {
  font-size: 18px;
  margin-bottom: 4px;
}

.office-header p {
  color: #6b7280;
  font-size: 13px;
}

.office-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.office-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.office-card:hover {
  border-color: #3b82f6;
  background: #f8faff;
}

.office-card .office-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.office-card .office-address {
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 2px;
}

.office-card .office-phone {
  color: #9ca3af;
  font-size: 11px;
}

.shop-content {
  background: white;
  border-radius: 12px;
  padding: 16px;
}

.selected-office {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f7ff;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
}

.office-label {
  color: #6b7280;
}

.selected-office .office-name {
  font-weight: 500;
  color: #3b82f6;
}

.btn-change {
  margin-left: auto;
  padding: 2px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 12px;
}

.btn-change:hover {
  background: #f3f4f6;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.categories {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.cat-btn {
  padding: 5px 12px;
  border: 1px solid #d1d5db;
  border-radius: 16px;
  background: white;
  cursor: pointer;
  font-size: 12px;
}

.cat-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.search input {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 16px;
  width: 200px;
  font-size: 13px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

.product-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.product-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  background: white;
}

.product-card:hover {
  border-color: #3b82f6;
  background: #fafafa;
}

.product-image {
  width: 56px;
  height: 56px;
  min-width: 56px;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image .placeholder {
  font-size: 24px;
}

.product-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.product-info {
  flex: 1;
  min-width: 0;
}

.product-category {
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 2px;
}

.product-name {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.product-spec {
  font-size: 12px;
  color: #6b7280;
}

.product-price {
  font-weight: 600;
  color: #3b82f6;
  font-size: 15px;
}

.product-stock {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #f3f4f6;
  color: #6b7280;
}

.product-stock.low-stock {
  background: #fef2f2;
  color: #dc2626;
}

.product-right {
  text-align: right;
  padding-left: 12px;
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
  border-radius: 12px;
  position: relative;
  max-height: 85vh;
  overflow-y: auto;
}

.modal-large {
  width: 100%;
  max-width: 520px;
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: white;
  border: none;
  font-size: 22px;
  cursor: pointer;
  z-index: 1;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.product-detail {
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.detail-image {
  width: 100%;
  height: 180px;
  background: #f3f4f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.detail-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.detail-image .placeholder {
  font-size: 48px;
}

.detail-info {
  flex: 1;
}

.category-tag {
  display: inline-block;
  padding: 3px 10px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 20px;
  font-size: 11px;
  margin-bottom: 8px;
}

.detail-info h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
}

.spec-info {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 8px;
}

.detail-info .description {
  color: #6b7280;
  line-height: 1.5;
  font-size: 13px;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.price-section {
  margin-bottom: 12px;
}

.point-price {
  font-size: 22px;
  font-weight: 700;
  color: #3b82f6;
}

.stock-info {
  padding: 10px;
  background: #f9fafb;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
}

.stock-label {
  color: #6b7280;
}

.stock-value {
  font-weight: 500;
  margin: 0 4px;
}

.stock-note {
  color: #9ca3af;
  font-size: 11px;
}

.options-section {
  margin-bottom: 12px;
}

.option-group {
  margin-bottom: 10px;
}

.option-group label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
  color: #6b7280;
}

.quantity-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.quantity-selector button {
  width: 32px;
  height: 32px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 16px;
}

.quantity-selector span {
  font-size: 16px;
  font-weight: 500;
  min-width: 32px;
  text-align: center;
}

.delivery-options {
  display: flex;
  gap: 8px;
}

.delivery-radio {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
}

.delivery-radio input {
  display: none;
}

.delivery-radio span {
  font-weight: 500;
}

.delivery-radio.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.delivery-radio.active span {
  color: #3b82f6;
}

.option-group input[type="text"],
.option-group input[type="tel"],
.option-group select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
}

.option-group input:focus,
.option-group select:focus {
  outline: none;
  border-color: #3b82f6;
}

.total-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f0f7ff;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
}

.total-section strong {
  font-size: 18px;
  color: #3b82f6;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-lg {
  flex: 1;
  padding: 12px 16px;
  font-size: 14px;
}
</style>
