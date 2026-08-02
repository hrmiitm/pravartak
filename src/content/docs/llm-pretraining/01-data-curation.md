---
title: Data collection & curation
description: Filtering pipelines, exact and fuzzy deduplication, data mixing, and curriculum strategies for LLM pretraining.
sidebar:
  order: 2
---

# Data collection & curation

**Data quality** determines model quality. Pretraining data curation — filtering, deduplication, and mixing ratios — impacts final performance more than raw dataset size or hyperparameter tuning.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>Filtering · Deduplication · Mixing · Licensing · PDF</small></p>
  <a href="../../slides/llm-pretraining/01-data-curation/">Open slide deck →</a>
</div>

## 1. Sources of pretraining data

Modern pretraining corpora draw from diverse sources with varying quality, volume, and licensing profiles:

| Source | Examples | Quality Profile | Volume | Cost |
|---|---|---|---|---|
| **Web Crawl** | Common Crawl, C4, FineWeb | Variable (High noise) | Trillions of tokens | Low |
| **Books & Literature** | Project Gutenberg, Books3 | High (Long context) | ~30B tokens | Questionable legality |
| **Academic Papers** | ArXiv, S2ORC | High (Technical reasoning) | ~50B tokens | Low |
| **Source Code** | GitHub, The Stack | Variable (Structured logic) | ~500B tokens | Low |
| **Encyclopedia** | Wikipedia dumps | Very high (Factual signal) | ~4B tokens | Free |
| **Curated Datasets** | Dolma, RedPajama, DCLM | High (Pre-filtered) | 1T–5T tokens | Medium (Compute) |

:::note
Common Crawl contains >250 billion web pages (~100T raw tokens). The primary technical challenge is not gathering data, but extracting high-quality text signals from an ocean of web noise. FineWeb (Penedo et al., 2024) demonstrated that aggressive filtering of Common Crawl yields a 15T-token dataset that drastically outperforms larger, noisier corpora.
:::

## 2. Filtering & cleaning pipeline

A production data pipeline processes raw web extracts through 6 sequential filtering stages:

```text
Raw Web Pages (HTML)
       │
       ▼
 1. URL Blocklisting (Spam, Adult, Low-Quality Domains)
       │
       ▼
 2. Language Identification (fastText Classifier > 0.65 threshold)
       │
       ▼
 3. Text & Boilerplate Extraction (Trafilatura / Resiliparse)
       │
       ▼
 4. Heuristic Quality Filtering (Symbol Ratio, Word Count, Repetition)
       │
       ▼
 5. Perplexity Filtering (KenLM trained on Wikipedia / High-Quality Ref)
       │
       ▼
 6. Toxicity & PII Redaction (Email, Phone, Credit Card, SSN Removal)
```

### Key Heuristic Filters
- **Length**: Discard documents with `< 200` characters or `< 50` words.
- **Symbol-to-Word Ratio**: Discard documents where `#`, `{`, `}`, `|` exceed 10% of total tokens.
- **Alphabetic Ratio**: Require at least 70% of characters to be standard alphabetic text.
- **Repetition Checks**: Remove documents with line repetition `> 30%` or duplicate n-grams `> 20%`.
- **Perplexity Filtering**: Score text using a fast 5-gram language model (KenLM). Discard tail documents with abnormally high perplexity (unnatural text) or abnormally low perplexity (repetitive SEO boilerplate).

:::tip
Do not over-filter for toxicity during pretraining. Aggressive pretraining toxicity filters often inadvertently purge content related to marginalized groups, harming model fairness and degrading the model's ability to recognize harmful language during alignment.
:::

## 3. Deduplication strategies

Duplicate and near-duplicate documents waste compute, cause memorization, and degrade generalization.

```text
DOCUMENT-LEVEL DEDUPLICATION          SUBSTRING-LEVEL DEDUPLICATION
┌───────────────┐ ┌───────────────┐   ┌───────────────────────────────┐
│ Page A (Dup)  │ │ Page B (Dup)  │   │ Boilerplate Copyright Footer  │
└───────────────┘ └───────────────┘   └───────────────────────────────┘
  SHA-256 / MinHash + LSH               Suffix Arrays / Burrows-Wheeler
```

### Exact Deduplication
Hashes normalized text (SHA-256 after lowercasing and whitespace stripping). Fast, but misses near-duplicates and mirrored pages.

### Fuzzy Deduplication (MinHash + LSH)
Finds near-duplicate documents with high Jaccard similarity:
1. **Shingling**: Convert document into set of character $n$-grams (e.g. 5-grams).
2. **MinHash**: Compute 128 min-hash signatures per document.
3. **LSH (Locality-Sensitive Hashing)**: Divide signatures into $b$ bands of $r$ rows (e.g., 8 bands of 16 rows). Band collisions indicate candidate duplicate pairs ($Jaccard \ge 0.8$).

### Substring-Level Deduplication
Uses **Suffix Arrays** (Lee et al., 2022) to remove repeated passages, boilerplate navigation bars, cookie notices, and copyright footers across otherwise unique documents.

:::tip
Document-level dedup is essential, but substring-level dedup prevents models from memorizing verbatim web boilerplates. Pythia experiments proved that deduplication directly reduces memorization and improves downstream benchmark accuracy.
:::

## 4. Data mixing & curriculum learning

Once sources are cleaned, determining the **mixing ratio** is critical:

| Category | Target Ratio (LLaMA / Dolma) | Target Ratio (Code LLM) |
|---|---|---|
| Web Crawl | 60% – 70% | 15% – 20% |
| Source Code | 10% – 15% | 75% – 80% |
| Books & Literature | 5% – 10% | 2% – 5% |
| Academic Papers | 5% | 2% |
| Wikipedia | 3% – 5% | 1% |

### Curriculum Learning
Adjusting data mixtures over time. Increasing the ratio of high-quality data (code, math, academic papers) in the final 10–20% of training steps (decay phase) yields disproportionate gains on benchmark benchmarks.

## Practice

1. Write a Python script to compute MinHash signatures for two short strings and measure their Jaccard similarity.
2. Compare exact hashing vs MinHash on two web pages that differ only by a copyright year in the footer.

[Open the data curation slide deck](../../slides/llm-pretraining/01-data-curation/)
