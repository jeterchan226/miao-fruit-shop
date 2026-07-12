import { useCallback, useEffect, useRef, useState } from 'react';
import { listAdminOrders } from './api.js';
import { createChime } from './chime.js';
import { isAfter, newestCreatedAt, unreadOrders } from './notifications.js';

const LAST_READ_KEY = 'admin_notif_last_read_at';
const SOUND_KEY = 'admin_notif_sound_on';
// 輪詢間隔:5 秒。櫃檯平板長開,新單最多 5 秒內就會被偵測到並發聲/跳橫幅。
const POLL_MS = 5000;
const RECENT_SIZE = 10;

export function useOrderNotifications({ token, onAuthError }) {
  const [recentOrders, setRecentOrders] = useState([]);
  const [lastReadAt, setLastReadAt] = useState(
    () => localStorage.getItem(LAST_READ_KEY) || null,
  );
  const [soundOn, setSoundOn] = useState(
    () => localStorage.getItem(SOUND_KEY) !== 'off',
  );

  const chimeRef = useRef(null);
  if (chimeRef.current === null) chimeRef.current = createChime();
  const prevNewestRef = useRef(null);
  const soundOnRef = useRef(soundOn);
  const unlockedRef = useRef(false);

  useEffect(() => {
    soundOnRef.current = soundOn;
  }, [soundOn]);

  const persistLastRead = useCallback((iso) => {
    if (!iso) return;
    setLastReadAt(iso);
    localStorage.setItem(LAST_READ_KEY, iso);
  }, []);

  const poll = useCallback(async () => {
    if (!token) return;
    let data;
    try {
      data = await listAdminOrders(token, { page: 1, page_size: RECENT_SIZE });
    } catch (err) {
      if (err?.status === 401) onAuthError?.();
      return;
    }
    const items = data.items || [];
    setRecentOrders(items);
    const newest = newestCreatedAt(items);

    // 首次：以最新訂單初始化基準，不發聲；無標記時順便初始化已讀標記。
    if (prevNewestRef.current === null) {
      prevNewestRef.current = newest;
      if (!localStorage.getItem(LAST_READ_KEY) && newest) persistLastRead(newest);
      return;
    }
    // 出現更新的訂單 → 發聲（需已解鎖音訊且開啟）。
    if (isAfter(newest, prevNewestRef.current)) {
      if (unlockedRef.current && soundOnRef.current) chimeRef.current.play();
    }
    prevNewestRef.current = newest;
  }, [token, onAuthError, persistLastRead]);

  // 輪詢：立即一次 + 每 POLL_MS。
  useEffect(() => {
    if (!token) return undefined;
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [token, poll]);

  // Wake Lock：前景時保持螢幕不睡，回前景時重新取得。
  useEffect(() => {
    if (!token) return undefined;
    let wakeLock = null;
    const request = async () => {
      try {
        if ('wakeLock' in navigator && document.visibilityState === 'visible') {
          wakeLock = await navigator.wakeLock.request('screen');
        }
      } catch {
        /* 不支援或被拒則略過 */
      }
    };
    const onVis = () => {
      if (document.visibilityState === 'visible') request();
    };
    request();
    document.addEventListener('visibilitychange', onVis);
    return () => {
      document.removeEventListener('visibilitychange', onVis);
      if (wakeLock) wakeLock.release().catch(() => {});
    };
  }, [token]);

  const unlockAudio = useCallback(() => {
    unlockedRef.current = true;
    chimeRef.current.unlock();
  }, []);

  const toggleSound = useCallback(() => {
    setSoundOn((on) => {
      const next = !on;
      localStorage.setItem(SOUND_KEY, next ? 'on' : 'off');
      return next;
    });
  }, []);

  const markRead = useCallback(
    (order) => {
      if (order?.created_at && isAfter(order.created_at, lastReadAt)) {
        persistLastRead(order.created_at);
      }
    },
    [lastReadAt, persistLastRead],
  );

  const markAllRead = useCallback(() => {
    const newest = newestCreatedAt(recentOrders);
    if (newest) persistLastRead(newest);
  }, [recentOrders, persistLastRead]);

  const unread = unreadOrders(recentOrders, lastReadAt);

  return {
    recentOrders,
    unread,
    unreadCount: unread.length,
    soundOn,
    toggleSound,
    unlockAudio,
    markRead,
    markAllRead,
    refresh: poll,
  };
}
