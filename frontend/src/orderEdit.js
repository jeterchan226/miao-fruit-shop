/* 後台訂單品項編輯 — 逐行規則、送出比對與金額試算(後台編輯與代客下單共用) */
import { computeLayers, computeShipping } from './pricing.js';

/*
 * 編輯中的一行訂單品項:
 *   { spec_id, label, unitPrice, qty, isTwoPack, isNew, locked }
 * isNew   — 本次編輯新增的行,單價為規格目前價格(R5);否則為下單價(R6)。
 * locked  — 規格已下架或已刪除,數量不可改,只能移除(R10)。
 */

const normalize = (items) =>
  items
    .map((it) => `${Number(it.spec_id)}:${Number(it.qty)}`)
    .sort()
    .join(',');

// 訂單品項(規格+數量)與開啟時相同 → false,不送 items(R13)。
export function orderItemsDiff(original, form) {
  return normalize(original) !== normalize(form);
}

const specLabel = (productName, label) => (productName ? `${productName} · ${label}` : label);

// 訂單既有的訂單品項 → 編輯行。名稱用下單時的快照,規格現況只用來判斷包裝類型與是否上架。
export function linesFromOrderItems(items, specs) {
  return items.map((it) => {
    const spec = specs.find((s) => s.id === it.spec_id);
    return {
      spec_id: it.spec_id,
      label: specLabel(it.product_name, it.spec_label),
      unitPrice: it.unit_price,
      qty: it.qty,
      // 規格已刪除時與後端 compute_amounts 一致,視為非兩粒裝
      isTwoPack: spec ? spec.is_two_pack : false,
      isNew: false,
      locked: !spec || !spec.is_active,
    };
  });
}

// 兩粒裝數量以 2 為單位增減(R3)。
export const qtyStep = (isTwoPack) => (isTwoPack ? 2 : 1);

// 加訂新規格的行:單價為目前價格(R5),兩粒裝從 2 起跳(R3)。spec 需帶 productName。
export function newLine(spec) {
  return {
    spec_id: spec.id,
    label: specLabel(spec.productName, spec.label),
    unitPrice: spec.price,
    qty: qtyStep(spec.is_two_pack),
    isTwoPack: spec.is_two_pack,
    isNew: true,
    locked: false,
  };
}

// 選單加入規格時建立的行。後端依規格比對差異,訂單原有的規格即使移除後再加回,
// 仍沿用原下單價(R6),因此還原原行;其餘為新行。
export function lineForSpec(spec, orderItems) {
  const original = orderItems.find((it) => it.spec_id === spec.id);
  return original ? linesFromOrderItems([original], [spec])[0] : newLine(spec);
}

// 可新增的規格:上架中、有庫存、且不在此訂單中(R8)。
export function addableSpecs(specs, lines) {
  const taken = new Set(lines.map((l) => Number(l.spec_id)));
  return specs.filter((s) => s.is_active && s.stock_qty > 0 && !taken.has(s.id));
}

// 即時試算:每行以自身單價(既有行為下單價、新行為目前價格)計算,運費依層數照規則(R7)。
// 與後端 order_items.compute_amounts 一致;沒有訂單品項時回 null。
export function previewAmounts(lines) {
  if (!lines.length) return null;
  const counted = lines.map((l) => ({ count: Number(l.qty), isTwoPack: l.isTwoPack }));
  const subtotal = lines.reduce((sum, l) => sum + l.unitPrice * Number(l.qty), 0);
  const shippingFee = computeShipping(subtotal, computeLayers(counted));
  return { subtotal, shippingFee, total: subtotal + shippingFee };
}

// 送出前檢查;回傳錯誤訊息,合法則回 null。後端仍會再驗一次。
export function validateLines(lines) {
  if (!lines.length) return '訂單至少保留一個訂單品項；全部不要請取消訂單。';
  for (const l of lines) {
    const qty = Number(l.qty);
    if (l.qty === '' || !Number.isInteger(qty) || qty < 1) {
      return '請確認每個訂單品項的數量為正整數。';
    }
    if (l.isTwoPack && qty % 2 !== 0) {
      return `${l.label} 為兩粒裝，請以雙數（2、4、6…）購買。`;
    }
    // 規格已刪除的訂單品項無 spec_id 可送,只能移除
    if (l.spec_id == null) return `${l.label} 的規格已刪除，修改訂單品項前請先移除它。`;
  }
  return null;
}

// PRICE_CHANGED 後重新載入規格:新行改用最新價格,既有行下單價不變。
export function repriceNewLines(lines, specs) {
  return lines.map((l) => {
    if (!l.isNew) return l;
    const spec = specs.find((s) => s.id === l.spec_id);
    return spec ? { ...l, unitPrice: spec.price } : l;
  });
}

export const money = (n) => `NT$ ${Number(n || 0).toLocaleString()}`;

const FALLBACK_MESSAGES = {
  ITEM_QTY_LOCKED: '已下架規格的數量不可修改，只能移除此訂單品項。',
  INSUFFICIENT_STOCK: '庫存不足，請調整數量。',
  EVEN_QTY_REQUIRED: '兩粒裝請以雙數（2、4、6…）購買。',
};

export function orderEditErrorMessage(err) {
  const data = err?.data || {};
  if (err?.code === 'PRICE_CHANGED') {
    return `規格價格已更新，新的訂單總額為 ${money(data.total)}，請重新確認後再儲存。`;
  }
  if (err?.code === 'DUPLICATE_SPEC') return '同一規格只能有一個訂單品項，請合併數量。';
  if (err?.code in FALLBACK_MESSAGES) return data.detail || FALLBACK_MESSAGES[err.code];
  return data.detail || '儲存失敗。';
}
