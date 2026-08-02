---
title: Training objectives
description: Causal Language Modeling (CLM), Masked Language Modeling (MLM), Span Corruption, Fill-in-the-Middle (FIM), and objective selection.
sidebar:
  order: 5
---

# Training objectives

The **training objective** defines the self-supervised task used to train the model over unlabelled text. The objective shapes the model's architectural constraints, data efficiency, and downstream capabilities.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>CLM · MLM · Span Corruption · FIM · UL2 · PDF</small></p>
  <a href="../../slides/llm-pretraining/04-training-objectives/">Open slide deck →</a>
</div>

## 1. Causal Language Modeling (CLM)

**CLM** (Next-Token Prediction) trains decoder-only models to predict token $x_t$ given all preceding tokens $x_{<t}$:

$$\mathcal{L}_{\text{CLM}}(\theta) = -\sum_{t=1}^{T} \log P(x_t \mid x_1, x_2, \ldots, x_{t-1}; \theta)$$

```text
Input Sequence:  The   cat   sat   on   the   mat
Target Output:   cat   sat   on   the   mat   <EOS>
Masking:         Causal triangular attention mask (cannot look ahead)
```

### Why CLM Dominates Modern LLMs
- **100% Data Efficiency**: Every token in the sequence serves as a target prediction label (unlike MLM's 15% masking rate).
- **Native Autoregressive Generation**: Aligns directly with text generation, chat, and reasoning loops.
- **Predictable Scaling**: Loss scales smoothly with compute according to power laws.

:::note
**Teacher Forcing**: During training, ground-truth prefix tokens are always fed into the model regardless of whether previous predictions were correct.
:::

## 2. Masked Language Modeling (MLM)

**MLM** (Devlin et al., 2019) replaces 15% of input tokens with `[MASK]` and trains a bidirectional encoder to reconstruct them:

$$\mathcal{L}_{\text{MLM}}(\theta) = -\sum_{i \in \mathcal{M}} \log P(x_i \mid x_{\backslash \mathcal{M}}; \theta)$$

- **15% Masking Rule**: 80% `[MASK]`, 10% random token, 10% unchanged.
- **Strength**: Unconstrained bidirectional context makes MLM exceptional for embeddings, classification, and extraction tasks.
- **Limitation**: Inefficient for text generation ($~6.7\times$ lower per-token supervision than CLM).

## 3. Fill-in-the-Middle (FIM) for Code

Standard CLM only learns left-to-right generation. Code completion requires infilling code at a cursor location between existing prefix and suffix blocks.

**FIM** (Bavarian et al., 2022) rearranges document segments into Prefix-Suffix-Middle format during pretraining:

```text
Original Document: [Prefix] [Middle] [Suffix]

FIM Transformation (PSM Format):
<PRE> [Prefix] <SUF> [Suffix] <MID> [Middle]
```

- **Zero Penalty**: Applying FIM to 50% of pretraining documents grants infilling capabilities with zero degradation to standard left-to-right performance.
- **Standard Objective**: Trained using standard cross-entropy loss over the transformed document.

## 4. Objective comparison matrix

| Objective | Architecture | Bidirectional Context | Generation Capable | Data Efficiency | Best Fit |
|---|---|---|---|---|---|
| **CLM** | Decoder-only | ❌ (Causal mask) | ✅ Excellent | High (100% tokens) | General LLMs, Code, Chat |
| **CLM + FIM** | Decoder-only | ⚠️ (Infilling via transform) | ✅ Excellent | High (100% tokens) | Code Models (StarCoder, CodeLlama) |
| **MLM** | Encoder-only | ✅ Full | ❌ Cannot generate | Low (15% tokens) | Text Embeddings, Classification |
| **Span Corruption** | Encoder-Decoder | ✅ Encoder / Causal Dec | ✅ Good | Medium (~15% spans) | T5, Structured Translation |
| **Prefix LM** | Decoder-only | ✅ Prefix / Causal Suffix | ✅ Good | High | PaLM, Conditional tasks |

:::important
For general-purpose LLMs, **CLM augmented with 50% FIM** is the industry recommended default.
:::

## Practice

Write a Python function that accepts a string, splits it into Prefix, Middle, Suffix, and formats it in FIM PSM format:
`<PRE> prefix <SUF> suffix <MID> middle`.

[Open the training objectives slide deck](../../slides/llm-pretraining/04-training-objectives/)
