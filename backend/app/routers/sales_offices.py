from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole, SalesOffice
from app.schemas.sales_office import SalesOfficeCreate, SalesOfficeUpdate, SalesOfficeResponse
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


@router.get("")
def get_sales_offices(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    query = db.query(SalesOffice)
    if is_active is not None:
        query = query.filter(SalesOffice.is_active == is_active)
    offices = query.all()
    return [
        {
            "id": o.id,
            "code": o.code,
            "name": o.name,
            "address": o.address,
            "phone": o.phone,
            "manager_name": o.manager_name,
            "is_active": o.is_active,
        }
        for o in offices
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_sales_office(
    data: SalesOfficeCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    office = SalesOffice(
        code=data.code,
        name=data.name,
        address=data.address,
        phone=data.phone,
        manager_name=data.manager_name,
        is_active=True,
    )
    db.add(office)
    db.commit()
    db.refresh(office)
    return {
        "id": office.id,
        "code": office.code,
        "name": office.name,
        "address": office.address,
        "phone": office.phone,
        "manager_name": office.manager_name,
        "is_active": office.is_active,
    }


@router.put("/{office_id}")
def update_sales_office(
    office_id: int,
    data: SalesOfficeUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    office = db.query(SalesOffice).filter(SalesOffice.id == office_id).first()
    if not office:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="판매소를 찾을 수 없습니다")
    
    if data.code is not None:
        office.code = data.code
    if data.name is not None:
        office.name = data.name
    if data.address is not None:
        office.address = data.address
    if data.phone is not None:
        office.phone = data.phone
    if data.manager_name is not None:
        office.manager_name = data.manager_name
    if data.is_active is not None:
        office.is_active = data.is_active
    
    db.commit()
    db.refresh(office)
    return {
        "id": office.id,
        "code": office.code,
        "name": office.name,
        "address": office.address,
        "phone": office.phone,
        "manager_name": office.manager_name,
        "is_active": office.is_active,
    }


@router.delete("/{office_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_office(
    office_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    office = db.query(SalesOffice).filter(SalesOffice.id == office_id).first()
    if not office:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="판매소를 찾을 수 없습니다")
    db.delete(office)
    db.commit()
