/* Cart drawer + multi-step checkout (data → payment → done) */

import { useEffect, useMemo, useState } from 'react';

import { createOrder } from './api.js';
import { StoreIcon } from './Icons.jsx';

const FREE_SHIPPING = 5000;
const SHIPPING_FEE  = 150;

const getTomorrowStr = () => {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().split('T')[0];
};

const formatDateDisplay = (s) => {
  if (!s) return '';
  const [y, m, d] = s.split('-');
  return `${y}年 ${parseInt(m)}月 ${parseInt(d)}日`;
};

/* ── Date Picker Sheet ─────────────────────────────────────── */

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六'];

const DatePickerSheet = ({ value, onSelect, onClose }) => {
  const today    = new Date();
  const tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
  const maxDate  = new Date(today.getFullYear(), today.getMonth() + 6, today.getDate());

  const initDate   = value ? new Date(value + 'T00:00:00') : tomorrow;
  const [viewYear,  setViewYear]  = useState(initDate.getFullYear());
  const [viewMonth, setViewMonth] = useState(initDate.getMonth());

  const prevMonth = () => {
    if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11); }
    else setViewMonth(viewMonth - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0); }
    else setViewMonth(viewMonth + 1);
  };

  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const firstDay    = new Date(viewYear, viewMonth, 1).getDay();
  const cells       = Array(firstDay).fill(null).concat(
    Array.from({ length: daysInMonth }, (_, i) => i + 1)
  );

  const selParts  = value ? value.split('-').map(Number) : null;
  const isSelected = (d) =>
    d && selParts &&
    selParts[0] === viewYear && selParts[1] - 1 === viewMonth && selParts[2] === d;

  const isDisabled = (d) => {
    if (!d) return true;
    const date = new Date(viewYear, viewMonth, d);
    return date < tomorrow || date > maxDate;
  };

  const handleDay = (d) => {
    if (isDisabled(d)) return;
    const m  = String(viewMonth + 1).padStart(2, '0');
    const dd = String(d).padStart(2, '0');
    onSelect(`${viewYear}-${m}-${dd}`);
  };

  const canPrev = new Date(viewYear, viewMonth, 0) >= tomorrow;
  const canNext = new Date(viewYear, viewMonth + 1, 1) <= maxDate;

  return (
    <>
      <div className="bs-scrim" onClick={onClose} />
      <div className="bottom-sheet dp-sheet">
        <div className="bs-handle" />
        <div className="dp-header">
          <button type="button" className="dp-nav" onClick={prevMonth} disabled={!canPrev}>‹</button>
          <span className="dp-month">{viewYear}年 {viewMonth + 1}月</span>
          <button type="button" className="dp-nav" onClick={nextMonth} disabled={!canNext}>›</button>
        </div>
        <div className="dp-grid">
          {WEEKDAYS.map(w => <div key={w} className="dp-wd">{w}</div>)}
          {cells.map((d, i) => (
            <button
              key={i}
              type="button"
              className={'dp-day' + (isSelected(d) ? ' is-selected' : '') + (isDisabled(d) ? ' is-disabled' : '')}
              onClick={() => handleDay(d)}
            >{d || ''}</button>
          ))}
        </div>
        <div className="dp-footer-pad" />
      </div>
    </>
  );
};

/* ── Bottom Sheet ──────────────────────────────────────────── */

const BottomSheet = ({ open, title, items, selected, onSelect, onClose }) => {
  if (!open) return null;
  return (
    <>
      <div className="bs-scrim" onClick={onClose} />
      <div className="bottom-sheet">
        <div className="bs-handle" />
        <div className="bs-header">
          <span className="bs-title">{title}</span>
          <button className="bs-close" type="button" onClick={onClose}>×</button>
        </div>
        <div className="bs-list">
          {items.map(item => (
            <button
              key={item}
              type="button"
              className={'bs-item' + (item === selected ? ' is-active' : '')}
              onClick={() => onSelect(item)}
            >{item}</button>
          ))}
        </div>
      </div>
    </>
  );
};

/* ── Cart Item ─────────────────────────────────────────────── */

const CartItem = ({ item, onQty, onRemove }) => (
  <div className="cart-item">
    <div className="cart-item__img" style={{backgroundImage:`url(${item.image})`}}></div>
    <div>
      <p className="cart-item__t">{item.name}</p>
      <p className="cart-item__s">{item.specLabel} · {item.qty}</p>
      <div className="cart-item__row">
        <div className="qty">
          <button onClick={() => onQty(item.lineId, item.count - 1)} aria-label="減少">−</button>
          <span className="v">{item.count}</span>
          <button onClick={() => onQty(item.lineId, item.count + 1)} aria-label="增加">+</button>
        </div>
        <button className="cart-item__rm" onClick={() => onRemove(item.lineId)}>移除</button>
      </div>
    </div>
    <span className="cart-item__price">NT$ {(item.price * item.count).toLocaleString()}</span>
  </div>
);

