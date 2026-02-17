"""
판매소 주문 관리 라우터
- 판매소별 주문 목록, 상세, 상태 변경
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import UserRole, User
from app.models.order import Order, OrderItem, OrderStatus, OrderType, Delivery, DeliveryStatus
from app.schemas.sales import OfflineSaleCreate, RefundCreate, SalesHistoryResponse
from app.services import sales_service
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def _get_sales_office_id(current_user: TokenData, db: Session) -> int:
    """판매소 담당자의 sales_office_id 반환"""
    if current_user.role == UserRole.ADMIN.value:
        return None
    elif current_user.role == UserRole.SALES_OFFICE.value:
        user = db.query(User).filter(User.id == current_user.user_id).first()
        if user and user.sales_office_id:
            return user.sales_office_id
        raise HTTPException(status_code=403, detail="판매소 정보가 없습니다")
    raise HTTPException(status_code=403, detail="접근 권한이 없습니다")


def _build_sales_order_response(order: Order) -> dict:
    """판매소용 주문 응답 데이터 구성"""
    user_data = None
    if order.user:
        user_data = {
            "id": order.user.id,
            "name": order.user.name,
            "service_number": order.user.service_number,
            "rank": order.user.rank.name if order.user.rank else None,
            "unit": order.user.unit,
        }
    
    delivery_data = None
    if order.delivery:
        delivery_location_data = None
        if order.delivery.delivery_location:
            delivery_location_data = {
                "id": order.delivery.delivery_location.id,
                "name": order.delivery.delivery_location.name,
                "address": order.delivery.delivery_location.address,
            }
        delivery_data = {
            "id": order.delivery.id,
            "delivery_type": order.delivery.delivery_type.value,
            "status": order.delivery.status.value,
            "delivery_location": delivery_location_data,
            "recipient_name": order.delivery.recipient_name,
            "recipient_phone": order.delivery.recipient_phone,
            "shipping_address": order.delivery.shipping_address,
            "tracking_number": order.delivery.tracking_number,
        }
    
    items_data = []
    for item in order.items:
        items_data.append({
            "id": item.id,
            "item_id": item.item_id,
            "item_name": item.item.name if item.item else None,
            "spec_id": item.spec_id,
            "spec_size": item.spec.size if item.spec else None,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
        })
    
    return {
        "id": order.id,
        "order_number": order.order_number,
        "user": user_data,
        "order_type": order.order_type.value,
        "status": order.status.value,
        "total_amount": order.total_amount,
        "reserved_point": order.reserved_point,
        "used_point": order.used_point,
        "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
        "items": items_data,
        "delivery": delivery_data,
        "item_count": len(order.items),
    }


@router.get("/orders")
def get_sales_orders(
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    판매소 주문 목록 조회
    - 판매소 담당자: 자신의 판매소 주문만 조회
    - 관리자: 모든 주문 조회 (sales_office_id 파라미터 필요)
    """
    sales_office_id = _get_sales_office_id(current_user, db)
    
    query = db.query(Order).options(
        joinedload(Order.user).joinedload(User.rank),
        joinedload(Order.items).joinedload(OrderItem.item),
        joinedload(Order.items).joinedload(OrderItem.spec),
        joinedload(Order.delivery),
    )
    
    if sales_office_id:
        query = query.filter(Order.sales_office_id == sales_office_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    if order_type:
        query = query.filter(Order.order_type == order_type)
    
    if keyword:
        query = query.filter(Order.order_number.contains(keyword))
    
    total = query.count()
    orders = query.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_build_sales_order_response(o) for o in orders]
    }


@router.get("/orders/{order_id}")
def get_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """판매소 주문 상세 조회"""
    sales_office_id = _get_sales_office_id(current_user, db)
    
    query = db.query(Order).options(
        joinedload(Order.user).joinedload(User.rank),
        joinedload(Order.items).joinedload(OrderItem.item),
        joinedload(Order.items).joinedload(OrderItem.spec),
        joinedload(Order.delivery),
    ).filter(Order.id == order_id)
    
    if sales_office_id:
        query = query.filter(Order.sales_office_id == sales_office_id)
    
    order = query.first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")
    
    return _build_sales_order_response(order)


@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    주문 상태 변경
    - confirmed -> processing: 상품 준비중
    - processing -> shipped: 배송 시작
    - shipped -> delivered: 배송 완료
    """
    sales_office_id = _get_sales_office_id(current_user, db)
    
    query = db.query(Order).filter(Order.id == order_id)
    if sales_office_id:
        query = query.filter(Order.sales_office_id == sales_office_id)
    
    order = query.first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")
    
    new_status = status_data.get("status")
    tracking_number = status_data.get("tracking_number")
    
    if new_status:
        try:
            order.status = OrderStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 상태값입니다")
    
    if tracking_number and order.delivery:
        order.delivery.tracking_number = tracking_number
        if new_status == "shipped":
            from datetime import datetime
            order.delivery.shipped_at = datetime.utcnow()
            order.delivery.status = DeliveryStatus.IN_TRANSIT
    
    if new_status == "delivered":
        from datetime import datetime
        if order.delivery:
            order.delivery.delivered_at = datetime.utcnow()
            order.delivery.status = DeliveryStatus.DELIVERED
        if order.reserved_point > 0:
            order.user.current_point -= order.reserved_point
            order.user.reserved_point -= order.reserved_point
            order.used_point = order.reserved_point
            order.reserved_point = 0
    
    db.commit()
    db.refresh(order)
    return _build_sales_order_response(order)


@router.post("/offline", status_code=status.HTTP_201_CREATED)
def create_offline_sale(
    sale_data: OfflineSaleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    """오프라인 판매 등록"""
    order = sales_service.create_offline_sale(db, staff_id=current_user.user_id, sale_data=sale_data)
    return {"message": "오프라인 판매가 완료되었습니다", "order_id": order.id}


@router.post("/refund")
def process_refund(
    refund_data: RefundCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    """반품 처리"""
    order = sales_service.process_refund(db, staff_id=current_user.user_id, refund_data=refund_data)
    if not order:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="반품 처리가 불가능합니다")
    return {"message": "반품이 처리되었습니다", "order_id": order.id}


@router.get("/history", response_model=SalesHistoryResponse)
def get_sales_history(
    sales_office_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    """판매 이력 조회 (오프라인 판매)"""
    orders, total = sales_service.get_sales_history(db, sales_office_id=sales_office_id, skip=skip, limit=limit)
    items = []
    for order in orders:
        user_name = order.user.name if order.user else "알 수 없음"
        items.append({
            "id": order.id,
            "order_number": order.order_number,
            "user_name": user_name,
            "total_amount": order.total_amount,
            "ordered_at": order.ordered_at.isoformat() if order.ordered_at else "",
            "status": order.status.value,
        })
    return {"total": total, "items": items}
