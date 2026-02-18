# API 명세서

> 군 피복 구매관리 시스템 REST API 명세

## 기본 정보

- **Base URL**: `http://localhost:8000/api`
- **인증**: Bearer Token (JWT)
- **Content-Type**: `application/json`

## 공통 사항

### 인증 헤더

```
Authorization: Bearer <access_token>
```

### 공통 응답 형식

#### 성공 응답

```json
{
  "id": 1,
  "name": "데이터",
  ...
}
```

#### 목록 응답

```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [...]
}
```

#### 에러 응답

```json
{
  "detail": "에러 메시지"
}
```

---

## 인증 API

### 로그인

```
POST /api/auth/login
```

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 현재 사용자 조회

```
GET /api/auth/me
```

**Response:**
```json
{
  "user_id": 1,
  "username": "admin",
  "name": "관리자",
  "role": "admin",
  "service_number": "20-123456",
  "rank": {
    "id": 2,
    "name": "대령"
  },
  "unit": "군수사령부",
  "current_point": 800000,
  "reserved_point": 0,
  "sales_office_id": null,
  "tailor_company_id": null
}
```

---

## 사용자 API

> 권한: admin

### 사용자 목록 조회

```
GET /api/users
```

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | int | No | 페이지 번호 (기본: 1) |
| page_size | int | No | 페이지 크기 (기본: 20) |
| role | string | No | 권한 필터 |
| rank_id | int | No | 계급 필터 |
| is_active | bool | No | 활성 상태 필터 |
| keyword | string | No | 검색어 (이름, 아이디, 군번) |

**Response:**
```json
{
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "items": [
    {
      "id": 1,
      "username": "user01",
      "name": "홍길동",
      "email": "user01@example.com",
      "role": "general",
      "rank": {"id": 4, "name": "대위"},
      "service_number": "21-100001",
      "unit": "제1보병사단",
      "service_years": 3,
      "current_point": 600000,
      "reserved_point": 0,
      "is_active": true
    }
  ]
}
```

### 사용자 상세 조회

```
GET /api/users/{user_id}
```

### 사용자 생성

```
POST /api/users
```

**Request Body:**
```json
{
  "username": "user11",
  "password": "user123",
  "name": "새사용자",
  "email": "user11@example.com",
  "role": "general",
  "rank_id": 4,
  "service_number": "21-100011",
  "unit": "제1보병사단",
  "enlistment_date": "2021-03-01"
}
```

### 사용자 수정

```
PUT /api/users/{user_id}
```

### 사용자 삭제

```
DELETE /api/users/{user_id}
```

### 군번으로 사용자 조회

```
GET /api/users/by-service-number/{service_number}
```

**Response:**
```json
{
  "id": 1,
  "username": "user01",
  "name": "홍길동",
  "service_number": "21-100001",
  "unit": "제1보병사단",
  "rank": {"id": 4, "name": "대위"},
  "current_point": 600000
}
```

### 사용자 일괄 등록

```
POST /api/users/bulk-import
```

**Request Body:**
```json
{
  "users": [
    {"username": "user11", "password": "user123", ...},
    {"username": "user12", "password": "user123", ...}
  ]
}
```

**Response:**
```json
{
  "created": 2,
  "total": 2,
  "errors": []
}
```

### 사용자 진급

```
POST /api/users/{user_id}/promote
```

**Request Body:**
```json
{
  "new_rank_id": 3,
  "promotion_date": "2024-04-01"
}
```

### 계급 목록 조회

```
GET /api/users/ranks
```

---

## 카테고리 API

### 카테고리 목록

```
GET /api/categories
```

### 카테고리 트리

```
GET /api/categories/tree
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "상의",
    "children": [
      {
        "id": 11,
        "name": "전투복",
        "children": [
          {"id": 111, "name": "전투복 상의"}
        ]
      }
    ]
  }
]
```

---

## 품목 API

### 품목 목록

```
GET /api/clothings
```

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| category_id | int | 카테고리 필터 |
| clothing_type | string | ready_made / custom |
| keyword | string | 검색어 |
| is_active | bool | 활성 상태 |

### 품목 상세

```
GET /api/clothings/{id}
```

