import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('createOrder', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue({ ok: true, text: async () => '{"order_no":"MM-AAAAAA"}' });
    // api.js 載入時就會寫 window,須先 stub 再 import
    vi.stubGlobal('window', { location: { hostname: 'shop.test', protocol: 'https:' } });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sends the Idempotency-Key header', async () => {
    const { createOrder } = await import('./api.js');

    await createOrder({ note: null }, 'key-1');

    const [path, options] = fetchMock.mock.calls[0];
    expect(path).toBe('/api/orders');
    expect(options.method).toBe('POST');
    expect(options.headers['Idempotency-Key']).toBe('key-1');
  });
});
