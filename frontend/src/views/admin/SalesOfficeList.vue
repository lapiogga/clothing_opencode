<template>
  <div class="sales-office-list">
    <div class="page-header">
      <h1>피복판매소 관리</h1>
      <button class="btn btn-primary" @click="openModal()">
        + 판매소 등록
      </button>
    </div>

    <Table
      :columns="columns"
      :data="salesOffices"
      :loading="loading"
    >
      <template #row="{ item }">
        <td>{{ item.code }}</td>
        <td>{{ item.name }}</td>
        <td>{{ item.address }}</td>
        <td>{{ item.phone }}</td>
        <td>{{ item.managerName || '-' }}</td>
        <td>
          <span :class="['status-badge', item.status]">
            {{ item.status === 'active' ? '운영중' : '운영중지' }}
          </span>
        </td>
        <td class="actions">
          <button class="btn btn-sm btn-outline" @click="openModal(item)">수정</button>
          <button class="btn btn-sm btn-danger" @click="deleteOffice(item)">삭제</button>
        </td>
      </template>
    </Table>

    <Modal v-if="showModal" :title="isEdit ? '판매소 수정' : '판매소 등록'" @close="closeModal">
      <form @submit.prevent="handleSubmit" class="office-form">
        <div class="form-row">
          <div class="form-group">
            <label>판매소 코드 <span class="required">*</span></label>
            <input v-model="form.code" type="text" required />
          </div>
          <div class="form-group">
            <label>판매소명 <span class="required">*</span></label>
            <input v-model="form.name" type="text" required />
          </div>
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
            <select v-model="form.status">
              <option value="active">운영중</option>
              <option value="inactive">운영중지</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>담당자명</label>
            <input v-model="form.managerName" type="text" />
          </div>
          <div class="form-group">
            <label>담당자 연락처</label>
            <input v-model="form.managerPhone" type="tel" />
          </div>
        </div>

        <div class="form-group">
          <label>운영시간</label>
          <input v-model="form.operatingHours" type="text" placeholder="09:00 - 18:00" />
        </div>

        <div class="form-group">
          <label>비고</label>
          <textarea v-model="form.notes" rows="3"></textarea>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" @click="closeModal">취소</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '저장 중...' : '저장' }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'
import Table from '@/components/common/Table.vue'
import Modal from '@/components/common/Modal.vue'

const salesOffices = ref([])
const loading = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)

const columns = [
  { key: 'code', label: '코드' },
  { key: 'name', label: '판매소명' },
  { key: 'address', label: '주소' },
  { key: 'phone', label: '연락처' },
  { key: 'manager', label: '담당자' },
  { key: 'status', label: '상태' },
  { key: 'actions', label: '관리' }
]

const form = reactive({
  code: '',
  name: '',
  address: '',
  phone: '',
  status: 'active',
  managerName: '',
  managerPhone: '',
  operatingHours: '',
  notes: ''
})

onMounted(() => {
  fetchSalesOffices()
})

async function fetchSalesOffices() {
  loading.value = true
  try {
    const response = await api.get('/sales-offices')
    salesOffices.value = response.data
  } catch (error) {
    console.error('Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

function openModal(office = null) {
  if (office) {
    isEdit.value = true
    editId.value = office.id
    Object.assign(form, {
      code: office.code,
      name: office.name,
      address: office.address,
      phone: office.phone || '',
      status: office.status,
      managerName: office.managerName || '',
      managerPhone: office.managerPhone || '',
      operatingHours: office.operatingHours || '',
      notes: office.notes || ''
    })
  } else {
    isEdit.value = false
    editId.value = null
    Object.assign(form, {
      code: '',
      name: '',
      address: '',
      phone: '',
      status: 'active',
      managerName: '',
      managerPhone: '',
      operatingHours: '',
      notes: ''
    })
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editId.value = null
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/sales-offices/${editId.value}`, form)
      alert('수정되었습니다.')
    } else {
      await api.post('/sales-offices', form)
      alert('등록되었습니다.')
    }
    closeModal()
    fetchSalesOffices()
  } catch (error) {
    alert('저장에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function deleteOffice(office) {
  if (!confirm(`"${office.name}"을(를) 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/sales-offices/${office.id}`)
    alert('삭제되었습니다.')
    fetchSalesOffices()
  } catch (error) {
    alert('삭제에 실패했습니다.')
  }
}
</script>

<style scoped>
.sales-office-list {
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

.office-form .form-group {
  margin-bottom: 16px;
}

.office-form label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
}

.office-form input,
.office-form select,
.office-form textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.required {
  color: #dc2626;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
