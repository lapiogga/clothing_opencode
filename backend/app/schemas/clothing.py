from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.clothing import ClothingType, CategoryLevel


class CategoryBase(BaseModel):
    name: str
    level: CategoryLevel
    parent_id: Optional[int] = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryTreeResponse(CategoryResponse):
    children: List["CategoryTreeResponse"] = []


class ClothingBase(BaseModel):
    name: str
    category_id: int
    clothing_type: ClothingType
    image_url: Optional[str] = None
    description: Optional[str] = None


class ClothingCreate(ClothingBase):
    pass


class ClothingUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    clothing_type: Optional[ClothingType] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SpecBase(BaseModel):
    spec_code: str
    size: str
    price: int


class SpecCreate(SpecBase):
    pass


class SpecUpdate(BaseModel):
    spec_code: Optional[str] = None
    size: Optional[str] = None
    price: Optional[int] = None
    is_active: Optional[bool] = None


class SpecResponse(SpecBase):
    id: int
    item_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ClothingResponse(ClothingBase):
    id: int
    is_active: bool
    created_at: datetime
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


class ClothingDetailResponse(ClothingResponse):
    specs: List[SpecResponse] = []


class ClothingListResponse(BaseModel):
    items: List[ClothingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


CategoryTreeResponse.model_rebuild()
