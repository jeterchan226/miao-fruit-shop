// 純邏輯：通知中心的相對時間、未讀計算、新單偵測。
// 無 DOM、無 localStorage、無副作用，便於單元測試。

export function formatRelativeTime(iso, nowMs = Date.now()) {
  const then = new Date(iso).getTime();
  const diffSec = Math.max(0, Math.floor((nowMs - then) / 1000));
  if (diffSec < 60) return '剛剛';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} 分鐘前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} 小時前`;
  const diffDay = Math.floor(diffHour / 24);
  return `${diffDay} 天前`;
}

export function isAfter(aIso, bIso) {
  if (!aIso || !bIso) return false;
  return new Date(aIso).getTime() > new Date(bIso).getTime();
}

export function newestCreatedAt(orders) {
  if (!orders || orders.length === 0) return null;
  return orders.reduce(
    (max, o) =>
      max === null || new Date(o.created_at).getTime() > new Date(max).getTime()
        ? o.created_at
        : max,
    null,
  );
}

export function unreadOrders(orders, lastReadAtIso) {
  if (!orders || !lastReadAtIso) return [];
  return orders.filter((o) => isAfter(o.created_at, lastReadAtIso));
}
