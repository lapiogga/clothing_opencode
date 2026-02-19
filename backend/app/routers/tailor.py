from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.schemas.tailor import VoucherCreate, VoucherRegister, VoucherCancelRequest, VoucherResponse, VoucherListResponse, TailorCompanyCreate, TailorCompanyUpdate, VoucherIssueDirect
from app.models.tailor import VoucherStatus, TailorCompany, TailorVoucher
from app.models.user import UserRole
from app.services import tailor_service
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


@router.get("/companies")
def get_tailor_companies(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    companies = db.query(TailorCompany).filter(TailorCompany.is_active == True).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "business_number": c.business_number,
            "address": c.address,
            "phone": c.phone,
            "manager_name": c.manager_name,
            "is_active": c.is_active,
        }
        for c in companies
    ]


@router.post("/companies", status_code=status.HTTP_201_CREATED)
def create_tailor_company(
    data: TailorCompanyCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    existing = db.query(TailorCompany).filter(TailorCompany.code == data.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 존재하는 업체 코드입니다")
    
    company = TailorCompany(
        name=data.name,
        code=data.code,
        business_number=data.business_number,
        address=data.address,
        phone=data.phone,
        manager_name=data.manager_name,
        manager_phone=data.manager_phone,
        is_active=data.is_active,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return {
        "id": company.id,
        "name": company.name,
        "code": company.code,
        "business_number": company.business_number,
        "address": company.address,
        "phone": company.phone,
        "manager_name": company.manager_name,
        "manager_phone": company.manager_phone,
        "is_active": company.is_active,
    }


@router.put("/companies/{company_id}")
def update_tailor_company(
    company_id: int,
    data: TailorCompanyUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    company = db.query(TailorCompany).filter(TailorCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업체를 찾을 수 없습니다")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)
    
    db.commit()
    db.refresh(company)
    return {
        "id": company.id,
        "name": company.name,
        "code": company.code,
        "business_number": company.business_number,
        "address": company.address,
        "phone": company.phone,
        "manager_name": company.manager_name,
        "manager_phone": company.manager_phone,
        "is_active": company.is_active,
    }


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tailor_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    company = db.query(TailorCompany).filter(TailorCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업체를 찾을 수 없습니다")
    
    db.delete(company)
    db.commit()


@router.post("", response_model=VoucherResponse, status_code=status.HTTP_201_CREATED)
def create_voucher(
    voucher_data: VoucherCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    voucher = tailor_service.create_voucher(db, staff_id=current_user.user_id, voucher_data=voucher_data)
    return voucher


@router.post("/issue-direct", status_code=status.HTTP_201_CREATED)
def issue_voucher_direct(
    voucher_data: VoucherIssueDirect,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    """
    맞춤피복 체척권 직접 발행 (일반 사용자용)
    - 주문 없이 맞춤피복 선택 시 체척권만 발행
    """
    voucher = tailor_service.issue_voucher_direct(
        db,
        user_id=current_user.user_id,
        item_id=voucher_data.item_id,
        amount=voucher_data.amount,
        sales_office_id=voucher_data.sales_office_id,
        notes=voucher_data.notes,
    )
    return {
        "id": voucher.id,
        "voucher_number": voucher.voucher_number,
        "user_id": voucher.user_id,
        "item_id": voucher.item_id,
        "amount": voucher.amount,
        "status": voucher.status.value,
        "issued_at": voucher.issued_at.isoformat() if voucher.issued_at else None,
        "expires_at": voucher.expires_at.isoformat() if voucher.expires_at else None,
        "notes": voucher.notes,
    }


@router.get("", response_model=VoucherListResponse)
def get_vouchers(
    user_id: Optional[int] = None,
    status: Optional[VoucherStatus] = None,
    keyword: Optional[str] = None,
    clothing_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    """
    체척권 목록 조회
    - clothing_type: 'custom'이면 맞춤피복 체척권만 조회
    """
    query = db.query(TailorVoucher).options(
        joinedload(TailorVoucher.user),
        joinedload(TailorVoucher.item),
    )
    
    if current_user.role == "tailor_company":
        pass
    elif user_id:
        query = query.filter(TailorVoucher.user_id == user_id)
    else:
        query = query.filter(TailorVoucher.user_id == current_user.user_id)
    
    if status:
        query = query.filter(TailorVoucher.status == status)
    
    # 맞춤피복만 필터링
    if clothing_type == 'custom':
        from app.models.clothing import ClothingItem, ClothingType
        query = query.join(ClothingItem, TailorVoucher.item_id == ClothingItem.id).filter(
            ClothingItem.clothing_type == ClothingType.CUSTOM
        )
    
    if keyword:
        query = query.filter(
            (TailorVoucher.voucher_number.contains(keyword)) |
            (TailorVoucher.user.has(name=keyword)) |
            (TailorVoucher.user.has(service_number=keyword))
        )
    
    total = query.count()
    skip = (page - 1) * page_size
    vouchers = query.order_by(TailorVoucher.id.desc()).offset(skip).limit(page_size).all()
    
    items = []
    for v in vouchers:
        items.append({
            "id": v.id,
            "voucher_number": v.voucher_number,
            "user_id": v.user_id,
            "tailor_company_id": v.tailor_company_id,
            "order_id": v.order_id,
            "user": {
                "id": v.user.id,
                "name": v.user.name,
                "service_number": v.user.service_number,
                "unit": v.user.unit,
                "rank": {"name": v.user.rank.name} if v.user.rank else None,
            } if v.user else None,
            "item_id": v.item_id,
            "item": {"id": v.item.id, "name": v.item.name} if v.item else None,
            "amount": v.amount,
            "status": v.status.value,
            "issued_at": v.issued_at.isoformat() if v.issued_at else None,
            "registered_at": v.registered_at.isoformat() if v.registered_at else None,
            "used_at": v.used_at.isoformat() if v.used_at else None,
            "cancelled_at": v.cancelled_at.isoformat() if v.cancelled_at else None,
            "cancel_reason": v.cancel_reason,
            "expires_at": v.expires_at.isoformat() if v.expires_at else None,
            "notes": v.notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })
    
    return {"total": total, "items": items}


@router.post("/{voucher_id}/cancel-request")
def request_cancel_voucher(
    voucher_id: int,
    cancel_data: VoucherCancelRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    voucher = tailor_service.request_cancel_voucher(db, user_id=current_user.user_id, voucher_id=voucher_id, cancel_data=cancel_data)
    if not voucher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="취소 요청이 불가능합니다")
    return {"message": "체척권이 취소되었습니다", "voucher_id": voucher.id}


@router.post("/{voucher_id}/approve-cancel")
def approve_cancel_voucher(
    voucher_id: int,
    approved: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    voucher = tailor_service.approve_cancel_voucher(db, staff_id=current_user.user_id, voucher_id=voucher_id, approved=approved)
    if not voucher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="취소 승인이 불가능합니다")
    return {"message": "취소 승인이 처리되었습니다", "voucher_id": voucher.id}


@router.post("/register", response_model=VoucherResponse)
def register_voucher(
    register_data: VoucherRegister,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    voucher = tailor_service.register_voucher(db, staff_id=current_user.user_id, register_data=register_data)
    if not voucher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="체척권 등록이 불가능합니다")
    return voucher
