from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError, PriceChangedError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PriceChangedError)
    async def _handle_price_changed(
        _request: Request, exc: PriceChangedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": exc.code,
                "subtotal": exc.subtotal,
                "shipping_fee": exc.shipping_fee,
                "cod_fee": exc.cod_fee,
                "total": exc.total,
            },
        )

    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )
