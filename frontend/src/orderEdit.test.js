import { describe, it, expect } from 'vitest';
import {
  addableSpecs,
  adminOrderPayload,
  emptyOrderForm,
  lineForSpec,
  linesFromOrderItems,
  newLine,
  orderEditErrorMessage,
  orderItemsDiff,
  previewAmounts,
  repriceNewLines,
  validateLines,
  validateNewOrder,
  validateOrderEdit,
} from './orderEdit.js';

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

const specs = [
  { id: 1, label: '5 台斤', price: 1000, is_two_pack: false, is_active: true, stock_qty: 10 },
  { id: 2, label: '3 台斤', price: 600, is_two_pack: false, is_active: false, stock_qty: 5 },
  { id: 3, label: '2 粒裝', price: 300, is_two_pack: true, is_active: true, stock_qty: 8 },
  { id: 4, label: '10 台斤', price: 1800, is_two_pack: false, is_active: true, stock_qty: 0 },
  { id: 5, label: '8 台斤', price: 1500, is_two_pack: false, is_active: true, stock_qty: 3 },
];

describe('linesFromOrderItems', () => {
  const items = [
    { spec_id: 1, product_name: '甘露梨', spec_label: '5 台斤', is_two_pack: false, unit_price: 880, qty: 2 },
    { spec_id: 2, product_name: '甘露梨', spec_label: '3 台斤', is_two_pack: false, unit_price: 500, qty: 1 },
    { spec_id: 99, product_name: '甘露梨', spec_label: '2 粒精緻禮盒', is_two_pack: true, unit_price: 300, qty: 4 },
    { spec_id: 3, product_name: '甘露梨', spec_label: '改過包裝的規格', is_two_pack: false, unit_price: 300, qty: 3 },
    { spec_id: null, product_name: '甘露梨', spec_label: '舊規格', is_two_pack: false, unit_price: 400, qty: 1 },
  ];
  const lines = linesFromOrderItems(items, specs);

  it('既有行沿用下單價與快照名稱', () => {
    expect(lines[0]).toMatchObject({
      spec_id: 1, label: '甘露梨 · 5 台斤', unitPrice: 880, qty: 2,
      isTwoPack: false, isNew: false, locked: false,
    });
  });
  it('已下架規格的行鎖定數量(R10)', () => {
    expect(lines[1]).toMatchObject({ spec_id: 2, locked: true, isTwoPack: false });
  });
  it('規格已刪除仍以快照為兩粒裝,並鎖定數量', () => {
    expect(lines[2]).toMatchObject({ spec_id: 99, locked: true, isTwoPack: true });
  });
  it('規格改過包裝類型時採快照', () => {
    expect(lines[3]).toMatchObject({ spec_id: 3, isTwoPack: false });
  });
  it('無 spec_id 的舊資料鎖定數量', () => {
    expect(lines[4]).toMatchObject({ spec_id: null, locked: true, isTwoPack: false });
  });
  it('規格已刪除的兩粒裝 ×4 以 2 層試算,與後端一致', () => {
    expect(previewAmounts([lines[2]])).toEqual({ subtotal: 1200, shippingFee: 150, total: 1350 });
  });
});

describe('newLine', () => {
  it('用目前價格,箱裝預設數量 1', () => {
    expect(newLine({ ...specs[0], productName: '甘露梨' })).toEqual({
      spec_id: 1, label: '甘露梨 · 5 台斤', unitPrice: 1000, qty: 1,
      isTwoPack: false, isNew: true, locked: false,
    });
  });
  it('兩粒裝預設數量 2', () => {
    expect(newLine({ ...specs[2], productName: '甘露梨' })).toMatchObject({ qty: 2, isTwoPack: true });
  });
});

