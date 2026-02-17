"""풍부한 테스트 데이터 생성 스크립트"""
import random
from datetime import datetime, timedelta, date
from app.database import engine, SessionLocal, Base
from app.models import *
from app.utils.auth import get_password_hash

def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("테이블 재생성 완료")

def create_ranks(db):
    ranks_data = [
        (UserRank.GENERAL_OFFICER, "장성급", UserRankGroup.OFFICER, 1000000),
        (UserRank.COLONEL, "대령", UserRankGroup.OFFICER, 800000),
        (UserRank.MAJOR, "소령", UserRankGroup.OFFICER, 800000),
        (UserRank.CAPTAIN, "대위", UserRankGroup.OFFICER, 600000),
        (UserRank.LIEUTENANT, "소위", UserRankGroup.OFFICER, 600000),
        (UserRank.WARRANT_OFFICER, "준위", UserRankGroup.OFFICER, 500000),
        (UserRank.SERGEANT_MAJOR, "상사", UserRankGroup.NCO, 450000),
        (UserRank.SERGEANT, "중사", UserRankGroup.NCO, 400000),
        (UserRank.CORPORAL, "하사", UserRankGroup.NCO, 350000),
        (UserRank.CIVILIAN, "군무원", UserRankGroup.CIVILIAN, 400000),
    ]
    ranks = {}
    for code, name, group, point in ranks_data:
        rank = Rank(name=name, code=code, rank_group=group, annual_point=point)
        db.add(rank)
        ranks[code] = rank
    db.flush()
    return ranks

def create_sales_offices(db):
    offices_data = [
        ("SO001", "중앙피복판매소", "서울특별시 용산구 한강로 1길", "02-1234-5678", "박판매"),
        ("SO002", "부산피복판매소", "부산광역시 해운대구 좌동순환로", "051-9876-5432", "김부산"),
        ("SO003", "대전피복판매소", "대전광역시 유성구 대학로", "042-5555-1234", "이대전"),
    ]
    offices = []
    for code, name, address, phone, manager in offices_data:
        office = SalesOffice(
            name=name, code=code, address=address, 
            phone=phone, manager_name=manager, is_active=True
        )
        db.add(office)
        offices.append(office)
    db.flush()
    return offices

def create_tailor_companies(db):
    companies_data = [
        ("TC001", "군복맞춤센터", "123-45-67890", "서울특별시 용산구 청파로", "02-1111-2222", "김체척"),
        ("TC002", "프리미엄맞춤", "987-65-43210", "서울특별시 강남구 테헤란로", "02-3333-4444", "박프리"),
    ]
    companies = []
    for code, name, biz, address, phone, manager in companies_data:
        company = TailorCompany(
            name=name, code=code, business_number=biz,
            address=address, phone=phone, manager_name=manager, is_active=True
        )
        db.add(company)
        companies.append(company)
    db.flush()
    return companies

