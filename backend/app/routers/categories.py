from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.database import get_db
from app.models.user import UserRole
from app.models.clothing import CategoryLevel, ClothingType
from app.schemas.clothing import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeResponse,
)
from app.services.clothing_service import CategoryService
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


@router.get("", response_model=list[CategoryResponse])
def get_categories(
    level: Optional[CategoryLevel] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = CategoryService(db)
    return service.get_list(level=level, parent_id=parent_id)


@router.get("/tree", response_model=list[CategoryTreeResponse])
def get_category_tree(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = CategoryService(db)
    return service.get_tree()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = CategoryService(db)
    try:
        category = service.create(data)
        return CategoryResponse.model_validate(category)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = CategoryService(db)
    category = service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="카테고리를 찾을 수 없습니다")
    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = CategoryService(db)
    try:
        category = service.update(category_id, data)
        return CategoryResponse.model_validate(category)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = CategoryService(db)
    try:
        if not service.delete(category_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="카테고리를 찾을 수 없습니다")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/export")
def export_categories(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = CategoryService(db)
    return service.export_to_excel()


@router.post("/import")
def import_categories(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = CategoryService(db)
    try:
        result = service.import_from_excel(file.file)
        return {"message": f"{result['created']}개 카테고리가 생성되었습니다", "details": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
