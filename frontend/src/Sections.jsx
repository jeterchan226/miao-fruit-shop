/* Notices, Packaging, Belief (brand), Contact, Footer */

import { scrollToId } from './Hero.jsx';

const NOTICES = [
  { icon: 'calendar',     title: '產季時間',   body: '每年 7 月下旬至 10 月中旬，依品種陸續採收。建議提前下單，先收訂單先安排出貨。' },
  { icon: 'truck',        title: '出貨時間',   body: '當日上午 11:00 前完成付款的訂單，當日下午採摘包裝、翌日早班宅配出貨。週日不出貨。' },
  { icon: 'file-check',   title: '付款方式',   body: '採銀行轉帳，下單後依轉帳資訊完成付款；五千元以上免運。' },
  { icon: 'box',          title: '配送方式',   body: '使用低溫冷藏宅配 (7–18°C)，全台本島隔日到貨，外島約 2–3 個工作天。' },
  { icon: 'shield-check', title: '保存方式',   body: '收到後請連同原本塑膠袋一起放入冰箱冷藏。冷藏可保存約 10–14 天，常溫請於 3 天內食用完畢。' },
  { icon: 'phone',        title: '售後處理',   body: '若運送途中造成擠壓、軟爛，請於收貨 24 小時內 LINE 拍照通知，我們會立刻補寄或退款。' },
];
import { StoreIcon } from './Icons.jsx';

export const SecTitle = ({ eyebrow, title, sub }) =>
<div className="sec__head">
    {eyebrow && <div className="eyebrow">{eyebrow}</div>}
    <h2><span className="leaf"></span>{title}<span className="leaf r"></span></h2>
    {sub && <p className="sub">{sub}</p>}
  </div>;


export const Rail = () => {
  const I = StoreIcon;
  return (
    <aside className="rail">
      <h4 className="rail__title">🍐 訂購快速資訊</h4>
      <div className="rail__item">
        <span className="rail__chip"><I name="calendar" /></span>
        <div><h4>產季</h4><p>每年 7 月下旬 – 10 月中旬，依品種陸續採收</p></div>
      </div>
      <div className="rail__item">
        <span className="rail__chip"><I name="truck" /></span>
        <div><h4>出貨</h4><p>當日採收，翌日早班宅配出貨</p></div>
      </div>
      <div className="rail__item">
        <span className="rail__chip"><I name="box" /></span>
        <div><h4>運費</h4><p>滿 NT$ 5,000 免運，未滿 150 元</p></div>
      </div>
      <div className="rail__item">
        <span className="rail__chip"><I name="shield-check" /></span>
        <div><h4>運送保障</h4><p>運送途中若有損壞，憑照片補寄或退款</p></div>
      </div>
      <button className="btn btn--sage btn--full rail__btn" onClick={() => scrollToId('notice')}>
        查看完整注意事項 →
      </button>
    </aside>);

};

export const Notices = () => {
  const I = StoreIcon;
  return (
    <section className="sec" id="notice">
      <div className="container">
        <SecTitle eyebrow="ORDER NOTES" title="訂購注意事項" sub="買前先看看這幾件事，確保水梨在最好的狀態下到您家。" />
        <div className="notices">
          {NOTICES.map((n) =>
          <article className="notice" key={n.title}>
              <span className="notice__chip"><I name={n.icon} /></span>
              <h4>{n.title}</h4>
              <p>{n.body}</p>
            </article>
          )}
        </div>
      </div>
    </section>);

};

