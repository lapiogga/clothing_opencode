"""
메뉴 관리 서비스
"""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.menu import Menu, MenuPermission
from app.models.user import UserRole
from app.schemas.menu import MenuCreate, MenuUpdate, MenuTreeResponse


class MenuService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, menu_id: int) -> Optional[Menu]:
        return self.db.query(Menu).filter(Menu.id == menu_id).first()

    def get_list(self, is_active: Optional[bool] = None) -> List[Menu]:
        query = self.db.query(Menu)
        if is_active is not None:
            query = query.filter(Menu.is_active == is_active)
        return query.order_by(Menu.sort_order).all()

    def get_tree(self) -> List[MenuTreeResponse]:
        """전체 메뉴 트리 조회"""
        root_menus = (
            self.db.query(Menu)
            .filter(Menu.parent_id == None, Menu.is_active == True)
            .order_by(Menu.sort_order)
            .all()
        )
        return [self._build_tree(menu) for menu in root_menus]

    def get_tree_by_role(self, role: str) -> List[MenuTreeResponse]:
        """역할별 메뉴 트리 조회"""
        root_menus = (
            self.db.query(Menu)
            .filter(Menu.parent_id == None, Menu.is_active == True)
            .order_by(Menu.sort_order)
            .all()
        )
        
        result = []
        for menu in root_menus:
            tree = self._build_tree_with_role(menu, role)
            if tree:
                result.append(tree)
        return result

    def _build_tree(self, menu: Menu) -> MenuTreeResponse:
        children = (
            self.db.query(Menu)
            .filter(Menu.parent_id == menu.id, Menu.is_active == True)
            .order_by(Menu.sort_order)
            .all()
        )
        return MenuTreeResponse(
            id=menu.id,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            parent_id=menu.parent_id,
            sort_order=menu.sort_order,
            is_category=menu.is_category,
            is_active=menu.is_active,
            allowed_roles=menu.get_allowed_roles_list(),
            children=[self._build_tree(child) for child in children],
            created_at=menu.created_at,
        )

    def _build_tree_with_role(self, menu: Menu, role: str) -> Optional[MenuTreeResponse]:
        """역할 권한에 따른 메뉴 트리 구성"""
        allowed_roles = menu.get_allowed_roles_list()
        
        # 대분류는 권한 체크 없이 표시, 하위 메뉴에서 필터링
        if not menu.is_category:
            # 권한이 없으면 None 반환
            if allowed_roles and role not in allowed_roles:
                return None

        # 하위 메뉴 조회
        children = (
            self.db.query(Menu)
            .filter(Menu.parent_id == menu.id, Menu.is_active == True)
            .order_by(Menu.sort_order)
            .all()
        )
        
        # 하위 메뉴 필터링
        filtered_children = []
        for child in children:
            child_tree = self._build_tree_with_role(child, role)
            if child_tree:
                filtered_children.append(child_tree)
        
        # 대분류인데 하위 메뉴가 없으면 None 반환
        if menu.is_category and not filtered_children:
            return None

        return MenuTreeResponse(
            id=menu.id,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            parent_id=menu.parent_id,
            sort_order=menu.sort_order,
            is_category=menu.is_category,
            is_active=menu.is_active,
            allowed_roles=allowed_roles,
            children=filtered_children,
            created_at=menu.created_at,
        )

    def create(self, data: MenuCreate) -> Menu:
        if data.parent_id:
            parent = self.get_by_id(data.parent_id)
            if not parent:
                raise ValueError("상위 메뉴를 찾을 수 없습니다")

        menu = Menu(
            name=data.name,
            path=data.path,
            icon=data.icon,
            parent_id=data.parent_id,
            sort_order=data.sort_order,
            is_category=data.is_category,
            is_active=data.is_active,
        )
        menu.set_allowed_roles_list(data.allowed_roles)
        
        self.db.add(menu)
        self.db.commit()
        self.db.refresh(menu)
        return menu

    def update(self, menu_id: int, data: MenuUpdate) -> Menu:
        menu = self.get_by_id(menu_id)
        if not menu:
            raise ValueError("메뉴를 찾을 수 없습니다")

        update_data = data.model_dump(exclude_unset=True)
        
        # allowed_roles 별도 처리
        if 'allowed_roles' in update_data:
            menu.set_allowed_roles_list(update_data.pop('allowed_roles'))
        
        for key, value in update_data.items():
            setattr(menu, key, value)

        self.db.commit()
        self.db.refresh(menu)
        return menu

    def delete(self, menu_id: int) -> bool:
        menu = self.get_by_id(menu_id)
        if not menu:
            return False

        # 하위 메뉴 확인
        has_children = self.db.query(Menu).filter(Menu.parent_id == menu_id).first()
        if has_children:
            raise ValueError("하위 메뉴가 있어 삭제할 수 없습니다")

        self.db.delete(menu)
        self.db.commit()
        return True

    def initialize_default_menus(self):
        """기본 메뉴 초기화"""
        default_menus = [
            {"name": "대시보드", "path": "/", "sort_order": 0, "is_category": False, "allowed_roles": ["admin", "sales_office", "tailor_company", "general"]},
            
            {"name": "시스템 관리", "path": None, "sort_order": 10, "is_category": True, "allowed_roles": ["admin"]},
            {"name": "사용자 관리", "path": "/admin/users", "sort_order": 11, "is_category": False, "parent_name": "시스템 관리", "allowed_roles": ["admin"]},
            {"name": "피복판매소 관리", "path": "/admin/sales-offices", "sort_order": 12, "is_category": False, "parent_name": "시스템 관리", "allowed_roles": ["admin"]},
            {"name": "체척업체 관리", "path": "/admin/tailor-companies", "sort_order": 13, "is_category": False, "parent_name": "시스템 관리", "allowed_roles": ["admin"]},
            {"name": "화면 관리", "path": "/admin/menus", "sort_order": 14, "is_category": False, "parent_name": "시스템 관리", "allowed_roles": ["admin"]},
            
            {"name": "품목 관리", "path": None, "sort_order": 20, "is_category": True, "allowed_roles": ["admin"]},
            {"name": "카테고리 관리", "path": "/admin/categories", "sort_order": 21, "is_category": False, "parent_name": "품목 관리", "allowed_roles": ["admin"]},
            {"name": "피복 품목 관리", "path": "/admin/clothing", "sort_order": 22, "is_category": False, "parent_name": "품목 관리", "allowed_roles": ["admin"]},
            
            {"name": "포인트 관리", "path": None, "sort_order": 30, "is_category": True, "allowed_roles": ["admin"]},
            {"name": "포인트 지급", "path": "/admin/points", "sort_order": 31, "is_category": False, "parent_name": "포인트 관리", "allowed_roles": ["admin"]},
            
            {"name": "판매 관리", "path": None, "sort_order": 40, "is_category": True, "allowed_roles": ["sales_office"]},
            {"name": "오프라인 판매", "path": "/sales/offline", "sort_order": 41, "is_category": False, "parent_name": "판매 관리", "allowed_roles": ["sales_office"]},
            {"name": "온라인 주문 관리", "path": "/sales/orders", "sort_order": 42, "is_category": False, "parent_name": "판매 관리", "allowed_roles": ["sales_office"]},
            {"name": "재고 관리", "path": "/sales/inventory", "sort_order": 43, "is_category": False, "parent_name": "판매 관리", "allowed_roles": ["sales_office"]},
            {"name": "반품 처리", "path": "/sales/refund", "sort_order": 44, "is_category": False, "parent_name": "판매 관리", "allowed_roles": ["sales_office"]},
            {"name": "통계", "path": "/sales/stats", "sort_order": 45, "is_category": False, "parent_name": "판매 관리", "allowed_roles": ["sales_office"]},
            
            {"name": "쇼핑몰", "path": None, "sort_order": 50, "is_category": True, "allowed_roles": ["admin", "general"]},
            {"name": "피복 쇼핑", "path": "/user/shop", "sort_order": 51, "is_category": False, "parent_name": "쇼핑몰", "allowed_roles": ["admin", "general"]},
            {"name": "장바구니", "path": "/user/cart", "sort_order": 52, "is_category": False, "parent_name": "쇼핑몰", "allowed_roles": ["admin", "general"]},
            {"name": "주문/배송 조회", "path": "/user/orders", "sort_order": 53, "is_category": False, "parent_name": "쇼핑몰", "allowed_roles": ["admin", "general"]},
            {"name": "포인트 조회", "path": "/user/points", "sort_order": 54, "is_category": False, "parent_name": "쇼핑몰", "allowed_roles": ["admin", "general"]},
            
            {"name": "체척권 관리", "path": None, "sort_order": 60, "is_category": True, "allowed_roles": ["tailor_company"]},
            {"name": "체척권 등록", "path": "/tailor/register", "sort_order": 61, "is_category": False, "parent_name": "체척권 관리", "allowed_roles": ["tailor_company"]},
            {"name": "체척권 현황", "path": "/tailor/vouchers", "sort_order": 62, "is_category": False, "parent_name": "체척권 관리", "allowed_roles": ["tailor_company"]},
            
            {"name": "내 정보", "path": None, "sort_order": 70, "is_category": True, "allowed_roles": ["admin", "sales_office", "tailor_company", "general"]},
            {"name": "프로필", "path": "/user/profile", "sort_order": 71, "is_category": False, "parent_name": "내 정보", "allowed_roles": ["admin", "sales_office", "tailor_company", "general"]},
        ]
        
        # 이미 메뉴가 있으면 초기화하지 않음
        existing = self.db.query(Menu).first()
        if existing:
            return
        
        parent_map = {}
        for menu_data in default_menus:
            parent_name = menu_data.pop("parent_name", None)
            
            menu = Menu(**menu_data)
            menu.set_allowed_roles_list(menu_data["allowed_roles"])
            
            if parent_name and parent_name in parent_map:
                menu.parent_id = parent_map[parent_name]
            
            self.db.add(menu)
            self.db.flush()  # ID 생성을 위해 flush
            parent_map[menu.name] = menu.id
        
        self.db.commit()
