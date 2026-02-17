# 프로젝트 문서

> 군 피복 구매관리 시스템 문서 인덱스

## 문서 목록

### 📋 기획 문서

| 문서 | 설명 | 파일 |
|------|------|------|
| 요구사항 정의서 | 시스템 요구사항 정의 | [clothing_requirement.txt](../clothing_requirement.txt) |
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
| AGENTS.md | AI 코딩 에이전트용 가이드라인 | [AGENTS.md](../AGENTS.md) |
| README.md | 프로젝트 개요 및 실행 가이드 | [README.md](../README.md) |

## 빠른 링크

### 시작하기

1. [README.md](../README.md) - 프로젝트 개요 및 설치
2. [요구사항 정의서](../clothing_requirement.txt) - 기능 요구사항
3. [AGENTS.md](../AGENTS.md) - 개발 가이드라인

### 개발 참조

- [DB 스키마](db-schema.md) - 테이블 구조, 필드 설명
- [API 명세서](api-spec.md) - 엔드포인트, 요청/응답 형식
- [화면설계서](ui-design.md) - UI 컴포넌트, 레이아웃

### 주요 변경사항

#### 필드 네이밍 통일 (2024-01)

| 이전 | 현재 | 설명 |
|------|------|------|
| employee_id | service_number | 군번 |
| department | unit | 소속 |
| position | rank.name | 계급 |
| points | current_point | 보유 포인트 |

#### API 구조 개선 (2024-01)

- `/api/orders` - 사용자용 주문 API
- `/api/sales/orders` - 판매소용 주문 관리 API

## 문서 업데이트 이력

| 일자 | 문서 | 변경 내용 |
|------|------|----------|
| 2024-01 | 전체 | 초기 문서 생성 |
| 2024-01 | AGENTS.md | 개발 가이드라인 정리 |
| 2024-01 | db-schema.md | 전체 테이블 문서화 |
| 2024-01 | api-spec.md | 전체 API 문서화 |
| 2024-01 | ui-design.md | 화면설계서 작성 |
| 2024-01 | project-plan.md | 기획서 업데이트 |
