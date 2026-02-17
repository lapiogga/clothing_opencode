<template>
  <aside class="sidebar">
    <nav>
      <ul class="menu">
        <li>
          <router-link to="/" class="menu-item" active-class="active">
            대시보드
          </router-link>
        </li>

        <template v-if="authStore.userRole === 'admin'">
          <li class="menu-category">사용자 관리</li>
          <li>
            <router-link to="/admin/users" class="menu-item" active-class="active">
              사용자 목록
            </router-link>
          </li>
          <li>
            <router-link to="/admin/points" class="menu-item" active-class="active">
              포인트 지급
            </router-link>
          </li>
          
          <li class="menu-category">품목 관리</li>
          <li>
            <router-link to="/admin/categories" class="menu-item" active-class="active">
              카테고리 관리
            </router-link>
          </li>
          <li>
            <router-link to="/admin/clothing" class="menu-item" active-class="active">
              피복 품목 관리
            </router-link>
          </li>
          
          <li class="menu-category">조직 관리</li>
          <li>
            <router-link to="/admin/sales-offices" class="menu-item" active-class="active">
              피복판매소 관리
            </router-link>
          </li>
        </template>

        <template v-if="authStore.hasAnyRole(['admin', 'sales_office'])">
          <li class="menu-category">판매 관리</li>
          <li>
            <router-link to="/sales/offline" class="menu-item" active-class="active">
              오프라인 판매
            </router-link>
          </li>
          <li>
            <router-link to="/sales/orders" class="menu-item" active-class="active">
              온라인 주문 관리
            </router-link>
          </li>
          <li>
            <router-link to="/sales/inventory" class="menu-item" active-class="active">
              재고 관리
            </router-link>
          </li>
          <li>
            <router-link to="/sales/refund" class="menu-item" active-class="active">
              반품 처리
            </router-link>
          </li>
          <li>
            <router-link to="/sales/stats" class="menu-item" active-class="active">
              통계
            </router-link>
          </li>
        </template>

        <template v-if="authStore.hasAnyRole(['admin', 'general'])">
          <li class="menu-category">쇼핑몰</li>
          <li>
            <router-link to="/user/shop" class="menu-item" active-class="active">
              피복 쇼핑
            </router-link>
          </li>
          <li>
            <router-link to="/user/cart" class="menu-item" active-class="active">
              장바구니
            </router-link>
          </li>
          <li>
            <router-link to="/user/orders" class="menu-item" active-class="active">
              주문/배송 조회
            </router-link>
          </li>
          <li>
            <router-link to="/user/points" class="menu-item" active-class="active">
              포인트 조회
            </router-link>
          </li>
        </template>

        <template v-if="authStore.hasAnyRole(['admin', 'tailor_company'])">
          <li class="menu-category">체척권 관리</li>
          <li>
            <router-link to="/tailor/register" class="menu-item" active-class="active">
              체척권 등록
            </router-link>
          </li>
          <li>
            <router-link to="/tailor/vouchers" class="menu-item" active-class="active">
              체척권 현황
            </router-link>
          </li>
        </template>

        <li class="menu-category">내 정보</li>
        <li>
          <router-link to="/user/profile" class="menu-item" active-class="active">
            프로필
          </router-link>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 60px;
  left: 0;
  bottom: 0;
  width: 220px;
  background: #2c3e50;
  padding: 10px 0;
  overflow-y: auto;
}

.menu {
  list-style: none;
}

.menu-category {
  padding: 15px 20px 8px 20px;
  color: #95a5a6;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.menu-item {
  display: block;
  padding: 12px 20px 12px 25px;
  color: #bdc3c7;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.menu-item.active {
  background: rgba(74, 144, 217, 0.2);
  color: white;
  border-left-color: #4a90d9;
}
</style>