const Empty = ({ onBrowse }) => {
  const I = StoreIcon;
  return (
    <div className="drawer__empty">
      <span className="ill"><I name="cart" size={42} stroke={1.4} /></span>
      <h4>購物車是空的</h4>
      <p>來看看現在正當季的水梨吧 🍐</p>
      <button className="btn btn--sage" onClick={onBrowse}>逛逛商品</button>
    </div>
  );
};

const Steps = ({ step }) => (
  <div className="checkout__steps">
    <span className={'s ' + (step === 'cart' ? 'is-active' : 'is-done')}>
      <span className="n">1</span>確認商品
    </span>
    <span className="div"></span>
    <span className={'s ' + (step === 'info' ? 'is-active' : (step === 'pay' || step === 'done' ? 'is-done' : ''))}>
      <span className="n">2</span>收件資料
    </span>
    <span className="div"></span>
    <span className={'s ' + (step === 'pay' ? 'is-active' : (step === 'done' ? 'is-done' : ''))}>
      <span className="n">3</span>付款方式
    </span>
    <span className="div"></span>
    <span className={'s ' + (step === 'done' ? 'is-active' : '')}>
      <span className="n">✓</span>完成
    </span>
  </div>
);

/* ── Info Form ─────────────────────────────────────────────── */

const InfoForm = ({ form, setForm, errors }) => {
  const set = (k, v) => setForm({ ...form, [k]: v });
  const [sheet,  setSheet]  = useState(null);   // null | 'city' | 'district'
  const [dpOpen, setDpOpen] = useState(false);

  const zipData  = window.TW_ZIPCODE || {};
  const cities   = Object.keys(zipData);
  const districts = form.city ? Object.keys(zipData[form.city] || {}) : [];

  const onCitySelect = (city) => {
    setForm({ ...form, city, district: '', zipcode: '' });
    setSheet(null);
  };

  const onDistrictSelect = (district) => {
    const zipcode = (zipData[form.city] || {})[district] || '';
    setForm({ ...form, district, zipcode });
    setSheet(null);
  };

  return (
    <div style={{display:'flex', flexDirection:'column', gap:14}}>

      {/* Date picker + bottom sheets — position:fixed, renders above drawer */}
      {dpOpen && (
        <DatePickerSheet
          value={form.ship}
          onSelect={(date) => { set('ship', date); setDpOpen(false); }}
          onClose={() => setDpOpen(false)}
        />
      )}
      <BottomSheet
        open={sheet === 'city'}
        title="選擇縣市"
        items={cities}
        selected={form.city}
        onSelect={onCitySelect}
        onClose={() => setSheet(null)}
      />
      <BottomSheet
        open={sheet === 'district'}
        title="選擇區域"
        items={districts}
        selected={form.district}
        onSelect={onDistrictSelect}
        onClose={() => setSheet(null)}
      />

      {/* Name + Phone */}
      <div className="field--row">
        <div className="field">
          <label>收件人姓名 <span className="req">*</span></label>
          <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="王小明" />
          {errors.name && <span className="err">{errors.name}</span>}
        </div>
        <div className="field">
          <label>聯絡電話 <span className="req">*</span></label>
          <input value={form.phone} onChange={e => set('phone', e.target.value)} placeholder="0912-345-678" inputMode="tel" />
          {errors.phone && <span className="err">{errors.phone}</span>}
        </div>
      </div>

      {/* Email */}
      <div className="field">
        <label>E-mail（出貨通知）</label>
        <input value={form.email} onChange={e => set('email', e.target.value)} placeholder="you@example.com" inputMode="email" />
      </div>

      {/* Address */}
      <div className="field">
        <label>收件地址 <span className="req">*</span></label>
        <div className="field--row" style={{marginBottom:8}}>
          <div className="field">
            <button
              type="button"
              className={'addr-btn' + (!form.city ? ' addr-btn--empty' : '')}
              onClick={() => setSheet('city')}
            >
              <span>{form.city || '請選擇縣市'}</span>
              <span className="addr-btn__arrow">▾</span>
            </button>
            {errors.city && <span className="err">{errors.city}</span>}
          </div>
          <div className="field">
            <button
              type="button"
              className={'addr-btn' + (!form.district ? ' addr-btn--empty' : '') + (!form.city ? ' addr-btn--disabled' : '')}
              onClick={() => { if (form.city) setSheet('district'); }}
              disabled={!form.city}
            >
              <span>{form.district || '請選擇區域'}</span>
              <span className="addr-btn__arrow">▾</span>
            </button>
            {errors.district && <span className="err">{errors.district}</span>}
          </div>
        </div>
        {form.zipcode && (
          <div className="zipcode-tag">郵遞區號：{form.zipcode}</div>
        )}
        <input
          value={form.street}
          onChange={e => set('street', e.target.value)}
          placeholder="路／街／巷／弄／號／樓"
        />
        {errors.street && <span className="err">{errors.street}</span>}
      </div>

      {/* Delivery date + time window */}
      <div className="field--row date-row">
        <div className="field">
          <label>希望送達日 <span className="req">*</span></label>
          <button
            type="button"
            className={'addr-btn' + (!form.ship ? ' addr-btn--empty' : '')}
            onClick={() => setDpOpen(true)}
          >
            <span>{form.ship ? formatDateDisplay(form.ship) : '請選擇日期'}</span>
            <span className="addr-btn__arrow">▾</span>
          </button>
          {errors.ship && <span className="err">{errors.ship}</span>}
        </div>
        <div className="field">
          <label>送達時段</label>
          <div className="window-opts">
            {[
              { v: 'any', l: '不指定' },
              { v: 'am',  l: '上午 9–13' },
              { v: 'pm',  l: '下午 14–18' },
            ].map(opt => (
              <button
                key={opt.v}
                type="button"
                className={'window-opt' + (form.window === opt.v ? ' is-active' : '')}
                onClick={() => set('window', opt.v)}
              >{opt.l}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Notes */}
      <div className="field">
        <label>備註（送禮卡片、特殊需求）</label>
        <textarea value={form.note} onChange={e => set('note', e.target.value)} placeholder="如為送禮，請告訴我們收禮人稱呼與祝福語。" />
      </div>
    </div>
  );
};

/* ── Pay Form ──────────────────────────────────────────────── */

const PayForm = ({ pay, setPay, form }) => {
  const fullAddress = form.city
    ? `${form.zipcode} ${form.city}${form.district}${form.street}`
    : '—';
  return (
    <div style={{display:'flex', flexDirection:'column', gap:14}}>
      <div className="pay-opts">
        <label className={'pay-opt' + (pay === 'linepay' ? ' is-active' : '')}>
          <input type="radio" checked={pay === 'linepay'} onChange={() => setPay('linepay')} />
          <div style={{flex:1}}>
            <p className="pay-opt__t">LINE Pay</p>
            <p className="pay-opt__s">點付款後自動轉至 LINE Pay 結帳</p>
          </div>
          <span className="pill pill--sage" style={{background:'#06C755'}}>推薦</span>
        </label>
        <label className={'pay-opt' + (pay === 'card' ? ' is-active' : '')}>
          <input type="radio" checked={pay === 'card'} onChange={() => setPay('card')} />
          <div style={{flex:1}}>
            <p className="pay-opt__t">信用卡</p>
            <p className="pay-opt__s">VISA / MasterCard / JCB</p>
          </div>
        </label>
        <label className={'pay-opt' + (pay === 'atm' ? ' is-active' : '')}>
          <input type="radio" checked={pay === 'atm'} onChange={() => setPay('atm')} />
          <div style={{flex:1}}>
            <p className="pay-opt__t">ATM 轉帳</p>
            <p className="pay-opt__s">下單後取得虛擬帳號，3 天內完成轉帳</p>
          </div>
        </label>
        <label className={'pay-opt' + (pay === 'cod' ? ' is-active' : '')}>
          <input type="radio" checked={pay === 'cod'} onChange={() => setPay('cod')} />
          <div style={{flex:1}}>
            <p className="pay-opt__t">貨到付款</p>
            <p className="pay-opt__s">運費另加 NT$ 30</p>
          </div>
        </label>
      </div>
      <div className="checkout-summary">
        <h5>寄送資訊</h5>
        <div className="ln"><span className="t">收件人</span><span>{form.name || '—'}</span></div>
        <div className="ln"><span className="t">電話</span><span>{form.phone || '—'}</span></div>
        <div className="ln"><span className="t">地址</span><span style={{maxWidth:'60%', textAlign:'right'}}>{fullAddress}</span></div>
        <div className="ln"><span className="t">送達日</span><span>{form.ship || '—'}</span></div>
      </div>
    </div>
  );
};

/* ── Checkout Page ─────────────────────────────────────────── */

const CheckoutPage = ({
  step, form, setForm, errors, pay, setPay,
  subtotal, shipping, codFee, total,
  submitting, submitError,
  onBack, onNext, onClose,
}) => {
  useEffect(() => {
    const scrollY = window.scrollY;
    document.body.style.cssText =
      `overflow:hidden;position:fixed;top:-${scrollY}px;width:100%;`;
    return () => {
      document.body.style.cssText = '';
      window.scrollTo(0, scrollY);
    };
  }, []);

  return (
    <div className="checkout-page">
      <div className="checkout-page__head">
        <button className="checkout-page__back" type="button" onClick={onBack}>‹ 返回</button>
        <Steps step={step} />
        <button className="checkout-page__close" type="button" onClick={onClose}>×</button>
      </div>
      <div className="checkout-page__body">
        <div className="checkout-page__inner">
          {step === 'info' && <InfoForm form={form} setForm={setForm} errors={errors} />}
          {step === 'pay'  && <PayForm  pay={pay}  setPay={setPay}  form={form} />}
          <div className="order-card">
            <div className="order-card__row">
              <span>商品小計</span>
              <span>NT$ {subtotal.toLocaleString()}</span>
            </div>
            <div className="order-card__row">
              <span>運費</span>
              <span>{shipping === 0 ? '免運 🍐' : `NT$ ${shipping.toLocaleString()}`}</span>
            </div>
            {codFee > 0 && (
              <div className="order-card__row">
                <span>貨到付款手續費</span>
                <span>NT$ {codFee}</span>
              </div>
            )}
            <div className="order-card__total">
              <span>訂單合計</span>
              <strong>NT$ {total.toLocaleString()}</strong>
            </div>
          </div>
          <div className="checkout-page__actions">
            <button className="btn btn--ghost co-back" type="button" onClick={onBack}>上一步</button>
            <button className="btn btn--primary co-next" type="button" onClick={onNext} disabled={submitting}>
              {submitting ? '送出中...' : (step === 'info' ? '下一步：選擇付款' : '送出訂單')}
            </button>
          </div>
          {submitError && <div className="checkout-error">{submitError}</div>}
        </div>
      </div>
    </div>
  );
};

/* ── Cart Drawer ───────────────────────────────────────────── */

export const CartDrawer = ({ open, onClose, items, onQty, onRemove, onPlaceOrder }) => {
  const [step, setStep]       = useState('cart');
  const [form, setForm]       = useState({
    name: '', phone: '', email: '',
    city: '', district: '', zipcode: '', street: '',
    ship: getTomorrowStr(), window: 'any', note: ''
  });
  const [errors, setErrors]   = useState({});
  const [pay, setPay]         = useState('linepay');
  const [orderId, setOrderId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    if (open && items.length === 0 && step !== 'cart' && step !== 'done') setStep('cart');
  }, [open, items.length]);

  const subtotal = useMemo(() => items.reduce((s, i) => s + i.price * i.count, 0), [items]);
  const shipping = subtotal === 0 ? 0 : (subtotal >= FREE_SHIPPING ? 0 : SHIPPING_FEE);
  const codFee   = pay === 'cod' && step === 'pay' ? 30 : 0;
  const total    = subtotal + shipping + codFee;

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = '請輸入姓名';
    if (!form.phone.trim()) e.phone = '請輸入電話';
    else if (!/^[0-9\-\s]{8,}$/.test(form.phone)) e.phone = '電話格式不正確';
    if (!form.city) e.city = '請選擇縣市';
    if (!form.district) e.district = '請選擇區域';
    if (!form.street.trim()) e.street = '請輸入詳細地址';
    if (!form.ship) {
      e.ship = '請選擇送達日期';
    } else {
      const entered  = new Date(form.ship + 'T00:00:00');
      const tomorrow = new Date(getTomorrowStr() + 'T00:00:00');
      if (isNaN(entered.getTime())) e.ship = '日期無效，請重新選擇';
      else if (entered < tomorrow)  e.ship = '送達日不得早於明天';
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const formatApiError = (err) => {
    const data = err?.data || {};
    if (err?.code === 'PRICE_CHANGED') {
      return `商品價格已更新，新的訂單合計為 NT$ ${Number(data.total || 0).toLocaleString()}，請重新確認後再送出。`;
    }
    if (err?.code === 'INSUFFICIENT_STOCK') return data.detail || '庫存不足，請調整購買數量。';
    if (err?.code === 'NOT_FOUND') return '商品規格已更新，請重新整理頁面後再加入購物車。';
    if (err?.status === 422) return '訂單資料格式有誤，請檢查收件資訊後再送出。';
    return '目前無法送出訂單，請稍後再試。';
  };

  const buildOrderPayload = () => ({
    customer: {
      name: form.name,
      phone: form.phone,
      email: form.email || null,
    },
    shipping: {
      zipcode: form.zipcode,
      city: form.city,
      district: form.district,
      street: form.street,
      preferred_date: form.ship,
      delivery_window: form.window,
    },
    items: items.map(i => ({
      spec_id: i.specId,
      qty: i.count,
    })),
    payment_method: pay,
    note: form.note || null,
    expected_total: total,
  });

  const next = async () => {
    if (step === 'cart') {
      if (items.length === 0) return;
      setSubmitError(null);
      setStep('info');
    } else if (step === 'info') {
      setSubmitError(null);
      if (validate()) setStep('pay');
    } else if (step === 'pay') {
      if (submitting) return;
      setSubmitting(true);
      setSubmitError(null);
      try {
        const order = await createOrder(buildOrderPayload());
        setOrderId(order.order_no);
        setStep('done');
        onPlaceOrder?.();
      } catch (err) {
        console.error('[order] create failed:', err);
        setSubmitError(formatApiError(err));
      } finally {
        setSubmitting(false);
      }
    }
  };

  const back = () => {
    if (step === 'info') setStep('cart');
    else if (step === 'pay') setStep('info');
  };

  const closeAll = () => {
    onClose();
    setTimeout(() => {
      if (step === 'done') {
        setStep('cart');
        setForm({ name:'', phone:'', email:'', city:'', district:'', zipcode:'', street:'', ship: getTomorrowStr(), window:'any', note:'' });
        setPay('linepay');
        setOrderId(null);
        setSubmitError(null);
      }
    }, 200);
  };

  if (!open) return null;

  if (step === 'info' || step === 'pay') {
    return (
      <CheckoutPage
        step={step}
        form={form} setForm={setForm} errors={errors}
        pay={pay} setPay={setPay}
        subtotal={subtotal} shipping={shipping} codFee={codFee} total={total}
        submitting={submitting}
        submitError={submitError}
        onBack={back}
        onNext={next}
        onClose={closeAll}
      />
    );
  }

  return (
    <>
      <div className="scrim" onClick={closeAll}></div>
      <aside className="drawer" role="dialog" aria-label="購物車">
        <div className="drawer__head">
          <div>
            <h3>{step === 'done' ? '訂單完成' : '購物車'}</h3>
            <p className="sub">
              {step === 'done' ? '感謝您的訂購' :
               items.length === 0 ? '購物車是空的' :
               `共 ${items.reduce((s,i)=>s+i.count,0)} 件商品`}
            </p>
          </div>
          <button className="drawer__close" onClick={closeAll} aria-label="關閉">×</button>
        </div>

        <div className="drawer__body">
          {step === 'done' ? (
            <div className="success">
              <span className="seal">✓</span>
              <h4>訂單已成立</h4>
              <p>
                我們已收到您的訂單，將於當日採收後盡快出貨。<br/>
                出貨通知將透過 LINE / Email 寄送給您。
              </p>
              <span className="order-id">訂單編號 {orderId}</span>
              <div style={{marginTop:24, display:'flex', gap:10, justifyContent:'center'}}>
                <button className="btn btn--sage" onClick={closeAll}>繼續逛逛</button>
                <button className="btn btn--ghost" onClick={() => { window.print(); }}>列印訂單</button>
              </div>
            </div>
          ) : (
            items.length === 0 ? (
              <Empty onBrowse={closeAll} />
            ) : (
              <div>
                {items.map(it => (
                  <CartItem key={it.lineId} item={it} onQty={onQty} onRemove={onRemove} />
                ))}
              </div>
            )
          )}
        </div>

        {step === 'cart' && items.length > 0 && (
          <div className="drawer__foot">
            {subtotal < FREE_SHIPPING && (
              <div className="drawer__free">
                <span>距離免運還差 NT$ {(FREE_SHIPPING - subtotal).toLocaleString()}</span>
                <span className="bar"><i style={{width: Math.min(100, subtotal/FREE_SHIPPING*100) + '%'}}></i></span>
              </div>
            )}
            <div className="drawer__totals">
              <div className="row"><span>商品小計</span><span>NT$ {subtotal.toLocaleString()}</span></div>
              <div className="row"><span>運費</span><span>{shipping === 0 ? '免運 🍐' : 'NT$ ' + shipping}</span></div>
              <div className="row total"><span>合計</span><span className="v">NT$ {total.toLocaleString()}</span></div>
            </div>
            <button className="btn btn--primary btn--full" onClick={next}>前往結帳 →</button>
          </div>
        )}
      </aside>
    </>
  );
};
