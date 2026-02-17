# 군 피복 구매관리 시스템

> Military Clothing Purchase Management System

## 프로젝트 개요

군 피복 구매관리 시스템은 군 인원에게 지급되는 피복포인트를 관리하고, 피복품목을 온라인/오프라인으로 구매할 수 있는 통합 관리 시스템입니다.

### 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy, SQLite |
| Frontend | Vue 3, Vite, Pinia, Vue Router |
| 인증 | JWT Token |
| 스타일 | CSS (Scoped CSS) |

### 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Admin  │ │  Sales  │ │ Tailor  │ │  User   │           │
│  │  Views  │ │  Views  │ │  Views  │ │  Views  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └────────────┴────────────┴────────────┘              │
│                         │ Pinia Store                       │
│                         ▼                                    │
│                    ┌─────────┐                              │
│                    │   API   │ axios                        │
│                    └────┬────┘                              │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTP/JSON
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       Backend (FastAPI)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Routers                           │   │
│  │  auth │ users │ orders │ inventory │ tailor │ ...   │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │ Services                          │
│  ┌──────────────────────┴──────────────────────────────┐   │
│  │                   SQLAlchemy ORM                     │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│                    ┌─────────┐                              │
│                    │ SQLite  │                              │
│                    └─────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## 설치 및 실행

### 시스템 요구사항

- Python 3.11+
- Node.js 18+
- npm 또는 bun

### 백엔드 설치

```bash
cd clothing-system/backend

# 가상환경 생성 (선택)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# DB 초기화 및 시드 데이터 생성
python3 init_db.py
```

### 프론트엔드 설치

```bash
cd clothing-system/frontend

# 의존성 설치
npm install
```

### 실행

```bash
# 백엔드 (포트 8000)
cd clothing-system/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 (포트 5173)
cd clothing-system/frontend
npm run dev
```

### 접속 정보

- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 테스트 계정

| ID | 비밀번호 | 역할 | 군번 | 비고 |
|----|---------|------|------|------|
| admin | admin123 | 군수담당자 | 20-123456 | 전체 관리 |
| sales1 | sales123 | 피복판매소 | 30-100001 | 1판매소 |
| sales2 | sales123 | 피복판매소 | 30-100002 | 2판매소 |
| sales3 | sales123 | 피복판매소 | 30-100003 | 3판매소 |
| tailor1 | tailor123 | 체척업체 | 40-200001 | A업체 |
| tailor2 | tailor123 | 체척업체 | 40-200002 | B업체 |
| user01 | user123 | 일반사용자 | 21-100001 | 대위 |
| user02 | user123 | 일반사용자 | 15-100002 | 중사 |
| ... | ... | ... | ... | ... |
| user10 | user123 | 일반사용자 | 10-100010 | 하사 |

## 사용자 역할 및 권한

### 1. 군수담당자 (admin)

| 기능 | 설명 |
|------|------|
| 사용자 관리 | 일괄/개별 등록, 진급 처리, 계급 수정 |
| 포인트 관리 | 계급별 포인트 지급, 지급 이력 조회 |
| 품목 관리 | 대/중/소분류 관리, 품목 등록/수정/삭제 |
| 판매소 관리 | 피복판매소 등록/수정/삭제/조회 |
| 체척업체 관리 | 체척업체 등록/수정/삭제/조회 |
| 체척권 관리 | 취소 요청 승인 처리 |
| 통계 | 전체 현황 조회 |

### 2. 피복판매소담당자 (sales_office)

| 기능 | 설명 |
|------|------|
| 주문 관리 | 온라인 주문 배송 처리, 직권 취소 |
| 오프라인 판매 | 직접 판매, 반품 처리 |
| 재고 관리 | 입고 처리, 재고 조정, 이력 관리 |
| 배송지 관리 | 직접 배송지 등록/수정/삭제 |
| 통계 | 일별/품목별/사용자별 판매현황 |

