/* 後台訂單編輯 — 送出比對與金額試算 */
import { computeLayers, computeShipping } from './pricing.js';

const normalize = (items) =>
  items
    .map((it) => `${Number(it.spec_id)}:${Number(it.qty)}`)
    .sort()
    .join(',');

// 訂單品項(規格+數量)與開啟時相同 → false,不送 items(R13)。
export function orderItemsDiff(original, form) {
  return normalize(original) !== normalize(form);
}

// 既有規格沿用下單價(R6)、新增規格用目前價格(R5);
// 規格不在清單中(未載入或已刪除)無從得知是否兩粒裝,回 null。
export function previewAmounts(original, form, specs) {
  const lines = [];
  for (const it of form) {
    const specId = Number(it.spec_id);
    const spec = specs.find((s) => s.id === specId);
    if (!spec) return null;
    const existing = original.find((o) => o.spec_id === specId);
    lines.push({
      price: existing ? existing.unit_price : spec.price,
      count: Number(it.qty),
      isTwoPack: spec.is_two_pack,
    });
  }
  const subtotal = lines.reduce((sum, l) => sum + l.price * l.count, 0);
  const shippingFee = computeShipping(subtotal, computeLayers(lines));
  return { subtotal, shippingFee, total: subtotal + shippingFee };
}
