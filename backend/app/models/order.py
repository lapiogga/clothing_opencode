"""
주문 모델 정의
- 주문, 주문품목, 배송 관련 SQLAlchemy 모델
"""
import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean, Numeric, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin


class OrderStatus(str, enum.Enum):
    """
    주문 상태 Enum
    - PENDING: 주문 접수 (온라인 결제 대기)
    - CONFIRMED: 주문 확정
    - PROCESSING: 상품 준비중
    - SHIPPED: 배송중
    - DELIVERED: 배송완료
    - RECEIVED: 수령완료
    - CANCELLED: 주문 취소
    - RETURNED: 반품
    - REFUNDED: 환불 완료
    """
    PENDING = "pending"           # 주문 접수
    CONFIRMED = "confirmed"       # 주문 확정
    PROCESSING = "processing"     # 상품 준비중
    SHIPPED = "shipped"           # 배송중
    DELIVERED = "delivered"       # 배송완료
    RECEIVED = "received"         # 수령완료
    CANCELLED = "cancelled"       # 주문 취소
    RETURNED = "returned"         # 반품
    REFUNDED = "refunded"         # 환불 완료


class OrderType(str, enum.Enum):
    """주문 유형 Enum"""
    ONLINE = "online"     # 온라인 주문
    OFFLINE = "offline"   # 오프라인 판매 (판매소 직접 방문)


class DeliveryType(str, enum.Enum):
    """배송 유형 Enum"""
    PARCEL = "parcel"   # 택배 배송
    DIRECT = "direct"   # 직접 수령


class DeliveryStatus(str, enum.Enum):
    """배송 상태 Enum"""
    PREPARING = "preparing"       # 배송 준비중
    IN_TRANSIT = "in_transit"     # 배송중
    DELIVERED = "delivered"       # 배송 완료
    FAILED = "failed"             # 배송 실패


class PaymentMethod(str, enum.Enum):
    """결제 수단 Enum"""
    POINT = "point"       # 포인트 결제
    VOUCHER = "voucher"   # 체척권 결제


class Order(Base, TimestampMixin):
    """
    주문 테이블
    - 온라인/오프라인 주문 정보 관리
    - 포인트 예약, 사용, 취소 등 상태 관리
    """
    __tablename__ = "orders"

    # 주문 기본 정보
    order_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    sales_office_id: Mapped[int] = mapped_column(ForeignKey("sales_offices.id"), nullable=False, index=True)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # 금액 정보
    total_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)            # 총 주문 금액
    reserved_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)          # 예약 포인트
    used_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)              # 사용 포인트
    used_voucher_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)     # 체척권 사용액
    
    # 주문 일시
    ordered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 취소 정보
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # 관계 매핑
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="orders")
    sales_office: Mapped["SalesOffice"] = relationship("SalesOffice", back_populates="orders")
    canceller: Mapped["User | None"] = relationship("User", foreign_keys=[cancelled_by])
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")
    delivery: Mapped["Delivery | None"] = relationship("Delivery", back_populates="order", uselist=False)
    point_transactions: Mapped[list["PointTransaction"]] = relationship("PointTransaction", back_populates="order")
    tailor_vouchers: Mapped[list["TailorVoucher"]] = relationship("TailorVoucher", back_populates="order")


class OrderItem(Base, TimestampMixin):
    """
    주문 품목 테이블
    - 주문에 포함된 개별 품목 정보
    """
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("clothing_items.id"), nullable=False)
    spec_id: Mapped[int | None] = mapped_column(ForeignKey("clothing_specs.id"), nullable=True)  # 맞춤 피복은 null
    
    # 수량 및 금액
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 결제 방식
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False, default=PaymentMethod.POINT)
    
    # 반품 정보
    is_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    return_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 관계 매핑
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    item: Mapped["ClothingItem"] = relationship("ClothingItem", back_populates="order_items")
    spec: Mapped["ClothingSpec | None"] = relationship("ClothingSpec", back_populates="order_items")


class DeliveryLocation(Base, TimestampMixin):
    """
    배송지 테이블
    - 판매소별 직접 수령 가능한 배송지 관리
    """
    __tablename__ = "delivery_locations"

    sales_office_id: Mapped[int] = mapped_column(ForeignKey("sales_offices.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)                 # 배송지명
    address: Mapped[str] = mapped_column(String(200), nullable=False)              # 주소
    contact_person: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 담당자
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)   # 연락처
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 관계 매핑
    sales_office: Mapped["SalesOffice"] = relationship("SalesOffice", back_populates="delivery_locations")
    deliveries: Mapped[list["Delivery"]] = relationship("Delivery", back_populates="delivery_location")


class Delivery(Base, TimestampMixin):
    """
    배송 정보 테이블
    - 주문별 배송 상태 및 정보 관리
    """
    __tablename__ = "deliveries"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    delivery_type: Mapped[DeliveryType] = mapped_column(Enum(DeliveryType), nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.PREPARING, nullable=False)
    
    # 배송지 정보
    delivery_location_id: Mapped[int | None] = mapped_column(ForeignKey("delivery_locations.id"), nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # 배송 추적
    tracking_number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 운송장 번호
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)    # 발송일시
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 도착일시
    delivery_note: Mapped[str | None] = mapped_column(Text, nullable=True)          # 배송 비고

    # 관계 매핑
    order: Mapped["Order"] = relationship("Order", back_populates="delivery")
    delivery_location: Mapped["DeliveryLocation | None"] = relationship("DeliveryLocation", back_populates="deliveries")


# 순환 참조 해결을 위한 지연 import
from app.models.user import User
from app.models.clothing import ClothingItem, ClothingSpec
from app.models.sales import SalesOffice
from app.models.tailor import TailorVoucher
from app.models.point import PointTransaction
