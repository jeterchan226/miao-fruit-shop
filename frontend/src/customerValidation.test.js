import { describe, it, expect } from 'vitest';
import { getTomorrowStr, validateCustomerShipping } from './customerValidation.js';

const NOW = new Date('2026-11-10T12:00:00Z');

const valid = () => ({
  name: '王小明',
  phone: '0912-345-678',
  city: '台北市',
  district: '中正區',
  street: '重慶南路1號',
  preferredDate: '2026-11-11',
});

describe('getTomorrowStr', () => {
  it('回傳隔天的 YYYY-MM-DD', () => {
    expect(getTomorrowStr(NOW)).toBe('2026-11-11');
  });
});

describe('validateCustomerShipping', () => {
  it('全部合法 → 空物件', () => {
    expect(validateCustomerShipping(valid(), NOW)).toEqual({});
  });

  it('姓名、詳細地址只有空白 → 必填', () => {
    const errors = validateCustomerShipping({ ...valid(), name: '  ', street: ' ' }, NOW);
    expect(errors.name).toBe('請輸入姓名');
    expect(errors.street).toBe('請輸入詳細地址');
  });

  it('電話空白 → 必填;格式不符 → 格式錯誤', () => {
    expect(validateCustomerShipping({ ...valid(), phone: '' }, NOW).phone).toBe('請輸入電話');
    expect(validateCustomerShipping({ ...valid(), phone: '0912abc' }, NOW).phone).toBe('電話格式不正確');
  });

  it('欄位為 null(如後台舊資料)也視為未填,不會拋錯', () => {
    const errors = validateCustomerShipping(
      { name: null, phone: null, city: null, district: null, street: null, preferredDate: null }, NOW,
    );
    expect(Object.keys(errors)).toEqual(['name', 'phone', 'city', 'district', 'street', 'preferredDate']);
  });

  it('縣市、區域未填 → 提示選擇', () => {
    const errors = validateCustomerShipping({ ...valid(), city: '', district: '' }, NOW);
    expect(errors.city).toBe('請選擇縣市');
    expect(errors.district).toBe('請選擇區域');
  });

  it('送達日未填 / 無效 / 早於明天 → 各自提示', () => {
    expect(validateCustomerShipping({ ...valid(), preferredDate: '' }, NOW).preferredDate)
      .toBe('請選擇送達日期');
    expect(validateCustomerShipping({ ...valid(), preferredDate: 'abc' }, NOW).preferredDate)
      .toBe('日期無效，請重新選擇');
    expect(validateCustomerShipping({ ...valid(), preferredDate: '2026-11-10' }, NOW).preferredDate)
      .toBe('送達日不得早於明天');
  });

  it('送達日為明天 → 合法', () => {
    expect(validateCustomerShipping(valid(), NOW).preferredDate).toBeUndefined();
  });
});

describe('validateCustomerShipping — 既有訂單的原送達日', () => {
  it('送達日維持訂單原值時,即使早於明天也放行', () => {
    const fields = { ...valid(), preferredDate: '2026-11-01' };
    expect(validateCustomerShipping(fields, NOW, { savedDate: '2026-11-01' })).toEqual({});
  });
  it('改成其他早於明天的日期 → 仍擋下', () => {
    const fields = { ...valid(), preferredDate: '2026-11-05' };
    expect(validateCustomerShipping(fields, NOW, { savedDate: '2026-11-01' }).preferredDate)
      .toBe('送達日不得早於明天');
  });
  it('原送達日也不可清空', () => {
    const fields = { ...valid(), preferredDate: '' };
    expect(validateCustomerShipping(fields, NOW, { savedDate: '2026-11-01' }).preferredDate)
      .toBe('請選擇送達日期');
  });
});
