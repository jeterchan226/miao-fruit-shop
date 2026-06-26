import { describe, it, expect } from 'vitest';
import {
  formatRelativeTime,
  isAfter,
  newestCreatedAt,
  unreadOrders,
} from './notifications.js';

const NOW = Date.parse('2026-06-26T12:00:00Z');
const ago = (ms) => new Date(NOW - ms).toISOString();

describe('formatRelativeTime', () => {
  it('小於一分鐘 → 剛剛', () => {
    expect(formatRelativeTime(ago(30 * 1000), NOW)).toBe('剛剛');
  });
  it('分鐘', () => {
    expect(formatRelativeTime(ago(5 * 60 * 1000), NOW)).toBe('5 分鐘前');
  });
  it('小時', () => {
    expect(formatRelativeTime(ago(3 * 60 * 60 * 1000), NOW)).toBe('3 小時前');
  });
  it('天', () => {
    expect(formatRelativeTime(ago(2 * 24 * 60 * 60 * 1000), NOW)).toBe('2 天前');
  });
});

describe('isAfter', () => {
  it('a 晚於 b → true', () => {
    expect(isAfter(ago(0), ago(1000))).toBe(true);
  });
  it('a 不晚於 b → false', () => {
    expect(isAfter(ago(1000), ago(0))).toBe(false);
  });
  it('任一為空 → false', () => {
    expect(isAfter(null, ago(0))).toBe(false);
    expect(isAfter(ago(0), null)).toBe(false);
  });
});

describe('newestCreatedAt', () => {
  it('空陣列 → null', () => {
    expect(newestCreatedAt([])).toBe(null);
  });
  it('取最大 created_at', () => {
    const orders = [
      { created_at: ago(5000) },
      { created_at: ago(1000) },
      { created_at: ago(9000) },
    ];
    expect(newestCreatedAt(orders)).toBe(ago(1000));
  });
});

describe('unreadOrders', () => {
  it('無標記 → []', () => {
    expect(unreadOrders([{ created_at: ago(0) }], null)).toEqual([]);
  });
  it('回傳晚於標記者', () => {
    const marker = ago(5000);
    const orders = [
      { order_no: 'A', created_at: ago(1000) },
      { order_no: 'B', created_at: ago(9000) },
    ];
    expect(unreadOrders(orders, marker).map((o) => o.order_no)).toEqual(['A']);
  });
});
