# 데이터베이스 스키마 설계서

> 군 피복 구매관리 시스템 DB 스키마 문서

## ERD 개요

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ranks     │     │    users    │     │ sales_offices│
│  (계급)     │◄────│   (사용자)   │────►│  (판매소)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   orders    │   │ point_      │   │ tailor_     │
│   (주문)    │   │ transactions│   │ vouchers    │
└──────┬──────┘   └─────────────┘   └─────────────┘
       │
       ▼
┌─────────────┐
│ order_items │
│(주문상세)   │
└─────────────┘
```

## 테이블 상세

### 1. 계급 (ranks)

사용자 계급 정보

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| name | VARCHAR(50) | NOT NULL, UNIQUE | 계급명 |
| code | ENUM | NOT NULL, UNIQUE | 계급코드 (general_officer, colonel, major, captain, lieutenant, warrant_officer, sergeant_major, sergeant, corporal, civilian) |
| rank_group | ENUM | NOT NULL | 계급장군 (officer, nco, civilian) |
| annual_point | INTEGER | NOT NULL | 연간 포인트 |
| service_year_bonus | INTEGER | DEFAULT 5000 | 복무년수 보너스 (1년당) |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**초기 데이터:**

| name | code | rank_group | annual_point |
|------|------|------------|--------------|
| 장성급 | general_officer | officer | 1,000,000 |
| 대령 | colonel | officer | 800,000 |
| 소령 | major | officer | 800,000 |
| 대위 | captain | officer | 600,000 |
| 소위 | lieutenant | officer | 600,000 |
| 준위 | warrant_officer | officer | 500,000 |
| 상사 | sergeant_major | nco | 450,000 |
| 중사 | sergeant | nco | 400,000 |
| 하사 | corporal | nco | 350,000 |
| 군무원 | civilian | civilian | 400,000 |

---

### 2. 사용자 (users)

시스템 사용자 정보

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 로그인 ID |
| password_hash | VARCHAR(255) | NOT NULL | 비밀번호 해시 |
| name | VARCHAR(100) | NOT NULL | 이름 |
| email | VARCHAR(100) | UNIQUE, NULL | 이메일 |
| phone | VARCHAR(20) | NULL | 전화번호 |
| role | ENUM | NOT NULL, DEFAULT 'general' | 권한 (admin, sales_office, tailor_company, general) |
| rank_id | INTEGER | FK, NULL | 계급 ID |
| service_number | VARCHAR(20) | NOT NULL, UNIQUE | 군번 |
| unit | VARCHAR(100) | NULL | 소속 |
| enlistment_date | DATE | NULL | 입대일 |
| retirement_date | DATE | NULL | 전역예정일 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| sales_office_id | INTEGER | FK, NULL | 소속 판매소 |
| tailor_company_id | INTEGER | FK, NULL | 소속 체척업체 |
| current_point | INTEGER | DEFAULT 0 | 보유 포인트 |
| reserved_point | INTEGER | DEFAULT 0 | 예약 포인트 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**계산 프로퍼티:**

```python
@property
def service_years(self) -> int:
    """입대일 기준 복무년수"""
    ...

@property
def available_point(self) -> int:
    """사용 가능 포인트 (current_point - reserved_point)"""
    return self.current_point - self.reserved_point
```

**인덱스:**
- username (UNIQUE)
- service_number (UNIQUE)
- email (UNIQUE)

---

### 3. 사용자 진급 이력 (user_rank_histories)

진급 및 포인트 조정 이력

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| user_id | INTEGER | FK, NOT NULL | 사용자 ID |
| old_rank_id | INTEGER | FK, NULL | 이전 계급 ID |
| new_rank_id | INTEGER | FK, NOT NULL | 진급 후 계급 ID |
| promotion_date | DATE | NOT NULL | 진급일 |
| point_adjustment | INTEGER | DEFAULT 0 | 포인트 조정액 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

---

### 4. 카테고리 (categories)

피복 품목 카테고리 (계층 구조)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| name | VARCHAR(50) | NOT NULL | 카테고리명 |
| code | VARCHAR(20) | UNIQUE | 카테고리 코드 |
| parent_id | INTEGER | FK, NULL | 상위 카테고리 ID |
| level | INTEGER | DEFAULT 1 | 계층 레벨 (1: 대분류, 2: 중분류, 3: 소분류) |
| sort_order | INTEGER | DEFAULT 0 | 정렬 순서 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**구조 예시:**

```
대분류 (level=1)
├── 중분류 (level=2)
│   ├── 소분류 (level=3)
│   └── 소분류
└── 중분류
    └── 소분류
