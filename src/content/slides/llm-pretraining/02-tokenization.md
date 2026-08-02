---
marp: true
title: Tokenization & Vocabulary Design
description: Subword algorithms, Byte-Pair Encoding (BPE), vocabulary sizing, fertility, and multilingual considerations.
theme: default
size: 16:9
paginate: true
---

# Tokenization & Vocabulary Design

### Interfacing Text with Neural Networks

- Character vs Word vs Subword tokenization
- Byte-Pair Encoding (BPE) walkthrough
- Vocabulary size & fertility trade-offs
- Multilingual tokenization disparity

---

## Why Subword Tokenization?

| Level | Vocab Size | Sequence Length | OOV Errors |
|---|---|---|---|
| **Character** | ~256 | Very Long (5×–10×) | None |
| **Word** | 500K+ | Short (1×) | Severe |
| **Subword** | 32K – 256K | Balanced (1.3×–1.5×) | None (Byte fallback) |

- Subword algorithms balance sequence length and vocabulary embedding parameters.

---

## Byte-Pair Encoding (BPE) Algorithm

```text
Corpus:  l o w (×5),  l o w e r (×2)
Step 1:  Merge (l, o)  ──► lo   │ Corpus: lo w (×5),  lo w e r (×2)
Step 2:  Merge (lo, w) ──► low  │ Corpus: low (×5),   low e r (×2)
Step 3:  Merge (e, r)  ──► er   │ Corpus: low (×5),   low er (×2)
```

- **Byte-Level BPE**: Operates on raw UTF-8 bytes. Guarantees zero `[UNK]` errors for any input text or binary payload.

---

## Vocab Size & Fertility Trade-offs

- **Fertility**: Average number of tokens per word.
- **32K Vocab (LLaMA 1)**: Small embedding table, higher fertility (~1.4 tokens/word).
- **128K Vocab (LLaMA 3)**: Shorter sequences (~1.1 tokens/word), better multilinguality, larger embedding footprint.

```text
Rule of Thumb: Align vocab size to a multiple of 64 or 128 for GPU Tensor Core speedup!
```

---

## Multilingual Tokenization Disparity

- Tokenizers trained mainly on English fragment non-Latin scripts into byte fallbacks:
  - English: `"Hello world"` $\rightarrow$ 2 tokens
  - Hindi: `"नमस्ते दुनिया"` $\rightarrow$ 8 tokens
- **Fix**: Train BPE on a balanced multilingual corpus or increase vocab size to 128K–256K.
