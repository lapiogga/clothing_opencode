# 개발자 가이드

> 군 피복 구매관리 시스템 개발 지침서

## 1. 개발 환경 설정

### 1.1 필수 요구사항

| 항목 | 버전 | 비고 |
|------|------|------|
| Python | 3.11+ | Backend |
| Node.js | 18+ | Frontend |
| npm | 9+ | 패키지 관리 |

### 1.2 Backend 설정

```bash
cd backend

# 가상환경 생성 (선택)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# DB 초기화 및 시드 데이터
python init_db.py

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 1.3 Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
```

### 1.4 접속 정보

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## 2. 프로젝트 구조

### 2.1 Backend 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 설정 (JWT secret, DB 경로)
│   ├── database.py          # DB 연결 (SQLAlchemy)
│   ├── models/              # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── base.py          # TimestampMixin
│   │   ├── user.py          # User, Rank
│   │   ├── clothing.py      # ClothingItem, ClothingSpec, Category
│   │   ├── order.py         # Order, OrderItem, Delivery
│   │   ├── point.py         # PointGrant, PointTransaction
│   │   ├── sales.py         # SalesOffice, Inventory, InventoryHistory
│   │   └── tailor.py        # TailorCompany, TailorVoucher
│   ├── schemas/             # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── clothing.py
│   │   ├── order.py
│   │   ├── point.py
│   │   ├── sales.py
│   │   └── tailor.py
│   ├── routers/             # API 라우터
│   │   ├── __init__.py
│   │   ├── auth.py          # /api/auth/*
│   │   ├── users.py         # /api/users/*
│   │   ├── clothings.py     # /api/clothings/*
│   │   ├── orders.py        # /api/orders/*
│   │   ├── sales.py         # /api/sales/*
│   │   ├── inventory.py     # /api/inventory/*
│   │   ├── points.py        # /api/points/*
│   │   ├── tailor.py        # /api/tailor-vouchers/*
│   │   ├── categories.py    # /api/categories/*
│   │   ├── sales_offices.py # /api/sales-offices/*
│   │   └── delivery.py      # /api/delivery-locations/*
│   ├── services/            # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── clothing_service.py
│   │   ├── order_service.py
│   │   ├── sales_service.py
│   │   ├── inventory_service.py
│   │   └── tailor_service.py
│   └── utils/               # 유틸리티
│       ├── __init__.py
│       └── auth.py          # JWT 인증
├── init_db.py               # DB 초기화
├── seed_data.py             # 시드 데이터
├── requirements.txt         # Python 의존성
└── clothing.db              # SQLite DB 파일
```

### 2.2 Frontend 구조

```
frontend/
├── src/
│   ├── main.js              # Vue 앱 진입점
│   ├── App.vue              # 루트 컴포넌트
│   ├── api/                 # Axios 인스턴스
│   │   └── index.js
│   ├── router/              # Vue Router 설정
│   │   └── index.js
│   ├── stores/              # Pinia 스토어
│   │   ├── auth.js          # 인증 상태
│   │   ├── cart.js          # 장바구니
│   │   ├── clothing.js      # 품목 상태
│   │   └── order.js         # 주문 상태
│   ├── components/          # 재사용 컴포넌트
│   │   ├── common/          # 공통 컴포넌트
│   │   │   ├── Pagination.vue
│   │   │   ├── SearchFilter.vue
│   │   │   └── Table.vue
│   │   └── layout/          # 레이아웃
│   │       ├── Header.vue
│   │       └── Sidebar.vue
│   └── views/               # 페이지 컴포넌트
│       ├── Login.vue
│       ├── Dashboard.vue
│       ├── admin/           # 군수담당자
│       │   ├── UserList.vue
│       │   ├── UserForm.vue
│       │   ├── CategoryList.vue
│       │   ├── ClothingList.vue
│       │   ├── PointGrant.vue
│       │   ├── SalesOfficeList.vue
│       │   └── TailorCompanyList.vue
│       ├── sales/           # 판매소 담당자
│       │   ├── OrderList.vue
│       │   ├── OfflineSale.vue
│       │   ├── Inventory.vue
│       │   ├── Refund.vue
│       │   └── Stats.vue
│       ├── tailor/          # 체척업체
│       │   ├── VoucherList.vue
│       │   └── VoucherRegister.vue
│       └── user/            # 일반사용자
│           ├── Shop.vue
│           ├── Cart.vue
│           ├── Orders.vue
│           ├── Points.vue
│           └── Profile.vue
├── index.html
├── package.json
└── vite.config.js
```

---

## 3. 코딩 컨벤션

### 3.1 Python (Backend)

#### 파일 헤더

```python
"""
파일 설명 - 모든 주요 파일에 한국어 설명 추가
"""
```

#### Import 순서

```python
# 1. 표준 라이브러리
from datetime import datetime, date
from typing import Optional, List

