"""
재고 관리 라우터
- 판매소별 재고 조회, 입고, 조정, 이력 관리
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole
from app.models.clothing import ClothingItem, ClothingSpec, Category
from app.models.sales import Inventory, SalesOffice
from app.schemas.sales import InventoryAdjust, InventoryReceive, InventoryResponse, InventoryHistoryResponse
from app.services import inventory_service
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def get_sales_office_filter(current_user: TokenData, db: Session, sales_office_id: Optional[int] = None) -> Optional[int]:
    """
    판매소 필터 결정
    - 관리자: 요청 파라미터의 sales_office_id 사용
    - 판매소 담당자: 자신의 sales_office_id로 강제 설정
    - 그 외: None (전체 조회 불가)
    """
    if current_user.role == UserRole.ADMIN.value:
        return sales_office_id
    elif current_user.role == UserRole.SALES_OFFICE.value:
        # 판매소 담당자는 자신의 판매소만 조회 가능
        from app.services.user_service import UserService
        user = UserService(db).get_by_id(current_user.user_id)
        if user and user.sales_office_id:
            return user.sales_office_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="판매소 정보가 없습니다"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="재고 조회 권한이 없습니다"
        )


@router.get("/summary")
def get_inventory_summary(
    sales_office_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    재고 요약 정보 조회
    - 전체 품목 수, 재고 부족 품목, 품절 품목
    """
    office_id = get_sales_office_filter(current_user, db, sales_office_id)
    summary = inventory_service.get_inventory_summary(db, sales_office_id=office_id)
    return summary


@router.get("")
def get_inventory(
    sales_office_id: Optional[int] = None,
    item_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    재고 목록 조회
    - 판매소별, 품목별 필터링
    - 품목명, 카테고리 정보 포함
    """
    office_id = get_sales_office_filter(current_user, db, sales_office_id)
    
    # 기본 쿼리
    query = db.query(Inventory)
    if office_id:
        query = query.filter(Inventory.sales_office_id == office_id)
    if item_id:
        query = query.filter(Inventory.item_id == item_id)
    
    # 품목명 검색
    if keyword:
        query = query.join(ClothingItem).filter(
            ClothingItem.name.contains(keyword)
        )
    
    total = query.count()
    inventory_list = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 응답 데이터 구성 (품목 정보 포함)
    items = []
    for inv in inventory_list:
        item = db.query(ClothingItem).filter(ClothingItem.id == inv.item_id).first()
        spec = db.query(ClothingSpec).filter(ClothingSpec.id == inv.spec_id).first() if inv.spec_id else None
        category = db.query(Category).filter(Category.id == item.category_id).first() if item else None
        sales_office = db.query(SalesOffice).filter(SalesOffice.id == inv.sales_office_id).first()
        
        items.append({
            "id": inv.id,
            "sales_office_id": inv.sales_office_id,
            "sales_office": {
                "id": sales_office.id if sales_office else None,
                "name": sales_office.name if sales_office else None,
            } if sales_office else None,
            "item_id": inv.item_id,
            "spec_id": inv.spec_id,
            "quantity": inv.quantity,
            "reserved_quantity": inv.reserved_quantity,
            "available_quantity": inv.available_quantity,
            "product": {
                "id": item.id if item else None,
                "name": item.name if item else None,
                "category": {
                    "id": category.id if category else None,
                    "name": category.name if category else None,
                } if category else None,
            } if item else None,
            "spec": {
                "id": spec.id if spec else None,
                "size": spec.size if spec else None,
                "price": spec.price if spec else None,
            } if spec else None,
            "minStock": 10,
            "lastUpdated": inv.updated_at.isoformat() if inv.updated_at else None,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/receive", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def receive_inventory(
    receive_data: InventoryReceive,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    재고 입고 처리
    - 판매소 담당자만 자신의 판매소에 입고 가능
    """
    # 권한 확인
    get_sales_office_filter(current_user, db, receive_data.sales_office_id)
    
    inventory = inventory_service.receive_inventory(db, staff_id=current_user.user_id, receive_data=receive_data)
    return {
        "id": inventory.id,
        "sales_office_id": inventory.sales_office_id,
        "item_id": inventory.item_id,
        "spec_id": inventory.spec_id,
        "quantity": inventory.quantity,
        "reserved_quantity": inventory.reserved_quantity,
        "available_quantity": inventory.available_quantity,
    }


@router.post("/adjust", response_model=InventoryResponse)
def adjust_inventory(
    adjust_data: InventoryAdjust,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    재고 조정 처리
    - 입고, 출고, 재고조사 등
    """
    # 권한 확인
    get_sales_office_filter(current_user, db, adjust_data.sales_office_id)
    
    inventory = inventory_service.adjust_inventory(db, staff_id=current_user.user_id, adjust_data=adjust_data)
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="재고 정보를 찾을 수 없습니다")
    return {
        "id": inventory.id,
        "sales_office_id": inventory.sales_office_id,
        "item_id": inventory.item_id,
        "spec_id": inventory.spec_id,
        "quantity": inventory.quantity,
        "reserved_quantity": inventory.reserved_quantity,
        "available_quantity": inventory.available_quantity,
    }


@router.get("/history")
def get_inventory_history(
    inventory_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    재고 이력 조회
    - 판매소별 이력만 조회 가능
    """
    # 판매소 필터 확인
    office_id = get_sales_office_filter(current_user, db, None)
    
    skip = (page - 1) * page_size
    history, total = inventory_service.get_inventory_history(
        db, 
        inventory_id=inventory_id, 
        sales_office_id=office_id,
        skip=skip, 
        limit=page_size
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": h.id,
                "inventory_id": h.inventory_id,
                "adjustment_type": h.adjustment_type.value,
                "quantity": h.quantity,
                "before_quantity": h.before_quantity,
                "after_quantity": h.after_quantity,
                "reason": h.reason,
                "adjustment_date": h.adjustment_date.isoformat() if h.adjustment_date else None,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
    }


@router.get("/available")
def get_available_inventory(
    sales_office_id: int,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> Any:
    """
    판매 가능한 재고 목록 조회 (일반 사용자용)
    - 지정된 판매소의 가용 재고만 조회
    - 품목 정보 포함
    """
    sales_office = db.query(SalesOffice).filter(SalesOffice.id == sales_office_id).first()
    if not sales_office:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="판매소를 찾을 수 없습니다")
    
    query = db.query(Inventory).filter(
        Inventory.sales_office_id == sales_office_id,
        Inventory.quantity > 0
    )
    
    if keyword:
        query = query.join(ClothingItem).filter(
            ClothingItem.name.contains(keyword)
        )
    
    total = query.count()
    inventory_list = query.offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for inv in inventory_list:
        item = db.query(ClothingItem).filter(ClothingItem.id == inv.item_id).first()
        if not item or not item.is_active:
            continue
        spec = db.query(ClothingSpec).filter(ClothingSpec.id == inv.spec_id).first() if inv.spec_id else None
        category = db.query(Category).filter(Category.id == item.category_id).first() if item else None
        
        items.append({
            "inventory_id": inv.id,
            "item_id": inv.item_id,
            "spec_id": inv.spec_id,
            "item_name": item.name,
            "category_id": category.id if category else None,
            "category_name": category.name if category else None,
            "clothing_type": item.clothing_type.value,
            "description": item.description,
            "image_url": item.image_url,
            "spec_size": spec.size if spec else None,
            "spec_price": spec.price if spec else None,
            "available_quantity": inv.available_quantity,
            "reserved_quantity": inv.reserved_quantity,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "sales_office": {
            "id": sales_office.id,
            "name": sales_office.name,
        }
    }
