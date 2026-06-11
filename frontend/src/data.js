/* 妙媽媽果園 — 商品資料 */

const PRODUCTS = [
  {
    id: 'kanro',
    name: '甘露梨',
    sub: 'Kanro · 蜜糖之味',
    desc: '園區珍稀品種，產量稀少，蜜香濃郁、入口即化，識貨的老客戶才點。',
    image: 'assets/product_5.jpg',
    season: '10 月上旬 – 10 月中旬',
    tag: '珍稀',
    tagColor: 'red',
    specs: [
      { id: 's1', label: '2 粒精緻禮盒', qty: '2 顆 · 約 1.6 台斤', price: 880, stock: 'in', note: '蜜糖之味' },
      { id: 's2', label: '5 台斤家庭箱', qty: '6–8 顆 · 5 台斤', price: 1880, stock: 'low', note: '剩 3 箱' },
      { id: 's3', label: '10 台斤大箱',  qty: '12–16 顆 · 10 台斤', price: 3580, stock: 'in', note: '老客戶限定' },
    ],
  },
];

const NOTICES = [
  { icon: 'calendar', title: '產季時間', body: '每年 7 月下旬至 10 月中旬，依品種陸續採收。建議提前下單，先收訂單先安排出貨。' },
  { icon: 'truck',    title: '出貨時間', body: '當日上午 11:00 前完成付款的訂單，當日下午採摘包裝、翌日早班宅配出貨。週日不出貨。' },
  { icon: 'file-check', title: '付款方式', body: 'LINE Pay、信用卡、ATM 轉帳、銀行匯款，五千元以上免運。' },
  { icon: 'box',      title: '配送方式', body: '使用低溫冷藏宅配 (7–18°C)，全台本島隔日到貨，外島約 2–3 個工作天。' },
  { icon: 'shield-check', title: '保存方式', body: '收到後請連同原本塑膠袋一起放入冰箱冷藏。冷藏可保存約 10–14 天，常溫請於 3 天內食用完畢。' },
  { icon: 'phone',    title: '售後處理', body: '若運送途中造成擠壓、軟爛，請於收貨 24 小時內 LINE 拍照通知，我們會立刻補寄或退款。' },
];

window.PRODUCTS = PRODUCTS;
window.NOTICES  = NOTICES;
