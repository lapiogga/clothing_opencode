from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserRole
from app.models.point import PointType, TransactionType
from app.schemas.point import (
    PointGrantCreate, PointGrantYearlyCreate, PointGrantResponse,
    PointTransactionResponse, PointHistoryResponse, MyPointResponse,
    PointBulkGrantRequest, PointSingleGrantRequest,
)
from app.services.point_service import PointService
from app.utils.auth import get_current_user, TokenData

router = APIRouter()


def check_admin_or_sales(current_user: TokenData = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN.value, UserRole.SALES_OFFICE.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 또는 군수담당자 권한이 필요합니다"
        )
    return current_user


@router.get("/my", response_model=MyPointResponse)
def get_my_point(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = PointService(db)
    try:
        return service.get_my_point(current_user.user_id, year)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/history", response_model=PointHistoryResponse)
def get_point_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    service = PointService(db)
    return service.get_history(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/grant", response_model=PointGrantResponse, status_code=status.HTTP_201_CREATED)
def grant_point(
    data: PointGrantCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin_or_sales),
):
    service = PointService(db)
    try:
        grant = service.grant_point(data, current_user.user_id)
        return service._grant_to_response(grant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/grant-single", status_code=status.HTTP_201_CREATED)
def grant_single_point(
    data: PointSingleGrantRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin_or_sales),
):
    service = PointService(db)
    try:
        result = service.grant_single(data, current_user.user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/grant-bulk")
def grant_bulk_point(
    data: PointBulkGrantRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin_or_sales),
):
    service = PointService(db)
    try:
        granted, errors = service.grant_bulk(data, current_user.user_id)
        return {"granted": granted, "errors": errors}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/grant-history")
def get_grant_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin_or_sales),
):
    service = PointService(db)
    return service.get_grant_history(
        page=page,
        page_size=page_size,
    )


@router.post("/grant-yearly")
def grant_yearly_point(
    data: PointGrantYearlyCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin_or_sales),
):
    service = PointService(db)
    granted, errors = service.grant_yearly(data, current_user.user_id)
    return {
        "granted": granted,
        "errors": errors,
    }


@router.get("/user/{user_id}", response_model=MyPointResponse)
def get_user_point(
    user_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin_or_sales),
):
    service = PointService(db)
    try:
        return service.get_my_point(user_id, year)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/history", response_model=PointHistoryResponse)
def get_user_point_history(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_admin_or_sales),
):
    service = PointService(db)
    return service.get_history(
        user_id=user_id,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
    )
