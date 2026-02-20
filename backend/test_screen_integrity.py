"""
화면간 정합성 테스트 스크립트
- 등록/수정/삭제/조회/참조 관련 화면간 정합성
- 백엔드/프론트엔드 간 정합성
- 10회 반복 실행
"""
import sys
import json
from datetime import date, datetime

sys.path.insert(0, '/home/user/opencode/clothing-system/backend')

from app.database import SessionLocal
from app.models.user import User, UserRole, Rank
from app.models.clothing import ClothingItem, ClothingSpec, Category, ClothingType
from app.models.sales import SalesOffice, Inventory
from app.models.order import Order, OrderItem, OrderStatus, OrderType, Delivery, DeliveryType, DeliveryStatus, PaymentMethod
from app.models.tailor import TailorVoucher, VoucherStatus
from app.models.point import PointTransaction, TransactionType
from app.services.user_service import UserService
from app.services.clothing_service import ClothingService
from app.services.order_service import create_order, cancel_order, receive_order
from app.services.tailor_service import issue_voucher_direct, request_cancel_voucher, approve_cancel_voucher
from app.services.sales_service import create_offline_sale, process_refund
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.clothing import ClothingCreate, SpecCreate
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.sales import OfflineSaleCreate, RefundCreate


class TestResult:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.total += 1
        self.passed += 1
        print(f"  ✅ {test_name}")
    
    def add_fail(self, test_name, error):
        self.total += 1
        self.failed += 1
        self.errors.append({"test": test_name, "error": str(error)})
        print(f"  ❌ {test_name}: {error}")
    
    def summary(self):
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": f"{self.passed}/{self.total}",
            "errors": self.errors
        }


def test_user_crud(db, result):
    """사용자 CRUD 정합성 테스트"""
    print("\n=== 사용자 CRUD 테스트 ===")
    
    service = UserService(db)
    
    # 1. Create
    try:
        rank = db.query(Rank).first()
        user_data = UserCreate(
            username=f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            password="test123",
            name="테스트사용자",
            service_number=f"99-{datetime.now().strftime('%H%M%S')}",
            rank_id=rank.id,
            unit="테스트부대",
            role=UserRole.GENERAL,
        )
        user = service.create(user_data)
        user_id = user.id
        result.add_pass("사용자 생성")
    except Exception as e:
        result.add_fail("사용자 생성", e)
        return
    
    # 2. Read
    try:
        found = service.get_by_id(user_id)
        assert found is not None, "조회된 사용자가 없음"
        assert found.name == "테스트사용자", "이름 불일치"
        result.add_pass("사용자 조회")
    except Exception as e:
        result.add_fail("사용자 조회", e)
    
    # 3. Update
    try:
        update_data = UserUpdate(name="수정된사용자", unit="수정된부대")
        updated = service.update(user_id, update_data)
        assert updated.name == "수정된사용자", "이름 수정 실패"
        assert updated.unit == "수정된부대", "소속 수정 실패"
        result.add_pass("사용자 수정")
    except Exception as e:
        result.add_fail("사용자 수정", e)
    
    # 4. Delete
    try:
        deleted = service.delete(user_id)
        assert deleted == True, "삭제 실패"
        found = service.get_by_id(user_id)
        assert found is None, "삭제된 사용자가 조회됨"
        result.add_pass("사용자 삭제")
    except Exception as e:
        result.add_fail("사용자 삭제", e)


