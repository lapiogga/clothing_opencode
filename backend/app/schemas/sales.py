from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.models.order import PaymentMethod
from app.models.sales import AdjustmentType


class OfflineSaleItem(BaseModel):
    item_id: int
    spec_id: Optional[int] = None
    quantity: int = 1
    unit_price: int
    payment_method: PaymentMethod = PaymentMethod.POINT


class OfflineSaleCreate(BaseModel):
    user_id: int
    sales_office_id: int
    items: list[OfflineSaleItem]


class RefundItem(BaseModel):
    order_item_id: int
    quantity: int = 1
    reason: Optional[str] = None


class RefundCreate(BaseModel):
    order_id: int
    items: list[RefundItem]


class InventoryAdjust(BaseModel):
    sales_office_id: int
    item_id: int
    spec_id: Optional[int] = None
    adjustment_type: AdjustmentType
    quantity: int
    reason: Optional[str] = None


class InventoryReceive(BaseModel):
    sales_office_id: int
    item_id: int
    spec_id: Optional[int] = None
    quantity: int


class InventoryResponse(BaseModel):
    id: int
    sales_office_id: int
    item_id: int
    spec_id: Optional[int]
    quantity: int
    reserved_quantity: int
    available_quantity: int

    class Config:
        from_attributes = True


class InventoryHistoryResponse(BaseModel):
    id: int
    inventory_id: int
    adjustment_type: AdjustmentType
    quantity: int
    before_quantity: int
    after_quantity: int
    reason: Optional[str]
    adjustment_date: date

    class Config:
        from_attributes = True


class SalesHistoryItem(BaseModel):
    id: int
    order_number: str
    user_name: str
    total_amount: int
    ordered_at: str
    status: str

    class Config:
        from_attributes = True


class SalesHistoryResponse(BaseModel):
    total: int
    items: list[SalesHistoryItem]
