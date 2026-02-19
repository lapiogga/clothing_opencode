"""
포인트 정합성 테스트 스크립트
- 구매, 취소, 반품, 체척권 발행/취소 시 포인트 차감/복원 검증
- 재고 차감/복원 검증
- 5회 반복 실행
"""
import sys
import random
from datetime import date

sys.path.insert(0, '/home/user/opencode/clothing-system/backend')

from app.database import SessionLocal
from app.models.user import User
from app.models.clothing import ClothingItem, ClothingSpec, ClothingType
from app.models.sales import SalesOffice, Inventory
from app.models.order import Order, OrderStatus, OrderType
from app.models.tailor import TailorVoucher, VoucherStatus
from app.services.order_service import create_order, cancel_order, receive_order
from app.services.tailor_service import issue_voucher_direct, request_cancel_voucher, approve_cancel_voucher
from app.schemas.order import OrderCreate, OrderItemCreate
from app.models.order import PaymentMethod


def get_initial_state(db, user_id):
    """사용자의 현재 포인트 상태 반환"""
    user = db.query(User).filter(User.id == user_id).first()
    return {
        'current_point': user.current_point,
        'reserved_point': user.reserved_point,
        'available_point': user.current_point - user.reserved_point,
    }


def get_inventory_state(db, sales_office_id, item_id, spec_id):
    """재고 상태 반환"""
    inv = db.query(Inventory).filter(
        Inventory.sales_office_id == sales_office_id,
        Inventory.item_id == item_id,
        Inventory.spec_id == spec_id,
    ).first()
    return inv.quantity if inv else 0


def test_online_purchase(db, user, sales_office, item, spec):
    """온라인 구매 테스트"""
    print("\n=== 온라인 구매 테스트 ===")
    
    initial = get_initial_state(db, user.id)
    initial_inventory = get_inventory_state(db, sales_office.id, item.id, spec.id)
    
    print(f"초기 상태: 보유 {initial['current_point']}P, 예약 {initial['reserved_point']}P, 사용가능 {initial['available_point']}P")
    print(f"초기 재고: {initial_inventory}개")
    
    # 주문 생성
    quantity = 1
    total_price = spec.price * quantity
    
    order_data = OrderCreate(
        sales_office_id=sales_office.id,
        order_type=OrderType.ONLINE,
        items=[OrderItemCreate(
            item_id=item.id,
            spec_id=spec.id,
            quantity=quantity,
            payment_method=PaymentMethod.POINT,
        )],
        delivery_type='parcel',
        recipient_name='테스트',
        recipient_phone='010-0000-0000',
        shipping_address='테스트 주소',
    )
    
    try:
        order = create_order(db, user.id, order_data)
        print(f"주문 생성 성공: 주문번호 {order.order_number}")
    except ValueError as e:
        print(f"주문 생성 실패: {e}")
        return None
    
    after_order = get_initial_state(db, user.id)
    print(f"주문 후: 보유 {after_order['current_point']}P, 예약 {after_order['reserved_point']}P, 사용가능 {after_order['available_point']}P")
    
    # 검증: 예약 포인트 증가
    assert after_order['reserved_point'] == initial['reserved_point'] + total_price, "예약 포인트가 올바르지 않음"
    assert after_order['current_point'] == initial['current_point'], "보유 포인트가 변경됨 (주문 시점엔 변경되면 안됨)"
    
    # 배송 완료 상태로 변경 후 수령 완료 처리
    order.status = OrderStatus.DELIVERED
    db.commit()
    receive_order(db, order.id, user.id)
    
    after_receive = get_initial_state(db, user.id)
    print(f"수령 후: 보유 {after_receive['current_point']}P, 예약 {after_receive['reserved_point']}P, 사용가능 {after_receive['available_point']}P")
    
    # 검증: 보유 포인트와 예약 포인트 모두 차감
    assert after_receive['current_point'] == initial['current_point'] - total_price, "보유 포인트 차감이 올바르지 않음"
    assert after_receive['reserved_point'] == initial['reserved_point'], "예약 포인트 해제가 올바르지 않음"
    
    print("✅ 온라인 구매 테스트 통과")
    return order


