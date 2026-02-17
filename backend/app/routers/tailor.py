from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.schemas.tailor import VoucherCreate, VoucherRegister, VoucherCancelRequest, VoucherResponse, VoucherListResponse
from app.models.tailor import VoucherStatus, TailorCompany, TailorVoucher
from app.services import tailor_service
from app.utils.auth import get_current_user

router = APIRouter()


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
            "address": c.address,
            "phone": c.phone,
        }
        for c in companies
    ]


@router.post("", response_model=VoucherResponse, status_code=status.HTTP_201_CREATED)
def create_voucher(
    voucher_data: VoucherCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    voucher = tailor_service.create_voucher(db, staff_id=current_user.user_id, voucher_data=voucher_data)
    return voucher


@router.get("", response_model=VoucherListResponse)
def get_vouchers(
    user_id: Optional[int] = None,
    status: Optional[VoucherStatus] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
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
