"""
포인트 모델 정의
- 포인트 지급 및 거래 내역 관련 SQLAlchemy 모델
"""
import enum
from datetime import date
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Date, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin


class PointType(str, enum.Enum):
    """
    포인트 지급 유형 Enum
    - ANNUAL: 연간 정기 지급
    - PROMOTION: 진급에 따른 지급
    - RETIREMENT: 전역 시 일할 계산 지급
    - REFUND: 환불에 의한 지급
    - CANCEL: 주문 취소에 의한 지급
    - ADJUSTMENT: 수동 조정
    """
    ANNUAL = "annual"           # 연간 지급
    PROMOTION = "promotion"     # 진급 지급
    RETIREMENT = "retirement"   # 전역 시 일할 계산
    REFUND = "refund"           # 환불
    CANCEL = "cancel"           # 취소
    ADJUSTMENT = "adjustment"   # 조정


class TransactionType(str, enum.Enum):
    """
    포인트 거래 유형 Enum
    - GRANT: 포인트 지급 (증가)
    - USE: 포인트 사용 (차감)
    - RESERVE: 주문 시 포인트 예약
    - RELEASE: 예약 포인트 해제 (환불/취소)
    - REFUND: 환불 포인트 복구
    - DEDUCT: 예약 포인트 차감 (배송 완료 시)
    """
    GRANT = "grant"       # 지급
    USE = "use"           # 사용
    RESERVE = "reserve"   # 예약
    RELEASE = "release"   # 예약 해제
    REFUND = "refund"     # 환불
    DEDUCT = "deduct"     # 차감


class PointGrant(Base, TimestampMixin):
    """
    포인트 지급 내역 테이블
    - 연간/진급/전역 등으로 지급된 포인트 내역 관리
    - 사용자별 연도별 지급유형은 중복 불가 (UniqueConstraint)
    """
    __tablename__ = "point_grants"
    __table_args__ = (UniqueConstraint("user_id", "year", "point_type", name="uq_point_grant"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    point_type: Mapped[PointType] = mapped_column(Enum(PointType), nullable=False)
    
    # 포인트 구성
    base_amount: Mapped[int] = mapped_column(Integer, nullable=False)          # 기본 포인트 (계급별)
    service_year_bonus: Mapped[int] = mapped_column(Integer, default=0)        # 복무년수 보너스
    daily_calc_amount: Mapped[int] = mapped_column(Integer, default=0)         # 일할 계산액 (전역 시)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)         # 총 지급액
    
    # 지급 정보
    grant_date: Mapped[date] = mapped_column(Date, nullable=False)             # 지급일
    description: Mapped[str | None] = mapped_column(Text, nullable=True)       # 비고
    granted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # 지급자

    # 관계 매핑
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="point_grants")
    granter: Mapped["User | None"] = relationship("User", foreign_keys=[granted_by])


class PointTransaction(Base, TimestampMixin):
    """
    포인트 거래 내역 테이블
    - 모든 포인트 변동 사항을 기록 (지급, 사용, 예약, 환불 등)
    - 포인트 이력 추적 및 감사용
    """
    __tablename__ = "point_transactions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)               # 거래 금액
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)        # 거래 후 보유 잔액
    reserved_after: Mapped[int] = mapped_column(Integer, nullable=False)       # 거래 후 예약액
    
    # 연관 정보 (선택)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)
    order_item_id: Mapped[int | None] = mapped_column(ForeignKey("order_items.id"), nullable=True)
    voucher_id: Mapped[int | None] = mapped_column(ForeignKey("tailor_vouchers.id"), nullable=True, index=True)
    point_grant_id: Mapped[int | None] = mapped_column(ForeignKey("point_grants.id"), nullable=True)
    
    description: Mapped[str | None] = mapped_column(Text, nullable=True)       # 거래 설명

    # 관계 매핑
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="point_transactions")
    order: Mapped["Order | None"] = relationship("Order", back_populates="point_transactions")
    order_item: Mapped["OrderItem | None"] = relationship("OrderItem")
    voucher: Mapped["TailorVoucher | None"] = relationship("TailorVoucher", back_populates="point_transactions")
    point_grant: Mapped["PointGrant | None"] = relationship("PointGrant")


# 순환 참조 해결을 위한 지연 import
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.tailor import TailorVoucher
