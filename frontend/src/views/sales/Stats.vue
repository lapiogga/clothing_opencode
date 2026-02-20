<template>
  <div class="stats">
    <!-- Header -->
    <header class="header">
      <h1>통계</h1>
      <div class="period-selector">
        <button 
          v-for="p in periods" 
          :key="p.value" 
          :class="['period-btn', { active: selectedPeriod === p.value }]"
          @click="setPeriod(p.value)"
        >
          {{ p.label }}
        </button>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>데이터 로딩 중...</span>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Summary -->
      <section class="summary">
        <div class="metric primary">
          <span class="metric-value">{{ formatNumber(stats.totalSales) }}</span>
          <span class="metric-label">총 매출</span>
        </div>
        <div class="metric">
          <span class="metric-value">{{ stats.totalOrders }}</span>
          <span class="metric-label">판매건</span>
        </div>
        <div class="metric">
          <span class="metric-value">{{ formatNumber(stats.totalPoints) }}</span>
          <span class="metric-label">포인트 사용</span>
        </div>
        <div class="metric">
          <span class="metric-value">{{ stats.refundCount }}</span>
          <span class="metric-label">반품</span>
        </div>
      </section>

      <!-- Charts -->
      <section class="charts">
        <div class="chart-panel">
          <h3>일별 추이</h3>
          <div v-if="!stats.dailySales?.length" class="empty">데이터 없음</div>
          <div v-else class="bar-chart">
            <div 
              v-for="(d, i) in stats.dailySales" 
              :key="i" 
              class="bar-item"
              :style="{ '--height': getBarHeight(d.amount) + '%' }"
              :title="d.date + ': ' + formatNumber(d.amount) + '원'"
            >
              <span class="bar-tooltip">{{ d.date.slice(5) }}</span>
            </div>
          </div>
        </div>

        <div class="chart-panel">
          <h3>카테고리별</h3>
          <div v-if="!stats.categorySales?.length" class="empty">데이터 없음</div>
          <div v-else class="donut-chart">
            <div class="donut">
              <svg viewBox="0 0 36 36">
                <circle 
                  v-for="(c, i) in donutSegments" 
                  :key="i"
                  cx="18" cy="18" r="15.9"
                  fill="none"
                  :stroke="c.color"
                  stroke-width="3"
                  :stroke-dasharray="c.percent + ' ' + (100 - c.percent)"
                  :stroke-dashoffset="c.offset"
                />
              </svg>
              <span class="donut-center">{{ categoryTotal }}개</span>
            </div>
            <div class="legend">
              <div v-for="(c, i) in stats.categorySales" :key="i" class="legend-item">
                <span class="dot" :style="{ background: colors[i % colors.length] }"></span>
                <span class="name">{{ c.name }}</span>
                <span class="value">{{ formatNumber(c.amount) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Tables -->
      <section class="tables">
        <div class="table-panel">
          <h3>인기 상품</h3>
          <div v-if="!stats.topProducts?.length" class="empty">데이터 없음</div>
          <ul v-else class="rank-list">
            <li v-for="(p, i) in stats.topProducts" :key="p.id">
              <span class="rank" :class="{ top: i < 3 }">{{ i + 1 }}</span>
              <span class="name">{{ p.name }}</span>
              <span class="qty">{{ p.quantity }}개</span>
              <span class="amount">{{ formatNumber(p.amount) }}</span>
            </li>
          </ul>
        </div>

        <div class="table-panel">
          <h3>결제 수단</h3>
          <div v-if="!stats.paymentMethods?.length" class="empty">데이터 없음</div>
          <ul v-else class="payment-list">
            <li v-for="p in stats.paymentMethods" :key="p.type">
              <span class="type">{{ getPaymentLabel(p.type) }}</span>
              <div class="progress">
                <div class="fill" :style="{ width: p.percentage + '%' }"></div>
              </div>
              <span class="percent">{{ p.percentage }}%</span>
            </li>
          </ul>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const loading = ref(true)
const selectedPeriod = ref('month')
const stats = ref({
  totalSales: 0,
  totalOrders: 0,
  totalPoints: 0,
  refundCount: 0,
  topProducts: [],
  paymentMethods: [],
  dailySales: [],
  categorySales: []
})

const periods = [
  { label: '주간', value: 'week' },
  { label: '월간', value: 'month' },
  { label: '분기', value: 'quarter' }
]

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

const categoryTotal = computed(() => stats.value.categorySales?.length || 0)

const donutSegments = computed(() => {
  if (!stats.value.categorySales?.length) return []
  const total = stats.value.categorySales.reduce((sum, c) => sum + c.amount, 0)
  let offset = 25
  return stats.value.categorySales.map((c, i) => {
    const percent = (c.amount / total) * 100
    const segment = { percent, color: colors[i % colors.length], offset }
    offset = offset - percent
    return segment
  })
})

const maxDaily = computed(() => {
  if (!stats.value.dailySales?.length) return 1
  return Math.max(...stats.value.dailySales.map(d => d.amount))
})

function getBarHeight(amount) {
  return (amount / maxDaily.value) * 100
}

function formatNumber(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '만'
  return n.toLocaleString()
}

function getPaymentLabel(type) {
  return { points: '포인트', cash: '현금', card: '카드' }[type] || type
}

function setPeriod(period) {
  selectedPeriod.value = period
  fetchStats()
}

function getDateRange(period) {
  const end = new Date()
  const start = new Date()
  
  if (period === 'week') start.setDate(end.getDate() - 7)
  else if (period === 'month') start.setMonth(end.getMonth() - 1)
  else start.setMonth(end.getMonth() - 3)
  
  return {
    startDate: start.toISOString().split('T')[0],
    endDate: end.toISOString().split('T')[0]
  }
}

async function fetchStats() {
  loading.value = true
  try {
    const { startDate, endDate } = getDateRange(selectedPeriod.value)
    const res = await api.get('/stats/sales', { params: { startDate, endDate } })
    stats.value = res.data
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<style scoped>
.stats {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #111;
}

.period-selector {
  display: flex;
  gap: 4px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}

.period-btn {
  padding: 6px 14px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.period-btn.active {
  background: white;
  color: #111;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6b7280;
  gap: 12px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Summary */
.summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric {
  background: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}

.metric.primary {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
}

.metric-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.metric.primary .metric-value {
  font-size: 32px;
}

.metric-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.metric.primary .metric-label {
  color: rgba(255,255,255,0.8);
}

/* Charts */
.charts {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.chart-panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.chart-panel h3 {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 16px;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
  font-size: 13px;
}

/* Bar Chart */
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 160px;
  padding-top: 8px;
}

.bar-item {
  flex: 1;
  height: var(--height);
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  position: relative;
  cursor: pointer;
  transition: opacity 0.2s;
}

.bar-item:hover {
  opacity: 0.8;
}

.bar-tooltip {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #9ca3af;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s;
}

.bar-item:hover .bar-tooltip {
  opacity: 1;
}

/* Donut Chart */
.donut-chart {
  display: flex;
  align-items: center;
  gap: 20px;
}

.donut {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
}

.donut svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.legend {
  flex: 1;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.name {
  flex: 1;
  color: #374151;
}

.value {
  color: #6b7280;
  font-family: monospace;
}

/* Tables */
.tables {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.table-panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.table-panel h3 {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

/* Rank List */
.rank-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.rank-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}

.rank-list li:last-child {
  border-bottom: none;
}

.rank {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
}

.rank.top {
  background: #fef3c7;
  color: #d97706;
}

.rank-list .name {
  flex: 1;
  font-size: 13px;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-list .qty {
  font-size: 12px;
  color: #6b7280;
}

.rank-list .amount {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  min-width: 60px;
  text-align: right;
}

/* Payment List */
.payment-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.payment-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
}

.payment-list .type {
  width: 60px;
  font-size: 13px;
  color: #374151;
}

.progress {
  flex: 1;
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}

.fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 3px;
  transition: width 0.3s;
}

.percent {
  width: 40px;
  font-size: 12px;
  color: #6b7280;
  text-align: right;
}

/* Responsive */
@media (max-width: 768px) {
  .stats {
    padding: 16px;
  }
  
  .header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .summary {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts,
  .tables {
    grid-template-columns: 1fr;
  }
  
  .donut-chart {
    flex-direction: column;
  }
}
</style>
