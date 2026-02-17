"""
포인트 서비스
- 포인트 지급, 사용, 예약, 환불 등 포인트 관련 비즈니스 로직 처리
"""
from datetime import date, datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.point import PointGrant, PointTransaction, PointType, TransactionType
from app.schemas.point import (
    PointGrantCreate, PointGrantYearlyCreate, PointGrantResponse,
    PointTransactionResponse, PointHistoryResponse, MyPointResponse,
    PointBulkGrantRequest, PointSingleGrantRequest,
)
from app.services.user_service import UserService


class PointService:
    """
    포인트 관련 비즈니스 로직을 처리하는 서비스 클래스
    
    주요 기능:
    - 포인트 지급 (개별, 일괄, 연간)
    - 포인트 사용 및 예약
    - 포인트 환불 및 예약 해제
    - 포인트 이력 조회
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)

    def get_my_point(self, user_id: int, year: Optional[int] = None) -> MyPointResponse:
        """
        사용자의 현재 포인트 정보 조회
        
        Args:
            user_id: 사용자 ID
            year: 조회할 연도 (선택)
            
        Returns:
            MyPointResponse: 보유/예약/사용가능 포인트 및 지급 내역
        """
        user = self.user_service.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        query = self.db.query(PointGrant).filter(PointGrant.user_id == user_id)
        if year:
            query = query.filter(PointGrant.year == year)

        grants = query.order_by(PointGrant.year.desc()).all()

        return MyPointResponse(
            current_point=user.current_point,
            reserved_point=user.reserved_point,
            available_point=user.available_point,
            grants=[self._grant_to_response(g) for g in grants],
        )

    def get_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        transaction_type: Optional[TransactionType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> PointHistoryResponse:
        """
        사용자의 포인트 거래 내역 조회
        
        Args:
            user_id: 사용자 ID
            page: 페이지 번호
            page_size: 페이지 크기
            transaction_type: 거래 유형 필터 (선택)
            start_date: 시작일 필터 (선택)
            end_date: 종료일 필터 (선택)
            
        Returns:
            PointHistoryResponse: 거래 내역 목록
        """
        query = self.db.query(PointTransaction).filter(PointTransaction.user_id == user_id)

        if transaction_type:
            query = query.filter(PointTransaction.transaction_type == transaction_type)
        if start_date:
            query = query.filter(PointTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(PointTransaction.created_at < end_date)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(PointTransaction.created_at.desc()).offset(offset).limit(page_size).all()

        return PointHistoryResponse(
            items=[self._transaction_to_response(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_grant_history(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        전체 포인트 지급 내역 조회 (관리자용)
        
        Args:
            page: 페이지 번호
            page_size: 페이지 크기
            
        Returns:
            dict: 지급 내역 목록 (사용자 정보 포함)
        """
        query = self.db.query(PointTransaction).filter(
            PointTransaction.transaction_type == TransactionType.GRANT
        )

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(PointTransaction.created_at.desc()).offset(offset).limit(page_size).all()

        result = []
        for t in items:
            user = self.db.query(User).filter(User.id == t.user_id).first()
            result.append({
                "id": t.id,
                "createdAt": t.created_at.isoformat() if t.created_at else None,
                "user": {
                    "id": user.id if user else None,
                    "name": user.name if user else "알 수 없음",
                    "employeeId": user.service_number if user else None,
                    "unit": user.unit if user else None,
                },
                "amount": t.amount,
                "reason": t.description.split("(")[1].rstrip(")") if t.description and "(" in t.description else "기타",
                "note": t.description,
            })

        return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def grant_point(self, data: PointGrantCreate, granted_by: Optional[int] = None) -> PointGrant:
        """
        포인트 지급 (정규 지급)
        - PointGrant 레코드 생성
        - 사용자 포인트 증가
        - PointTransaction 생성
        
        Args:
            data: 지급 정보 (사용자ID, 연도, 유형, 금액 등)
            granted_by: 지급자 ID
            
        Returns:
            PointGrant: 생성된 지급 내역
        """
        user = self.user_service.get_by_id(data.user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        # 중복 지급 방지: 동일 사용자/연도/유형의 지급 내역 확인
        existing = (
            self.db.query(PointGrant)
            .filter(
                PointGrant.user_id == data.user_id,
                PointGrant.year == data.year,
                PointGrant.point_type == data.point_type,
            )
            .first()
        )
        if existing:
            raise ValueError(f"{data.year}년 {data.point_type.value} 포인트가 이미 지급되었습니다")

        # 지급 내역 생성
        grant = PointGrant(
            user_id=data.user_id,
            year=data.year,
            point_type=data.point_type,
            base_amount=data.base_amount,
            service_year_bonus=data.service_year_bonus,
            daily_calc_amount=data.daily_calc_amount,
            total_amount=data.base_amount + data.service_year_bonus + data.daily_calc_amount,
            grant_date=date.today(),
            description=data.description,
            granted_by=granted_by,
        )
        self.db.add(grant)

        # 사용자 포인트 증가
        user.current_point += grant.total_amount

        # 거래 내역 생성
        transaction = PointTransaction(
            user_id=data.user_id,
            transaction_type=TransactionType.GRANT,
            amount=grant.total_amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            point_grant_id=grant.id,
            description=data.description or f"{data.year}년 {data.point_type.value} 포인트 지급",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(grant)
        return grant

    def grant_yearly(self, data: PointGrantYearlyCreate, granted_by: Optional[int] = None) -> Tuple[int, List[str]]:
        """
        연간 포인트 일괄 지급
        - 대상 사용자의 연간 포인트 자동 계산 후 지급
        
        Args:
            data: 지급 정보 (연도, 대상 사용자 ID 목록)
            granted_by: 지급자 ID
            
        Returns:
            Tuple[int, List[str]]: (지급 성공 수, 오류 메시지 목록)
        """
        if data.user_ids:
            users = [self.user_service.get_by_id(uid) for uid in data.user_ids]
            users = [u for u in users if u is not None]
        else:
            users = self.db.query(User).filter(User.is_active == True, User.rank_id != None).all()

        granted_count = 0
        errors = []

        for user in users:
            try:
                # 연간 포인트 자동 계산
                calc = self.user_service.calculate_yearly_point(user, data.year, data.grant_date)

                grant_data = PointGrantCreate(
                    user_id=user.id,
                    year=data.year,
                    point_type=data.point_type,
                    base_amount=calc["base_amount"],
                    service_year_bonus=calc["service_year_bonus"],
                    daily_calc_amount=calc["daily_calc_amount"],
                    description=f"{data.year}년 연간 포인트 지급",
                )
                self.grant_point(grant_data, granted_by)
                granted_count += 1
            except ValueError as e:
                errors.append(f"{user.name}({user.service_number}): {str(e)}")
            except Exception as e:
                errors.append(f"{user.name}({user.service_number}): 포인트 지급 중 오류 발생")

        return granted_count, errors

    def grant_single(self, data: PointSingleGrantRequest, granted_by: Optional[int] = None) -> dict:
        """
        개별 포인트 지급 (간편 지급)
        - PointGrant 없이 바로 PointTransaction만 생성
        
        Args:
            data: 지급 정보 (사용자ID, 금액, 사유)
            granted_by: 지급자 ID
            
        Returns:
            dict: 지급 결과
        """
        user = self.user_service.get_by_id(data.user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        # 사용자 포인트 증가
        user.current_point += data.amount

        # 거래 내역 생성
        transaction = PointTransaction(
            user_id=data.user_id,
            transaction_type=TransactionType.GRANT,
            amount=data.amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            description=data.note or f"포인트 지급 ({data.reason})",
        )
        self.db.add(transaction)

        self.db.commit()
        
        return {
            "user_id": data.user_id,
            "user_name": user.name,
            "amount": data.amount,
            "balance_after": user.current_point,
        }

    def grant_bulk(self, data: PointBulkGrantRequest, granted_by: Optional[int] = None) -> Tuple[int, List[str]]:
        """
        일괄 포인트 지급
        - 전체 또는 특정 계급 사용자에게 동일 금액 지급
        
        Args:
            data: 지급 정보 (대상, 금액, 사유)
            granted_by: 지급자 ID
            
        Returns:
            Tuple[int, List[str]]: (지급 성공 수, 오류 메시지 목록)
        """
        query = self.db.query(User).filter(User.is_active == True)
        
        if data.target == "rank" and data.rank_id:
            query = query.filter(User.rank_id == data.rank_id)
        
        users = query.all()
        
        granted_count = 0
        errors = []
        
        for user in users:
            try:
                user.current_point += data.amount
                
                transaction = PointTransaction(
                    user_id=user.id,
                    transaction_type=TransactionType.GRANT,
                    amount=data.amount,
                    balance_after=user.current_point,
                    reserved_after=user.reserved_point,
                    description=data.note or f"일괄 포인트 지급 ({data.reason})",
                )
                self.db.add(transaction)
                granted_count += 1
            except Exception as e:
                errors.append(f"{user.name}: {str(e)}")
        
        self.db.commit()
        
        return granted_count, errors

    def use_point(
        self,
        user_id: int,
        amount: int,
        order_id: Optional[int] = None,
        voucher_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> PointTransaction:
        """
        포인트 사용 (즉시 차감)
        - 오프라인 판매 시 사용
        
        Args:
            user_id: 사용자 ID
            amount: 사용할 금액
            order_id: 주문 ID (선택)
            voucher_id: 체척권 ID (선택)
            description: 설명
            
        Returns:
            PointTransaction: 생성된 거래 내역
        """
        user = self.user_service.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        if user.available_point < amount:
            raise ValueError(f"사용 가능한 포인트가 부족합니다 (현재: {user.available_point})")

        user.current_point -= amount

        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.USE,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            voucher_id=voucher_id,
            description=description or "포인트 사용",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def reserve_point(
        self,
        user_id: int,
        amount: int,
        order_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> PointTransaction:
        """
        포인트 예약 (온라인 주문 시)
        - 주문 시 포인트를 예약하여 다른 주문에 사용되지 않도록 함
        
        Args:
            user_id: 사용자 ID
            amount: 예약할 금액
            order_id: 주문 ID
            description: 설명
            
        Returns:
            PointTransaction: 생성된 거래 내역
        """
        user = self.user_service.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        if user.available_point < amount:
            raise ValueError(f"예약 가능한 포인트가 부족합니다 (현재: {user.available_point})")

        # 예약 포인트 증가
        user.reserved_point += amount

        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.RESERVE,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            description=description or "포인트 예약",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def release_point(
        self,
        user_id: int,
        amount: int,
        order_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> PointTransaction:
        """
        포인트 예약 해제 (주문 취소 시)
        - 예약된 포인트를 다시 사용 가능 상태로 복구
        
        Args:
            user_id: 사용자 ID
            amount: 해제할 금액
            order_id: 주문 ID
            description: 설명
            
        Returns:
            PointTransaction: 생성된 거래 내역
        """
        user = self.user_service.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        if user.reserved_point < amount:
            raise ValueError(f"해제할 예약 포인트가 부족합니다 (현재: {user.reserved_point})")

        user.reserved_point -= amount

        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.RELEASE,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            description=description or "포인트 예약 해제",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def deduct_reserved(
        self,
        user_id: int,
        amount: int,
        order_id: Optional[int] = None,
        voucher_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> PointTransaction:
        """
        예약 포인트 차감 (배송 완료 시)
        - 예약된 포인트를 실제로 차감
        - reserved_point와 current_point 모두 감소
        
        Args:
            user_id: 사용자 ID
            amount: 차감할 금액
            order_id: 주문 ID
            voucher_id: 체척권 ID
            description: 설명
            
        Returns:
            PointTransaction: 생성된 거래 내역
        """
        user = self.user_service.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        if user.reserved_point < amount:
            raise ValueError(f"차감할 예약 포인트가 부족합니다 (현재: {user.reserved_point})")

        user.reserved_point -= amount
        user.current_point -= amount

        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.DEDUCT,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            voucher_id=voucher_id,
            description=description or "예약 포인트 차감",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def refund_point(
        self,
        user_id: int,
        amount: int,
        order_id: Optional[int] = None,
        voucher_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> PointTransaction:
        """
        포인트 환불
        - 반품이나 오류로 인한 포인트 복구
        
        Args:
            user_id: 사용자 ID
            amount: 환불할 금액
            order_id: 주문 ID
            voucher_id: 체척권 ID
            description: 설명
            
        Returns:
            PointTransaction: 생성된 거래 내역
        """
        user = self.user_service.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다")

        user.current_point += amount

        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.REFUND,
            amount=amount,
            balance_after=user.current_point,
            reserved_after=user.reserved_point,
            order_id=order_id,
            voucher_id=voucher_id,
            description=description or "포인트 환불",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def _grant_to_response(self, grant: PointGrant) -> PointGrantResponse:
        """PointGrant 모델을 응답 스키마로 변환"""
        return PointGrantResponse(
            id=grant.id,
            user_id=grant.user_id,
            year=grant.year,
            point_type=grant.point_type,
            base_amount=grant.base_amount,
            service_year_bonus=grant.service_year_bonus,
            daily_calc_amount=grant.daily_calc_amount,
            total_amount=grant.total_amount,
            grant_date=grant.grant_date,
            granted_by=grant.granted_by,
            description=grant.description,
            created_at=grant.created_at,
        )

    def _transaction_to_response(self, transaction: PointTransaction) -> PointTransactionResponse:
        """PointTransaction 모델을 응답 스키마로 변환"""
        return PointTransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            balance_after=transaction.balance_after,
            reserved_after=transaction.reserved_after,
            order_id=transaction.order_id,
            voucher_id=transaction.voucher_id,
            description=transaction.description,
            created_at=transaction.created_at,
        )
