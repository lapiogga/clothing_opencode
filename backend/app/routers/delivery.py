"""
배송지 관리 라우터
- 판매소별 배송지 조회, 등록, 수정, 삭제
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole
from app.models.order import DeliveryLocation
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


@router.get("")
def get_delivery_locations(
    sales_office_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    배송지 목록 조회
    - 관리자: 전체 또는 판매소별 조회
    - 일반 사용자: 지정된 판매소의 배송지만 조회
    """
    query = db.query(DeliveryLocation).filter(DeliveryLocation.is_active == True)
    
    if sales_office_id:
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
