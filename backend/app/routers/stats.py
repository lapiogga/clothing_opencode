from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order, OrderStatus, OrderType, OrderItem, Delivery, DeliveryStatus
from app.models.user import User, UserRole
from app.models.clothing import ClothingItem
from app.models.sales import Inventory, SalesOffice
from app.models.tailor import TailorCompany, TailorVoucher, VoucherStatus
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """역할별 대시보드 통계"""
    role = current_user.role
    user_id = current_user.user_id
    
    if role == UserRole.ADMIN.value:
        return get_admin_dashboard(db)
    elif role == UserRole.SALES_OFFICE.value:
        return get_sales_office_dashboard(db, user_id)
    elif role == UserRole.TAILOR_COMPANY.value:
        return get_tailor_dashboard(db, user_id)
    else:
        return get_user_dashboard(db, user_id)


def get_admin_dashboard(db: Session) -> dict:
    """관리자 대시보드"""
    total_users = db.query(User).filter(User.is_active == True).count()
    sales_offices = db.query(SalesOffice).filter(SalesOffice.is_active == True).count()
    tailor_companies = db.query(TailorCompany).filter(TailorCompany.is_active == True).count()
    clothing_items = db.query(ClothingItem).filter(ClothingItem.is_active == True).count()
    
    return {
        "totalUsers": total_users,
        "salesOffices": sales_offices,
        "tailorCompanies": tailor_companies,
        "clothingItems": clothing_items,
    }


def get_sales_office_dashboard(db: Session, user_id: int) -> dict:
    """판매소 대시보드"""
    user = db.query(User).filter(User.id == user_id).first()
    sales_office_id = user.sales_office_id if user else None
    
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 금일 판매
    today_sales = db.query(Order).filter(
        Order.sales_office_id == sales_office_id,
        Order.ordered_at >= today_start,
        Order.status != OrderStatus.CANCELLED,
    ).count() if sales_office_id else 0
    
    # 배송 대기 (온라인 주문 중 배송 준비/배송중)
    pending_delivery = 0
    if sales_office_id:
        pending_delivery = db.query(Order).join(Delivery).filter(
            Order.sales_office_id == sales_office_id,
            Order.order_type == OrderType.ONLINE,
            Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.SHIPPED]),
            Delivery.status.in_([DeliveryStatus.PREPARING, DeliveryStatus.IN_TRANSIT]),
        ).count()
    
    # 재고 부족 품목
    low_stock = 0
    if sales_office_id:
        low_stock = db.query(Inventory).filter(
            Inventory.sales_office_id == sales_office_id,
            (Inventory.quantity - Inventory.reserved_quantity) < 10,
        ).count()
    
    # 반품 요청 (취소 요청 상태)
    refund_requests = 0
    if sales_office_id:
        refund_requests = db.query(Order).filter(
            Order.sales_office_id == sales_office_id,
            Order.status == OrderStatus.CANCELLED,
        ).count()
    
    return {
        "todaySales": today_sales,
        "pendingDelivery": pending_delivery,
        "lowStock": low_stock,
        "refundRequests": refund_requests,
    }


def get_tailor_dashboard(db: Session, user_id: int) -> dict:
    """체척업체 대시보드"""
    # 미등록 체척권
    pending_vouchers = db.query(TailorVoucher).filter(
        TailorVoucher.status == VoucherStatus.ISSUED,
    ).count()
    
    # 완료 건수
    completed_vouchers = db.query(TailorVoucher).filter(
        TailorVoucher.status == VoucherStatus.USED,
    ).count()
    
    return {
        "pendingVouchers": pending_vouchers,
        "completedVouchers": completed_vouchers,
    }


def get_user_dashboard(db: Session, user_id: int) -> dict:
    """일반 사용자 대시보드"""
    # 진행 중인 주문
    active_orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED]),
    ).count()
    
    # 미사용 체척권
    active_vouchers = db.query(TailorVoucher).filter(
        TailorVoucher.user_id == user_id,
        TailorVoucher.status == VoucherStatus.ISSUED,
    ).count()
    
    return {
        "activeOrders": active_orders,
        "activeVouchers": active_vouchers,
    }


