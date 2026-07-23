---
title: Model Context Protocol (MCP)
description: Connect an AI application to reusable tools, data, and workflows with one practical Python server.
sidebar:
  order: 1
---

# Model Context Protocol (MCP)

**MCP is a common way for an AI application to discover and use external capabilities.** It gives an AI host a consistent connection to tools, data, and reusable prompts instead of requiring a custom integration for every system.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>10 slides · diagrams · Q&amp;A · runnable demo</small></p>
  <a href="../../slides/mcp/">Open slide deck →</a>
</div>

## The problem it solves

An LLM can reason over the text it receives, but it does not automatically know the latest order status, read a private policy, or create a ticket. An application can add those abilities with tools—but bespoke connections do not scale well.

```text
Without MCP:  each AI app writes a custom GitHub / database / files integration
With MCP:     compatible AI apps use one standard interface to each MCP server
```

MCP is often an adapter around systems that already exist. It does **not** replace REST APIs, databases, or the model. It standardizes the AI-facing connection to them.

## The architecture

```text
User → AI host → MCP client ── stdio or Streamable HTTP ── MCP server → API / files / database
                   │
                   └── one client connection per server
```

| Part | Responsibility |
| --- | --- |
| **Host** | The AI application that manages the model and its MCP connections. |
| **Client** | The host component that speaks MCP to one server. |
| **Server** | A program that publishes capabilities. |
| **Transport** | The channel carrying protocol messages: local `stdio` or Streamable HTTP. |

The protocol uses JSON-RPC messages and starts with initialization and capability negotiation. SDKs normally handle those messages for you.

## Three capabilities to remember

| Capability | Think of it as | Example |
| --- | --- | --- |
| **Tool** | Action | `calculate_grade(score)` |
| **Resource** | Readable data | `course://grading-policy` |
| **Prompt** | Reusable instruction | `explain_mark(score)` |

```text
Tool = action     Resource = data     Prompt = repeatable instruction
```

## MCP, tool calling, and RAG

**Q: Does MCP replace tool calling?**<br />
No. Tool calling is how a model chooses a function and its arguments. MCP is a standard way for the host to discover and invoke an external capability.

**Q: Does MCP replace APIs or RAG?**<br />
No. An MCP server can call an existing API. RAG retrieves relevant documents for the model’s context; an MCP server can expose a search tool or resource used by a RAG workflow.

```text
Model chooses a tool → host sends MCP tools/call → server runs code → result returns to model
```

## Build one small server

Create an isolated Python project and add the official SDK:

```bash
mkdir mcp-starter && cd mcp-starter
uv init
uv add "mcp[cli]"
```

Create `server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Student Tools")


@mcp.tool()
def percentage(obtained: float, total: float) -> dict:
    """Calculate a student's percentage and grade category."""
    if not 0 <= obtained <= total or total <= 0:
        raise ValueError("Marks must satisfy 0 <= obtained <= total.")

    score = round(obtained / total * 100, 2)
    grade = "Excellent" if score >= 90 else "Very Good" if score >= 75 else "Good" if score >= 60 else "Pass" if score >= 40 else "Fail"
    return {"percentage": score, "grade": grade}


@mcp.resource("course://grading-policy")
def grading_policy() -> str:
    """Return the grading bands used by the percentage tool."""
    return "90+: Excellent; 75–89.99: Very Good; 60–74.99: Good; 40–59.99: Pass; below 40: Fail."


@mcp.prompt()
def explain_mark(score: float) -> str:
    """Create a reusable instruction for explaining a mark kindly."""
    return f"Explain a score of {score}% in two encouraging sentences and suggest one next step."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

`@mcp.tool()`, `@mcp.resource()`, and `@mcp.prompt()` publish the three capabilities. Type hints and docstrings give a compatible client a schema and useful descriptions.

## Run and verify it

Start the server in one terminal:

```bash
uv run python server.py
```

It serves the Streamable HTTP endpoint at `http://localhost:8000/mcp`. In a second terminal, launch the official Inspector:

```bash
npx -y @modelcontextprotocol/inspector
```

Open the Inspector URL it prints, connect to `http://localhost:8000/mcp`, list the tools, and call `percentage` with `obtained: 425` and `total: 500`. The expected result is `85.0` and `Very Good`.

For a local-only integration, `stdio` is also common: the AI host starts the server as a subprocess. Never send normal logs to stdout in that mode—stdout carries protocol messages; log to stderr instead.

## Design safely

- Treat tool descriptions and model output as untrusted input; validate every argument on the server.
- Give each tool the least access it needs. A read-only lookup should not gain write permissions.
- Ask for user confirmation before actions with real-world effects, such as sending mail or deleting data.
- Keep credentials in environment-managed secrets, not source code or tool arguments.
- For remote servers, use HTTPS, authenticate users, authorize each operation, and record safe audit logs.

## Quick check

1. Why is an MCP server useful when an application already has a REST API?
2. Which capability fits a course-policy document: tool, resource, or prompt?
3. What validates the arguments before the server reaches a database or external API?

Answers: MCP provides the AI-facing discovery and invocation layer; the policy is a resource; and server-side validation is the control that must run before the action.

## Keep learning

- [MCP architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)
- [Official Python SDK quickstart](https://github.com/modelcontextprotocol/python-sdk)
- [MCP transport specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)

[Open the MCP slides](../../slides/mcp/)
