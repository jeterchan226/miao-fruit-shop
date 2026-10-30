// 純邏輯：通知中心的相對時間、未讀計算、新單偵測。
// 無 DOM、無 localStorage、無副作用，便於單元測試。

// 代客下單是管理員自己建的，不提醒（鈴聲、未讀、新訂單橫幅），也不推進已讀標記。
export function isCustomerOrder(order) {
  return order.source !== 'admin';
}

function customerOrders(orders) {
  return orders.filter(isCustomerOrder);
}

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

// 顧客下單中最新的 created_at；全為代客下單或空時為 null。
export function newestCreatedAt(orders) {
  if (!orders) return null;
  return customerOrders(orders).reduce(
    (max, o) => (max === null || isAfter(o.created_at, max) ? o.created_at : max),
    null,
  );
}

export function unreadOrders(orders, lastReadAtIso) {
  if (!orders || !lastReadAtIso) return [];
  return customerOrders(orders).filter((o) => isAfter(o.created_at, lastReadAtIso));
}

// recentOrders 中 created_at 嚴格晚於 sinceIso 的顧客下單。
// sinceIso 為 falsy（表格空、無基準）時，全部視為新。
export function newOrdersSince(recentOrders, sinceIso) {
  if (!recentOrders) return [];
  const customer = customerOrders(recentOrders);
  if (!sinceIso) return customer;
  return customer.filter((o) => isAfter(o.created_at, sinceIso));
}

const EPOCH_ISO = new Date(0).toISOString();

// 一次輪詢的判斷。state 為 null 表示尚未輪詢過；否則 newest 是上次的最新顧客下單時間（可為 null）。
// 回傳下一個 state、是否響鈴，以及要初始化的已讀標記（不需初始化時為 null）。
export function evaluatePoll(state, orders, hasLastRead) {
  const newest = newestCreatedAt(orders);
  if (state === null) {
    // 首次：不響鈴。newest 為 null（無訂單或全為代客下單）時以 epoch 為已讀標記，之後的顧客下單都算未讀。
    return {
      state: { newest },
      chime: false,
      initLastReadAt: hasLastRead ? null : newest || EPOCH_ISO,
    };
  }
  const chime = Boolean(newest) && (state.newest === null || isAfter(newest, state.newest));
  return { state: { newest }, chime, initLastReadAt: null };
}