```

---

### 5. 피복 품목 (clothing_items)

피복 품목 정보

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| name | VARCHAR(100) | NOT NULL | 품목명 |
| code | VARCHAR(30) | UNIQUE | 품목 코드 |
| category_id | INTEGER | FK, NOT NULL | 카테고리 ID |
| clothing_type | ENUM | NOT NULL | 품목유형 (ready_made: 완제품, custom: 맞춤) |
| description | TEXT | NULL | 설명 |
| image_url | VARCHAR(255) | NULL | 이미지 URL |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

---

### 6. 피복 규격 (clothing_specs)

완제품 규격 (사이즈별)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| item_id | INTEGER | FK, NOT NULL | 품목 ID |
| spec_code | VARCHAR(30) | NOT NULL | 규격 코드 |
| size | VARCHAR(20) | NOT NULL | 사이즈 (S, M, L, XL, 90, 95, 100...) |
| points | INTEGER | NOT NULL | 포인트 가격 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**유니크 제약:** (item_id, spec_code)

---

### 7. 판매소 (sales_offices)

피복 판매소 정보

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| name | VARCHAR(100) | NOT NULL | 판매소명 |
| code | VARCHAR(20) | UNIQUE, NOT NULL | 판매소 코드 |
| address | VARCHAR(200) | NULL | 주소 |
| phone | VARCHAR(20) | NULL | 전화번호 |
| manager_name | VARCHAR(50) | NULL | 담당자명 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

---

### 8. 체척업체 (tailor_companies)

맞춤피복 체척업체 정보

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| name | VARCHAR(100) | NOT NULL | 업체명 |
| code | VARCHAR(20) | UNIQUE, NOT NULL | 업체 코드 |
| business_number | VARCHAR(20) | NULL | 사업자번호 |
| address | VARCHAR(200) | NULL | 주소 |
| phone | VARCHAR(20) | NULL | 전화번호 |
| manager_name | VARCHAR(50) | NULL | 담당자명 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

---

### 9. 재고 (inventory)

판매소별 품목 재고

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| sales_office_id | INTEGER | FK, NOT NULL | 판매소 ID |
| item_id | INTEGER | FK, NOT NULL | 품목 ID |
| spec_id | INTEGER | FK, NULL | 규격 ID (맞춤피복은 NULL) |
| quantity | INTEGER | DEFAULT 0 | 재고 수량 |
| reserved_quantity | INTEGER | DEFAULT 0 | 예약 수량 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**계산 프로퍼티:**

```python
@property
def available_quantity(self) -> int:
    """가용 재고 (quantity - reserved_quantity)"""
    return self.quantity - self.reserved_quantity
