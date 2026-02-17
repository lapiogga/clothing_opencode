# AGENTS.md

> AI 코딩 에이전트를 위한 피복 구매관리 시스템 프로젝트 가이드라인

## 프로젝트 개요

군 피복 구매관리 시스템 - FastAPI + Vue 3 + Vite + Pinia + SQLite

### 핵심 특징

- 다중 역할 기반 접근 제어 (4가지 역할)
- 포인트 기반 피복 구매 시스템
- 온라인/오프라인 판매 통합 관리
- 체척권(맞춤피복) 관리

## 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| Backend | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | SQLite | 3.x |
| Frontend | Vue 3 | 3.4+ |
| Build | Vite | 5.x |
| State | Pinia | 2.x |
| Router | Vue Router | 4.x |
| HTTP | Axios | 1.x |

## 실행 명령어

### Backend

```bash
cd backend

# 의존성 설치
pip install -r requirements.txt

# DB 초기화
python init_db.py

# 개발 서버 실행 (포트 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행 (포트 5173)
npm run dev

# 빌드
npm run build
```

## 코드 스타일 가이드

### Python (Backend)

```python
# 파일 헤더 - 모든 주요 파일에 한국어 설명 추가
"""
사용자 관련 라우터
- 로그인, 사용자 CRUD, 진급 처리
"""

# Import 순서
from datetime import datetime, date               # 1. 표준 라이브러리
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException  # 2. 서드파티
from sqlalchemy.orm import Session, joinedload

from app.database import get_db                   # 3. 로컬 모듈
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

# 타입 힌트 필수 사용
def get_user(user_id: int, db: Session) -> Optional[User]:
    ...

# Enum 값 비교
if user.role == UserRole.ADMIN.value:  # .value 사용
    ...

# 응답 데이터 구성 함수 패턴
def _build_order_response(order: Order) -> dict:
    """주문 응답 데이터 구성"""
    return {
        "id": order.id,
        "order_number": order.order_number,
        ...
    }
```

### Vue (Frontend)

```vue
<!-- 컴포넌트 구조 -->
<template>
  <div class="page">
    <h1>페이지 제목</h1>
    <!-- 내용 -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

// 상태
const items = ref([])
const loading = ref(false)

// 계산된 속성
const filteredItems = computed(() => {
  return items.value.filter(...)
})

// 라이프사이클
onMounted(() => {
  fetchItems()
})

// 메서드
async function fetchItems() {
  loading.value = true
  try {
    const res = await api.get('/endpoint')
    items.value = res.data.items || res.data
  } catch (e) {
    console.error('Error:', e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 컴포넌트 스코프 스타일 */
.page {
  padding: 20px;
}
</style>
```

## 데이터베이스 규칙

### 필드 네이밍

| 사용 | 비권장 | 설명 |
|------|--------|------|
| `service_number` | ~~employee_id~~ | 군번 |
| `unit` | ~~department~~ | 소속 |
| `current_point` | ~~points~~ | 보유 포인트 |
| `rank_id` | - | 계급 FK |
| `sales_office_id` | - | 판매소 FK |
| `tailor_company_id` | - | 체척업체 FK |

### 필수 필드

- `service_number`: 모든 사용자 필수 (NULL 불가)
- `enlistment_date`: 복무년수 계산용
- `rank_id`: 포인트 계산용

### 관계 매핑

```python
# User -> Rank
user.rank.name  # 계급명

# Order -> User -> Rank
order.user.rank.name  # 주문자 계급

# OrderItem -> Item, Spec
item.item.name    # 품목명
item.spec.size    # 규격
```

## API 설계 규칙

### 엔드포인트 구조

```
/api/auth/*           # 인증
/api/users/*          # 사용자 관리 (admin)
/api/categories/*     # 카테고리
/api/clothings/*      # 품목
/api/inventory/*      # 재고
/api/orders/*         # 주문 (사용자용)
/api/sales/*          # 판매 관리 (판매소용)
/api/delivery-locations/*  # 배송지
/api/points/*         # 포인트
/api/tailor-vouchers/* # 체척권
/api/sales-offices/*  # 판매소
```

### 응답 형식

```python
# 목록 응답
{
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [...]
}

# 단일 응답
{
    "id": 1,
    "name": "...",
    ...
}

# 성공 메시지
{"message": "처리되었습니다", "id": 1}
```

### 역할별 접근 제어

