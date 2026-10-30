import { describe, it, expect } from 'vitest';
import {
  ORDER_SOURCE_ADMIN,
  ORDER_SOURCE_STOREFRONT,
  PAYMENT_METHOD_TRANSFER,
} from './constants.js';

// 這些值是與後端 API 的契約，改動須與 backend/app/core/constants.py 同步。
describe('訂單常數', () => {
  it('訂單來源的值', () => {
    expect(ORDER_SOURCE_STOREFRONT).toBe('storefront');
    expect(ORDER_SOURCE_ADMIN).toBe('admin');
  });

  it('付款方式的值', () => {
    expect(PAYMENT_METHOD_TRANSFER).toBe('transfer');
  });
});
