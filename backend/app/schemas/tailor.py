from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.tailor import VoucherStatus


class TailorCompanyBase(BaseModel):
    name: str
    code: str
    business_number: Optional[str] = None
    address: str
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    is_active: bool = True


class TailorCompanyCreate(TailorCompanyBase):
    pass


class TailorCompanyUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    business_number: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    is_active: Optional[bool] = None


class VoucherCreate(BaseModel):
    user_id: int
    order_id: int
    order_item_id: int
    item_id: int
    amount: int
    expires_at: Optional[date] = None
    notes: Optional[str] = None


class VoucherIssueDirect(BaseModel):
    """맞춤피복 직접 체척권 발행용 (주문 없이)"""
    user_id: int
    item_id: int
    amount: int
    sales_office_id: int
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
    item: Optional[dict] = None
    amount: int
    status: VoucherStatus
    issued_at: datetime
    registered_at: Optional[datetime]
    used_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_reason: Optional[str]
    expires_at: Optional[date]
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class VoucherListResponse(BaseModel):
    total: int
    items: list[VoucherResponse]
