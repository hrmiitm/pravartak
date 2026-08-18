# Module 06 — Conditional Routing in LangGraph

---

# Learning Objectives

By the end of this module, you will be able to:

- Understand what conditional routing is.
- Learn why routing is important in AI agents.
- Build routing logic using LangGraph.
- Use deterministic routing instead of an LLM router.
- Understand how our AI Assistant routes user requests.

---

# Prerequisites

Before starting this module, you should understand:

- Python functions
- LangGraph Nodes and Edges
- State Management

---

# Why Conditional Routing?

Real AI assistants do much more than simply answer questions.

Different user requests require different actions.

For example:

- Remember a user's name
- Solve a mathematical expression
- Check the weather
- Search Wikipedia
- Generate a normal conversational response

Instead of sending every request directly to the LLM, we first determine the user's intent and then decide where the request should go.

This decision-making process is called **Conditional Routing**.

---

# What is Conditional Routing?

Conditional Routing means selecting the next node in the graph based on the current state.

Instead of:

```
START

↓

Assistant

↓

END
```

we can build:

```
START

↓

Supervisor

↓

Memory

or

Assistant
```

The graph chooses the next node dynamically.

---

# Why Use a Supervisor?

The Supervisor acts as the traffic controller of the graph.

Its responsibilities include:

- Reading the latest user message
- Detecting the user's intent
- Choosing the next node
- Returning the routing decision

The Supervisor **does not answer the user's question**.

It only decides where execution should continue.

---

# Deterministic Routing

A common approach is to use an LLM as a router.

Example:

```
User

↓

LLM

↓

Memory?

↓

Tool?

↓

Assistant?
```

Although flexible, this introduces unnecessary latency.

For many applications, simple rule-based routing is faster and more reliable.

Our project uses deterministic routing.

Instead of asking another LLM, we classify the request using pattern matching.

This significantly reduces execution time.

---

# Intent Detection

Our router classifies requests into the following intents:

| Intent | Example |
|---------|---------|
| memory | "My name is Shambhavi" |
| calculator | "125 × 125" |
| weather | "Weather in Tokyo" |
| wikipedia | "Who is Alan Turing?" |
| assistant | General conversation |

---

# Router Architecture

The routing process is:

```
User

↓

Supervisor

↓

Intent Detection

↓

Route Selection

↓

Memory

or

Assistant
```

---

# Example 1 — Memory Request

User:

```
My name is Alice
```

Execution:

```
START

↓

Supervisor

↓

Intent = memory

↓

Memory Node

↓

END
```

---

# Example 2 — Weather Request

User:

```
What is the weather in Tokyo?
```

Execution:

```
START

↓

Supervisor

↓

Intent = weather

↓

Assistant

↓

Weather Tool

↓

Assistant

↓

END
```

Notice that the Supervisor routes the request to the Assistant, and the Assistant decides to call the Weather Tool.

---

# Conditional Edges in LangGraph

LangGraph provides conditional edges that allow execution to branch dynamically.

Example:

```python
builder.add_conditional_edges(
    "supervisor",
    supervisor_router,
)
```

The routing function decides which edge to follow.

---

# Router Function

A routing function returns the name of the next node.

Example:

```python
def supervisor_router(state):

    if state["route"] == "memory":
        return "memory"

    return "assistant"
```

LangGraph automatically follows the corresponding edge.

---

# Advantages of Deterministic Routing

Compared with an LLM router:

- Faster execution
- Lower cost
- Predictable behavior
- Easier debugging
- Better reproducibility

For workshop projects and production systems with well-defined intents, deterministic routing is often the preferred solution.

---

# Common Mistakes

❌ Sending every request through an LLM router.

❌ Mixing routing logic with business logic.

❌ Returning invalid node names.

❌ Forgetting to add conditional edges.

---

# Best Practices

- Keep routing logic lightweight.
- Separate intent detection from execution.
- Route only when necessary.
- Let specialized nodes perform the actual work.

---

# Key Takeaways

- Conditional routing allows LangGraph to choose different execution paths.
- A Supervisor decides where requests should go.
- Deterministic routing is often faster than LLM-based routing.
- Conditional edges connect routing decisions with graph execution.

---

# Exercises

### Exercise 1

Modify the router so that weather requests are detected.

---

### Exercise 2

Add a new intent called **Wikipedia** and route factual questions to the Assistant.

---

### Exercise 3

Print the detected intent in Learn Mode before routing.

---

# Summary

Conditional Routing enables LangGraph applications to make intelligent execution decisions.

By separating routing from execution, we create workflows that are modular, efficient, and easier to maintain.

Our AI Assistant uses deterministic routing to quickly classify user requests and direct them to the appropriate node before execution continues.