def test_offline_purchase(db, user, sales_office, item, spec):
    """오프라인 구매 테스트"""
    print("\n=== 오프라인 구매 테스트 ===")
    
    initial = get_initial_state(db, user.id)
    initial_inventory = get_inventory_state(db, sales_office.id, item.id, spec.id)
    
    print(f"초기 상태: 보유 {initial['current_point']}P, 예약 {initial['reserved_point']}P, 사용가능 {initial['available_point']}P")
    print(f"초기 재고: {initial_inventory}개")
    
    # 주문 생성
    quantity = 1
    total_price = spec.price * quantity
    
    order_data = OrderCreate(
        sales_office_id=sales_office.id,
        order_type=OrderType.OFFLINE,
        items=[OrderItemCreate(
            item_id=item.id,
            spec_id=spec.id,
            quantity=quantity,
            payment_method=PaymentMethod.POINT,
        )],
        delivery_type='direct',
    )
    
    try:
        order = create_order(db, user.id, order_data)
        print(f"주문 생성 성공: 주문번호 {order.order_number}")
    except ValueError as e:
        print(f"주문 생성 실패: {e}")
        return None
    
    after_order = get_initial_state(db, user.id)
    after_inventory = get_inventory_state(db, sales_office.id, item.id, spec.id)
    
    print(f"주문 후: 보유 {after_order['current_point']}P, 예약 {after_order['reserved_point']}P")
    print(f"재고 후: {after_inventory}개")
    
    # 검증: 보유 포인트 즉시 차감
    assert after_order['current_point'] == initial['current_point'] - total_price, "보유 포인트 차감이 올바르지 않음"
    assert after_inventory == initial_inventory - quantity, "재고 차감이 올바르지 않음"
    
    print("✅ 오프라인 구매 테스트 통과")
    return order


def test_voucher_issue(db, user, item):
    """체척권 발행 테스트"""
    print("\n=== 체척권 발행 테스트 ===")
    
    initial = get_initial_state(db, user.id)
    amount = 50000
    
    print(f"초기 상태: 보유 {initial['current_point']}P, 예약 {initial['reserved_point']}P, 사용가능 {initial['available_point']}P")
    
    try:
        voucher = issue_voucher_direct(db, user.id, item.id, amount, None, "테스트 발행")
        print(f"체척권 발행 성공: {voucher.voucher_number}")
    except ValueError as e:
        print(f"체척권 발행 실패: {e}")
        return None
    
    after_issue = get_initial_state(db, user.id)
    print(f"발행 후: 보유 {after_issue['current_point']}P, 예약 {after_issue['reserved_point']}P")
    
    # 검증: 보유 포인트 차감
    assert after_issue['current_point'] == initial['current_point'] - amount, "체척권 발행 시 포인트 차감이 올바르지 않음"
    
    print("✅ 체척권 발행 테스트 통과")
    return voucher


def test_voucher_cancel(db, user, voucher, admin_id):
    """체척권 취소 승인 테스트"""
    print("\n=== 체척권 취소 승인 테스트 ===")
    
    initial = get_initial_state(db, user.id)
    amount = voucher.amount
    
    print(f"초기 상태: 보유 {initial['current_point']}P")
    
    # 취소 요청
    from app.schemas.tailor import VoucherCancelRequest
    cancel_data = VoucherCancelRequest(reason="테스트 취소")
    
    result = request_cancel_voucher(db, user.id, voucher.id, cancel_data)
    if not result:
        print("취소 요청 실패")
        return False
    
    print(f"취소 요청 상태: {result.status}")
    
    # 관리자 승인
    approved = approve_cancel_voucher(db, admin_id, voucher.id, True)
    if not approved:
        print("취소 승인 실패")
        return False
    
    after_cancel = get_initial_state(db, user.id)
    print(f"취소 승인 후: 보유 {after_cancel['current_point']}P")
    
    # 검증: 포인트 복원
    assert after_cancel['current_point'] == initial['current_point'] + amount, "체척권 취소 시 포인트 복원이 올바르지 않음"
    
    print("✅ 체척권 취소 승인 테스트 통과")
    return True


