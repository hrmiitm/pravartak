---
title: Tool-Calling LLM
description: Build a tool-calling workflow with LangChain and Ollama, defining custom tools, binding them to an LLM, executing tool calls, and feeding results back for a final answer.
sidebar:
  order: 1
---

By the end of this lesson, you will be able to define custom tools with LangChain, bind them to a local LLM, invoke the model so it can call tools, execute the returned tool calls, send the results back to the model, and receive a final grounded response.

:::caution[Local services required]
This lesson runs entirely on your machine through [Ollama](https://ollama.com). Start Ollama and pull the model used below before running any code:

```bash
ollama pull gemma4:e4b
```
:::

## Setup

The project uses LangChain for tool definition and orchestration, and Ollama for generation. Dependencies are defined in `pyproject.toml`:

```toml
dependencies = [
    "langchain-core>=0.3.0",
    "langchain-ollama>=0.3.0",
]
```

Install them with:

```bash
uv sync
```

The example works with two simple math tools and a single query:

```python
query = "What is (25 + 17) * 3? Use tools."
```

## What are tools?

A language model alone can only reason and generate text. **Tool calling** lets the model decide when to invoke external functions — tools — to get information or perform computation it cannot do on its own.

Every tool-calling workflow has three stages:

```text
               ┌── CALL TOOLS ──┐   ┌── EXECUTE ──┐   ┌── FINAL ANSWER ──┐
query ───────▶  LLM decides     ─▶  run the tool  ─▶  LLM uses results ─▶ answer
               which tools       and returns       and synthesizes
               to call           output              a response
```

1. **Call tools** — the LLM decides which tools to invoke and with what arguments.
2. **Execute** — the actual tool function runs and returns a result.
3. **Final answer** — the LLM receives the tool results and produces a grounded response.

## Defining tools with `@tool`

LangChain provides a `@tool` decorator that turns a plain Python function into a LangChain tool. The decorator automatically extracts the function's name, description, and parameter schema from the docstring and type hints:

```python
from langchain_core.tools import tool

@tool
def add(a: int, b: int) -> int:
    """
    Add two integers.
    Args:
        a: First integer
        b: Second integer
    Returns:
        The sum of a and b
    """
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """
    Multiply two integers.
    Args:
        a: First integer
        b: Second integer
    Returns:
        The product of a and b
    """
    return a * b
```

The docstring is critical — the LLM reads it to decide *when* to call the tool and *what arguments to pass*. Type hints (`int`) define the parameter schema that the model sees.

## Creating the LLM and binding tools

A chat model is created with `ChatOllama`, pointing at the local Ollama server. Tools are bound to the model with `llm.bind_tools()`, which tells the model which tools are available and injects the tool schemas into its prompt:

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma4:e4b",
    base_url="http://localhost:11434",
    temperature=0.8,
)

llm_with_tools = llm.bind_tools([add, multiply])
```

- `model` — the Ollama model to use.
- `base_url` — the Ollama server address.
- `temperature` — controls randomness; `0.8` allows some creativity while keeping reasoning coherent.

After binding, the model is aware of the tools and can choose to call them when appropriate.

## Invoking the LLM

The first invocation sends the user query to the model. The model analyzes the query, determines that it needs to use the `add` and `multiply` tools, and returns a response containing `tool_calls`:

```python
query = "What is (25 + 17) * 3? Use tools."

response = llm_with_tools.invoke(query)
print("USER QUERY:")
print(query)
print("RESPONSE FROM LLM WITH TOOLS:")
print(response)
```

The `response` object contains a `tool_calls` list — each entry has a `name` (which tool to call), `args` (the arguments), and a unique `id` (to correlate results later).

## Executing the tools

The tool calls from the LLM are not executed automatically. You must look them up in a tool registry and invoke each one manually:

```python
tools = {
    "add": add,
    "multiply": multiply,
}

tool_results = []

for tool_call in response.tool_calls:
    tool = tools[tool_call["name"]]
    result = tool.invoke(tool_call["args"])
    tool_results.append(result)
```

Each tool's `invoke()` method runs the actual Python function with the arguments the LLM provided. The results are collected in order so they can be mapped back to the original tool calls.

## Sending results back to the model

Once the tools have been executed, the results must be fed back to the model as a `ToolMessage`. This message includes the tool call ID (so the model can correlate), the result content, and the original tool call metadata:

```python
from langchain_core.messages import ToolMessage

messages = [
    response,
]

for tool_call, result in zip(response.tool_calls, tool_results):
    messages.append(
        ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"]
        )
    )
```

The `ToolMessage` acts as the bridge between the tool execution and the LLM — it tells the model exactly what each tool returned, using the same `tool_call_id` the model originally provided.

## Getting the final answer

With the tool results now in the conversation history, a second invocation to the model produces the final answer. The model sees the original query, its own tool calls, and the tool results, and synthesizes a complete response:

```python
final = llm_with_tools.invoke(messages)

print("FINAL RESPONSE FROM LLM AFTER EXECUTING THE TOOLS:")
print(final.content)
```

For the query `"What is (25 + 17) * 3? Use tools."`, the model first calls `add(25, 17)` to get `42`, then calls `multiply(42, 3)` to get `126`, and finally answers with `126`.

## Key takeaways

| Concept | What it does |
|---|---|
| `@tool` decorator | Turns a Python function into a LangChain tool with automatic schema extraction |
| `llm.bind_tools()` | Makes tools available to the model by injecting their schemas |
| `tool_calls` | The LLM's decision about which tools to call and with what arguments |
| `ToolMessage` | Delivers tool execution results back to the model in a structured format |
| Two-step invoke | First call gets tool calls; second call (with results) gets the final answer |

## Knowledge check

1. Why does the `@tool` decorator need a docstring with `Args` and `Returns` sections?
2. What happens if you call `llm_with_tools.invoke(query)` without first binding tools?
3. Why is `tool_call_id` important when constructing a `ToolMessage`?
4. What would happen if you sent the tool results back to the model without including the original `response` message?
5. Why is `temperature=0.8` a reasonable choice for tool-calling workflows?

<details>
<summary>Suggested answers</summary>

1. The docstring provides the description and parameter schema that the LLM uses to decide when and how to call the tool.
2. Without bound tools, the model cannot see or invoke any tools — it will answer using only its training knowledge.
3. The `tool_call_id` links each result back to the specific tool call it belongs to, so the model can correctly associate inputs and outputs.
4. The model would not know which tool call each result corresponds to, breaking the correlation between tool calls and their results.
5. A moderate temperature allows the model to reason flexibly about which tools to call and in what order, while still being deterministic enough for reliable tool use.

</details>

## Assignment

1. Add a `subtract` tool and update the query to `"What is (25 + 17) * 3 - 10? Use tools."` — verify the model uses all three tools.
2. Create a tool that fetches the current time using `datetime.now()` and test it with a query like `"What time is it?"`.
3. Experiment with `temperature=0.0` and `temperature=1.5` — observe how tool selection and argument accuracy change.
4. Wrap the tool-calling loop (invoke → execute → ToolMessage → final invoke) in a reusable function that accepts any list of tools and a query string.
5. Add error handling so that if a tool raises an exception, the error message is sent back to the model as a `ToolMessage` instead of crashing.