### 3. 체척업체담당자 (tailor_company)

| 기능 | 설명 |
|------|------|
| 체척권 등록 | 사용자 체척권 등록 처리 |
| 현황 조회 | 등록된 체척권 목록 조회 |

### 4. 일반사용자 (general)

| 기능 | 설명 |
|------|------|
| 쇼핑 | 온라인 피복 구매 (완제품/맞춤피복) |
| 주문 관리 | 구매 내역 조회, 취소, 반품 요청 |
| 포인트 조회 | 보유 포인트, 지급 이력 확인 |
| 배송 확인 | 배송 상태 추적 |

## 계급 체계 및 포인트

### 계급별 연간 포인트

| 계급 | 계급장군 | 연간포인트 | 복무년수 보너스 |
|------|---------|-----------|----------------|
| 장성급 | 장교 | 1,000,000P | 5,000P/년 |
| 대령 | 장교 | 800,000P | 5,000P/년 |
| 소령 | 장교 | 800,000P | 5,000P/년 |
| 대위 | 장교 | 600,000P | 5,000P/년 |
| 소위 | 장교 | 600,000P | 5,000P/년 |
| 준위 | 장교 | 500,000P | 5,000P/년 |
| 상사 | 부사관 | 450,000P | 5,000P/년 |
| 중사 | 부사관 | 400,000P | 5,000P/년 |
| 하사 | 부사관 | 350,000P | 5,000P/년 |
| 군무원 | 군무원 | 400,000P | 5,000P/년 |

### 포인트 지급 규칙

1. **정기 지급**: 매년 1월 1일 일괄 지급
2. **복무년수 보너스**: 입대일 기준 1년당 5,000P 추가
3. **진급 시**: 진급일부터 연말까지 일할계산하여 차액 지급
4. **퇴직 예정자**: 퇴직예정일 기준 일할계산하여 지급

## 디렉토리 구조

```
clothing-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 앱 진입점
│   │   ├── config.py         # 설정
│   │   ├── database.py       # DB 연결
│   │   ├── models/           # SQLAlchemy 모델
│   │   │   ├── user.py       # 사용자, 계급
│   │   │   ├── clothing.py   # 품목, 규격, 카테고리
│   │   │   ├── order.py      # 주문, 주문상세, 배송
│   │   │   ├── point.py      # 포인트 지급, 거래
│   │   │   ├── sales.py      # 판매소, 재고
│   │   │   └── tailor.py     # 체척업체, 체척권
│   │   ├── schemas/          # Pydantic 스키마
│   │   ├── routers/          # API 라우터
│   │   │   ├── auth.py       # 인증
│   │   │   ├── users.py      # 사용자 관리
│   │   │   ├── orders.py     # 주문 (사용자용)
│   │   │   ├── sales.py      # 판매 관리 (판매소용)
│   │   │   ├── inventory.py  # 재고 관리
│   │   │   ├── tailor.py     # 체척권 관리
│   │   │   ├── points.py     # 포인트 관리
│   │   │   └── ...
│   │   ├── services/         # 비즈니스 로직
│   │   └── utils/            # 유틸리티 (인증 등)
│   ├── init_db.py            # DB 초기화
│   ├── seed_data.py          # 시드 데이터
│   └── requirements.txt      # Python 의존성
│
├── frontend/
│   ├── src/
│   │   ├── main.js           # Vue 앱 진입점
│   │   ├── App.vue           # 루트 컴포넌트
│   │   ├── api/              # API 호출 모듈
│   │   ├── router/           # Vue Router 설정
│   │   ├── stores/           # Pinia 스토어
│   │   │   ├── auth.js       # 인증 상태
│   │   │   ├── cart.js       # 장바구니
│   │   │   ├── clothing.js   # 품목 상태
│   │   │   └── ...
│   │   ├── components/       # 재사용 컴포넌트
│   │   │   ├── common/       # 공통 컴포넌트
│   │   │   ├── layout/       # 레이아웃
│   │   │   ├── clothing/     # 품목 관련
│   │   │   └── order/        # 주문 관련
│   │   └── views/            # 페이지 컴포넌트
│   │       ├── admin/        # 군수담당자
│   │       ├── sales/        # 판매소
│   │       ├── tailor/       # 체척업체
│   │       └── user/         # 일반사용자
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   ├── README.md             # 문서 인덱스
│   ├── db-schema.md          # DB 스키마 설계서
│   ├── api-spec.md           # API 명세서
│   ├── ui-design.md          # 화면설계서
│   └── project-plan.md       # 프로젝트 기획서
│
├── clothing_requirement.txt  # 요구사항 정의서
└── README.md                 # 이 파일
```

