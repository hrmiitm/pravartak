---
title: Tokenization & vocabulary design
description: Character vs word vs subword algorithms, Byte-Pair Encoding (BPE), WordPiece, Unigram, vocabulary size, and fertility trade-offs.
sidebar:
  order: 3
---

# Tokenization & vocabulary design

**Tokenization** is the bridge between human text and integer sequences processed by neural networks. It is the most upstream pipeline component: every character in a pretraining corpus passes through the tokenizer.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>BPE · Vocab Size · Fertility · Multilingual · PDF</small></p>
  <a href="../../slides/llm-pretraining/02-tokenization/">Open slide deck →</a>
</div>

## 1. From characters to subwords

| Strategy | Vocab Size | Sequence Length | Out-Of-Vocab (OOV) | Pros / Cons |
|---|---|---|---|---|
| **Character-Level** | ~100 – 256 | Very Long (5×–10×) | None | Zero OOV, but quadratic attention cost explodes on long sequences |
| **Word-Level** | 500,000+ | Short (1×) | High | Minimal sequence length, but massive embedding table & severe OOV issues |
| **Subword-Level** | 32,000 – 256,000 | Balanced (1.3×–1.5×) | None (Byte fallback) | Optimal balance: common words are single tokens, rare words split into subwords |

## 2. Byte-Pair Encoding (BPE) algorithm

**BPE** (Sennrich et al., 2016) is the standard subword tokenization algorithm used in GPT-2, GPT-4, LLaMA, and Mistral.

### Step-by-Step Training Walkthrough
1. **Initialize**: Start with base vocabulary of single characters/bytes (256 bytes for Byte-Level BPE).
2. **Count Pairs**: Iterate over corpus and count frequencies of adjacent token pairs.
3. **Merge Top Pair**: Merge the most frequent pair into a new subword token. Add it to vocabulary.
4. **Iterate**: Repeat counting and merging until target vocabulary size is reached.

```text
Initial Corpus:  l o w (×5),  l o w e r (×2)
Step 1: Merge (l, o)  → lo   │ Corpus: lo w (×5),  lo w e r (×2)
Step 2: Merge (lo, w) → low  │ Corpus: low (×5),   low e r (×2)
Step 3: Merge (e, r)  → er   │ Corpus: low (×5),   low er (×2)
Vocab added: ["lo", "low", "er"]
```

:::note
Modern LLMs use **Byte-Level BPE** (Radford et al., 2019). Operating on raw UTF-8 bytes guarantees that any string (emojis, non-Latin scripts, code, binary data) can be tokenized without `[UNK]` (out-of-vocabulary) errors.
:::

## 3. Tokenization algorithms comparison

- **BPE**: Bottom-up deterministic frequency merging. Ecosystem default (HuggingFace `tokenizers`, `tiktoken`).
- **WordPiece**: Maximizes likelihood of training data under a unigram language model when adding new tokens. Used by BERT.
- **Unigram LM**: Top-down probabilistic approach. Starts with large candidate set and prunes tokens that minimize loss increase. Used by SentencePiece and T5.

## 4. Vocabulary size & fertility trade-offs

**Fertility** is the average number of tokens required to encode a word. Lower fertility means shorter sequences and better compute efficiency.

| Vocab Size | Embedding Params ($d=4096$) | Fertility (English) | Pros / Cons |
|---|---|---|---|
| **32K** (LLaMA 1) | 131 Million | ~1.4 tokens/word | Small embedding table, but longer sequence lengths |
| **64K** | 262 Million | ~1.25 tokens/word | Good balance for monolingual models |
| **128K** (LLaMA 3) | 524 Million | ~1.1 tokens/word | Efficient sequence compression, multi-language support |
| **256K** (Gemma) | 1.05 Billion | ~1.05 tokens/word | Near word-level efficiency, but consumes >1B params in embeddings |

:::important
Always align vocabulary size to a multiple of **64** or **128** (e.g., 32,000, 128,256). Tensor cores on modern GPUs execute matrix multiplications significantly faster when matrix dimensions align with warp execution boundaries.
:::

## 5. Multilingual tokenization disparity

An English-dominated tokenizer creates severe tokenization disparity across languages:

```text
English:    "Hello world"            → 2 tokens (fertility = 1.0)
Hindi:      "नमस्ते दुनिया"          → 8 tokens (fertility = 4.0)
Chinese:    "你好世界"               → 6 tokens (fertility = 3.0)
```

### Mitigation Strategies
1. **Balanced Training Corpus**: Train tokenizer on a multilingual corpus proportional to desired target distribution.
2. **CJK Pre-segmentation**: Split CJK characters prior to BPE merging to prevent inefficient byte fallback.
3. **Expand Vocabulary**: Use 128K+ vocab sizes to reserve dedicated tokens for non-Latin alphabets and scripts.

## 6. Training a custom tokenizer with Python

```python
from tokenizers import Tokenizer, models, trainers, pre_tokenizers

# 1. Initialize Byte-Level BPE model
tokenizer = Tokenizer(models.BPE())
tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)

# 2. Configure BpeTrainer
trainer = trainers.BpeTrainer(
    vocab_size=32000,
    min_frequency=2,
    special_tokens=["<s>", "</s>", "<pad>", "<unk>"]
)

# 3. Train on sample text files
tokenizer.train(files=["corpus.txt"], trainer=trainer)
tokenizer.save("custom_bpe_tokenizer.json")
```

## Practice

1. Use HuggingFace `tokenizers` to train a 32K BPE tokenizer on Python source code vs English text.
2. Measure the fertility ratio of both tokenizers on code snippets.

[Open the tokenization slide deck](../../slides/llm-pretraining/02-tokenization/)
