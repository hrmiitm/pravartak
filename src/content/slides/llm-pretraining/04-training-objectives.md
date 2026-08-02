---
marp: true
title: Pretraining Training Objectives
description: CLM, MLM, Fill-in-the-Middle (FIM), and objective trade-offs.
theme: default
size: 16:9
paginate: true
---

# Pretraining Training Objectives

### Self-Supervised Objectives for Foundation Models

- Next-token prediction: Causal Language Modeling (CLM)
- Masked Language Modeling (MLM)
- Fill-in-the-Middle (FIM) for code infilling
- Objective selection matrix

---

## Causal Language Modeling (CLM)

$$\mathcal{L}_{\text{CLM}}(\theta) = -\sum_{t=1}^{T} \log P(x_t \mid x_{<t}; \theta)$$

- Trains decoder-only models to predict the next token given preceding context.
- **100% Data Efficiency**: Every token in the sequence serves as a training target.
- **Teacher Forcing**: Ground-truth tokens are fed into the model during training.

---

## Fill-in-the-Middle (FIM) for Code

- Standard CLM cannot generate text in the middle of a cursor location.
- **FIM PSM Transformation**:

```text
Original: [Prefix] [Middle] [Suffix]
Transformed: <PRE> [Prefix] <SUF> [Suffix] <MID> [Middle]
```

- Applying FIM to **50% of code documents** adds infilling capabilities with **zero loss** in standard generation benchmarks!

---

## Objectives Matrix

| Objective | Architecture | Generation | Efficiency | Primary Use Case |
|---|---|---|---|---|
| **CLM** | Decoder | ✅ Excellent | 100% Tokens | General LLMs / Chat |
| **CLM + FIM** | Decoder | ✅ Excellent | 100% Tokens | Code Models (StarCoder) |
| **MLM** | Encoder | ❌ None | 15% Tokens | Text Embeddings / BERT |
| **Span Corruption** | Enc-Dec | ✅ Good | 15% Spans | T5 / Translation |
