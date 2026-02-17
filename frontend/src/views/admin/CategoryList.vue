<template>
  <div class="category-list">
    <div class="page-header">
      <h1>카테고리 관리</h1>
      <button class="btn btn-primary" @click="openModal()">
        + 카테고리 추가
      </button>
    </div>

    <div class="category-grid">
      <div
        v-for="category in clothingStore.categories"
        :key="category.id"
        class="category-card"
      >
        <div class="category-info">
          <h3>{{ category.name }}</h3>
          <p class="description">{{ category.description || '설명 없음' }}</p>
          <div class="meta">
            <span>품목 수: {{ category.productCount || 0 }}</span>
            <span>순서: {{ category.sortOrder }}</span>
          </div>
        </div>
        <div class="category-actions">
          <button class="btn btn-sm btn-outline" @click="openModal(category)">수정</button>
          <button
            class="btn btn-sm btn-danger"
            @click="deleteCategory(category)"
            :disabled="category.productCount > 0"
          >
            삭제
          </button>
        </div>
      </div>
    </div>

    <div v-if="clothingStore.categories.length === 0" class="empty-state">
      <p>등록된 카테고리가 없습니다.</p>
    </div>

    <Modal v-if="showModal" :title="isEdit ? '카테고리 수정' : '카테고리 추가'" @close="closeModal">
      <form @submit.prevent="handleSubmit" class="category-form">
        <div class="form-group">
          <label>카테고리명 <span class="required">*</span></label>
          <input v-model="form.name" type="text" placeholder="카테고리명 입력" required />
        </div>

        <div class="form-group">
          <label>설명</label>
          <textarea v-model="form.description" placeholder="카테고리 설명" rows="3"></textarea>
        </div>

        <div class="form-group">
          <label>정렬 순서</label>
          <input v-model.number="form.sortOrder" type="number" min="0" placeholder="0" />
        </div>

        <div class="form-group">
          <label>피복 타입</label>
          <select v-model="form.type">
            <option value="ready_made">완제품</option>
            <option value="custom">맞춤피복</option>
            <option value="both">공통</option>
          </select>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" @click="closeModal">취소</button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? '저장 중...' : '저장' }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useClothingStore } from '@/stores/clothing'
import Modal from '@/components/common/Modal.vue'

const clothingStore = useClothingStore()

const showModal = ref(false)
const isEdit = ref(false)
const loading = ref(false)
const editId = ref(null)

const form = reactive({
  name: '',
  description: '',
  sortOrder: 0,
  type: 'both'
})

onMounted(() => {
  clothingStore.fetchCategories()
})

function openModal(category = null) {
  if (category) {
    isEdit.value = true
    editId.value = category.id
    Object.assign(form, {
      name: category.name,
      description: category.description || '',
      sortOrder: category.sortOrder || 0,
      type: category.type || 'both'
    })
  } else {
    isEdit.value = false
    editId.value = null
    Object.assign(form, {
      name: '',
      description: '',
      sortOrder: 0,
      type: 'both'
    })
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editId.value = null
}

async function handleSubmit() {
  loading.value = true
  try {
    if (isEdit.value) {
      await clothingStore.updateCategory(editId.value, { ...form })
      alert('수정되었습니다.')
    } else {
      await clothingStore.createCategory({ ...form })
      alert('등록되었습니다.')
    }
    closeModal()
  } catch (error) {
    alert('저장에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

async function deleteCategory(category) {
  if (category.productCount > 0) {
    alert('품목이 등록된 카테고리는 삭제할 수 없습니다.')
    return
  }
  if (!confirm(`"${category.name}" 카테고리를 삭제하시겠습니까?`)) return
  
  try {
    await clothingStore.deleteCategory(category.id)
    alert('삭제되었습니다.')
  } catch (error) {
    alert('삭제에 실패했습니다.')
  }
}
</script>

<style scoped>
.category-list {
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

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.category-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.category-info h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
}

.meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #9ca3af;
}

.category-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.category-form .form-group {
  margin-bottom: 16px;
}

.category-form label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
}

.category-form input,
.category-form select,
.category-form textarea {
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
  margin-top: 24px;
}
</style>
