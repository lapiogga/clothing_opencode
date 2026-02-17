import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.tailor import TailorVoucher, VoucherStatus
from app.models.point import PointTransaction, TransactionType
from app.schemas.tailor import VoucherCreate, VoucherRegister, VoucherCancelRequest


def generate_voucher_number() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    unique = uuid.uuid4().hex[:8].upper()
    return f"TV-{date_str}-{unique}"


def create_voucher(db: Session, staff_id: int, voucher_data: VoucherCreate) -> TailorVoucher:
    voucher_number = generate_voucher_number()
    
    voucher = TailorVoucher(
        voucher_number=voucher_number,
        user_id=voucher_data.user_id,
        order_id=voucher_data.order_id,
        order_item_id=voucher_data.order_item_id,
        item_id=voucher_data.item_id,
        amount=voucher_data.amount,
        status=VoucherStatus.ISSUED,
        expires_at=voucher_data.expires_at,
        notes=voucher_data.notes,
    )
    db.add(voucher)
    db.commit()
    db.refresh(voucher)
    return voucher


def get_vouchers(db: Session, user_id: Optional[int] = None, status: Optional[VoucherStatus] = None, skip: int = 0, limit: int = 20) -> tuple[list, int]:
    query = db.query(TailorVoucher)
    if user_id:
        query = query.filter(TailorVoucher.user_id == user_id)
    if status:
        query = query.filter(TailorVoucher.status == status)
    total = query.count()
    vouchers = query.order_by(TailorVoucher.id.desc()).offset(skip).limit(limit).all()
    return vouchers, total


def get_voucher(db: Session, voucher_id: int) -> Optional[TailorVoucher]:
    return db.query(TailorVoucher).filter(TailorVoucher.id == voucher_id).first()


def register_voucher(db: Session, staff_id: int, register_data: VoucherRegister) -> Optional[TailorVoucher]:
    voucher = db.query(TailorVoucher).filter(TailorVoucher.id == register_data.voucher_id).first()
    if not voucher or voucher.status != VoucherStatus.ISSUED:
        return None
    
    voucher.tailor_company_id = register_data.tailor_company_id
    voucher.status = VoucherStatus.REGISTERED
    voucher.registered_at = datetime.utcnow()
    voucher.registered_by = staff_id
    
    db.commit()
    db.refresh(voucher)
    return voucher


def request_cancel_voucher(db: Session, user_id: int, voucher_id: int, cancel_data: VoucherCancelRequest) -> Optional[TailorVoucher]:
    voucher = db.query(TailorVoucher).filter(
        TailorVoucher.id == voucher_id,
        TailorVoucher.user_id == user_id,
    ).first()
    
    if not voucher:
        return None
    
    if voucher.status not in [VoucherStatus.ISSUED, VoucherStatus.REGISTERED]:
        return None
    
    if voucher.status == VoucherStatus.REGISTERED:
        return None
    
    voucher.cancel_reason = cancel_data.reason
    voucher.cancelled_at = datetime.utcnow()
    voucher.cancelled_by = user_id
    voucher.status = VoucherStatus.CANCELLED
    
    _refund_voucher_amount(db, voucher)
    
    db.commit()
    db.refresh(voucher)
    return voucher


def approve_cancel_voucher(db: Session, staff_id: int, voucher_id: int, approved: bool) -> Optional[TailorVoucher]:
    voucher = db.query(TailorVoucher).filter(TailorVoucher.id == voucher_id).first()
    
    if not voucher or voucher.status == VoucherStatus.CANCELLED:
        return None
    
    if approved:
        voucher.status = VoucherStatus.CANCELLED
        voucher.cancelled_at = datetime.utcnow()
        voucher.cancelled_by = staff_id
        _refund_voucher_amount(db, voucher)
    
    db.commit()
    db.refresh(voucher)
    return voucher


def _refund_voucher_amount(db: Session, voucher: TailorVoucher) -> None:
    from app.models.user import User
    if voucher.amount > 0:
        user = db.query(User).filter(User.id == voucher.user_id).first()
        if user:
            user.current_point += voucher.amount
            transaction = PointTransaction(
                user_id=voucher.user_id,
                transaction_type=TransactionType.REFUND,
                amount=voucher.amount,
                balance_after=user.current_point,
                reserved_after=user.reserved_point,
                voucher_id=voucher.id,
                description="체척권 취소 포인트 환불",
            )
            db.add(transaction)
