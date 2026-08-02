---
marp: true
title: Data Collection & Curation
description: Data sources, quality filtering pipelines, deduplication algorithms, and mixing strategies.
theme: default
size: 16:9
paginate: true
---

# Data Collection & Curation

### Quality Beats Quantity at Scale

- Sources of pretraining data
- 6-stage web text cleaning pipeline
- Deduplication: Exact, MinHash LSH, and Substring
- Data mixing ratios & curriculum learning

---

## Sources of Pretraining Data

| Source | Volume | Quality Profile | Cost |
|---|---|---|---|
| **Web Crawl** | Trillions of tokens | Low/Variable (Requires aggressive filtering) | Low |
| **Books & Lit** | ~30B tokens | High (Long context cohesion) | Legal risk |
| **Academic Papers** | ~50B tokens | High (Technical reasoning) | Low |
| **Source Code** | ~500B tokens | High (Logical structure & syntax) | Low |
| **Wikipedia** | ~4B tokens | Very High (Factual signal) | Free |

- **FineWeb**: 15T-token clean web dataset outperforming larger raw crawls.

---

## 6-Stage Web Cleaning Pipeline

```text
Raw Web HTML
  │  ► 1. URL Domain Blocklisting
  │  ► 2. Language ID (fastText > 0.65)
  │  ► 3. Trafilatura Text Extraction
  │  ► 4. Heuristic Quality Filters (Symbol/word ratio, length)
  │  ► 5. Perplexity Filtering (KenLM 5-gram)
  ▼  ► 6. Toxicity & PII Redaction
Clean Pretraining Corpus
```

---

## Deduplication Strategies

- **Exact Deduplication**: SHA-256 hash matching on normalized text
- **Fuzzy Deduplication (MinHash + LSH)**:
  - Shingle text into $N$-grams
  - Compute 128 MinHash signatures per document
  - Group into $b$ bands of $r$ rows to find candidate duplicate pairs ($Jaccard \ge 0.8$)
- **Substring Deduplication (Suffix Arrays)**:
  - Removes repeated boilerplate passages across otherwise unique pages

---

## Data Mixing Ratios & Curriculum

### General-Purpose Mix (LLaMA / Dolma)
- **Web Crawl**: 60% – 70%
- **Source Code**: 10% – 15%
- **Books & Academic**: 10% – 15%
- **Wikipedia / Ref**: 3% – 5%

### Curriculum Learning
- Increase high-quality data (math, code, academic papers) in final **10%–20%** of training. Boosts benchmark performance significantly.
