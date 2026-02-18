"""데이터베이스 초기화 및 시드 데이터"""
from app.database import engine, SessionLocal, Base
from app.models import *
from app.utils.auth import get_password_hash
from app.services.menu_service import MenuService

def init_db():
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료")
    
    # 기본 메뉴 초기화
    db = SessionLocal()
    try:
        menu_service = MenuService(db)
        menu_service.initialize_default_menus()
        print("기본 메뉴 초기화 완료")
    except Exception as e:
        print(f"메뉴 초기화 실패: {e}")
    finally:
        db.close()

def seed_data():
    db = SessionLocal()
    try:
        if db.query(User).first():
            print("시드 데이터가 이미 존재합니다")
            return

        ranks_data = [
            (UserRank.GENERAL_OFFICER, "장성급", UserRankGroup.OFFICER, 1000000),
            (UserRank.COLONEL, "대령", UserRankGroup.OFFICER, 800000),
            (UserRank.MAJOR, "소령", UserRankGroup.OFFICER, 800000),
            (UserRank.CAPTAIN, "대위", UserRankGroup.OFFICER, 600000),
            (UserRank.LIEUTENANT, "소위", UserRankGroup.OFFICER, 600000),
            (UserRank.WARRANT_OFFICER, "준위", UserRankGroup.OFFICER, 500000),
            (UserRank.NCO, "부사관", UserRankGroup.NCO, 400000),
            (UserRank.CIVILIAN, "군무원", UserRankGroup.CIVILIAN, 400000),
        ]
        ranks = {}
        for code, name, group, point in ranks_data:
            rank = Rank(name=name, code=code, rank_group=group, annual_point=point)
            db.add(rank)
            ranks[code] = rank
        db.flush()

        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            name="군수담당자",
            role=UserRole.ADMIN,
            rank_id=ranks[UserRank.COLONEL].id,
            service_years=10,
            current_point=1000000,
            reserved_point=0
        )
        db.add(admin)

        sales_office = SalesOffice(
            name="중앙피복판매소",
            code="SO001",
            address="서울특별시 용산구",
            phone="02-1234-5678",
            manager_name="판매소장",
            is_active=True
        )
        db.add(sales_office)
        db.flush()

        sales_user = User(
            username="sales",
            password_hash=get_password_hash("sales123"),
            name="판매소담당자",
            role=UserRole.SALES_OFFICE,
            rank_id=ranks[UserRank.NCO].id,
            sales_office_id=sales_office.id,
            service_years=5,
            current_point=400000,
            reserved_point=0
        )
        db.add(sales_user)

        tailor_company = TailorCompany(
            name="군복맞춤센터",
            code="TC001",
            business_number="123-45-67890",
            address="서울특별시 용산구",
            phone="02-9876-5432",
            manager_name="김체척",
            is_active=True
        )
        db.add(tailor_company)
        db.flush()

        tailor_user = User(
            username="tailor",
            password_hash=get_password_hash("tailor123"),
            name="체척업체담당자",
            role=UserRole.TAILOR_COMPANY,
            rank_id=ranks[UserRank.NCO].id,
            tailor_company_id=tailor_company.id,
            service_years=3,
            current_point=0,
            reserved_point=0
        )
        db.add(tailor_user)

        normal_user = User(
            username="user",
            password_hash=get_password_hash("user123"),
            name="일반사용자",
            role=UserRole.GENERAL,
            rank_id=ranks[UserRank.CAPTAIN].id,
            service_years=2,
            current_point=610000,
            reserved_point=0
        )
        db.add(normal_user)

        cat1 = Category(name="완제품", level=CategoryLevel.LARGE, parent_id=None)
        db.add(cat1)
        db.flush()

        cat2 = Category(name="상의", level=CategoryLevel.MEDIUM, parent_id=cat1.id)
        db.add(cat2)
        db.flush()

        cat3 = Category(name="전투복", level=CategoryLevel.SMALL, parent_id=cat2.id)
        db.add(cat3)
        db.flush()

        clothing = ClothingItem(
            name="전투복 상의",
            category_id=cat3.id,
            clothing_type=ClothingType.READY_MADE,
            image_url=None,
            is_active=True
        )
        db.add(clothing)
        db.flush()

        spec1 = ClothingSpec(
            item_id=clothing.id,
            spec_code="90",
            size="90",
            price=50000
        )
        spec2 = ClothingSpec(
            item_id=clothing.id,
            spec_code="95",
            size="95",
            price=50000
        )
        spec3 = ClothingSpec(
            item_id=clothing.id,
            spec_code="100",
            size="100",
            price=53000
        )
        db.add_all([spec1, spec2, spec3])
        db.flush()

        inv1 = Inventory(
            sales_office_id=sales_office.id,
            item_id=clothing.id,
            spec_id=spec1.id,
            quantity=100
        )
        inv2 = Inventory(
            sales_office_id=sales_office.id,
            item_id=clothing.id,
            spec_id=spec2.id,
            quantity=100
        )
        inv3 = Inventory(
            sales_office_id=sales_office.id,
            item_id=clothing.id,
            spec_id=spec3.id,
            quantity=50
        )
        db.add_all([inv1, inv2, inv3])

        cat4 = Category(name="맞춤피복", level=CategoryLevel.LARGE, parent_id=None)
        db.add(cat4)
        db.flush()

        cat5 = Category(name="정복", level=CategoryLevel.MEDIUM, parent_id=cat4.id)
        db.add(cat5)
        db.flush()

        tailor_clothing = ClothingItem(
            name="정복 상의",
            category_id=cat5.id,
            clothing_type=ClothingType.CUSTOM,
            image_url=None,
            is_active=True
        )
        db.add(tailor_clothing)

        delivery_loc = DeliveryLocation(
            sales_office_id=sales_office.id,
            name="본부중대",
            address="서울특별시 용산구 본부중대",
            contact_person="중대장",
            contact_phone="02-1111-2222"
        )
        db.add(delivery_loc)

        db.commit()
        print("시드 데이터 생성 완료")
        print("\n테스트 계정:")
        print("  - admin / admin123 (군수담당자)")
        print("  - sales / sales123 (피복판매소)")
        print("  - tailor / tailor123 (체척업체)")
        print("  - user / user123 (일반사용자)")

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
