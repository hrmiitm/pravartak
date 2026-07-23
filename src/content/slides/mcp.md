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

## MCP vs tool calling vs RAG

| Question | Short answer |
| --- | --- |
| Does MCP replace tool calling? | No—tool calling chooses; MCP connects. |
| Does MCP replace REST? | No—it often wraps an existing API. |
| Does MCP replace RAG? | No—RAG retrieves context; MCP can expose retrieval. |

> MCP standardizes the connection, not the model’s reasoning.

<!-- notes
This is a high-value Q and A slide. Repeat the simple relationship: tool calling chooses, MCP connects, RAG retrieves.
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

## Run and test

Terminal 1:

```bash
uv run python server.py
```

Terminal 2:

```bash
npx -y @modelcontextprotocol/inspector
```

Connect Inspector to `http://localhost:8000/mcp` → list tools → call `percentage(425, 500)` → expect **85.0**.

<!-- notes
The MCP endpoint is not a normal web page. Inspector is a fast way to verify discovery and execution before connecting an AI host.
-->

---

## Local or remote?

| Use case | Prefer | Remember |
| --- | --- | --- |
| Desktop / IDE / local files | `stdio` | Logs go to stderr, never stdout |
| Shared cloud service | Streamable HTTP | HTTPS, authentication, authorization |

For remote tools: validate inputs, least privilege, user confirmation for writes, and safe audit logs.

<!-- notes
Avoid treating a tool description as a security boundary. The server owns validation and authorization.
-->

---

## Check your understanding

**Q:** A server exposes `course://policy`. Which capability is it?<br />
**A:** A resource.

**Q:** What happens before a database query?<br />
**A:** The server validates arguments and authorizes the request.

**Q:** What is the key relationship?<br />
**A:** Tool calling chooses. MCP connects. RAG retrieves.

Start small: publish one safe tool, inspect it, then connect a real system.

<!-- notes
Close by asking learners to change the grade thresholds or add a read-only attendance lookup, then use Inspector to check the interface again.
-->
