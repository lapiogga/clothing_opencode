<template>
  <div class="table-container">
    <table class="data-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="{ width: col.width }"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody v-if="loading">
        <tr>
          <td :colspan="columns.length" class="loading-cell">
            <div class="loading-spinner"></div>
            <span>로딩 중...</span>
          </td>
        </tr>
      </tbody>
      <tbody v-else-if="data.length === 0">
        <tr>
          <td :colspan="columns.length" class="empty-cell">
            {{ emptyMessage }}
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr v-for="(item, index) in data" :key="item.id || index">
          <slot name="row" :item="item" :index="index">
            <td v-for="col in columns" :key="col.key">
              {{ item[col.key] }}
            </td>
          </slot>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  columns: {
    type: Array,
    required: true
  },
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  emptyMessage: {
    type: String,
    default: '데이터가 없습니다'
  }
})
</script>

<style scoped>
.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  padding: 14px 16px;
  text-align: left;
  background: #f9fafb;
  font-weight: 500;
  font-size: 13px;
  color: #6b7280;
  border-bottom: 1px solid #e5e7eb;
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
}

.data-table tbody tr:hover {
  background: #f9fafb;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 60px 20px !important;
  color: #9ca3af;
}

.loading-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
