---
title: Practical tips & gotchas
description: Learning rate schedules, initialization scaling, loss spike debugging, fault tolerance, and hyperparameter cheat sheets.
sidebar:
  order: 9
---

# Practical tips & gotchas

Pretraining an LLM at scale is complex systems engineering. This page distills practical lessons, hyperparameter defaults, and debugging playbooks from real-world training runs.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>LR Schedules · Loss Spikes · Fault Tolerance · Cheat Sheet · PDF</small></p>
  <a href="../../slides/llm-pretraining/08-practical-tips/">Open slide deck →</a>
</div>

## 1. Learning rate schedules & warmup

The standard pretraining schedule uses **Linear Warmup + Cosine Decay**:

$$\eta_t = \eta_{\text{min}} + \frac{1}{2}(\eta_{\text{max}} - \eta_{\text{min}})\left(1 + \cos\left(\frac{t - T_w}{T - T_w} \cdot \pi\right)\right)$$

```text
Learning Rate
  ▲
η │     /────────────────────────────\
  │    /  Warmup                       \  Cosine Decay
  │   /  (2,000 steps)                  \
  │  /                                    \
  │ /                                       \
0 └─┴─────────────────────────────────────────┴──► Training Steps
```

### WSD (Warmup-Stable-Decay) Schedule
An increasingly popular alternative: constant learning rate between warmup and a short 10% decay phase. Allows flexible checkpointing and extending training runs without committing to a fixed step horizon $T$ upfront.

## 2. Hyperparameter defaults cheat sheet

| Hyperparameter | Recommended Value | Reference Source |
|---|---|---|
| **Optimizer** | AdamW ($\beta_1=0.9, \beta_2=0.95, \epsilon=10^{-8}$) | LLaMA / GPT-3 |
| **Weight Decay** | $0.1$ | LLaMA / Mistral |
| **Gradient Clipping** | Max norm $1.0$ | Universal |
| **Warmup Steps** | 2,000 steps (or 1%–2% total tokens) | LLaMA 3 |
| **Peak Learning Rate** | $3 \times 10^{-4}$ (7B) / $1.5 \times 10^{-4}$ (70B) | Scale-dependent |
| **Dropout** | **0.0 (Disabled)** | Modern LLMs |
| **Batch Size Ramp-up** | Start @ 512K tokens $\rightarrow$ Ramp to 4M+ tokens | GPT-3 / LLaMA |

:::note
Modern LLMs use **zero dropout** during pretraining. Datasets with trillions of tokens provide sufficient implicit regularization. Dropout introduces noise that hinders final loss convergence.
:::

## 3. Loss spike debugging playbook

Loss spikes occur when gradients suddenly explode during training:

```text
Loss
  ▲
  │       ▲ Spikes!
  │      / \
  │───/\─/   \──/\──────── Loss Recovers (Normal)
  │               \────── Loss Diverges to NaN (Fatal)
  └────────────────────────► Steps
```

### Diagnostic Steps
1. **Check Gradient Norm**: If gradient norm exceeds $> 10.0$, gradient clipping is failing to catch an anomalous batch.
2. **Inspect Data Batch**: Log token IDs of the batch preceding the spike. Look for repetitive corrupted text, malformed HTML, or binary noise.
3. **Numerical Instability**: In FP16 attention, $Q K^\top / \sqrt{d_k}$ values can overflow. Apply **Attention Logit Capping** or switch to BF16.
4. **Recovery**: If loss recovers within 100–500 steps, let training proceed. If loss diverges to `NaN`, roll back to checkpoint $N-2000$ steps and skip the bad data batch.

## 4. Initialization scaling

To prevent residual variance from growing linearly with model depth $L$:
- Initialize standard weights from $\mathcal{N}(0, 0.02)$.
- Scale output projection weights in residual blocks by $\frac{1}{\sqrt{2L}}$.

## 5. Checkpointing & fault tolerance

In multi-node clusters (1,000+ GPUs), hardware failures occur daily:
- **Save Frequency**: Save full checkpoints every 500–1,000 steps (~30–60 mins).
- **Asynchronous Checkpointing**: Use PyTorch `dcp` (Distributed Checkpoint) to save states asynchronously to NVMe storage without pausing GPU compute.
- **Save Optimizer States**: Always save AdamW first/second moment estimates for exact resumption.

## 6. Budget-friendly pretraining roadmap

```text
┌─────────────────────────────────────────────────────────────┐
│  $1,000 Run   │ 125M Model @ 2.5B Tokens (~8h on 1× A100)   │
│  $10,000 Run  │ 1B Model   @ 20B Tokens  (~3 days on 8× A100)│
└─────────────────────────────────────────────────────────────┘
```

:::tip
Always test code, tokenizers, data pipelines, and distributed scripts on a **125M model** first. It catches 90% of infrastructure bugs in minutes before launching multi-GPU scale runs.
:::

## Practice

Review your training plan:
1. Confirm that dropout is disabled ($0.0$).
2. Verify AdamW hyperparameter settings ($\beta_1=0.9, \beta_2=0.95$).
3. Set up automated checkpoint rotation keeping the latest 3 rolling checkpoints.

[Open the practical tips slide deck](../../slides/llm-pretraining/08-practical-tips/)