def create_users(db, ranks, offices, companies):
    users = []
    
    admin = User(
        username="admin", password_hash=get_password_hash("admin123"),
        name="군수담당자", role=UserRole.ADMIN,
        rank_id=ranks[UserRank.COLONEL].id, service_number="20-123456",
        enlistment_date=date(2010, 3, 1),
        retirement_date=date(2030, 3, 1),
        current_point=1000000, reserved_point=0, is_active=True
    )
    db.add(admin)
    users.append(admin)
    
    today = date.today()
    
    sales_users = []
    for i, office in enumerate(offices):
        years = 5 + i
        enlistment_date = date(today.year - years, 1, 1)
        sales_user = User(
            username=f"sales{i+1}", password_hash=get_password_hash("sales123"),
            name=f"{office.name[:2]}판매담당", role=UserRole.SALES_OFFICE,
            rank_id=ranks[UserRank.SERGEANT].id, service_number=f"30-10000{i+1}",
            sales_office_id=office.id,
            enlistment_date=enlistment_date,
            retirement_date=date(enlistment_date.year + 20, 1, 1),
            current_point=400000, reserved_point=0, is_active=True
        )
        db.add(sales_user)
        sales_users.append(sales_user)
        users.append(sales_user)
    
    for i, company in enumerate(companies):
        years = 3 + i
        enlistment_date = date(today.year - years, 6, 1)
        tailor_user = User(
            username=f"tailor{i+1}", password_hash=get_password_hash("tailor123"),
            name=f"{company.name[:2]}담당", role=UserRole.TAILOR_COMPANY,
            rank_id=ranks[UserRank.SERGEANT].id, service_number=f"40-20000{i+1}",
            tailor_company_id=company.id,
            enlistment_date=enlistment_date,
            retirement_date=date(enlistment_date.year + 20, 6, 1),
            current_point=0, reserved_point=0, is_active=True
        )
        db.add(tailor_user)
        users.append(tailor_user)
    
    general_users_data = [
        ("user01", "김민수", UserRank.CAPTAIN, "21-100001", 3, "1보병사단"),
        ("user02", "이영호", UserRank.MAJOR, "15-100002", 8, "2보병사단"),
        ("user03", "박정호", UserRank.COLONEL, "08-100003", 15, "3보병사단"),
        ("user04", "최성우", UserRank.SERGEANT_MAJOR, "12-100004", 12, "기계화보병사단"),
        ("user05", "정현준", UserRank.WARRANT_OFFICER, "05-100005", 20, "특전사"),
        ("user06", "강동원", UserRank.CIVILIAN, "21-100006", 5, "국방부"),
        ("user07", "윤준혁", UserRank.LIEUTENANT, "25-100007", 1, "포병여단"),
        ("user08", "장태현", UserRank.SERGEANT, "18-100008", 7, "공병단"),
        ("user09", "임성민", UserRank.CAPTAIN, "22-100009", 4, "통신여단"),
        ("user10", "한지훈", UserRank.SERGEANT_MAJOR, "10-100010", 15, "방공포병여단"),
    ]
    
    for username, name, rank_code, service_number, years, unit in general_users_data:
        rank = ranks[rank_code]
        base_point = rank.annual_point
        bonus = years * 5000
        total_point = base_point + bonus
        reserved = random.randint(0, total_point // 5)
        
        enlistment_date = date(today.year - years, random.randint(1, 12), random.randint(1, 28))
        retirement_date = date(enlistment_date.year + 20, enlistment_date.month, enlistment_date.day)
        
        user = User(
            username=username, password_hash=get_password_hash("user123"),
            name=name, role=UserRole.GENERAL,
            rank_id=rank.id, service_number=service_number, unit=unit,
            enlistment_date=enlistment_date,
            retirement_date=retirement_date,
            current_point=total_point, reserved_point=reserved, is_active=True
        )
        db.add(user)
        users.append(user)
    
    db.flush()
    
    for user in users:
        if user.role == UserRole.GENERAL and user.current_point > 0:
            grant_tx = PointTransaction(
                user_id=user.id,
                transaction_type=TransactionType.GRANT,
                amount=user.current_point,
                balance_after=user.current_point,
                reserved_after=user.reserved_point,
                description=f"2026년 연간 포인트 지급"
            )
            db.add(grant_tx)
            
            if user.reserved_point > 0:
                reserve_tx = PointTransaction(
                    user_id=user.id,
                    transaction_type=TransactionType.RESERVE,
                    amount=user.reserved_point,
                    balance_after=user.current_point,
                    reserved_after=user.reserved_point,
                    description="주문 포인트 예약"
                )
                db.add(reserve_tx)
    
    db.flush()
    return users, sales_users

def create_categories_and_items(db):
    categories = {}
    
    ready_made_categories = {
        "완제품": {
            "상의": ["전투복상의", "정복상의", "야상"],
            "하의": ["전투복하의", "정복하의"],
            "외투": ["파카", "방한복"],
        }
    }
    
    tailor_made_categories = {
        "맞춤피복": {
            "정복": ["정복상의맞춤", "정복하의맞춤"],
            "군복": ["전투복맞춤", "야상맞춤"],
        }
    }
    
    accessory_categories = {
        "피복부품": {
            "모자": ["전투모", "정모"],
            "신발": ["전투화", "구두"],
            "잡화": ["벨트", "장갑", "양말"],
        }
    }
    
    items = []
    item_id = 1
    
    def add_category(name, level, parent_id=None):
        cat = Category(name=name, level=level, parent_id=parent_id, is_active=True)
        db.add(cat)
        db.flush()
        return cat
    
    for large_name, medium_dict in ready_made_categories.items():
        large_cat = add_category(large_name, CategoryLevel.LARGE)
        categories[large_name] = large_cat
        
        for medium_name, small_list in medium_dict.items():
            medium_cat = add_category(medium_name, CategoryLevel.MEDIUM, large_cat.id)
            
            for small_name in small_list:
                small_cat = add_category(small_name, CategoryLevel.SMALL, medium_cat.id)
                
                base_price = random.randint(15, 80) * 1000
                item = ClothingItem(
                    name=f"{small_name}",
                    category_id=small_cat.id,
                    clothing_type=ClothingType.READY_MADE,
                    description=f"{small_name} - 품질 좋은 군용 피복",
                    is_active=True
                )
                db.add(item)
                db.flush()
                items.append({
                    'item': item,
                    'type': 'ready',
                    'base_price': base_price,
                    'category': small_name
                })
    
    for large_name, medium_dict in tailor_made_categories.items():
        large_cat = add_category(large_name, CategoryLevel.LARGE)
        categories[large_name] = large_cat
        
        for medium_name, small_list in medium_dict.items():
            medium_cat = add_category(medium_name, CategoryLevel.MEDIUM, large_cat.id)
            
            for small_name in small_list:
                small_cat = add_category(small_name, CategoryLevel.SMALL, medium_cat.id)
                
                base_price = random.randint(100, 300) * 1000
                item = ClothingItem(
                    name=f"{small_name}",
                    category_id=small_cat.id,
                    clothing_type=ClothingType.CUSTOM,
                    description=f"{small_name} - 맞춤 제작",
                    is_active=True
                )
                db.add(item)
                db.flush()
                items.append({
                    'item': item,
                    'type': 'tailor',
                    'base_price': base_price,
                    'category': small_name
                })
    
    for large_name, medium_dict in accessory_categories.items():
        large_cat = add_category(large_name, CategoryLevel.LARGE)
        categories[large_name] = large_cat
        
        for medium_name, small_list in medium_dict.items():
            medium_cat = add_category(medium_name, CategoryLevel.MEDIUM, large_cat.id)
            
            for small_name in small_list:
                small_cat = add_category(small_name, CategoryLevel.SMALL, medium_cat.id)
                
                base_price = random.randint(5, 30) * 1000
                item = ClothingItem(
                    name=f"{small_name}",
                    category_id=small_cat.id,
                    clothing_type=ClothingType.READY_MADE,
                    description=f"{small_name} - 군용 피복 부품",
                    is_active=True
                )
                db.add(item)
                db.flush()
                items.append({
                    'item': item,
                    'type': 'ready',
                    'base_price': base_price,
                    'category': medium_name
                })
    
    return items

def create_specs_and_inventory(db, items, offices):
    sizes = ["85", "90", "95", "100", "105", "110"]
    shoe_sizes = ["230", "240", "250", "260", "270", "280", "290"]
    
    all_specs = []
    inventories = []
    
    for item_data in items:
        item = item_data['item']
        base_price = item_data['base_price']
        
        if item_data['type'] == 'ready':
            if '신발' in item_data['category'] or '전투화' in item.name:
                size_list = shoe_sizes
            else:
                size_list = sizes
            
            for i, size in enumerate(size_list):
                price = base_price + (i * 2000)
                spec = ClothingSpec(
                    item_id=item.id,
                    spec_code=size,
                    size=size,
                    price=price,
                    is_active=True
                )
                db.add(spec)
                db.flush()
                all_specs.append({
                    'spec': spec,
                    'item': item,
                    'item_data': item_data
                })
                
                for office in offices:
                    qty = random.randint(20, 150)
                    inv = Inventory(
                        sales_office_id=office.id,
                        item_id=item.id,
                        spec_id=spec.id,
                        quantity=qty,
                        reserved_quantity=random.randint(0, qty // 4)
                    )
                    db.add(inv)
                    inventories.append(inv)
        else:
            spec = ClothingSpec(
                item_id=item.id,
                spec_code="CUSTOM",
                size="맞춤",
                price=base_price,
                is_active=True
            )
            db.add(spec)
            db.flush()
            all_specs.append({
                'spec': spec,
                'item': item,
                'item_data': item_data
            })
    
    db.flush()
    return all_specs, inventories

def create_orders_and_transactions(db, users, specs, offices, ranks):
    general_users = [u for u in users if u.role == UserRole.GENERAL]
    ready_specs = [s for s in specs if s['item_data']['type'] == 'ready']
    tailor_specs = [s for s in specs if s['item_data']['type'] == 'tailor']
    
    orders = []
    order_items = []
    point_transactions = []
    tailor_vouchers = []
    
    for _ in range(30):
        user = random.choice(general_users)
        office = random.choice(offices)
        
        if user.available_point < 50000:
            continue
        
        order_type = random.choice([OrderType.ONLINE, OrderType.OFFLINE])
        status = random.choice([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.DELIVERED, OrderStatus.CANCELLED])
        
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        
        total_amount = 0
        reserved_point = 0
        
        order = Order(
            order_number=order_number,
            user_id=user.id,
            sales_office_id=office.id,
            order_type=order_type,
            status=status,
            total_amount=0,
            reserved_point=0,
            used_point=0,
            ordered_at=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        db.add(order)
        db.flush()
        
        num_items = random.randint(1, 3)
        available_specs = [s for s in ready_specs if s['spec'].price <= user.available_point]
        
        if not available_specs:
            db.delete(order)
            continue
        
        for _ in range(min(num_items, len(available_specs))):
            spec_data = random.choice(available_specs)
            spec = spec_data['spec']
            item = spec_data['item']
            
            qty = random.randint(1, 2)
            unit_price = spec.price
            item_total = unit_price * qty
            
            if total_amount + item_total > user.available_point:
                continue
            
            order_item = OrderItem(
                order_id=order.id,
                item_id=item.id,
                spec_id=spec.id,
                quantity=qty,
                unit_price=unit_price,
                total_price=item_total,
                payment_method=PaymentMethod.POINT
            )
            db.add(order_item)
            db.flush()
            order_items.append(order_item)
            total_amount += item_total
        
        if total_amount == 0:
            db.delete(order)
            continue
        
        order.total_amount = total_amount
        
        if order_type == OrderType.ONLINE and status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            order.reserved_point = total_amount
            reserved_point = total_amount
        
        if status == OrderStatus.DELIVERED:
            order.used_point = total_amount
        
        orders.append(order)
    
    for _ in range(10):
        user = random.choice(general_users)
        
        if user.available_point < 100000:
            continue
        
        office = random.choice(offices)
        spec_data = random.choice(tailor_specs)
        spec = spec_data['spec']
        item = spec_data['item']
        
        order_number = f"TRD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        
        order = Order(
            order_number=order_number,
            user_id=user.id,
            sales_office_id=office.id,
            order_type=OrderType.ONLINE,
            status=OrderStatus.PENDING,
            total_amount=spec.price,
            reserved_point=spec.price,
            ordered_at=datetime.now() - timedelta(days=random.randint(0, 10))
        )
        db.add(order)
        db.flush()
        
        order_item = OrderItem(
            order_id=order.id,
            item_id=item.id,
            spec_id=spec.id,
            quantity=1,
            unit_price=spec.price,
            total_price=spec.price,
            payment_method=PaymentMethod.VOUCHER
        )
        db.add(order_item)
        db.flush()
        
        voucher_number = f"VCH{datetime.now().strftime('%Y%m%d')}{random.randint(10000, 99999)}"
        voucher = TailorVoucher(
            voucher_number=voucher_number,
            user_id=user.id,
            order_id=order.id,
            order_item_id=order_item.id,
            item_id=item.id,
            amount=spec.price,
            status=VoucherStatus.ISSUED,
            issued_at=datetime.now()
        )
        db.add(voucher)
        db.flush()
        tailor_vouchers.append(voucher)
    
    db.flush()
    return orders, order_items, tailor_vouchers

def create_delivery_locations(db, offices):
    locations = []
    loc_data = [
        ("본부중대", "서울 용산구 본부중대", "김중대장", "02-1111-0001"),
        ("1대대", "서울 용산구 1대대", "이대대장", "02-1111-0002"),
        ("2대대", "서울 용산구 2대대", "박대대장", "02-1111-0003"),
        ("지원대", "서울 용산구 지원대", "최지원장", "02-1111-0004"),
    ]
    
    for office in offices:
        for name, addr, person, phone in loc_data:
            loc = DeliveryLocation(
                sales_office_id=office.id,
                name=f"{office.name[:2]}{name}",
                address=addr,
                contact_person=person,
                contact_phone=phone,
                is_active=True
            )
            db.add(loc)
            locations.append(loc)
    
    db.flush()
    return locations

def seed_data():
    db = SessionLocal()
    try:
        print("계급 생성 중...")
        ranks = create_ranks(db)
        
        print("피복판매소 생성 중...")
        offices = create_sales_offices(db)
        
        print("체척업체 생성 중...")
        companies = create_tailor_companies(db)
        
        print("사용자 생성 중...")
        users, sales_users = create_users(db, ranks, offices, companies)
        
        print("카테고리 및 품목 생성 중...")
        items = create_categories_and_items(db)
        
        print("규격 및 재고 생성 중...")
        specs, inventories = create_specs_and_inventory(db, items, offices)
        
        print("배송지 생성 중...")
        locations = create_delivery_locations(db, offices)
        
        print("주문 및 거래내역 생성 중...")
        orders, order_items, vouchers = create_orders_and_transactions(db, users, specs, offices, ranks)
        
        db.commit()
        
        print("\n" + "="*50)
        print("테스트 데이터 생성 완료!")
        print("="*50)
        print(f"- 계급: {len(ranks)}개")
        print(f"- 피복판매소: {len(offices)}개")
        print(f"- 체척업체: {len(companies)}개")
        print(f"- 사용자: {len(users)}명")
        print(f"- 품목: {len(items)}개")
        print(f"- 규격: {len(specs)}개")
        print(f"- 재고: {len(inventories)}건")
        print(f"- 주문: {len(orders)}건")
        print(f"- 체척권: {len(vouchers)}건")
        print(f"- 배송지: {len(locations)}개")
        print("\n테스트 계정:")
        print("  - admin / admin123 (군수담당자)")
        print("  - sales1 / sales123 (피복판매소)")
        print("  - tailor1 / tailor123 (체척업체)")
        print("  - user01 / user123 ~ user10 / user123 (일반사용자)")
        
    except Exception as e:
        db.rollback()
        print(f"시드 데이터 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_data()
