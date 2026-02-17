from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.tailor import VoucherStatus


class VoucherCreate(BaseModel):
    user_id: int
    order_id: int
    order_item_id: int
    item_id: int
    amount: int
    expires_at: Optional[date] = None
    notes: Optional[str] = None


class VoucherRegister(BaseModel):
    voucher_id: int
    tailor_company_id: int


class VoucherCancelRequest(BaseModel):
    reason: str


class VoucherApproveCancel(BaseModel):
    approved: bool
    note: Optional[str] = None


class VoucherResponse(BaseModel):
    id: int
    voucher_number: str
    user_id: int
    tailor_company_id: Optional[int]
    order_id: Optional[int]
    item_id: int
    amount: int
    status: VoucherStatus
    issued_at: datetime
    registered_at: Optional[datetime]
    used_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_reason: Optional[str]
    expires_at: Optional[date]

    class Config:
        from_attributes = True


class VoucherListResponse(BaseModel):
    total: int
    items: list[VoucherResponse]
