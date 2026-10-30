import { afterEach, describe, expect, it } from 'vitest';
import { localDateRangeToUtc } from './dateRange.js';

const ORIGINAL_TZ = process.env.TZ;

const inZone = (tz, fn) => {
  process.env.TZ = tz;
  return fn();
};

afterEach(() => {
  process.env.TZ = ORIGINAL_TZ;
});

describe('localDateRangeToUtc', () => {
  it('台北:起日 00:00 含、迄日隔天 00:00 不含', () => {
    expect(
      inZone('Asia/Taipei', () =>
        localDateRangeToUtc({ dateFrom: '2026-10-30', dateTo: '2026-10-31' }),
      ),
    ).toEqual({
      created_from: '2026-10-29T16:00:00.000Z',
      created_before: '2026-10-31T16:00:00.000Z',
    });
  });

  it('UTC 時區不位移', () => {
    expect(
      inZone('UTC', () => localDateRangeToUtc({ dateFrom: '2026-10-30', dateTo: '2026-10-30' })),
    ).toEqual({
      created_from: '2026-10-30T00:00:00.000Z',
      created_before: '2026-10-31T00:00:00.000Z',
    });
  });

  it('跨月、跨年邊界', () => {
    expect(
      inZone('Asia/Taipei', () =>
        localDateRangeToUtc({ dateFrom: '2026-01-01', dateTo: '2026-12-31' }),
      ),
    ).toEqual({
      created_from: '2025-12-31T16:00:00.000Z',
      created_before: '2026-12-31T16:00:00.000Z',
    });
  });

  it('DST 結束日(紐約 2026-11-01 為 25 小時)', () => {
    expect(
      inZone('America/New_York', () =>
        localDateRangeToUtc({ dateFrom: '2026-11-01', dateTo: '2026-11-01' }),
      ),
    ).toEqual({
      created_from: '2026-11-01T04:00:00.000Z',
      created_before: '2026-11-02T05:00:00.000Z',
    });
  });

  it('只給單邊或都沒給', () => {
    inZone('Asia/Taipei', () => {
      expect(localDateRangeToUtc({ dateFrom: '2026-10-30' })).toEqual({
        created_from: '2026-10-29T16:00:00.000Z',
      });
      expect(localDateRangeToUtc({ dateTo: '2026-10-30' })).toEqual({
        created_before: '2026-10-30T16:00:00.000Z',
      });
      expect(localDateRangeToUtc({ dateFrom: '', dateTo: '' })).toEqual({});
      expect(localDateRangeToUtc()).toEqual({});
    });
  });
});