describe('lineForSpec', () => {
  const orderItems = [
    { spec_id: 1, product_name: '甘露梨', spec_label: '5 台斤', is_two_pack: false, unit_price: 880, qty: 2 },
  ];
  it('規格不在訂單中 → 新行,用目前價格', () => {
    expect(lineForSpec({ ...specs[2], productName: '甘露梨' }, orderItems)).toMatchObject({
      spec_id: 3, unitPrice: 300, isNew: true,
    });
  });
  it('移除後再加回訂單原有的規格 → 還原原行與下單價,與後端依規格比對一致', () => {
    expect(lineForSpec({ ...specs[0], productName: '甘露梨' }, orderItems)).toEqual({
      spec_id: 1, label: '甘露梨 · 5 台斤', unitPrice: 880, qty: 2,
      isTwoPack: false, isNew: false, locked: false,
    });
  });
});

describe('addableSpecs', () => {
  it('只列上架中、有庫存、且不在訂單中的規格(R8)', () => {
    const lines = [{ spec_id: 1 }];
    expect(addableSpecs(specs, lines).map((s) => s.id)).toEqual([3, 5]);
  });
});

describe('previewAmounts', () => {
  it('依每行單價與數量計算,箱裝每箱 1 層', () => {
    expect(
      previewAmounts([{ unitPrice: 880, qty: 1, isTwoPack: false }])
    ).toEqual({ subtotal: 880, shippingFee: 100, total: 980 });
  });
  it('兩粒裝每 2 箱 1 層', () => {
    // 880*2 + 300*2 = 2360;層數 2 + 1 = 3 → 運費 180
    expect(
      previewAmounts([
        { unitPrice: 880, qty: 2, isTwoPack: false },
        { unitPrice: 300, qty: '2', isTwoPack: true },
      ])
    ).toEqual({ subtotal: 2360, shippingFee: 180, total: 2540 });
  });
  it('達免運門檻運費 0', () => {
    expect(previewAmounts([{ unitPrice: 880, qty: 4, isTwoPack: false }])).toEqual({
      subtotal: 3520, shippingFee: 0, total: 3520,
    });
  });
  it('沒有任何行 → null', () => {
    expect(previewAmounts([])).toBeNull();
  });
});

describe('validateLines', () => {
  const line = (over) => ({ spec_id: 1, qty: 1, isTwoPack: false, ...over });

  it('合法 → null', () => {
    expect(validateLines([line(), line({ spec_id: 3, qty: '4', isTwoPack: true })])).toBeNull();
  });
  it('沒有任何訂單品項 → 請改取消訂單(R2)', () => {
    expect(validateLines([])).toBe('訂單至少保留一個訂單品項；全部不要請取消訂單。');
  });
  it.each([0, -1, 1.5, '', 'abc'])('數量 %s 不是正整數', (qty) => {
    expect(validateLines([line({ qty })])).toBe('請確認每個訂單品項的數量為正整數。');
  });
  it('兩粒裝單數(R3)', () => {
    expect(validateLines([line({ label: '甘露梨 · 2 粒精緻禮盒', qty: 3, isTwoPack: true })])).toBe(
      '甘露梨 · 2 粒精緻禮盒 為兩粒裝，請以雙數（2、4、6…）購買。'
    );
  });
  it('規格已刪除的訂單品項無法隨品項變更送出', () => {
    expect(validateLines([line(), line({ spec_id: null, label: '甘露梨 · 舊規格' })])).toBe(
      '甘露梨 · 舊規格 的規格已刪除，修改訂單品項前請先移除它。'
    );
  });
});

describe('repriceNewLines', () => {
  it('新行改用規格最新價格,既有行下單價不變', () => {
    const lines = [
      { spec_id: 1, unitPrice: 880, isNew: false },
      { spec_id: 3, unitPrice: 250, isNew: true },
    ];
    expect(repriceNewLines(lines, specs).map((l) => l.unitPrice)).toEqual([880, 300]);
  });
  it('新行改用規格目前的包裝類型,既有行維持快照', () => {
    const lines = [
      { spec_id: 1, unitPrice: 880, isTwoPack: true, isNew: false },
      { spec_id: 3, unitPrice: 300, isTwoPack: false, isNew: true },
    ];
    expect(repriceNewLines(lines, specs).map((l) => l.isTwoPack)).toEqual([true, true]);
  });
});

