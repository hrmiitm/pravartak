---
marp: true
title: Evaluation & Benchmarks
description: Perplexity, MFU, downstream evaluation suites, and decontamination strategies.
theme: default
size: 16:9
paginate: true
---

# Evaluation & Benchmarks

### Measuring Model Capabilities and Data Cleanliness

- Perplexity & MFU hardware metrics
- Standard zero-shot / few-shot benchmarks
- Evaluation frameworks (`lm-evaluation-harness`)
- Benchmark contamination detection

---

## Perplexity & Hardware Metrics

### Perplexity (PPL)

$$\text{PPL} = \exp \left( -\frac{1}{T} \sum_{t=1}^{T} \log P(x_t \mid x_{<t}) \right)$$

- Primary self-supervised progress signal during pretraining.
- Measure PPL on both in-domain and out-of-domain held-out validation sets.

### Model FLOPs Utilization (MFU)
- Healthy MFU on modern clusters is **40%–60%**.

---

## Standard Downstream Benchmarks

| Benchmark | Domain | Metric | What It Tests |
|---|---|---|---|
| **MMLU** | Knowledge | 5-shot Accuracy | 57 academic subjects |
| **HellaSwag** | Reasoning | 10-shot Accuracy | Sentence completion |
| **GSM8K** | Math | 5-shot Exact Match | Grade-school math reasoning |
| **HumanEval** | Code | pass@1 (0-shot) | Python function synthesis |
| **IFEval** | Instruction | Strict Accuracy | Verifiable constraint following |

---

## Benchmark Contamination Mitigation

- **Contamination**: Test questions leaking into pretraining web text.
- **Decontamination**:
  - Filter 13-gram / 8-gram overlaps against evaluation benchmarks before training.
  - Embed canary GUID strings in benchmark datasets.
  - Run perturbation analysis (swapping numbers/names) to detect verbatim memorization.

```text
Tooling: lm-evaluation-harness (EleutherAI) is the industry runner standard.
```