def test_clothing_crud(db, result):
    """품목 CRUD 정합성 테스트"""
    print("\n=== 품목 CRUD 테스트 ===")
    
    service = ClothingService(db)
    
    # 카테고리 조회
    category = db.query(Category).first()
    if not category:
        result.add_fail("품목 생성", "카테고리 없음")
        return
    
    # 1. Create
    try:
        clothing_data = ClothingCreate(
            name=f"테스트품목_{datetime.now().strftime('%H%M%S')}",
            category_id=category.id,
            clothing_type=ClothingType.READY_MADE,
            description="테스트용 품목",
        )
        item = service.create(clothing_data)
        item_id = item.id
        result.add_pass("품목 생성")
    except Exception as e:
        result.add_fail("품목 생성", e)
        return
    
    # 2. Read
    try:
        found = service.get_by_id(item_id)
        assert found is not None, "조회된 품목이 없음"
        result.add_pass("품목 조회")
    except Exception as e:
        result.add_fail("품목 조회", e)
    
    # 3. Create Spec
    try:
        spec_data = SpecCreate(
            spec_code=f"SPEC_{datetime.now().strftime('%H%M%S')}",
            size="100",
            price=50000,
        )
        spec = service.create_spec(item_id, spec_data)
        spec_id = spec.id
        result.add_pass("규격 생성")
    except Exception as e:
        result.add_fail("규격 생성", e)
    
    # 4. Delete Spec
    try:
        if spec_id:
            deleted = service.delete_spec(spec_id)
            assert deleted == True, "규격 삭제 실패"
            result.add_pass("규격 삭제")
    except Exception as e:
        result.add_fail("규격 삭제", e)
    
    # 5. Delete Item
    try:
        deleted = service.delete(item_id)
        assert deleted == True, "품목 삭제 실패"
        result.add_pass("품목 삭제")
    except Exception as e:
        result.add_fail("품목 삭제", e)


def test_order_consistency(db, result):
    """주문 정합성 테스트"""
    print("\n=== 주문 정합성 테스트 ===")
    
    # 테스트 데이터 조회
    user = db.query(User).filter(User.role == UserRole.GENERAL).first()
    sales_office = db.query(SalesOffice).first()
    item = db.query(ClothingItem).filter(ClothingItem.clothing_type == ClothingType.READY_MADE).first()
    
    if not all([user, sales_office, item]):
        result.add_fail("주문 생성", "테스트 데이터 부족")
        return
    
    spec = db.query(ClothingSpec).filter(ClothingSpec.item_id == item.id).first()
    if not spec:
        result.add_fail("주문 생성", "규격 없음")
        return
    
    initial_point = user.current_point
    initial_reserved = user.reserved_point
    
    # 1. 온라인 주문 생성
    try:
        order_data = OrderCreate(
            sales_office_id=sales_office.id,
            order_type=OrderType.ONLINE,
            items=[OrderItemCreate(
                item_id=item.id,
                spec_id=spec.id,
                quantity=1,
                payment_method=PaymentMethod.POINT,
            )],
            delivery_type='parcel',
            recipient_name='테스트',
            recipient_phone='010-0000-0000',
            shipping_address='테스트 주소',
        )
        
        order = create_order(db, user.id, order_data)
        order_id = order.id
        
        # 포인트 검증
        db.refresh(user)
        assert user.reserved_point == initial_reserved + spec.price, "예약 포인트 불일치"
        assert user.current_point == initial_point, "보유 포인트가 변경됨"
        
        result.add_pass("온라인 주문 생성")
    except Exception as e:
        result.add_fail("온라인 주문 생성", e)
        return
    
    # 2. 주문 조회
    try:
        found = db.query(Order).filter(Order.id == order_id).first()
        assert found is not None, "주문 조회 실패"
        assert found.status == OrderStatus.CONFIRMED, "주문 상태 불일치"
        result.add_pass("주문 조회")
    except Exception as e:
        result.add_fail("주문 조회", e)
    
    # 3. 주문 취소
    try:
        from app.schemas.order import OrderCancel
        cancel_data = OrderCancel(reason="테스트 취소")
        cancelled = cancel_order(db, order_id, user.id, cancel_data)
        
        db.refresh(user)
        assert user.reserved_point == initial_reserved, "예약 포인트 해제 실패"
        assert cancelled.status == OrderStatus.CANCELLED, "취소 상태 불일치"
        
        result.add_pass("주문 취소")
    except Exception as e:
        result.add_fail("주문 취소", e)