| 엔드포인트 | admin | sales_office | tailor_company | general |
|-----------|-------|--------------|----------------|---------|
| /api/users/* | ✅ | ❌ | ❌ | ❌ |
| /api/sales/orders | ✅ | ✅ (자신 판매소) | ❌ | ❌ |
| /api/orders | ❌ | ❌ | ❌ | ✅ (자신 주문) |
| /api/tailor-vouchers | ✅ | ❌ | ✅ | ✅ (자신 것) |

## 프론트엔드 규칙

### 페이지 구조

```
views/
├── admin/        # 군수담당자
│   ├── UserList.vue
│   ├── PointGrant.vue
│   ├── ClothingList.vue
│   └── ...
├── sales/        # 판매소
│   ├── OrderList.vue
│   ├── Inventory.vue
│   ├── OfflineSale.vue
│   └── Refund.vue
├── tailor/       # 체척업체
│   ├── VoucherList.vue
│   └── VoucherRegister.vue
└── user/         # 일반사용자
    ├── Shop.vue
    ├── Orders.vue
    ├── Points.vue
    └── Profile.vue
```

### UI 디자인 원칙

1. **컴팩트한 리스트 디자인**: 그리드보다는 리스트 형태 선호
2. **아코디언/펼침**: 상세 정보는 펼쳐서 보기
3. **모달**: 편집/상세는 모달로 처리
4. **색상 코드**:
   - Primary: `#3b82f6` (파랑)
   - Success: `#16a34a` (초록)
   - Danger: `#dc2626` (빨강)
   - Warning: `#f59e0b` (주황)

### API 호출 패턴

```javascript
// 올바른 필드명 사용
const res = await api.get('/sales/orders', {
  params: { 
    sales_office_id: auth.user?.sales_office_id  // O
    // employeeId: ...  ✗
  }
})

// 응답 데이터 처리
const orders = res.data.items || res.data
```

## 비즈니스 로직

### 포인트 계산

```python
# 연간 포인트 = 기본 포인트 + 복무년수 보너스
annual_point = rank.annual_point + (rank.service_year_bonus * user.service_years)

# 진급 시 일할계산
remaining_days = (year_end - promotion_date).days
daily_rate = point_diff / 365
adjustment = daily_rate * remaining_days
```

### 주문 플로우

```
1. 주문 생성
   └─> reserved_point 증가
   └─> reserved_quantity 증가

2. 배송 완료
   └─> current_point 차감
   └─> reserved_point 차감
   └─> quantity 차감
   └─> reserved_quantity 차감

3. 주문 취소
   └─> reserved_point 차감

4. 반품
   └─> current_point 증가
   └─> quantity 증가
```

### 체척권 상태

| 상태 | 설명 | 전이 가능 |
|------|------|-----------|
| issued | 발급 | → registered, cancelled |
| registered | 등록 | → used |
| used | 사용완료 | - |
| cancelled | 취소 | - |
| expired | 만료 | - |

## 테스트 계정

| ID | 비밀번호 | 역할 | sales_office_id | tailor_company_id |
|----|---------|------|-----------------|-------------------|
| admin | admin123 | admin | null | null |
| sales1 | sales123 | sales_office | 1 | null |
| tailor1 | tailor123 | tailor_company | null | 1 |
| user01 | user123 | general | null | null |

## 변경 이력

### 2024년 (최신)

1. **필드 네이밍 통일**
   - `employee_id` → `service_number` (군번)
   - `department` → `unit` (소속)
   - `points` → `current_point` (보유포인트)
   - `position` → `rank.name` (계급)

2. **포인트 시스템**
   - `points` 컬럼 → `points` (규격별 포인트)
   - 판매가/포인트가 분리 제거 → 포인트만 사용

3. **API 구조**
   - `/api/orders` (사용자용) / `/api/sales/orders` (판매소용) 분리
   - `/api/tailor-vouchers` 엔드포인트 정리

4. **프론트엔드 리팩토링**
   - 컴팩트 리스트 디자인 적용
   - 필드명 백엔드와 일치하도록 수정

## 파일 생성 시 체크리스트

- [ ] 한국어 주석/문서 추가
- [ ] 타입 힌트 사용 (Python)
- [ ] 스코프 스타일 사용 (Vue)
- [ ] 올바른 필드명 사용 (service_number, unit, current_point)
- [ ] 역할 기반 접근 제어 확인
- [ ] 에러 처리 및 사용자 메시지

## 문제 해결 가이드

### 데이터가 안 보일 때

1. API 응답 필드명 확인 (`res.data.items` vs `res.data`)
2. 백엔드에서 `joinedload`로 관계 데이터 로드 확인
3. 프론트엔드 필드명과 백엔드 응답 필드명 일치 확인

### 권한 오류

1. 사용자 역할 확인 (`current_user.role`)
2. 판매소/체척업체 ID 확인
3. 엔드포인트별 권한 체크 로직 확인

### 포인트 계산 오류

1. 계급(`rank`) 로드 확인
2. 입대일(`enlistment_date`) 확인
3. `service_years` 계산 로직 확인
