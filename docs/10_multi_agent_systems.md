# Module 10 — Multi-Agent Systems in LangGraph

---

# Learning Objectives

By the end of this module, you will be able to:

- Understand what Multi-Agent Systems are.
- Learn why multiple specialized agents are useful.
- Understand how agents communicate.
- Build scalable AI workflows using LangGraph.
- Identify situations where multiple agents outperform a single agent.

---

# Prerequisites

Before starting this module, you should understand:

- State Management
- Nodes and Edges
- Conditional Routing
- Tool Calling

---

# What is a Multi-Agent System?

A Multi-Agent System (MAS) is a collection of specialized AI agents that work together to solve a problem.

Instead of one large agent trying to perform every task, responsibilities are divided among multiple smaller agents.

Each agent specializes in one task and collaborates with others when necessary.

---

# Why Use Multiple Agents?

As AI applications grow, a single agent becomes difficult to manage.

For example, imagine an assistant that needs to:

- Answer general questions
- Search the web
- Remember user information
- Generate code
- Analyze documents

Combining all these responsibilities into one agent increases complexity and makes debugging difficult.

Specialized agents solve this problem.

---

# Single-Agent vs Multi-Agent

## Single-Agent

```
User

↓

Assistant

↓

Everything
```

Advantages:

- Simple
- Easy to build

Disadvantages:

- Difficult to scale
- Large prompts
- Complex reasoning

---

## Multi-Agent

```
User

↓

Supervisor

↓

Research Agent

Memory Agent

Coding Agent

Weather Agent

↓

Final Response
```

Advantages:

- Modular
- Easier debugging
- Better scalability
- Independent improvements

---

# Agent Roles

A Multi-Agent System typically consists of:

| Agent | Responsibility |
|--------|---------------|
| Supervisor | Coordinate execution |
| Memory Agent | Store and retrieve user data |
| Research Agent | Search external knowledge |
| Tool Agent | Execute tools |
| Coding Agent | Generate or review code |

Each agent has a clearly defined responsibility.

---

# Agent Communication

Agents communicate through shared state.

Example:

```
User

↓

Supervisor

↓

Research Agent

↓

State Updated

↓

Assistant

↓

Response
```

The shared state allows information to flow between agents without tightly coupling their implementations.

---

# Multi-Agent Workflow

Example:

User:

```
What is the weather in Tokyo and who invented Python?
```

Execution:

```
Supervisor

↓

Weather Agent

↓

Research Agent

↓

Assistant

↓

Final Response
```

Each agent contributes only the information it is responsible for.

---

# Benefits

- Separation of concerns
- Reusable agents
- Parallel execution
- Better maintainability
- Easier testing

---

# Challenges

- Increased coordination
- State synchronization
- Routing complexity
- Debugging communication

---

# Best Practices

- Give each agent one responsibility.
- Minimize communication between agents.
- Keep prompts specialized.
- Share only the necessary state.
- Use a supervisor to coordinate execution.

---

# Common Mistakes

❌ One agent doing every task.

❌ Overlapping responsibilities.

❌ Excessive communication.

❌ Sharing unnecessary data.

---

# Key Takeaways

- Multi-Agent Systems divide work among specialized agents.
- A Supervisor coordinates execution.
- Shared state enables communication.
- Modular agents are easier to scale and maintain.

---

# Exercises

1. Design a Research Agent and a Memory Agent for an AI assistant.
2. Create a workflow involving three specialized agents.
3. Explain why a Supervisor is important in a Multi-Agent architecture.

---

# Summary

Multi-Agent Systems improve scalability, modularity, and maintainability by dividing complex AI tasks among specialized agents. LangGraph provides an effective framework for coordinating these agents through shared state and graph-based execution.