---
title: Distributed training & 3D parallelism
description: Data Parallelism (DDP), ZeRO stages 1-3, Tensor Parallelism (TP), Pipeline Parallelism (PP), 3D Parallelism, and mixed precision.
sidebar:
  order: 6
---

# Distributed training & 3D parallelism

A 70B parameter model in FP16 occupies **140 GB** just for weights — far exceeding a single 80 GB A100/H100 GPU. Accounting for optimizer states, gradients, and activations, training requires scaling across hundreds or thousands of GPUs.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>DDP · ZeRO 1-3 · Tensor Parallel · Pipeline · 3D · PDF</small></p>
  <a href="../../slides/llm-pretraining/05-distributed-training/">Open slide deck →</a>
</div>

## 1. Memory footprint breakdown (7B Model Example)

Training with AdamW optimizer in FP32 requires:

$$\text{Memory} = \underbrace{4\Phi}_{\text{Weights}} + \underbrace{4\Phi}_{\text{Gradients}} + \underbrace{8\Phi}_{\text{AdamW States (2 moments)}} = 16\Phi \text{ bytes}$$

For a 7B parameter model ($\Phi = 7\times 10^9$):
- **Weights (FP32)**: 28 GB
- **Gradients (FP32)**: 28 GB
- **AdamW Optimizer States**: 56 GB
- **Total Static Memory**: **112 GB** (excluding activation memory)!

## 2. ZeRO Optimization (Stages 1–3)

ZeRO (Zero Redundancy Optimizer, Rajbhandari et al., 2020) eliminates memory redundancy by sharding state across data-parallel GPUs:

```text
STANDARD DDP       │ Full Weights   │ Full Gradients │ Full Optimizer States
───────────────────┼────────────────┼────────────────┼───────────────────────
ZeRO Stage 1       │ Full Weights   │ Full Gradients │ SHARDED Optimizer
ZeRO Stage 2       │ Full Weights   │ SHARDED Grads  │ SHARDED Optimizer
ZeRO Stage 3       │ SHARDED Weight │ SHARDED Grads  │ SHARDED Optimizer
```

| Strategy | Sharded State | Memory / GPU ($N$ GPUs) | Extra Communication |
|---|---|---|---|
| **DDP** | None (Replicated) | $16\Phi$ | AllReduce (Gradients) |
| **ZeRO-1** | Optimizer States | $4\Phi + 4\Phi + \frac{8\Phi}{N}$ | Minimal |
| **ZeRO-2** | Optimizer + Gradients | $4\Phi + \frac{12\Phi}{N}$ | Minimal |
| **ZeRO-3** | Weights + Grads + Optimizer | $\frac{16\Phi}{N}$ | AllGather (Forward + Backward) |

## 3. Tensor Parallelism (TP)

**Tensor Parallelism** (Shoeybi et al., 2019) splits individual weight matrices **within** a layer across GPUs.

```text
Column-Parallel Linear (QKV Projection):
Input X ──► [ GPU 0: W_1 ] ──► Y_1 ──┐
        └──► [ GPU 1: W_2 ] ──► Y_2 ──┴──► Concat(Y_1, Y_2)

Row-Parallel Linear (Output Projection):
[ GPU 0: X_1 W_1 ] ──┐
[ GPU 1: X_2 W_2 ] ──┴──► AllReduce(Sum) ──► Output Y
```

:::tip
TP requires ultra-high bandwidth (NVLink @ 900 GB/s on H100). Keep TP degree bounded within a single node (e.g. $TP=4$ or $TP=8$).
:::

## 4. Pipeline Parallelism (PP)

**Pipeline Parallelism** divides model layers sequentially across GPU nodes.

```text
GPU 0 (Layers 1-20)   ──► Forward ──► GPU 1 (Layers 21-40) ──► Forward ──► GPU 2...
                      ◄── Backward ◄──                       ◄── Backward ◄──
```

### 1F1B Schedule (One Forward, One Backward)
To minimize memory overhead from holding activations, 1F1B alternates execution of forward and backward passes across micro-batches, reducing the pipeline bubble fraction to:

$$\text{Bubble Fraction} \approx \frac{P - 1}{M}$$

Where $P$ is the number of pipeline stages and $M$ is the number of micro-batches ($M \gg P$).

## 5. 3D Parallelism composition

Production pretraining combines all three strategies in a 3D grid:

$$\text{Total GPUs} = \text{TP Degree} \times \text{PP Degree} \times \text{DP Degree}$$

```text
       ┌───────────────────────────────────────┐
       │     3D Parallelism Topology           │
       ├───────────────────────────────────────┤
       │ TP (Node Level)    │ NVLink Intra-Node│
       │ PP (Rack Level)    │ InfiniBand Inter │
       │ DP / ZeRO (Cluster)│ Scale Across     │
       └───────────────────────────────────────┘
```

## 6. Mixed precision formats (FP16 vs BF16 vs FP8)

- **FP16**: 5-bit exponent, 10-bit mantissa. Prone to underflow; requires dynamic loss scaling.
- **BF16**: 8-bit exponent, 7-bit mantissa. Matches FP32 dynamic range. **Industry standard for pretraining**.
- **FP8 (E4M3 / E5M2)**: Native on Hopper GPUs (H100). 2× FLOPS boost for matrix multiplies, requiring per-tensor scaling factors.

## Practice

Calculate total GPU memory required to train a 13B model under:
1. Standard DDP (FP32 AdamW).
2. ZeRO-2 across 8 GPUs.
3. ZeRO-3 across 64 GPUs.

[Open the distributed training slide deck](../../slides/llm-pretraining/05-distributed-training/)
