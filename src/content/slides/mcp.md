---
marp: true
title: Model Context Protocol (MCP)
description: A practical introduction to tools, resources, prompts, and one Python server
theme: default
size: 16:9
paginate: true
---

<!-- _class: lead -->
<!-- _paginate: false -->

# Model Context Protocol

One standard connection for AI, tools, and data.

<!-- notes
Set the outcome: learners should be able to explain the connection and run one small server, not memorize every protocol message.
-->

---

## Why MCP?

LLMs do not automatically know private or live information.

```text
Without MCP: each AI app builds custom connections to each system
With MCP:    compatible AI apps connect through a common interface
```

MCP is an AI-facing adapter—not a replacement for APIs, databases, or models.

<!-- notes
Use an order status or student policy as a concrete example. The existing API or database remains in place behind the MCP server.
-->

---

## The connection

```text
User → AI host → MCP client ── stdio / HTTP ── MCP server → API / files / database
                   │
                   └── one connection per server
```

| Part | Owns |
| --- | --- |
| Host | Model + MCP connections |
| Client | Protocol conversation |
| Server | Published capabilities |

<!-- notes
Clarify that an MCP host is the AI application, not necessarily the machine where a server is deployed.
-->

---

## Three capabilities

| Capability | Think of it as | Example |
| --- | --- | --- |
| **Tool** | Action | `percentage(425, 500)` |
| **Resource** | Data | `course://grading-policy` |
| **Prompt** | Reusable instruction | `explain_mark(85)` |

```text
Tool = action     Resource = data     Prompt = instruction
```

<!-- notes
Ask learners which capability a document belongs to. The usual answer is a resource, unless they need a tool to search it.
-->

---

## What happens on a tool call?

```text
1. Client lists tools and their schemas
2. Model selects a tool + arguments
3. Host sends tools/call to the server
4. Server validates, runs code, returns a result
5. Model uses the result in its reply
```

The SDK handles JSON-RPC, initialization, and capability negotiation.

<!-- notes
Keep the distinction sharp: the model chooses; the host and server execute. The model itself does not run the Python function.
-->

---

## Direct function or MCP server?

| Question | Direct function | MCP server |
| --- | --- | --- |
| Lives where? | Chatbot process | Separate server process |
| Host gets it how? | `tools=[percentage]` | Discovers it through MCP |
| Call crosses? | Python function call | `stdio` or HTTP protocol |
| Reusable by another host? | Only by importing code | Yes |

Both use tool calling: the model chooses; MCP changes the connection.

<!-- notes
Direct tools are ideal for a small private capability. MCP earns its complexity when a capability should be reused, isolated, or separately operated.
-->

---

## Build the server

```bash
mkdir mcp-starter && cd mcp-starter
uv init
uv add "mcp[cli]"
```

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Student Tools")

@mcp.tool()
def percentage(obtained: float, total: float) -> dict:
    if not 0 <= obtained <= total or total <= 0:
        raise ValueError("Invalid marks")
    return {"percentage": round(obtained / total * 100, 2)}
```

<!-- notes
The docs page contains the complete three-capability server. Highlight that the decorator, docstring, and type hints become a usable interface for the client.
-->

---

## Chatbot A: direct Python tool

```bash
uv add openai-agents
export OPENAI_API_KEY="your-api-key"
```

```python
@function_tool
def percentage(obtained: float, total: float) -> dict: ...

agent = Agent(name="Student Assistant", tools=[percentage])
result = await Runner.run(agent, "I got 425 out of 500")
```

```text
User → model → imported Python function → model → reply
```

<!-- notes
The tool is an in-process function. The chatbot owns its code, schema, and execution. This is ordinary function tool calling.
-->

---

## Chatbot B: local MCP server

```python
async with MCPServerStreamableHttp(
    name="Student Tools",
    params={"url": "http://127.0.0.1:8000/mcp"},
) as server:
    agent = Agent(name="Student Assistant", mcp_servers=[server])
    result = await Runner.run(agent, "I got 425 out of 500")
```

```text
User → model → MCP client → local MCP server → percentage() → model → reply
```

Run `server.py` in terminal 1, then `mcp_chatbot.py` in terminal 2.

<!-- notes
The chatbot does not import percentage. It connects, lists the server's tool schemas, and invokes the selected tool through MCP.
-->

---

## Check your understanding

**Q:** A server exposes `course://policy`. Which capability is it?<br />
**A:** A resource.

**Q:** How do I run the local MCP chatbot?<br />
**A:** Start `server.py` in terminal 1, then run `mcp_chatbot.py` in terminal 2.

**Q:** What is the key relationship?<br />
**A:** Tool calling chooses. Direct functions run in-process. MCP discovers and calls an external server.

Start small: run both chatbot versions with the same marks question.

<!-- notes
Close by asking learners why an IDE assistant can reuse the MCP server but cannot reuse a function that lives only inside another chatbot process.
-->
