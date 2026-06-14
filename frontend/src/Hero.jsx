/* Hero — three variants: split / fullbleed / collage */

import { StoreIcon } from './Icons.jsx';

export const scrollToId = (id) => {
  const el = document.getElementById(id);
  if (!el) return;
  const top = el.getBoundingClientRect().top + window.scrollY - 80;
  window.scrollTo({ top, behavior: 'smooth' });
};
window.scrollToId = scrollToId;

const HeroSplit = () => {
  const I = StoreIcon;
  return (
    <section className="hero hero--split" id="top">
      <div className="hero__grid">
        <div className="hero__col">
          <div className="container" style={{padding:0, maxWidth:'none'}}>
            <div className="eyebrow-row" style={{marginLeft:32}}>卓蘭 · 高接梨 · 2026 產季</div>
            <div style={{paddingLeft:32}}>
              <h1>新鮮現採水梨，<br/><span className="accent">產地直送</span>。</h1>
              <p className="lede">
                來自梨園的用心，香甜多汁、清脆爽口。<br/>
                給家人最安心的美味，一箱一箱手挑、隔日到府。
              </p>
              <div className="hero__ctas">
                <button className="btn btn--primary btn--lg" onClick={() => scrollToId('shop')}>
                  選購水梨
                  <span style={{fontSize:14}}>→</span>
                </button>
                <button className="btn btn--ghost btn--lg" onClick={() => scrollToId('notice')}>
                  查看注意事項
                </button>
              </div>
              <div className="trust">
                <div className="trust__item">
                  <span className="trust__chip"><I name="truck" /></span>
                  <div>
                    <p className="trust__t">產地直送</p>
                    <p className="trust__s">當日採收 · 隔日到府</p>
                  </div>
                </div>
                <div className="trust__item">
                  <span className="trust__chip"><I name="shield-check" /></span>
                  <div>
                    <p className="trust__t">品質把關</p>
                    <p className="trust__s">逐顆挑選 · 損壞包賠</p>
                  </div>
                </div>
                <div className="trust__item">
                  <span className="trust__chip"><I name="plant" /></span>
                  <div>
                    <p className="trust__t">友善栽培</p>
                    <p className="trust__s">低農藥 · 安心吃</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="hero__photo">
          <div className="hero__seal">
            <span className="yr">EST. 1998</span>
            妙媽媽果園
            <span className="leaf">🍐</span>
          </div>
        </div>
      </div>
      <div className="hero__dots">
        <button className="is-active" aria-label="slide 1"></button>
        <button aria-label="slide 2"></button>
        <button aria-label="slide 3"></button>
      </div>
    </section>
  );
};

const HeroFullbleed = () => {
  const I = StoreIcon;
  return (
    <section className="hero hero--fullbleed" id="top">
      <div className="hero__bleed">
        <div className="hero__overlay">
          <div className="container">
            <div className="eyebrow-row" style={{color:'#fff'}}>卓蘭 · 高接梨 · 2026 產季</div>
            <h1>新鮮現採水梨，<br/>產地直送。</h1>
            <p className="lede">
              來自梨園的用心，香甜多汁、清脆爽口。一箱一箱手挑、隔日到府。
            </p>
            <div className="hero__ctas">
              <button className="btn btn--primary btn--lg" onClick={() => scrollToId('shop')}>
                選購水梨 →
              </button>
              <button className="btn btn--ghost btn--lg" style={{color:'#fff', borderColor:'rgba(255,255,255,.45)'}} onClick={() => scrollToId('notice')}>
                查看注意事項
              </button>
            </div>
            <div className="trust">
              <div className="trust__item">
                <span className="trust__chip"><I name="truck" /></span>
                <div><p className="trust__t">產地直送</p><p className="trust__s">當日採收 · 隔日到府</p></div>
              </div>
              <div className="trust__item">
                <span className="trust__chip"><I name="shield-check" /></span>
                <div><p className="trust__t">品質把關</p><p className="trust__s">逐顆挑選 · 損壞包賠</p></div>
              </div>
              <div className="trust__item">
                <span className="trust__chip"><I name="plant" /></span>
                <div><p className="trust__t">友善栽培</p><p className="trust__s">低農藥 · 安心吃</p></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

const HeroCollage = () => {
  return (
    <section className="hero hero--collage" id="top">
      <div className="container hero__grid">
        <div className="hero__col">
          <div className="eyebrow-row">卓蘭 · 高接梨 · 2026 產季</div>
          <h1>新鮮現採水梨，<br/><span className="accent">產地直送</span>。</h1>
          <p className="lede">
            來自梨園的用心，香甜多汁、清脆爽口。一箱一箱手挑、隔日到府。
          </p>
          <div className="hero__ctas">
            <button className="btn btn--primary btn--lg" onClick={() => scrollToId('shop')}>
              選購水梨 →
            </button>
            <button className="btn btn--ghost btn--lg" onClick={() => scrollToId('notice')}>
              查看注意事項
            </button>
          </div>
        </div>
        <div className="collage">
          <div className="polaroid">
            <span className="washi washi--1"></span>
            <span className="mono">07 · 28</span>
            <img src="assets/product_1.jpg" alt="" />
            <span className="cap">果園清晨</span>
          </div>
          <div className="polaroid">
            <span className="mono">PORTRA 400</span>
            <img src="assets/product_4.jpg" alt="" />
            <span className="cap">當日採收</span>
          </div>
          <div className="polaroid">
            <span className="mono">08 · 15</span>
            <img src="assets/product_6.jpg" alt="" />
            <span className="cap">手挑出貨</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export const Hero = ({ variant }) => {
  if (variant === 'fullbleed') return <HeroFullbleed />;
  if (variant === 'collage')   return <HeroCollage />;
  return <HeroSplit />;
};
