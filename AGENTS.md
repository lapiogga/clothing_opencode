# AGENTS.md

> AI 코딩 에이전트를 위한 피복 구매관리 시스템 프로젝트 가이드라인

## 프로젝트 개요

군 피복 구매관리 시스템 - FastAPI + Vue 3 + Vite + Pinia + SQLite/PostgreSQL

## 실행 명령어

### Backend (FastAPI)

```bash
cd backend

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행 (SQLite)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# DB 초기화 및 시드 데이터
python init_db.py

# 프로덕션용 (PostgreSQL)
DATABASE_URL="postgresql://user:pass@host:5432/db" uvicorn app.main:app --host 0.0.0.0 --port $PORT

# 테스트
pytest                                    # 전체 테스트
pytest tests/test_users.py               # 단일 파일
pytest tests/test_users.py::test_create_user -v  # 단일 테스트

# 린트/포맷
black . && isort .                        # 코드 포맷
flake8                                    # 린트 검사
```

### Frontend (Vue 3 + Vite)

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 (프록시로 백엔드 연결)
npm run dev

# 프로덕션 빌드
npm run build

# 테스트
npm run test                              # 전체 테스트
npm run test -- src/stores/user.spec.js   # 단일 파일
npm run test -- -t "fetchUsers"           # 테스트 이름으로 실행
```

### 배포

```bash
# Frontend (Vercel)
cd frontend && vercel --prod

# Backend (Render)
# render.yaml 파일로 Blueprint 배포 또는 웹에서 수동 배포
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy 2.0+, SQLite(개발)/PostgreSQL(프로덕션) |
| Frontend | Vue 3 (Composition API), Vite, Pinia |
| 인증 | JWT Token (python-jose) |
| HTTP | Axios |
| 배포 | Vercel (Frontend) + Render (Backend) + Supabase (DB) |

## 환경변수

### Backend (.env)
```bash
DATABASE_URL=postgresql://postgres.REF:PASSWORD@host.pooler.supabase.com:6543/postgres
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (.env.production)
```bash
VITE_API_URL=https://your-backend.onrender.com
```

## 코드 스타일 가이드

### Python (Backend)

```python
"""파일 헤더 - 모든 주요 파일에 한국어 설명 추가"""

# Import 순서: 표준 → 서드파티 → 로컬
from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, UserRole
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse, UserListResponse

router = APIRouter()

