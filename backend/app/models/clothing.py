import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin


class ClothingType(str, enum.Enum):
    READY_MADE = "ready_made"
    CUSTOM = "custom"


class CategoryLevel(str, enum.Enum):
    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[CategoryLevel] = mapped_column(Enum(CategoryLevel), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    parent: Mapped["Category | None"] = relationship("Category", remote_side="Category.id", backref="children")
    items: Mapped[list["ClothingItem"]] = relationship("ClothingItem", back_populates="category")


class ClothingItem(Base, TimestampMixin):
    __tablename__ = "clothing_items"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    clothing_type: Mapped[ClothingType] = mapped_column(Enum(ClothingType), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship("Category", back_populates="items")
    specs: Mapped[list["ClothingSpec"]] = relationship("ClothingSpec", back_populates="item")
    inventory_items: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="item")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="item")
    tailor_vouchers: Mapped[list["TailorVoucher"]] = relationship("TailorVoucher", back_populates="item")


class ClothingSpec(Base, TimestampMixin):
    __tablename__ = "clothing_specs"
    __table_args__ = (UniqueConstraint("item_id", "spec_code", name="uq_clothing_spec"),)

    item_id: Mapped[int] = mapped_column(ForeignKey("clothing_items.id"), nullable=False, index=True)
    spec_code: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    item: Mapped["ClothingItem"] = relationship("ClothingItem", back_populates="specs")
    inventory_items: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="spec")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="spec")


from app.models.sales import Inventory
from app.models.order import OrderItem
from app.models.tailor import TailorVoucher
