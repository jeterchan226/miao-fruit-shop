/* App — top-level state, tweaks, sections */

const { useState: useStateA, useEffect: useEffectA } = React;

function App() {
  // ── Tweaks ────────────────────────────────────────────────
  const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
    "heroLayout": "split",
    "palette": "cream",
    "packagingLayout": "cards",
    "density": "standard"
  }/*EDITMODE-END*/;

  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // apply palette + density via root attributes
  useEffectA(() => {
    document.documentElement.setAttribute('data-palette', tweaks.palette);
    document.documentElement.setAttribute('data-density', tweaks.density);
  }, [tweaks.palette, tweaks.density]);

  // ── Cart state ────────────────────────────────────────────
  const [cart, setCart] = useStateA([]); // [{lineId, productId, name, image, specLabel, qty, price, count}]
  const [drawerOpen, setDrawerOpen] = useStateA(false);
  const [toast, setToast] = useStateA(null);
  const [activeSec, setActiveSec] = useStateA('shop');

  const cartCount = cart.reduce((s, i) => s + i.count, 0);

  const addToCart = (p, spec, count = 1) => {
    setCart(prev => {
      const lineId = p.id + '-' + spec.id;
      const found = prev.find(i => i.lineId === lineId);
      if (found) {
        return prev.map(i => i.lineId === lineId ? { ...i, count: i.count + count } : i);
      }
      return [...prev, {
        lineId, productId: p.id, name: p.name,
        image: p.image, specLabel: spec.label, qty: spec.qty,
        price: spec.price, count
      }];
    });
    setToast(`${p.name} · ${spec.label} ×${count} 已加入購物車 🍐`);
  };

  const setQty = (lineId, count) => {
    if (count <= 0) {
      setCart(prev => prev.filter(i => i.lineId !== lineId));
    } else {
      setCart(prev => prev.map(i => i.lineId === lineId ? { ...i, count } : i));
    }
  };
  const remove = (lineId) => setCart(prev => prev.filter(i => i.lineId !== lineId));

  useEffectA(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 1800);
    return () => clearTimeout(t);
  }, [toast]);

  // scroll spy
  useEffectA(() => {
    const sections = ['shop','notice','packaging','about','contact'];
    const onScroll = () => {
      const y = window.scrollY + 120;
      let cur = sections[0];
      for (const id of sections) {
        const el = document.getElementById(id);
        if (el && el.offsetTop <= y) cur = id;
      }
      setActiveSec(cur);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // ── Render ────────────────────────────────────────────────
  return (
    <>
      <Header
        cartCount={cartCount}
        onCart={() => setDrawerOpen(true)}
        active={activeSec}
        onNav={(id) => id === 'top' ? window.scrollTo({top:0, behavior:'smooth'}) : window.scrollToId(id)}
      />
      <Hero variant={tweaks.heroLayout} />

      <section className="sec" id="shop">
        <div className="container">
          <SecTitle
            eyebrow="OUR PEARS"
            title="精選水梨商品"
            sub="甘露梨珍稀品種，蜜香濃郁、入口即化。提供 2 粒禮盒、5 台斤與 10 台斤三種規格選擇。"
          />
          <div className="shop">
            <div className="shop__grid shop__grid--specs">
              {window.PRODUCTS.flatMap(p =>
                p.specs.map(spec => (
                  <SpecCard key={p.id + '-' + spec.id} p={p} spec={spec} onAdd={addToCart} />
                ))
              )}
            </div>
            <Rail />
          </div>
        </div>
      </section>

      <Packaging variant={tweaks.packagingLayout} />
      <Notices />
      <Belief />
      <Contact />
      <Footer />

      <CartDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        items={cart}
        onQty={setQty}
        onRemove={remove}
        onPlaceOrder={() => setCart([])}
      />

      {toast && <div className="toast">{toast}</div>}

      <TweaksPanel>
        <TweakSection label="主視覺與配色">
          <TweakRadio
            label="Hero 版型"
            value={tweaks.heroLayout}
            onChange={v => setTweak('heroLayout', v)}
            options={[
              { value:'split', label:'經典左右切' },
              { value:'fullbleed', label:'整圖鋪滿' },
              { value:'collage', label:'拼貼相本' },
            ]}
          />
          <TweakRadio
            label="整體配色"
            value={tweaks.palette}
            onChange={v => setTweak('palette', v)}
            options={[
              { value:'cream', label:'米白' },
              { value:'sage', label:'鼠尾草綠' },
              { value:'brown', label:'深棕' },
            ]}
          />
        </TweakSection>

        <TweakSection label="商品與包裝呈現">
          <TweakRadio
            label="包裝展示"
            value={tweaks.packagingLayout}
            onChange={v => setTweak('packagingLayout', v)}
            options={[
              { value:'cards', label:'並列卡' },
              { value:'carousel', label:'橫條輪播' },
              { value:'magazine', label:'雜誌跨頁' },
            ]}
          />
        </TweakSection>

        <TweakSection label="字體與密度">
          <TweakRadio
            label="字體大小密度"
            value={tweaks.density}
            onChange={v => setTweak('density', v)}
            options={[
              { value:'compact', label:'緊湊' },
              { value:'standard', label:'標準' },
              { value:'spacious', label:'寬鬆' },
            ]}
          />
        </TweakSection>
      </TweaksPanel>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
