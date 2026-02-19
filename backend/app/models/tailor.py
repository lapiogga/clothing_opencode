import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin


class VoucherStatus(str, enum.Enum):
    ISSUED = "issued"              # 발행됨
    REGISTERED = "registered"      # 등록됨 (체척업체)
    USED = "used"                  # 사용완료
    CANCEL_REQUESTED = "cancel_requested"  # 취소 요청됨
    CANCELLED = "cancelled"        # 취소됨
    EXPIRED = "expired"            # 만료됨


class TailorCompany(Base, TimestampMixin):
    __tablename__ = "tailor_companies"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    business_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    manager_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    staff: Mapped[list["User"]] = relationship("User", back_populates="tailor_company")
    vouchers: Mapped[list["TailorVoucher"]] = relationship("TailorVoucher", back_populates="tailor_company")


class TailorVoucher(Base, TimestampMixin):
    __tablename__ = "tailor_vouchers"

    voucher_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    tailor_company_id: Mapped[int | None] = mapped_column(ForeignKey("tailor_companies.id"), nullable=True, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)
    order_item_id: Mapped[int | None] = mapped_column(ForeignKey("order_items.id"), nullable=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("clothing_items.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[VoucherStatus] = mapped_column(Enum(VoucherStatus), default=VoucherStatus.ISSUED, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    registered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    registered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="tailor_vouchers")
    tailor_company: Mapped["TailorCompany | None"] = relationship("TailorCompany", back_populates="vouchers")
    order: Mapped["Order | None"] = relationship("Order", back_populates="tailor_vouchers")
    order_item: Mapped["OrderItem | None"] = relationship("OrderItem")
    item: Mapped["ClothingItem"] = relationship("ClothingItem", back_populates="tailor_vouchers")
    registrar: Mapped["User | None"] = relationship("User", foreign_keys=[registered_by])
    canceller: Mapped["User | None"] = relationship("User", foreign_keys=[cancelled_by])
    point_transactions: Mapped[list["PointTransaction"]] = relationship("PointTransaction", back_populates="voucher")


from app.models.user import User
from app.models.clothing import ClothingItem
from app.models.order import Order, OrderItem
from app.models.point import PointTransaction
