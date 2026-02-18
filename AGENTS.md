# AGENTS.md

> AI 코딩 에이전트를 위한 피복 구매관리 시스템 프로젝트 가이드라인

## 프로젝트 개요

군 피복 구매관리 시스템 - FastAPI + Vue 3 + Vite + Pinia + SQLite

## 실행 명령어

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt      # 의존성 설치
python init_db.py                    # DB 초기화 및 시드 데이터
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # 개발 서버

# 테스트 (pytest 설치 후)
pytest                               # 전체 테스트
pytest tests/test_users.py           # 단일 파일
pytest tests/test_users.py::test_create_user -v  # 단일 테스트

# 린트/포맷 (black, isort 설치 후)
black . && isort .                   # 코드 포맷
flake8                               # 린트 검사
```

### Frontend (Vue 3 + Vite)

```bash
cd frontend
npm install                          # 의존성 설치
npm run dev                          # 개발 서버 (포트 3000)
npm run build                        # 프로덕션 빌드

# 테스트 (vitest 설치 후)
npm run test                         # 전체 테스트
npm run test -- src/stores/user.spec.js  # 단일 파일
npm run test -- -t "fetchUsers"      # 테스트 이름으로 실행
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy 2.0+, SQLite |
| Frontend | Vue 3 (Composition API), Vite, Pinia |
| 인증 | JWT Token (python-jose) |
| HTTP | Axios |

## 코드 스타일 가이드

### Python (Backend)

```python
"""파일 헤더 - 모든 주요 파일에 한국어 설명 추가"""

# Import 순서: 표준 → 서드파티 → 로컬
from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.services.user_service import UserService

router = APIRouter()

# 타입 힌트 필수, Enum 비교 시 .value 사용
@router.get("", response_model=UserListResponse)
def get_users(page: int = Query(1, ge=1), db: Session = Depends(get_db)) -> UserListResponse:
    service = UserService(db)
    return service.get_list(page=page)

# 에러 처리: ValueError → HTTPException 변환
@router.post("")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    try:
        return service._to_response(service.create(user_data))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# 권한 체크: Depends로 의존성 주입
def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한 없음")
    return current_user
```

### Service Layer 패턴

```python
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, user_data: UserCreate) -> User:
        if self.get_by_username(user_data.username):
            raise ValueError("이미 존재하는 사용자명입니다")
        user = User(...)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _to_response(self, user: User) -> UserResponse:
        """모델 → 스키마 변환"""
        return UserResponse(id=user.id, name=user.name, ...)
```

### Vue (Frontend) - Composition API

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'

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

### Pinia Store 패턴

```javascript
export const useUserStore = defineStore('user', () => {
  const users = ref([])
  const loading = ref(false)
  const pagination = ref({ page: 1, pageSize: 10, total: 0 })

  async function fetchUsers(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/users', { params })
      users.value = res.data.items
      pagination.value = { page: res.data.page, pageSize: res.data.page_size, total: res.data.total }
    } finally {
      loading.value = false
    }
  }
  return { users, loading, pagination, fetchUsers }
})
```

## 데이터베이스 규칙

| 사용 | 비권장 | 설명 |
|------|--------|------|
| `service_number` | ~~employee_id~~ | 군번 (필수) |
| `unit` | ~~department~~ | 소속 |
| `current_point` | ~~points~~ | 보유 포인트 |
| `rank_id` | - | 계급 FK |

## API 설계 규칙

### 엔드포인트

```
/api/auth/*           # 인증
/api/users/*          # 사용자 관리 (admin)
/api/orders/*         # 주문 (사용자용)
/api/sales/*          # 판매 관리 (판매소용)
/api/inventory/*      # 재고
/api/points/*         # 포인트
/api/tailor-vouchers/* # 체척권
```

### 응답 형식

```python
# 목록: { items, total, page, page_size, total_pages }
# 단일: { id, name, ... }
# 성공: { "message": "처리되었습니다" }
```

### 역할별 접근 제어

| 엔드포인트 | admin | sales_office | tailor_company | general |
|-----------|-------|--------------|----------------|---------|
| /api/users/* | ✅ | ❌ | ❌ | ❌ |
| /api/sales/orders | ✅ | ✅ | ❌ | ❌ |
| /api/orders | ❌ | ❌ | ❌ | ✅ |

## 프론트엔드 규칙

```
views/
├── admin/        # 군수담당자 (UserList, PointGrant, ClothingList)
├── sales/        # 판매소 (OrderList, Inventory, OfflineSale)
├── tailor/       # 체척업체 (VoucherList, VoucherRegister)
└── user/         # 일반사용자 (Shop, Orders, Points, Profile)
```

**UI 원칙**: 컴팩트 리스트, 모달로 편집, 색상 (Primary `#3b82f6`, Success `#16a34a`, Danger `#dc2626`)

## 파일 생성 체크리스트

- [ ] 한국어 주석/문서 추가
- [ ] 타입 힌트 사용 (Python), Composition API (Vue)
- [ ] 올바른 필드명 사용 (service_number, unit, current_point)
- [ ] 역할 기반 접근 제어 확인 (check_admin, get_current_user)
- [ ] 에러 처리: try/catch, ValueError → HTTPException

## 테스트 계정

| ID | 비밀번호 | 역할 |
|----|---------|------|
| admin | admin123 | admin |
| sales1 | sales123 | sales_office |
| tailor1 | tailor123 | tailor_company |
| user01 | user123 | general |
