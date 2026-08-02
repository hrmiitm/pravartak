---
title: Transformer model architecture
description: Deep dive into modern decoder-only architectures — GQA, RoPE, Pre-RMSNorm, SwiGLU FFN, and Mixture of Experts (MoE).
sidebar:
  order: 4
---

# Transformer model architecture

Modern LLM architectures (LLaMA 3, Mistral, Gemma 2) differ significantly from the original Transformer (Vaswani et al., 2017). This page details the exact architectural components used in production foundation models.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>GQA · RoPE · RMSNorm · SwiGLU · MoE · PDF</small></p>
  <a href="../../slides/llm-pretraining/03-model-architecture/">Open slide deck →</a>
</div>

## 1. Modern Transformer block layout

```text
       Input Token IDs
             │
             ▼
     Embedding Layer
             │
 ┌───────────┴───────────┐
 │ ┌───────────────────┐ │
 │ │ Pre-RMSNorm       │ │
 │ ├───────────────────┤ │
 │ │ RoPE + FlashGQA   │ │ (Attention Sublayer)
 │ └─────────┬─────────┘ │
 │           ├───────────┤ (Residual Add)
 │ ┌─────────┴─────────┐ │
 │ │ Pre-RMSNorm       │ │
 │ ├───────────────────┤ │
 │ │ SwiGLU FFN / MoE  │ │ (Feed-Forward Sublayer)
 │ └─────────┬─────────┘ │
 │           ├───────────┤ (Residual Add)
 └───────────┬───────────┘
             │ × N Layers
             ▼
      Final RMSNorm
             │
             ▼
   Linear Head (LM Head)
```

## 2. Attention variants (MHA vs MQA vs GQA)

Autoregressive inference caches Key ($K$) and Value ($V$) tensors for all prior tokens. For full **Multi-Head Attention (MHA)**, the KV-cache consumes massive memory:

$$\text{KV Cache Size (bytes)} = 2 \times L \times H_{kv} \times d_{head} \times S \times \text{bytes\_per\_elem}$$

For a 70B model ($L=80$, $H=64$, $d_{head}=128$, $S=4096$ in FP16), full MHA requires **~10 GB per sequence**!

```text
Multi-Head Attention (MHA)        Multi-Query Attention (MQA)       Grouped-Query Attention (GQA)
 Q Q Q Q   K K K K   V V V V       Q Q Q Q      K      V            Q Q Q Q   Q Q Q Q     K K   V V
 └─┴─┴─┘   └─┴─┴─┘   └─┴─┴─┘       └─┴─┴─┘      │      │            └───┬───┘   └───┬───┘     │ │   │ │
  8 Heads   8 Heads   8 Heads       8 Heads   1 Head 1 Head          Group 1  Group 2    2 KV Heads
```

| Attention Variant | Query Heads ($H_q$) | KV Heads ($H_{kv}$) | KV Cache Footprint | Downstream Quality |
|---|---|---|---|---|
| **Multi-Head (MHA)** | $H$ | $H$ | 100% (Baseline) | Baseline |
| **Multi-Query (MQA)** | $H$ | $1$ | $1/H$ (~12.5%) | Degradation in complex reasoning |
| **Grouped-Query (GQA)** | $H$ | $G = H/8$ | $1/8$ (12.5%) | Quality parity with MHA |

:::tip
**Grouped-Query Attention (GQA)** with 8 query heads per KV head is the industry default. LLaMA 3 70B uses $H_q=64$ and $H_{kv}=8$, reducing KV-cache by 8× with zero loss in benchmarks.
:::

## 3. Rotary Position Embeddings (RoPE)

RoPE (Su et al., 2021) encodes relative position by rotating Query and Key vectors in complex space by an angle proportional to position $m$:

$$q_m = R_\Theta^{(m)} W^Q x_m, \quad k_n = R_\Theta^{(n)} W^K x_n$$

$$q_m^\top k_n = (W^Q x_m)^\top R_\Theta^{(n-m)} (W^K x_n)$$

### Key Advantages
- **Relative Distance**: The inner product $q_m^\top k_n$ depends strictly on distance $(n-m)$.
- **Context Window Extension**: Adjusting the base frequency parameter $\Theta$ (e.g. increasing $\Theta$ from $10,000$ to $500,000$ in LLaMA 3) enables context extrapolation from 8K to 128K tokens.

## 4. Normalization (Pre-RMSNorm)

Modern models use **Pre-RMSNorm** (Zhang & Sennrich, 2019) instead of Post-LayerNorm:

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_{i=1}^d x_i^2 + \epsilon}} \odot \gamma$$

1. **Pre-Norm Placement**: Normalizes sublayer inputs rather than residual outputs, stabilizing gradients in 80+ layer networks.
2. **Mean Removal**: Removes mean-centering calculation from LayerNorm, speeding up kernel execution by ~7%–10% without affecting model convergence.

## 5. Feed-Forward Networks (SwiGLU)

Standard FFNs use two projections with ReLU. Modern LLMs use **SwiGLU** (Shazeer, 2020):

$$\text{SwiGLU}(x) = \left( \text{Swish}(x W_1) \odot x W_3 \right) W_2$$

where $\text{Swish}(x) = x \cdot \sigma(\beta x)$.

:::important
SwiGLU uses **three** weight matrices ($W_1, W_2, W_3$) instead of two. To maintain equivalent parameter counts to a standard $4d$ FFN, the hidden dimension is set to $\frac{8}{3}d$ (rounded to nearest multiple of 256).
:::

## 6. Mixture of Experts (MoE)

**MoE** (e.g., Mixtral 8x7B) replaces dense FFN layers with a sparse routing mechanism:

$$y = \sum_{i=1}^{K} g_i(x) \cdot \text{Expert}_i(x)$$

- **Total vs Active Parameters**: Mixtral 8x7B has 47B total parameters, but routes each token to Top-2 experts ($K=2$), activating only 13B parameters per token during forward pass.
- **Routing & Load Balancing**: An auxiliary loss prevents "expert collapse" (where all tokens route to 1 or 2 dominant experts).

## 7. Foundation model recipe matrix

| Model | Normalization | Attention | Position | FFN | Bias Terms | Vocab Size |
|---|---|---|---|---|---|---|
| **LLaMA 3** | Pre-RMSNorm | GQA (8:1) | RoPE ($\Theta=500K$) | SwiGLU | None | 128,256 |
| **Mistral 7B** | Pre-RMSNorm | GQA + Sliding Window | RoPE ($\Theta=10K$) | SwiGLU | None | 32,000 |
| **Gemma 2** | Pre-RMSNorm | GQA + Local/Global | RoPE | GeGLU | None | 256,000 |

[Open the architecture slide deck](../../slides/llm-pretraining/03-model-architecture/)