describe('orderEditErrorMessage', () => {
  const err = (code, data = {}, status = 409) => ({ code, status, data: { code, ...data } });

  it('PRICE_CHANGED 顯示新金額請重新確認', () => {
    expect(orderEditErrorMessage(err('PRICE_CHANGED', { total: 3280 }))).toBe(
      '規格價格或包裝類型已更新，新的訂單總額為 NT$ 3,280，請重新確認後再儲存訂單。'
    );
  });
  it.each([
    ['ITEM_QTY_LOCKED', '5 台斤 已下架，數量不可修改'],
    ['INSUFFICIENT_STOCK', '庫存不足:5 台斤'],
    ['EVEN_QTY_REQUIRED', '2 粒裝 為 2 粒裝，請以雙數（2、4、6…）購買'],
  ])('%s 顯示後端訊息', (code, detail) => {
    expect(orderEditErrorMessage(err(code, { detail }))).toBe(detail);
  });
  it.each([
    ['ITEM_QTY_LOCKED', '已下架規格的數量不可修改，只能移除此訂單品項。'],
    ['INSUFFICIENT_STOCK', '庫存不足，請調整數量。'],
    ['EVEN_QTY_REQUIRED', '兩粒裝請以雙數（2、4、6…）購買。'],
  ])('%s 無後端訊息時用預設', (code, fallback) => {
    expect(orderEditErrorMessage(err(code))).toBe(fallback);
  });
  it('DUPLICATE_SPEC', () => {
    expect(orderEditErrorMessage(err('DUPLICATE_SPEC', {}, 422))).toBe(
      '同一規格只能有一個訂單品項，請合併數量。'
    );
  });
  it('其他錯誤沿用後端 detail,否則通用訊息', () => {
    expect(orderEditErrorMessage(err('ORDER_NOT_EDITABLE', { detail: '已出貨' }))).toBe('已出貨');
    expect(orderEditErrorMessage(undefined)).toBe('儲存失敗。');
  });
});

const filledForm = () => ({
  ...emptyOrderForm(),
  customer_name: '王小明',
  customer_phone: '0912345678',
  ship_zipcode: '100',
  ship_city: '台北市',
  ship_district: '中正區',
  ship_street: '重慶南路1號',
  preferred_date: '2026-11-12',
});

const boxLine = () => newLine({
  id: 7, label: '5 台斤家庭箱', price: 1880, is_two_pack: false, productName: '甘露梨',
});

describe('emptyOrderForm', () => {
  it('欄位皆空白,時段預設不指定', () => {
    const form = emptyOrderForm();
    expect(form.customer_name).toBe('');
    expect(form.customer_email).toBe('');
    expect(form.delivery_window).toBe('any');
  });
});

describe('validateNewOrder', () => {
  // 與商店頁共用 validateCustomerShipping;以固定「今天」避免送達日檢查隨日期漂移
  const NOW = new Date('2026-11-10T12:00:00Z');
  const check = (form, lines = [boxLine()]) => validateNewOrder(form, lines, NOW);

  it('必填欄位都有、訂單品項合法 → null', () => {
    expect(check(filledForm())).toBeNull();
  });
  it('Email、備註、郵遞區號可留空(同商店頁)', () => {
    expect(check({ ...filledForm(), customer_email: '', note: '', ship_zipcode: '' })).toBeNull();
  });
  it('缺顧客姓名 → 沿用商店頁訊息', () => {
    expect(check({ ...filledForm(), customer_name: '  ' })).toBe('請輸入姓名');
  });
  it('電話格式不符 → 沿用商店頁訊息', () => {
    expect(check({ ...filledForm(), customer_phone: '0912abc' })).toBe('電話格式不正確');
  });
  it('缺希望送達日期 → 沿用商店頁訊息', () => {
    expect(check({ ...filledForm(), preferred_date: '' })).toBe('請選擇送達日期');
  });
  it('送達日早於明天 → 擋下(同商店頁)', () => {
    expect(check({ ...filledForm(), preferred_date: '2026-11-10' })).toBe('送達日不得早於明天');
  });
  it('沒有訂單品項 → 提示新增,不提取消訂單', () => {
    const msg = check(filledForm(), []);
    expect(msg).toMatch('請至少新增一個訂單品項');
    expect(msg).not.toMatch('取消訂單');
  });
  it('訂單品項不合法 → 沿用 validateLines 訊息', () => {
    const pair = newLine({ id: 8, label: '2 粒裝', price: 300, is_two_pack: true, productName: '甘露梨' });
    expect(check(filledForm(), [{ ...pair, qty: 3 }])).toMatch('雙數');
  });
});

