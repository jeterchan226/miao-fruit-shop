/* Spec card — one card per spec, with qty stepper (single-product storefront) */

import { useEffect, useRef, useState } from 'react';

const stockLabel = (s) => s === 'in' ? '現貨供應' : s === 'low' ? '剩量不多' : '預購中';

const Price = ({ value }) => (
  <span className="price">
    <span className="pre">NT$</span>{value.toLocaleString()}
  </span>
);

export const SpecCard = ({ p, spec, onAdd }) => {
  const [qty, setQty] = useState(1);
  const [imgIdx, setImgIdx] = useState(0);
  const slidesRef = useRef(null);
  const disabled = spec.stock === 'out';
  const productSub = p.sub ? p.sub.split(' · ')[1] : p.slug;
  const images = (spec.images && spec.images.length > 0) ? spec.images : (p.images || []);

  const timerRef = useRef(null);

  const goTo = (i) => {
    setImgIdx(i);
    if (slidesRef.current) {
      const slide = slidesRef.current.children[i];
      if (slide) slide.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  };

  const resetTimer = (newIdx) => {
    clearInterval(timerRef.current);
    if (images.length <= 1) return;
    timerRef.current = setInterval(() => {
      setImgIdx((prev) => {
        const next = (prev + 1) % images.length;
        if (slidesRef.current) {
          const slide = slidesRef.current.children[next];
          if (slide) slide.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
        return next;
      });
    }, 3500);
  };

  useEffect(() => {
    resetTimer(0);
    return () => clearInterval(timerRef.current);
  }, [images.length]);

  const handleDotClick = (i) => {
    goTo(i);
    resetTimer(i);
  };

  return (
    <article className="pcard speccard">
      <div className="pcard__carousel">
        <div className="pcard__slides" ref={slidesRef}>
          {images.length > 0 ? images.map((url, i) => (
            <div
              key={i}
              className="pcard__slide"
              style={{ backgroundImage: `url(${url})` }}
            />
          )) : (
            <div className="pcard__slide pcard__slide--empty" />
          )}
        </div>
        <span className="pcard__season">產季 {p.season}</span>
        {images.length > 1 && (
          <div className="pcard__dots">
            {images.map((_, i) => (
              <button
                key={i}
                className={'pcard__dot' + (i === imgIdx ? ' is-active' : '')}
                onClick={() => handleDotClick(i)}
                aria-label={`圖片 ${i + 1}`}
              />
            ))}
          </div>
        )}
      </div>
      <div className="pcard__body">
        <div className="pcard__head">
          <h3 className="pcard__name">{spec.label}</h3>
          <p className="pcard__sub">{productSub ? `${p.name} · ${productSub}` : p.name}</p>
        </div>
        <div className="specs__panel">
          <div className="specs__row">
            <span className="k">內容</span>
            <span>{spec.qty}</span>
          </div>
          {spec.note && (
            <div className="specs__row">
              <span className="k">備註</span>
              <span className="specs__note">{spec.note}</span>
            </div>
          )}
          <div className="specs__row">
            <span className="k">狀態</span>
            <span className={'stock stock--' + spec.stock}>
              {stockLabel(spec.stock)}
            </span>
          </div>
        </div>
        <div className="pcard__foot speccard__foot">
          <Price value={spec.price} />
          <div className="speccard__actions">
            <div className="qty">
              <button onClick={() => setQty(q => Math.max(1, q - 1))} aria-label="減少數量">−</button>
              <span className="v">{qty}</span>
              <button onClick={() => setQty(q => q + 1)} aria-label="增加數量">+</button>
            </div>
            <button
              className="btn btn--primary"
              disabled={disabled}
              onClick={() => { onAdd(p, spec, qty); setQty(1); }}
            >
              {disabled ? '預購登記' : '加入購物車'}
            </button>
          </div>
        </div>
      </div>
    </article>
  );
};
