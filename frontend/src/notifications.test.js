import { describe, it, expect } from 'vitest';
import {
  evaluatePoll,
  formatRelativeTime,
  isAfter,
  isCustomerOrder,
  newestCreatedAt,
  newOrdersSince,
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

describe('newOrdersSince', () => {
  it('回傳晚於基準者', () => {
    const since = ago(5000);
    const recent = [
      { order_no: 'A', created_at: ago(1000) },
      { order_no: 'B', created_at: ago(9000) },
    ];
    expect(newOrdersSince(recent, since).map((o) => o.order_no)).toEqual(['A']);
  });
  it('無更新訂單 → []', () => {
    const since = ago(0);
    expect(newOrdersSince([{ order_no: 'A', created_at: ago(1000) }], since)).toEqual([]);
  });
  it('基準為 null（表格空）→ 全部視為新', () => {
    const recent = [
      { order_no: 'A', created_at: ago(1000) },
      { order_no: 'B', created_at: ago(2000) },
    ];
    expect(newOrdersSince(recent, null).map((o) => o.order_no)).toEqual(['A', 'B']);
  });
  it('相同 created_at → 不算新', () => {
    const t = ago(3000);
    expect(newOrdersSince([{ order_no: 'A', created_at: t }], t)).toEqual([]);
  });
  it('recentOrders 為空 / undefined → []', () => {
    expect(newOrdersSince([], ago(0))).toEqual([]);
    expect(newOrdersSince(undefined, ago(0))).toEqual([]);
  });
});

describe('排除代客下單（source === admin）', () => {
  it('只有代客下單 → 不計未讀', () => {
    const orders = [{ order_no: 'A', source: 'admin', created_at: ago(1000) }];
    expect(unreadOrders(orders, ago(5000))).toEqual([]);
  });
  it('混合 → 只計顧客下單未讀', () => {
    const orders = [
      { order_no: 'A', source: 'admin', created_at: ago(1000) },
      { order_no: 'B', source: 'storefront', created_at: ago(2000) },
    ];
    expect(unreadOrders(orders, ago(5000)).map((o) => o.order_no)).toEqual(['B']);
  });
  it('只有代客下單 → 橫幅無新訂單', () => {
    const recent = [{ order_no: 'A', source: 'admin', created_at: ago(1000) }];
    expect(newOrdersSince(recent, ago(5000))).toEqual([]);
    expect(newOrdersSince(recent, null)).toEqual([]);
  });
  it('混合 → 橫幅只列顧客下單', () => {
    const recent = [
      { order_no: 'A', source: 'admin', created_at: ago(1000) },
      { order_no: 'B', source: 'storefront', created_at: ago(2000) },
    ];
    expect(newOrdersSince(recent, ago(5000)).map((o) => o.order_no)).toEqual(['B']);
  });
  it('只有代客下單 → 最新建立時間為 null，不響鈴', () => {
    const orders = [{ order_no: 'A', source: 'admin', created_at: ago(1000) }];
    expect(newestCreatedAt(orders)).toBe(null);
  });
  it('混合 → 最新建立時間只看顧客下單', () => {
    const orders = [
      { order_no: 'A', source: 'admin', created_at: ago(1000) },
      { order_no: 'B', source: 'storefront', created_at: ago(2000) },
    ];
    expect(newestCreatedAt(orders)).toBe(ago(2000));
  });
  it('isCustomerOrder：代客下單為否，顧客下單為是', () => {
    expect(isCustomerOrder({ source: 'admin' })).toBe(false);
    expect(isCustomerOrder({ source: 'storefront' })).toBe(true);
  });
});

describe('evaluatePoll', () => {
  const customer = (no, t) => ({ order_no: no, source: 'storefront', created_at: t });
  const admin = (no, t) => ({ order_no: no, source: 'admin', created_at: t });

  it('首次輪詢：以最新顧客下單為基準，不響鈴；無已讀標記時初始化為該時間', () => {
    const r = evaluatePoll(null, [customer('A', ago(1000))], false);
    expect(r).toEqual({ state: { newest: ago(1000) }, chime: false, initLastReadAt: ago(1000) });
  });
  it('首次輪詢：已有已讀標記時不初始化', () => {
    expect(evaluatePoll(null, [customer('A', ago(1000))], true).initLastReadAt).toBe(null);
  });
  it('首次輪詢：只有代客下單 → 基準為 null，已讀標記初始化為 epoch', () => {
    const r = evaluatePoll(null, [admin('A', ago(1000))], false);
    expect(r).toEqual({
      state: { newest: null },
      chime: false,
      initLastReadAt: '1970-01-01T00:00:00.000Z',
    });
  });
  it('出現更新的顧客下單 → 響鈴並推進基準', () => {
    const r = evaluatePoll({ newest: ago(5000) }, [customer('A', ago(1000))], true);
    expect(r).toEqual({ state: { newest: ago(1000) }, chime: true, initLastReadAt: null });
  });
  it('只多了代客下單 → 不響鈴', () => {
    const orders = [admin('B', ago(1000)), customer('A', ago(5000))];
    const r = evaluatePoll({ newest: ago(5000) }, orders, true);
    expect(r.chime).toBe(false);
    expect(r.state).toEqual({ newest: ago(5000) });
  });
  it('基準為 null（先前只有代客下單）後出現顧客下單 → 響鈴', () => {
    const orders = [customer('B', ago(1000)), admin('A', ago(5000))];
    expect(evaluatePoll({ newest: null }, orders, true).chime).toBe(true);
  });
  it('沒有新訂單 → 不響鈴', () => {
    const r = evaluatePoll({ newest: ago(1000) }, [customer('A', ago(1000))], true);
    expect(r.chime).toBe(false);
  });
});
