/* 顧客/收件資訊驗證 — 顧客下單(商店頁購物車)與代客下單(後台)共用同一套規則 */

export const getTomorrowStr = (now = new Date()) => {
  const d = new Date(now);
  d.setDate(d.getDate() + 1);
  return d.toISOString().split('T')[0];
};

const PHONE_PATTERN = /^[0-9\-\s]{8,}$/;

/*
 * fields: { name, phone, city, district, street, preferredDate }
 * savedDate — 編輯既有訂單時的原送達日;維持原值不受「不得早於明天」限制,改日期才檢查。
 * 回傳以欄位為 key 的錯誤訊息;全部合法時為空物件。後端仍會再驗一次。
 */
export function validateCustomerShipping(fields, now = new Date(), { savedDate } = {}) {
  const e = {};
  const text = (v) => (v ?? '').trim();
  const { preferredDate } = fields;
  const name = text(fields.name);
  const phone = text(fields.phone);
  if (!name) e.name = '請輸入姓名';
  if (!phone) e.phone = '請輸入電話';
  else if (!PHONE_PATTERN.test(phone)) e.phone = '電話格式不正確';
  if (!text(fields.city)) e.city = '請選擇縣市';
  if (!text(fields.district)) e.district = '請選擇區域';
  if (!text(fields.street)) e.street = '請輸入詳細地址';
  if (!preferredDate) {
    e.preferredDate = '請選擇送達日期';
  } else {
    const entered  = new Date(preferredDate + 'T00:00:00');
    const tomorrow = new Date(getTomorrowStr(now) + 'T00:00:00');
    if (isNaN(entered.getTime())) e.preferredDate = '日期無效，請重新選擇';
    else if (entered < tomorrow && preferredDate !== savedDate) {
      e.preferredDate = '送達日不得早於明天';
    }
  }
  return e;
}
