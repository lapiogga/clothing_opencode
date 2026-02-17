<template>
  <div class="stats">
    <div class="page-header">
      <h1>판매 통계</h1>
      <div class="date-range">
        <input v-model="startDate" type="date" />
        <span>~</span>
        <input v-model="endDate" type="date" />
        <button class="btn btn-primary" @click="fetchStats">조회</button>
      </div>
    </div>

    <div class="summary-cards">
      <div class="summary-card">
        <div class="icon">💰</div>
        <div class="content">
          <div class="label">총 매출</div>
          <div class="value">{{ stats.totalSales?.toLocaleString() }}원</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="icon">📦</div>
        <div class="content">
          <div class="label">총 판매건</div>
          <div class="value">{{ stats.totalOrders?.toLocaleString() }}건</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="icon">⭐</div>
        <div class="content">
          <div class="label">포인트 사용</div>
          <div class="value">{{ stats.totalPoints?.toLocaleString() }}P</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="icon">🔄</div>
        <div class="content">
          <div class="label">반품건</div>
          <div class="value">{{ stats.refundCount?.toLocaleString() }}건</div>
        </div>
      </div>
    </div>

    <div class="charts-section">
      <div class="chart-card">
        <h3>일별 판매 추이</h3>
        <div class="chart-container" ref="salesChart"></div>
      </div>
      <div class="chart-card">
        <h3>카테고리별 판매 비중</h3>
        <div class="chart-container" ref="categoryChart"></div>
      </div>
    </div>

    <div class="tables-section">
      <div class="table-card">
        <h3>인기 상품 TOP 10</h3>
        <table class="stats-table">
          <thead>
            <tr>
              <th>순위</th>
              <th>상품명</th>
              <th>판매수량</th>
              <th>매출액</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in stats.topProducts" :key="item.id">
              <td>{{ index + 1 }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.quantity?.toLocaleString() }}</td>
              <td>{{ item.amount?.toLocaleString() }}원</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="table-card">
        <h3>결제 수단별 현황</h3>
        <table class="stats-table">
          <thead>
            <tr>
              <th>결제수단</th>
              <th>건수</th>
              <th>금액</th>
              <th>비율</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in stats.paymentMethods" :key="item.type">
              <td>{{ getPaymentLabel(item.type) }}</td>
              <td>{{ item.count?.toLocaleString() }}</td>
              <td>{{ item.amount?.toLocaleString() }}원</td>
              <td>{{ item.percentage }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/api'

const startDate = ref(getDefaultStartDate())
const endDate = ref(getDefaultEndDate())
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

const salesChart = ref(null)
const categoryChart = ref(null)
let charts = []

function getDefaultStartDate() {
  const date = new Date()
  date.setMonth(date.getMonth() - 1)
  return date.toISOString().split('T')[0]
}

function getDefaultEndDate() {
  return new Date().toISOString().split('T')[0]
}

onMounted(() => {
  fetchStats()
})

onUnmounted(() => {
  charts.forEach(chart => chart?.destroy?.())
})

async function fetchStats() {
  try {
    const response = await api.get('/stats/sales', {
      params: {
        startDate: startDate.value,
        endDate: endDate.value
      }
    })
    stats.value = response.data
    renderCharts()
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

function renderCharts() {
  renderSalesChart()
  renderCategoryChart()
}

function renderSalesChart() {
  if (!salesChart.value || !stats.value.dailySales) return
  
  const canvas = document.createElement('canvas')
  salesChart.value.innerHTML = ''
  salesChart.value.appendChild(canvas)
  
  const ctx = canvas.getContext('2d')
  const data = stats.value.dailySales
  
  const labels = data.map(d => d.date.slice(5))
  const values = data.map(d => d.amount)
  
  const max = Math.max(...values) * 1.1
  const height = 200
  const width = salesChart.value.clientWidth
  const padding = 40
  
  ctx.clearRect(0, 0, width, height)
  
  ctx.strokeStyle = '#e5e7eb'
  ctx.lineWidth = 1
  for (let i = 0; i <= 4; i++) {
    const y = padding + (height - padding * 2) * (i / 4)
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(width - padding, y)
    ctx.stroke()
  }
  
  ctx.strokeStyle = '#3b82f6'
  ctx.lineWidth = 2
  ctx.beginPath()
  data.forEach((d, i) => {
    const x = padding + (width - padding * 2) * (i / (data.length - 1 || 1))
    const y = height - padding - (d.amount / max) * (height - padding * 2)
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.stroke()
  
  ctx.fillStyle = '#3b82f6'
  data.forEach((d, i) => {
    const x = padding + (width - padding * 2) * (i / (data.length - 1 || 1))
    const y = height - padding - (d.amount / max) * (height - padding * 2)
    ctx.beginPath()
    ctx.arc(x, y, 3, 0, Math.PI * 2)
    ctx.fill()
  })
  
  ctx.fillStyle = '#6b7280'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'center'
  labels.forEach((label, i) => {
    if (i % Math.ceil(labels.length / 7) === 0) {
      const x = padding + (width - padding * 2) * (i / (data.length - 1 || 1))
      ctx.fillText(label, x, height - 10)
    }
  })
}

function renderCategoryChart() {
  if (!categoryChart.value || !stats.value.categorySales) return
  
  const container = categoryChart.value
  container.innerHTML = ''
  
  const total = stats.value.categorySales.reduce((sum, c) => sum + c.amount, 0)
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
  
  stats.value.categorySales.forEach((cat, i) => {
    const item = document.createElement('div')
    item.className = 'category-item'
    const percentage = ((cat.amount / total) * 100).toFixed(1)
    item.innerHTML = `
      <div class="category-color" style="background: ${colors[i % colors.length]}"></div>
      <div class="category-info">
        <span class="category-name">${cat.name}</span>
        <span class="category-amount">${cat.amount?.toLocaleString()}원 (${percentage}%)</span>
      </div>
      <div class="category-bar">
        <div class="bar-fill" style="width: ${percentage}%; background: ${colors[i % colors.length]}"></div>
      </div>
    `
    container.appendChild(item)
  })
}

function getPaymentLabel(type) {
  const labels = {
    points: '포인트',
    cash: '현금',
    card: '카드'
  }
  return labels[type] || type
}
</script>

<style scoped>
.stats {
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

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-range input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.summary-card .icon {
  font-size: 32px;
}

.summary-card .label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 4px;
}

.summary-card .value {
  font-size: 24px;
  font-weight: 600;
}

.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.chart-container {
  height: 200px;
  position: relative;
}

.category-item {
  display: grid;
  grid-template-columns: 12px 1fr;
  gap: 8px;
  margin-bottom: 12px;
  align-items: center;
}

.category-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.category-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.category-name {
  color: #374151;
}

.category-amount {
  color: #6b7280;
}

.category-bar {
  grid-column: span 2;
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
}

.tables-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.table-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.table-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
}

.stats-table th,
.stats-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

.stats-table th {
  background: #f9fafb;
  font-weight: 500;
  font-size: 13px;
  color: #6b7280;
}
</style>
