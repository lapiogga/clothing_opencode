import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useOrderStore = defineStore('order', () => {
  const orders = ref([])
  const currentOrder = ref(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0
  })
  const filters = ref({
    status: null,
    startDate: null,
    endDate: null,
    search: ''
  })

  const orderList = computed(() => orders.value)

  const statusLabels = {
    pending: '주문대기',
    confirmed: '주문확인',
    preparing: '상품준비중',
    shipped: '배송중',
    delivered: '배송완료',
    cancelled: '주문취소',
    refunded: '반품완료'
  }

  async function fetchOrders(params = {}) {
    loading.value = true
    try {
      const queryParams = {
        ...filters.value,
        ...params,
        page: pagination.value.page,
        pageSize: pagination.value.pageSize
      }
      const response = await api.get('/orders', { params: queryParams })
      orders.value = response.data.items
      pagination.value.total = response.data.total
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchOrder(id) {
    loading.value = true
    try {
      const response = await api.get(`/orders/${id}`)
      currentOrder.value = response.data
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createOrder(orderData) {
    loading.value = true
    try {
      const response = await api.post('/orders', orderData)
      orders.value.unshift(response.data)
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateOrderStatus(id, status) {
    loading.value = true
    try {
      const response = await api.put(`/orders/${id}/status`, { status })
      const index = orders.value.findIndex(o => o.id === id)
      if (index !== -1) {
        orders.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function cancelOrder(id) {
    loading.value = true
    try {
      const response = await api.put(`/orders/${id}/cancel`)
      const index = orders.value.findIndex(o => o.id === id)
      if (index !== -1) {
        orders.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function requestRefund(id, refundData) {
    loading.value = true
    try {
      const response = await api.post(`/orders/${id}/refund`, refundData)
      const index = orders.value.findIndex(o => o.id === id)
      if (index !== -1) {
        orders.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  function setFilter(key, value) {
    filters.value[key] = value
    pagination.value.page = 1
  }

  function resetFilters() {
    filters.value = {
      status: null,
      startDate: null,
      endDate: null,
      search: ''
    }
    pagination.value.page = 1
  }

  function setPage(page) {
    pagination.value.page = page
  }

  function getStatusLabel(status) {
    return statusLabels[status] || status
  }

  return {
    orders,
    currentOrder,
    loading,
    pagination,
    filters,
    orderList,
    statusLabels,
    fetchOrders,
    fetchOrder,
    createOrder,
    updateOrderStatus,
    cancelOrder,
    requestRefund,
    setFilter,
    resetFilters,
    setPage,
    getStatusLabel
  }
})
