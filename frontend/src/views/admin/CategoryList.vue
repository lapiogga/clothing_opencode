<template>
  <div class="category-list">
    <div class="page-header">
      <h1>카테고리 관리</h1>
      <div class="header-actions">
        <button class="btn btn-outline" @click="downloadExcel">📥 엑셀 다운로드</button>
        <label class="btn btn-outline upload-btn">
          📤 엑셀 업로드
          <input type="file" @change="uploadExcel" accept=".xls,.xlsx" hidden />
        </label>
        <button class="btn btn-primary" @click="openModal()">+ 추가</button>
      </div>
    </div>

    <div class="category-tree">
      <div v-for="large in categoryTree" :key="large.id" class="category-group">
        <div class="category-level large">
          <span class="level-badge large">대</span>
          <span class="category-name">{{ large.name }}</span>
          <span class="category-type">{{ getTypeLabel(large.name) }}</span>
          <div class="category-actions">
            <button class="btn btn-sm btn-outline" @click="openModal(large)">수정</button>
            <button class="btn btn-sm btn-danger" @click="deleteCategory(large)">삭제</button>
          </div>
        </div>
        <template v-for="medium in large.children" :key="medium.id">
          <div class="category-level medium">
            <span class="level-badge medium">중</span>
            <span class="category-name">{{ medium.name }}</span>
            <div class="category-actions">
              <button class="btn btn-sm btn-outline" @click="openModal(medium)">수정</button>
              <button class="btn btn-sm btn-danger" @click="deleteCategory(medium)">삭제</button>
            </div>
          </div>
          <div v-for="small in medium.children" :key="small.id" class="category-level small">
            <span class="level-badge small">소</span>
            <span class="category-name">{{ small.name }}</span>
            <div class="category-actions">
              <button class="btn btn-sm btn-outline" @click="openModal(small)">수정</button>
              <button class="btn btn-sm btn-danger" @click="deleteCategory(small)">삭제</button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-if="categoryTree.length === 0" class="empty-state">
      <p>등록된 카테고리가 없습니다.</p>
      <p class="hint">엑셀 파일을 업로드하거나 직접 추가하세요.</p>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ isEdit ? '수정' : '추가' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="handleSubmit" class="category-form">
          <div class="form-group">
            <label>이름 <span class="required">*</span></label>
            <input v-model="form.name" type="text" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>레벨</label>
              <select v-model="form.level">
                <option value="large">대분류</option>
                <option value="medium">중분류</option>
                <option value="small">소분류</option>
              </select>
            </div>
          </div>
          <div class="form-group" v-if="form.level !== 'large'">
            <label>상위 카테고리</label>
            <select v-model="form.parent_id">
              <option :value="null">선택</option>
              <option v-for="p in parentOptions" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeModal">취소</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">저장</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/api'

const categoryTree = ref([])
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const form = reactive({
  name: '',
  level: 'large',
  parent_id: null,
  sort_order: 0
})

const parentOptions = computed(() => {
  const options = []
  if (form.level === 'medium') {
    for (const large of categoryTree.value) {
      options.push({ id: large.id, name: large.name })
    }
  } else if (form.level === 'small') {
    for (const large of categoryTree.value) {
      for (const medium of large.children || []) {
        options.push({ id: medium.id, name: `${large.name} > ${medium.name}` })
      }
    }
  }
  return options
})

onMounted(() => fetchCategories())

async function fetchCategories() {
  loading.value = true
  try {
    const res = await api.get('/categories/tree')
    categoryTree.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function getTypeLabel(name) {
  if (name === '완제품') return '완제품'
  if (name === '맞춤피복') return '맞춤피복'
  return ''
}

function openModal(category = null) {
  if (category) {
    isEdit.value = true
    editId.value = category.id
    Object.assign(form, {
      name: category.name,
      level: category.level,
      parent_id: category.parent_id,
      sort_order: category.sort_order || 0
    })
  } else {
    isEdit.value = false
    editId.value = null
    Object.assign(form, { name: '', level: 'large', parent_id: null, sort_order: 0 })
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/categories/${editId.value}`, form)
      alert('수정되었습니다.')
    } else {
      await api.post('/categories', form)
      alert('등록되었습니다.')
    }
    closeModal()
    fetchCategories()
  } catch (e) {
    alert(e.response?.data?.detail || '저장 실패')
  } finally {
    submitting.value = false
  }
}

async function deleteCategory(category) {
  if (!confirm(`"${category.name}" 삭제?`)) return
  try {
    await api.delete(`/categories/${category.id}`)
    alert('삭제되었습니다.')
    fetchCategories()
  } catch (e) {
    alert(e.response?.data?.detail || '삭제 실패')
  }
}

async function downloadExcel() {
  try {
    const res = await api.get('/categories/export', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = 'cloth_category.xls'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    alert('다운로드 실패')
  }
}

async function uploadExcel(event) {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await api.post('/categories/import', formData)
    alert(res.data.message)
    fetchCategories()
  } catch (e) {
    alert(e.response?.data?.detail || '업로드 실패')
  }
  event.target.value = ''
}
</script>

<style scoped>
.category-list { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }
.upload-btn { cursor: pointer; }
.category-tree { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.category-group { border-bottom: 1px solid #e5e7eb; }
.category-group:last-child { border-bottom: none; }
.category-level { display: flex; align-items: center; gap: 10px; padding: 12px 16px; }
.category-level.large { background: #f9fafb; }
.category-level.medium { padding-left: 40px; border-top: 1px solid #f3f4f6; }
.category-level.small { padding-left: 70px; border-top: 1px solid #f3f4f6; font-size: 13px; }
.category-name { flex: 1; font-weight: 500; }
.category-type { font-size: 11px; color: #6b7280; padding: 2px 8px; background: #f3f4f6; border-radius: 4px; }
.category-actions { display: flex; gap: 4px; }
.level-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.level-badge.large { background: #dbeafe; color: #1e40af; }
.level-badge.medium { background: #dcfce7; color: #166534; }
.level-badge.small { background: #fef3c7; color: #92400e; }
.empty-state { text-align: center; padding: 60px 20px; color: #6b7280; background: white; border-radius: 8px; }
.empty-state .hint { font-size: 13px; color: #9ca3af; margin-top: 8px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: white; border-radius: 8px; width: 100%; max-width: 400px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
.modal-header h2 { font-size: 16px; }
.close-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #6b7280; }
.category-form { padding: 20px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; margin-bottom: 4px; font-size: 13px; font-weight: 500; }
.form-group input, .form-group select { width: 100%; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.required { color: #dc2626; }
.form-actions { display: flex; justify-content: flex-end; gap: 8px; padding-top: 12px; border-top: 1px solid #e5e7eb; }
</style>
