from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, orders, sales, inventory, tailor, stats
from app.routers import users, categories, clothings, points, sales_offices, delivery, menus

app = FastAPI(
    title="피복 구매관리 시스템",
    description="피복 구매관리 시스템 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(clothings.router, prefix="/api/clothings", tags=["clothings"])
app.include_router(points.router, prefix="/api/points", tags=["points"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(sales.router, prefix="/api/sales", tags=["sales"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(tailor.router, prefix="/api/tailor-vouchers", tags=["tailor"])
app.include_router(sales_offices.router, prefix="/api/sales-offices", tags=["sales-offices"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(delivery.router, prefix="/api/delivery-locations", tags=["delivery"])
app.include_router(menus.router, prefix="/api/menus", tags=["menus"])


@app.get("/")
def root():
    return {"message": "피복 구매관리 시스템 API"}
