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

## One chatbot, two tools

| Capability | Boundary | Why? |
| --- | --- | --- |
| `validate_marks(425, 500)` | Direct Python tool | Chatbot-specific safety check |
| `percentage(425, 500)` | MCP server tool | Shared student-service capability |

Both are selected by the model in the **same answer**.

<!-- notes
The key is not that MCP is more advanced. Choose the smallest boundary that matches ownership and reuse: a local validation rule stays in the chatbot; the reusable student calculation lives behind MCP.
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
    score = round(obtained / total * 100, 2)
    grade = "Excellent" if score >= 90 else "Very Good" if score >= 75 else "Good" if score >= 60 else "Pass" if score >= 40 else "Fail"
    return {"percentage": score, "grade": grade}
```

<!-- notes
This short slide shows the MCP boundary. The lesson has the complete grade-band logic and resource/prompt examples.
-->

---

## One chatbot configuration

```bash
uv add openai-agents
ollama pull gemma4:e2b
```

```python
ollama = AsyncOpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
model = OpenAIChatCompletionsModel("gemma4:e2b", ollama)

@function_tool
def validate_marks(obtained: float, total: float) -> str: ...

async with MCPServerStreamableHttp(
    name="Student Tools", params={"url": "http://127.0.0.1:8000/mcp"}
) as server:
    agent = Agent(
        name="Student Assistant",
        model=model,
        tools=[validate_marks],
        mcp_servers=[server],
    )
```

<!-- notes
This SDK exposes the server's MCP tools to the Agent. A full MCP host also discovers resource and prompt metadata, then lets the model choose the matching capability.
-->

---

## One question, both paths

```bash
# Terminal 1
uv run code-test/mymcp.py

# Terminal 2
uv run code-test/chatbot.py
```

```text
I scored 425 out of 500. What is my percentage and grade?
    ↓
validate_marks(425, 500) → valid             [direct function]
percentage(425, 500) → 85.0, "Very Good"   [local MCP server]
    ↓
Assistant reply
```

<!-- notes
The agent discovers percentage from MCP, but runs validate_marks locally. In a full MCP host, the model can also choose a resource or prompt after the host has discovered their metadata.
-->

---

## Check your understanding

**Q:** A server exposes `course://policy`. Which capability is it?<br />
**A:** A resource.

**Q:** Why is validation a direct tool?<br />
**A:** It is small, local, and specific to this chatbot.

**Q:** What is the key relationship?<br />
**A:** Tool calling chooses both. MCP is used when a capability should be shared or separately managed.

Start small: run one chatbot that uses both boundaries.

<!-- notes
Close by asking learners whether their next capability is application-private or shared across hosts. That is the practical decision point.
-->
