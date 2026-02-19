import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem, Delivery, OrderStatus, OrderType, DeliveryType, DeliveryStatus
from app.models.point import PointTransaction, TransactionType
from app.models.sales import Inventory, InventoryHistory, AdjustmentType
from app.models.clothing import ClothingSpec
from app.schemas.order import OrderCreate, DeliveryUpdate, OrderCancel


def generate_order_number() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    unique = uuid.uuid4().hex[:8].upper()
    return f"ORD-{date_str}-{unique}"


def create_order(db: Session, user_id: int, order_data: OrderCreate) -> Order:
    from app.models.user import User
    
    order_number = generate_order_number()
    
    # 사용자 확인 및 포인트 검증
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("사용자를 찾을 수 없습니다.")
    
    order = Order(
        order_number=order_number,
        user_id=user_id,
        sales_office_id=order_data.sales_office_id,
        order_type=order_data.order_type,
        status=OrderStatus.PENDING,
        total_amount=0,
        reserved_point=0,
        used_point=0,
        used_voucher_amount=0,
    )
    db.add(order)
    db.flush()
    
    total_amount = 0
    total_point = 0
    total_voucher = 0
    order_items_list = []
    
    for item_data in order_data.items:
        spec = db.query(ClothingSpec).filter(ClothingSpec.id == item_data.spec_id).first() if item_data.spec_id else None
        unit_price = spec.price if spec else 0
        total_price = unit_price * item_data.quantity
        
        order_item = OrderItem(
            order_id=order.id,
            item_id=item_data.item_id,
            spec_id=item_data.spec_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            total_price=total_price,
            payment_method=item_data.payment_method,
        )
        db.add(order_item)
        order_items_list.append(order_item)
        
        total_amount += total_price
        if item_data.payment_method.value == "point":
            total_point += total_price
        else:
            total_voucher += total_price
    
    order.total_amount = total_amount
    
    # 포인트 검증 (마이너스 방지)
    available_point = user.current_point - user.reserved_point
    if total_point > available_point:
        raise ValueError(f"사용 가능한 포인트가 부족합니다. (사용가능: {available_point}P, 필요: {total_point}P)")
    
    if order_data.order_type == OrderType.ONLINE:
        order.reserved_point = total_point
        order.used_point = 0
        _reserve_points(db, user_id, order.id, total_point)
        order.status = OrderStatus.CONFIRMED
    else:
        order.used_point = total_point
        order.used_voucher_amount = total_voucher
        _deduct_points(db, user_id, order.id, total_point)
        _deduct_inventory(db, order.id, order_data.sales_office_id, order_items_list)
        order.status = OrderStatus.DELIVERED
    
    if order_data.delivery_type:
        delivery = Delivery(
            order_id=order.id,
            delivery_type=order_data.delivery_type,
            status=DeliveryStatus.PREPARING if order_data.order_type == OrderType.ONLINE else DeliveryStatus.DELIVERED,
            delivery_location_id=order_data.delivery_location_id,
            recipient_name=order_data.recipient_name,
            recipient_phone=order_data.recipient_phone,
            shipping_address=order_data.shipping_address,
            delivery_note=order_data.delivery_note,
        )
        if order_data.order_type == OrderType.OFFLINE:
            delivery.delivered_at = datetime.utcnow()
        db.add(delivery)
    
    db.commit()
    db.refresh(order)
    return order


def _reserve_points(db: Session, user_id: int, order_id: int, amount: int) -> None:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user and amount > 0:
        user.reserved_point += amount
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.RESERVE,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            description="주문 포인트 예약",
        )
        db.add(transaction)


def _deduct_points(db: Session, user_id: int, order_id: int, amount: int) -> None:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user and amount > 0:
        user.current_point -= amount
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.DEDUCT,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            description="오프라인 구매 포인트 차감",
        )
        db.add(transaction)


def _deduct_inventory(db: Session, order_id: int, sales_office_id: int, items: list) -> None:
    from app.models.user import User
    for item in items:
        inventory = db.query(Inventory).filter(
            Inventory.sales_office_id == sales_office_id,
            Inventory.item_id == item.item_id,
            Inventory.spec_id == item.spec_id,
        ).first()
        if inventory:
            before = inventory.quantity
            inventory.quantity -= item.quantity
            history = InventoryHistory(
                inventory_id=inventory.id,
                adjustment_type=AdjustmentType.DECREASE,
                quantity=item.quantity,
                before_quantity=before,
                after_quantity=inventory.quantity,
                reason="오프라인 판매",
                adjusted_by=1,
                order_id=order_id,
            )
            db.add(history)


