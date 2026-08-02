---
marp: true
title: LLM Pretraining Overview
description: Overview, historical milestones, and decision framework for LLM pretraining from scratch.
theme: default
size: 16:9
paginate: true
---

# LLM Pretraining Overview

### Foundations of Large Language Models

- What pretraining installs in model weights
- Pretraining vs fine-tuning paradigm shift
- Timeline of major pretraining milestones
- When to pretrain vs fine-tune

---

## What is Pretraining?

- **Self-Supervised Learning**: Learning statistical language structure from trillions of unlabelled tokens
- **Compute Heavyweight**: Accounts for **~99%** of compute, time, and budget in the LLM lifecycle
- **Base Knowledge Installation**: Installs facts, grammar, world knowledge, and reasoning primitives

<!-- notes
Emphasize that alignment (SFT/RLHF) only steers pre-existing pretrained capabilities.
-->

---

## Pretraining Paradigm Shift

```text
Before 2018: Task-Specific Models
[Sentiment Data] ──► Sentiment Model
[Parallel Text]   ──► Translation Model

Post-2018: Pretrain ──► Adapt
[Trillions of Web Tokens] ──► Pretrained Base Model ──► Adapt (SFT/DPO/Prompting)
```

- **One Model, Endless Tasks**: A single pretraining run powers downstream applications.

---

## Major Pretraining Milestones

| Year | Model | Parameters | Tokens | Innovation |
|---|---|---|---|---|
| 2018 | GPT-1 | 117M | ~5B | CLM pretraining + fine-tuning |
| 2019 | BERT | 340M | ~3.3B | Masked language modeling |
| 2020 | GPT-3 | 175B | 300B | In-context learning at scale |
| 2022 | Chinchilla | 70B | 1.4T | Compute-optimal scaling laws |
| 2023 | LLaMA | 7B–65B | 1–1.4T | Open-weight pretraining recipe |
| 2024 | LLaMA 3 | 8B–405B | 15T+ | Over-training & 128K vocabulary |

---

## When to Pretrain from Scratch?

### ✅ Pretrain from Scratch when:
- Highly specialized domain distribution (medical, legal, molecular)
- Custom symbolic/multilingual tokenization requirements
- Need total control over dataset lineage, licensing, and safety

### ❌ Do NOT Pretrain when:
- Use case can be solved by fine-tuning an open base model
- Dataset size is $< 50\text{B}$ tokens (small scratch runs underperform)

---

## The End-to-End Pipeline

1. **Data Curation**: Web filtering, deduplication (MinHash/Suffix Arrays), mixing
2. **Tokenization**: Subword BPE, vocabulary size tuning, fertility
3. **Architecture**: Pre-RMSNorm, RoPE, GQA, SwiGLU, MoE
4. **Objectives**: CLM, Fill-in-the-Middle (FIM)
5. **Distributed Systems**: 3D Parallelism, ZeRO 1–3, Mixed Precision
6. **Scaling Laws**: Kaplan vs Chinchilla compute budgeting
7. **Evaluation**: Perplexity, MMLU, GSM8K, decontamination
