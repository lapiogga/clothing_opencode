<template>
  <div class="inventory">
    <div class="page-header">
      <h1>재고 관리</h1>
      <div class="header-actions">
        <button class="btn btn-outline" @click="openReceive">입고 처리</button>
      </div>
    </div>

    <div class="summary-cards">
      <div class="summary-card">
        <div class="label">전체 품목</div>
        <div class="value">{{ summary.totalItems }}</div>
      </div>
      <div class="summary-card warning">
        <div class="label">재고 부족</div>
        <div class="value">{{ summary.lowStock }}</div>
      </div>
      <div class="summary-card danger">
        <div class="label">품절</div>
        <div class="value">{{ summary.outOfStock }}</div>
      </div>
    </div>

    <div class="search-section">
      <select v-if="isAdmin" v-model="salesOfficeFilter" class="office-select" @change="handleOfficeChange">
        <option :value="null">전체 판매소</option>
        <option v-for="office in salesOffices" :key="office.id" :value="office.id">
          {{ office.name }}
        </option>
      </select>
      <input
        v-model="searchKeyword"
        type="text"
        placeholder="품목명 검색"
        class="search-input"
        @keyup.enter="handleSearch"
      />
      <button class="btn btn-primary" @click="handleSearch">검색</button>
    </div>

    <Table
      :columns="columns"
      :data="inventory"
      :loading="loading"
    >
      <template #row="{ item }">
        <td v-if="isAdmin">{{ item.sales_office?.name || '-' }}</td>
        <td>
          <div class="product-info">
            <span class="product-name">{{ item.product?.name || '-' }}</span>
            <span class="product-spec" v-if="item.spec">[{{ item.spec.size }}]</span>
          </div>
        </td>
        <td>{{ item.product?.category?.name || '-' }}</td>
        <td :class="getStockClass(item.quantity)">
          {{ item.quantity?.toLocaleString() }}
        </td>
        <td>{{ item.reserved_quantity?.toLocaleString() || 0 }}</td>
        <td>{{ (item.quantity - (item.reserved_quantity || 0))?.toLocaleString() }}</td>
        <td>
          <span :class="['status-badge', getStockStatus(item)]">
            {{ getStockStatusLabel(item) }}
          </span>
        </td>
        <td>{{ formatDate(item.lastUpdated) }}</td>
        <td class="actions">
          <button class="btn btn-sm btn-outline" @click="openAdjustment(item)">조정</button>
          <button class="btn btn-sm btn-outline" @click="viewHistory(item)">이력</button>
        </td>
      </template>
    </Table>

    <Pagination
      :current-page="pagination.page"
      :total-pages="totalPages"
      :total-items="pagination.total"
      @page-change="handlePageChange"
    />

    <!-- 입고 처리 모달 -->
    <div v-if="showReceive" class="modal-overlay" @click.self="closeReceive">
      <div class="modal-content">
        <div class="modal-header">
          <h2>입고 처리</h2>
          <button class="close-btn" @click="closeReceive">&times;</button>
        </div>
        <form @submit.prevent="submitReceive" class="form-content">
          <div class="form-group">
            <label>품목 선택 <span class="required">*</span></label>
            <select v-model="receiveForm.item_id" @change="onItemChange" required>
              <option value="">선택하세요</option>
              <option v-for="item in clothingItems" :key="item.id" :value="item.id">
                {{ item.name }} ({{ item.clothing_type === 'ready_made' ? '완제품' : '맞춤' }})
              </option>
            </select>
          </div>

          <div class="form-group" v-if="receiveForm.item_id && availableSpecs.length > 0">
            <label>규격 선택 <span class="required">*</span></label>
            <select v-model="receiveForm.spec_id" required>
              <option value="">선택하세요</option>
              <option v-for="spec in availableSpecs" :key="spec.id" :value="spec.id">
                {{ spec.size }} - {{ spec.price?.toLocaleString() }}P
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>입고 수량 <span class="required">*</span></label>
            <input v-model.number="receiveForm.quantity" type="number" min="1" required />
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeReceive">취소</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? '처리 중...' : '입고' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 재고 조정 모달 -->
    <div v-if="showAdjustment" class="modal-overlay" @click.self="closeAdjustment">
      <div class="modal-content">
        <div class="modal-header">
          <h2>재고 조정</h2>
          <button class="close-btn" @click="closeAdjustment">&times;</button>
        </div>
        <form @submit.prevent="submitAdjustment" class="form-content">
          <div class="form-group">
            <label>품목</label>
            <div class="product-display">
              {{ adjustmentItem.product?.name || '-' }}
              <span v-if="adjustmentItem.spec">[{{ adjustmentItem.spec.size }}]</span>
            </div>
            <div class="current-stock">현재 재고: {{ adjustmentItem.quantity?.toLocaleString() }}</div>
          </div>

          <div class="form-group">
            <label>조정 유형 <span class="required">*</span></label>
            <select v-model="adjustmentForm.adjustment_type" required>
              <option value="">선택하세요</option>
              <option value="increase">증가</option>
              <option value="decrease">감소</option>
              <option value="correction">수량 정정</option>
            </select>
          </div>

          <div class="form-group">
            <label>{{ adjustmentForm.adjustment_type === 'correction' ? '정정 수량' : '조정 수량' }} <span class="required">*</span></label>
            <input v-model.number="adjustmentForm.quantity" type="number" min="0" required />
          </div>

          <div class="form-group">
            <label>사유</label>
            <input v-model="adjustmentForm.reason" type="text" placeholder="조정 사유 입력" />
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeAdjustment">취소</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? '처리 중...' : '저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 재고 이력 모달 -->
    <div v-if="showHistory" class="modal-overlay" @click.self="closeHistory">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h2>재고 이력 - {{ historyItem?.product?.name || '' }}</h2>
          <button class="close-btn" @click="closeHistory">&times;</button>
        </div>
        <div class="history-content">
          <table class="history-table" v-if="historyLogs.length > 0">
            <thead>
              <tr>
                <th>일시</th>
                <th>유형</th>
                <th>수량</th>
                <th>변경 전</th>
                <th>변경 후</th>
                <th>사유</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in historyLogs" :key="log.id">
                <td>{{ formatDateTime(log.adjustment_date) }}</td>
                <td>
                  <span :class="['type-badge', log.adjustment_type]">
                    {{ getAdjustmentTypeLabel(log.adjustment_type) }}
                  </span>
                </td>
                <td :class="log.adjustment_type === 'decrease' ? 'minus' : 'plus'">
                  {{ log.adjustment_type === 'decrease' ? '-' : '+' }}{{ log.quantity }}
                </td>
                <td>{{ log.before_quantity }}</td>
                <td>{{ log.after_quantity }}</td>
                <td>{{ log.reason || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-history">이력이 없습니다</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import Table from '@/components/common/Table.vue'
import Pagination from '@/components/common/Pagination.vue'

const authStore = useAuthStore()

const inventory = ref([])
const clothingItems = ref([])
const availableSpecs = ref([])
const salesOffices = ref([])
const loading = ref(false)
const summary = ref({ totalItems: 0, lowStock: 0, outOfStock: 0 })
const pagination = ref({ page: 1, pageSize: 20, total: 0 })
const searchKeyword = ref('')
const salesOfficeFilter = ref(null)

const isAdmin = computed(() => authStore.user?.role === 'admin')

const baseColumns = [
  { key: 'product', label: '품목' },
  { key: 'category', label: '카테고리' },
  { key: 'quantity', label: '재고수량' },
  { key: 'reserved', label: '예약수량' },
  { key: 'available', label: '가용수량' },
  { key: 'status', label: '상태' },
  { key: 'lastUpdated', label: '최종수정' },
  { key: 'actions', label: '관리' }
]

const columns = computed(() => {
  if (isAdmin.value) {
    return [{ key: 'sales_office', label: '판매소' }, ...baseColumns]
  }
  return baseColumns
})

const showReceive = ref(false)
const showAdjustment = ref(false)
const showHistory = ref(false)
const adjustmentItem = ref({})
const historyItem = ref({})
const historyLogs = ref([])
const submitting = ref(false)

const receiveForm = reactive({
  item_id: '',
  spec_id: '',
  quantity: 1
})

const adjustmentForm = reactive({
  adjustment_type: '',
  quantity: null,
  reason: ''
})

const totalPages = computed(() => Math.ceil(pagination.value.total / pagination.value.pageSize))

onMounted(async () => {
  if (isAdmin.value) {
    await fetchSalesOffices()
  }
  fetchInventory()
  fetchSummary()
})

async function fetchSalesOffices() {
  try {
    const response = await api.get('/sales-offices')
    salesOffices.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch sales offices:', error)
  }
}

async function fetchInventory() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    if (salesOfficeFilter.value) {
      params.sales_office_id = salesOfficeFilter.value
    }
    const response = await api.get('/inventory', { params })
    inventory.value = response.data.items || []
    pagination.value.total = response.data.total || 0
  } catch (error) {
    console.error('Failed to fetch inventory:', error)
    alert('재고 목록 조회에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

async function fetchSummary() {
  try {
    const response = await api.get('/inventory/summary')
    summary.value = response.data
  } catch (error) {
    console.error('Failed to fetch summary:', error)
  }
}

async function fetchClothingItems() {
  try {
    const response = await api.get('/clothings', { params: { page_size: 100 } })
    clothingItems.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch clothing items:', error)
  }
}

async function onItemChange() {
  receiveForm.spec_id = ''
  availableSpecs.value = []
  if (receiveForm.item_id) {
    try {
      const response = await api.get(`/clothings/${receiveForm.item_id}/specs`)
      availableSpecs.value = response.data || []
    } catch (error) {
      console.error('Failed to fetch specs:', error)
    }
  }
}

function handleSearch() {
  pagination.value.page = 1
  fetchInventory()
}

function handleOfficeChange() {
  pagination.value.page = 1
  fetchInventory()
  fetchSummary()
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchInventory()
}

async function openReceive() {
  await fetchClothingItems()
  Object.assign(receiveForm, { item_id: '', spec_id: '', quantity: 1 })
  availableSpecs.value = []
  showReceive.value = true
}

function closeReceive() {
  showReceive.value = false
}

async function submitReceive() {
  submitting.value = true
  try {
    const userRes = await api.get('/auth/me')
    const salesOfficeId = userRes.data.sales_office_id
    if (!salesOfficeId) {
      alert('판매소 정보가 없습니다.')
      return
    }
    await api.post('/inventory/receive', {
      sales_office_id: salesOfficeId,
      item_id: receiveForm.item_id,
      spec_id: receiveForm.spec_id || null,
      quantity: receiveForm.quantity
    })
    alert('입고 처리되었습니다.')
    closeReceive()
    fetchInventory()
    fetchSummary()
  } catch (error) {
    alert(error.response?.data?.detail || '입고 처리에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

function openAdjustment(item) {
  adjustmentItem.value = item
  Object.assign(adjustmentForm, { adjustment_type: '', quantity: null, reason: '' })
  showAdjustment.value = true
}

function closeAdjustment() {
  showAdjustment.value = false
  adjustmentItem.value = {}
}

async function submitAdjustment() {
  submitting.value = true
  try {
    // 재고 아이템에서 판매소 ID 가져오기
    const salesOfficeId = adjustmentItem.value.sales_office_id
    if (!salesOfficeId) {
      alert('판매소 정보가 없습니다.')
      return
    }
    await api.post('/inventory/adjust', {
      sales_office_id: salesOfficeId,
      item_id: adjustmentItem.value.item_id,
      spec_id: adjustmentItem.value.spec_id,
      adjustment_type: adjustmentForm.adjustment_type,
      quantity: adjustmentForm.quantity,
      reason: adjustmentForm.reason
    })
    alert('재고가 조정되었습니다.')
    closeAdjustment()
    fetchInventory()
    fetchSummary()
  } catch (error) {
    alert(error.response?.data?.detail || '재고 조정에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function viewHistory(item) {
  historyItem.value = item
  try {
    const response = await api.get('/inventory/history', {
      params: { inventory_id: item.id, page_size: 50 }
    })
    historyLogs.value = response.data.items || []
    showHistory.value = true
  } catch (error) {
    alert('이력 조회에 실패했습니다.')
  }
}

function closeHistory() {
  showHistory.value = false
  historyLogs.value = []
  historyItem.value = {}
}

function getStockClass(quantity) {
  if (quantity === 0) return 'out-of-stock'
  if (quantity <= 10) return 'low-stock'
  return ''
}

function getStockStatus(item) {
  if (item.quantity === 0) return 'out'
  if (item.quantity <= 10) return 'low'
  return 'normal'
}

function getStockStatusLabel(item) {
  const status = getStockStatus(item)
  const labels = { normal: '정상', low: '부족', out: '품절' }
  return labels[status]
}

function getAdjustmentTypeLabel(type) {
  const labels = {
    increase: '증가',
    decrease: '감소',
    correction: '정정'
  }
  return labels[type] || type
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ko-KR')
}
</script>

<style scoped>
.inventory {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.summary-card .label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.summary-card .value {
  font-size: 28px;
  font-weight: 600;
}

.summary-card.warning {
  border-left: 4px solid #f59e0b;
}

.summary-card.danger {
  border-left: 4px solid #dc2626;
}

.search-section {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.office-select {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  min-width: 150px;
}

.search-input {
  flex: 1;
  max-width: 300px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.product-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.product-name {
  font-weight: 500;
}

.product-spec {
  color: #6b7280;
  font-size: 12px;
}

.out-of-stock {
  color: #dc2626;
  font-weight: 600;
}

.low-stock {
  color: #f59e0b;
  font-weight: 600;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.normal { background: #dcfce7; color: #166534; }
.status-badge.low { background: #fef3c7; color: #92400e; }
.status-badge.out { background: #fee2e2; color: #dc2626; }

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

.form-content {
  padding: 20px;
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
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.product-display {
  font-weight: 500;
}

.current-stock {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.required {
  color: #dc2626;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.history-content {
  padding: 20px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

.history-table th {
  background: #f9fafb;
  font-weight: 600;
}

.type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type-badge.increase { background: #dcfce7; color: #166534; }
.type-badge.decrease { background: #fee2e2; color: #dc2626; }
.type-badge.correction { background: #e0e7ff; color: #3730a3; }

.plus { color: #16a34a; font-weight: 500; }
.minus { color: #dc2626; font-weight: 500; }

.empty-history {
  text-align: center;
  color: #9ca3af;
  padding: 40px;
}
</style>
