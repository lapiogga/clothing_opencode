<template>
  <div class="clothing-list">
    <div class="page-header">
      <h1>품목 관리</h1>
      <button class="btn btn-primary" @click="openForm()">
        + 품목 등록
      </button>
    </div>

    <SearchFilter
      :search-placeholder="'품목명 검색'"
      :filters="searchFilters"
      @search="handleSearch"
      @filter-change="handleFilterChange"
    />

    <Table
      :columns="columns"
      :data="items"
      :loading="loading"
    >
      <template #row="{ item }">
        <td>
          <div class="product-info">
            <div class="product-image-placeholder" v-if="!item.image_url">📷</div>
            <img v-else :src="item.image_url" class="product-image" />
            <div>
              <div class="product-name">{{ item.name }}</div>
              <div class="product-desc">{{ item.description || '-' }}</div>
            </div>
          </div>
        </td>
        <td>{{ item.category?.name || '-' }}</td>
        <td>
          <span :class="['type-badge', item.clothing_type]">
            {{ item.clothing_type === 'ready_made' ? '완제품' : '맞춤피복' }}
          </span>
        </td>
        <td>{{ item.min_price ? item.min_price.toLocaleString() + 'P' : '-' }}</td>
        <td>{{ item.total_stock?.toLocaleString() || '0' }}</td>
        <td>
          <span :class="['status-badge', item.is_active ? 'active' : 'inactive']">
            {{ item.is_active ? '판매중' : '판매중지' }}
          </span>
        </td>
        <td class="actions">
          <button class="btn btn-sm btn-outline" @click="viewSpecs(item)">규격관리</button>
          <button class="btn btn-sm btn-outline" @click="openForm(item)">수정</button>
          <button class="btn btn-sm btn-danger" @click="deleteProduct(item)">삭제</button>
        </td>
      </template>
    </Table>

    <Pagination
      :current-page="pagination.page"
      :total-pages="totalPages"
      :total-items="pagination.total"
      @page-change="handlePageChange"
    />

    <!-- 품목 등록/수정 모달 -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ editProduct ? '품목 수정' : '품목 등록' }}</h2>
          <button class="close-btn" @click="closeForm">&times;</button>
        </div>

        <form @submit.prevent="handleSubmit" class="product-form">
          <div class="form-group">
            <label>품목명 <span class="required">*</span></label>
            <input v-model="form.name" type="text" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>카테고리 <span class="required">*</span></label>
              <select v-model="form.category_id" required>
                <option value="">선택하세요</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                  {{ cat.full_name || cat.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>피복 타입 <span class="required">*</span></label>
              <select v-model="form.clothing_type" required>
                <option value="ready_made">완제품</option>
                <option value="custom">맞춤피복</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>설명</label>
            <textarea v-model="form.description" rows="3"></textarea>
          </div>

          <div class="form-group">
            <label>이미지 URL</label>
            <input v-model="form.image_url" type="url" placeholder="원본 이미지 URL" />
            <div v-if="form.image_url" class="image-preview">
              <img :src="form.image_url" alt="이미지 미리보기" />
            </div>
          </div>

          <div class="form-group">
            <label>썸네일 URL</label>
            <input v-model="form.thumbnail_url" type="url" placeholder="썸네일 이미지 URL (목록용)" />
            <div v-if="form.thumbnail_url" class="image-preview thumbnail">
              <img :src="form.thumbnail_url" alt="썸네일 미리보기" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>상태</label>
              <select v-model="form.is_active">
                <option :value="true">판매중</option>
                <option :value="false">판매중지</option>
              </select>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeForm">취소</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? '저장 중...' : '저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 규격 관리 모달 -->
    <div v-if="showSpecs" class="modal-overlay" @click.self="closeSpecs">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h2>규격 관리 - {{ selectedProduct?.name }}</h2>
          <button class="close-btn" @click="closeSpecs">&times;</button>
        </div>

        <div class="specs-content">
          <div class="specs-header">
            <h3>규격 목록</h3>
            <!-- 맞춤피복은 규격추가 버튼 숨김 -->
            <button v-if="selectedProduct?.clothing_type !== 'custom'" class="btn btn-sm btn-primary" @click="openSpecForm()">+ 규격 추가</button>
          </div>
          
          <!-- 맞춤피복 안내 문구 -->
          <div v-if="selectedProduct?.clothing_type === 'custom'" class="custom-notice">
            <span class="notice-icon">📐</span>
            맞춤피복은 기본 규격 "맞춤"이 자동으로 생성됩니다. 가격만 수정 가능합니다.
          </div>

          <table class="specs-table">
            <thead>
              <tr>
                <th>규격코드</th>
                <th>사이즈</th>
                <th>가격(P)</th>
                <th>상태</th>
                <th>관리</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="spec in specs" :key="spec.id">
                <td>{{ spec.spec_code }}</td>
                <td>{{ spec.size }}</td>
                <td>{{ spec.price?.toLocaleString() }}P</td>
                <td>
                  <span :class="['status-badge', spec.is_active ? 'active' : 'inactive']">
                    {{ spec.is_active ? '활성' : '비활성' }}
                  </span>
                </td>
                <td class="actions">
                  <button class="btn btn-sm btn-outline" @click="openSpecForm(spec)">수정</button>
                  <!-- 맞춤피복은 삭제 버튼 숨김 -->
                  <button v-if="selectedProduct?.clothing_type !== 'custom'" class="btn btn-sm btn-danger" @click="deleteSpec(spec)">삭제</button>
                </td>
              </tr>
              <tr v-if="specs.length === 0">
                <td colspan="5" class="empty">등록된 규격이 없습니다</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 규격 등록/수정 모달 -->
    <div v-if="showSpecForm" class="modal-overlay" @click.self="closeSpecForm">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ editSpec ? '규격 수정' : '규격 추가' }}</h2>
          <button class="close-btn" @click="closeSpecForm">&times;</button>
        </div>

        <form @submit.prevent="handleSpecSubmit" class="spec-form">
          <div class="form-row">
            <div class="form-group">
              <label>규격코드 <span class="required">*</span></label>
              <input v-model="specForm.spec_code" type="text" required placeholder="예: SPEC001" />
            </div>
            <div class="form-group">
              <label>사이즈 <span class="required">*</span></label>
              <input v-model="specForm.size" type="text" required placeholder="예: 95, 100, 105" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>가격(P) <span class="required">*</span></label>
              <input v-model.number="specForm.price" type="number" min="0" required />
            </div>
            <div class="form-group">
              <label>상태</label>
              <select v-model="specForm.is_active">
                <option :value="true">활성</option>
                <option :value="false">비활성</option>
              </select>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeSpecForm">취소</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? '저장 중...' : '저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/api'
