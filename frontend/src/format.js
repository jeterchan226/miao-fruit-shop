/* 顯示用格式化 */

// 金額:3520 → "NT$ 3,520"
export const money = (n) => `NT$ ${Number(n || 0).toLocaleString()}`;
