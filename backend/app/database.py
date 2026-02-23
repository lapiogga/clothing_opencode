import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 환경변수에서 DB URL 가져오기 (Supabase PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clothing.db")

# PostgreSQL 연결 문자열 변환 (postgres:// → postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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
