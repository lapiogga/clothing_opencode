from typing import Optional
from pydantic import BaseModel


class SalesOfficeBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None


class SalesOfficeCreate(SalesOfficeBase):
    pass


class SalesOfficeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: Optional[bool] = None


class SalesOfficeResponse(SalesOfficeBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
