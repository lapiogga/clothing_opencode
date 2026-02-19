from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole, UserRank, UserRankGroup


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.GENERAL
    rank_id: Optional[int] = None
    service_number: str
    unit: Optional[str] = None
    enlistment_date: Optional[date] = None
    retirement_date: Optional[date] = None


class UserCreate(UserBase):
    username: str
    password: str
    sales_office_id: Optional[int] = None
    tailor_company_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    rank_id: Optional[int] = None
    service_number: Optional[str] = None
    unit: Optional[str] = None
    enlistment_date: Optional[date] = None
    retirement_date: Optional[date] = None
    is_active: Optional[bool] = None
    sales_office_id: Optional[int] = None
    tailor_company_id: Optional[int] = None


class RankResponse(BaseModel):
    id: int
    name: str
    code: UserRank
    rank_group: UserRankGroup
    annual_point: int
    service_year_bonus: int

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    rank: Optional[RankResponse] = None
    service_number: str
    unit: Optional[str] = None
    service_years: int
    enlistment_date: Optional[date] = None
    retirement_date: Optional[date] = None
    is_active: bool
    current_point: int
    reserved_point: int
    available_point: int
    sales_office_id: Optional[int] = None
    tailor_company_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class UserBulkImport(BaseModel):
    users: List[UserCreate]


class UserPointResponse(BaseModel):
    user_id: int
    current_point: int
    reserved_point: int
    available_point: int
    annual_grants: List["PointGrantResponse"]


class PromoteRequest(BaseModel):
    new_rank_id: int
    promotion_date: date


class PromoteResponse(BaseModel):
    user_id: int
    old_rank: Optional[RankResponse]
    new_rank: RankResponse
    point_adjustment: int
    promotion_date: date


from app.schemas.point import PointGrantResponse
UserPointResponse.model_rebuild()
