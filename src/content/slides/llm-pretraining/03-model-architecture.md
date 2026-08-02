---
marp: true
title: Transformer Model Architecture
description: Modern decoder-only architectural recipe — GQA, RoPE, Pre-RMSNorm, SwiGLU, and MoE.
theme: default
size: 16:9
paginate: true
---

# Transformer Model Architecture

### Deep Dive into Modern Decoder-Only LLMs

- Attention variants: MHA vs MQA vs GQA
- Rotary Position Embeddings (RoPE)
- Pre-RMSNorm & SwiGLU Feed-Forward Networks
- Mixture of Experts (MoE)

---

## Attention Variants (MHA vs MQA vs GQA)

```text
MHA: 8 Query Heads ──► 8 KV Heads  (100% KV-Cache Footprint)
MQA: 8 Query Heads ──► 1 KV Head   (12.5% Footprint, quality drop)
GQA: 8 Query Heads ──► 2 KV Heads  (25% Footprint, baseline quality)
```

- **Grouped-Query Attention (GQA)**: 8 query heads share 1 KV head group. Industry default for memory-efficient inference.

---

## Rotary Position Embeddings (RoPE)

- Rotates Query and Key vectors in complex space by position-dependent angle $m\Theta$:

$$q_m^\top k_n = (W^Q x_m)^\top R_\Theta^{(n-m)} (W^K x_n)$$

- Inner product depends purely on relative distance $(n-m)$.
- Increasing base frequency $\Theta$ (e.g. 10,000 $\rightarrow$ 500,000) unlocks 128K context window extension.

---

## Pre-RMSNorm & SwiGLU FFN

### Pre-RMSNorm
- Normalizes sublayer inputs before attention/FFN.
- Eliminates mean-centering calculations in LayerNorm ($\sim 10\%$ speedup).

### SwiGLU FFN
- Replaces standard ReLU/GELU with Gated Linear Unit:

$$\text{SwiGLU}(x) = (\text{Swish}(x W_1) \odot x W_3) W_2$$

---

## Mixture of Experts (MoE)

- Replaces dense FFN with sparse routing:
  - **Mixtral 8x7B**: 47B total parameters.
  - **Top-2 Routing**: Routes each token to top 2 experts ($K=2$).
  - **Active Params**: Activates only **13B parameters** per token.

| Model | Norm | Attention | Position | FFN | Vocab Size |
|---|---|---|---|---|---|
| **LLaMA 3** | Pre-RMSNorm | GQA | RoPE ($\Theta=500K$) | SwiGLU | 128,256 |