import SearchFilter from '@/components/common/SearchFilter.vue'
import Table from '@/components/common/Table.vue'
import Pagination from '@/components/common/Pagination.vue'

const items = ref([])
const categories = ref([])
const specs = ref([])
const loading = ref(false)
const submitting = ref(false)
const pagination = ref({ page: 1, pageSize: 20, total: 0 })
const searchQuery = ref('')
const categoryFilter = ref(null)
const typeFilter = ref(null)

const showForm = ref(false)
const showSpecs = ref(false)
const showSpecForm = ref(false)
const editProduct = ref(null)
const editSpec = ref(null)
const selectedProduct = ref(null)

const form = reactive({
  name: '',
  category_id: '',
  clothing_type: 'ready_made',
  description: '',
  image_url: '',
  is_active: true,
})

const specForm = reactive({
  spec_code: '',
  size: '',
  price: 0,
  is_active: true,
})

const columns = [
  { key: 'product', label: '품목정보' },
  { key: 'category', label: '카테고리' },
  { key: 'clothing_type', label: '타입' },
  { key: 'price', label: '가격' },
  { key: 'stock', label: '총재고' },
  { key: 'status', label: '상태' },
  { key: 'actions', label: '관리' }
]

const searchFilters = computed(() => [
  {
    key: 'category_id',
    label: '카테고리',
    options: [
      { value: null, label: '전체' },
      ...categories.value.map(c => ({ value: c.id, label: c.full_name || c.name }))
    ]
  },
  {
    key: 'clothing_type',
    label: '타입',
    options: [
      { value: null, label: '전체' },
      { value: 'ready_made', label: '완제품' },
      { value: 'custom', label: '맞춤피복' }
    ]
  }
])

const totalPages = computed(() => {
  return Math.ceil(pagination.value.total / pagination.value.pageSize)
})

onMounted(() => {
  fetchCategories()
  fetchProducts()
})

