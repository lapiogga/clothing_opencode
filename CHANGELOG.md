# Changelog

모든 주요 변경사항은 이 파일에 기록됩니다.

## [2026-02-20] - 체척권 취소 승인 기능 및 통계 화면 개선

### 추가 (Added)
- **체척권 취소 승인 기능**
  - `VoucherStatus.CANCEL_REQUESTED` 상태 추가 (취소 요청됨)
  - 관리자용 체척권 취소 승인 화면 (`/admin/voucher-cancellations`)
  - 취소 승인 시 포인트 자동 환불 기능
  - 취소 반려 기능 (원래 상태로 복구)

- **체척권 목록 화면** (`/user/vouchers`)
  - 사용자 체척권 조회 기능
  - 상태별 필터링 (발행됨/등록됨/사용완료/취소됨)
  - 체척권 취소 요청 기능

- **배송지 관리 화면** (`/sales/delivery-locations`)
  - 판매소 배송지 등록/수정/삭제

- **대시보드 통계 API** (`/api/stats/dashboard`)
  - 역할별 맞춤 통계 제공

- **판매 통계 API** (`/api/stats/sales`)
  - 일별 판매 추이, 인기 상품, 카테고리별 비중

### 변경 (Changed)
- **체척권 취소 프로세스 개선**
  - 기존: 즉시 취소 처리
  - 변경: 취소 요청 → 관리자 승인 → 취소 완료 (포인트 환불)

- **체척권 등록 시 상태 검증 강화**
  - 취소 요청/취소됨 상태의 체척권 등록 차단

- **통계 화면 UI 개선**
  - 미니멀 디자인 적용
  - 기간 선택 기능 (주간/월간/분기)
  - CSS 기반 차트 (바 차트, 도넛 차트)
  - 로딩 스피너 추가
  - 반응형 레이아웃

- **직접 배송 기능**
  - "직접 수령" → "직접 배송"으로 명칭 변경
  - 배송지 선택 기능 추가

### 수정 (Fixed)
- **사용자 검색 API 권한**
  - `/api/users/search` 엔드포인트 추가
  - 판매소, 체척업체 권한 허용

- **체척업체 목록 API**
  - `manager_phone` 필드 제거 (모델에 없음)

- **메뉴 권한**
  - 체척권 관리 메뉴에 admin 권한 추가

- **UserResponse 스키마**
  - `sales_office_id`, `tailor_company_id` 필드 추가

### API 변경사항

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/users/search` | GET | 사용자 검색 (판매소, 체척업체 권한) |
| `/api/tailor-vouchers/{id}/approve-cancel` | POST | 체척권 취소 승인/반려 |
| `/api/stats/dashboard` | GET | 대시보드 통계 |
| `/api/stats/sales` | GET | 판매 통계 |
| `/api/delivery-locations` | POST | 배송지 등록 |
| `/api/delivery-locations/{id}` | PUT | 배송지 수정 |
| `/api/delivery-locations/{id}` | DELETE | 배송지 삭제 |

### 체척권 상태 흐름

```
발행됨 (issued)
    ├─→ 등록됨 (registered) → 사용완료 (used)
    │
    └─→ 취소요청 (cancel_requested)
            ├─→ 취소됨 (cancelled) [포인트 환불]
            └─→ 발행됨 (issued) [반려 시 복구]
```

### 체크사항

#### 오류 수정
- [x] 체척업체 목록 조회 시 `manager_phone` 필드 오류 수정
- [x] 재고 부족 품목 조회 시 property 비교 오류 수정
- [x] 사용자 검색 API 권한 문제 수정

#### 정책 변경
- [x] 체척권 취소 시 관리자 승인 필요
- [x] 취소 승인 시에만 포인트 환불
- [x] 취소 반려 시 원래 상태로 복구

#### 기능 검증
- [x] Frontend Build 성공
- [x] Backend API 응답 정상
- [x] Git Commit 완료
- [x] GitHub Push 완료

---

## [2026-02-18] - 초기 릴리즈

### 추가 (Added)
- 사용자 관리 (CRUD)
- 피복 품목 관리
- 카테고리 관리
- 피복판매소 관리
- 체척업체 관리
- 포인트 지급
- 오프라인 판매
- 재고 관리
- 피복 쇼핑
- 주문 관리
