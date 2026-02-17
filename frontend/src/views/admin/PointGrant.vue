<template>
  <div class="point-grant">
    <div class="page-header">
      <h1>포인트 지급</h1>
    </div>

    <div class="grant-section">
      <div class="section-title">개별 지급</div>
      <form @submit.prevent="grantSingle" class="grant-form">
        <div class="form-row">
          <div class="form-group">
            <label>사용자 검색</label>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="사번 또는 이름으로 검색"
              @input="searchUsers"
            />
            <div v-if="searchResults.length > 0" class="search-results">
              <div
                v-for="user in searchResults"
                :key="user.id"
                class="search-item"
                @click="selectUser(user)"
              >
                {{ user.service_number || user.username }} - {{ user.name }} ({{ user.unit || user.role }})
              </div>
            </div>
          </div>
          <div v-if="selectedUser" class="selected-user">
            <span>{{ selectedUser.name }} ({{ selectedUser.unit || selectedUser.service_number || selectedUser.username }})</span>
            <span class="current-points">현재 포인트: {{ selectedUser.current_point?.toLocaleString() }}P (사용가능: {{ selectedUser.available_point?.toLocaleString() }}P)</span>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>지급 금액 <span class="required">*</span></label>
            <input v-model.number="singleAmount" type="number" min="1" required />
          </div>
          <div class="form-group">
            <label>지급 사유 <span class="required">*</span></label>
            <select v-model="singleReason" required>
              <option value="">선택하세요</option>
              <option value="annual">연간 지급</option>
              <option value="promotion">승진 축하</option>
              <option value="compensation">보상</option>
              <option value="correction">정정</option>
              <option value="other">기타</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>상세 사유</label>
          <textarea v-model="singleNote" rows="2" placeholder="상세 사유 입력"></textarea>
        </div>

        <button type="submit" class="btn btn-primary" :disabled="!selectedUser || submitting">
          지급하기
        </button>
      </form>
    </div>

    <div class="grant-section">
      <div class="section-title">일괄 지급</div>
      <form @submit.prevent="grantBulk" class="grant-form">
        <div class="form-row">
          <div class="form-group">
            <label>대상 선택</label>
            <select v-model="bulkTarget">
              <option value="all">전체 사용자</option>
              <option value="department">특정 부서</option>
              <option value="position">특정 직급</option>
            </select>
          </div>
          <div v-if="bulkTarget === 'department'" class="form-group">
            <label>부서명</label>
            <input v-model="bulkDepartment" type="text" placeholder="부서명 입력" />
          </div>
          <div v-if="bulkTarget === 'position'" class="form-group">
            <label>직급</label>
            <input v-model="bulkPosition" type="text" placeholder="직급 입력" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>지급 금액 <span class="required">*</span></label>
            <input v-model.number="bulkAmount" type="number" min="1" required />
          </div>
          <div class="form-group">
            <label>지급 사유 <span class="required">*</span></label>
            <select v-model="bulkReason" required>
              <option value="">선택하세요</option>
              <option value="annual">연간 지급</option>
              <option value="bonus">보너스</option>
              <option value="other">기타</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>상세 사유</label>
          <textarea v-model="bulkNote" rows="2" placeholder="상세 사유 입력"></textarea>
        </div>

        <button type="submit" class="btn btn-primary" :disabled="submitting">
          일괄 지급하기
        </button>
      </form>
    </div>

    <div class="history-section">
      <div class="section-title">최근 지급 내역</div>
      <Table :columns="historyColumns" :data="recentHistory" :loading="historyLoading">
        <template #row="{ item }">
          <td>{{ formatDate(item.createdAt) }}</td>
          <td>{{ item.user?.name }} ({{ item.user?.unit || item.user?.employeeId || item.user?.id }})</td>
          <td class="amount">+{{ item.amount?.toLocaleString() }}P</td>
          <td>{{ getReasonLabel(item.reason) }}</td>
          <td>{{ item.note || '-' }}</td>
          <td>{{ item.grantedBy?.name }}</td>
        </template>
      </Table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import Table from '@/components/common/Table.vue'

