from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import admin_auth, admin_images, admin_orders, admin_products, orders, products
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="妙媽媽果園 API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(admin_auth.router)
    app.include_router(admin_images.router)
    app.include_router(admin_products.router)
    app.include_router(admin_orders.router)
    app.include_router(orders.router)
    app.include_router(products.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