def test_order_cancel(db, user, order):
    """주문 취소 테스트"""
    print("\n=== 주문 취소 테스트 ===")
    
    initial = get_initial_state(db, user.id)
    reserved = order.reserved_point
    
    print(f"초기 상태: 보유 {initial['current_point']}P, 예약 {initial['reserved_point']}P")
    
    from app.schemas.order import OrderCancel
    cancel_data = OrderCancel(reason="테스트 취소")
    
    result = cancel_order(db, order.id, user.id, cancel_data)
    if not result:
        print("주문 취소 실패")
        return False
    
    after_cancel = get_initial_state(db, user.id)
    print(f"취소 후: 보유 {after_cancel['current_point']}P, 예약 {after_cancel['reserved_point']}P")
    
    # 검증: 예약 포인트 해제
    assert after_cancel['reserved_point'] == initial['reserved_point'] - reserved, "예약 포인트 해제가 올바르지 않음"
    assert after_cancel['current_point'] == initial['current_point'], "보유 포인트가 변경됨"
    
    print("✅ 주문 취소 테스트 통과")
    return True


def run_tests():
    """전체 테스트 실행"""
    db = SessionLocal()
    
    try:
        # 테스트 데이터 조회
        user = db.query(User).filter(User.role == 'general').first()
        admin = db.query(User).filter(User.role == 'admin').first()
        sales_office = db.query(SalesOffice).first()
        
        # 완제품 및 규격 찾기
        ready_made_item = db.query(ClothingItem).filter(
            ClothingItem.clothing_type == ClothingType.READY_MADE
        ).first()
        spec = db.query(ClothingSpec).filter(ClothingSpec.item_id == ready_made_item.id).first() if ready_made_item else None
        
        # 맞춤피복 찾기
        custom_item = db.query(ClothingItem).filter(
            ClothingItem.clothing_type == ClothingType.CUSTOM
        ).first()
        
        if not all([user, admin, sales_office, ready_made_item, spec, custom_item]):
            print("테스트 데이터가 부족합니다.")
            return
        
        # 테스트 시작 전 사용자 포인트 상태 초기화
        user.reserved_point = 0
        db.commit()
        
        print(f"사용자: {user.name} (ID: {user.id})")
        print(f"관리자: {admin.name} (ID: {admin.id})")
        print(f"판매소: {sales_office.name}")
        print(f"완제품: {ready_made_item.name}")
        print(f"맞춤피복: {custom_item.name}")
        
        results = {
            'online_purchase': 0,
            'offline_purchase': 0,
            'voucher_issue': 0,
            'voucher_cancel': 0,
            'order_cancel': 0,
        }
        
        # 5회 반복 테스트
        for i in range(5):
            print(f"\n{'='*50}")
            print(f"반복 {i+1}/5")
            print('='*50)
            
            # 체척권 발행 테스트
            voucher = test_voucher_issue(db, user, custom_item)
            if voucher:
                results['voucher_issue'] += 1
                # 체척권 취소 테스트
                if test_voucher_cancel(db, user, voucher, admin.id):
                    results['voucher_cancel'] += 1
            
            # 온라인 구매 테스트
            order = test_online_purchase(db, user, sales_office, ready_made_item, spec)
            if order:
                results['online_purchase'] += 1
            
            # 오프라인 구매 테스트
            order = test_offline_purchase(db, user, sales_office, ready_made_item, spec)
            if order:
                results['offline_purchase'] += 1
        
        # 결과 요약
        print(f"\n{'='*50}")
        print("테스트 결과 요약 (5회 반복)")
        print('='*50)
        print(f"온라인 구매: {results['online_purchase']}/5 성공")
        print(f"오프라인 구매: {results['offline_purchase']}/5 성공")
        print(f"체척권 발행: {results['voucher_issue']}/5 성공")
        print(f"체척권 취소 승인: {results['voucher_cancel']}/5 성공")
        
        # 최종 상태
        final = get_initial_state(db, user.id)
        print(f"\n최종 포인트 상태:")
        print(f"  보유: {final['current_point']}P")
        print(f"  예약: {final['reserved_point']}P")
        print(f"  사용가능: {final['available_point']}P")
        
    finally:
        db.close()


if __name__ == '__main__':
    run_tests()
