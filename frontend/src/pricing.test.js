import { describe, it, expect } from 'vitest';
import { FREE_SHIPPING, computeLayers, computeShipping } from './pricing.js';

describe('computeLayers', () => {
  it('非2粒每箱1層', () => {
    expect(computeLayers([{ isTwoPack: false, count: 3 }])).toBe(3);
  });
  it('2粒每2箱1層', () => {
    expect(computeLayers([{ isTwoPack: true, count: 4 }])).toBe(2);
  });
  it('混合', () => {
    expect(computeLayers([{ isTwoPack: false, count: 1 }, { isTwoPack: true, count: 2 }])).toBe(2);
  });
});

describe('computeShipping', () => {
  it('分級', () => {
    expect(computeShipping(1000, 1)).toBe(100);
    expect(computeShipping(1000, 2)).toBe(150);
    expect(computeShipping(1000, 3)).toBe(180);
    expect(computeShipping(1000, 4)).toBe(180);
  });
  it('滿門檻免運', () => {
    expect(computeShipping(FREE_SHIPPING, 3)).toBe(0);
  });
  it('零層免運費', () => {
    expect(computeShipping(0, 0)).toBe(0);
  });
});
