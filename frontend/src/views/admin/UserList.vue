<template>
  <div class="user-list">
    <div class="page-header">
      <h1>사용자 관리</h1>
      <button class="btn btn-primary" @click="openCreateModal">
        + 사용자 등록
      </button>
    </div>

    <SearchFilter
      :search-placeholder="'이름, 사번, 부서 검색'"
      :filters="searchFilters"
      @search="handleSearch"
      @filter-change="handleFilterChange"
    />

    <Table
      :columns="columns"
      :data="userStore.users"
      :loading="userStore.loading"
      :empty-message="'등록된 사용자가 없습니다'"
    >
      <template #row="{ item }">
        <td>{{ item.service_number || '-' }}</td>
        <td>{{ item.name }}</td>
        <td>{{ item.unit || '-' }}</td>
        <td>{{ item.rank?.name || '-' }}</td>
        <td>
          <span :class="['role-badge', item.role]">
            {{ getRoleLabel(item.role) }}
          </span>
        </td>
        <td>{{ item.current_point?.toLocaleString() }}P</td>
        <td>
          <span :class="['status-badge', item.is_active ? 'active' : 'inactive']">
            {{ item.is_active ? '활성' : '비활성' }}
          </span>
        </td>
        <td class="actions">
          <button class="btn btn-sm btn-outline" @click="editUser(item)">수정</button>
          <button class="btn btn-sm btn-danger" @click="deleteUser(item)">삭제</button>
        </td>
      </template>
    </Table>

    <Pagination
      :current-page="userStore.pagination.page"
      :total-pages="totalPages"
      :total-items="userStore.pagination.total"
      @page-change="handlePageChange"
    />

    <UserForm
      v-if="showForm"
      :user="selectedUser"
      @close="closeForm"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import SearchFilter from '@/components/common/SearchFilter.vue'
import Table from '@/components/common/Table.vue'
import Pagination from '@/components/common/Pagination.vue'
import UserForm from './UserForm.vue'

const userStore = useUserStore()

const showForm = ref(false)
const selectedUser = ref(null)
const searchQuery = ref('')
const roleFilter = ref(null)
const statusFilter = ref(null)

const columns = [
  { key: 'service_number', label: '군번' },
  { key: 'name', label: '이름' },
  { key: 'unit', label: '소속' },
  { key: 'rank', label: '계급' },
  { key: 'role', label: '권한' },
  { key: 'current_point', label: '포인트' },
  { key: 'is_active', label: '상태' },
  { key: 'actions', label: '관리' }
]

const searchFilters = [
  {
    key: 'role',
    label: '권한',
    options: [
      { value: null, label: '전체' },
      { value: 'admin', label: '관리자' },
      { value: 'general', label: '일반사용자' },
      { value: 'sales_office', label: '판매소' },
      { value: 'tailor_company', label: '체척업체' }
    ]
  },
  {
    key: 'is_active',
    label: '상태',
    options: [
      { value: null, label: '전체' },
      { value: true, label: '활성' },
      { value: false, label: '비활성' }
    ]
  }
]

const totalPages = computed(() => {
  return userStore.pagination.totalPages || Math.ceil(userStore.pagination.total / userStore.pagination.pageSize)
})

onMounted(() => {
  fetchUsers()
})

async function fetchUsers() {
  const params = {
    keyword: searchQuery.value,
    page: userStore.pagination.page,
    page_size: userStore.pagination.pageSize,
  }
  if (roleFilter.value) params.role = roleFilter.value
  if (statusFilter.value !== null) params.is_active = statusFilter.value
  
  await userStore.fetchUsers(params)
}

function handleSearch(query) {
  searchQuery.value = query
  userStore.pagination.page = 1
  fetchUsers()
}

function handleFilterChange(key, value) {
  if (key === 'role') roleFilter.value = value
  if (key === 'is_active') statusFilter.value = value
  userStore.pagination.page = 1
  fetchUsers()
}

function handlePageChange(page) {
  userStore.pagination.page = page
  fetchUsers()
}

function openCreateModal() {
  selectedUser.value = null
  showForm.value = true
}

function editUser(user) {
  selectedUser.value = { ...user }
  showForm.value = true
}

async function deleteUser(user) {
  if (!confirm(`${user.name}님을 삭제하시겠습니까?`)) return
  try {
    await userStore.deleteUser(user.id)
    alert('삭제되었습니다.')
  } catch (error) {
    alert('삭제에 실패했습니다.')
  }
}

function closeForm() {
  showForm.value = false
  selectedUser.value = null
}

async function handleSave(userData) {
  try {
    if (selectedUser.value) {
      await userStore.updateUser(selectedUser.value.id, userData)
      alert('수정되었습니다.')
    } else {
      await userStore.createUser(userData)
      alert('등록되었습니다.')
    }
    closeForm()
    fetchUsers()
  } catch (error) {
    alert('저장에 실패했습니다.')
  }
}

function getRoleLabel(role) {
  const labels = {
    admin: '관리자',
    general: '일반사용자',
    sales_office: '판매소',
    tailor_company: '체척업체'
  }
  return labels[role] || role
}

function formatPoints(points) {
  return points ? points.toLocaleString() + 'P' : '0P'
}
</script>

<style scoped>
.user-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.role-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.role-badge.admin {
  background: #fef3c7;
  color: #92400e;
}

.role-badge.general {
  background: #dbeafe;
  color: #1e40af;
}

.role-badge.sales_office {
  background: #dcfce7;
  color: #166534;
}

.role-badge.tailor_company {
  background: #f3e8ff;
  color: #7c3aed;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.active {
  background: #dcfce7;
  color: #166534;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #dc2626;
}

.actions {
  display: flex;
  gap: 8px;
}
</style>
