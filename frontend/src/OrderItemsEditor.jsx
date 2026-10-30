/* 訂單品項編輯區 — 後台編輯訂單與代客下單共用 */

import { money } from './format.js';
import { addableSpecs, lineForSpec, previewAmounts, qtyStep } from './orderEdit.js';

/*
 * lines    — 編輯行(見 orderEdit.js),由呼叫端持有
 * onChange — (nextLines) => void
 * specs    — 後台規格清單,每筆另帶 productName
 * orderItems — 訂單開啟時的訂單品項(新訂單為 [])
 * isNewOrder — 代客下單:尚未成立,可移除到 0 行(R2 只限既有訂單)
 */
export default function OrderItemsEditor({
  lines, onChange, specs, orderItems = [], disabled = false, isNewOrder = false,
}) {
  const onlyOne = !isNewOrder && lines.length === 1;
  const addable = addableSpecs(specs, lines);
  const preview = previewAmounts(lines);

  const setQty = (idx, qty) =>
    onChange(lines.map((l, i) => (i === idx ? { ...l, qty } : l)));

  const step = (idx, delta) => {
    const line = lines[idx];
    const unit = qtyStep(line.isTwoPack);
    setQty(idx, Math.max(unit, Number(line.qty) + delta * unit));
  };

  const remove = (idx) => onChange(lines.filter((_, i) => i !== idx));

  const add = (specId) => {
    const spec = specs.find((s) => s.id === Number(specId));
    if (spec) onChange([...lines, lineForSpec(spec, orderItems)]);
  };

  return (
    <div className="adm-items-editor">
      {lines.some((l) => !l.isNew) && (
        <p className="adm-field__hint">
          既有訂單品項沿用下單價，新增訂單品項以規格目前價格計算。
        </p>
      )}
      {lines.map((line, idx) => {
        const unit = qtyStep(line.isTwoPack);
        return (
          <div className="adm-items-editor__row" key={line.spec_id ?? `idx-${idx}`}>
            <div className="adm-items-editor__info">
              <div className="adm-items-editor__label">
                {line.label}
                {line.isNew && <span className="adm-items-editor__tag">新增</span>}
              </div>
              <div className="adm-items-editor__price">
                {line.isNew ? '目前價格' : '下單價'} {money(line.unitPrice)}
                {line.isTwoPack && ' · 兩粒裝，以雙數購買'}
              </div>
              {line.locked && (
                <div className="adm-items-editor__locked">已下架，數量不可修改</div>
              )}
            </div>
            <div className="adm-items-editor__qty">
              <button
                type="button"
                className="adm-items-editor__step"
                onClick={() => step(idx, -1)}
                disabled={disabled || line.locked || Number(line.qty) <= unit}
                aria-label="減少數量"
              >
                −
              </button>
              <input
                type="number"
                inputMode="numeric"
                min={unit}
                step={unit}
                className="adm-field__input adm-items-editor__qty-input"
                value={line.qty}
                onChange={(e) => setQty(idx, e.target.value)}
                disabled={disabled || line.locked}
                aria-label={`${line.label} 數量`}
              />
              <button
                type="button"
                className="adm-items-editor__step"
                onClick={() => step(idx, 1)}
                disabled={disabled || line.locked}
                aria-label="增加數量"
              >
                +
              </button>
            </div>
            <button
              type="button"
              className="adm-modal__item-row-remove"
              onClick={() => remove(idx)}
              disabled={disabled || onlyOne}
              title={onlyOne ? '全部不要請取消訂單' : '移除此訂單品項'}
              aria-label="移除此訂單品項"
            >
              ✕
            </button>
          </div>
        );
      })}
      {onlyOne && <p className="adm-field__hint">訂單至少保留一個訂單品項；全部不要請取消訂單。</p>}
      <label className="adm-field">
        <span className="adm-field__label">新增訂單品項</span>
        <select
          className="adm-field__input"
          value=""
          onChange={(e) => add(e.target.value)}
          disabled={disabled || addable.length === 0}
        >
          <option value="">
            {!addable.length
              ? '沒有可新增的規格'
              : isNewOrder ? '選擇規格…' : '選擇要加訂的規格…'}
          </option>
          {addable.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}（{money(s.price)}，庫存 {s.stock_qty}）
            </option>
          ))}
        </select>
      </label>
      {preview && (
        <div className="adm-modal__totals">
          <span>小計</span><span>{money(preview.subtotal)}</span>
          <span>運費</span><span>{money(preview.shippingFee)}</span>
          <span className="grand">試算總額</span>
          <span className="grand-val">{money(preview.total)}</span>
        </div>
      )}
    </div>
  );
}
