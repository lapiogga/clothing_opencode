from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel

from app.models.point import PointType, TransactionType


class PointGrantBase(BaseModel):
    user_id: int
    year: int
    point_type: PointType
    base_amount: int
    service_year_bonus: int = 0
    daily_calc_amount: int = 0
    description: Optional[str] = None


class PointGrantCreate(PointGrantBase):
    pass


class PointGrantYearlyCreate(BaseModel):
    year: int
    user_ids: Optional[List[int]] = None
    point_type: PointType = PointType.ANNUAL
    grant_date: date


class PointGrantResponse(PointGrantBase):
    id: int
    total_amount: int
    grant_date: date
    granted_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PointTransactionResponse(BaseModel):
    id: int
    user_id: int
    transaction_type: TransactionType
    amount: int
    balance_after: int
    reserved_after: int
    order_id: Optional[int] = None
    voucher_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PointHistoryResponse(BaseModel):
    items: List[PointTransactionResponse]
    total: int
    page: int
    page_size: int


class MyPointResponse(BaseModel):
    current_point: int
    reserved_point: int
    available_point: int
    grants: List[PointGrantResponse]


class PointUseRequest(BaseModel):
    amount: int
    order_id: Optional[int] = None
    voucher_id: Optional[int] = None
    description: Optional[str] = None


class PointReserveRequest(BaseModel):
    amount: int
    order_id: Optional[int] = None
    description: Optional[str] = None


class PointBulkGrantRequest(BaseModel):
    target: str = "all"
    rank_id: Optional[int] = None
    amount: int
    reason: str
    note: Optional[str] = None


class PointSingleGrantRequest(BaseModel):
    user_id: int
    amount: int
    reason: str
    note: Optional[str] = None
