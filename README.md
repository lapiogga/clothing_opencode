# 피복 구매관리 시스템

군 피복 구매관리 시스템 - FastAPI + Vue 3 + SQLite

## 시스템 요구사항

- Python 3.11+
- Node.js 18+
- pip 또는 uv

## 설치

### 백엔드

```bash
cd clothing-system/backend

# 의존성 설치
pip install -r requirements.txt

# 또는 uv 사용
uv pip install -r requirements.txt

# DB 초기화 및 시드 데이터 생성
python3 init_db.py
```

### 프론트엔드

```bash
cd clothing-system/frontend

# 의존성 설치
npm install
# 또는
bun install
```

## 실행

### 백엔드

```bash
cd clothing-system/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드

```bash
cd clothing-system/frontend
npm run dev
# 또는
bun run dev
```

## 테스트 계정

| ID | 비밀번호 | 역할 | 군번 |
|----|---------|------|------|
| admin | admin123 | 군수담당자 | 20-123456 |
| sales1 | sales123 | 피복판매소담당자 | 30-100001 |
| sales2 | sales123 | 피복판매소담당자 | 30-100002 |
| sales3 | sales123 | 피복판매소담당자 | 30-100003 |
| tailor1 | tailor123 | 체척업체담당자 | 40-200001 |
| tailor2 | tailor123 | 체척업체담당자 | 40-200002 |
| user01 | user123 | 일반사용자 | 21-100001 |
| user02 | user123 | 일반사용자 | 15-100002 |
| ... | ... | ... | ... |
| user10 | user123 | 일반사용자 | 10-100010 |

## 계급 체계

| 계급 | 계급장군 | 연간포인트 |
|------|---------|-----------|
| 장성급 | 장교 | 1,000,000P |
| 대령 | 장교 | 800,000P |
| 소령 | 장교 | 800,000P |
| 대위 | 장교 | 600,000P |
| 소위 | 장교 | 600,000P |
| 준위 | 장교 | 500,000P |
| 상사 | 부사관 | 450,000P |
| 중사 | 부사관 | 400,000P |
| 하사 | 부사관 | 350,000P |
| 군무원 | 군무원 | 400,000P |

## API 문서

백엔드 실행 후:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 디렉토리 구조

```
clothing-system/
├── backend/
│   ├── app/
│   │   ├── models/      # SQLAlchemy 모델
│   │   ├── schemas/     # Pydantic 스키마
│   │   ├── routers/     # API 라우터
│   │   ├── services/    # 비즈니스 로직
│   │   └── utils/       # 유틸리티
│   ├── tests/
│   ├── init_db.py       # DB 초기화
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── views/       # 페이지 컴포넌트
│   │   ├── components/  # 재사용 컴포넌트
│   │   ├── stores/      # Pinia 스토어
│   │   ├── router/      # Vue Router
│   │   └── api/         # API 호출
│   └── package.json
│
└── docs/
    ├── api-spec.md      # API 명세서
    ├── db-schema.md     # DB 스키마
    └── ui-design.md     # 화면설계서
```

## 사용자 역할

1. **군수담당자 (ADMIN)**: 전체 시스템 관리
2. **피복판매소담당자 (SALES_OFFICE)**: 오프라인 판매, 재고관리
3. **체척업체담당자 (TAILOR_COMPANY)**: 체척권 등록
4. **일반사용자 (NORMAL)**: 피복 구매

## 주요 기능

- 사용자 관리 (일괄 등록, 진급 처리)
- 피복 품목 관리 (대/중/소분류)
- 피복포인트 관리 (계급별 지급, 일할계산)
- 오프라인 판매 및 반품
- 온라인 구매 및 배송
- 재고 관리
- 체척권 관리
- 통계 및 정산
