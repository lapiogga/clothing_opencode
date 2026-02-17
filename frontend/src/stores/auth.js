/**
 * 인증 스토어 (Pinia)
 * 
 * 사용자 로그인, 로그아웃, 권한 관리를 담당
 * - 토큰 및 사용자 정보를 localStorage에 저장하여 세션 유지
 * - 역할 기반 접근 제어(RBAC) 지원
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // ============================================
  // 상태 (State)
  // ============================================
  
  /** JWT 액세스 토큰 */
  const token = ref(localStorage.getItem('token') || null)
  
  /** 현재 로그인한 사용자 정보 */
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // ============================================
  // 계산된 속성 (Computed)
  // ============================================
  
  /** 로그인 여부 */
  const isLoggedIn = computed(() => !!token.value)
  
  /** 현재 사용자 역할 */
  const userRole = computed(() => user.value?.role || null)

  // ============================================
  // 액션 (Actions)
  // ============================================
  
  /**
   * 로그인 처리
   * 
   * @param {string} username - 사용자 아이디
   * @param {string} password - 비밀번호
   * @returns {Object} - { success: boolean, message?: string }
   */
  async function login(username, password) {
    try {
      // 1. 로그인 API 호출하여 토큰 획득
      const response = await api.post('/auth/login', { username, password })
      const accessToken = response.data.access_token
      token.value = accessToken
      
      // 2. 토큰을 localStorage에 저장
      localStorage.setItem('token', accessToken)
      
      // 3. 사용자 정보 조회
      const userResponse = await api.get('/auth/me')
      user.value = userResponse.data
      
      // 4. 사용자 정보를 localStorage에 저장
      localStorage.setItem('user', JSON.stringify(userResponse.data))
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '로그인에 실패했습니다.' 
      }
    }
  }

  /**
   * 로그아웃 처리
   * - 토큰 및 사용자 정보 초기화
   * - localStorage에서 제거
   */
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  /**
   * 특정 역할 확인
   * 
   * @param {string} role - 확인할 역할 (admin, general, sales_office, tailor_company)
   * @returns {boolean}
   */
  function hasRole(role) {
    return user.value?.role === role
  }

  /**
   * 여러 역할 중 하나라도 가지고 있는지 확인
   * 
   * @param {string[]} roles - 확인할 역할 배열
   * @returns {boolean}
   */
  function hasAnyRole(roles) {
    return roles.includes(user.value?.role)
  }

  /**
   * 사용자 정보 새로고침
   * - 서버에서 최신 사용자 정보를 다시 가져옴
   */
  async function fetchUser() {
    if (!token.value) return
    
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(response.data))
    } catch (error) {
      // 토큰이 만료된 경우 로그아웃
      if (error.response?.status === 401) {
        logout()
      }
    }
  }

  return {
    // 상태
    token,
    user,
    // 계산된 속성
    isLoggedIn,
    userRole,
    // 액션
    login,
    logout,
    hasRole,
    hasAnyRole,
    fetchUser,
  }
})