export const Packaging = ({ variant }) => {
  const I = StoreIcon;
  return (
    <section className={'sec packaging packaging--' + (variant || 'cards')} id="packaging">
      <div className="container" data-comment-anchor="86a2bfcf1b-div-63-7">
        <SecTitle eyebrow="HOW IT ARRIVES" title="包裝展示" sub="每箱都會以雙層紙箱、紙絲、防撞紙托層層保護，收到時就像剛從果園摘下來一樣。" />
        <div className="pack-grid">
          <article className="pack pack--portrait">
            <img src="assets/outside.jpg" alt="" loading="lazy" decoding="async" />
            <div className="pack__cap"><span>外箱：單層禮盒 vs 兩層箱子</span><span className="mono">01 / 05</span></div>
          </article>
          <article className="pack pack--portrait">
            <img src="assets/all_sets.jpg" alt="" loading="lazy" decoding="async" />
            <div className="pack__cap"><span>內裝規格：5 / 6 / 7 粒裝</span><span className="mono">02 / 05</span></div>
          </article>
          <article className="pack">
            <img src="assets/box-2pcs.jpg" alt="" loading="lazy" decoding="async" />
            <div className="pack__cap"><span>禮盒：2 粒精緻禮盒</span><span className="mono">03 / 05</span></div>
          </article>
          <article className="pack">
            <img src="assets/box-2pcs-alt.jpg" alt="" loading="lazy" decoding="async" />
            <div className="pack__cap"><span>內襯：防撞紙托保護</span><span className="mono">04 / 05</span></div>
          </article>
          <div className="pledge">
            <h3>產地直送 · 安心送達</h3>
            <p>當日採收後即刻分裝、低溫宅配。本島隔日到貨、外島 2–3 天送達。</p>
            <div className="pledge__row">
              <div>
                <span className="pledge__icon"><I name="plant" /></span>
                <span className="pledge__lbl">果園採收</span>
              </div>
              <div>
                <span className="pledge__icon"><I name="box" /></span>
                <span className="pledge__lbl">手工分裝</span>
              </div>
              <div>
                <span className="pledge__icon"><I name="truck" /></span>
                <span className="pledge__lbl">隔日到府</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>);

};

export const Belief = () => {
  const I = StoreIcon;
  return (
    <section className="sec" id="about">
      <div className="container">
        <SecTitle eyebrow="OUR STORY" title="妙媽媽果園" sub="一家人在卓蘭山頭種梨二十多年，從嫁接、套袋到採收，每一顆都是用心。" />
        <div className="belief">
          <div className="belief__copy">
            <div className="eyebrow-row">EST. 1998 · 卓蘭</div>
            <h3>來自梨園的好滋味，<br />給家人最安心的美味。</h3>
            <p>
              我們的梨園座落在苗栗卓蘭山頭，海拔 400 公尺，日照足、日夜溫差大，是高接梨最理想的生長環境。
              妙媽媽從嫁接、疏果、套袋到採收，每一步都親手經手，三十年來沒有變過。
            </p>
            <p>
              我們相信好水梨不是靠包裝美，而是靠土地的養分和農夫的耐心。
              產地直送，省去中盤層層轉手，水梨從果園到您家中，最快只要 24 小時。
            </p>
            <p className="belief__sig">— 妙媽媽果園</p>

            <div className="belief__pillars">
              <div className="belief__pillar">
                <span className="chip"><I name="plant" /></span>
                <div>
                  <h5>友善栽培</h5>
                  <p>低農藥、有機肥，讓土地慢慢養出甜度</p>
                </div>
              </div>
              <div className="belief__pillar">
                <span className="chip"><I name="shield-check" /></span>
                <div>
                  <h5>逐顆挑選</h5>
                  <p>外觀、大小、糖度三道把關才裝箱</p>
                </div>
              </div>
              <div className="belief__pillar">
                <span className="chip"><I name="truck" /></span>
                <div>
                  <h5>產地直送</h5>
                  <p>當日採收、隔日到府，最新鮮的狀態</p>
                </div>
              </div>
              <div className="belief__pillar">
                <span className="chip"><I name="file-check" /></span>
                <div>
                  <h5>運送保障</h5>
                  <p>運送途中若有損壞，憑照片補寄或退款</p>
                </div>
              </div>
            </div>
          </div>
          <div className="belief__mosaic">
            <figure className="bphoto bphoto--feature">
              <img src="assets/product_2.jpg" alt="" loading="lazy" decoding="async" />
            </figure>
            <figure className="bphoto">
              <img src="assets/product_3.jpg" alt="" loading="lazy" decoding="async" />
            </figure>
            <figure className="bphoto">
              <img src="assets/product_4.jpg" alt="" loading="lazy" decoding="async" />
            </figure>
            <figure className="bphoto">
              <img src="assets/product_5.jpg" alt="" loading="lazy" decoding="async" />
            </figure>
            <figure className="bphoto">
              <img src="assets/product_6.jpg" alt="" loading="lazy" decoding="async" />
            </figure>
          </div>
        </div>
      </div>
    </section>);

};

