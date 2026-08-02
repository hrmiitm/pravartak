---
marp: true
title: Practical Tips & Gotchas
description: Learning rate schedules, hyperparameter defaults, loss spike debugging, and budget setups.
theme: default
size: 16:9
paginate: true
---

# Practical Tips & Gotchas

### Engineering Lessons from Production Runs

- Warmup + Cosine & WSD schedules
- Hyperparameter cheat sheet
- Loss spike debugging playbook
- Budget-friendly pretraining roadmap

---

## Learning Rate Schedules

```text
Linear Warmup (2,000 steps) ──► Cosine Decay (to 10% peak LR)
```

- **WSD (Warmup-Stable-Decay)**: Constant learning rate phase followed by a 10% decay phase. Enables extending training runs flexibly.

---

## Hyperparameter Cheat Sheet

| Parameter | Recommended Value | Source |
|---|---|---|
| **Optimizer** | AdamW ($\beta_1=0.9, \beta_2=0.95$) | LLaMA / GPT-3 |
| **Weight Decay** | 0.1 | Universal |
| **Gradient Clipping** | Max norm 1.0 | Universal |
| **Warmup Steps** | 2,000 steps | LLaMA 3 |
| **Dropout** | **0.0 (Disabled)** | Modern LLMs |
| **Batch Size** | Ramp 512K $\rightarrow$ 4M+ tokens | GPT-3 / LLaMA |

---

## Loss Spike Debugging Playbook

- **Symptom**: Loss suddenly explodes during training.
- **Action**:
  1. Check gradient norm ($> 10.0$ indicates batch anomaly).
  2. Inspect token IDs of the batch preceding the spike (look for web garbage/binary noise).
  3. Apply **Attention Logit Capping** or switch FP16 to BF16.
  4. If loss diverges to NaN, rollback 2,000 steps and skip the corrupted batch.

---

## Budget-Friendly Pretraining

```text
$1,000 Run   │ 125M Model @ 2.5B Tokens (~8 hours on 1× A100 GPU)
$10,000 Run  │ 1B Model   @ 20B Tokens  (~3 days on 8× A100 GPUs)
```

- **Rule of 125M**: Always prototype tokenizers, data filters, and distributed scripts on a 125M model before scaling up!
