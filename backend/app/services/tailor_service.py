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


def issue_voucher_direct(db: Session, user_id: int, item_id: int, amount: int, sales_office_id: int = None, notes: str = None) -> TailorVoucher:
    """
    맞춤피복 체척권 직접 발행 (주문 없이)
    - 사용자가 맞춤피복 선택 시 즉시 체척권 발행
    - 발행과 동시에 포인트 차감
    """
    from app.models.user import User
    
    # 사용자 포인트 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("사용자를 찾을 수 없습니다.")
    
    # 사용 가능 포인트 확인
    available_point = user.current_point - user.reserved_point
    if available_point < amount:
        raise ValueError(f"사용 가능한 포인트가 부족합니다. (사용가능: {available_point}P, 필요: {amount}P)")
    
    voucher_number = generate_voucher_number()
    
    voucher = TailorVoucher(
        voucher_number=voucher_number,
        user_id=user_id,
        item_id=item_id,
        amount=amount,
        status=VoucherStatus.ISSUED,
        notes=notes or "맞춤피복 체척권 발행",
    )
    db.add(voucher)
    
    # 포인트 차감
    user.current_point -= amount
    transaction = PointTransaction(
        user_id=user_id,
        transaction_type=TransactionType.DEDUCT,
        amount=amount,
        balance_after=user.current_point,
        reserved_after=user.reserved_point,
        voucher_id=voucher.id,
        description="체척권 발행 포인트 차감",
    )
    db.add(transaction)
    
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
    """
    체척권 등록 (체척업체)
    - 발행된(ISSUED) 상태만 등록 가능
    - 취소 요청/취소됨/사용완료 상태는 등록 불가
    """
    voucher = db.query(TailorVoucher).filter(TailorVoucher.id == register_data.voucher_id).first()
    
    if not voucher:
        return None
    
    # 발행된 상태만 등록 가능
    if voucher.status != VoucherStatus.ISSUED:
        return None
    
    # 취소 요청/취소됨 상태 체크
    if voucher.status in [VoucherStatus.CANCEL_REQUESTED, VoucherStatus.CANCELLED]:
        return None
    
    voucher.tailor_company_id = register_data.tailor_company_id
    voucher.status = VoucherStatus.REGISTERED
    voucher.registered_at = datetime.utcnow()
    voucher.registered_by = staff_id
    
    db.commit()
    db.refresh(voucher)
    return voucher


def request_cancel_voucher(db: Session, user_id: int, voucher_id: int, cancel_data: VoucherCancelRequest) -> Optional[TailorVoucher]:
    """
    체척권 취소 요청 (사용자)
    - 취소 요청 상태로 변경 (승인 대기)
    """
    voucher = db.query(TailorVoucher).filter(
        TailorVoucher.id == voucher_id,
        TailorVoucher.user_id == user_id,
    ).first()
    
    if not voucher:
        return None
    
    # 발행된 상태만 취소 요청 가능
    if voucher.status != VoucherStatus.ISSUED:
        return None
    
    # 이미 등록된 경우 취소 불가
    if voucher.tailor_company_id:
        return None
    
    voucher.cancel_reason = cancel_data.reason
    voucher.status = VoucherStatus.CANCEL_REQUESTED
    
    db.commit()
    db.refresh(voucher)
    return voucher


def approve_cancel_voucher(db: Session, staff_id: int, voucher_id: int, approved: bool) -> Optional[TailorVoucher]:
    """
    체척권 취소 승인/반려 (관리자)
    - 승인: 취소 상태로 변경 + 포인트 환불
    - 반려: 원래 상태로 복구
    """
    voucher = db.query(TailorVoucher).filter(TailorVoucher.id == voucher_id).first()
    
    if not voucher:
        return None
    
    # 취소 요청 상태만 승인/반려 가능
    if voucher.status != VoucherStatus.CANCEL_REQUESTED:
        return None
    
    if approved:
        voucher.status = VoucherStatus.CANCELLED
        voucher.cancelled_at = datetime.utcnow()
        voucher.cancelled_by = staff_id
        _refund_voucher_amount(db, voucher)
    else:
        # 반려 시 원래 상태로 복구
        voucher.status = VoucherStatus.ISSUED
        voucher.cancel_reason = None
    
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
