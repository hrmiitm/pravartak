---
title: Ollama basics
description: Run, manage, and build with large language models on your own machine.
sidebar:
  order: 2
---

# Ollama basics

**Ollama** is a tool for running open-weight large language models locally, on your own hardware. It packages a model's weights together with everything needed to run them — a runtime, a default configuration, and a simple interface — so you can go from "I want to try this model" to a running chat session in one command, without setting up Python environments, CUDA drivers, or inference frameworks by hand.

## 1. What is Ollama?

Think of Ollama as a way to get a model running locally with the same one-line simplicity you'd expect from installing an app. Under the hood it wraps `llama.cpp` (and similar inference engines) and handles the parts people usually get stuck on:

- Downloading and quantizing model weights so they fit on consumer hardware
- Picking sensible defaults (context length, chat template, stop tokens) for each model
- Serving the model over a local API so any application — not just the terminal — can talk to it
- Loading and unloading models from memory automatically as they're needed

You pull a model, you run it, and everything else — GPU offloading, memory management, prompt formatting — is handled for you.

## 2. Why is it useful?

The appeal of Ollama comes down to a handful of practical advantages over calling a hosted API:

- **Privacy** — prompts and responses never leave your machine, which matters for sensitive code, documents, or data.
- **Cost** — once a model is downloaded, running it is free. No per-token billing, no rate limits.
- **Offline availability** — no internet connection required once a model is pulled.
- **Fast iteration** — swapping between models, testing prompt changes, or benchmarking behavior has no API latency or cost attached.
- **Control** — you choose exactly which model version you're running, and it doesn't change under you when a provider updates their hosted model.

The trade-off is capability: a model small enough to run on a laptop is generally less capable than a frontier hosted model. Ollama is best understood as a complement to hosted APIs, not a full replacement — the right tool for local dev, offline work, privacy-sensitive tasks, and experimentation.

## 3. Basic commands

| Command | What it does |
| --- | --- |
| `ollama pull <model>` | Download a model to your machine |
| `ollama run <model>` | Start an interactive chat session with a model (pulls it first if missing) |
| `ollama list` | List models downloaded locally |
| `ollama ps` | List models currently loaded in memory |
| `ollama show <model>` | Show a model's details — parameters, template, system prompt |
| `ollama stop <model>` | Unload a model from memory immediately |
| `ollama rm <model>` | Delete a downloaded model from disk |
| `ollama cp <model> <new-name>` | Copy a model under a new name (useful before customizing it) |

Example — pull and chat with a small model:

```bash
ollama pull llama3.2
ollama run llama3.2
```

`ollama run` drops you into an interactive prompt. Type `/bye` to exit.

:::note
`ollama run` and `ollama pull` do the same download under the hood — `run` just pulls automatically if the model isn't present yet, so you rarely need to call `pull` on its own except to pre-download something.
:::

## 4. The server aspect, explained

Every Ollama command is actually a client talking to a local server — this is the part people miss when they think of Ollama as "just a CLI."

```text
ollama run llama3.2
        ↓
  Is the server running?
        ↓
   No → start it automatically
        ↓
  Client sends request to
  http://localhost:11434
        ↓
  Server loads the model into
  memory (if not already loaded)
        ↓
  Server streams the response back
```

Running `ollama serve` starts that server explicitly in the foreground; on most installs it's also registered as a background service, which is why `ollama run` appears to "just work" without you ever starting anything yourself.

A few consequences follow from this client-server design:

- **Every command goes through the API.** `ollama run` isn't special — it's a thin CLI client for the same `/api/generate` and `/api/chat` endpoints any other application can call. Anything the CLI can do, your own code can do too.
- **Models are loaded on demand and unloaded after inactivity.** The server keeps a model in memory only while it's being used (by default, a few minutes after the last request), which is why the first request after idling feels slower — it's reloading the model.
- **The server listens on localhost by default.** It's bound to `127.0.0.1:11434`, so nothing outside your machine can reach it unless you deliberately change the `OLLAMA_HOST` environment variable to bind to a network interface.
- **One server, many clients.** Because the server owns the model in memory, several applications on the same machine can send it requests concurrently instead of each spinning up its own copy of the model.

:::caution
Binding `OLLAMA_HOST` to `0.0.0.0` exposes the API to your network with no authentication by default. Fine on a trusted local network for testing; don't do it on a machine reachable from the internet without putting a proxy or auth layer in front of it.
:::

## 5. API calls

Because everything goes through the local server, any language that can make an HTTP request can drive Ollama. The two core endpoints are `/api/generate` and `/api/chat`; the rest of the API covers model and server management.

| Endpoint | Purpose |
| --- | --- |
| `POST /api/generate` | Single-turn text completion from a raw prompt |
| `POST /api/chat` | Multi-turn conversation, using a list of role-tagged messages |
| `POST /api/embeddings` | Generate embedding vectors for a piece of text |
| `GET /api/tags` | List locally available models (same data as `ollama list`) |
| `POST /api/show` | Return a model's Modelfile, parameters, and template |
| `POST /api/pull` | Download a model (streams progress) |
| `POST /api/push` | Upload a model to a registry |
| `POST /api/copy` | Duplicate a model under a new name |
| `DELETE /api/delete` | Remove a model |
| `GET /api/ps` | List models currently loaded in memory |

