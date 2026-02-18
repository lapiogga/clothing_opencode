<template>
  <div class="search-filter">
    <div class="search-input">
      <input
        :value="searchValue"
        type="text"
        :placeholder="searchPlaceholder"
        @input="handleSearchInput"
        @keyup.enter="handleSearch"
      />
      <button class="search-btn" @click="handleSearch">검색</button>
    </div>

    <div class="filters">
      <div v-for="filter in filters" :key="filter.key" class="filter-group">
        <label>{{ filter.label }}</label>
        <select
          :value="filterValues[filter.key]"
          @change="handleFilterChange(filter.key, $event.target.value)"
        >
          <option
            v-for="option in filter.options"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  searchPlaceholder: {
    type: String,
    default: '검색어를 입력하세요'
  },
  filters: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['search', 'filter-change', 'update:modelValue'])

const searchValue = ref('')
const filterValues = reactive({})

watch(() => props.modelValue, (newVal) => {
  if (newVal.search !== undefined) {
    searchValue.value = newVal.search
  }
  Object.assign(filterValues, newVal)
}, { immediate: true })

let searchTimeout
function handleSearchInput(event) {
  searchValue.value = event.target.value
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    emit('search', searchValue.value)
  }, 300)
}

function handleSearch() {
  emit('search', searchValue.value)
}

function handleFilterChange(key, value) {
  // select의 value는 항상 문자열이므로 "null" → null, "true"/"false" → boolean 변환
  let parsedValue = value
  if (value === 'null' || value === '') {
    parsedValue = null
  } else if (value === 'true') {
    parsedValue = true
  } else if (value === 'false') {
    parsedValue = false
  }
  
  filterValues[key] = parsedValue
  emit('filter-change', key, parsedValue)
  emit('update:modelValue', { search: searchValue.value, ...filterValues })
}
</script>

<style scoped>
.search-filter {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.search-input {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.search-input input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.search-input input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-btn {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.search-btn:hover {
  background: #2563eb;
}

.filters {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  color: #6b7280;
}

.filter-group select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  min-width: 120px;
}

.filter-group select:focus {
  outline: none;
  border-color: #3b82f6;
}
</style>
