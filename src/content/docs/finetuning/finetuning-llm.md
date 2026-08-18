---
title: Fine-tuning LLMs
description: A practical reference for adapting pretrained language models.
sidebar:
  order: 1
---

# Fine-tuning LLMs

**Fine-tuning** is the process of taking a pretrained large language model and further training it on a smaller, more specific dataset so it performs better on a particular domain, task, or style. This page is a practical reference — methods, numbers, and checklists — for when you're actually setting up a fine-tuning run.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>Slides · drawing tools · PDF</small></p>
  <a href="../../slides/llm-finetuning/">Open slide deck →</a>
</div>

## 1. The fine-tuning spectrum

There isn't one way to fine-tune a model — approaches trade off how many parameters you update against how much data and compute you need:

| Approach | Params updated | Data needed | Cost |
| --- | --- | --- | --- |
| Full fine-tuning | 100% | Large (10k–1M+ examples) | Very high |
| PEFT (LoRA, etc.) | <1% | Medium (1k–100k examples) | Low–Medium |
| Prompt/Prefix tuning | Tiny (soft prompts) | Small–Medium | Low |
| In-context learning | 0% | A few examples | None (inference only) |
| RLHF / DPO | Varies | Preference pairs | High (needs a reward signal) |

## 2. Full fine-tuning

Full fine-tuning updates **every** weight in the model via standard backpropagation on task-specific data.

- Needs the full optimizer state in memory — Adam roughly doubles the memory footprint of the parameters themselves (moment estimates for every weight).
- One full model checkpoint has to be stored per task, since nothing is shared.
- Carries real risk of **catastrophic forgetting**: the model can lose general capabilities it had before fine-tuning.

:::note
Rule of thumb: fine-tuning a 7B-parameter model in full requires roughly **60–120GB of GPU memory** once you account for mixed-precision weights plus optimizer states.
:::

## 3. Parameter-efficient fine-tuning (PEFT)

PEFT methods freeze the pretrained backbone and train only a small number of extra or modified parameters on top of it. This means one shared base model can serve many tasks, each with its own small adapter (megabytes, not gigabytes).

| Method | Idea |
| --- | --- |
| **LoRA** | Low-Rank Adaptation — see below |
| **QLoRA** | LoRA applied on top of a quantized base model |
| **Adapters** | Small bottleneck layers inserted between transformer blocks |
| **Prefix/Prompt tuning** | Learnable "virtual tokens" prepended to the input |

### LoRA: the math

LoRA approximates the weight update as a low-rank decomposition:

$$W' = W + \Delta W = W + BA$$

where $W \in \mathbb{R}^{d \times k}$ is the frozen pretrained weight, $B \in \mathbb{R}^{d \times r}$ and $A \in \mathbb{R}^{r \times k}$ are the trainable matrices, and rank $r \ll \min(d,k)$.

- Only $A$ and $B$ are trained; the original $W$ never changes.
- Typical rank: $r = 4$ to $64$.
- Usually applied to the attention projection matrices ($W_q$, $W_v$).
- Trainable parameters are often **under 1%** of the full model.

### QLoRA: LoRA + quantization

- The frozen base model is loaded in **4-bit precision** (NF4 quantization).
- LoRA adapters are trained in higher precision (bf16/fp16) on top of that quantized base.
- **Double quantization** and **paged optimizers** manage the memory spikes that would otherwise occur during training.
- This combination makes it possible to fine-tune a **65B-parameter model on a single 48GB GPU**, at near-full-fine-tuning quality.

## 4. Instruction tuning

Instruction tuning teaches a base (next-token-prediction) model to actually **follow instructions**.

- Data format: (instruction, response) pairs, often wrapped with a system prompt.
- Common datasets: Alpaca, Dolly, FLAN, OpenAssistant, or a custom curated set.
- It's typically the **first** stage after pretraining, before any preference alignment.
- Loss is standard cross-entropy, but it's usually **masked** so the loss is only computed on the response tokens — not the instruction/prompt tokens.

## 5. Aligning with human preferences

After instruction tuning, models are often further aligned using human feedback:

1. **RLHF** (Reinforcement Learning from Human Feedback)
   - Train a reward model on human-ranked outputs.
   - Optimize the policy (the LLM) against that reward model using PPO.
2. **DPO** (Direct Preference Optimization)
   - Skips the separate reward model and the RL loop entirely.
   - Directly optimizes the policy on preference pairs using a closed-form loss derived from the RLHF objective.
   - Simpler and more stable to train than PPO-based RLHF, and increasingly the default choice.

## 6. Data preparation checklist

- **Quality beats quantity** — a few thousand clean examples often outperform a noisy 100k+ set.
- Deduplicate, and filter for length, language, and toxicity.
- Match the **distribution** of your actual target task/domain.
- Format consistently: chat templates, special tokens, system prompts.
- Hold out a validation set that mirrors real evaluation conditions.
- For preference data specifically: make sure rankings are consistent and rationale-driven, not arbitrary.

## 7. Training hyperparameters

| Setting | Guidance |
| --- | --- |
| Learning rate | PEFT tolerates higher LR (`1e-4`–`3e-4`) than full fine-tuning (`1e-5`–`5e-5`) |
| Batch size | Use gradient accumulation if GPU memory is limited |
| Epochs | 1–3 is typical; more risks overfitting on small datasets |
| Precision | Mixed precision (bf16/fp16) + gradient checkpointing to save memory |
| Monitoring | Track validation loss and task-specific metrics, not just training loss |
| Stopping | Use early stopping to avoid overfitting or forgetting |

## 8. Common pitfalls

- **Catastrophic forgetting** — the model loses general capabilities after narrow fine-tuning.
  - Mitigate with a lower learning rate, PEFT instead of full fine-tuning, or by mixing in general-purpose data.
- **Overfitting** on small datasets — watch for train/validation loss divergence.
- **Data leakage** between train and eval splits.
- **Reward hacking** in RLHF — the policy learns to exploit flaws in the reward model rather than genuinely improving.
- **Distribution mismatch** — fine-tuning data doesn't resemble real deployment inputs.

## 9. Evaluation

- Task-specific automatic metrics: accuracy, F1, BLEU/ROUGE, exact match.
- Held-out human evaluation for open-ended generation quality.
- Regression testing on **general capability benchmarks**, to catch forgetting.
- For alignment work: win-rate against a baseline model via pairwise preference judgments.
- Always compare against a strong baseline — zero-shot or few-shot prompting — before crediting fine-tuning with the improvement.

## 10. Choosing an approach

| If you have... | Consider... |
| --- | --- |
| Small dataset, limited compute | LoRA / QLoRA |
| Very limited GPU memory | QLoRA |
| Large curated dataset, need max performance | Full fine-tuning |
| A model that needs to follow instructions | Instruction tuning first |
| A model that needs to match human preferences/style | Follow up with DPO/RLHF |
| Multiple tasks, one base model | PEFT adapters (swap per task) |

## Practice

Pick a small open dataset (a few thousand instruction/response pairs) and sketch out a fine-tuning plan: which row of the spectrum table you'd use, what learning rate and epoch count you'd start with, and what you'd check in evaluation to confirm the model didn't forget its general capabilities.

[LoRA paper](https://arxiv.org/abs/2106.09685)

[QLoRA paper](https://arxiv.org/abs/2305.14314)

[DPO paper](https://arxiv.org/abs/2305.18290)

[Open the fine-tuning slides](../../slides/llm-finetuning/)
