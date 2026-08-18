# Module 08 — Tool Calling in LangGraph

---

# Learning Objectives

By the end of this module, you will be able to:

- Understand what tools are in LangGraph.
- Learn why LLMs need external tools.
- Register tools using LangChain.
- Integrate tools into a LangGraph workflow.
- Build AI assistants that interact with external systems.

---

# Prerequisites

Before starting this module, you should understand:

- LangGraph Nodes
- State Management
- Conditional Routing
- Memory

---

# Why Do We Need Tools?

Large Language Models are excellent at generating text, but they cannot reliably perform every task.

For example:

- Perform accurate mathematical calculations
- Access live weather information
- Retrieve current facts from external APIs
- Read databases
- Search documents

To solve these problems, LangGraph allows an LLM to call external **Tools**.

---

# What is a Tool?

A Tool is simply a Python function that the LLM is allowed to call.

Instead of answering everything itself, the LLM can decide:

```
Should I answer?

OR

Should I use a tool?
```

---

# Tool Calling Workflow

```
User

↓

Assistant

↓

LLM

↓

Tool Decision

↓

Calculator
Weather
Wikipedia

↓

Tool Output

↓

LLM

↓

Final Response
```

The LLM remains responsible for deciding **when** a tool is needed.

---

# Registering a Tool

LangChain provides the `@tool` decorator.

Example:

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    return "42"
```

After registration, the assistant can call this tool automatically.

---

# Binding Tools

Tools are attached to the language model before execution.

Example:

```python
assistant_llm = llm.bind_tools(TOOLS)
```

Now the model understands which external capabilities are available.

---

# ToolNode

LangGraph executes tools using a `ToolNode`.

```
Assistant

↓

ToolNode

↓

Calculator

↓

Assistant
```

The ToolNode receives the tool request, executes the function, and returns the result.

---

# Tools Used in Our AI Assistant

Our assistant currently supports the following tools.

| Tool | Purpose |
|------|---------|
| Calculator | Evaluate mathematical expressions |
| Weather | Retrieve live weather information |
| Wikipedia | Retrieve factual information |

Each tool is implemented as an independent Python function.

---

# Example 1 — Calculator

User:

```
What is 125 × 125?
```

Execution:

```
User

↓

Assistant

↓

Calculator Tool

↓

15625

↓

Assistant

↓

Response
```

The calculation is performed by the tool rather than by the language model.

---

# Example 2 — Weather

User:

```
What is the weather in Tokyo?
```

Execution:

```
Assistant

↓

Weather Tool

↓

OpenStreetMap

↓

Open-Meteo API

↓

Assistant
```

The assistant retrieves live weather data from external APIs.

---

# Example 3 — Wikipedia

User:

```
Who is Alan Turing?
```

Execution:

```
Assistant

↓

Wikipedia Tool

↓

Wikipedia

↓

Summary

↓

Assistant
```

The assistant augments its knowledge using external information.

---

# Why Use Tools?

Without tools:

- Static knowledge
- Hallucinated calculations
- No real-time information

With tools:

- Accurate calculations
- Live data
- Reliable external information
- Extensible architecture

---

# Best Practices

- One responsibility per tool.
- Keep API logic separate from tool definitions.
- Validate tool inputs.
- Handle exceptions gracefully.
- Return concise outputs.

---

# Common Mistakes

❌ Performing calculations with the LLM.

❌ Mixing API calls directly into assistant logic.

❌ Creating very large tools that perform multiple unrelated tasks.

❌ Forgetting to register tools.

---

# Key Takeaways

- Tools extend the capabilities of an LLM.
- ToolNode executes external functions.
- The LLM decides when tools are required.
- External APIs make assistants more powerful and reliable.

---

# Exercises

### Exercise 1

Create a tool that returns the current date.

---

### Exercise 2

Create a tool that converts text to uppercase.

---

### Exercise 3

Integrate a new external API as a LangGraph tool.

---

# Summary

Tool Calling is one of the most powerful features of LangGraph.

Instead of relying solely on language generation, the assistant can perform calculations, access live APIs, and interact with external systems, resulting in more accurate and capable AI applications.