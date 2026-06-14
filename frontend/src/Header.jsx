/* Header — sticky top nav with mobile hamburger */

import { useEffect, useState } from 'react';

import { StoreIcon } from './Icons.jsx';

export const Header = ({ cartCount, onCart, active, onNav }) => {
  const I = StoreIcon;
  const [open, setOpen] = useState(false);

  const links = [
    { id: 'shop', label: '商品' },
    { id: 'notice', label: '注意事項' },
    { id: 'packaging', label: '包裝' },
    { id: 'about', label: '品牌故事' },
    { id: 'contact', label: '聯絡我們' }
  ];

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  const handleNav = (id) => {
    setOpen(false);
    onNav(id);
  };

  return (
    <header className={'nav' + (open ? ' nav--open' : '')}>
      <div className="container nav__inner" data-comment-anchor="8107df7aad-div-14-7">
        <button className="nav__brand" onClick={() => handleNav('top')}>
          <span className="orb">
            <img src="assets/small_logo.jpg" alt="妙媽媽果園" />
          </span>
          <span>
            妙媽媽果園
            <span className="sub" style={{ display: 'block', marginTop: 2 }}>MIAO MAMA ORCHARD</span>
          </span>
        </button>

        <nav className={'nav__links' + (open ? ' is-open' : '')} aria-hidden={!open && undefined}>
          {links.map((l) =>
            <button
              key={l.id}
              aria-current={active === l.id ? 'true' : undefined}
              onClick={() => handleNav(l.id)}>
              {l.label}
            </button>
          )}
        </nav>

        <div className="nav__actions">
          <button className="nav__cart" onClick={onCart}>
            <I name="cart" size={18} />
            <span className="nav__cart-label">購物車</span>
            {cartCount > 0 && <span className="badge">{cartCount}</span>}
          </button>
          <button
            className="nav__toggle"
            aria-label={open ? '關閉選單' : '開啟選單'}
            aria-expanded={open}
            onClick={() => setOpen(v => !v)}>
            <span className={'nav__toggle-bars' + (open ? ' is-open' : '')}>
              <span></span><span></span><span></span>
            </span>
          </button>
        </div>
      </div>
      {open && <div className="nav__scrim" onClick={() => setOpen(false)} aria-hidden="true"></div>}
    </header>
  );
};
