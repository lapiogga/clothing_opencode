import enum
from datetime import date
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin


class AdjustmentType(str, enum.Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    RESTOCK = "restock"
    CORRECTION = "correction"
    RETURN = "return"


class SalesOffice(Base, TimestampMixin):
    __tablename__ = "sales_offices"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    manager_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    staff: Mapped[list["User"]] = relationship("User", back_populates="sales_office")
    inventory: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="sales_office")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="sales_office")
    delivery_locations: Mapped[list["DeliveryLocation"]] = relationship("DeliveryLocation", back_populates="sales_office")


class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("sales_office_id", "item_id", "spec_id", name="uq_inventory"),)

    sales_office_id: Mapped[int] = mapped_column(ForeignKey("sales_offices.id"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("clothing_items.id"), nullable=False, index=True)
    spec_id: Mapped[int | None] = mapped_column(ForeignKey("clothing_specs.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    sales_office: Mapped["SalesOffice"] = relationship("SalesOffice", back_populates="inventory")
    item: Mapped["ClothingItem"] = relationship("ClothingItem", back_populates="inventory_items")
    spec: Mapped["ClothingSpec | None"] = relationship("ClothingSpec", back_populates="inventory_items")
    adjustments: Mapped[list["InventoryHistory"]] = relationship("InventoryHistory", back_populates="inventory")

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity


class InventoryHistory(Base, TimestampMixin):
    __tablename__ = "inventory_history"

    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), nullable=False, index=True)
    adjustment_type: Mapped[AdjustmentType] = mapped_column(Enum(AdjustmentType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    before_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    after_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    adjusted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    adjustment_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)

    inventory: Mapped["Inventory"] = relationship("Inventory", back_populates="adjustments")
    adjuster: Mapped["User"] = relationship("User")
    order: Mapped["Order | None"] = relationship("Order")


from app.models.user import User
from app.models.clothing import ClothingItem, ClothingSpec
from app.models.order import Order, DeliveryLocation
