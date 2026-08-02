---
title: LLM pretraining
description: Master reference and learning path for pretraining Large Language Models from scratch.
sidebar:
  label: Overview
  order: 1
---

# Overview

**Pretraining** is the foundational stage in which a model learns the statistical structure, syntax, world knowledge, and reasoning primitives of language from massive unlabelled text corpora. It accounts for ~99% of compute and time in the LLM lifecycle.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>Overview · Timeline · Strategy · PDF</small></p>
  <a href="../../slides/llm-pretraining/overview/">Open slide deck →</a>
</div>

## 1. The pretraining paradigm shift

Before the pretrain-and-fine-tune era, NLP models were task-specific: sentiment analysis, machine translation, or named entity recognition each required separate models trained on custom task datasets.

The **pretrain → adapt** paradigm upended this approach:
1. **Pretraining**: Train a single large Transformer on trillions of tokens using self-supervised objectives (e.g., next-token prediction).
2. **Adaptation**: Fine-tune or align (SFT, DPO/RLHF, or in-context prompting) for any downstream task with minimal labelled data.

:::note
Pretraining installs capabilities, facts, and reasoning patterns into model weights. Subsequent alignment (SFT, RLHF) merely **steers** those existing capabilities toward desired instruction-following behaviors.
:::

## 2. Key pretraining milestones

The evolution from GPT-1 to modern foundation models illustrates the exponential scaling trajectory of parameters, data, and innovations:

| Year | Model | Parameters | Tokens | Key Innovation |
|---|---|---|---|---|
| **2018** | GPT-1 | 117M | ~5B | Generative pretraining + task fine-tuning |
| **2019** | BERT | 340M | ~3.3B | Masked language modeling (bidirectional) |
| **2019** | GPT-2 | 1.5B | ~10B | Scaled CLM, zero-shot task transfer |
| **2020** | GPT-3 | 175B | 300B | In-context learning (few-shot prompting) |
| **2020** | T5 | 11B | ~1T | Unified text-to-text span corruption |
| **2022** | Chinchilla | 70B | 1.4T | Compute-optimal scaling laws |
| **2023** | LLaMA | 7B–65B | 1–1.4T | Open-weight efficient pretraining recipe |
| **2023** | Mistral | 7B | Undisclosed | Sliding window attention, GQA |
| **2024** | LLaMA 3 | 8B–405B | 15T+ | Massive over-training & 128K vocab |

## 3. When should you pretrain from scratch?

Pretraining a 7B-parameter model on 1T+ tokens costs $100,000–$300,000+ in cloud compute. It is a last resort, not a starting point.

Pretraining from scratch is justified when:
- **Unique Domain & Distribution**: Medical, legal, financial, or scientific text has a fundamentally different vocabulary and statistical structure than general web crawls.
- **Custom Tokenizer Needed**: Highly multilingual, code-heavy, or specialized symbolic domains (chemistry, math) perform poorly on standard English-centric tokenizers.
- **Full Control & Ownership**: Complete control over training data lineage, license compliance, and safety properties.
- **Core Scaling Research**: Studying architecture, data mixtures, or optimization dynamics.

:::caution[Avoid this common pitfall]
Pretraining from scratch on a small domain corpus (e.g., 10B medical tokens) will almost always **underperform** fine-tuning an open base model (e.g., LLaMA 3 8B) on those same 10B tokens. Base models bring massive general reasoning and language understanding that small scratch runs cannot replicate.
:::

## 4. Pretraining pipeline overview

This workshop walks through every stage of the pretraining engineering pipeline:

```text
Raw Web Crawl / Books / Code
       │
       ▼
 1. Data Curation & Filtering (Deduplication, Quality Heuristics, Mixing)
       │
       ▼
 2. Tokenization (Byte-Pair Encoding, Vocabulary Size, Fertility)
       │
       ▼
 3. Architecture Design (Pre-RMSNorm, RoPE, GQA, SwiGLU, MoE)
       │
       ▼
 4. Training Objectives (CLM, MLM, Fill-in-the-Middle)
       │
       ▼
 5. Distributed Systems (3D Parallelism, ZeRO-1..3, Mixed Precision)
       │
       ▼
 6. Scaling Laws (Kaplan vs Chinchilla, Over-training Ratios)
       │
       ▼
 7. Evaluation & Benchmarks (Perplexity, MMLU, Decontamination)
       │
       ▼
 8. Practical Tips & Engineering (Loss Spikes, LR Schedules, Fault Tolerance)
```

## Practice

Define your target use case:
1. Estimate whether fine-tuning an existing base model meets your requirements.
2. If pretraining is required, identify your primary domain constraints (vocabulary, language distribution, compute budget).

[Open the overview slide deck](../../slides/llm-pretraining/overview/)
