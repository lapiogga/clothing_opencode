<template>
  <div class="dashboard">
    <h2>{{ greeting }}{{ authStore.user?.name }}님</h2>
    
    <div v-if="authStore.userRole === 'admin'" class="role-dashboard">
      <h3>군수담당자 대시보드</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <h4>전체 사용자</h4>
          <p class="stat-number">{{ stats.totalUsers }}</p>
        </div>
        <div class="stat-card">
          <h4>피복판매소</h4>
          <p class="stat-number">{{ stats.salesOffices }}</p>
        </div>
        <div class="stat-card">
          <h4>체척업체</h4>
          <p class="stat-number">{{ stats.tailorCompanies }}</p>
        </div>
        <div class="stat-card">
          <h4>품목 수</h4>
          <p class="stat-number">{{ stats.clothingItems }}</p>
        </div>
      </div>
    </div>

    <div v-else-if="authStore.userRole === 'sales_office'" class="role-dashboard">
      <h3>피복판매소 대시보드</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <h4>금일 판매</h4>
          <p class="stat-number">{{ stats.todaySales }}건</p>
        </div>
        <div class="stat-card">
          <h4>배송 대기</h4>
          <p class="stat-number">{{ stats.pendingDelivery }}건</p>
        </div>
        <div class="stat-card">
          <h4>재고 부족 품목</h4>
          <p class="stat-number">{{ stats.lowStock }}건</p>
        </div>
        <div class="stat-card">
          <h4>반품 요청</h4>
          <p class="stat-number">{{ stats.refundRequests }}건</p>
        </div>
      </div>
    </div>

    <div v-else-if="authStore.userRole === 'tailor_company'" class="role-dashboard">
      <h3>체척업체 대시보드</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <h4>미등록 체척권</h4>
          <p class="stat-number">{{ stats.pendingVouchers }}건</p>
        </div>
        <div class="stat-card">
          <h4>완료 건수</h4>
          <p class="stat-number">{{ stats.completedVouchers }}건</p>
        </div>
      </div>
    </div>

    <div v-else-if="authStore.userRole === 'general'" class="role-dashboard">
      <h3>일반사용자 대시보드</h3>
      <div class="stats-grid">
        <div class="stat-card highlight">
          <h4>사용 가능 포인트</h4>
          <p class="stat-number">{{ formatPoint(authStore.user?.available_point) }}원</p>
        </div>
        <div class="stat-card">
          <h4>예약 포인트</h4>
          <p class="stat-number">{{ formatPoint(authStore.user?.reserved_point) }}원</p>
        </div>
        <div class="stat-card">
          <h4>주문 중</h4>
          <p class="stat-number">{{ stats.activeOrders }}건</p>
        </div>
        <div class="stat-card">
          <h4>미사용 체척권</h4>
          <p class="stat-number">{{ stats.activeVouchers }}건</p>
        </div>
      </div>
      
      <div class="quick-actions">
        <h4>빠른 메뉴</h4>
        <div class="action-buttons">
          <router-link to="/user/shop" class="action-btn">
            피복 쇼핑
          </router-link>
          <router-link to="/user/orders" class="action-btn">
            주문 조회
          </router-link>
          <router-link to="/user/points" class="action-btn">
            포인트 내역
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()
const stats = ref({
  totalUsers: 0,
  salesOffices: 0,
  tailorCompanies: 0,
  clothingItems: 0,
  todaySales: 0,
  pendingDelivery: 0,
  lowStock: 0,
  refundRequests: 0,
  pendingVouchers: 0,
  completedVouchers: 0,
  activeOrders: 0,
  activeVouchers: 0
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '좋은 아침입니다, '
  if (hour < 18) return '좋은 오후입니다, '
  return '좋은 저녁입니다, '
})

function formatPoint(point) {
  if (!point) return '0'
  return point.toLocaleString()
}

onMounted(async () => {
  await authStore.fetchUser()
  try {
    const res = await api.get('/stats/dashboard')
    stats.value = { ...stats.value, ...res.data }
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

h2 {
  margin-bottom: 30px;
  color: #333;
}

h3 {
  margin-bottom: 20px;
  color: #555;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card.highlight {
  background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%);
}

.stat-card.highlight h4,
.stat-card.highlight .stat-number {
  color: white;
}

.stat-card h4 {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #4a90d9;
}

.quick-actions {
  margin-top: 30px;
}

.quick-actions h4 {
  margin-bottom: 15px;
  color: #555;
}

.action-buttons {
  display: flex;
  gap: 15px;
}

.action-btn {
  padding: 12px 24px;
  background: #4a90d9;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #357abd;
}
</style>
