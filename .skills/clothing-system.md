# 피복 구매관리 시스템 개발 스킬

## 개요

이 스킬은 군 피복 구매관리 시스템 개발에 필요한 전문 지식을 제공합니다.

## 기술 스택

### Backend
- **FastAPI**: Python 웹 프레임워크
- **SQLAlchemy 2.0+**: ORM
- **SQLite**: 데이터베이스
- **Pydantic**: 데이터 검증
- **python-jose**: JWT 인증

### Frontend
- **Vue 3**: Composition API
- **Vite**: 빌드 도구
- **Pinia**: 상태 관리
- **Vue Router**: 라우팅
- **Axios**: HTTP 클라이언트

## 핵심 도메인 지식

### 1. 피복 타입

| 타입 | Enum | 설명 | 재고관리 |
|------|------|------|---------|
| 완제품 | `ready_made` | 규격별 재고 관리 | O |
| 맞춤피복 | `custom` | 체척권 발행 | X |

### 2. 사용자 역할

| 역할 | Enum | 설명 |
|------|------|------|
| 군수담당자 | `admin` | 전체 관리 |
| 판매소담당자 | `sales_office` | 주문/재고/판매 |
| 체척업체담당자 | `tailor_company` | 체척권 등록 |
| 일반사용자 | `general` | 쇼핑/주문 |

### 3. 주문 상태 플로우

```
온라인 주문:
PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED → RECEIVED
                              ↓
                          CANCELLED

오프라인 판매:
즉시 DELIVERED 상태
```

### 4. 포인트 거래 유형

| 유형 | 설명 |
|------|------|
| `grant` | 지급 |
| `use` | 사용 |
| `reserve` | 예약 |
| `release` | 해제 |
| `refund` | 환불 |
| `deduct` | 차감 |

## 코딩 패턴

### Backend Service Layer

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
```

### Frontend Composition API

```vue
<script setup>
import { ref, onMounted } from 'vue'
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
    alert('데이터를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}
</script>
```

## 주요 API 엔드포인트

### 쇼핑 관련
- `GET /api/inventory/available` - 구매 가능 재고
- `GET /api/clothings/custom/available` - 맞춤피복 목록
- `POST /api/orders` - 주문 생성
- `POST /api/tailor-vouchers/issue-direct` - 체척권 직접 발행

### 판매 관련
- `GET /api/sales/orders` - 주문 목록
- `POST /api/sales/offline` - 오프라인 판매
- `POST /api/sales/refund` - 반품 처리

## 필드 네이밍 규칙

| 사용 | 비권장 | 설명 |
|------|--------|------|
| `service_number` | ~~employee_id~~ | 군번 |
| `unit` | ~~department~~ | 소속 |
| `current_point` | ~~points~~ | 보유 포인트 |
| `clothing_type` | - | 피복 타입 |

## 테스트 계정

| ID | 비밀번호 | 역할 |
|----|---------|------|
| admin | admin123 | admin |
| sales1 | sales123 | sales_office |
| tailor1 | tailor123 | tailor_company |
| user01 | user123 | general |

## 관련 문서

- [개발자 가이드](../docs/developer-guide.md)
- [API 명세서](../docs/api-spec.md)
- [화면설계서](../docs/ui-design.md)
- [AGENTS.md](../AGENTS.md)
