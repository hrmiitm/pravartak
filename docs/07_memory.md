# Module 07 — Memory in LangGraph

---

# Learning Objectives

By the end of this module, you will be able to:

- Understand why memory is important in AI applications.
- Differentiate between short-term and long-term memory.
- Implement persistent memory using SQLite.
- Store and retrieve user information.
- Integrate memory into a LangGraph workflow.

---

# Prerequisites

Before starting this module, you should understand:

- State Management
- Nodes and Edges
- Conditional Routing

---

# Why Do AI Assistants Need Memory?

Without memory, every conversation starts from scratch.

Example:

```
User:
My name is Alice.

Assistant:
Nice to meet you!

(New Session)

User:
What is my name?

Assistant:
I don't know.
```

This creates a poor user experience.

Memory allows an assistant to personalize future conversations.

---

# Types of Memory

## 1. Short-Term Memory

Exists only while the application is running.

Example:

```
Python Dictionary

↓

Close Program

↓

Memory Lost
```

---

## 2. Long-Term Memory

Stored permanently.

Example:

```
SQLite

↓

Restart Application

↓

Memory Still Exists
```

Our AI Assistant uses SQLite for persistent memory.

---

# Memory Architecture

```
User

↓

Supervisor

↓

Memory Node

↓

SQLite Database

↓

Assistant
```

The Memory Node is responsible for storing and retrieving information.

---

# Database Design

Our assistant stores information as simple key-value pairs.

| Key | Value |
|-----|-------|
| name | Alice |
| city | Chennai |
| language | Python |

This design makes it easy to extend memory without changing the database schema.

---

# SQLite Table

```sql
CREATE TABLE profile (

    key TEXT PRIMARY KEY,

    value TEXT
)
```

---

# Storing Memory

When the user says:

```
My name is Alice
```

the assistant performs:

```
remember("name", "Alice")
```

which stores:

```
Key   → name

Value → Alice
```

---

# Retrieving Memory

When the user asks:

```
What is my name?
```

the assistant performs:

```
recall("name")
```

and retrieves:

```
Alice
```

---

# Memory Workflow

```
User

↓

"My name is Alice"

↓

Memory Node

↓

SQLite

↓

assistant.db
```

Later:

```
User

↓

"What is my name?"

↓

Memory Node

↓

SQLite

↓

Alice

↓

Assistant
```

---

# Why SQLite?

SQLite is:

- Lightweight
- Fast
- Serverless
- Cross-platform
- Included with Python

For workshop projects and small AI assistants, SQLite is an excellent choice.

---

# Advantages of Persistent Memory

- Personalization
- Better conversations
- Information survives restart
- Easy debugging
- Simple deployment

---

# Common Mistakes

❌ Keeping everything in RAM.

❌ Storing large documents inside memory.

❌ Mixing memory logic with LLM code.

❌ Forgetting to initialize the database.

---

# Best Practices

- Separate memory from assistant logic.
- Store only important user information.
- Use descriptive keys.
- Keep database operations modular.

---

# Example Conversation

```
User:
My name is Alice.

Assistant:
Nice to meet you, Alice!

(Restart application)

User:
What is my name?

Assistant:
Your name is Alice.
```

This demonstrates persistent memory.

---

# Key Takeaways

- Memory enables personalized AI assistants.
- SQLite provides persistent storage.
- Key-value storage is simple and extensible.
- Memory should be implemented as an independent module.

---

# Exercises

### Exercise 1

Store the user's favorite programming language.

---

### Exercise 2

Store the user's city.

---

### Exercise 3

Modify the assistant so it remembers multiple preferences using different keys.

---

# Summary

Memory is one of the most important components of intelligent AI systems.

By separating memory into its own module and using SQLite for persistent storage, we build assistants that remember users across sessions while maintaining a clean and scalable architecture.