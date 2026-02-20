from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus, OrderType
from app.models.point import PointTransaction, TransactionType
from app.models.sales import Inventory, InventoryHistory, AdjustmentType
from app.schemas.sales import OfflineSaleCreate, RefundCreate


def create_offline_sale(db: Session, staff_id: int, sale_data: OfflineSaleCreate) -> Order:
    from app.services.order_service import generate_order_number
    
    order_number = generate_order_number()
    
    order = Order(
        order_number=order_number,
        user_id=sale_data.user_id,
        sales_office_id=sale_data.sales_office_id,
        order_type=OrderType.OFFLINE,
        status=OrderStatus.DELIVERED,
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
    
    for item_data in sale_data.items:
        total_price = item_data.unit_price * item_data.quantity
        
        order_item = OrderItem(
            order_id=order.id,
            item_id=item_data.item_id,
            spec_id=item_data.spec_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
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
    order.used_point = total_point
    order.used_voucher_amount = total_voucher
    
    if total_point > 0:
        _deduct_user_points(db, sale_data.user_id, order.id, total_point)
    
    _deduct_inventory_for_sale(db, order.id, sale_data.sales_office_id, order_items_list, staff_id)
    
    db.commit()
    db.refresh(order)
    return order


def _deduct_user_points(db: Session, user_id: int, order_id: int, amount: int) -> None:
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
            description="오프라인 판매 포인트 차감",
        )
        db.add(transaction)


def _deduct_inventory_for_sale(db: Session, order_id: int, sales_office_id: int, items: list, staff_id: int) -> None:
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
                adjusted_by=staff_id,
                order_id=order_id,
            )
            db.add(history)


def process_refund(db: Session, staff_id: int, refund_data: RefundCreate) -> Optional[Order]:
    order = db.query(Order).filter(Order.id == refund_data.order_id).first()
    if not order:
        return None
    
    if order.status not in [OrderStatus.DELIVERED, OrderStatus.SHIPPED]:
        return None
    
    total_refund_point = 0
    
    for refund_item in refund_data.items:
        order_item = db.query(OrderItem).filter(
            OrderItem.id == refund_item.order_item_id,
            OrderItem.order_id == order.id,
        ).first()
        if not order_item or order_item.is_returned:
            continue
        
        refund_quantity = min(refund_item.quantity, order_item.quantity - (order_item.quantity if order_item.is_returned else 0))
        if refund_quantity <= 0:
            continue
        
        refund_amount = order_item.unit_price * refund_quantity
        
        if order_item.payment_method.value == "point":
            total_refund_point += refund_amount
        
        _restore_inventory_for_refund(db, order.id, order.sales_office_id, order_item, refund_quantity, staff_id)
        
        order_item.is_returned = True
        order_item.returned_at = datetime.utcnow()
        order_item.return_reason = refund_item.reason
    
    if total_refund_point > 0:
        _refund_user_points(db, order.user_id, order.id, total_refund_point)
    
    all_returned = all(item.is_returned for item in order.items)
    if all_returned:
        order.status = OrderStatus.REFUNDED
    
    db.commit()
    db.refresh(order)
    return order


def _refund_user_points(db: Session, user_id: int, order_id: int, amount: int) -> None:
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
            description="반품 포인트 환불",
        )
        db.add(transaction)


def _restore_inventory_for_refund(db: Session, order_id: int, sales_office_id: int, order_item: OrderItem, quantity: int, staff_id: int) -> None:
    inventory = db.query(Inventory).filter(
        Inventory.sales_office_id == sales_office_id,
        Inventory.item_id == order_item.item_id,
        Inventory.spec_id == order_item.spec_id,
    ).first()
    if inventory:
        before = inventory.quantity
        inventory.quantity += quantity
        history = InventoryHistory(
            inventory_id=inventory.id,
            adjustment_type=AdjustmentType.RETURN,
            quantity=quantity,
            before_quantity=before,
            after_quantity=inventory.quantity,
            reason="반품 재고 복구",
            adjusted_by=staff_id,
            order_id=order_id,
        )
        db.add(history)


def get_sales_history(db: Session, sales_office_id: Optional[int] = None, skip: int = 0, limit: int = 20) -> tuple[list, int]:
    query = db.query(Order).filter(Order.order_type == OrderType.OFFLINE)
    if sales_office_id:
        query = query.filter(Order.sales_office_id == sales_office_id)
    total = query.count()
    orders = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()
    return orders, total
