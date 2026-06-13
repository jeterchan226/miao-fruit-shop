class AppError(Exception):
    """Business 層拋出的領域例外基底(不含 HTTP 概念)。"""

    code: str = "APP_ERROR"
    status_code: int = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class InsufficientStockError(AppError):
    code = "INSUFFICIENT_STOCK"
    status_code = 409


class InvalidStatusTransition(AppError):
    code = "INVALID_STATUS_TRANSITION"
    status_code = 409


class AuthError(AppError):
    code = "AUTH_ERROR"
    status_code = 401