async function fetchCategories() {
  try {
    const response = await api.get('/categories/tree')
    const flatCategories = []
    flattenCategories(response.data, flatCategories)
    categories.value = flatCategories
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

function flattenCategories(cats, result, prefix = '') {
  for (const cat of cats) {
    result.push({
      ...cat,
      full_name: prefix ? `${prefix} > ${cat.name}` : cat.name
    })
    if (cat.children && cat.children.length > 0) {
      flattenCategories(cat.children, result, prefix ? `${prefix} > ${cat.name}` : cat.name)
    }
  }
}

async function fetchProducts() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
    }
    if (searchQuery.value) params.keyword = searchQuery.value
    if (categoryFilter.value) params.category_id = categoryFilter.value
    if (typeFilter.value) params.clothing_type = typeFilter.value
    
    const response = await api.get('/clothings', { params })
    
    // 각 품목에 대한 가격과 재고 정보 추가 조회
    const itemsWithDetails = await Promise.all(
      response.data.items.map(async (item) => {
        try {
          // 규격 정보 조회
          const specsRes = await api.get(`/clothings/${item.id}/specs`)
          const itemSpecs = specsRes.data || []
          
          // 최소 가격 계산
          const minPrice = itemSpecs.length > 0 
            ? Math.min(...itemSpecs.filter(s => s.is_active).map(s => s.price))
            : null
          
          return {
            ...item,
            min_price: minPrice,
            total_stock: 0, // 재고는 별도 재고관리에서 관리
          }
        } catch {
          return { ...item, min_price: null, total_stock: 0 }
        }
      })
    )
    
    items.value = itemsWithDetails
    pagination.value.total = response.data.total
  } catch (error) {
    console.error('Failed to fetch products:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch(query) {
  searchQuery.value = query
  pagination.value.page = 1
  fetchProducts()
}

function handleFilterChange(key, value) {
  if (key === 'category_id') categoryFilter.value = value
  if (key === 'clothing_type') typeFilter.value = value
  pagination.value.page = 1
  fetchProducts()
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchProducts()
}

function openForm(product = null) {
  if (product) {
    editProduct.value = product
    Object.assign(form, {
      name: product.name,
      category_id: product.category_id,
      clothing_type: product.clothing_type,
      description: product.description || '',
      image_url: product.image_url || '',
      is_active: product.is_active,
    })
  } else {
    editProduct.value = null
    Object.assign(form, {
      name: '',
      category_id: '',
      clothing_type: 'ready_made',
      description: '',
      image_url: '',
      is_active: true,
    })
  }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editProduct.value = null
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editProduct.value) {
      await api.put(`/clothings/${editProduct.value.id}`, form)
      alert('수정되었습니다.')
    } else {
      await api.post('/clothings', form)
      alert('등록되었습니다.')
    }
    closeForm()
    fetchProducts()
  } catch (error) {
    alert(error.response?.data?.detail || '저장에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function deleteProduct(product) {
  if (!confirm(`"${product.name}"을(를) 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/clothings/${product.id}`)
    alert('삭제되었습니다.')
    fetchProducts()
  } catch (error) {
    alert(error.response?.data?.detail || '삭제에 실패했습니다.')
  }
}

// 규격 관리
async function viewSpecs(product) {
  selectedProduct.value = product
  try {
    const response = await api.get(`/clothings/${product.id}/specs`)
    specs.value = response.data || []
    showSpecs.value = true
  } catch (error) {
    alert('규격 조회에 실패했습니다.')
  }
}

function closeSpecs() {
  showSpecs.value = false
  selectedProduct.value = null
  specs.value = []
}

function openSpecForm(spec = null) {
  if (spec) {
    editSpec.value = spec
    Object.assign(specForm, {
      spec_code: spec.spec_code,
      size: spec.size,
      price: spec.price,
      is_active: spec.is_active,
    })
  } else {
    editSpec.value = null
    Object.assign(specForm, {
      spec_code: '',
      size: '',
      price: 0,
      is_active: true,
    })
  }
  showSpecForm.value = true
}

function closeSpecForm() {
  showSpecForm.value = false
  editSpec.value = null
}

async function handleSpecSubmit() {
  submitting.value = true
  try {
    if (editSpec.value) {
      await api.put(`/clothings/${selectedProduct.value.id}/specs/${editSpec.value.id}`, specForm)
      alert('수정되었습니다.')
    } else {
      await api.post(`/clothings/${selectedProduct.value.id}/specs`, specForm)
      alert('등록되었습니다.')
    }
    closeSpecForm()
    // 규격 목록 새로고침
    const response = await api.get(`/clothings/${selectedProduct.value.id}/specs`)
    specs.value = response.data || []
    fetchProducts() // 가격 업데이트를 위해 목록도 새로고침
  } catch (error) {
    alert(error.response?.data?.detail || '저장에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function deleteSpec(spec) {
  if (!confirm(`규격 "${spec.spec_code}"을(를) 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/clothings/${selectedProduct.value.id}/specs/${spec.id}`)
    alert('삭제되었습니다.')
    const response = await api.get(`/clothings/${selectedProduct.value.id}/specs`)
    specs.value = response.data || []
    fetchProducts()
  } catch (error) {
    alert(error.response?.data?.detail || '삭제에 실패했습니다.')
  }
}
</script>

<style scoped>
.clothing-list {
  padding: 20px;
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

.product-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-image {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  object-fit: cover;
}

.product-image-placeholder {
  width: 48px;
  height: 48px;
  background: #f3f4f6;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-name {
  font-weight: 500;
}

.product-desc {
  font-size: 12px;
  color: #9ca3af;
}

.type-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type-badge.ready_made {
  background: #dbeafe;
  color: #1e40af;
}

.type-badge.custom {
  background: #fef3c7;
  color: #92400e;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.active {
  background: #dcfce7;
  color: #166534;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #dc2626;
}

.actions {
  display: flex;
  gap: 4px;
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
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-large {
  max-width: 700px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
}

.product-form,
.spec-form {
  padding: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.required {
  color: #dc2626;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.specs-content {
  padding: 20px;
}

.specs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.specs-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.specs-table {
  width: 100%;
  border-collapse: collapse;
}

.specs-table th,
.specs-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.specs-table th {
  background: #f9fafb;
  font-weight: 600;
  font-size: 14px;
}

.specs-table td {
  font-size: 14px;
}

.specs-table .empty {
  text-align: center;
  color: #9ca3af;
  padding: 40px;
}

.custom-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef3c7;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #92400e;
}

.notice-icon {
  font-size: 16px;
}
</style>
