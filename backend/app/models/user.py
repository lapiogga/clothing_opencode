"""
사용자 모델 정의
- 사용자, 계급, 진급이력 관련 SQLAlchemy 모델
"""
import enum
from datetime import date
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Date, Boolean, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    """사용자 권한 Enum"""
    ADMIN = "admin"                     # 관리자 (군수담당자)
    SALES_OFFICE = "sales_office"       # 판매소 담당자
    TAILOR_COMPANY = "tailor_company"   # 체척업체 담당자
    GENERAL = "general"                 # 일반 사용자


class UserRank(str, enum.Enum):
    """
    계급 Enum
    - 장교: 장성급, 대령, 소령, 대위, 소위, 준위
    - 부사관: 상사, 중사, 하사
    - 군무원
    """
    GENERAL_OFFICER = "general_officer"  # 장성급
    COLONEL = "colonel"                  # 대령
    MAJOR = "major"                      # 소령
    CAPTAIN = "captain"                  # 대위
    LIEUTENANT = "lieutenant"            # 소위
    WARRANT_OFFICER = "warrant_officer"  # 준위
    SERGEANT_MAJOR = "sergeant_major"    # 상사
    SERGEANT = "sergeant"                # 중사
    CORPORAL = "corporal"                # 하사
    CIVILIAN = "civilian"                # 군무원


class UserRankGroup(str, enum.Enum):
    """계급장군 Enum (장교/부사관/군무원)"""
    OFFICER = "officer"      # 장교
    NCO = "nco"              # 부사관
    CIVILIAN = "civilian"    # 군무원


# 계급별 연간 포인트 매핑
RANK_POINT_MAPPING = {
    UserRank.GENERAL_OFFICER: 1000000,   # 장성급: 100만점
    UserRank.COLONEL: 800000,            # 대령: 80만점
    UserRank.MAJOR: 800000,              # 소령: 80만점
    UserRank.CAPTAIN: 600000,            # 대위: 60만점
    UserRank.LIEUTENANT: 600000,         # 소위: 60만점
    UserRank.WARRANT_OFFICER: 500000,    # 준위: 50만점
    UserRank.SERGEANT_MAJOR: 450000,     # 상사: 45만점
    UserRank.SERGEANT: 400000,           # 중사: 40만점
    UserRank.CORPORAL: 350000,           # 하사: 35만점
    UserRank.CIVILIAN: 400000,           # 군무원: 40만점
}


class Rank(Base, TimestampMixin):
    """
    계급 마스터 테이블
    - 계급명, 코드, 계급장군, 연간포인트, 복무년수보너스 관리
    """
    __tablename__ = "ranks"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    code: Mapped[UserRank] = mapped_column(Enum(UserRank), nullable=False, unique=True)
    rank_group: Mapped[UserRankGroup] = mapped_column(Enum(UserRankGroup), nullable=False)
    annual_point: Mapped[int] = mapped_column(Integer, nullable=False)
    service_year_bonus: Mapped[int] = mapped_column(Integer, default=5000)  # 복무 1년당 5,000점 추가

    users: Mapped[list["User"]] = relationship("User", back_populates="rank")


class User(Base, TimestampMixin):
    """
    사용자 테이블
    - 시스템 사용자 정보 관리
    - 포인트, 권한, 계급, 소속 등 관리
    """
    __tablename__ = "users"

    # 로그인 정보
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 기본 정보
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    
    # 권한 및 계급
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.GENERAL)
    rank_id: Mapped[int | None] = mapped_column(ForeignKey("ranks.id"), nullable=True)
    
    # 군 정보
    service_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)  # 군번 (필수)
    unit: Mapped[str | None] = mapped_column(String(100))                # 소속
    enlistment_date: Mapped[date | None] = mapped_column(Date, nullable=True)   # 입대일
    retirement_date: Mapped[date | None] = mapped_column(Date, nullable=True)   # 전역예정일
    
    # 상태
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 소속 조직 (판매소 또는 체척업체)
    sales_office_id: Mapped[int | None] = mapped_column(ForeignKey("sales_offices.id"), nullable=True)
    tailor_company_id: Mapped[int | None] = mapped_column(ForeignKey("tailor_companies.id"), nullable=True)
    
    # 포인트 정보
    current_point: Mapped[int] = mapped_column(Integer, default=0)       # 보유 포인트
    reserved_point: Mapped[int] = mapped_column(Integer, default=0)      # 예약 포인트 (주문 중)

    @property
    def service_years(self) -> int:
        """
        복무년수 계산 (입대일 기준)
        - 입대일이 없으면 0 반환
        - 입대일로부터 경과한 전체 년수 계산
        """
        if self.enlistment_date:
            today = date.today()
            years = today.year - self.enlistment_date.year
            # 올해 입대일이 지나지 않았으면 1년 차감
            if (today.month, today.day) < (self.enlistment_date.month, self.enlistment_date.day):
                years -= 1
            return max(0, years)
        return 0

    # 관계 매핑
    rank: Mapped["Rank | None"] = relationship("Rank", back_populates="users")
    sales_office: Mapped["SalesOffice | None"] = relationship("SalesOffice", back_populates="staff")
    tailor_company: Mapped["TailorCompany | None"] = relationship("TailorCompany", back_populates="staff")
    orders: Mapped[list["Order"]] = relationship("Order", foreign_keys="Order.user_id", back_populates="user")
    point_grants: Mapped[list["PointGrant"]] = relationship("PointGrant", foreign_keys="PointGrant.user_id", back_populates="user")
    point_transactions: Mapped[list["PointTransaction"]] = relationship("PointTransaction", foreign_keys="PointTransaction.user_id", back_populates="user")
    rank_histories: Mapped[list["UserRankHistory"]] = relationship("UserRankHistory", back_populates="user")
    tailor_vouchers: Mapped[list["TailorVoucher"]] = relationship("TailorVoucher", foreign_keys="TailorVoucher.user_id", back_populates="user")

    @property
    def available_point(self) -> int:
        """사용 가능한 포인트 (보유 - 예약)"""
        return self.current_point - self.reserved_point


class UserRankHistory(Base, TimestampMixin):
    """
    진급 이력 테이블
    - 사용자의 진급 내역 및 포인트 조정 이력 관리
    """
    __tablename__ = "user_rank_histories"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    old_rank_id: Mapped[int | None] = mapped_column(ForeignKey("ranks.id"), nullable=True)      # 이전 계급
    new_rank_id: Mapped[int] = mapped_column(ForeignKey("ranks.id"), nullable=False)            # 진급 후 계급
    promotion_date: Mapped[date] = mapped_column(Date, nullable=False)                          # 진급일
    point_adjustment: Mapped[int] = mapped_column(Integer, default=0)                           # 포인트 조정액

    # 관계 매핑
    user: Mapped["User"] = relationship("User", back_populates="rank_histories")
    old_rank: Mapped["Rank | None"] = relationship("Rank", foreign_keys=[old_rank_id])
    new_rank: Mapped["Rank"] = relationship("Rank", foreign_keys=[new_rank_id])


# 순환 참조 해결을 위한 지연 import
from app.models.sales import SalesOffice
from app.models.order import Order
from app.models.tailor import TailorCompany, TailorVoucher
from app.models.point import PointGrant, PointTransaction