## API 개요

### 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/auth/login | 로그인 |
| GET | /api/auth/me | 현재 사용자 정보 |

### 사용자

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/users | 사용자 목록 |
| POST | /api/users | 사용자 생성 |
| PUT | /api/users/{id} | 사용자 수정 |
| DELETE | /api/users/{id} | 사용자 삭제 |
| GET | /api/users/by-service-number/{sn} | 군번으로 조회 |
| POST | /api/users/bulk-import | 일괄 등록 |
| POST | /api/users/{id}/promote | 진급 처리 |

### 주문 (사용자용)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/orders | 내 주문 목록 |
| POST | /api/orders | 주문 생성 |
| GET | /api/orders/{id} | 주문 상세 |
| POST | /api/orders/{id}/cancel | 주문 취소 |

### 주문 (판매소용)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/sales/orders | 판매소 주문 목록 |
| PUT | /api/sales/orders/{id}/status | 주문 상태 변경 |
| POST | /api/sales/offline | 오프라인 판매 |
| POST | /api/sales/refund | 반품 처리 |

### 재고

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/inventory | 재고 목록 |
| GET | /api/inventory/available | 구매 가능 재고 |
| POST | /api/inventory/adjust | 재고 조정 |

### 포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/points/grant-single | 개별 지급 |
| POST | /api/points/grant-bulk | 일괄 지급 |
| GET | /api/points/grant-history | 지급 이력 |

### 체척권

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/tailor-vouchers | 체척권 목록 |
| POST | /api/tailor-vouchers/register | 체척권 등록 |
| GET | /api/tailor-vouchers/companies | 체척업체 목록 |

## 비즈니스 로직

### 주문 생성 플로우

```
1. 사용자가 품목 선택 → 장바구니 담기
2. 판매소 선택 (온라인 구매 시)
3. 배송 방법 선택 (택배/직접수령)
4. 주문 생성
   - 재고 예약 (reserved_quantity 증가)
   - 포인트 예약 (reserved_point 증가)
5. 판매소에서 배송 처리
   - 배송 완료 시 재고 차감, 포인트 차감
```

### 포인트 거래 유형

| 유형 | 설명 |
|------|------|
| grant | 지급 (정기, 진급) |
| use | 사용 (배송 완료) |
| reserve | 예약 (주문 생성) |
| release | 해제 (주문 취소) |
| refund | 환불 (반품) |
| deduct | 차감 (오프라인 판매) |

### 주문 상태

| 상태 | 설명 |
|------|------|
| pending | 주문 접수 |
| confirmed | 주문 확인 |
| processing | 상품 준비중 |
| shipped | 배송중 |
| delivered | 배송완료 |
| cancelled | 취소 |
| refunded | 반품완료 |

## 라이선스

Internal Use Only - 군 내부 사용용

## 문서

- [요구사항 정의서](../clothing_requirement.txt)
- [DB 스키마 설계서](docs/db-schema.md)
- [API 명세서](docs/api-spec.md)
- [화면설계서](docs/ui-design.md)
- [프로젝트 기획서](docs/project-plan.md)
