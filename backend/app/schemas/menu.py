"""
메뉴 관련 스키마
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MenuBase(BaseModel):
    name: str
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_category: bool = False
    is_active: bool = True
    allowed_roles: List[str] = []


class MenuCreate(MenuBase):
    pass


class MenuUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_category: Optional[bool] = None
    is_active: Optional[bool] = None
    allowed_roles: Optional[List[str]] = None


class MenuResponse(BaseModel):
    id: int
    name: str
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int
    is_category: bool
    is_active: bool
    allowed_roles: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MenuTreeResponse(BaseModel):
    id: int
    name: str
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int
    is_category: bool
    is_active: bool
    allowed_roles: List[str]
    children: List["MenuTreeResponse"] = []
    created_at: datetime

    class Config:
        from_attributes = True


class MenuListResponse(BaseModel):
    items: List[MenuResponse]
    total: int
