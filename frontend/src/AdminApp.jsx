/* Admin order management app. */

import { useEffect, useMemo, useState } from 'react';

import {
  getAdminOrder,
  getCurrentAdmin,
  listAdminOrders,
  loginAdmin,
  updateAdminOrderStatus,
} from './api.js';

const TOKEN_KEY = 'miao.admin.token';

const STATUS_LABELS = {
  pending_payment: '待付款',
  pending: '待確認',
  confirmed: '已確認',
  shipping: '出貨中',
  delivered: '已送達',
  cancelled: '已取消',
};

const NEXT_STATUS = {
  pending_payment: ['confirmed', 'cancelled'],
  pending: ['confirmed', 'cancelled'],
  confirmed: ['shipping', 'cancelled'],
  shipping: ['delivered'],
  delivered: [],
  cancelled: [],
};

const money = (n) => `NT$ ${Number(n || 0).toLocaleString()}`;
const dateText = (s) => s ? new Date(s).toLocaleString('zh-TW', { hour12: false }) : '-';
const statusLabel = (s) => STATUS_LABELS[s] || s || '-';

const ErrorBar = ({ message }) => message ? <div className="adm-alert">{message}</div> : null;

function LoginView({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const token = await loginAdmin(username, password);
      onLogin(token.access_token);
    } catch (err) {
      setError(err?.data?.detail || '登入失敗，請確認帳號密碼。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="admin-page adm-login">
      <form className="adm-login__box" onSubmit={submit}>
        <div>
          <p className="adm-kicker">Admin</p>
          <h1>妙媽媽果園後台</h1>
        </div>
        <label>
          <span>帳號</span>
          <input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" />
        </label>
        <label>
          <span>密碼</span>
          <input value={password} onChange={e => setPassword(e.target.value)} type="password" autoComplete="current-password" />
        </label>
        <ErrorBar message={error} />
        <button className="adm-btn adm-btn--primary" disabled={loading || !username || !password}>
          {loading ? '登入中...' : '登入'}
        </button>
      </form>
    </main>
  );
}

function FilterBar({ filters, setFilters, onApply, onClear, loading }) {
  const set = (key, value) => setFilters(prev => ({ ...prev, [key]: value }));
  return (
    <div className="adm-filters">
      <label>
        <span>狀態</span>
        <select value={filters.status} onChange={e => set('status', e.target.value)}>
          <option value="">全部</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </label>
      <label>
        <span>姓名 / 電話</span>
        <input value={filters.q} onChange={e => set('q', e.target.value)} placeholder="搜尋" />
      </label>
      <label>
        <span>訂單編號</span>
        <input value={filters.order_no} onChange={e => set('order_no', e.target.value)} placeholder="MM-" />
      </label>
      <label>
        <span>起日</span>
        <input type="date" value={filters.date_from} onChange={e => set('date_from', e.target.value)} />
      </label>
      <label>
        <span>迄日</span>
        <input type="date" value={filters.date_to} onChange={e => set('date_to', e.target.value)} />
      </label>
      <div className="adm-filter-actions">
        <button className="adm-btn adm-btn--primary" onClick={onApply} disabled={loading}>查詢</button>
        <button className="adm-btn" onClick={onClear} disabled={loading}>清除</button>
      </div>
    </div>
  );
}

function OrdersTable({ orders, selected, onSelect }) {
  return (
    <div className="adm-table-wrap">
      <table className="adm-table">
        <thead>
          <tr>
            <th>訂單</th>
            <th>狀態</th>
            <th>客戶</th>
            <th>電話</th>
            <th className="num">金額</th>
            <th>建立時間</th>
          </tr>
        </thead>
        <tbody>
          {orders.map(order => (
            <tr
              key={order.order_no}
              className={selected === order.order_no ? 'is-selected' : ''}
              onClick={() => onSelect(order.order_no)}
            >
              <td className="mono">{order.order_no}</td>
              <td><span className={`adm-status adm-status--${order.status}`}>{statusLabel(order.status)}</span></td>
              <td>{order.customer_name}</td>
              <td>{order.customer_phone}</td>
              <td className="num">{money(order.total)}</td>
              <td>{dateText(order.created_at)}</td>
            </tr>
          ))}
          {orders.length === 0 && (
            <tr>
              <td colSpan="6" className="adm-empty">沒有符合條件的訂單</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function OrderDetail({ order, loading, error, onChangeStatus }) {
  const nextStatuses = useMemo(() => order ? NEXT_STATUS[order.status] || [] : [], [order]);
  const [target, setTarget] = useState('');

  useEffect(() => {
    setTarget('');
  }, [order?.order_no, order?.status]);

  if (loading) return <aside className="adm-detail"><p className="adm-muted">載入明細中...</p></aside>;
  if (error) return <aside className="adm-detail"><ErrorBar message={error} /></aside>;
  if (!order) return <aside className="adm-detail"><p className="adm-muted">選擇一筆訂單查看明細</p></aside>;

  return (
    <aside className="adm-detail">
      <div className="adm-detail__head">
        <div>
          <p className="adm-kicker">Order</p>
          <h2>{order.order_no}</h2>
        </div>
        <span className={`adm-status adm-status--${order.status}`}>{statusLabel(order.status)}</span>
      </div>

      <section className="adm-block">
        <h3>收件資訊</h3>
        <dl className="adm-dl">
          <dt>收件人</dt><dd>{order.customer_name}</dd>
          <dt>電話</dt><dd>{order.customer_phone}</dd>
          <dt>Email</dt><dd>{order.customer_email || '-'}</dd>
          <dt>地址</dt><dd>{order.ship_zipcode} {order.ship_city}{order.ship_district}{order.ship_street}</dd>
          <dt>希望送達</dt><dd>{order.preferred_date} / {order.delivery_window}</dd>
          <dt>付款方式</dt><dd>{order.payment_method}</dd>
          <dt>備註</dt><dd>{order.note || '-'}</dd>
        </dl>
      </section>

      <section className="adm-block">
        <h3>商品明細</h3>
        <div className="adm-lines">
          {order.items.map((item, index) => (
            <div className="adm-line" key={`${item.spec_label}-${index}`}>
              <div>
                <strong>{item.product_name}</strong>
                <span>{item.spec_label} x {item.qty}</span>
              </div>
              <b>{money(item.line_total)}</b>
            </div>
          ))}
        </div>
        <div className="adm-total">
          <span>小計</span><b>{money(order.subtotal)}</b>
          <span>運費</span><b>{money(order.shipping_fee)}</b>
          <span>貨到付款</span><b>{money(order.cod_fee)}</b>
          <span>總計</span><strong>{money(order.total)}</strong>
        </div>
      </section>

      <section className="adm-block">
        <h3>狀態更新</h3>
        <div className="adm-status-form">
          <select value={target} onChange={e => setTarget(e.target.value)} disabled={nextStatuses.length === 0}>
            <option value="">{nextStatuses.length ? '選擇下一個狀態' : '此訂單已不可變更'}</option>
            {nextStatuses.map(status => <option key={status} value={status}>{statusLabel(status)}</option>)}
          </select>
          <button className="adm-btn adm-btn--primary" disabled={!target} onClick={() => onChangeStatus(order.order_no, target)}>
            更新
          </button>
        </div>
      </section>
    </aside>
  );
}

export default function AdminApp() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [admin, setAdmin] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [filters, setFilters] = useState({
    status: '', q: '', order_no: '', date_from: '', date_to: '',
  });
  const [orders, setOrders] = useState({ total: 0, page: 1, page_size: 20, items: [] });
  const [selected, setSelected] = useState('');
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');
  const [detailError, setDetailError] = useState('');

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken('');
    setAdmin(null);
    setSelected('');
    setDetail(null);
  };

  const loadOrders = async (page = 1, filterValues = filters) => {
    if (!token) return;
    setLoading(true);
    setError('');
    try {
      const data = await listAdminOrders(token, {
        ...filterValues,
        page,
        page_size: 20,
      });
      setOrders(data);
      if (data.items.length === 0) {
        setSelected('');
        setDetail(null);
      } else if (!data.items.some(item => item.order_no === selected)) {
        setSelected(data.items[0].order_no);
      }
    } catch (err) {
      if (err?.status === 401) logout();
      else setError(err?.data?.detail || '無法載入訂單。');
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (orderNo) => {
    if (!token || !orderNo) return;
    setDetailLoading(true);
    setDetailError('');
    try {
      const data = await getAdminOrder(token, orderNo);
      setDetail(data);
    } catch (err) {
      if (err?.status === 401) logout();
      else setDetailError(err?.data?.detail || '無法載入訂單明細。');
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    if (!token) {
      setAuthChecked(true);
      return;
    }
    getCurrentAdmin(token)
      .then(user => {
        setAdmin(user);
        setAuthChecked(true);
      })
      .catch(() => {
        logout();
        setAuthChecked(true);
      });
  }, [token]);

  useEffect(() => {
    if (admin) loadOrders(1);
  }, [admin]);

  useEffect(() => {
    if (selected) loadDetail(selected);
  }, [selected]);

  const handleLogin = (accessToken) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
  };

  const clearFilters = () => {
    const cleared = { status: '', q: '', order_no: '', date_from: '', date_to: '' };
    setFilters(cleared);
    loadOrders(1, cleared);
  };

  const changeStatus = async (orderNo, status) => {
    setDetailError('');
    try {
      const updated = await updateAdminOrderStatus(token, orderNo, status);
      setDetail(updated);
      await loadOrders(orders.page);
    } catch (err) {
      setDetailError(err?.data?.detail || '狀態更新失敗。');
    }
  };

  if (!authChecked) return <main className="admin-page adm-shell adm-center">載入中...</main>;
  if (!token || !admin) return <LoginView onLogin={handleLogin} />;

  return (
    <main className="admin-page adm-shell">
      <header className="adm-topbar">
        <div>
          <p className="adm-kicker">Miao Fruit Shop</p>
          <h1>訂單管理</h1>
        </div>
        <div className="adm-user">
          <span>{admin.username}</span>
          <button className="adm-btn" onClick={logout}>登出</button>
        </div>
      </header>

      <FilterBar
        filters={filters}
        setFilters={setFilters}
        onApply={() => loadOrders(1)}
        onClear={clearFilters}
        loading={loading}
      />
      <ErrorBar message={error} />

      <section className="adm-grid">
        <div className="adm-list">
          <div className="adm-list__head">
            <span>共 {orders.total} 筆</span>
            <div className="adm-pager">
              <button className="adm-btn" disabled={orders.page <= 1 || loading} onClick={() => loadOrders(orders.page - 1)}>上一頁</button>
              <span>{orders.page}</span>
              <button className="adm-btn" disabled={orders.items.length < orders.page_size || loading} onClick={() => loadOrders(orders.page + 1)}>下一頁</button>
            </div>
          </div>
          {loading ? <p className="adm-muted">載入訂單中...</p> : (
            <OrdersTable orders={orders.items} selected={selected} onSelect={setSelected} />
          )}
        </div>
        <OrderDetail
          order={detail}
          loading={detailLoading}
          error={detailError}
          onChangeStatus={changeStatus}
        />
      </section>
    </main>
  );
}
