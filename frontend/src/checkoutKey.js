/* Idempotency key for storefront order submission. */

// crypto.randomUUID 需 Safari 15.4+ 且僅限 secure context，iPadOS 15 底線要有 fallback
export const generateCheckoutKey = () => {
  if (crypto.randomUUID) return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
};

// key 綁訂單內容：內容未變的重試沿用，內容改變換新 key
export const nextCheckoutKey = (previous, payload) => {
  const fingerprint = JSON.stringify(payload);
  if (previous?.fingerprint === fingerprint) return previous;
  return { key: generateCheckoutKey(), fingerprint };
};
