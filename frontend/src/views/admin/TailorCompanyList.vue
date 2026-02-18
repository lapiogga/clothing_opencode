<template>
  <div class="tailor-company-list">
    <div class="page-header">
      <h1>체척업체 관리</h1>
      <button class="btn btn-primary" @click="openModal()">
        + 업체 등록
      </button>
    </div>

    <Table
      :columns="columns"
      :data="companies"
      :loading="loading"
    >
      <template #row="{ item }">
        <td>{{ item.code }}</td>
        <td>{{ item.name }}</td>
        <td>{{ item.business_number || '-' }}</td>
        <td>{{ item.address }}</td>
        <td>{{ item.phone }}</td>
        <td>{{ item.manager_name || '-' }}</td>
        <td>
          <span :class="['status-badge', item.is_active ? 'active' : 'inactive']">
            {{ item.is_active ? '운영중' : '운영중지' }}
          </span>
        </td>
        <td class="actions">
          <button class="btn btn-sm btn-outline" @click="openModal(item)">수정</button>
          <button class="btn btn-sm btn-danger" @click="deleteCompany(item)">삭제</button>
        </td>
      </template>
    </Table>

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ isEdit ? '업체 수정' : '업체 등록' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="handleSubmit" class="company-form">
          <div class="form-row">
            <div class="form-group">
              <label>업체 코드 <span class="required">*</span></label>
              <input v-model="form.code" type="text" required />
            </div>
            <div class="form-group">
              <label>업체명 <span class="required">*</span></label>
              <input v-model="form.name" type="text" required />
            </div>
          </div>

          <div class="form-group">
            <label>사업자등록번호</label>
            <input v-model="form.business_number" type="text" placeholder="123-45-67890" />
          </div>

          <div class="form-group">
            <label>주소 <span class="required">*</span></label>
            <input v-model="form.address" type="text" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>연락처</label>
              <input v-model="form.phone" type="tel" />
            </div>
            <div class="form-group">
              <label>운영상태</label>
              <select v-model="form.is_active">
                <option :value="true">운영중</option>
                <option :value="false">운영중지</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>담당자명</label>
              <input v-model="form.manager_name" type="text" />
            </div>
            <div class="form-group">
              <label>담당자 연락처</label>
              <input v-model="form.manager_phone" type="tel" />
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeModal">취소</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              {{ submitting ? '저장 중...' : '저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'
import Table from '@/components/common/Table.vue'

const companies = ref([])
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const columns = [
  { key: 'code', label: '업체코드' },
  { key: 'name', label: '업체명' },
  { key: 'business_number', label: '사업자번호' },
  { key: 'address', label: '주소' },
  { key: 'phone', label: '연락처' },
  { key: 'manager_name', label: '담당자' },
  { key: 'is_active', label: '상태' },
  { key: 'actions', label: '관리' }
]

const form = reactive({
  code: '',
  name: '',
  business_number: '',
  address: '',
  phone: '',
  manager_name: '',
  manager_phone: '',
  is_active: true
})

onMounted(() => fetchCompanies())

async function fetchCompanies() {
  loading.value = true
  try {
    const res = await api.get('/tailor-vouchers/companies')
    companies.value = res.data
  } catch (e) {
    console.error('Failed to fetch companies:', e)
  } finally {
    loading.value = false
  }
}

function openModal(item = null) {
  if (item) {
    isEdit.value = true
    editId.value = item.id
    Object.assign(form, {
      code: item.code,
      name: item.name,
      business_number: item.business_number || '',
      address: item.address,
      phone: item.phone || '',
      manager_name: item.manager_name || '',
      manager_phone: item.manager_phone || '',
      is_active: item.is_active
    })
  } else {
    isEdit.value = false
    editId.value = null
    Object.assign(form, {
      code: '',
      name: '',
      business_number: '',
      address: '',
      phone: '',
      manager_name: '',
      manager_phone: '',
      is_active: true
    })
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  isEdit.value = false
  editId.value = null
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/tailor-vouchers/companies/${editId.value}`, form)
      alert('수정되었습니다.')
    } else {
      await api.post('/tailor-vouchers/companies', form)
      alert('등록되었습니다.')
    }
    closeModal()
    fetchCompanies()
  } catch (e) {
    alert(e.response?.data?.detail || '저장에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function deleteCompany(item) {
  if (!confirm(`"${item.name}"을(를) 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/tailor-vouchers/companies/${item.id}`)
    alert('삭제되었습니다.')
    fetchCompanies()
  } catch (e) {
    alert(e.response?.data?.detail || '삭제에 실패했습니다.')
  }
}
</script>

<style scoped>
.tailor-company-list {
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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
}

.company-form {
  padding: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.required {
  color: #dc2626;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
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
  gap: 4px;
}
</style>