### 품목 규격 목록

```
GET /api/clothings/{id}/specs
```

**Response:**
```json
[
  {
    "id": 1,
    "spec_code": "TV-90",
    "size": "90",
    "points": 50000,
    "is_active": true
  }
]
```

---

## 재고 API

### 재고 목록

```
GET /api/inventory
```

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| sales_office_id | int | 판매소 ID |
| keyword | string | 검색어 |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "sales_office_id": 1,
      "item_id": 1,
      "item_name": "전투복 상의",
      "item_code": "TV-001",
      "spec_id": 1,
      "spec_size": "90",
      "quantity": 100,
      "reserved_quantity": 10,
      "available_quantity": 90
    }
  ]
}
```

### 구매 가능 재고

```
GET /api/inventory/available
```

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| sales_office_id | int | 판매소 ID (필수) |
| clothing_type | string | ready_made / custom |

**Response:**
```json
{
  "items": [
    {
      "item_id": 1,
      "item_name": "전투복 상의",
      "item_code": "TV-001",
      "spec_id": 1,
      "spec_size": "90",
      "points": 50000,
      "available_quantity": 90,
      "clothing_type": "ready_made"
    }
  ]
}
```

### 재고 조정

```
POST /api/inventory/adjust
```

**Request Body:**
```json
{
  "sales_office_id": 1,
  "item_id": 1,
  "spec_id": 1,
  "adjustment_type": "increase",
  "quantity": 50,
  "reason": "입고"
}
```

### 재고 이력

```
GET /api/inventory/history
```

---

## 주문 API (사용자용)

> 권한: general

### 내 주문 목록

```
GET /api/orders
```

**Response:**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "order_number": "ORD-20240101-0001",
      "status": "delivered",
      "order_type": "online",
      "total_amount": 100000,
      "used_point": 100000,
      "ordered_at": "2024-01-01T10:00:00",
      "item_count": 2,
      "items": [
        {
          "id": 1,
          "item_name": "전투복 상의",
          "spec_size": "90",
          "quantity": 2,
          "unit_price": 50000,
          "total_price": 100000
        }
      ],
      "delivery": {
        "delivery_type": "parcel",
        "status": "delivered",
        "tracking_number": "1234567890"
      }
    }
  ]
}
```

### 주문 상세

```
GET /api/orders/{id}
```

### 주문 생성

```
POST /api/orders
```

**Request Body:**
```json
{
  "sales_office_id": 1,
  "items": [
    {
      "item_id": 1,
      "spec_id": 1,
      "quantity": 2
    }
  ],
  "delivery_type": "parcel",
  "recipient_name": "홍길동",
  "recipient_phone": "010-1234-5678",
  "shipping_address": "서울시 강남구..."
}
```

**Response:**
```json
{
  "id": 1,
  "order_number": "ORD-20240101-0001",
  "status": "pending",
  "total_amount": 100000,
  "reserved_point": 100000
}
```

### 주문 취소

```
POST /api/orders/{id}/cancel
```

---

## 판매 관리 API (판매소용)

> 권한: sales_office, admin

### 판매소 주문 목록

```
GET /api/sales/orders
```

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| status | string | 주문 상태 필터 |
| order_type | string | online / offline |
| keyword | string | 주문번호 검색 |

**Response:**
```json
{
  "total": 50,
  "items": [
    {
      "id": 1,
      "order_number": "ORD-20240101-0001",
      "user": {
        "id": 10,
        "name": "홍길동",
        "service_number": "21-100001",
        "rank": "대위",
        "unit": "제1보병사단"
      },
      "status": "pending",
      "order_type": "online",
      "total_amount": 100000,
      "reserved_point": 100000,
      "item_count": 2,
      "items": [...],
      "delivery": {...}
    }
  ]
}
```

### 주문 상태 변경

```
PUT /api/sales/orders/{id}/status
```

**Request Body:**
```json
{
  "status": "shipped",
  "tracking_number": "1234567890"
}
```

### 오프라인 판매

```
POST /api/sales/offline
```