const searchQuery = ref('')
const searchResults = ref([])
const selectedUser = ref(null)
const singleAmount = ref(null)
const singleReason = ref('')
const singleNote = ref('')

const bulkTarget = ref('all')
const bulkDepartment = ref('')
const bulkPosition = ref('')
const bulkAmount = ref(null)
const bulkReason = ref('')
const bulkNote = ref('')

const submitting = ref(false)
const recentHistory = ref([])
const historyLoading = ref(false)

const historyColumns = [
  { key: 'date', label: '지급일' },
  { key: 'user', label: '사용자' },
  { key: 'amount', label: '지급액' },
  { key: 'reason', label: '사유' },
  { key: 'note', label: '상세' },
  { key: 'grantedBy', label: '지급자' }
]

onMounted(() => {
  fetchHistory()
})

let searchTimeout
async function searchUsers() {
  clearTimeout(searchTimeout)
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  
  searchTimeout = setTimeout(async () => {
    try {
      const response = await api.get('/users', {
        params: { keyword: searchQuery.value, page_size: 10 }
      })
      searchResults.value = response.data.items
    } catch (error) {
      console.error('Search failed:', error)
    }
  }, 300)
}

function selectUser(user) {
  selectedUser.value = user
  searchQuery.value = ''
  searchResults.value = []
}

async function grantSingle() {
  if (!selectedUser.value || !singleAmount.value || !singleReason.value) return
  
  submitting.value = true
  try {
    await api.post('/points/grant-single', {
      user_id: selectedUser.value.id,
      amount: singleAmount.value,
      reason: singleReason.value,
      note: singleNote.value
    })
    alert('포인트가 지급되었습니다.')
    selectedUser.value = null
    singleAmount.value = null
    singleReason.value = ''
    singleNote.value = ''
    fetchHistory()
  } catch (error) {
    alert(error.response?.data?.detail || '지급에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function grantBulk() {
  if (!bulkAmount.value || !bulkReason.value) return
  
  const confirmMsg = bulkTarget.value === 'all' 
    ? '전체 사용자에게 포인트를 지급하시겠습니까?'
    : `선택된 대상에게 포인트를 지급하시겠습니까?`
  
  if (!confirm(confirmMsg)) return
  
  submitting.value = true
  try {
    const payload = {
      target: bulkTarget.value,
      amount: bulkAmount.value,
      reason: bulkReason.value,
      note: bulkNote.value
    }
    
    if (bulkTarget.value === 'position' && bulkPosition.value) {
      payload.rank_id = parseInt(bulkPosition.value)
    }
    
    await api.post('/points/grant-bulk', payload)
    alert('일괄 지급이 완료되었습니다.')
    bulkAmount.value = null
    bulkReason.value = ''
    bulkNote.value = ''
    fetchHistory()
  } catch (error) {
    alert(error.response?.data?.detail || '일괄 지급에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const response = await api.get('/points/grant-history', { params: { page_size: 20 } })
    recentHistory.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch history:', error)
  } finally {
    historyLoading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

function getReasonLabel(reason) {
  const labels = {
    annual: '연간 지급',
    promotion: '승진 축하',
    compensation: '보상',
    correction: '정정',
    bonus: '보너스',
    other: '기타'
  }
  return labels[reason] || reason
}
</script>

<style scoped>
.point-grant {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.grant-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  margin-bottom: 16px;
  position: relative;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.search-item {
  padding: 10px 12px;
  cursor: pointer;
}

.search-item:hover {
  background: #f3f4f6;
}

.selected-user {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #f0fdf4;
  border-radius: 6px;
  margin-bottom: 16px;
}

.current-points {
  font-size: 13px;
  color: #166534;
}

.required {
  color: #dc2626;
}

.history-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.amount {
  color: #16a34a;
  font-weight: 600;
}
</style>