# 2. 서드파티
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 3. 로컬 모듈
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
```

#### 타입 힌트

```python
# 모든 함수에 타입 힌트 필수
def get_user(user_id: int, db: Session) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()
```

#### Enum 비교

```python
# Enum 값 비교 시 .value 사용
if current_user.role != UserRole.ADMIN.value:
    raise HTTPException(status_code=403, detail="권한 없음")
```

#### 에러 처리

```python
# ValueError → HTTPException 변환
try:
    user = service.create(user_data)
except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail=str(e)
    )
```

### 3.2 Vue (Frontend)

#### Composition API

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const items = ref([])
const loading = ref(false)

onMounted(() => fetchItems())

async function fetchItems() {
  loading.value = true
  try {
    const res = await api.get('/endpoint')
    items.value = res.data.items || res.data
  } catch (e) {
    console.error('Error:', e)
    alert('데이터를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}
</script>
```

#### 스타일 가이드

- **Scoped CSS 사용**: `<style scoped>`
- **색상 변수**: Primary `#3b82f6`, Success `#16a34a`, Danger `#dc2626`
- **한국어 라벨**: 모든 UI 텍스트는 한국어

---

## 4. 핵심 비즈니스 로직

### 4.1 피복 타입

| 타입 | Enum 값 | 설명 |
|------|---------|------|
| 완제품 | `ready_made` | 재고 관리 O, 규격 선택 |
| 맞춤피복 | `custom` | 재고 관리 X, 체척권 발행 |

### 4.2 주문 플로우

```
1. 사용자: 품목 선택 → 규격 선택 → 수량 → 배송정보
2. 주문 생성:
   - Order.status = PENDING
   - 재고: reserved_quantity 증가
   - 포인트: reserved_point 증가
3. 판매소 배송 처리:
   - status: PENDING → CONFIRMED → SHIPPED → DELIVERED
   - tracking_number 입력
4. 배송 완료:
   - 재고: quantity 차감, reserved_quantity 차감
   - 포인트: current_point 차감, reserved_point 차감
5. 수령 완료 (사용자):
   - status: DELIVERED → RECEIVED
```

### 4.3 맞춤피복 플로우

```
1. 사용자: 맞춤피복 선택 → "바로구매" 클릭
2. 체척권 발행 (POST /api/tailor-vouchers/issue-direct):
   - TailorVoucher 생성 (status = ISSUED)
   - 주문 생성 없이 체척권만 발행
3. 체척업체 등록:
   - 체척권 번호로 등록
   - status: ISSUED → REGISTERED
```

### 4.4 오프라인 판매 플로우

```
1. 판매소 담당자: 사용자 검색 → 품목 선택 → 수량
2. 판매 완료 (POST /api/sales/offline):
   - Order 생성 (order_type = OFFLINE, status = DELIVERED)
   - 포인트 즉시 차감
   - 재고 즉시 차감
```

---

## 5. 주요 API 엔드포인트

### 5.1 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/auth/login | 로그인 |
| GET | /api/auth/me | 현재 사용자 정보 |

