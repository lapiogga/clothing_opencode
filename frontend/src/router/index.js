import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  
  {
    path: '/admin/users',
    name: 'UserList',
    component: () => import('@/views/admin/UserList.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/users/:id',
    name: 'UserForm',
    component: () => import('@/views/admin/UserForm.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/categories',
    name: 'CategoryList',
    component: () => import('@/views/admin/CategoryList.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/clothing',
    name: 'ClothingList',
    component: () => import('@/views/admin/ClothingList.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/sales-offices',
    name: 'SalesOfficeList',
    component: () => import('@/views/admin/SalesOfficeList.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/tailor-companies',
    name: 'TailorCompanyList',
    component: () => import('@/views/admin/TailorCompanyList.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/menus',
    name: 'MenuList',
    component: () => import('@/views/admin/MenuList.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/admin/points',
    name: 'PointGrant',
    component: () => import('@/views/admin/PointGrant.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  
  {
    path: '/sales/offline',
    name: 'OfflineSale',
    component: () => import('@/views/sales/OfflineSale.vue'),
    meta: { requiresAuth: true, roles: ['sales_office'] }
  },
  {
    path: '/sales/orders',
    name: 'SalesOrderList',
    component: () => import('@/views/sales/OrderList.vue'),
    meta: { requiresAuth: true, roles: ['sales_office'] }
  },
  {
    path: '/sales/inventory',
    name: 'Inventory',
    component: () => import('@/views/sales/Inventory.vue'),
    meta: { requiresAuth: true, roles: ['sales_office'] }
  },
  {
    path: '/sales/refund',
    name: 'Refund',
    component: () => import('@/views/sales/Refund.vue'),
    meta: { requiresAuth: true, roles: ['sales_office'] }
  },
  {
    path: '/sales/delivery-locations',
    name: 'DeliveryLocations',
    component: () => import('@/views/sales/DeliveryLocations.vue'),
    meta: { requiresAuth: true, roles: ['sales_office'] }
  },
  {
    path: '/sales/stats',
    name: 'SalesStats',
    component: () => import('@/views/sales/Stats.vue'),
    meta: { requiresAuth: true, roles: ['sales_office'] }
  },
  
  {
    path: '/user/shop',
    name: 'Shop',
    component: () => import('@/views/user/Shop.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'general'] }
  },
  {
    path: '/user/cart',
    name: 'Cart',
    component: () => import('@/views/user/Cart.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'general'] }
  },
  {
    path: '/user/orders',
    name: 'Orders',
    component: () => import('@/views/user/Orders.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'general'] }
  },
  {
    path: '/user/points',
    name: 'Points',
    component: () => import('@/views/user/Points.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'general'] }
  },
  {
    path: '/user/vouchers',
    name: 'UserVouchers',
    component: () => import('@/views/user/Vouchers.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'general'] }
  },
  {
    path: '/user/profile',
    name: 'Profile',
    component: () => import('@/views/user/Profile.vue'),
    meta: { requiresAuth: true }
  },
  
  {
    path: '/tailor/register',
    name: 'VoucherRegister',
    component: () => import('@/views/tailor/VoucherRegister.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'tailor_company'] }
  },
  {
    path: '/tailor/vouchers',
    name: 'VoucherList',
    component: () => import('@/views/tailor/VoucherList.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'tailor_company'] }
  },
  
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
  } else if (to.meta.roles && !to.meta.roles.includes(authStore.userRole)) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
