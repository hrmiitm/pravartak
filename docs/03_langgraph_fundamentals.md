# Chapter 3: LangGraph Fundamentals

## Learning Objectives

By the end of this chapter, participants will be able to:

- Understand what LangGraph is.
- Explain why graphs are used instead of linear chains.
- Identify the core components of a LangGraph application.
- Understand graph execution flow.
- Build their first LangGraph workflow.

---

# Introduction

As AI applications become increasingly complex, traditional linear pipelines become difficult to maintain.

Modern AI systems require:

- branching
- looping
- memory
- tool usage
- dynamic routing
- human intervention
- multiple agents

Representing these behaviors using nested function calls or long if-else statements quickly becomes difficult.

LangGraph addresses this challenge by representing AI workflows as **graphs**.

---

# What is LangGraph?

LangGraph is an open-source framework developed within the LangChain ecosystem for building **stateful, graph-based AI applications**.

Instead of representing an application as a fixed sequence of operations, LangGraph models it as a graph consisting of interconnected nodes.

Each node performs a specific task, while edges define how execution moves from one node to another.

This graph-based architecture makes it easier to build complex workflows involving:

- conditional execution
- loops
- retries
- memory
- tool calling
- multi-agent collaboration
- human-in-the-loop interactions

LangGraph is particularly well suited for production AI systems because it provides explicit control over workflow execution.

---

# Why Graphs Instead of Chains?

Traditional LLM pipelines typically follow a linear sequence:

```
Input
  │
  ▼
Step A
  │
  ▼
Step B
  │
  ▼
Step C
  │
  ▼
Output
```

While this approach works for simple workflows, it struggles with dynamic decision-making.

Graphs allow workflows to:

- branch into multiple paths
- revisit previous steps
- execute loops
- merge results
- pause for human input
- coordinate multiple agents

This flexibility makes graphs a natural representation for modern agentic systems.

---

# Chains vs Graphs

| Chains | Graphs |
|----------|---------|
| Linear execution | Non-linear execution |
| Fixed order | Dynamic execution |
| Difficult to extend | Easy to extend |
| Limited branching | Native branching |
| Limited looping | Native loops |
| Harder to model complex workflows | Designed for complex workflows |

---

# A Simple LangGraph

```
        START
           │
           ▼
     Generate Reply
           │
           ▼
      Validate Reply
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
 Approved     Needs Fix
     │           │
     ▼           │
    END ◄────────┘
```

Even this simple workflow demonstrates something that traditional chains cannot easily express:

- conditional execution
- retry loops
- explicit state transitions

---

# Core Components of LangGraph

Every LangGraph application is built using four fundamental concepts:

1. State
2. Nodes
3. Edges
4. Graph Execution

Understanding these four concepts is essential because every workflow—whether it is a chatbot, research assistant, coding agent, or multi-agent system—is ultimately composed of these building blocks.

---

## 1. State

### What is State?

State is the shared data that flows through the graph as execution progresses.

Each node reads information from the state, performs some computation, and returns updates that become part of the new state.

Rather than passing dozens of variables between functions, LangGraph keeps all relevant information inside a single state object.

```
Input
   │
   ▼
 State
   │
   ▼
 Node A
   │
 Updated State
   │
   ▼
 Node B
```

Typical information stored in state includes:

- User messages
- LLM responses
- Retrieved documents
- Tool outputs
- Conversation history
- Intermediate reasoning
- Metadata

---

## 2. Nodes

A Node represents a unit of work.

Each node performs exactly one logical task.

Examples include:

- Calling an LLM
- Executing a tool
- Searching a database
- Summarizing text
- Classifying user intent
- Validating an answer
- Asking for human approval

```
State
   │
   ▼
+-------------+
|    Node     |
+-------------+
   │
Updated State
```

A well-designed graph consists of small, focused nodes rather than one large node that performs many unrelated operations.

---

## 3. Edges

Edges define how execution moves from one node to another.

There are two primary types of edges.

### Normal Edge

Always moves to the next node.

```
Node A
   │
   ▼
Node B
```

### Conditional Edge

Chooses the next node based on the current state.

```
          Decision
             │
     ┌───────┴────────┐
     ▼                ▼
 Success           Retry
     │                │
     ▼                ▼
 Continue       Previous Node
```

Conditional edges enable dynamic workflows where different inputs follow different execution paths.

---

## 4. Graph Execution

When a LangGraph application starts, execution begins at the **START** node.

The graph then follows its edges until it reaches **END**.

```
START
   │
   ▼
Node A
   │
   ▼
Node B
   │
   ▼
Node C
   │
   ▼
END
```

If conditional edges or loops are present, execution may revisit nodes multiple times before reaching the end.

This execution model allows LangGraph to naturally represent complex reasoning workflows.

---

# Putting It All Together

The following diagram illustrates how the four core concepts interact.

```
           START
              │
              ▼
      Shared State
              │
              ▼
        +-----------+
        |  Node A   |
        +-----------+
              │
        Updated State
              │
              ▼
        +-----------+
        |  Node B   |
        +-----------+
              │
      Conditional Edge
         ┌────┴─────┐
         ▼          ▼
     Continue    Retry
         │          │
         └────┬─────┘
              ▼
             END
```

In this workflow:

- The graph maintains a shared state.
- Nodes perform individual tasks.
- Edges determine execution flow.
- Conditional edges allow dynamic behavior.
- Execution ends only when the graph reaches the END node.