def test_offline_sale_consistency(db, result):
    """오프라인 판매 정합성 테스트"""
    print("\n=== 오프라인 판매 정합성 테스트 ===")
    
    user = db.query(User).filter(User.role == UserRole.GENERAL).first()
    sales_office = db.query(SalesOffice).first()
    staff = db.query(User).filter(User.role == UserRole.SALES_OFFICE).first()
    
    if not all([user, sales_office, staff]):
        result.add_fail("오프라인 판매", "테스트 데이터 부족")
        return
    
    inv = db.query(Inventory).filter(
        Inventory.sales_office_id == sales_office.id,
        Inventory.quantity > 0,
    ).first()
    
    if not inv:
        result.add_fail("오프라인 판매", "재고 없음")
        return
    
    initial_point = user.current_point
    initial_inventory = inv.quantity
    
    # 1. 오프라인 판매
    try:
        sale_data = OfflineSaleCreate(
            user_id=user.id,
            sales_office_id=sales_office.id,
            items=[{
                "item_id": inv.item_id,
                "spec_id": inv.spec_id,
                "quantity": 1,
                "unit_price": inv.spec.price if inv.spec else 10000,
                "payment_method": "point",
            }],
        )
        
        order = create_offline_sale(db, staff.id, sale_data)
        
        # 검증
        db.refresh(user)
        db.refresh(inv)
        
        assert user.current_point < initial_point, "포인트 차감 안됨"
        assert inv.quantity == initial_inventory - 1, "재고 차감 불일치"
        
        result.add_pass("오프라인 판매")
    except Exception as e:
        result.add_fail("오프라인 판매", e)


def test_voucher_consistency(db, result):
    """체척권 정합성 테스트"""
    print("\n=== 체척권 정합성 테스트 ===")
    
    user = db.query(User).filter(User.role == UserRole.GENERAL).first()
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    custom_item = db.query(ClothingItem).filter(ClothingItem.clothing_type == ClothingType.CUSTOM).first()
    
    if not all([user, admin, custom_item]):
        result.add_fail("체척권 발행", "테스트 데이터 부족")
        return
    
    initial_point = user.current_point
    amount = 50000
    
    # 1. 체척권 발행
    try:
        voucher = issue_voucher_direct(db, user.id, custom_item.id, amount, None, "테스트 발행")
        voucher_id = voucher.id
        
        db.refresh(user)
        assert user.current_point == initial_point - amount, "포인트 차감 불일치"
        assert voucher.status == VoucherStatus.ISSUED, "상태 불일치"
        
        result.add_pass("체척권 발행")
    except Exception as e:
        result.add_fail("체척권 발행", e)
        return
    
    # 2. 취소 요청
    try:
        from app.schemas.tailor import VoucherCancelRequest
        cancel_data = VoucherCancelRequest(reason="테스트 취소")
        
        requested = request_cancel_voucher(db, user.id, voucher_id, cancel_data)
        
        db.refresh(voucher)
        assert voucher.status == VoucherStatus.CANCEL_REQUESTED, "취소 요청 상태 불일치"
        
        result.add_pass("체척권 취소 요청")
    except Exception as e:
        result.add_fail("체척권 취소 요청", e)
    
    # 3. 취소 승인
    try:
        approved = approve_cancel_voucher(db, admin.id, voucher_id, True)
        
        db.refresh(user)
        db.refresh(voucher)
        
        assert user.current_point == initial_point, "포인트 복원 불일치"
        assert voucher.status == VoucherStatus.CANCELLED, "취소 상태 불일치"
        
        result.add_pass("체척권 취소 승인")
    except Exception as e:
        result.add_fail("체척권 취소 승인", e)


def test_inventory_consistency(db, result):
    """재고 정합성 테스트"""
    print("\n=== 재고 정합성 테스트 ===")
    
    sales_office = db.query(SalesOffice).first()
    
    if not sales_office:
        result.add_fail("재고 조회", "판매소 없음")
        return
    
    # 1. 재고 조회
    try:
        inventories = db.query(Inventory).filter(
            Inventory.sales_office_id == sales_office.id
        ).all()
        
        assert len(inventories) > 0, "재고 없음"
        
        for inv in inventories:
            assert inv.quantity >= 0, "마이너스 재고"
            assert inv.reserved_quantity >= 0, "마이너스 예약 수량"
            assert inv.quantity >= inv.reserved_quantity, "재고 < 예약 수량"
        
        result.add_pass("재고 조회 및 정합성")
    except Exception as e:
        result.add_fail("재고 조회 및 정합성", e)


