import { describe, it, expect } from 'vitest';
import { orderItemsDiff, previewAmounts } from './orderEdit.js';

const original = [
  { spec_id: 1, qty: 2, unit_price: 880 },
  { spec_id: 2, qty: 1, unit_price: 500 },
];

describe('orderItemsDiff', () => {
  it('規格與數量都相同 → false(不送 items)', () => {
    expect(orderItemsDiff(original, [{ spec_id: 1, qty: 2 }, { spec_id: 2, qty: 1 }])).toBe(false);
  });
  it('表單值為字串仍視為相同', () => {
    expect(orderItemsDiff(original, [{ spec_id: '1', qty: '2' }, { spec_id: '2', qty: '1' }])).toBe(false);
  });
  it('只換順序 → false', () => {
    expect(orderItemsDiff(original, [{ spec_id: 2, qty: 1 }, { spec_id: 1, qty: 2 }])).toBe(false);
  });
  it('數量改變 → true', () => {
    expect(orderItemsDiff(original, [{ spec_id: 1, qty: 4 }, { spec_id: 2, qty: 1 }])).toBe(true);
  });
  it('移除一行 → true', () => {
    expect(orderItemsDiff(original, [{ spec_id: 1, qty: 2 }])).toBe(true);
  });
  it('新增一行 → true', () => {
    expect(
      orderItemsDiff(original, [{ spec_id: 1, qty: 2 }, { spec_id: 2, qty: 1 }, { spec_id: 3, qty: 1 }])
    ).toBe(true);
  });
  it('換規格 → true', () => {
    expect(orderItemsDiff(original, [{ spec_id: 1, qty: 2 }, { spec_id: 3, qty: 1 }])).toBe(true);
  });
});

describe('previewAmounts', () => {
  const specs = [
    { id: 1, price: 1000, is_two_pack: false },
    { id: 2, price: 600, is_two_pack: false },
    { id: 3, price: 300, is_two_pack: true },
  ];

  it('既有規格沿用下單價,不用目前價格', () => {
    expect(previewAmounts(original, [{ spec_id: 1, qty: 1 }], specs)).toEqual({
      subtotal: 880,
      shippingFee: 100,
      total: 980,
    });
  });
  it('新增規格用目前價格,兩粒裝每 2 箱 1 層', () => {
    // 880*2 + 300*2 = 2360;層數 2 + 1 = 3 → 運費 180
    expect(
      previewAmounts(original, [{ spec_id: 1, qty: 2 }, { spec_id: '3', qty: '2' }], specs)
    ).toEqual({ subtotal: 2360, shippingFee: 180, total: 2540 });
  });
  it('達免運門檻運費 0', () => {
    expect(previewAmounts(original, [{ spec_id: 1, qty: 4 }], specs)).toEqual({
      subtotal: 3520,
      shippingFee: 0,
      total: 3520,
    });
  });
  it('有未知規格 → null', () => {
    expect(previewAmounts(original, [{ spec_id: 9, qty: 1 }], specs)).toBeNull();
  });
  it('既有規格不在規格清單(未載入) → null,避免誤判兩粒裝', () => {
    expect(previewAmounts(original, [{ spec_id: 1, qty: 2 }], [])).toBeNull();
  });
});
