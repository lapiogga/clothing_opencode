from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderCancel, DeliveryUpdate, OrderListResponse
from app.services import order_service
from app.utils.auth import get_current_user

router = APIRouter()


def _build_order_response(order):
    """주문 응답 데이터 구성 (배송지 정보 포함)"""
    delivery_data = None
    if order.delivery:
        delivery_location_data = None
        if order.delivery.delivery_location:
            delivery_location_data = {
                "id": order.delivery.delivery_location.id,
                "name": order.delivery.delivery_location.name,
                "address": order.delivery.delivery_location.address,
                "contact_person": order.delivery.delivery_location.contact_person,
                "contact_phone": order.delivery.delivery_location.contact_phone,
            }
        delivery_data = {
            "id": order.delivery.id,
            "delivery_type": order.delivery.delivery_type,
            "status": order.delivery.status,
            "delivery_location_id": order.delivery.delivery_location_id,
            "delivery_location": delivery_location_data,
            "recipient_name": order.delivery.recipient_name,
            "recipient_phone": order.delivery.recipient_phone,
            "shipping_address": order.delivery.shipping_address,
            "tracking_number": order.delivery.tracking_number,
            "shipped_at": order.delivery.shipped_at,
            "delivered_at": order.delivery.delivered_at,
        }
    
    items_data = [
        {
            "id": item.id,
            "item_id": item.item_id,
            "item_name": item.item.name if item.item else None,
            "spec_id": item.spec_id,
            "spec_size": item.spec.size if item.spec else None,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "payment_method": item.payment_method,
            "is_returned": item.is_returned,
        }
        for item in order.items
    ]
    
    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "sales_office_id": order.sales_office_id,
        "order_type": order.order_type,
        "status": order.status,
        "total_amount": order.total_amount,
        "reserved_point": order.reserved_point,
        "used_point": order.used_point,
        "used_voucher_amount": order.used_voucher_amount,
        "ordered_at": order.ordered_at,
        "items": items_data,
        "delivery": delivery_data,
    }


@router.get("", response_model=OrderListResponse)
def get_orders(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    orders, total = order_service.get_orders(db, user_id=current_user.user_id, skip=skip, limit=limit)
    return {"total": total, "items": [_build_order_response(o) for o in orders]}


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    order = order_service.create_order(db, user_id=current_user.user_id, order_data=order_data)
    return _build_order_response(order)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="주문을 찾을 수 없습니다")
    if order.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다")
    return _build_order_response(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    cancel_data: OrderCancel,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    order = order_service.cancel_order(db, order_id, current_user.user_id, cancel_data)
    if not order:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="주문 취소가 불가능합니다")
    return _build_order_response(order)


@router.put("/{order_id}/delivery", response_model=OrderResponse)
def update_delivery(
    order_id: int,
    delivery_data: DeliveryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    order = order_service.update_delivery(db, order_id, delivery_data)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="주문 또는 배송 정보를 찾을 수 없습니다")
    return order


@router.post("/{order_id}/force-cancel", response_model=OrderResponse)
def force_cancel_order(
    order_id: int,
    cancel_data: OrderCancel,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    order = order_service.force_cancel_order(db, order_id, current_user.user_id, cancel_data)
    if not order:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="직권 취소가 불가능합니다")
    return order


@router.post("/{order_id}/receive", response_model=OrderResponse)
def receive_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    """
    주문 수령 완료 처리
    - 배송 완료(DELIVERED) 상태에서만 수령 완료 가능
    - 포인트 확정 차감 처리
    """
    order = order_service.receive_order(db, order_id, current_user.user_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="수령 완료 처리가 불가능합니다. 배송 완료 상태인지 확인해주세요."
        )
    return _build_order_response(order)