export const Contact = () => {
  const I = StoreIcon;
  return (
    <section className="sec" id="contact">
      <div className="container">
        <SecTitle eyebrow="GET IN TOUCH" title="聯絡我們" sub="任何訂單、配送、商品問題，歡迎透過下列方式聯繫，我們儘速回覆您。" />
        <div className="contact-band">
          <div className="contact-band__left">
            <div className="eyebrow-row">CONTACT</div>
            <h3>有任何問題，<br />歡迎隨時來訊。</h3>
            <p className="lede">
              想諮詢產季、訂購狀況，或想了解我們果園的話，最方便的方式是加 LINE。
              我們會親自回覆您。
            </p>
            <div className="contact-band__rows">
              <a className="contact-row">
                <span className="contact-row__chip line"><I name="line" size={22} /></span>
                <div style={{ flex: 1 }}>
                  <p className="contact-row__k">LINE 官方帳號（最快回覆）</p>
                  <p className="contact-row__v">@475dhpfn</p>
                </div>
                <span className="pill pill--sage">加入好友</span>
              </a>
              <a className="contact-row">
                <span className="contact-row__chip"><I name="phone" /></span>
                <div style={{ flex: 1 }}>
                  <p className="contact-row__k">客服電話</p>
                  <p className="contact-row__v mono">0910-567-118</p>
                </div>
                <span className="pill pill--ghost">9:00 – 18:00</span>
              </a>
              <a className="contact-row">
                <span className="contact-row__chip"><I name="pin" /></span>
                <div style={{ flex: 1 }}>
                  <p className="contact-row__k">果園地址</p>
                  <p className="contact-row__v">苗栗縣卓蘭鎮雙連45號</p>
                </div>
                <span className="pill pill--ghost" data-comment-anchor="f88aa2f6e1-span-213-17">僅供出貨</span>
              </a>
              <a className="contact-row">
                <span className="contact-row__chip"><I name="clock" /></span>
                <div style={{ flex: 1 }}>
                  <p className="contact-row__k">產季營業時間</p>
                  <p className="contact-row__v">星期一～星期四</p>
                </div>
                <span className="pill pill--ghost">產季限定</span>
              </a>
            </div>
          </div>
          <div className="contact-band__right">
            <div className="contact-band__stamp">
              <span className="dot"></span>
              產季中 · 接單出貨中
            </div>
          </div>
        </div>
      </div>
    </section>);

};

export const Footer = () => {
  const I = StoreIcon;
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer__grid">
          <div className="footer__brand">
            <p className="mark">🍐 妙媽媽果園</p>
            <p className="tag">來自梨園的好滋味</p>
            <p className="blurb">
              卓蘭高接梨產地直送，<br />三十年用心栽培，<br />給家人最安心的美味。
            </p>
            <span className="footer__pill">EST. 1998 · MIAOLI</span>
          </div>
          <div className="footer__col">
            <h5>商品</h5>
            <ul>
              <li><a>甘露梨</a></li>
            </ul>
          </div>
          <div className="footer__col">
            <h5>訂購服務</h5>
            <ul>
              <li><a>注意事項</a></li>
              <li><a>付款方式</a></li>
              <li><a>配送方式</a></li>
              <li><a>保存方式</a></li>
            </ul>
          </div>
          <div className="footer__col">
            <h5>關於我們</h5>
            <ul>
              <li><a>品牌故事</a></li>
              <li><a>果園介紹</a></li>
              <li><a></a></li>
            </ul>
          </div>
          <div className="footer__col">
            <h5>聯絡資訊</h5>
            <p>LINE @475dhpfn<br />TEL 0910-567-118<br />苗栗縣卓蘭鎮<br />雙連45號</p>
          </div>
          <div className="footer__socials" style={{ flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <a className="footer__social line" href="https://page.line.me/475dhpfn" target="_blank" rel="noreferrer" aria-label="LINE 官方帳號" title="LINE" style={{ textDecoration: 'none' }}>
                <I name="line" size={18} />
              </a>
            </div>
          </div>
        </div>
        <div className="footer__bottom">
          <span>© 2026 妙媽媽果園 Miao Mama Orchard. All rights reserved.</span>
          <span className="links">
            <a>隱私權政策</a>
            <a>使用條款</a>
            <a>退換貨說明</a>
            <a>網站地圖</a>
          </span>
        </div>
      </div>
    </footer>);

};
