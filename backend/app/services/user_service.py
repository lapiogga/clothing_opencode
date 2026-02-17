from datetime import date, datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User, Rank, UserRankHistory, UserRole, UserRank, RANK_POINT_MAPPING
from app.models.point import PointGrant, PointTransaction, PointType, TransactionType
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse, PromoteRequest
from app.utils.auth import get_password_hash


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_service_number(self, service_number: str) -> Optional[User]:
        return self.db.query(User).filter(User.service_number == service_number).first()

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None,
        rank_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        keyword: Optional[str] = None,
    ) -> UserListResponse:
        query = self.db.query(User)

        if role:
            query = query.filter(User.role == role)
        if rank_id:
            query = query.filter(User.rank_id == rank_id)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if keyword:
            query = query.filter(
                or_(
                    User.name.contains(keyword),
                    User.username.contains(keyword),
                    User.service_number.contains(keyword),
                )
            )

        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        items = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

        return UserListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def create(self, user_data: UserCreate) -> User:
        if self.get_by_username(user_data.username):
            raise ValueError("이미 존재하는 사용자명입니다")
        if user_data.service_number and self.get_by_service_number(user_data.service_number):
            raise ValueError("이미 등록된 군번입니다")

        user = User(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            name=user_data.name,
            email=user_data.email,
            phone=user_data.phone,
            role=user_data.role,
            rank_id=user_data.rank_id,
            service_number=user_data.service_number,
            unit=user_data.unit,
            service_years=user_data.service_years,
            retirement_date=user_data.retirement_date,
            sales_office_id=user_data.sales_office_id,
            tailor_company_id=user_data.tailor_company_id,
            current_point=0,
            reserved_point=0,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: int, user_data: UserUpdate) -> User:
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def bulk_create(self, users: List[UserCreate]) -> Tuple[int, List[str]]:
        created = 0
        errors = []
        for i, user_data in enumerate(users):
            try:
                self.create(user_data)
                created += 1
            except ValueError as e:
                errors.append(f"행 {i + 1}: {str(e)}")
        return created, errors

    def promote(self, user_id: int, promote_data: PromoteRequest, granted_by: Optional[int] = None) -> User:
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        new_rank = self.db.query(Rank).filter(Rank.id == promote_data.new_rank_id).first()
        if not new_rank:
            raise ValueError("계급을 찾을 수 없습니다")

        old_rank = user.rank
        old_rank_id = user.rank_id

        point_diff = new_rank.annual_point - (old_rank.annual_point if old_rank else 0)

        history = UserRankHistory(
            user_id=user_id,
            old_rank_id=old_rank_id,
            new_rank_id=promote_data.new_rank_id,
            promotion_date=promote_data.promotion_date,
            point_adjustment=point_diff,
        )
        self.db.add(history)

        user.rank_id = promote_data.new_rank_id
        user.current_point += point_diff

        if point_diff != 0:
            transaction = PointTransaction(
                user_id=user_id,
                transaction_type=TransactionType.GRANT,
                amount=point_diff,
                balance_after=user.current_point,
                reserved_after=user.reserved_point,
                description=f"진급에 따른 포인트 조정 ({old_rank.name if old_rank else '없음'} → {new_rank.name})",
            )
            self.db.add(transaction)

        self.db.commit()
        self.db.refresh(user)
        return user

    def calculate_yearly_point(self, user: User, year: int, grant_date: date) -> dict:
        rank = user.rank
        if not rank:
            return {"base_amount": 0, "service_year_bonus": 0, "daily_calc_amount": 0, "total_amount": 0}

        base_amount = rank.annual_point
        service_year_bonus = rank.service_year_bonus * user.service_years

        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        if user.retirement_date and user.retirement_date.year == year:
            days_served = (user.retirement_date - year_start).days + 1
            total_days = 365 if year % 4 != 0 else 366
            daily_calc_amount = int((base_amount + service_year_bonus) * days_served / total_days)
        else:
            daily_calc_amount = 0

        total_amount = base_amount + service_year_bonus + daily_calc_amount
        if user.retirement_date and user.retirement_date.year == year:
            total_amount = daily_calc_amount

        return {
            "base_amount": base_amount,
            "service_year_bonus": service_year_bonus,
            "daily_calc_amount": daily_calc_amount,
            "total_amount": total_amount,
        }

    def get_user_point(self, user_id: int, year: Optional[int] = None) -> dict:
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        query = self.db.query(PointGrant).filter(PointGrant.user_id == user_id)
        if year:
            query = query.filter(PointGrant.year == year)

        grants = query.order_by(PointGrant.year.desc()).all()

        return {
            "user_id": user_id,
            "current_point": user.current_point,
            "reserved_point": user.reserved_point,
            "available_point": user.available_point,
            "grants": grants,
        }

    def _to_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            username=user.username,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            rank=user.rank,
            service_number=user.service_number,
            unit=user.unit,
            service_years=user.service_years,
            retirement_date=user.retirement_date,
            is_active=user.is_active,
            current_point=user.current_point,
            reserved_point=user.reserved_point,
            available_point=user.available_point,
            created_at=user.created_at,
        )
