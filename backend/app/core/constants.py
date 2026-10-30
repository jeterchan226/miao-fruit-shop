from typing import Final, Literal

# 金額規則常數(與前端 frontend/src/Cart.jsx 對齊)。金額一律整數 NT$。
FREE_SHIPPING_THRESHOLD = 3000  # subtotal 達此值(含)以上免運
SHIPPING_BY_LAYER = {1: 100, 2: 150, 3: 180}

# 訂單來源:顧客下單 / 代客下單
OrderSource = Literal["storefront", "admin"]
ORDER_SOURCE_STOREFRONT: Final = "storefront"
ORDER_SOURCE_ADMIN: Final = "admin"

# 付款方式:目前只有轉帳匯款
PaymentMethod = Literal["transfer"]
PAYMENT_METHOD_TRANSFER: Final = "transfer"
