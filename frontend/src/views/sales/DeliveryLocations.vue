<template>
  <div class="delivery-locations">
    <div class="page-header">
      <h1>배송지 관리</h1>
      <button class="btn btn-primary" @click="openCreateModal">+ 배송지 등록</button>
    </div>

    <div v-if="loading" class="loading">로딩 중...</div>

    <div v-else-if="locations.length === 0" class="empty-state">
      <p>등록된 배송지가 없습니다.</p>
      <p class="hint">새 배송지를 등록하여 직접 배송 서비스를 이용하세요.</p>
    </div>

    <div v-else class="location-list">
      <div v-for="loc in locations" :key="loc.id" class="location-card">
        <div class="location-header">
          <h3>{{ loc.name }}</h3>
          <div class="location-actions">
            <button class="btn btn-sm btn-outline" @click="openEditModal(loc)">수정</button>
            <button class="btn btn-sm btn-danger" @click="deleteLocation(loc)">삭제</button>
          </div>
        </div>
        <div class="location-body">
          <div class="info-row">
            <span class="label">주소</span>
            <span class="value">{{ loc.address }}</span>
          </div>
          <div v-if="loc.contact_person" class="info-row">
            <span class="label">담당자</span>
            <span class="value">{{ loc.contact_person }}</span>
          </div>
          <div v-if="loc.contact_phone" class="info-row">
            <span class="label">연락처</span>
            <span class="value">{{ loc.contact_phone }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 배송지 등록/수정 모달 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingLocation ? '배송지 수정' : '배송지 등록' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>배송지명 <span class="required">*</span></label>
            <input type="text" v-model="form.name" placeholder="예: 본부중대" />
          </div>
          <div class="form-group">
            <label>주소 <span class="required">*</span></label>
            <input type="text" v-model="form.address" placeholder="예: 서울특별시 용산구 본부중대" />
          </div>
          <div class="form-group">
            <label>담당자</label>
            <input type="text" v-model="form.contact_person" placeholder="담당자명" />
          </div>
          <div class="form-group">
            <label>연락처</label>
            <input type="tel" v-model="form.contact_phone" placeholder="02-0000-0000" />
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">취소</button>
          <button class="btn btn-primary" @click="submitForm" :disabled="!canSubmit || submitting">
            {{ submitting ? '처리 중...' : (editingLocation ? '수정' : '등록') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const loading = ref(false)
const submitting = ref(false)
const locations = ref([])
const showModal = ref(false)
const editingLocation = ref(null)

const form = ref({
  name: '',
  address: '',
  contact_person: '',
  contact_phone: '',
})

const canSubmit = computed(() => {
  return form.value.name.trim() && form.value.address.trim()
})

onMounted(() => {
  fetchLocations()
})

async function fetchLocations() {
  loading.value = true
  try {
    const salesOfficeId = authStore.user?.sales_office_id
    const res = await api.get('/delivery-locations', {
      params: { sales_office_id: salesOfficeId }
    })
    locations.value = res.data || []
  } catch (error) {
    console.error('Failed to fetch locations:', error)
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  editingLocation.value = null
  form.value = {
    name: '',
    address: '',
    contact_person: '',
    contact_phone: '',
  }
  showModal.value = true
}

function openEditModal(location) {
  editingLocation.value = location
  form.value = {
    name: location.name,
    address: location.address,
    contact_person: location.contact_person || '',
    contact_phone: location.contact_phone || '',
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingLocation.value = null
}

async function submitForm() {
  if (!canSubmit.value) return
  
  submitting.value = true
  try {
    const salesOfficeId = authStore.user?.sales_office_id
    const data = {
      ...form.value,
      sales_office_id: salesOfficeId,
    }
    
    if (editingLocation.value) {
      await api.put(`/delivery-locations/${editingLocation.value.id}`, data)
      alert('배송지가 수정되었습니다.')
    } else {
      await api.post('/delivery-locations', data)
      alert('배송지가 등록되었습니다.')
    }
    
    closeModal()
    fetchLocations()
  } catch (error) {
    alert(error.response?.data?.detail || '처리에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function deleteLocation(location) {
  if (!confirm(`"${location.name}" 배송지를 삭제하시겠습니까?`)) return
  
  try {
    await api.delete(`/delivery-locations/${location.id}`)
    alert('배송지가 삭제되었습니다.')
    fetchLocations()
  } catch (error) {
    alert(error.response?.data?.detail || '삭제에 실패했습니다.')
  }
}
</script>

<style scoped>
.delivery-locations {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
}

.empty-state p {
  margin-bottom: 8px;
  color: #6b7280;
}

.empty-state .hint {
  font-size: 13px;
  color: #9ca3af;
}

.location-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.location-card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.location-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.location-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.location-actions {
  display: flex;
  gap: 8px;
}

.location-body {
  padding: 16px 20px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  width: 70px;
  font-size: 13px;
  color: #6b7280;
  flex-shrink: 0;
}

.info-row .value {
  font-size: 14px;
  color: #1f2937;
}

/* Modal */
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
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
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

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.form-group .required {
  color: #dc2626;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Buttons */
.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
}

.btn-outline {
  background: white;
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.btn-outline:hover {
  background: #eff6ff;
}

.btn-danger {
  background: white;
  color: #dc2626;
  border: 1px solid #dc2626;
}

.btn-danger:hover {
  background: #fef2f2;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}
</style>
