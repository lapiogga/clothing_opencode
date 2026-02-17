<template>
  <div class="pagination">
    <button
      class="page-btn"
      :disabled="currentPage === 1"
      @click="$emit('page-change', currentPage - 1)"
    >
      이전
    </button>
    
    <div class="page-numbers">
      <button
        v-for="page in displayedPages"
        :key="page"
        :class="['page-num', { active: page === currentPage }]"
        @click="$emit('page-change', page)"
      >
        {{ page }}
      </button>
    </div>
    
    <button
      class="page-btn"
      :disabled="currentPage === totalPages || totalPages === 0"
      @click="$emit('page-change', currentPage + 1)"
    >
      다음
    </button>

    <div v-if="totalItems" class="total-info">
      총 {{ totalItems }}개
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: {
    type: Number,
    default: 1
  },
  totalPages: {
    type: Number,
    default: 1
  },
  totalItems: {
    type: Number,
    default: 0
  }
})

defineEmits(['page-change'])

const displayedPages = computed(() => {
  const pages = []
  const start = Math.max(1, props.currentPage - 2)
  const end = Math.min(props.totalPages, props.currentPage + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 24px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.page-btn:disabled {
  background: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

.page-btn:not(:disabled):hover {
  background: #f9fafb;
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-num {
  width: 36px;
  height: 36px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.page-num.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.page-num:not(.active):hover {
  background: #f9fafb;
}

.total-info {
  font-size: 14px;
  color: #6b7280;
  margin-left: 16px;
}
</style>
