import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# PostgreSQL 연결 문자열
# 개발: 로컬 Docker PostgreSQL
# 운영: Supabase PostgreSQL
DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/clothing_system"

# 환경변수에서 DB URL 가져오기 (Supabase PostgreSQL)
# DATABASE_URL이 설정되지 않으면 로컬 PostgreSQL 사용
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# PostgreSQL 연결 문자열 변환 (postgres:// → postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite 여부 확인
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # 로컬 개발용 SQLite (비추천)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # PostgreSQL (Supabase 또는 로컬 Docker)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import (
        user,
        clothing,
        sales,
        order,
        tailor,
        point,
        menu
    )
    Base.metadata.create_all(bind=engine)
