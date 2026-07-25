/* 運費與層數計算 — 與後端 order_service 公式一致 */

export const FREE_SHIPPING = 3000;
export const SHIPPING_BY_LAYER = { 1: 130, 2: 150, 3: 180 };

// 非2粒每箱1層；2粒每2箱1層。
export function computeLayers(items) {
  return items.reduce(
    (n, it) => n + (it.isTwoPack ? Math.floor(it.count / 2) : it.count),
    0
  );
}

export function computeShipping(subtotal, layers) {
  if (subtotal >= FREE_SHIPPING) return 0;
  if (layers <= 0) return 0;
  return SHIPPING_BY_LAYER[Math.min(layers, 3)];
}
