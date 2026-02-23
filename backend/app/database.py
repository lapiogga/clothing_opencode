import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
# 환경변수에서 DB URL 가져오기 (Vercel/Supabase용)
# Supabase: postgresql://user:pass@host:5432/db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clothing.db")

# Supabase/PostgreSQL 연결 문자열 변환
def get_database_url():
    url = DATABASE_URL
    # postgres:// -> postgresql:// 로 변환
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

# SQLite 여부 확인
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # 로컬 개발용 SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # 프로덕션용 PostgreSQL (Supabase)
    engine = create_engine(
        get_database_url(),
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
