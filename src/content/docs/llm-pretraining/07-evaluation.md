---
title: Evaluation & benchmarks
description: Perplexity, MFU, zero-shot/few-shot downstream benchmarks (MMLU, GSM8K, HumanEval), and contamination mitigation.
sidebar:
  order: 8
---

# Evaluation & benchmarks

**Evaluation** measures model capability throughout and after pretraining. Monitoring the right metrics prevents training blind spots and catches benchmark contamination.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>Perplexity · Benchmarks · Contamination · Frameworks · PDF</small></p>
  <a href="../../slides/llm-pretraining/07-evaluation/">Open slide deck →</a>
</div>

## 1. Perplexity & intrinsic metrics

**Perplexity (PPL)** is the exponentiated negative log-likelihood per token:

$$\text{PPL} = \exp \left( -\frac{1}{T} \sum_{t=1}^{T} \log P(x_t \mid x_{<t}) \right)$$

- Lower PPL indicates better predictive capability over the text distribution.
- **Validation Split Tracking**: Measure PPL on both an *in-domain* validation set and an *out-of-domain* validation set (e.g., ArXiv, code, non-English) to track generalizability.

### Operational Hardware Metrics
- **Model FLOPs Utilization (MFU)**: $\frac{\text{Actual FLOP/s}}{\text{Theoretical Peak FLOP/s}}$. Healthy MFU is **40%–60%**.
- **Token Throughput**: Tokens processed per second per GPU.

## 2. Standard downstream benchmarks

Models are evaluated across standardized zero-shot ($0$-shot) and few-shot ($5$-shot) benchmark suites:

| Benchmark | Knowledge Axis | Task Description | Metric |
|---|---|---|---|
| **MMLU** | Academic Knowledge | 57 subjects (Elementary Math to Professional Law) | 5-shot Multiple Choice Accuracy |
| **HellaSwag** | Commonsense Reasoning | Predict plausible sentence continuations | 10-shot Accuracy |
| **GSM8K** | Math Reasoning | Grade-school math word problems | 5-shot Exact Match |
| **HumanEval** | Code Generation | Functional Python code completion | pass@1 (0-shot) |
| **ARC-Challenge** | Science Reasoning | Grade 3–8 science questions | 25-shot Accuracy |
| **IFEval** | Instruction Following | Verifiable constraints (e.g. "write 3 paragraphs, no letter 'e'") | Strict Accuracy |

:::caution
Single benchmark scores can be deceptive. A model can achieve high MMLU scores via data contamination or prompt optimization while remaining unusable for code generation or instruction following. Always evaluate holistically across knowledge, math, code, and safety axes.
:::

## 3. Evaluation frameworks

- **lm-evaluation-harness** (EleutherAI): De facto open-source standard with 200+ benchmarks. Powering the HuggingFace Open LLM Leaderboard.
- **HELM** (Stanford): Holistic evaluation across 42 scenarios and 7 metric dimensions.
- **lighteval** (HuggingFace): Fast evaluation runner integrated into HuggingFace datasets and pipelines.

```bash
# Running benchmark evaluation via lm-evaluation-harness
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-3-8B \
  --tasks mmlu,hellaswag,gsm8k,humaneval \
  --batch_size 16
```

## 4. Benchmark contamination & decontamination

**Benchmark contamination** occurs when evaluation benchmark questions leak into web crawl pretraining data.

### Detection & Decontamination Techniques
1. **$N$-gram Overlap Filtering**: Remove pretraining documents that share 13-gram or 8-gram matches with evaluation questions.
2. **Canary Strings**: Embed unique GUID canary strings inside benchmark datasets to detect if web scrapers indexed test splits.
3. **Perturbation Analysis**: Swap names, numbers, or phrasing in benchmark questions. A drastic drop in score indicates verbatim memorization rather than reasoning capability.

## Practice

1. Run `lm-evaluation-harness` on a small model (e.g., `gpt2` or `Qwen/Qwen2.5-0.5B`) for `hellaswag` and `arc_easy`.
2. Inspect prompt templates used for 5-shot evaluation.

[Open the evaluation slide deck](../../slides/llm-pretraining/07-evaluation/)
