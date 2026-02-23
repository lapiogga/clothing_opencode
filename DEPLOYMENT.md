# 배포 가이드 (Vercel + Railway + Supabase)

## 개요

이 프로젝트는 3개 서비스로 분리 배포합니다:
- **Frontend**: Vue 3 + Vite → [Vercel](https://vercel.com) (무료)
- **Backend**: FastAPI → [Railway](https://railway.app) (무료 플랜)
- **Database**: PostgreSQL → [Supabase](https://supabase.com) (무료 플랜)

---

## 1단계: Supabase 설정 (데이터베이스)

### 1-1. Supabase 프로젝트 생성

1. https://supabase.com 접속 → Sign up / Log in
2. **New Project** 클릭
3. 프로젝트 정보 입력:
   - **Name**: `clothing-system`
   - **Database Password**: 강력한 비밀번호 (저장 필수!)
   - **Region**: Northeast Asia (Seoul)
4. **Create new project** → 약 2분 대기

### 1-2. 데이터베이스 연결 문자열 확인

1. 프로젝트 대시보드 → **Settings** → **Database**
2. **Connection string** → **URI** 탭
3. 연결 문자열 복사:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
   ```

---

## 2단계: Railway 배포 (백엔드)

### 2-1. Railway 프로젝트 생성

1. https://railway.app 접속 → **Start a New Project**
2. **Deploy from GitHub repo** 선택
3. GitHub 저장소 연결 (`clothing-system`)
4. **Root Directory** 설정: `backend`
5. **Variables** 탭에서 환경변수 추가:

   | Name | Value |
   |------|-------|
   | `DATABASE_URL` | Supabase 연결 문자열 |
   | `SECRET_KEY` | 랜덤 문자열 (32자 이상) |
   | `PORT` | 8000 (또는 Railway 자동 할당) |

6. **Deploy** 클릭

### 2-2. 백엔드 URL 확인

Railway 배포 완료 후, 생성된 URL 확인:
- 예: `https://clothing-system-backend.up.railway.app`

### 2-3. 데이터베이스 초기화

```bash
# 로컬에서 Supabase DB에 연결하여 테이블 생성
cd backend
DATABASE_URL="postgresql://..." python init_db.py
```

---

## 3단계: Vercel 배포 (프론트엔드)

### 3-1. Vercel 프로젝트 생성

1. https://vercel.com 접속 → **Add New Project**
2. GitHub 저장소 선택 (`clothing-system`)
3. **Root Directory**: `frontend`
4. **Framework Preset**: Vite
5. **Environment Variables**:

   | Name | Value |
   |------|-------|
   | `VITE_API_URL` | Railway 백엔드 URL (예: https://xxx.up.railway.app) |

6. **Deploy** 클릭

### 3-2. 프론트엔드 URL 확인

- 예: `https://clothing-system.vercel.app`

---

## 4단계: CORS 설정

백엔드에서 프론트엔드 도메인 허용 필요:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://clothing-system.vercel.app",  # 프론트엔드 URL
        "http://localhost:5173"  # 로컬 개발용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 배포 상태

| 서비스 | URL | 상태 |
|--------|-----|------|
| Frontend | https://frontend-two-sage-60.vercel.app | ✅ 배포 완료 |
| Backend | Railway에서 배포 필요 | ⏳ 대기 |
| Database | Supabase 설정 필요 | ⏳ 대기 |

---

## 비용 안내

| 서비스 | 무료 한도 |
|--------|----------|
| Vercel | 월 100GB 대역폭, 무제한 배포 |
| Railway | 월 $5 크레딧 (Hobby 플랜) |
| Supabase | 500MB DB, 1GB 파일 저장, 5GB 대역폭 |

---

## 문제 해결

### API 연결 실패

1. Railway 백엔드가 실행 중인지 확인
2. `VITE_API_URL` 환경변수가 올바른지 확인
3. CORS 설정 확인

### 로그인 실패

1. Supabase DB에 테이블이 생성되었는지 확인
2. `init_db.py` 실행하여 시드 데이터 생성
