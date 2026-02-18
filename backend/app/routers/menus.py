"""
메뉴 관리 라우터
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole
from app.schemas.menu import (
    MenuCreate, MenuUpdate, MenuResponse, MenuTreeResponse, MenuListResponse
)
from app.services.menu_service import MenuService
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


@router.get("/tree", response_model=list[MenuTreeResponse])
def get_menu_tree(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """역할별 메뉴 트리 조회"""
    service = MenuService(db)
    return service.get_tree_by_role(current_user.role)


@router.get("/all", response_model=MenuListResponse)
def get_all_menus(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    """전체 메뉴 목록 (관리자용)"""
    service = MenuService(db)
    menus = service.get_list(is_active)
    return MenuListResponse(
        items=[MenuResponse(
            id=m.id,
            name=m.name,
            path=m.path,
            icon=m.icon,
            parent_id=m.parent_id,
            sort_order=m.sort_order,
            is_category=m.is_category,
            is_active=m.is_active,
            allowed_roles=m.get_allowed_roles_list(),
            created_at=m.created_at,
        ) for m in menus],
        total=len(menus),
    )


@router.get("/tree/all", response_model=list[MenuTreeResponse])
def get_full_menu_tree(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    """전체 메뉴 트리 (관리자용)"""
    service = MenuService(db)
    return service.get_tree()


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(
    data: MenuCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    """메뉴 생성"""
    service = MenuService(db)
    try:
        menu = service.create(data)
        return MenuResponse(
            id=menu.id,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            parent_id=menu.parent_id,
            sort_order=menu.sort_order,
            is_category=menu.is_category,
            is_active=menu.is_active,
            allowed_roles=menu.get_allowed_roles_list(),
            created_at=menu.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{menu_id}", response_model=MenuResponse)
def update_menu(
    menu_id: int,
    data: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    """메뉴 수정"""
    service = MenuService(db)
    try:
        menu = service.update(menu_id, data)
        return MenuResponse(
            id=menu.id,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            parent_id=menu.parent_id,
            sort_order=menu.sort_order,
            is_category=menu.is_category,
            is_active=menu.is_active,
            allowed_roles=menu.get_allowed_roles_list(),
            created_at=menu.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    """메뉴 삭제"""
    service = MenuService(db)
    try:
        if not service.delete(menu_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="메뉴를 찾을 수 없습니다")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/initialize", status_code=status.HTTP_201_CREATED)
def initialize_menus(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    """기본 메뉴 초기화"""
    service = MenuService(db)
    service.initialize_default_menus()
    return {"message": "기본 메뉴가 초기화되었습니다"}