def get_orders(db: Session, user_id: Optional[int] = None, skip: int = 0, limit: int = 20) -> tuple[list, int]:
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.item),
        joinedload(Order.items).joinedload(OrderItem.spec),
        joinedload(Order.delivery).joinedload(Delivery.delivery_location),
    )
    if user_id:
        query = query.filter(Order.user_id == user_id)
    total = query.count()
    orders = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()
    return orders, total


def get_order(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.item),
        joinedload(Order.items).joinedload(OrderItem.spec),
        joinedload(Order.delivery).joinedload(Delivery.delivery_location),
    ).filter(Order.id == order_id).first()


def cancel_order(db: Session, order_id: int, user_id: int, cancel_data: OrderCancel) -> Optional[Order]:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        return None
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        return None
    
    if order.reserved_point > 0:
        _release_points(db, user_id, order_id, order.reserved_point)
    
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.utcnow()
    order.cancel_reason = cancel_data.reason
    order.cancelled_by = user_id
    
    db.commit()
    db.refresh(order)
    return order


def force_cancel_order(db: Session, order_id: int, admin_id: int, cancel_data: OrderCancel) -> Optional[Order]:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None
    
    if order.status == OrderStatus.CANCELLED:
        return None
    
    if order.reserved_point > 0:
        _release_points(db, order.user_id, order_id, order.reserved_point)
    
    if order.status == OrderStatus.DELIVERED and order.order_type == OrderType.OFFLINE:
        _refund_points(db, order.user_id, order_id, order.used_point)
        _restore_inventory(db, order_id, order.sales_office_id, order.items)
    
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.utcnow()
    order.cancel_reason = cancel_data.reason
    order.cancelled_by = admin_id
    
    db.commit()
    db.refresh(order)
    return order


def _release_points(db: Session, user_id: int, order_id: int, amount: int) -> None:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user and amount > 0:
        user.reserved_point -= amount
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.RELEASE,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            description="주문 취소 포인트 해제",
        )
        db.add(transaction)


def _refund_points(db: Session, user_id: int, order_id: int, amount: int) -> None:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user and amount > 0:
        user.current_point += amount
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.REFUND,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            description="주문 취소 포인트 환불",
        )
        db.add(transaction)


def _restore_inventory(db: Session, order_id: int, sales_office_id: int, items: list) -> None:
    for item in items:
        inventory = db.query(Inventory).filter(
            Inventory.sales_office_id == sales_office_id,
            Inventory.item_id == item.item_id,
            Inventory.spec_id == item.spec_id,
        ).first()
        if inventory:
            before = inventory.quantity
            inventory.quantity += item.quantity
            history = InventoryHistory(
                inventory_id=inventory.id,
                adjustment_type=AdjustmentType.RETURN,
                quantity=item.quantity,
                before_quantity=before,
                after_quantity=inventory.quantity,
                reason="주문 취소 재고 복구",
                adjusted_by=1,
                order_id=order_id,
            )
            db.add(history)


def update_delivery(db: Session, order_id: int, delivery_data: DeliveryUpdate) -> Optional[Order]:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or not order.delivery:
        return None
    
    delivery = order.delivery
    
    if delivery_data.status:
        delivery.status = delivery_data.status
        if delivery_data.status == DeliveryStatus.IN_TRANSIT:
            delivery.shipped_at = datetime.utcnow()
            order.status = OrderStatus.SHIPPED
        elif delivery_data.status == DeliveryStatus.DELIVERED:
            delivery.delivered_at = datetime.utcnow()
            order.status = OrderStatus.DELIVERED
            # 포인트는 수령 완료 시 확정 차감하므로 여기서는 처리하지 않음
    
    if delivery_data.tracking_number:
        delivery.tracking_number = delivery_data.tracking_number
    
    if delivery_data.delivery_note:
        delivery.delivery_note = delivery_data.delivery_note
    
    db.commit()
    db.refresh(order)
    return order


def receive_order(db: Session, order_id: int, user_id: int) -> Optional[Order]:
    """
    주문 수령 완료 처리
    - 배송 완료(DELIVERED) 상태에서만 수령 완료 가능
    - 포인트 확정 차감 처리
    """
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        return None
    
    if order.status != OrderStatus.DELIVERED:
        return None
    
    # 포인트 확정 차감
    if order.reserved_point > 0:
        _confirm_points(db, user_id, order_id, order.reserved_point)
    
    order.status = OrderStatus.RECEIVED
    
    db.commit()
    db.refresh(order)
    return order


def _confirm_points(db: Session, user_id: int, order_id: int, amount: int) -> None:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user and amount > 0:
        user.current_point -= amount
        user.reserved_point -= amount
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.USE,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            description="배송 완료 포인트 확정 차감",
        )
        db.add(transaction)
