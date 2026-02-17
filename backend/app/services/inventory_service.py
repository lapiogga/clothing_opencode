from typing import Optional

from sqlalchemy.orm import Session

from app.models.sales import Inventory, InventoryHistory, AdjustmentType
from app.schemas.sales import InventoryAdjust, InventoryReceive


def get_inventory_list(
    db: Session, 
    sales_office_id: Optional[int] = None, 
    item_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50
) -> tuple[list[Inventory], int]:
    query = db.query(Inventory)
    if sales_office_id:
        query = query.filter(Inventory.sales_office_id == sales_office_id)
    if item_id:
        query = query.filter(Inventory.item_id == item_id)
    total = query.count()
    inventory_list = query.offset(skip).limit(limit).all()
    return inventory_list, total


def get_inventory(db: Session, inventory_id: int) -> Optional[Inventory]:
    return db.query(Inventory).filter(Inventory.id == inventory_id).first()


def receive_inventory(db: Session, staff_id: int, receive_data: InventoryReceive) -> Inventory:
    inventory = db.query(Inventory).filter(
        Inventory.sales_office_id == receive_data.sales_office_id,
        Inventory.item_id == receive_data.item_id,
        Inventory.spec_id == receive_data.spec_id,
    ).first()
    
    if not inventory:
        inventory = Inventory(
            sales_office_id=receive_data.sales_office_id,
            item_id=receive_data.item_id,
            spec_id=receive_data.spec_id,
            quantity=0,
            reserved_quantity=0,
        )
        db.add(inventory)
        db.flush()
    
    before = inventory.quantity
    inventory.quantity += receive_data.quantity
    
    history = InventoryHistory(
        inventory_id=inventory.id,
        adjustment_type=AdjustmentType.INCREASE,
        quantity=receive_data.quantity,
        before_quantity=before,
        after_quantity=inventory.quantity,
        reason="입고",
        adjusted_by=staff_id,
    )
    db.add(history)
    
    db.commit()
    db.refresh(inventory)
    return inventory


def adjust_inventory(db: Session, staff_id: int, adjust_data: InventoryAdjust) -> Optional[Inventory]:
    inventory = db.query(Inventory).filter(
        Inventory.sales_office_id == adjust_data.sales_office_id,
        Inventory.item_id == adjust_data.item_id,
        Inventory.spec_id == adjust_data.spec_id,
    ).first()
    
    if not inventory:
        return None
    
    before = inventory.quantity
    
    if adjust_data.adjustment_type == AdjustmentType.INCREASE:
        inventory.quantity += adjust_data.quantity
    elif adjust_data.adjustment_type == AdjustmentType.DECREASE:
        inventory.quantity -= adjust_data.quantity
    elif adjust_data.adjustment_type == AdjustmentType.CORRECTION:
        inventory.quantity = adjust_data.quantity
    
    history = InventoryHistory(
        inventory_id=inventory.id,
        adjustment_type=adjust_data.adjustment_type,
        quantity=adjust_data.quantity,
        before_quantity=before,
        after_quantity=inventory.quantity,
        reason=adjust_data.reason,
        adjusted_by=staff_id,
    )
    db.add(history)
    
    db.commit()
    db.refresh(inventory)
    return inventory


def get_inventory_history(
    db: Session, 
    inventory_id: Optional[int] = None, 
    sales_office_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 50
) -> tuple[list, int]:
    query = db.query(InventoryHistory)
    if inventory_id:
        query = query.filter(InventoryHistory.inventory_id == inventory_id)
    if sales_office_id:
        # 해당 판매소의 재고에 대한 이력만 조회
        query = query.join(Inventory).filter(Inventory.sales_office_id == sales_office_id)
    total = query.count()
    history = query.order_by(InventoryHistory.id.desc()).offset(skip).limit(limit).all()
    return history, total


def get_inventory_summary(db: Session, sales_office_id: Optional[int] = None) -> dict:
    query = db.query(Inventory)
    if sales_office_id:
        query = query.filter(Inventory.sales_office_id == sales_office_id)
    
    inventory_list = query.all()
    
    total_items = len(inventory_list)
    low_stock = sum(1 for inv in inventory_list if 0 < inv.quantity <= 10)
    out_of_stock = sum(1 for inv in inventory_list if inv.quantity == 0)
    
    return {
        "totalItems": total_items,
        "lowStock": low_stock,
        "outOfStock": out_of_stock,
    }
