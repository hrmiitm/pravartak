---
marp: true
title: Scaling Laws & Compute Optimization
description: Kaplan power laws, Chinchilla scaling, over-training, and compute budgeting.
theme: default
size: 16:9
paginate: true
---

# Scaling Laws & Compute Optimization

### Forecasting Loss and Sizing Compute Budgets

- Kaplan Power Laws vs Chinchilla Scaling
- Compute-optimal token-to-parameter ratio
- Inference-aware over-training
- Step-by-step FLOPs calculation

---

## Kaplan vs Chinchilla Scaling

```text
Total Pretraining Compute:  C ≈ 6 × N × D  (FLOPs)
```

- **Kaplan (2020)**: Parameter-heavy scaling ($N \propto C^{0.73}$, $D \propto C^{0.27}$)
- **Chinchilla (Hoffmann et al., 2022)**: Equal scaling ($N \propto C^{0.50}$, $D \propto C^{0.50}$)
  - **Rule of Thumb**: Train on **~20 tokens per parameter**.

| Model Size | Chinchilla Optimal Tokens |
|---|---|
| **1B Model** | ~20 Billion Tokens |
| **7B Model** | ~140 Billion Tokens |
| **70B Model** | ~1.4 Trillion Tokens |

---

## Beyond Chinchilla: Over-Training

- Serving costs dominate over model lifecycle:

$$C_{\text{total}} = 6 N D_{\text{train}} + 2 N T_{\text{inf}}$$

- **LLaMA 3 8B**: Trained on **15 Trillion tokens** ($\sim 93.75\times$ Chinchilla ratio)!
- Shrinking model parameters $N$ while training on more tokens significantly cuts downstream inference serving costs.

---

## Compute Budget Estimation Example

$$C = 6 \times N \times D$$

For 7B model on 1T tokens:

$$C = 6 \times (7 \times 10^9) \times (1 \times 10^{12}) = 4.2 \times 10^{22} \text{ FLOPs}$$

- **H100 GPU @ 40% MFU** = 400 TFLOP/s.
- **Compute Time**: $\sim 29.1$ GPU Hours ($\sim 3.6$ hours on 8× H100s).
