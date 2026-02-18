from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole
from app.models.clothing import ClothingType
from app.schemas.clothing import (
    ClothingCreate, ClothingUpdate, ClothingResponse,
    ClothingDetailResponse, ClothingListResponse,
    SpecCreate, SpecUpdate, SpecResponse,
)
from app.services.clothing_service import ClothingService
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


@router.get("", response_model=ClothingListResponse)
def get_clothings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    clothing_type: Optional[ClothingType] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = ClothingService(db)
    return service.get_list(
        page=page,
        page_size=page_size,
        category_id=category_id,
        clothing_type=clothing_type,
        is_active=is_active,
        keyword=keyword,
    )


@router.post("", response_model=ClothingResponse, status_code=status.HTTP_201_CREATED)
def create_clothing(
    data: ClothingCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = ClothingService(db)
    try:
        item = service.create(data)
        return service._to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{clothing_id}", response_model=ClothingDetailResponse)
def get_clothing(
    clothing_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = ClothingService(db)
    result = service.get_detail(clothing_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="품목을 찾을 수 없습니다")
    return result


@router.put("/{clothing_id}", response_model=ClothingResponse)
def update_clothing(
    clothing_id: int,
    data: ClothingUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = ClothingService(db)
    try:
        item = service.update(clothing_id, data)
        return service._to_response(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{clothing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clothing(
    clothing_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = ClothingService(db)
    try:
        if not service.delete(clothing_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="품목을 찾을 수 없습니다")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{clothing_id}/specs", response_model=list[SpecResponse])
def get_clothing_specs(
    clothing_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = ClothingService(db)
    specs = service.get_specs(clothing_id)
    return [service._spec_to_response(s) for s in specs]


@router.post("/{clothing_id}/specs", response_model=SpecResponse, status_code=status.HTTP_201_CREATED)
def create_clothing_spec(
    clothing_id: int,
    data: SpecCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = ClothingService(db)
    try:
        spec = service.create_spec(clothing_id, data)
        return service._spec_to_response(spec)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{clothing_id}/specs/{spec_id}", response_model=SpecResponse)
def update_clothing_spec(
    clothing_id: int,
    spec_id: int,
    data: SpecUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = ClothingService(db)
    try:
        spec = service.update_spec(spec_id, data)
        return service._spec_to_response(spec)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{clothing_id}/specs/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clothing_spec(
    clothing_id: int,
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = ClothingService(db)
    if not service.delete_spec(spec_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="규격을 찾을 수 없습니다")


@router.get("/custom/available")
def get_custom_clothings(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    맞춤피복 목록 조회 (재고 관리 없음)
    - 활성화된 맞춤피복 품목과 규격 목록 반환
    """
    from app.models.clothing import ClothingItem, ClothingSpec, Category, ClothingType
    
    items = db.query(ClothingItem).filter(
        ClothingItem.clothing_type == ClothingType.CUSTOM,
        ClothingItem.is_active == True
    ).all()
    
    result = []
    for item in items:
        category = db.query(Category).filter(Category.id == item.category_id).first()
        specs = db.query(ClothingSpec).filter(
            ClothingSpec.item_id == item.id,
            ClothingSpec.is_active == True
        ).all()
        
        for spec in specs:
            result.append({
                "item_id": item.id,
                "spec_id": spec.id,
                "item_name": item.name,
                "category_id": category.id if category else None,
                "category_name": category.name if category else None,
                "clothing_type": "custom",
                "description": item.description,
                "image_url": item.image_url,
                "thumbnail_url": item.thumbnail_url,
                "spec_size": spec.size,
                "spec_price": spec.price,
            })
    
    return {"items": result, "total": len(result)}
