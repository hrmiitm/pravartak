# Chapter 4: Building ReAct Agents with LangGraph

## Learning Objectives

By the end of this chapter, participants will be able to:

- Explain the ReAct (Reason + Act) paradigm.
- Understand why AI agents need tools.
- Create custom tools using LangChain.
- Build a ReAct agent using LangGraph.
- Observe how an agent reasons before taking action.
- Understand the execution flow of a production-style AI agent.

---

# What is ReAct?

ReAct stands for **Reason + Act**.

It is a prompting and execution paradigm in which an AI agent alternates between reasoning about a task and taking actions using external tools.

Rather than immediately generating a response, the agent follows an iterative process:

1. Think about the problem.
2. Decide whether additional information or computation is required.
3. Invoke an appropriate tool if necessary.
4. Observe the tool's output.
5. Continue reasoning until enough information is available.
6. Produce the final answer.

This approach allows AI systems to solve problems that require external knowledge, calculations, database access, or interaction with APIs.

---

# ReAct Architecture

```
                    User Query
                         │
                         ▼
                   ReAct Agent
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
          Internal Reasoning   Tool Required?
                                   │
                         ┌─────────┴─────────┐
                         ▼                   ▼
                    No Tool             Call Tool
                         │                   │
                         ▼                   ▼
                  Final Response      Observation
                                             │
                                             ▼
                                      Continue Reasoning
                                             │
                                             ▼
                                        Final Response
```

The key idea is that the language model is no longer responsible for answering every question directly. Instead, it decides when external tools are necessary and incorporates their outputs into its reasoning process.

---

# Why ReAct?

Traditional LLM applications generate responses using only the knowledge encoded within the model.

This approach has several limitations:

- Mathematical calculations may be inaccurate.
- Information may be outdated.
- The model cannot directly access external systems.
- It cannot execute code or retrieve private organizational data.

ReAct overcomes these limitations by allowing the model to invoke specialized tools whenever additional capabilities are required.

Examples include:

- Calculator
- Web Search
- SQL Database
- Vector Database (RAG)
- Python Execution
- File Systems
- REST APIs

---

# Agent Execution Flow

A typical ReAct agent follows the execution loop shown below.

```
User Question
      │
      ▼
  Language Model
      │
      ▼
Need a Tool?
 ┌────┴────┐
 │         │
 ▼         ▼
No        Yes
 │         │
 ▼         ▼
Answer   Execute Tool
            │
            ▼
      Tool Observation
            │
            ▼
      Language Model
            │
            ▼
      Final Answer
```

This execution cycle continues until the language model determines that it has sufficient information to answer the user's request.