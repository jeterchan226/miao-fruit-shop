const LIFF_SDK_URL = 'https://static.line-scdn.net/liff/edge/2/sdk.js';

let sdkPromise = null;

const getLiffId = () => {
  const configured = window.MIAO_LIFF_ID || import.meta.env.VITE_MIAO_LIFF_ID;
  return configured && configured.trim() ? configured.trim() : '';
};

const getAddFriendUrl = () => {
  const configured =
    window.MIAO_LINE_ADD_FRIEND_URL || import.meta.env.VITE_MIAO_LINE_ADD_FRIEND_URL;
  return configured && configured.trim() ? configured.trim() : '';
};

const loadLiffSdk = () => {
  if (window.liff) return Promise.resolve(window.liff);
  if (sdkPromise) return sdkPromise;

  sdkPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${LIFF_SDK_URL}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(window.liff), { once: true });
      existing.addEventListener('error', reject, { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = LIFF_SDK_URL;
    script.async = true;
    script.onload = () => resolve(window.liff);
    script.onerror = reject;
    document.head.appendChild(script);
  });
  return sdkPromise;
};

export const initLineProfile = async () => {
  const liffId = getLiffId();
  if (!liffId) {
    return {
      available: false,
      status: 'not_configured',
      profile: null,
      friendshipStatus: 'unknown',
    };
  }

  const liff = await loadLiffSdk();
  await liff.init({ liffId, withLoginOnExternalBrowser: true });

  if (!liff.isLoggedIn()) {
    liff.login();
    return {
      available: true,
      status: 'login_redirect',
      profile: null,
      friendshipStatus: 'unknown',
    };
  }

  const profile = await liff.getProfile();
  let friendshipStatus = 'unknown';
  try {
    const friendship = await liff.getFriendship();
    friendshipStatus = friendship.friendFlag ? 'friend' : 'not_friend';
  } catch (_err) {
    friendshipStatus = 'unknown';
  }

  return {
    available: true,
    status: 'bound',
    profile,
    friendshipStatus,
  };
};

// LIFF SDK 沒有 requestFriendship API；加好友的正規做法是開啟官方帳號的加好友連結。
export const openLineAddFriend = () => {
  const url = getAddFriendUrl();
  if (!url) return false;
  if (window.liff?.openWindow) {
    window.liff.openWindow({ url, external: true });
  } else {
    window.open(url, '_blank', 'noopener');
  }
  return true;
};

// 使用者從加好友頁返回後，重新查詢最新好友狀態。
export const refreshLineFriendship = async () => {
  if (!window.liff?.isLoggedIn || !window.liff.isLoggedIn()) return 'unknown';
  try {
    const friendship = await window.liff.getFriendship();
    return friendship.friendFlag ? 'friend' : 'not_friend';
  } catch (_err) {
    return 'unknown';
  }
};
