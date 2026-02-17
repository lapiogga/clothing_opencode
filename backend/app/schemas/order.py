from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.order import OrderStatus, OrderType, DeliveryStatus, DeliveryType, PaymentMethod


class OrderItemCreate(BaseModel):
    item_id: int
    spec_id: Optional[int] = None
    quantity: int = 1
    payment_method: PaymentMethod = PaymentMethod.POINT


class OrderCreate(BaseModel):
    sales_office_id: int
    order_type: OrderType
    items: list[OrderItemCreate]
    delivery_type: Optional[DeliveryType] = None
    delivery_location_id: Optional[int] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    delivery_note: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str] = None
    spec_id: Optional[int]
    spec_size: Optional[str] = None
    quantity: int
    unit_price: int
    total_price: int
    payment_method: PaymentMethod
    is_returned: bool

    class Config:
        from_attributes = True


class DeliveryLocationResponse(BaseModel):
    id: int
    name: str
    address: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

    class Config:
        from_attributes = True


class DeliveryResponse(BaseModel):
    id: int
    delivery_type: DeliveryType
    status: DeliveryStatus
    delivery_location_id: Optional[int] = None
    delivery_location: Optional[DeliveryLocationResponse] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    tracking_number: Optional[str]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    sales_office_id: int
    order_type: OrderType
    status: OrderStatus
    total_amount: int
    reserved_point: int
    used_point: int
    used_voucher_amount: int
    ordered_at: datetime
    items: list[OrderItemResponse] = []
    delivery: Optional[DeliveryResponse] = None

    class Config:
        from_attributes = True


class DeliveryUpdate(BaseModel):
    status: Optional[DeliveryStatus] = None
    tracking_number: Optional[str] = None
    delivery_note: Optional[str] = None


class OrderCancel(BaseModel):
    reason: str


class OrderListResponse(BaseModel):
    total: int
    items: list[OrderResponse]
