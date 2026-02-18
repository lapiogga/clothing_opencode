"""
메뉴 관리 모델
- 메뉴 항목 및 역할별 권한 관리
"""
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin
from app.models.user import UserRole


class Menu(Base, TimestampMixin):
    """
    메뉴 테이블
    - 시스템 메뉴 및 권한 관리
    """
    __tablename__ = "menus"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 라우터 경로
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("menus.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_category: Mapped[bool] = mapped_column(Boolean, default=False)  # 대분류 여부
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 역할별 접근 권한 (JSON 형태로 저장: ["admin", "sales_office"])
    allowed_roles: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 관계
    children: Mapped[list["Menu"]] = relationship(
        "Menu", 
        back_populates="parent",
        remote_side="Menu.id",
        order_by="Menu.sort_order"
    )
    parent: Mapped["Menu | None"] = relationship("Menu", back_populates="children")
    
    def get_allowed_roles_list(self) -> list[str]:
        """권한 목록 반환"""
        if not self.allowed_roles:
            return []
        import json
        try:
            return json.loads(self.allowed_roles)
        except:
            return []
    
    def set_allowed_roles_list(self, roles: list[str]):
        """권한 목록 저장"""
        import json
        self.allowed_roles = json.dumps(roles)


class MenuPermission(Base, TimestampMixin):
    """
    메뉴 권한 테이블 (개별 역할별 권한)
    - 메뉴별 역할 권한 상세 관리용
    """
    __tablename__ = "menu_permissions"

    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id"), nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 관계
    menu: Mapped["Menu"] = relationship("Menu")