@router.get("/sales")
def get_sales_stats(
    startDate: Optional[date] = None,
    endDate: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """판매 통계 종합"""
    # 판매소 담당자의 경우 자신의 판매소만 조회
    sales_office_id = None
    if current_user.role == UserRole.SALES_OFFICE.value:
        user = db.query(User).filter(User.id == current_user.user_id).first()
        sales_office_id = user.sales_office_id if user else None
    
    # 기본 날짜 범위 (최근 30일)
    if not startDate:
        startDate = date.today() - timedelta(days=30)
    if not endDate:
        endDate = date.today()
    
    # 기본 쿼리 필터
    base_query = db.query(Order).filter(
        Order.status != OrderStatus.CANCELLED,
        func.date(Order.ordered_at) >= startDate,
        func.date(Order.ordered_at) <= endDate,
    )
    
    if sales_office_id:
        base_query = base_query.filter(Order.sales_office_id == sales_office_id)
    
    # 총 매출 및 판매건
    total_result = base_query.with_entities(
        func.sum(Order.total_amount).label("total"),
        func.count(Order.id).label("count"),
    ).first()
    
    total_sales = total_result.total or 0
    total_orders = total_result.count or 0
    
    # 포인트 사용액
    total_points = base_query.with_entities(
        func.sum(Order.used_point).label("points")
    ).first().points or 0
    
    # 반품 건수
    refund_count = db.query(Order).filter(
        Order.status == OrderStatus.CANCELLED,
        func.date(Order.ordered_at) >= startDate,
        func.date(Order.ordered_at) <= endDate,
    )
    if sales_office_id:
        refund_count = refund_count.filter(Order.sales_office_id == sales_office_id)
    refund_count = refund_count.count()
    
    # 일별 판매 추이
    daily_query = db.query(
        func.date(Order.ordered_at).label("sale_date"),
        func.sum(Order.total_amount).label("amount"),
        func.count(Order.id).label("count"),
    ).filter(
        Order.status != OrderStatus.CANCELLED,
        func.date(Order.ordered_at) >= startDate,
        func.date(Order.ordered_at) <= endDate,
    )
    
    if sales_office_id:
        daily_query = daily_query.filter(Order.sales_office_id == sales_office_id)
    
    daily_results = daily_query.group_by(func.date(Order.ordered_at)).order_by(func.date(Order.ordered_at)).all()
    
    daily_sales = [
        {
            "date": str(r.sale_date),
            "amount": r.amount or 0,
            "count": r.count or 0,
        }
        for r in daily_results
    ]
    
    # 인기 상품 TOP 10
    top_query = db.query(
        ClothingItem.id.label("id"),
        ClothingItem.name.label("name"),
        func.sum(OrderItem.quantity).label("quantity"),
        func.sum(OrderItem.total_price).label("amount"),
    ).join(OrderItem, OrderItem.item_id == ClothingItem.id).join(Order, Order.id == OrderItem.order_id).filter(
        Order.status != OrderStatus.CANCELLED,
        func.date(Order.ordered_at) >= startDate,
        func.date(Order.ordered_at) <= endDate,
    )
    
    if sales_office_id:
        top_query = top_query.filter(Order.sales_office_id == sales_office_id)
    
    top_results = top_query.group_by(ClothingItem.id, ClothingItem.name).order_by(func.sum(OrderItem.total_price).desc()).limit(10).all()
    
    top_products = [
        {
            "id": r.id,
            "name": r.name,
            "quantity": r.quantity or 0,
            "amount": r.amount or 0,
        }
        for r in top_results
    ]
    
    # 결제 수단별 현황 (포인트만 사용)
    payment_methods = [
        {
            "type": "points",
            "count": total_orders,
            "amount": total_points,
            "percentage": 100.0 if total_sales > 0 else 0,
        }
    ]
    
    # 카테고리별 판매
    from app.models.clothing import Category
    category_query = db.query(
        Category.name.label("name"),
        func.sum(OrderItem.total_price).label("amount"),
    ).join(ClothingItem, ClothingItem.category_id == Category.id).join(OrderItem, OrderItem.item_id == ClothingItem.id).join(Order, Order.id == OrderItem.order_id).filter(
        Order.status != OrderStatus.CANCELLED,
        func.date(Order.ordered_at) >= startDate,
        func.date(Order.ordered_at) <= endDate,
    )
    
    if sales_office_id:
        category_query = category_query.filter(Order.sales_office_id == sales_office_id)
    
    category_results = category_query.group_by(Category.name).all()
    
    category_sales = [
        {
            "name": r.name,
            "amount": r.amount or 0,
        }
        for r in category_results
    ]
    
    return {
        "totalSales": total_sales,
        "totalOrders": total_orders,
        "totalPoints": total_points,
        "refundCount": refund_count,
        "dailySales": daily_sales,
        "topProducts": top_products,
        "paymentMethods": payment_methods,
        "categorySales": category_sales,
    }
