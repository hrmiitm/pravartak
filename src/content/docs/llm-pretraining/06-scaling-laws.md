---
title: Scaling laws & compute optimization
description: Kaplan power laws vs Chinchilla compute-optimal scaling, over-training strategies, and inference-aware budget allocation.
sidebar:
  order: 7
---

# Scaling laws & compute optimization

**Scaling laws** describe mathematical power-law relationships between compute budget ($C$), parameters ($N$), tokens ($D$), and pretraining loss ($L$). They allow engineers to predict model loss before launching multi-million-dollar runs.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>Kaplan · Chinchilla · Over-training · Inference Budget · PDF</small></p>
  <a href="../../slides/llm-pretraining/06-scaling-laws/">Open slide deck →</a>
</div>

## 1. Power laws in neural scaling

Kaplan et al. (2020) demonstrated that test loss $L$ follows clean power laws across several orders of magnitude:

$$L(N) \approx \left(\frac{N_c}{N}\right)^{\alpha_N}, \quad L(D) \approx \left(\frac{D_c}{D}\right)^{\alpha_D}, \quad L(C) \approx \left(\frac{C_c}{C}\right)^{\alpha_C}$$

```text
Log Loss (L)
   │
   │───\
   │    ───\
   │        ───\  Power Law Regime (Clean Linear Slope on Log-Log Scale)
   │            ───\
   │                ───\───────────── Irreducible Loss (E)
   └─────────────────────────────────── Log Compute / Parameters / Tokens
```

## 2. Kaplan vs Chinchilla scaling

```text
COMPUTE FLOP FORMULA:  C ≈ 6 × N × D
```

| Dimension | Kaplan Scaling (2020) | Chinchilla Scaling (Hoffmann et al., 2022) |
|---|---|---|
| **Parameter Scaling** | $N \propto C^{0.73}$ (Param-heavy) | $N \propto C^{0.50}$ (Equal scaling) |
| **Token Scaling** | $D \propto C^{0.27}$ (Data-light) | $D \propto C^{0.50}$ (Equal scaling) |
| **Optimal Token-to-Param Ratio** | ~5 tokens per parameter | **~20 tokens per parameter** |

:::important
Chinchilla proved that 70B parameters trained on 1.4T tokens matches a 280B model trained on 300B tokens while using **4× less memory and inference compute**.
:::

### Chinchilla Token Benchmarks
- **1B Model**: ~20 Billion Tokens
- **7B Model**: ~140 Billion Tokens
- **70B Model**: ~1.4 Trillion Tokens

## 3. Beyond Chinchilla: Over-training

Modern foundation models (LLaMA 1, LLaMA 3) deliberately **over-train** far past the Chinchilla-optimal point:

```text
Model         Parameters   Chinchilla Tokens   Actual Tokens   Over-training Ratio
LLaMA 1 7B    7 Billion    140 Billion         1.0 Trillion    ~7.1×
LLaMA 3 8B    8 Billion    160 Billion         15.0 Trillion   ~93.75×
```

### Why Over-train?
Inference costs dominate over a model's operational lifecycle:

$$C_{\text{total}} = C_{\text{train}} + C_{\text{inference}} = 6ND_{\text{train}} + 2NT_{\text{inf\_tokens}}$$

When a model will serve trillions of user inference requests, spending additional training compute to shrink parameter size $N$ drastically reduces total lifecycle cost.

## 4. Calculating compute budgets

For a standard Transformer:

$$\text{Total Training FLOPs } (C) \approx 6 \times N \times D$$

### H100 Hardware Estimate Example
- 1 GPU H100 BF16 Peak = 1,000 TFLOP/s ($10^{15}$ FLOP/s).
- Realistic Model FLOPs Utilization (MFU) = 40% (400 TFLOP/s).
- **Training 7B model on 1T tokens**:

$$C = 6 \times (7 \times 10^9) \times (1 \times 10^{12}) = 4.2 \times 10^{22} \text{ FLOPs}$$

$$\text{Seconds} = \frac{4.2 \times 10^{22}}{400 \times 10^{12}} = 105,000 \text{ sec} \approx 29.1 \text{ GPU Hours}$$

Across 8× H100 GPUs, this run completes in **~3.6 hours**.

## Practice

1. Calculate the total FLOPs required to pretrain a 70B parameter model on 2T tokens.
2. Estimate the number of H100 GPUs needed to complete the run in 14 days assuming 45% MFU.

[Open the scaling laws slide deck](../../slides/llm-pretraining/06-scaling-laws/)
