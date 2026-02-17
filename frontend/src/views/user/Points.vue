<template>
  <div class="points">
    <div class="page-header">
      <h1>포인트 조회</h1>
    </div>

    <div class="balance-cards">
      <div class="balance-card main">
        <div class="balance-label">보유 포인트</div>
        <div class="balance-amount">{{ pointInfo.current_point?.toLocaleString() }}P</div>
      </div>
      <div class="balance-card sub">
        <div class="balance-label">예약 포인트</div>
        <div class="balance-amount">{{ pointInfo.reserved_point?.toLocaleString() }}P</div>
      </div>
      <div class="balance-card sub">
        <div class="balance-label">사용 가능</div>
        <div class="balance-amount">{{ pointInfo.available_point?.toLocaleString() }}P</div>
      </div>
    </div>

    <div class="tabs">
      <button :class="['tab', { active: activeTab === 'all' }]" @click="changeTab('all')">
        전체
      </button>
      <button :class="['tab', { active: activeTab === 'grant' }]" @click="changeTab('grant')">
        적립
      </button>
      <button :class="['tab', { active: activeTab === 'use' }]" @click="changeTab('use')">
        사용
      </button>
      <button :class="['tab', { active: activeTab === 'refund' }]" @click="changeTab('refund')">
        환불
      </button>
    </div>

    <div class="history-list">
      <div v-for="item in history" :key="item.id" class="history-item">
        <div class="item-left">
          <div class="item-date">{{ formatDate(item.created_at) }}</div>
          <div class="item-desc">{{ item.description || getTypeLabel(item.transaction_type) }}</div>
        </div>
        <div class="item-right">
          <div :class="['item-amount', getTypeClass(item.transaction_type)]">
            {{ getAmountPrefix(item.transaction_type) }}{{ item.amount?.toLocaleString() }}P
          </div>
          <div class="item-balance">잔액: {{ item.balance_after?.toLocaleString() }}P</div>
        </div>
      </div>

      <div v-if="history.length === 0" class="empty-state">
        내역이 없습니다.
      </div>
    </div>

    <Pagination
      :current-page="pagination.page"
      :total-pages="totalPages"
      @page-change="handlePageChange"
    />

    <div class="expire-info">
      <h3>포인트 유효기간 안내</h3>
      <ul>
        <li>적립된 포인트는 적립일로부터 1년간 사용 가능합니다.</li>
        <li>유효기간이 경과한 포인트는 매월 말일 자동 소멸됩니다.</li>
        <li>포인트는 현금으로 환불되지 않습니다.</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import Pagination from '@/components/common/Pagination.vue'

const activeTab = ref('all')
const history = ref([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const pointInfo = ref({
  current_point: 0,
  reserved_point: 0,
  available_point: 0
})

const totalPages = computed(() => {
  return Math.ceil(pagination.value.total / pagination.value.pageSize)
})

onMounted(() => {
  fetchPointInfo()
  fetchHistory()
})

async function fetchPointInfo() {
  try {
    const response = await api.get('/points/my')
    pointInfo.value = response.data
  } catch (error) {
    console.error('Failed to fetch point info:', error)
  }
}

async function fetchHistory() {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    }
    if (activeTab.value !== 'all') {
      params.transaction_type = activeTab.value
    }
    const response = await api.get('/points/history', { params })
    history.value = response.data.items || []
    pagination.value.total = response.data.total || 0
  } catch (error) {
    console.error('Failed to fetch history:', error)
  } finally {
    loading.value = false
  }
}

function changeTab(tab) {
  activeTab.value = tab
  pagination.value.page = 1
  fetchHistory()
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchHistory()
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

function getTypeLabel(type) {
  const labels = {
    grant: '포인트 지급',
    use: '포인트 사용',
    reserve: '포인트 예약',
    release: '예약 해제',
    deduct: '포인트 차감',
    refund: '포인트 환불'
  }
  return labels[type] || type
}

function getTypeClass(type) {
  if (type === 'grant' || type === 'refund' || type === 'release') return 'earn'
  return 'use'
}

function getAmountPrefix(type) {
  if (type === 'grant' || type === 'refund' || type === 'release') return '+'
  if (type === 'reserve') return ''
  return '-'
}
</script>

<style scoped>
.points {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.balance-cards {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.balance-card {
  padding: 24px;
  border-radius: 12px;
}

.balance-card.main {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.balance-card.sub {
  background: white;
  border: 1px solid #e5e7eb;
}

.balance-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.balance-amount {
  font-size: 28px;
  font-weight: 700;
}

.balance-card.sub .balance-amount {
  font-size: 24px;
  color: #1f2937;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.tab {
  padding: 10px 20px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.tab.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.history-list {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f3f4f6;
}

.history-item:last-child {
  border-bottom: none;
}

.item-date {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.item-desc {
  font-size: 14px;
}

.item-amount {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.item-amount.earn {
  color: #16a34a;
}

.item-amount.use {
  color: #dc2626;
}

.item-balance {
  font-size: 12px;
  color: #9ca3af;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.expire-info {
  background: #f9fafb;
  padding: 20px;
  border-radius: 8px;
  margin-top: 24px;
}

.expire-info h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.expire-info ul {
  list-style: disc;
  padding-left: 20px;
  font-size: 13px;
  color: #6b7280;
}

.expire-info li {
  margin-bottom: 6px;
}
</style>
