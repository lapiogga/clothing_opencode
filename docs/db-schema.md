# 데이터베이스 스키마

## 사용자 (users)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| username | String(50) | 아이디 (unique) |
| password_hash | String(255) | 비밀번호 해시 |
| name | String(100) | 이름 |
| email | String(100) | 이메일 (unique, nullable) |
| phone | String(20) | 전화번호 (nullable) |
| role | Enum | 권한 (admin, sales_office, tailor_company, general) |
| rank_id | Integer | FK (ranks.id, nullable) |
| service_number | String(20) | 군번 (unique, NOT NULL) |
| unit | String(100) | 소속 (nullable) |
| enlistment_date | Date | 입대일 (nullable) |
| retirement_date | Date | 전역예정일 (nullable) |
| is_active | Boolean | 활성 상태 |
| sales_office_id | Integer | FK (sales_offices.id, nullable) |
| tailor_company_id | Integer | FK (tailor_companies.id, nullable) |
| current_point | Integer | 보유 포인트 |
| reserved_point | Integer | 예약 포인트 |

**계산 필드 (property):**
- `service_years`: 입대일 기준 복무년수 자동 계산
- `available_point`: 사용 가능 포인트 (current_point - reserved_point)

## 계급 (ranks)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| name | String(50) | 계급명 (장성급, 대령, 소령, 대위, 소위, 준위, 상사, 중사, 하사, 군무원) |
| code | Enum | 계급 코드 |
| rank_group | Enum | 계급장군 (officer, nco, civilian) |
| annual_point | Integer | 연간 포인트 |
| service_year_bonus | Integer | 복무년수 보너스 (기본 5,000P/년) |

## 피복품목 (clothing_items)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| name | String(100) | 품목명 |
| category_id | Integer | FK (categories.id) |
| clothing_type | Enum | 완제품/맞춤 (ready_made, custom) |
| description | Text | 설명 |
| is_active | Boolean | 활성 상태 |

## 피복규격 (clothing_specs)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| item_id | Integer | FK (clothing_items.id) |
| spec_code | String(30) | 규격코드 |
| size | String(20) | 사이즈 |
| price | Integer | 가격 |
| is_active | Boolean | 활성 상태 |

## 재고 (inventory)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| sales_office_id | Integer | FK (sales_offices.id) |
| item_id | Integer | FK (clothing_items.id) |
| spec_id | Integer | FK (clothing_specs.id) |
| quantity | Integer | 재고수량 |
| reserved_quantity | Integer | 예약수량 |

**계산 필드:**
- `available_quantity`: 가용재고 (quantity - reserved_quantity)

## 주문 (orders)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| order_number | String(30) | 주문번호 (unique) |
| user_id | Integer | FK (users.id) |
| sales_office_id | Integer | FK (sales_offices.id) |
| order_type | Enum | 온라인/오프라인 (online, offline) |
| status | Enum | 주문상태 (pending, confirmed, shipped, delivered, cancelled, returned, refunded) |
| total_amount | Integer | 총금액 |
| reserved_point | Integer | 예약포인트 |
| used_point | Integer | 사용포인트 |
| ordered_at | DateTime | 주문일시 |

## 포인트거래 (point_transactions)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| user_id | Integer | FK (users.id) |
| transaction_type | Enum | 거래유형 (grant, use, reserve, release, refund, deduct) |
| amount | Integer | 금액 |
| balance_after | Integer | 거래후 잔액 |
| reserved_after | Integer | 거래후 예약액 |
| order_id | Integer | FK (orders.id, nullable) |
| description | Text | 설명 |

## 체척권 (tailor_vouchers)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| voucher_number | String(30) | 체척권번호 |
| user_id | Integer | FK (users.id) |
| order_id | Integer | FK (orders.id) |
| amount | Integer | 금액 |
| status | Enum | 상태 (issued, used, cancelled) |
| issued_at | DateTime | 발급일시 |
