---
marp: true
theme: default
paginate: true
size: 16:9
---

# Fine-Tuning Large Language Models
### From Foundations to Practice

---

# What is a Pretrained LLM?

Imagine someone who has read a huge chunk of the internet.

They know grammar, facts, code, reasoning patterns, countless writing styles.

But they don't know:

* Your company's product
* Your specific task's format
* The tone you want

This is a **pretrained model**: broad knowledge, no specialization.

---

# What is Fine-Tuning?

Fine-tuning is additional training on top of a pretrained model.

```text
Pretrained Model
   (general knowledge)
        ↓
  Fine-Tuning
   (specific data)
        ↓
Specialized Model
```

Same underlying model. Narrower, more reliable behavior.

---

# An Analogy

Hiring a brilliant generalist employee.

They know a lot, but not your company.

You could:

* Give them a manual to read every time (**prompting**)
* Let them look things up as needed (**RAG**)
* Train them properly, once, so it becomes second nature (**fine-tuning**)

---

# Why Fine-Tune?

Pretrained models are general-purpose by design.

Fine-tuning adapts a model to:

* A **domain** (legal, medical, code)
* A **task** (classification, summarization, following instructions)
* A **style or persona**

---

# Do You Even Need Fine-Tuning?

Alternatives exist:

* **Prompting** — just ask well, with instructions in the prompt
* **In-context learning** — show a few examples in the prompt
* **RAG** — fetch relevant documents at request time

These are often cheaper and faster to set up.

---

# When Fine-Tuning Wins

Fine-tuning is worth it when you need:

* Consistent behavior, every time
* Lower cost per request (no giant prompt needed)
* Capabilities that prompting alone can't reach

Otherwise, try prompting first.

---

# Not All Fine-Tuning is Equal

There's a whole spectrum of approaches.

They differ in:

* How many of the model's parameters actually change
* How much data you need
* How much compute it costs

More on the exact trade-offs in the docs.

---

# The Spectrum, Roughly

```text
Prompting            →  0% of the model changes

Prompt/Prefix Tuning →  a tiny learned addition

PEFT (e.g. LoRA)     →  a small fraction of parameters

Full Fine-Tuning     →  the entire model
```

More parameters changed = more powerful, but also more data and compute.

---

# Full Fine-Tuning

Update **every single weight** in the model.

```text
Pretrained Weights
        ↓
   Full Backprop
        ↓
All Weights Updated
```

Maximum flexibility. Also the most expensive option, by far.

---

# The Cost of Full Fine-Tuning

* Needs a lot of GPU memory — not just for the model, but for the optimizer too
* Requires a large, high-quality dataset
* Produces one full model copy per task

Risk: the model can **forget** general skills it used to have.

---

# Parameter-Efficient Fine-Tuning (PEFT)

Idea: freeze almost the whole model.

Train only a small add-on.

```text
Pretrained Model (frozen)
          +
  Small Trainable Piece
          =
  Adapted Behavior
```

Like sticky notes on a textbook, instead of rewriting the textbook.

---

# Why PEFT is Popular

* Much less GPU memory needed
* Much less data needed
* The tiny trained piece (an "adapter") is small — megabytes, not gigabytes
* One shared base model can serve many different tasks

---

# LoRA: The Idea

LoRA is the most common PEFT method.

Instead of updating a big weight matrix directly...

...it learns a small "correction" to it, built from two much smaller matrices.

```text
Original Weights (frozen)  +  Small Learned Correction
          =
  Adapted Weights
```

Refer to docs for more details.

---

# QLoRA: LoRA on a Diet

Same LoRA idea, but the frozen base model is compressed first.

```text
Full-Precision Model
        ↓
   Compress (quantize)
        ↓
Small Frozen Base + LoRA on top
```

Lets you fine-tune much larger models on much smaller hardware.

---

# Instruction Tuning

A base model just predicts the next word — it doesn't know it's supposed to "help."

Instruction tuning teaches it to actually follow requests.

```text
"Summarize this."
        ↓
Instruction-Tuned Model
        ↓
An actual summary, not just more text
```

Trained on pairs of (instruction, good response).

---

# Aligning with Human Preferences

After a model follows instructions, we also want it to follow them *well* — helpfully, safely, in a preferred style.

Two common approaches:

* **RLHF** — train a separate model to score outputs, then optimize against it
* **DPO** — skip that separate model, learn directly from "this response is better than that one" pairs

---

# Why This Matters

Instruction tuning teaches a model *what* to do.

Preference alignment teaches it *how* to do it well.

```text
Pretraining → Instruction Tuning → Preference Alignment
   (knows          (follows           (does it
    language)       requests)          helpfully)
```

---

# Good Data Matters More Than Fancy Methods

* A small, clean dataset usually beats a huge, messy one
* The data should look like what the model will actually see in production
* Formatting consistency matters — same structure every time

Full checklist in the docs.

---

# Common Pitfalls

* **Catastrophic forgetting** — model gets good at the new task, worse at everything else
* **Overfitting** — memorizes the small dataset instead of learning to generalize
* **Mismatched data** — training data doesn't resemble real usage

Watching validation performance, not just training performance, catches most of these early.

---

# Choosing an Approach

```text
Just need better outputs right now?      → Try prompting first
Small dataset, limited GPU?              → LoRA / QLoRA
Need absolute best performance,
large dataset, big budget?               → Full fine-tuning
Need the model to follow instructions?   → Instruction tuning first
Need it to match human preferences?      → Follow up with DPO/RLHF
```

---

# Summary

* Fine-tuning adapts a general pretrained model into a specialized one
* PEFT methods like LoRA/QLoRA are the practical default today
* Typical pipeline: **pretrain → instruction tune → preference align**
* Good data and careful evaluation matter more than exotic techniques
* Always compare against a strong prompting baseline first

---

# Time to see some examples in Colab!
