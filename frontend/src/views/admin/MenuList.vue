<template>
  <div class="menu-list">
    <div class="page-header">
      <h1>화면 관리</h1>
      <div class="header-actions">
        <button class="btn btn-outline" @click="initializeMenus">기본 메뉴 초기화</button>
        <button class="btn btn-primary" @click="openModal()">+ 메뉴 등록</button>
      </div>
    </div>

    <div class="menu-tree">
      <div v-for="menu in menus" :key="menu.id" class="menu-item-wrapper">
        <div class="menu-row" :class="{ category: menu.is_category }">
          <div class="menu-info">
            <span class="menu-name">{{ menu.name }}</span>
            <span v-if="menu.path" class="menu-path">{{ menu.path }}</span>
            <span :class="['status-badge', menu.is_active ? 'active' : 'inactive']">
              {{ menu.is_active ? '활성' : '비활성' }}
            </span>
          </div>
          <div class="menu-roles">
            <span v-for="role in menu.allowed_roles" :key="role" class="role-tag">
              {{ getRoleLabel(role) }}
            </span>
          </div>
          <div class="menu-actions">
            <button class="btn btn-sm btn-outline" @click="openModal(menu)">수정</button>
            <button class="btn btn-sm btn-danger" @click="deleteMenu(menu)">삭제</button>
          </div>
        </div>
        <div v-if="menu.children && menu.children.length > 0" class="menu-children">
          <div v-for="child in menu.children" :key="child.id" class="menu-row child">
            <div class="menu-info">
              <span class="menu-name">└ {{ child.name }}</span>
              <span v-if="child.path" class="menu-path">{{ child.path }}</span>
              <span :class="['status-badge', child.is_active ? 'active' : 'inactive']">
                {{ child.is_active ? '활성' : '비활성' }}
              </span>
            </div>
            <div class="menu-roles">
              <span v-for="role in child.allowed_roles" :key="role" class="role-tag">
                {{ getRoleLabel(role) }}
              </span>
            </div>
            <div class="menu-actions">
              <button class="btn btn-sm btn-outline" @click="openModal(child)">수정</button>
              <button class="btn btn-sm btn-danger" @click="deleteMenu(child)">삭제</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ isEdit ? '메뉴 수정' : '메뉴 등록' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="handleSubmit" class="menu-form">
          <div class="form-group">
            <label>메뉴명 <span class="required">*</span></label>
            <input v-model="form.name" type="text" required />
          </div>

          <div class="form-group">
            <label>경로</label>
            <input v-model="form.path" type="text" placeholder="/admin/..." />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>상위 메뉴</label>
              <select v-model="form.parent_id">
                <option :value="null">없음 (대분류)</option>
                <option v-for="menu in parentMenus" :key="menu.id" :value="menu.id">
                  {{ menu.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>정렬 순서</label>
              <input v-model.number="form.sort_order" type="number" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>대분류 여부</label>
              <select v-model="form.is_category">
                <option :value="true">대분류</option>
                <option :value="false">하위 메뉴</option>
              </select>
            </div>
            <div class="form-group">
              <label>활성 상태</label>
              <select v-model="form.is_active">
                <option :value="true">활성</option>
                <option :value="false">비활성</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>접근 권한</label>
            <div class="role-checkboxes">
              <label v-for="role in allRoles" :key="role.value" class="checkbox-label">
                <input type="checkbox" :value="role.value" v-model="form.allowed_roles" />
                {{ role.label }}
              </label>
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
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/api'

const menus = ref([])
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const allRoles = [
  { value: 'admin', label: '군수담당자' },
  { value: 'sales_office', label: '판매소담당자' },
  { value: 'tailor_company', label: '체척업체담당자' },
  { value: 'general', label: '일반사용자' }
]

const form = reactive({
  name: '',
  path: '',
  parent_id: null,
  sort_order: 0,
  is_category: false,
  is_active: true,
  allowed_roles: []
})

const parentMenus = computed(() => menus.value.filter(m => m.is_category))

onMounted(() => fetchMenus())

async function fetchMenus() {
  loading.value = true
  try {
    const res = await api.get('/menus/tree/all')
    menus.value = res.data
  } catch (e) {
    console.error('Failed to fetch menus:', e)
  } finally {
    loading.value = false
  }
}

function openModal(item = null) {
  if (item) {
    isEdit.value = true
    editId.value = item.id
    Object.assign(form, {
      name: item.name,
      path: item.path || '',
      parent_id: item.parent_id,
      sort_order: item.sort_order,
      is_category: item.is_category,
      is_active: item.is_active,
      allowed_roles: [...(item.allowed_roles || [])]
    })
  } else {
    isEdit.value = false
    editId.value = null
    Object.assign(form, {
      name: '',
      path: '',
      parent_id: null,
      sort_order: 0,
      is_category: false,
      is_active: true,
      allowed_roles: []
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
      await api.put(`/menus/${editId.value}`, form)
      alert('수정되었습니다.')
    } else {
      await api.post('/menus', form)
      alert('등록되었습니다.')
    }
    closeModal()
    fetchMenus()
  } catch (e) {
    alert(e.response?.data?.detail || '저장에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function deleteMenu(item) {
  if (!confirm(`"${item.name}" 메뉴를 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/menus/${item.id}`)
    alert('삭제되었습니다.')
    fetchMenus()
  } catch (e) {
    alert(e.response?.data?.detail || '삭제에 실패했습니다.')
  }
}

async function initializeMenus() {
  if (!confirm('기본 메뉴를 초기화하시겠습니까?\n기존 메뉴가 있다면 건너뜁니다.')) return
  try {
    await api.post('/menus/initialize')
    alert('기본 메뉴가 초기화되었습니다.')
    fetchMenus()
  } catch (e) {
    alert(e.response?.data?.detail || '초기화에 실패했습니다.')
  }
}

function getRoleLabel(role) {
  const roleMap = {
    admin: '군수담당자',
    sales_office: '판매소',
    tailor_company: '체척업체',
    general: '일반사용자'
  }
  return roleMap[role] || role
}
</script>

<style scoped>
.menu-list {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.menu-tree {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.menu-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.menu-row.category {
  background: #f9fafb;
  font-weight: 600;
}

.menu-row.child {
  padding-left: 40px;
  background: #fff;
}

.menu-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-name {
  font-size: 14px;
}

.menu-path {
  font-size: 12px;
  color: #6b7280;
  font-family: monospace;
}

.menu-roles {
  display: flex;
  gap: 4px;
  margin-right: 16px;
}

.role-tag {
  padding: 2px 8px;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 4px;
  font-size: 11px;
}

.menu-actions {
  display: flex;
  gap: 4px;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.status-badge.active {
  background: #dcfce7;
  color: #166534;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #dc2626;
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
  max-width: 500px;
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

.menu-form {
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

.role-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}
</style>
