# 프로젝트 문서

> 군 피복 구매관리 시스템 문서 인덱스

## 문서 목록

### 📋 기획 문서

| 문서 | 설명 | 파일 |
|------|------|------|
| 요구사항 정의서 | 시스템 요구사항 정의 | [requirements.md](requirements.md) |
| 프로젝트 기획서 | 프로젝트 계획 및 진행 현황 | [project-plan.md](project-plan.md) |

### 🗄️ 설계 문서

| 문서 | 설명 | 파일 |
|------|------|------|
| DB 스키마 설계서 | 데이터베이스 테이블 설계 | [db-schema.md](db-schema.md) |
| API 명세서 | REST API 엔드포인트 문서 | [api-spec.md](api-spec.md) |
| 화면설계서 | UI/UX 디자인 가이드 | [ui-design.md](ui-design.md) |

### 📖 개발 가이드

| 문서 | 설명 | 파일 |
|------|------|------|
| 개발자 가이드 | 개발 환경 설정 및 코딩 컨벤션 | [developer-guide.md](developer-guide.md) |
| AGENTS.md | AI 코딩 에이전트용 가이드라인 | [AGENTS.md](../AGENTS.md) |
| README.md | 프로젝트 개요 및 실행 가이드 | [README.md](../README.md) |

### ✅ 테스트 문서

| 문서 | 설명 | 파일 |
|------|------|------|
| 포인트 정합성 테스트 결과서 | 포인트 시스템 5회 반복 검증 | [test-results.md](test-results.md) |
| 화면간 정합성 테스트 결과서 | 화면간 CRUD 정합성 10회 반복 검증 | [test-screen-integrity.md](test-screen-integrity.md) |

### 🎯 스킬 파일

| 문서 | 설명 | 파일 |
|------|------|------|
| 피복 구매관리 시스템 스킬 | 도메인 지식 및 코딩 패턴 | [.skills/clothing-system.md](../.skills/clothing-system.md) |

## 빠른 링크

### 시작하기

1. [README.md](../README.md) - 프로젝트 개요 및 설치
2. [개발자 가이드](developer-guide.md) - 개발 환경 설정
3. [요구사항 정의서](requirements.md) - 기능 요구사항
4. [AGENTS.md](../AGENTS.md) - 개발 가이드라인

### 개발 참조

- [DB 스키마](db-schema.md) - 테이블 구조, 필드 설명
- [API 명세서](api-spec.md) - 엔드포인트, 요청/응답 형식
- [화면설계서](ui-design.md) - UI 컴포넌트, 레이아웃

### 테스트 참조

- [테스트 결과서](test-results.md) - 포인트 정합성 5회 반복 테스트 결과

### 최근 변경사항 (2026-02)

#### 포인트 시스템 정합성 개선
- 온라인 구매: 예약 포인트 증가 → 수령 시 차감/해제
- 오프라인 구매: 즉시 차감
- 체척권 발행: 즉시 차감, 취소 승인 시 복원
- 5회 반복 정합성 테스트 100% 통과

#### Shop.vue 리팩토링
- 품목 단위로 그룹화하여 표시
- 완제품: 팝업에서 규격 선택 후 주문
- 맞춤피복: "바로구매" 클릭 시 체척권 즉시 발행
- 보유/예약/사용가능 포인트 표시 추가

### 주요 변경사항 (2024-01)

#### 필드 네이밍 통일

| 이전 | 현재 | 설명 |
|------|------|------|
| employee_id | service_number | 군번 |
| department | unit | 소속 |
| position | rank.name | 계급 |
| points | current_point | 보유 포인트 |

#### API 구조 개선

- `/api/orders` - 사용자용 주문 API
- `/api/sales/orders` - 판매소용 주문 관리 API

## 문서 업데이트 이력

| 일자 | 문서 | 변경 내용 |
|------|------|----------|
| 2025-02 | developer-guide.md | 개발자 가이드 신규 작성 |
| 2025-02 | project-plan.md | 완료 기능 업데이트 |
| 2025-02 | api-spec.md | 체척권 직접 발행 API 추가 |
| 2025-02 | ui-design.md | Shop, OfflineSale 화면 설계 업데이트 |
| 2025-02 | .skills/clothing-system.md | 스킬 파일 신규 작성 |
| 2024-01 | 전체 | 초기 문서 생성 |
| 2024-01 | AGENTS.md | 개발 가이드라인 정리 |
| 2024-01 | db-schema.md | 전체 테이블 문서화 |
| 2024-01 | api-spec.md | 전체 API 문서화 |
| 2024-01 | ui-design.md | 화면설계서 작성 |
| 2024-01 | project-plan.md | 기획서 업데이트 |
