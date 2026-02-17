import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])
  const loading = ref(false)

  const cartItems = computed(() => items.value)
  const itemCount = computed(() => items.value.length)
  const totalAmount = computed(() => {
    return items.value.reduce((sum, item) => {
      const price = item.product.salePrice || item.product.price
      return sum + (price * item.quantity)
    }, 0)
  })
  const totalPoints = computed(() => {
    return items.value.reduce((sum, item) => {
      return sum + (item.product.pointPrice * item.quantity)
    }, 0)
  })

  async function fetchCart() {
    loading.value = true
    try {
      const response = await api.get('/cart')
      items.value = response.data
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function addToCart(product, quantity = 1, options = {}) {
    loading.value = true
    try {
      const response = await api.post('/cart/items', {
        productId: product.id,
        quantity,
        ...options
      })
      const existingIndex = items.value.findIndex(
        item => item.product.id === product.id && 
        JSON.stringify(item.options) === JSON.stringify(options)
      )
      if (existingIndex !== -1) {
        items.value[existingIndex] = response.data
      } else {
        items.value.push(response.data)
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateCartItem(itemId, quantity) {
    loading.value = true
    try {
      const response = await api.put(`/cart/items/${itemId}`, { quantity })
      const index = items.value.findIndex(item => item.id === itemId)
      if (index !== -1) {
        items.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function removeFromCart(itemId) {
    loading.value = true
    try {
      await api.delete(`/cart/items/${itemId}`)
      items.value = items.value.filter(item => item.id !== itemId)
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function clearCart() {
    loading.value = true
    try {
      await api.delete('/cart')
      items.value = []
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  function getLocalCart() {
    const saved = localStorage.getItem('cart')
    if (saved) {
      items.value = JSON.parse(saved)
    }
    return items.value
  }

  function saveLocalCart() {
    localStorage.setItem('cart', JSON.stringify(items.value))
  }

  return {
    items,
    loading,
    cartItems,
    itemCount,
    totalAmount,
    totalPoints,
    fetchCart,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    getLocalCart,
    saveLocalCart
  }
})
