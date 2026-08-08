/* Spec group tabs — 兩粒裝／箱裝兩組，各自共用一組圖片輪播 + 緊湊規格列表 */

import { useEffect, useRef, useState } from 'react';
import { StoreIcon } from './Icons.jsx';

const stockLabel = (s) => s === 'in' ? '現貨供應' : s === 'low' ? '剩量不多' : '已售完';

const GROUPS = [
  { key: 'box', label: '箱裝', filter: (s) => !s.isTwoPack },
  { key: 'twopack', label: '兩粒裝', filter: (s) => s.isTwoPack },
];

const Price = ({ value }) => (
  <span className="price">
    <span className="pre">NT$</span>{value.toLocaleString()}
  </span>
);

const GroupCarousel = ({ images, season }) => {
  const [imgIdx, setImgIdx] = useState(0);
  const slidesRef = useRef(null);
  const timerRef = useRef(null);

  const scrollToSlide = (i) => {
    const track = slidesRef.current;
    if (track) track.scrollTo({ left: track.clientWidth * i, behavior: 'smooth' });
  };

  const goTo = (i) => {
    setImgIdx(i);
    scrollToSlide(i);
  };

  const resetTimer = () => {
    clearInterval(timerRef.current);
    if (images.length <= 1) return;
    timerRef.current = setInterval(() => {
      setImgIdx((prev) => {
        const next = (prev + 1) % images.length;
        scrollToSlide(next);
        return next;
      });
    }, 3500);
  };

  useEffect(() => {
    resetTimer();
    return () => clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [images.length]);

  const handleDotClick = (i) => {
    goTo(i);
    resetTimer();
  };

  const handleArrow = (dir) => {
    const next = (imgIdx + dir + images.length) % images.length;
    goTo(next);
    resetTimer();
  };

  return (
    <div className="pcard__media">
      <div className="pcard__carousel">
        <div className="pcard__slides" ref={slidesRef}>
          {images.length > 0 ? images.map((url, i) => (
            <div key={i} className="pcard__slide" style={{ backgroundImage: `url(${url})` }} />
          )) : (
            <div className="pcard__slide pcard__slide--empty" />
          )}
        </div>
        <span className="pcard__season">產季 {season}</span>
        {images.length > 1 && (
          <>
            <button
              type="button"
              className="pcard__arrow pcard__arrow--prev"
              onClick={() => handleArrow(-1)}
              aria-label="上一張圖片"
            >
              <StoreIcon name="chevron-left" size={18} />
            </button>
            <button
              type="button"
              className="pcard__arrow pcard__arrow--next"
              onClick={() => handleArrow(1)}
              aria-label="下一張圖片"
            >
              <StoreIcon name="chevron-right" size={18} />
            </button>
          </>
        )}
      </div>
      {images.length > 1 && (
        <div className="pcard__thumbs">
          {images.map((url, i) => (
            <button
              key={i}
              type="button"
              className={'pcard__thumb' + (i === imgIdx ? ' is-active' : '')}
              style={{ backgroundImage: `url(${url})` }}
              onClick={() => handleDotClick(i)}
              aria-label={`圖片 ${i + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const SpecRow = ({ p, spec, onAdd }) => {
  const step = spec.isTwoPack ? 2 : 1;
  const [qty, setQty] = useState(step);
  const disabled = spec.stock === 'out';

  return (
    <div className="spec-row">
      <div className="spec-row__info">
        <h3 className="spec-row__name">{spec.label}</h3>
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
            <span className={'stock stock--' + spec.stock}>{stockLabel(spec.stock)}</span>
          </div>
          {spec.isTwoPack && (
            <div className="specs__row">
              <span className="k">購買單位</span>
              <span className="specs__note">請以雙數（2、4、6…）箱購買</span>
            </div>
          )}
        </div>
      </div>
      <div className="spec-row__actions">
        <Price value={spec.price} />
        <div className="speccard__actions">
          {!disabled && (
            <div className="qty">
              <button onClick={() => setQty(q => Math.max(step, q - step))} aria-label="減少數量">−</button>
              <span className="v">{qty}</span>
              <button onClick={() => setQty(q => q + step)} aria-label="增加數量">+</button>
            </div>
          )}
          <button
            className="btn btn--primary"
            disabled={disabled}
            onClick={() => { onAdd(p, spec, qty); setQty(step); }}
          >
            {disabled ? '已售完' : '加入購物車'}
          </button>
        </div>
      </div>
    </div>
  );
};

export const SpecGroupTabs = ({ product: p, onAdd }) => {
  const groups = GROUPS.map(g => ({ ...g, specs: p.specs.filter(g.filter) }));
  const defaultGroup = groups.find(g => g.key === 'box' && g.specs.length > 0)
    ?? groups.find(g => g.specs.length > 0)
    ?? groups[0];
  const [activeKey, setActiveKey] = useState(defaultGroup.key);
  const active = groups.find(g => g.key === activeKey) ?? defaultGroup;
  const images = active.specs[0]?.images || [];
  const productSub = p.sub ? p.sub.split(' · ')[1] : p.slug;

  return (
    <article className="pcard spec-group">
      <GroupCarousel key={active.key} images={images} season={p.season} />
      <div className="pcard__body">
        <div className="pcard__head">
          <h2 className="pcard__name">{p.name}</h2>
          <p className="pcard__sub">{productSub || p.name}</p>
        </div>
        <div className="specs__tabs">
          {groups.map(g => {
            const empty = g.specs.length === 0;
            return (
              <button
                key={g.key}
                type="button"
                className={'specs__tab' + (g.key === active.key ? ' is-active' : '') + (empty ? ' specs__tab--empty' : '')}
                disabled={empty}
                onClick={() => setActiveKey(g.key)}
              >
                {g.label}
                {empty && <span className="num">無商品</span>}
              </button>
            );
          })}
        </div>
        <div className="spec-rows">
          {active.specs.map(spec => (
            <SpecRow key={spec.id} p={p} spec={spec} onAdd={onAdd} />
          ))}
        </div>
      </div>
    </article>
  );
};
