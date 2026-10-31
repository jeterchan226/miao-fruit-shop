import { afterEach, describe, expect, it, vi } from 'vitest';

import { generateCheckoutKey, nextCheckoutKey } from './checkoutKey.js';

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('nextCheckoutKey', () => {
  it('generates a key when there is no previous one', () => {
    const { key, fingerprint } = nextCheckoutKey(null, { qty: 1 });
    expect(key).toMatch(UUID_V4);
    expect(fingerprint).toBe('{"qty":1}');
  });

  it('keeps the key when the payload is unchanged', () => {
    const first = nextCheckoutKey(null, { qty: 1 });
    expect(nextCheckoutKey(first, { qty: 1 })).toEqual(first);
  });

  it('replaces the key when the payload changes', () => {
    const first = nextCheckoutKey(null, { qty: 1 });
    const second = nextCheckoutKey(first, { qty: 2 });
    expect(second.key).not.toBe(first.key);
    expect(second.fingerprint).toBe('{"qty":2}');
  });
});

describe('generateCheckoutKey', () => {
  it('uses crypto.randomUUID when available', () => {
    vi.stubGlobal('crypto', { randomUUID: () => 'from-random-uuid' });
    expect(generateCheckoutKey()).toBe('from-random-uuid');
  });

  it('falls back to getRandomValues without randomUUID', () => {
    vi.stubGlobal('crypto', {
      getRandomValues: (bytes) => bytes.fill(0xff),
    });
    expect(generateCheckoutKey()).toMatch(UUID_V4);
  });
});
