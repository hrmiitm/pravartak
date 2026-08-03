# LangGraph Agentic AI Workshop

## Overview

This repository contains the material developed for the **LangGraph Agentic AI Workshop**, along with a reference implementation of a modular AI assistant built using LangGraph and LangChain.

The workshop is designed to introduce the fundamental concepts required to build agentic AI systems, progressing from prompt-based interactions to graph-based workflows, persistent memory, tool integration, and production-oriented design principles.

The repository serves two purposes:

- Workshop material covering the core concepts of LangGraph.
- A working reference implementation demonstrating those concepts in practice.

---

## Workshop Structure

The workshop consists of the following modules.

| Module | Topic |
|---------|-------|
| 00 | Workshop Overview |
| 01 | From Prompt to Agentic AI |
| 02 | Agentic Workflow Patterns |
| 03 | LangGraph Fundamentals |
| 04 | State Management |
| 05 | Nodes and Edges |
| 06 | Conditional Routing |
| 07 | Memory |
| 08 | Tool Calling |
| 09 | Human-in-the-Loop |
| 10 | Multi-Agent Systems |
| 11 | LangSmith |
| 12 | Production Best Practices |

Each module introduces a single concept and gradually builds towards a complete LangGraph application.

---

## Reference Implementation

The workshop includes a reference AI assistant demonstrating the concepts introduced throughout the modules.

### Features

- Graph-based workflow orchestration using LangGraph
- Deterministic supervisor-based routing
- Persistent memory backed by SQLite
- External tool integration
- Live weather retrieval
- Mathematical expression evaluation
- Wikipedia search
- Interactive learning mode with execution tracing
- Performance profiling

---

## Architecture

```
                   User
                     │
                     ▼
              Supervisor Node
            ┌─────────┴─────────┐
            ▼                   ▼
      Memory Node        Assistant Node
            │                   │
            ▼                   ▼
        SQLite DB          ToolNode
                                │
        ┌──────────────┬───────────────┬──────────────┐
        ▼              ▼               ▼
   Calculator     Weather API     Wikipedia
```

---

## Repository Structure

```
langgraph-agentic-workshop/

├── docs/
│   ├── 00_workshop_overview.md
│   ├── ...
│   └── 12_production_best_practices.md
│
├── examples/
│   ├── 01_hello_langgraph.py
│   ├── ...
│   └── 10_ai_assistant/
│
├── README.md
└── requirements.txt
```

---

## Installation

Clone the repository.

```bash
git clone <repository-url>
cd langgraph-agentic-workshop
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate the environment.

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Install the required packages.

```bash
pip install -r requirements.txt
```

---

## Running the Workshop

The workshop examples are located under the `examples/` directory and correspond to the documentation modules.

Each example can be executed independently.

Example:

```bash
python examples/01_hello_langgraph.py
```

---

## Running the AI Assistant

Navigate to the assistant.

```bash
cd examples/10_ai_assistant
```

Run the application.

```bash
python app.py
```

Two execution modes are available:

- **Learn Mode** – Displays graph execution, routing decisions, tool invocation, and execution timings.
- **Chat Mode** – Runs the assistant without execution tracing.

---

## Example Queries

**Calculator**

```
What is 125 * 125?
```

**Weather**

```
What is the weather in Tokyo?
```

**Memory**

```
My name is Alice.
```

```
What is my name?
```

**General Conversation**

```
Hello
```

---

## Technologies

- Python
- LangGraph
- LangChain
- Ollama
- SQLite
- HTTPX

---

## Future Work

Potential extensions include:

- Retrieval-Augmented Generation (RAG)
- Vector database integration
- Additional external tools
- Human approval workflows
- Multi-agent collaboration
- Document question answering

---

## License

This repository is released under the MIT License.