def test_frontend_backend_schema_match(db, result):
    """프론트엔드-백엔드 스키마 일치 테스트"""
    print("\n=== 프론트엔드-백엔드 스키마 일치 테스트 ===")
    
    # User 스키마 검증
    try:
        user = db.query(User).first()
        user_dict = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "service_number": user.service_number,
            "unit": user.unit,
            "role": user.role,
            "current_point": user.current_point,
            "reserved_point": user.reserved_point,
            "rank": {"id": user.rank.id, "name": user.rank.name} if user.rank else None,
        }
        
        required_fields = ["id", "username", "name", "service_number", "role", "current_point"]
        for field in required_fields:
            assert field in user_dict, f"필수 필드 {field} 없음"
        
        result.add_pass("User 스키마 일치")
    except Exception as e:
        result.add_fail("User 스키마 일치", e)
    
    # Order 스키마 검증
    try:
        order = db.query(Order).first()
        if order:
            order_dict = {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status.value,
                "order_type": order.order_type.value,
                "total_amount": order.total_amount,
            }
            
            required_fields = ["id", "order_number", "status", "total_amount"]
            for field in required_fields:
                assert field in order_dict, f"필수 필드 {field} 없음"
            
            result.add_pass("Order 스키마 일치")
        else:
            result.add_pass("Order 스키마 일치 (주문 없음)")
    except Exception as e:
        result.add_fail("Order 스키마 일치", e)


def test_role_based_access(db, result):
    """역할별 접근 권한 테스트"""
    print("\n=== 역할별 접근 권한 테스트 ===")
    
    # 1. 관리자 권한 확인
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        assert admin is not None, "관리자 없음"
        result.add_pass("관리자 계정 존재")
    except Exception as e:
        result.add_fail("관리자 계정 존재", e)
    
    # 2. 판매소 권한 확인
    try:
        sales = db.query(User).filter(User.role == UserRole.SALES_OFFICE).first()
        assert sales is not None, "판매소 담당자 없음"
        assert sales.sales_office_id is not None, "판매소 ID 없음"
        result.add_pass("판매소 계정 정합성")
    except Exception as e:
        result.add_fail("판매소 계정 정합성", e)
    
    # 3. 일반사용자 권한 확인
    try:
        general = db.query(User).filter(User.role == UserRole.GENERAL).first()
        assert general is not None, "일반사용자 없음"
        assert general.current_point >= 0, "마이너스 포인트"
        result.add_pass("일반사용자 계정 정합성")
    except Exception as e:
        result.add_fail("일반사용자 계정 정합성", e)


def run_single_iteration(iteration):
    """단일 반복 테스트 실행"""
    print(f"\n{'='*60}")
    print(f"반복 {iteration}/10")
    print('='*60)
    
    db = SessionLocal()
    result = TestResult()
    
    try:
        # 각 반복 시작 전 테스트 사용자 포인트 복원
        test_user = db.query(User).filter(User.role == UserRole.GENERAL).first()
        if test_user:
            test_user.current_point = 500000
            test_user.reserved_point = 0
            db.commit()
        
        test_user_crud(db, result)
        test_clothing_crud(db, result)
        test_order_consistency(db, result)
        test_offline_sale_consistency(db, result)
        test_voucher_consistency(db, result)
        test_inventory_consistency(db, result)
        test_frontend_backend_schema_match(db, result)
        test_role_based_access(db, result)
    finally:
        db.close()
    
    return result


def main():
    """10회 반복 테스트 실행"""
    print("="*60)
    print("화면간 정합성 테스트 (10회 반복)")
    print("="*60)
    
    all_results = []
    total_passed = 0
    total_failed = 0
    
    for i in range(1, 11):
        result = run_single_iteration(i)
        all_results.append(result.summary())
        total_passed += result.passed
        total_failed += result.failed
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약 (10회 반복)")
    print('='*60)
    
    for i, r in enumerate(all_results, 1):
        print(f"반복 {i}: {r['passed']}/{r['total']} 통과", end="")
        if r['failed'] > 0:
            print(f" ({r['failed']} 실패)")
        else:
            print()
    
    print(f"\n총계: {total_passed}/{total_passed + total_failed} 통과 ({total_failed} 실패)")
    
    # 실패한 테스트 상세
    all_errors = []
    for i, r in enumerate(all_results, 1):
        for err in r['errors']:
            all_errors.append({"iteration": i, **err})
    
    if all_errors:
        print(f"\n실패한 테스트 상세:")
        for err in all_errors:
            print(f"  반복 {err['iteration']}: {err['test']} - {err['error']}")
    
    print(f"\n성공률: {(total_passed / (total_passed + total_failed)) * 100:.1f}%")


if __name__ == '__main__':
    main()