```

**유니크 제약:** (sales_office_id, item_id, spec_id)

---

### 10. 재고 이력 (inventory_history)

재고 변동 이력

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| inventory_id | INTEGER | FK, NOT NULL | 재고 ID |
| adjustment_type | ENUM | NOT NULL | 조정 유형 (increase, decrease, receive, return) |
| quantity | INTEGER | NOT NULL | 조정 수량 |
| before_quantity | INTEGER | NOT NULL | 조정 전 수량 |
| after_quantity | INTEGER | NOT NULL | 조정 후 수량 |
| reason | VARCHAR(200) | NULL | 사유 |
| adjustment_date | DATE | NOT NULL | 조정 일자 |
| adjusted_by | INTEGER | FK, NULL | 조정자 ID |
| order_id | INTEGER | FK, NULL | 관련 주문 ID |
| created_at | DATETIME | AUTO | 생성일시 |

---

### 11. 주문 (orders)

주문 정보

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| order_number | VARCHAR(30) | NOT NULL, UNIQUE | 주문번호 |
| user_id | INTEGER | FK, NOT NULL | 주문자 ID |
| sales_office_id | INTEGER | FK, NULL | 판매소 ID |
| order_type | ENUM | NOT NULL | 주문유형 (online, offline) |
| status | ENUM | NOT NULL, DEFAULT 'pending' | 주문상태 |
| total_amount | INTEGER | DEFAULT 0 | 총 금액 |
| reserved_point | INTEGER | DEFAULT 0 | 예약 포인트 |
| used_point | INTEGER | DEFAULT 0 | 사용 포인트 |
| used_voucher_amount | INTEGER | DEFAULT 0 | 체척권 사용액 |
| ordered_at | DATETIME | NOT NULL | 주문 일시 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**주문 상태 (status):**

| 값 | 설명 |
|------|------|
| pending | 주문 접수 |
| confirmed | 주문 확인 |
| processing | 상품 준비중 |
| shipped | 배송중 |
| delivered | 배송완료 |
| cancelled | 취소 |
| refunded | 반품완료 |

---

### 12. 주문 상세 (order_items)

주문 품목 상세

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| order_id | INTEGER | FK, NOT NULL | 주문 ID |
| item_id | INTEGER | FK, NOT NULL | 품목 ID |
| spec_id | INTEGER | FK, NULL | 규격 ID |
| quantity | INTEGER | NOT NULL | 수량 |
| unit_price | INTEGER | NOT NULL | 단가 |
| total_price | INTEGER | NOT NULL | 총 금액 |
| payment_method | ENUM | DEFAULT 'point' | 결제수단 (point, voucher) |
| is_returned | BOOLEAN | DEFAULT FALSE | 반품 여부 |
| returned_at | DATETIME | NULL | 반품 일시 |
| return_reason | VARCHAR(200) | NULL | 반품 사유 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

---

### 13. 배송 (deliveries)

주문 배송 정보

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| order_id | INTEGER | FK, NOT NULL, UNIQUE | 주문 ID |
| delivery_type | ENUM | NOT NULL | 배송유형 (parcel: 택배, direct: 직접수령) |
| status | ENUM | NOT NULL, DEFAULT 'pending' | 배송상태 |
| delivery_location_id | INTEGER | FK, NULL | 배송지 ID (직접수령 시) |
| recipient_name | VARCHAR(50) | NULL | 수령인명 |
| recipient_phone | VARCHAR(20) | NULL | 수령인 연락처 |
| shipping_address | TEXT | NULL | 배송 주소 |
| tracking_number | VARCHAR(50) | NULL | 운송장번호 |
| shipped_at | DATETIME | NULL | 발송 일시 |
| delivered_at | DATETIME | NULL | 배송완료 일시 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**배송 상태 (status):**

| 값 | 설명 |
|------|------|
| pending | 대기중 |
| preparing | 준비중 |
| in_transit | 배송중 |
| delivered | 배송완료 |

---

### 14. 배송지 (delivery_locations)

직접 수령 배송지

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| sales_office_id | INTEGER | FK, NOT NULL | 판매소 ID |
| name | VARCHAR(100) | NOT NULL | 배송지명 |
| address | TEXT | NOT NULL | 주소 |
| manager_name | VARCHAR(50) | NULL | 담당자명 |
| manager_phone | VARCHAR(20) | NULL | 담당자 연락처 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

---

### 15. 포인트 지급 (point_grants)

포인트 지급 기록

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| user_id | INTEGER | FK, NOT NULL | 사용자 ID |
| year | INTEGER | NOT NULL | 지급 연도 |
| base_amount | INTEGER | NOT NULL | 기본 포인트 |
| service_year_bonus | INTEGER | DEFAULT 0 | 복무년수 보너스 |
| daily_calc_amount | INTEGER | DEFAULT 0 | 일할계산 금액 |
| total_amount | INTEGER | NOT NULL | 총 지급액 |
| grant_date | DATE | NOT NULL | 지급 일자 |
| granted_by | INTEGER | FK, NULL | 지급자 ID |
| description | VARCHAR(200) | NULL | 설명 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**유니크 제약:** (user_id, year)

---

### 16. 포인트 거래 (point_transactions)

포인트 입출 이력

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| user_id | INTEGER | FK, NOT NULL | 사용자 ID |
| transaction_type | ENUM | NOT NULL | 거래유형 |
| amount | INTEGER | NOT NULL | 금액 |
| balance_after | INTEGER | NOT NULL | 거래 후 잔액 |
| reserved_after | INTEGER | NOT NULL | 거래 후 예약액 |
| order_id | INTEGER | FK, NULL | 관련 주문 ID |
| voucher_id | INTEGER | FK, NULL | 관련 체척권 ID |
| grant_id | INTEGER | FK, NULL | 관련 지급 ID |
| description | TEXT | NULL | 설명 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**거래 유형 (transaction_type):**

| 값 | 설명 |
|------|------|
| grant | 지급 |
| use | 사용 |
| reserve | 예약 |
| release | 예약 해제 |
| refund | 환불 |
| deduct | 차감 |

---

### 17. 체척권 (tailor_vouchers)

맞춤피복 체척권

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 고유 ID |
| voucher_number | VARCHAR(30) | NOT NULL, UNIQUE | 체척권 번호 |
| user_id | INTEGER | FK, NOT NULL | 사용자 ID |
| tailor_company_id | INTEGER | FK, NULL | 체척업체 ID |
| order_id | INTEGER | FK, NULL | 주문 ID |
| order_item_id | INTEGER | FK, NULL | 주문 상세 ID |
| item_id | INTEGER | FK, NOT NULL | 품목 ID |
| amount | INTEGER | NOT NULL | 금액 |
| status | ENUM | NOT NULL, DEFAULT 'issued' | 상태 |
| issued_at | DATETIME | NOT NULL | 발급 일시 |
| registered_at | DATETIME | NULL | 등록 일시 |
| registered_by | INTEGER | FK, NULL | 등록자 ID |
| used_at | DATETIME | NULL | 사용 일시 |
| cancelled_at | DATETIME | NULL | 취소 일시 |
| cancelled_by | INTEGER | FK, NULL | 취소자 ID |
| cancel_reason | TEXT | NULL | 취소 사유 |
| expires_at | DATE | NULL | 만료일 |
| notes | TEXT | NULL | 비고 |
| created_at | DATETIME | AUTO | 생성일시 |
| updated_at | DATETIME | AUTO | 수정일시 |

**체척권 상태 (status):**

| 값 | 설명 |
|------|------|
| issued | 발급 |
| registered | 등록 |
| used | 사용완료 |
| cancelled | 취소 |
| expired | 만료 |

---

## 인덱스 전략

### 기본 인덱스

- 모든 PK: 자동 인덱스
- 외래키: 자동 인덱스 (SQLAlchemy)
- UNIQUE 제약 컬럼: 자동 인덱스

### 추가 인덱스 권장

```sql
-- 사용자 검색용
CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_users_unit ON users(unit);

-- 주문 검색용
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_ordered_at ON orders(ordered_at);

-- 재고 조회용
CREATE INDEX idx_inventory_item ON inventory(item_id);
```

## 데이터 무결성 규칙

### 외래키 제약

- `ON DELETE CASCADE`: 연관 데이터 자동 삭제
- `ON DELETE SET NULL`: 참조 해제 시 NULL 설정

### 비즈니스 규칙

1. **포인트 차감 시**:
   - `current_point >= reserved_point` 유지
   - `available_point >= 0` 유지

2. **재고 관리 시**:
   - `quantity >= reserved_quantity` 유지
   - `available_quantity >= 0` 유지

3. **주문 취소 시**:
   - `status`가 `pending`, `confirmed`, `processing`일 때만 가능
