# frontend/CLAUDE.md

## Single product, multi-spec — not multi-product

The shop is architecturally locked to one product (甘露梨) rendered as multiple `SpecCard`s (see [MEMORY: 單一商品多規格]). Don't introduce a multi-product catalog abstraction unless explicitly asked.

## Target device

Target device baseline for the storefront is iPadOS 15 Safari/WebKit — avoid `transparent` in gradients and keep first-load images light (see project memory on frontend target).
