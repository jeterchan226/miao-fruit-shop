/* 後台訂單日期篩選 → 後端 UTC 時間範圍(ADR 0005)
   後端只認 timezone-aware 的 UTC 時點;「哪一天」由這裡依瀏覽器當前時區換算。
   起日 00:00(含)→ created_from;迄日隔天 00:00(不含)→ created_before。 */

// 'YYYY-MM-DD' 在瀏覽器時區的當日 00:00(Date 本地建構子會處理 DST)
const localMidnight = (dateStr, addDays = 0) => {
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d + addDays);
};

export function localDateRangeToUtc({ dateFrom, dateTo } = {}) {
  const params = {};
  if (dateFrom) params.created_from = localMidnight(dateFrom).toISOString();
  if (dateTo) params.created_before = localMidnight(dateTo, 1).toISOString();
  return params;
}
