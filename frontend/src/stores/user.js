import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  const users = ref([])
  const currentUser = ref(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0
  })

  const userList = computed(() => users.value)

  async function fetchUsers(params = {}) {
    loading.value = true
    try {
      const response = await api.get('/users', { params })
      users.value = response.data.items
      pagination.value = {
        page: response.data.page || params.page || 1,
        pageSize: response.data.page_size || params.page_size || 10,
        total: response.data.total || 0,
        totalPages: response.data.total_pages || 1
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchUser(id) {
    loading.value = true
    try {
      const response = await api.get(`/users/${id}`)
      currentUser.value = response.data
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createUser(userData) {
    loading.value = true
    try {
      const response = await api.post('/users', userData)
      users.value.push(response.data)
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateUser(id, userData) {
    loading.value = true
    try {
      const response = await api.put(`/users/${id}`, userData)
      const index = users.value.findIndex(u => u.id === id)
      if (index !== -1) {
        users.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteUser(id) {
    loading.value = true
    try {
      await api.delete(`/users/${id}`)
      users.value = users.value.filter(u => u.id !== id)
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  function reset() {
    users.value = []
    currentUser.value = null
    pagination.value = { page: 1, pageSize: 10, total: 0 }
  }

  return {
    users,
    currentUser,
    loading,
    pagination,
    userList,
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deleteUser,
    reset
  }
})
