from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole, Rank
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserBulkImport, UserPointResponse, PromoteRequest, PromoteResponse,
)
from app.services.user_service import UserService
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


@router.get("/ranks")
def get_ranks(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    ranks = db.query(Rank).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "code": r.code.value,
            "rank_group": r.rank_group.value,
            "annual_point": r.annual_point,
        }
        for r in ranks
    ]


def check_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


@router.get("", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    rank_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = UserService(db)
    return service.get_list(
        page=page,
        page_size=page_size,
        role=role,
        rank_id=rank_id,
        is_active=is_active,
        keyword=keyword,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = UserService(db)
    try:
        user = service.create(user_data)
        return service._to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/by-service-number/{service_number}", response_model=UserResponse)
def get_user_by_service_number(
    service_number: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = UserService(db)
    user = service.get_by_service_number(service_number)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다")
    return service._to_response(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = UserService(db)
    user = service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다")
    return service._to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = UserService(db)
    try:
        user = service.update(user_id, user_data)
        return service._to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = UserService(db)
    if not service.delete(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다")


@router.post("/bulk-import")
def bulk_import_users(
    data: UserBulkImport,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = UserService(db)
    created, errors = service.bulk_create(data.users)
    return {
        "created": created,
        "total": len(data.users),
        "errors": errors,
    }


@router.post("/{user_id}/promote", response_model=PromoteResponse)
def promote_user(
    user_id: int,
    promote_data: PromoteRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin),
):
    service = UserService(db)
    try:
        user = service.promote(user_id, promote_data, current_user.user_id)
        history = user.rank_histories[-1]
        return PromoteResponse(
            user_id=user_id,
            old_rank=history.old_rank,
            new_rank=history.new_rank,
            point_adjustment=history.point_adjustment,
            promotion_date=history.promotion_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}/point", response_model=UserPointResponse)
def get_user_point(
    user_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    from app.schemas.point import PointGrantResponse
    from app.models.point import PointGrant
    
    service = UserService(db)
    try:
        result = service.get_user_point(user_id, year)
        grants = [
            PointGrantResponse.model_validate(g) 
            for g in result["grants"]
        ]
        return UserPointResponse(
            user_id=result["user_id"],
            current_point=result["current_point"],
            reserved_point=result["reserved_point"],
            available_point=result["available_point"],
            annual_grants=grants,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
