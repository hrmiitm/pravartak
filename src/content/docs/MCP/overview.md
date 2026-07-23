---
title: Model Context Protocol (MCP)
description: Connect an AI application to reusable tools, data, and workflows with one practical Python server.
sidebar:
  order: 1
---

# Model Context Protocol (MCP)

**MCP is a common way for an AI application to discover and use external capabilities.** It gives an AI host a consistent connection to tools, data, and reusable prompts instead of requiring a custom integration for every system.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>10 slides · diagrams · Q&amp;A · chatbot demo</small></p>
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
def grade_band(score: float) -> str:
    """Return the institution's grade band for a percentage score."""
    if not 0 <= score <= 100:
        raise ValueError("Score must be between 0 and 100.")
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Very Good"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Pass"
    return "Fail"


@mcp.resource("course://grading-policy")
def grading_policy() -> str:
    """Return the grading bands used by the grade_band tool."""
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

Open the Inspector URL it prints, connect to `http://localhost:8000/mcp`, list the tools, and call `grade_band` with `score: 85`. The expected result is `Very Good`.

For a local-only integration, `stdio` is also common: the AI host starts the server as a subprocess. Never send normal logs to stdout in that mode—stdout carries protocol messages; log to stderr instead.

## One chatbot: use a direct tool and MCP together

This single example answers: **“I scored 425 out of 500. What is my percentage, and which grade band does the university policy assign?”**

- `calculate_percentage` is a small, deterministic calculation owned only by this chatbot, so it is a **direct function tool**.
- `grade_band` is the institution's shared policy. It lives behind the local MCP server so a chatbot, IDE assistant, or future student portal can use the same official rule.

Add the Agents SDK and set an API key:

```bash
uv add openai-agents
export OPENAI_API_KEY="your-api-key"
```

Create `student_chatbot.py`:

```python
import asyncio

from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStreamableHttp


@function_tool
def calculate_percentage(obtained: float, total: float) -> float:
    """Calculate a percentage from marks obtained and total marks."""
    if not 0 <= obtained <= total or total <= 0:
        raise ValueError("Marks must satisfy 0 <= obtained <= total.")
    return round(obtained / total * 100, 2)


async def main() -> None:
    async with MCPServerStreamableHttp(
        name="Student Policy",
        params={"url": "http://127.0.0.1:8000/mcp"},
        cache_tools_list=True,
    ) as server:
        agent = Agent(
            name="Student Assistant",
            instructions=(
                "For marks questions, first use calculate_percentage. "
                "Then use the Student Policy MCP tool grade_band to classify that score. "
                "Do not invent a grading policy."
            ),
            tools=[calculate_percentage],
            mcp_servers=[server],
        )
        question = input("You: ")
        result = await Runner.run(agent, question)
        print("Assistant:", result.final_output)


asyncio.run(main())
```

Run the complete example in two terminals:

```bash
# Terminal 1: policy service, running locally
uv run python server.py

# Terminal 2: chatbot host
uv run python student_chatbot.py
```

Ask: `I scored 425 out of 500. What is my percentage, and which grade band does the university policy assign?`

```text
User question
  → model selects calculate_percentage(425, 500)     [direct Python tool]
  → model selects grade_band(85.0)                    [MCP tool]
  → MCP client calls http://127.0.0.1:8000/mcp
  → server returns "Very Good"
  → model writes the final reply
```

## Why this split is useful

| Capability in this chatbot | Use direct function tool when… | Use MCP when… |
| --- | --- | --- |
| `calculate_percentage` | The logic is small, local, deterministic, and belongs only to this app. | Not needed for this one app. |
| `grade_band` | It would duplicate the official policy inside every chatbot. | The policy must be shared, independently updated, audited, or reused by compatible AI hosts. |

Both are still **tools chosen by the model**. The difference is the boundary: a direct tool is an in-process function, while MCP discovers and invokes a separately running service.

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
- [OpenAI Agents SDK: local Streamable HTTP MCP servers](https://openai.github.io/openai-agents-python/mcp/)

[Open the MCP slides](../../slides/mcp/)
