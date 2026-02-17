import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useClothingStore = defineStore('clothing', () => {
  const categories = ref([])
  const products = ref([])
  const currentProduct = ref(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 12,
    total: 0
  })
  const filters = ref({
    category: null,
    search: '',
    type: 'all',
    size: null
  })

  const productList = computed(() => products.value)
  const categoryList = computed(() => categories.value)

  async function fetchCategories() {
    try {
      const response = await api.get('/categories')
      categories.value = response.data
      return response.data
    } catch (error) {
      throw error
    }
  }

  async function createCategory(categoryData) {
    loading.value = true
    try {
      const response = await api.post('/categories', categoryData)
      categories.value.push(response.data)
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateCategory(id, categoryData) {
    loading.value = true
    try {
      const response = await api.put(`/categories/${id}`, categoryData)
      const index = categories.value.findIndex(c => c.id === id)
      if (index !== -1) {
        categories.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteCategory(id) {
    loading.value = true
    try {
      await api.delete(`/categories/${id}`)
      categories.value = categories.value.filter(c => c.id !== id)
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchProducts(params = {}) {
    loading.value = true
    try {
      const queryParams = {
        ...filters.value,
        ...params,
        page: pagination.value.page,
        pageSize: pagination.value.pageSize
      }
      const response = await api.get('/clothings', { params: queryParams })
      products.value = response.data.items
      pagination.value.total = response.data.total
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchProduct(id) {
    loading.value = true
    try {
      const response = await api.get(`/clothings/${id}`)
      currentProduct.value = response.data
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createProduct(productData) {
    loading.value = true
    try {
      const response = await api.post('/clothings', productData)
      products.value.push(response.data)
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateProduct(id, productData) {
    loading.value = true
    try {
      const response = await api.put(`/clothings/${id}`, productData)
      const index = products.value.findIndex(p => p.id === id)
      if (index !== -1) {
        products.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteProduct(id) {
    loading.value = true
    try {
      await api.delete(`/clothings/${id}`)
      products.value = products.value.filter(p => p.id !== id)
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
      category: null,
      search: '',
      type: 'all',
      size: null
    }
    pagination.value.page = 1
  }

  function setPage(page) {
    pagination.value.page = page
  }

  return {
    categories,
    products,
    currentProduct,
    loading,
    pagination,
    filters,
    productList,
    categoryList,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    fetchProducts,
    fetchProduct,
    createProduct,
    updateProduct,
    deleteProduct,
    setFilter,
    resetFilters,
    setPage
  }
})