describe('adminOrderPayload', () => {
  it('組出 AdminOrderCreate,expected_total 為畫面試算總額', () => {
    const lines = [{ ...boxLine(), qty: '2' }];
    const payload = adminOrderPayload({ ...filledForm(), note: '電話訂購' }, lines);
    expect(payload).toEqual({
      customer_name: '王小明',
      customer_phone: '0912345678',
      customer_email: null,
      shipping: {
        zipcode: '100',
        city: '台北市',
        district: '中正區',
        street: '重慶南路1號',
        preferred_date: '2026-11-12',
        delivery_window: 'any',
      },
      items: [{ spec_id: 7, qty: 2 }],
      note: '電話訂購',
      expected_total: previewAmounts(lines).total,
    });
  });
  it('有填 Email 才送,備註空白送 null', () => {
    const payload = adminOrderPayload(
      { ...filledForm(), customer_email: 'a@b.tw', note: '' }, [boxLine()],
    );
    expect(payload.customer_email).toBe('a@b.tw');
    expect(payload.note).toBeNull();
  });
});

describe('validateOrderEdit', () => {
  // 編輯訂單存檔:顧客/收件欄位走與商店頁相同的 validateCustomerShipping
  const NOW = new Date('2026-11-10T12:00:00Z');
  const order = {
    preferred_date: '2026-11-01',
    items: [{ spec_id: 7, qty: 1, unit_price: 1880 }],
  };
  const editForm = (overrides = {}) => ({
    ...filledForm(),
    preferred_date: '2026-11-01',
    items: [{ ...boxLine(), isNew: false, qty: 1 }],
    ...overrides,
  });
  const check = (form) => validateOrderEdit(form, order, NOW);

  it('欄位合法、品項未變 → null', () => {
    expect(check(editForm())).toBeNull();
  });
  it('必填欄位清空 → 擋下', () => {
    expect(check(editForm({ customer_name: '' }))).toBe('請輸入姓名');
    expect(check(editForm({ customer_phone: ' ' }))).toBe('請輸入電話');
    expect(check(editForm({ ship_city: '' }))).toBe('請選擇縣市');
    expect(check(editForm({ ship_district: '' }))).toBe('請選擇區域');
    expect(check(editForm({ ship_street: '' }))).toBe('請輸入詳細地址');
    expect(check(editForm({ preferred_date: '' }))).toBe('請選擇送達日期');
  });
  it('電話格式不符 → 擋下', () => {
    expect(check(editForm({ customer_phone: 'abc' }))).toBe('電話格式不正確');
  });
  it('送達日維持原值即使已過 → 放行;改成早於明天的新日期 → 擋下', () => {
    expect(check(editForm())).toBeNull();
    expect(check(editForm({ preferred_date: '2026-11-09' }))).toBe('送達日不得早於明天');
  });
  it('品項有變動時才檢查訂單品項', () => {
    const pair = newLine({ id: 8, label: '2 粒裝', price: 300, is_two_pack: true, productName: '甘露梨' });
    expect(check(editForm({ items: [{ ...pair, qty: 3 }] }))).toMatch('雙數');
  });
});
