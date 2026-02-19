"""
배송지 관리 라우터
- 판매소별 배송지 조회, 등록, 수정, 삭제
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import UserRole
from app.models.order import DeliveryLocation
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


class DeliveryLocationCreate(BaseModel):
    sales_office_id: int
    name: str
    address: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None


class DeliveryLocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None


def check_sales_office_or_admin(current_user: TokenData = Depends(get_current_user)):
    """판매소 또는 관리자 권한 확인"""
    allowed_roles = [UserRole.ADMIN.value, UserRole.SALES_OFFICE.value]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다"
        )
    return current_user


@router.get("")
def get_delivery_locations(
    sales_office_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    배송지 목록 조회
    - 관리자: 전체 또는 판매소별 조회
    - 판매소: 자신의 판매소 배송지만 조회
    - 일반 사용자: 지정된 판매소의 배송지만 조회
    """
    query = db.query(DeliveryLocation).filter(DeliveryLocation.is_active == True)
    
    # 판매소 담당자는 자신의 판매소만 조회
    if current_user.role == UserRole.SALES_OFFICE.value:
        from app.services.user_service import UserService
        user = UserService(db).get_by_id(current_user.user_id)
        if user and user.sales_office_id:
            query = query.filter(DeliveryLocation.sales_office_id == user.sales_office_id)
        else:
            return []
    elif sales_office_id:
        query = query.filter(DeliveryLocation.sales_office_id == sales_office_id)
    
    locations = query.order_by(DeliveryLocation.name).all()
    
    return [
        {
            "id": loc.id,
            "sales_office_id": loc.sales_office_id,
            "name": loc.name,
            "address": loc.address,
            "contact_person": loc.contact_person,
            "contact_phone": loc.contact_phone,
        }
        for loc in locations
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_delivery_location(
    data: DeliveryLocationCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_sales_office_or_admin),
) -> Any:
    """배송지 등록"""
    # 판매소 담당자는 자신의 판매소에만 등록 가능
    if current_user.role == UserRole.SALES_OFFICE.value:
        from app.services.user_service import UserService
        user = UserService(db).get_by_id(current_user.user_id)
        if not user or user.sales_office_id != data.sales_office_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="자신의 판매소에만 배송지를 등록할 수 있습니다"
            )
    
    location = DeliveryLocation(
        sales_office_id=data.sales_office_id,
        name=data.name,
        address=data.address,
        contact_person=data.contact_person,
        contact_phone=data.contact_phone,
        is_active=True,
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return {
        "id": location.id,
        "sales_office_id": location.sales_office_id,
        "name": location.name,
        "address": location.address,
        "contact_person": location.contact_person,
        "contact_phone": location.contact_phone,
    }


@router.put("/{location_id}")
def update_delivery_location(
    location_id: int,
    data: DeliveryLocationUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_sales_office_or_admin),
) -> Any:
    """배송지 수정"""
    location = db.query(DeliveryLocation).filter(DeliveryLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="배송지를 찾을 수 없습니다")
    
    # 판매소 담당자는 자신의 판매소 배송지만 수정 가능
    if current_user.role == UserRole.SALES_OFFICE.value:
        from app.services.user_service import UserService
        user = UserService(db).get_by_id(current_user.user_id)
        if not user or user.sales_office_id != location.sales_office_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="자신의 판매소 배송지만 수정할 수 있습니다"
            )
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(location, key, value)
    
    db.commit()
    db.refresh(location)
    
    return {
        "id": location.id,
        "sales_office_id": location.sales_office_id,
        "name": location.name,
        "address": location.address,
        "contact_person": location.contact_person,
        "contact_phone": location.contact_phone,
    }


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_sales_office_or_admin),
) -> None:
    """배송지 삭제 (Soft Delete)"""
    location = db.query(DeliveryLocation).filter(DeliveryLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="배송지를 찾을 수 없습니다")
    
    # 판매소 담당자는 자신의 판매소 배송지만 삭제 가능
    if current_user.role == UserRole.SALES_OFFICE.value:
        from app.services.user_service import UserService
        user = UserService(db).get_by_id(current_user.user_id)
        if not user or user.sales_office_id != location.sales_office_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="자신의 판매소 배송지만 삭제할 수 있습니다"
            )
    
    # Soft delete
    location.is_active = False
    db.commit()
