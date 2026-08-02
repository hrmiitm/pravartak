---
marp: true
title: Distributed Training & 3D Parallelism
description: Scaling across GPU clusters with ZeRO, Tensor Parallelism, Pipeline Parallelism, and 3D Composition.
theme: default
size: 16:9
paginate: true
---

# Distributed Training & 3D Parallelism

### Scaling LLMs Across Large GPU Clusters

- Training memory breakdown ($16\Phi$ bytes)
- ZeRO Optimization Stages 1–3
- Tensor & Pipeline Parallelism
- 3D Parallelism & Mixed Precision

---

## Memory Footprint (7B Model Example)

$$\text{Memory} = 4\Phi \text{ (Weights)} + 4\Phi \text{ (Grads)} + 8\Phi \text{ (AdamW States)} = 16\Phi \text{ bytes}$$

- **Static Memory**: $7\text{B} \times 16 = \mathbf{112\text{ GB}}$ in FP32!
- Exceeds a single 80 GB A100 GPU before even allocating activation memory.

---

## ZeRO Optimization (Stages 1–3)

- **ZeRO-1**: Shards Optimizer States across GPUs (cuts memory ~4×)
- **ZeRO-2**: Shards Optimizer States + Gradients
- **ZeRO-3**: Shards Weights + Gradients + Optimizer States ($\frac{16\Phi}{N}$ memory per GPU)

```text
Memory Per GPU: ZeRO-3 reduces memory by factor N at cost of AllGather overhead
```

---

## Tensor & Pipeline Parallelism

### Tensor Parallelism (TP)
- Splits weight matrices column-wise and row-wise within a layer.
- Requires NVLink (900 GB/s) intra-node.

### Pipeline Parallelism (PP)
- Splits layers sequentially across nodes.
- **1F1B Schedule**: Alternates forward and backward passes to reduce activation memory bubbles.

---

## 3D Parallelism Composition

```text
TP (Within Node)   ──► NVLink High Bandwidth
PP (Across Nodes)  ──► InfiniBand Interconnect
DP / ZeRO (Cluster)──► Scale Across All Remaining Nodes
```

- **Mixed Precision**: BF16 is the standard pretraining precision (no loss scaling required). FP8 (E4M3/E5M2) boosts FLOPS on H100s.
