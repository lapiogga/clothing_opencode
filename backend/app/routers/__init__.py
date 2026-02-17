from app.routers.auth import router as auth_router
from app.routers.orders import router as orders_router
from app.routers.sales import router as sales_router
from app.routers.inventory import router as inventory_router
from app.routers.tailor import router as tailor_router
from app.routers.stats import router as stats_router
from app.routers.users import router as users_router
from app.routers.categories import router as categories_router
from app.routers.clothings import router as clothings_router
from app.routers.points import router as points_router

__all__ = [
    "auth_router", "orders_router", "sales_router",
    "inventory_router", "tailor_router", "stats_router",
    "users_router", "categories_router", "clothings_router", "points_router",
]