# 타입 힌트 필수, response_model 사용
@router.get("", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> UserListResponse:
    service = UserService(db)
    return service.get_list(page=page, page_size=page_size)

# 에러 처리: ValueError → HTTPException 변환
@router.post("", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    try:
        return service.create(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# 권한 체크: Depends로 의존성 주입
def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한 없음")
    return current_user
```

### Service Layer 패턴 (필수)

```python
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_list(self, page: int, page_size: int) -> dict:
        query = self.db.query(User)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "items": [self._to_response(u) for u in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def create(self, user_data: UserCreate) -> User:
        if self.get_by_username(user_data.username):
            raise ValueError("이미 존재하는 사용자명입니다")
        user = User(**user_data.model_dump())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _to_response(self, user: User) -> UserResponse:
        """모델 → 스키마 변환"""
        return UserResponse(
            id=user.id,
            username=user.username,
            name=user.name,
            service_number=user.service_number,
            role=user.role
        )
```

### Pydantic Schema 패턴

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# 생성용
class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)
    name: str = Field(..., min_length=2, max_length=50)
    service_number: str = Field(..., pattern=r"^\d{2}-\d{6}$")

# 응답용
class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    service_number: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy 모델 변환용

# 목록용
class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
```

### Vue (Frontend) - Composition API

```vue
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'

const store = useUserStore()
const items = ref([])
const loading = ref(false)
const error = ref(null)

// computed 사용
const hasItems = computed(() => items.value.length > 0)

onMounted(() => fetchItems())

async function fetchItems() {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/endpoint')
    items.value = res.data.items || res.data
  } catch (e) {
    console.error('Error:', e)
    error.value = e.response?.data?.detail || '데이터를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-if="loading">로딩중...</div>
  <div v-else-if="error" class="error">{{ error }}</div>
  <div v-else-if="hasItems">
    <!-- 목록 렌더링 -->
  </div>
  <div v-else>데이터가 없습니다.</div>
</template>
```

### Pinia Store 패턴

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  // State
  const users = ref([])
  const loading = ref(false)
  const pagination = ref({ page: 1, pageSize: 10, total: 0 })
  const error = ref(null)

  // Getters
  const hasUsers = computed(() => users.value.length > 0)

  // Actions
  async function fetchUsers(params = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await api.get('/users', { params })
      users.value = res.data.items
      pagination.value = {
        page: res.data.page,
        pageSize: res.data.page_size,
        total: res.data.total
      }
    } catch (e) {
      error.value = e.response?.data?.detail || '사용자 목록을 불러오지 못했습니다.'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { users, loading, pagination, error, hasUsers, fetchUsers }
})
```

## 데이터베이스 규칙

### 필드명 규칙

| 사용 | 비권장 | 설명 |
|------|--------|------|
| `service_number` | ~~employee_id~~ | 군번 (필수, 패턴: `\d{2}-\d{6}`) |
| `unit` | ~~department~~ | 소속 |
| `current_point` | ~~points~~ | 보유 포인트 |
| `rank_id` | - | 계급 FK |

### DB 연결 (database.py)

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 환경변수에서 DB URL (PostgreSQL 우선, 없으면 SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clothing.db")

# PostgreSQL 연결 문자열 변환
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
```

## API 설계 규칙

### 엔드포인트

```
/api/auth/*              # 인증
/api/users/*             # 사용자 관리 (admin)
/api/users/search        # 사용자 검색 (admin, sales_office, tailor_company)
/api/orders/*            # 주문 (사용자용)
/api/sales/*             # 판매 관리 (판매소용)
/api/inventory/*         # 재고
/api/points/*            # 포인트
/api/tailor-vouchers/*   # 체척권
/api/delivery-locations  # 배송지 관리
/api/stats/dashboard     # 대시보드 통계 (역할별)
/api/stats/sales         # 판매 통계 (판매소)
/api/menus/*             # 메뉴 관리
```

### 응답 형식

```python
# 목록: { items: [...], total: N, page: N, page_size: N }
# 단일: { id: 1, name: "...", ... }
# 생성 성공: { id: 1, ... } (201 Created)
# 수정/삭제 성공: { "message": "처리되었습니다" }
# 에러: { "detail": "에러 메시지" }
```

### 역할별 접근 제어

| 엔드포인트 | admin | sales_office | tailor_company | general |
|-----------|-------|--------------|----------------|---------|
| /api/users/* | ✅ | ❌ | ❌ | ❌ |
| /api/users/search | ✅ | ✅ | ✅ | ❌ |
| /api/sales/orders | ✅ | ✅ | ❌ | ❌ |
| /api/orders | ❌ | ❌ | ❌ | ✅ |
| /api/tailor-vouchers/* | ✅ | ❌ | ✅ | ✅ (자신만) |

## 프론트엔드 규칙

### 디렉토리 구조

```
views/
├── admin/        # 군수담당자 (UserList, PointGrant, ClothingList, TailorCompanyList)
├── sales/        # 판매소 (OrderList, Inventory, OfflineSale, Refund, Stats, DeliveryLocations)
├── tailor/       # 체척업체 (VoucherList, VoucherRegister)
└── user/         # 일반사용자 (Shop, Orders, Points, Vouchers, Profile)
```

### UI 원칙

- 컴팩트 리스트, 모달로 편집
- 색상: Primary `#3b82f6`, Success `#16a34a`, Danger `#dc2626`, Warning `#f59e0b`
- 로딩 상태 표시 필수
- 에러 메시지 사용자 친화적

## 파일 생성 체크리스트

- [ ] 한국어 주석/문서 추가
- [ ] 타입 힌트 사용 (Python), Composition API (Vue)
- [ ] 올바른 필드명 사용 (service_number, unit, current_point)
- [ ] 역할 기반 접근 제어 확인 (check_admin, get_current_user)
- [ ] 에러 처리: try/catch, ValueError → HTTPException
- [ ] response_model 지정
- [ ] 테스트 코드 작성

## 테스트 계정

| ID | 비밀번호 | 역할 |
|----|---------|------|
| admin | admin123 | admin |
| sales1 | sales123 | sales_office |
| tailor1 | tailor123 | tailor_company |
| user01 | user123 | general |
