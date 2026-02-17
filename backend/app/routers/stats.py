from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order, OrderStatus, OrderType
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/daily-sales")
def get_daily_sales(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_office_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    query = db.query(
        func.date(Order.ordered_at).label("sale_date"),
        func.sum(Order.total_amount).label("total_amount"),
        func.count(Order.id).label("order_count"),
    ).filter(Order.status != OrderStatus.CANCELLED)
    
    if start_date:
        query = query.filter(func.date(Order.ordered_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Order.ordered_at) <= end_date)
    if sales_office_id:
        query = query.filter(Order.sales_office_id == sales_office_id)
    
    results = query.group_by(func.date(Order.ordered_at)).order_by(func.date(Order.ordered_at).desc()).all()
    
    return {
        "items": [
            {
                "date": str(r.sale_date),
                "total_amount": r.total_amount or 0,
                "order_count": r.order_count or 0,
            }
            for r in results
        ]
    }


@router.get("/item-sales")
def get_item_sales(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    from app.models.order import OrderItem
    from app.models.clothing import ClothingItem
    
    query = db.query(
        ClothingItem.id.label("item_id"),
        ClothingItem.name.label("item_name"),
        func.sum(OrderItem.quantity).label("total_quantity"),
        func.sum(OrderItem.total_price).label("total_amount"),
    ).join(OrderItem, OrderItem.item_id == ClothingItem.id).join(Order, Order.id == OrderItem.order_id).filter(
        Order.status != OrderStatus.CANCELLED
    )
    
    if start_date:
        query = query.filter(func.date(Order.ordered_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Order.ordered_at) <= end_date)
    
    results = query.group_by(ClothingItem.id, ClothingItem.name).order_by(func.sum(OrderItem.total_price).desc()).limit(limit).all()
    
    return {
        "items": [
            {
                "item_id": r.item_id,
                "item_name": r.item_name,
                "total_quantity": r.total_quantity or 0,
                "total_amount": r.total_amount or 0,
            }
            for r in results
        ]
    }


@router.get("/user-sales")
def get_user_sales(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Any:
    from app.models.user import User
    
    query = db.query(
        User.id.label("user_id"),
        User.name.label("user_name"),
        User.service_number.label("service_number"),
        func.count(Order.id).label("order_count"),
        func.sum(Order.total_amount).label("total_amount"),
    ).join(Order, Order.user_id == User.id).filter(
        Order.status != OrderStatus.CANCELLED
    )
    
    if start_date:
        query = query.filter(func.date(Order.ordered_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Order.ordered_at) <= end_date)
    
    results = query.group_by(User.id, User.name, User.service_number).order_by(func.sum(Order.total_amount).desc()).limit(limit).all()
    
    return {
        "items": [
            {
                "user_id": r.user_id,
                "user_name": r.user_name,
                "service_number": r.service_number,
                "order_count": r.order_count or 0,
                "total_amount": r.total_amount or 0,
            }
            for r in results
        ]
    }