**Request Body:**
```json
{
  "user_id": 10,
  "sales_office_id": 1,
  "items": [
    {
      "item_id": 1,
      "spec_id": 1,
      "quantity": 2,
      "unit_price": 50000
    }
  ]
}
```

### 반품 처리

```
POST /api/sales/refund
```

**Request Body:**
```json
{
  "order_id": 1,
  "items": [
    {
      "order_item_id": 1,
      "quantity": 1,
      "reason": "사이즈 불만"
    }
  ]
}
```

---

## 포인트 API

### 포인트 지급 (개별)

```
POST /api/points/grant-single
```

**Request Body:**
```json
{
  "user_id": 10,
  "year": 2024,
  "base_amount": 600000,
  "service_year_bonus": 15000,
  "grant_date": "2024-01-01"
}
```

### 포인트 지급 (일괄)

```
POST /api/points/grant-bulk
```

**Request Body:**
```json
{
  "year": 2024,
  "grant_date": "2024-01-01"
}
```

### 포인트 지급 이력

```
GET /api/points/grant-history
```

---

## 체척권 API

### 체척권 목록

```
GET /api/tailor-vouchers
```

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| user_id | int | 사용자 ID (미지정 시 본인) |
| status | string | issued / registered / used / cancelled |
| keyword | string | 검색어 |

**Response:**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "voucher_number": "TV-20240101-ABCD1234",
      "user": {
        "id": 10,
        "name": "홍길동",
        "service_number": "21-100001",
        "unit": "제1보병사단",
        "rank": {"name": "대위"}
      },
      "item": {"id": 5, "name": "맞춤 정장"},
      "amount": 100000,
      "status": "issued",
      "issued_at": "2024-01-01T10:00:00"
    }
  ]
}
```

### 체척권 직접 발행 (맞춤피복용)

> 맞춤피복 구매 시 주문 없이 체척권만 발행

```
POST /api/tailor-vouchers/issue-direct
```

**Request Body:**
```json
{
  "user_id": 10,
  "item_id": 8,
  "amount": 1,
  "sales_office_id": 1,
  "notes": "맞춤피복 체척권 발행"
}
```

**Response:**
```json
{
  "id": 1,
  "voucher_number": "TV-20250219-ABCD1234",
  "user_id": 10,
  "item_id": 8,
  "amount": 1,
  "status": "issued",
  "issued_at": "2025-02-19T10:00:00",
  "notes": "맞춤피복 체척권 발행"
}
```

### 체척권 등록

```
POST /api/tailor-vouchers/register
```

**Request Body:**
```json
{
  "voucher_id": 1,
  "tailor_company_id": 1
}
```

### 체척권 취소 요청

```
POST /api/tailor-vouchers/{id}/cancel-request
```

**Request Body:**
```json
{
  "reason": "취소 사유"
}
```

### 체척업체 목록

```
GET /api/tailor-vouchers/companies
```

---

## 맞춤피복 API

### 맞춤피복 목록 조회

> 재고 관리 없이 활성화된 맞춤피복 목록만 조회

```
GET /api/clothings/custom/available
```

**Response:**
```json
{
  "items": [
    {
      "item_id": 8,
      "spec_id": 43,
      "item_name": "정복상의맞춤",
      "category_id": 14,
      "category_name": "정복상의맞춤",
      "clothing_type": "custom",
      "description": "정복상의맞춤 - 맞춤 제작",
      "image_url": null,
      "thumbnail_url": null,
      "spec_size": "맞춤",
      "spec_price": 149000
    }
  ],
  "total": 4
}
```

---

## 배송지 API

### 배송지 목록

```
GET /api/delivery-locations
```

### 배송지 생성

```
POST /api/delivery-locations
```

### 배송지 수정

```
PUT /api/delivery-locations/{id}
```

### 배송지 삭제

```
DELETE /api/delivery-locations/{id}
```

---

## 판매소 API

### 판매소 목록

```
GET /api/sales-offices
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "제1판매소",
    "code": "S001",
    "address": "서울시 용산구...",
    "phone": "02-1234-5678"
  }
]
```

---

## HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성 성공 |
| 204 | 삭제 성공 (내용 없음) |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 422 | 유효성 검사 실패 |
| 500 | 서버 오류 |
