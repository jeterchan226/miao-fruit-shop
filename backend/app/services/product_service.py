def derive_stock_status(stock_qty: int, low_stock_threshold: int) -> str:
    if stock_qty <= 0:
        return "out"
    if stock_qty <= low_stock_threshold:
        return "low"
    return "in"
