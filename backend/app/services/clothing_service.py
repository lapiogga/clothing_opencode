from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.models.clothing import Category, ClothingItem, ClothingSpec, CategoryLevel, ClothingType
from app.schemas.clothing import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeResponse,
    ClothingCreate, ClothingUpdate, ClothingResponse, ClothingDetailResponse,
    SpecCreate, SpecUpdate, SpecResponse, ClothingListResponse,
)


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_list(self, level: Optional[CategoryLevel] = None, parent_id: Optional[int] = None) -> List[Category]:
        query = self.db.query(Category).filter(Category.is_active == True)
        if level:
            query = query.filter(Category.level == level)
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        return query.order_by(Category.sort_order, Category.name).all()

    def get_tree(self) -> List[CategoryTreeResponse]:
        large_categories = (
            self.db.query(Category)
            .filter(Category.level == CategoryLevel.LARGE, Category.is_active == True)
            .order_by(Category.sort_order)
            .all()
        )
        return [self._build_tree(cat) for cat in large_categories]

    def _build_tree(self, category: Category) -> CategoryTreeResponse:
        children = (
            self.db.query(Category)
            .filter(Category.parent_id == category.id, Category.is_active == True)
            .order_by(Category.sort_order)
            .all()
        )
        return CategoryTreeResponse(
            id=category.id,
            name=category.name,
            level=category.level,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            created_at=category.created_at,
            children=[self._build_tree(child) for child in children],
        )

    def create(self, data: CategoryCreate) -> Category:
        if data.parent_id:
            parent = self.get_by_id(data.parent_id)
            if not parent:
                raise ValueError("상위 카테고리를 찾을 수 없습니다")
            if parent.level == CategoryLevel.SMALL:
                raise ValueError("소분류 하위에 카테고리를 생성할 수 없습니다")

        category = Category(
            name=data.name,
            level=data.level,
            parent_id=data.parent_id,
            sort_order=data.sort_order,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("카테고리를 찾을 수 없습니다")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category_id: int) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False

        has_children = self.db.query(Category).filter(Category.parent_id == category_id).first()
        if has_children:
            raise ValueError("하위 카테고리가 있어 삭제할 수 없습니다")

        has_items = self.db.query(ClothingItem).filter(ClothingItem.category_id == category_id).first()
        if has_items:
            raise ValueError("품목이 등록된 카테고리는 삭제할 수 없습니다")

        self.db.delete(category)
        self.db.commit()
        return True

    def export_to_excel(self) -> StreamingResponse:
        from xlwt import Workbook
        
        wb = Workbook()
        ws = wb.add_sheet('Sheet1')
        
        ws.write(0, 0, '대분류')
        ws.write(0, 1, '중분류')
        ws.write(0, 2, '품목')
        ws.write(0, 3, '피복타입')
        
        row = 1
        large_cats = self.db.query(Category).filter(
            Category.level == CategoryLevel.LARGE, Category.is_active == True
        ).order_by(Category.sort_order).all()
        
        for large in large_cats:
            medium_cats = self.db.query(Category).filter(
                Category.parent_id == large.id, Category.is_active == True
            ).order_by(Category.sort_order).all()
            
            if not medium_cats:
                ws.write(row, 0, large.name)
                clothing_type = '완제품' if large.name == '완제품' else '맞춤피복'
                ws.write(row, 3, clothing_type)
                row += 1
                continue
            
            for medium in medium_cats:
                small_cats = self.db.query(Category).filter(
                    Category.parent_id == medium.id, Category.is_active == True
                ).order_by(Category.sort_order).all()
                
                if not small_cats:
                    ws.write(row, 0, large.name)
                    ws.write(row, 1, medium.name)
                    clothing_type = '완제품' if large.name == '완제품' else '맞춤피복'
                    ws.write(row, 3, clothing_type)
                    row += 1
                    continue
                
                for small in small_cats:
                    ws.write(row, 0, large.name)
                    ws.write(row, 1, medium.name)
                    ws.write(row, 2, small.name)
                    clothing_type = '완제품' if large.name == '완제품' else '맞춤피복'
                    ws.write(row, 3, clothing_type)
                    row += 1
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type='application/vnd.ms-excel',
            headers={'Content-Disposition': 'attachment; filename="cloth_category.xls"'}
        )

    def import_from_excel(self, file) -> dict:
        import xlrd
        
        wb = xlrd.open_workbook(file_contents=file.read())
        ws = wb.sheet_by_index(0)
        
        created = 0
        errors = []
        
        large_cache = {}
        medium_cache = {}
        
        for row_idx in range(1, ws.nrows):
            try:
                large_name = str(ws.cell_value(row_idx, 0)).strip()
                medium_name = str(ws.cell_value(row_idx, 1)).strip()
                small_name = str(ws.cell_value(row_idx, 2)).strip()
                clothing_type_str = str(ws.cell_value(row_idx, 3)).strip()
                
                if not large_name:
                    continue
                
                clothing_type = ClothingType.CUSTOM if '맞춤' in clothing_type_str else ClothingType.READY_MADE
                
                if large_name not in large_cache:
                    large = self.db.query(Category).filter(
                        Category.name == large_name, Category.level == CategoryLevel.LARGE
                    ).first()
                    if not large:
                        large = Category(name=large_name, level=CategoryLevel.LARGE, sort_order=len(large_cache))
                        self.db.add(large)
                        self.db.flush()
                    large_cache[large_name] = large.id
                
                if medium_name:
                    medium_key = f"{large_name}_{medium_name}"
                    if medium_key not in medium_cache:
                        medium = self.db.query(Category).filter(
                            Category.name == medium_name,
                            Category.parent_id == large_cache[large_name]
                        ).first()
                        if not medium:
                            medium = Category(
                                name=medium_name,
                                level=CategoryLevel.MEDIUM,
                                parent_id=large_cache[large_name],
                                sort_order=len([k for k in medium_cache if k.startswith(large_name)])
                            )
                            self.db.add(medium)
                            self.db.flush()
                        medium_cache[medium_key] = medium.id
                
                if small_name and medium_name:
                    existing = self.db.query(Category).filter(
                        Category.name == small_name,
                        Category.parent_id == medium_cache[medium_key]
                    ).first()
                    if not existing:
                        small = Category(
                            name=small_name,
                            level=CategoryLevel.SMALL,
                            parent_id=medium_cache[medium_key],
                            sort_order=0
                        )
                        self.db.add(small)
                        created += 1
                        
            except Exception as e:
                errors.append(f"행 {row_idx + 1}: {str(e)}")
        
        self.db.commit()
        return {'created': created, 'errors': errors}