### 5.2 쇼핑 (일반사용자)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/inventory/available | 구매 가능 재고 |
| GET | /api/clothings/custom/available | 맞춤피복 목록 |
| POST | /api/orders | 주문 생성 |
| POST | /api/tailor-vouchers/issue-direct | 체척권 직접 발행 |

### 5.3 판매 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/sales/orders | 주문 목록 |
| PUT | /api/sales/orders/{id}/status | 주문 상태 변경 |
| POST | /api/sales/offline | 오프라인 판매 |
| POST | /api/sales/refund | 반품 처리 |

### 5.4 재고 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/inventory | 재고 목록 |
| POST | /api/inventory/adjust | 재고 조정 |
| POST | /api/inventory/receive | 재고 입고 |

---

## 6. 데이터베이스 필드 네이밍

| 사용 | 비권장 | 설명 |
|------|--------|------|
| `service_number` | ~~employee_id~~ | 군번 (필수) |
| `unit` | ~~department~~ | 소속 |
| `current_point` | ~~points~~ | 보유 포인트 |
| `rank_id` | - | 계급 FK |
| `sales_office_id` | - | 판매소 FK |
| `clothing_type` | - | 피복 타입 (ready_made/custom) |

---

## 7. 테스트 계정

| ID | 비밀번호 | 역할 | 군번 |
|----|---------|------|------|
| admin | admin123 | admin | 20-123456 |
| sales1 | sales123 | sales_office | 30-100001 |
| sales2 | sales123 | sales_office | 30-100002 |
| tailor1 | tailor123 | tailor_company | 40-200001 |
| user01 | user123 | general | 21-100001 |

---

## 8. 최근 변경사항 (2025-02)

### 8.1 Shop.vue 리팩토링

**변경 내용:**
- 품목 단위로 그룹화하여 표시 (규격별 개별 표시 → 품목별 카드)
- 완제품: 팝업에서 규격 선택 후 주문
- 맞춤피복: "바로구매" 클릭 시 체척권 즉시 발행

**관련 파일:**
- `frontend/src/views/user/Shop.vue`

### 8.2 OfflineSale.vue 신규 생성

**기능:**
- 사용자 검색 팝업
- 상품 그리드 표시
- 장바구니 관리
- 포인트 차감 판매

**관련 파일:**
- `frontend/src/views/sales/OfflineSale.vue`

### 8.3 맞춤피복 자동 규격 생성

**변경 내용:**
- 품목 등록 시 clothing_type이 'custom'이면 자동으로 '맞춤' 규격 생성
- 맞춤피복은 규격 추가/삭제 버튼 숨김

**관련 파일:**
- `backend/app/services/clothing_service.py`
- `frontend/src/views/admin/ClothingList.vue`

### 8.4 체척권 직접 발행 API

**신규 엔드포인트:**
```
POST /api/tailor-vouchers/issue-direct
```

**요청 본문:**
```json
{
  "user_id": 1,
  "item_id": 8,
  "amount": 1,
  "sales_office_id": 1,
  "notes": "맞춤피복 체척권 발행"
}
```

**관련 파일:**
- `backend/app/routers/tailor.py`
- `backend/app/services/tailor_service.py`
- `backend/app/schemas/tailor.py`

---

## 9. 문제 해결 가이드

### 9.1 포트 충돌

```bash
# 8000 포트 사용 중인 프로세스 확인
lsof -i :8000

# 5173 포트 사용 중인 프로세스 확인
lsof -i :5173
```

### 9.2 DB 초기화

```bash
cd backend
rm clothing.db
python init_db.py
```

### 9.3 프론트엔드 빌드 에러

```bash
cd frontend
rm -rf node_modules
npm install
npm run build
```

### 9.4 JWT 토큰 만료

- 토큰 만료 시간: 24시간
- 만료 시 재로그인 필요

---

## 10. 참고 문서

- [프로젝트 기획서](project-plan.md)
- [API 명세서](api-spec.md)
- [DB 스키마](db-schema.md)
- [화면설계서](ui-design.md)
- [AGENTS.md](../AGENTS.md) - AI 코딩 에이전트 가이드라인