Example — `/api/generate`:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

Example — `/api/chat`, which keeps role-tagged turns instead of a single prompt string:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    { "role": "user", "content": "Why is the sky blue?" }
  ],
  "stream": false
}'
```

By default, responses are streamed back as a sequence of JSON objects, one per token/chunk; setting `"stream": false` waits and returns the complete response as a single JSON object instead.

:::note
Ollama also exposes an OpenAI-compatible surface at `/v1/chat/completions` and, more recently, an Anthropic-compatible surface at `/v1/messages` — both translate to the same underlying model calls. This is what makes tools built against those APIs (including Claude Code — see section 7) able to point at Ollama with little to no code changes.
:::

## 6. The Modelfile, parameter by parameter

A **Modelfile** is Ollama's equivalent of a Dockerfile: a text file describing how to build a custom model — either from a base model with different settings, or from your own weights.

```dockerfile
FROM llama3.2

PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER stop "<|end|>"

SYSTEM """
You are a terse, technical assistant. Prefer code over prose.
"""

TEMPLATE """{{ if .System }}{{ .System }}{{ end }}
User: {{ .Prompt }}
Assistant:"""
```

| Instruction | Purpose |
| --- | --- |
| `FROM` | The base model or weights file to build from (a model name, or a path to GGUF weights) |
| `PARAMETER` | Sets a runtime inference setting — see table below. Can be repeated for each parameter |
| `TEMPLATE` | The prompt template used to format conversation turns before they reach the model |
| `SYSTEM` | The default system prompt baked into the model |
| `ADAPTER` | Applies a LoRA adapter on top of the base model, for lightweight fine-tuning |
| `LICENSE` | Attaches license text to the model, for models you plan to share |
| `MESSAGE` | Seeds example conversation turns, useful for few-shot behavior baked into the model itself |

Common `PARAMETER` settings:

| Parameter | Controls |
| --- | --- |
| `temperature` | Randomness of output. Lower = more deterministic, higher = more varied |
| `num_ctx` | Context window size, in tokens |
| `top_k` | Limits sampling to the k most likely next tokens |
| `top_p` | Nucleus sampling threshold — considers the smallest set of tokens whose probability adds up to p |
| `repeat_penalty` | Penalizes repeated tokens, to discourage looping output |
| `stop` | A sequence that, when generated, ends the response |
| `num_predict` | Maximum number of tokens to generate |

Build and run a custom model from a Modelfile:

```bash
ollama create my-assistant -f ./Modelfile
ollama run my-assistant
```

:::note
`ollama show <model> --modelfile` prints the effective Modelfile for any model already on your machine, including ones you didn't write yourself — a fast way to see exactly what defaults (template, system prompt, parameters) a model ships with.
:::

## 7. Claude Code integration with Ollama

Claude Code — Anthropic's terminal-based coding agent — normally talks to Anthropic's hosted API. Ollama can stand in for that backend, which lets you run Claude Code entirely against a local model.

This works because Ollama exposes an Anthropic Messages API-compatible endpoint, so Claude Code's requests can be pointed at your local server instead of `api.anthropic.com` by setting a few environment variables:

```bash
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_AUTH_TOKEN=ollama
export ANTHROPIC_API_KEY=""

claude --model qwen3-coder
```

A few things worth knowing before you try it in the workshop:

- **Model choice matters a lot for this use case.** Claude Code isn't a chat prompt — it sends a large system prompt plus tool definitions (for file edits, bash, search, etc.) with every request, and it relies on the model reliably emitting correctly-formatted tool calls. Models specifically tuned for tool use — `qwen3-coder` and `gpt-oss` are common picks — behave far more predictably here than general-purpose chat models.
- **Context window is a real constraint.** Because of that system-prompt-plus-tools overhead, a local model needs a reasonably large context window to hold a working session — small context windows get overwhelmed quickly and sessions degrade after a few turns. Set `num_ctx` accordingly in the Modelfile.
- **This is a genuinely local setup** — no data leaves the machine, and there's no per-token cost — but expect a noticeable capability gap against Claude's hosted models on complex, multi-step tasks. It's best suited to routine edits, boilerplate, and offline work, with the hosted models still the better choice for harder problems.
- **You can switch back at any time** by simply unsetting `ANTHROPIC_BASE_URL`, since it's Claude Code's only signal to route away from Anthropic's API.

## Practice

Pull a small model and chat with it from the terminal. Then call `/api/generate` directly with `curl` and compare the raw JSON response to what the CLI showed you. Finally, write a short Modelfile that sets a custom `SYSTEM` prompt and a lower `temperature`, build it with `ollama create`, and run it.

[Read the Ollama documentation](https://docs.ollama.com/)

[Read about the Anthropic API compatibility](https://ollama.com/blog/claude)