class ClothingService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, item_id: int) -> Optional[ClothingItem]:
        return self.db.query(ClothingItem).filter(ClothingItem.id == item_id).first()

    def _get_descendant_ids(self, category_id: int) -> List[int]:
        """지정된 카테고리와 모든 하위 카테고리 ID를 반환"""
        ids = [category_id]
        children = self.db.query(Category).filter(Category.parent_id == category_id).all()
        for child in children:
            ids.extend(self._get_descendant_ids(child.id))
        return ids

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None,
        clothing_type: Optional[ClothingType] = None,
        is_active: Optional[bool] = None,
        keyword: Optional[str] = None,
    ) -> ClothingListResponse:
        query = self.db.query(ClothingItem)

        if category_id:
            category_ids = self._get_descendant_ids(category_id)
            query = query.filter(ClothingItem.category_id.in_(category_ids))
        if clothing_type:
            query = query.filter(ClothingItem.clothing_type == clothing_type)
        if is_active is not None:
            query = query.filter(ClothingItem.is_active == is_active)
        if keyword:
            query = query.filter(ClothingItem.name.contains(keyword))

        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        items = query.order_by(ClothingItem.created_at.desc()).offset(offset).limit(page_size).all()

        return ClothingListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def create(self, data: ClothingCreate) -> ClothingItem:
        category = self.db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise ValueError("카테고리를 찾을 수 없습니다")

        item = ClothingItem(
            name=data.name,
            category_id=data.category_id,
            clothing_type=data.clothing_type,
            image_url=data.image_url,
            thumbnail_url=data.thumbnail_url if hasattr(data, 'thumbnail_url') else None,
            description=data.description,
        )
        self.db.add(item)
        self.db.flush()  # ID 생성을 위해 flush
        
        # 맞춤피복인 경우 자동으로 "맞춤" 규격 생성
        if data.clothing_type == ClothingType.CUSTOM:
            default_spec = ClothingSpec(
                item_id=item.id,
                spec_code=f"CUSTOM-{item.id}",
                size="맞춤",
                price=0,  # 기본 가격 0, 추후 수정 필요
                is_active=True,
            )
            self.db.add(default_spec)
        
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: int, data: ClothingUpdate) -> ClothingItem:
        item = self.get_by_id(item_id)
        if not item:
            raise ValueError("품목을 찾을 수 없습니다")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        item = self.get_by_id(item_id)
        if not item:
            return False

        has_orders = self.db.query(ClothingSpec).join(
            "order_items"
        ).filter(ClothingSpec.item_id == item_id).first()
        if has_orders:
            raise ValueError("주문 내역이 있는 품목은 삭제할 수 없습니다")

        self.db.delete(item)
        self.db.commit()
        return True

    def get_detail(self, item_id: int) -> Optional[ClothingDetailResponse]:
        item = self.get_by_id(item_id)
        if not item:
            return None

        specs = (
            self.db.query(ClothingSpec)
            .filter(ClothingSpec.item_id == item_id, ClothingSpec.is_active == True)
            .order_by(ClothingSpec.spec_code)
            .all()
        )

        return ClothingDetailResponse(
            id=item.id,
            name=item.name,
            category_id=item.category_id,
            clothing_type=item.clothing_type,
            image_url=item.image_url,
            description=item.description,
            is_active=item.is_active,
            created_at=item.created_at,
            category=item.category,
            specs=[self._spec_to_response(spec) for spec in specs],
        )

    def get_specs(self, item_id: int) -> List[ClothingSpec]:
        return (
            self.db.query(ClothingSpec)
            .filter(ClothingSpec.item_id == item_id, ClothingSpec.is_active == True)
            .order_by(ClothingSpec.spec_code)
            .all()
        )

    def create_spec(self, item_id: int, data: SpecCreate) -> ClothingSpec:
        item = self.get_by_id(item_id)
        if not item:
            raise ValueError("품목을 찾을 수 없습니다")

        existing = (
            self.db.query(ClothingSpec)
            .filter(ClothingSpec.item_id == item_id, ClothingSpec.spec_code == data.spec_code)
            .first()
        )
        if existing:
            raise ValueError("이미 존재하는 규격 코드입니다")

        spec = ClothingSpec(
            item_id=item_id,
            spec_code=data.spec_code,
            size=data.size,
            price=data.price,
        )
        self.db.add(spec)
        self.db.commit()
        self.db.refresh(spec)
        return spec

    def update_spec(self, spec_id: int, data: SpecUpdate) -> ClothingSpec:
        spec = self.db.query(ClothingSpec).filter(ClothingSpec.id == spec_id).first()
        if not spec:
            raise ValueError("규격을 찾을 수 없습니다")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(spec, key, value)

        self.db.commit()
        self.db.refresh(spec)
        return spec

    def delete_spec(self, spec_id: int) -> bool:
        spec = self.db.query(ClothingSpec).filter(ClothingSpec.id == spec_id).first()
        if not spec:
            return False

        self.db.delete(spec)
        self.db.commit()
        return True

    def _to_response(self, item: ClothingItem) -> ClothingResponse:
        return ClothingResponse(
            id=item.id,
            name=item.name,
            category_id=item.category_id,
            clothing_type=item.clothing_type,
            image_url=item.image_url,
            description=item.description,
            is_active=item.is_active,
            created_at=item.created_at,
            category=item.category,
        )

    def _spec_to_response(self, spec: ClothingSpec) -> SpecResponse:
        return SpecResponse(
            id=spec.id,
            item_id=spec.item_id,
            spec_code=spec.spec_code,
            size=spec.size,
            price=spec.price,
            is_active=spec.is_active,
            created_at=spec.created_at,
        )
