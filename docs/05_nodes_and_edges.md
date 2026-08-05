# Module 05 — Nodes and Edges in LangGraph

---

# Learning Objectives

By the end of this module, you will be able to:

- Understand what a node is.
- Understand what an edge is.
- Build simple execution pipelines.
- Understand how LangGraph moves between nodes.
- Visualize graph execution.

---

# Prerequisites

Before starting this module, you should understand:

- Python functions
- LangChain basics
- State Management (Module 04)

---

# Why Nodes and Edges?

Traditional LLM applications usually follow a simple flow:

```

User
↓

LLM
↓

Response

```

However, modern AI applications require multiple steps.

For example:

- Retrieve information
- Call tools
- Store memory
- Make routing decisions
- Ask humans for approval

Instead of writing deeply nested if-else statements, LangGraph models the application as a graph.

---

# What is a Node?

A **Node** is a unit of execution.

Think of it as one task in your workflow.

Examples:

- Generate an answer
- Search the web
- Store memory
- Call a calculator
- Execute a tool

A node receives the current **State**.

It performs some work.

Then it returns an updated State.

---

Example:

```python
def assistant(state):

    response = llm.invoke(state["messages"])

    return {
        "messages": [response]
    }