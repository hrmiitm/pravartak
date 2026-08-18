"""
====================================================================
Example 07 : ReAct Agent using LangGraph
====================================================================

Author : IITM Pravartak Workshop

Learning Objectives
-------------------
1. Understand the ReAct (Reason + Act) paradigm.
2. Build an AI agent using LangGraph.
3. Use MessagesState to maintain conversation history.
4. Integrate external tools into an AI workflow.
5. Use ToolNode for automatic tool execution.
6. Route dynamically using tools_condition().
7. Understand how LangGraph orchestrates agent workflows.

Architecture
------------

                START
                   │
                   ▼
           Assistant (LLM)
                   │
          tools_condition()
            │           │
            ▼           ▼
       ToolNode        END
            │
            └────────────► Assistant


Execution Flow
--------------

User Question
      │
      ▼
Assistant Node
      │
      ▼
Does the LLM request a tool?
      │
 ┌────┴────┐
 │         │
 ▼         ▼
ToolNode   END
 │
 ▼
Execute Tool
 │
 ▼
Tool Result
 │
 ▼
Assistant
 │
 ▼
Final Answer


Requirements
------------
pip install langgraph
pip install langchain
pip install langchain-ollama

Run Model
---------
ollama run qwen3:4b
"""

# ==========================================================
# Imports
# ==========================================================

import ast
import operator

from typing import Annotated

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from langchain_core.tools import tool

from langchain_ollama import ChatOllama

from langgraph.graph import (
    MessagesState,
    START,
    StateGraph,
)

from langgraph.prebuilt import (
    ToolNode,
    tools_condition,
)

# ==========================================================
# Safe Calculator
# ==========================================================

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def evaluate(node):
    """
    Safely evaluate an arithmetic expression.

    Supported Operations
    --------------------
    +
    -
    *
    /
    **
    Unary -
    """

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.BinOp):

        return OPERATORS[type(node.op)](
            evaluate(node.left),
            evaluate(node.right),
        )

    if isinstance(node, ast.UnaryOp):

        return OPERATORS[type(node.op)](
            evaluate(node.operand),
        )

    raise ValueError("Unsupported mathematical expression.")


# ==========================================================
# Tool 1 : Calculator
# ==========================================================

@tool
def calculator(expression: str) -> str:
    """
    Evaluate arithmetic expressions safely.

    Examples
    --------
    2 + 2

    (125 + 375) * 2

    5 ** 3
    """

    try:

        tree = ast.parse(
            expression,
            mode="eval",
        )

        result = evaluate(tree.body)

        return str(result)

    except Exception as e:

        return f"Calculation Error : {e}"


# ==========================================================
# Tool 2 : Weather
# ==========================================================

@tool
def weather(city: str) -> str:
    """
    Dummy weather service.

    In production this would call
    an external Weather API.
    """

    return f"It is currently sunny in {city}."


# ==========================================================
# Register Tools
# ==========================================================

tools = [
    calculator,
    weather,
]

# ==========================================================
# Local LLM
# ==========================================================

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
)

# Bind tools to the model
llm_with_tools = llm.bind_tools(tools)
# ==========================================================
# Assistant Node
# ==========================================================

SYSTEM_PROMPT = """
You are a helpful AI assistant.

Guidelines
----------
1. Answer general knowledge questions directly.
2. Use the calculator tool ONLY for mathematical calculations.
3. Use the weather tool ONLY for weather-related questions.
4. If a tool is available and appropriate, call it.
5. After receiving a tool result, provide a clear final answer.
"""


def assistant(state: MessagesState):
    """
    Main LLM node.

    This node:
    1. Receives the conversation.
    2. Decides whether to use a tool.
    3. Generates either:
        • A tool call
        • A final answer
    """

    print("\n" + "=" * 60)
    print("ASSISTANT NODE")
    print("=" * 60)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response],
    }


# ==========================================================
# Tool Node
# ==========================================================

tool_node = ToolNode(tools)

# ==========================================================
# Build Graph
# ==========================================================

builder = StateGraph(MessagesState)

builder.add_node(
    "assistant",
    assistant,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_edge(
    START,
    "assistant",
)

builder.add_conditional_edges(
    "assistant",
    tools_condition,
)

builder.add_edge(
    "tools",
    "assistant",
)

graph = builder.compile()

# ==========================================================
# Graph Visualization
# ==========================================================

print("\n")
print("=" * 60)
print("LANGGRAPH ARCHITECTURE")
print("=" * 60)

print(
    """
          START
             │
             ▼
      Assistant Node
             │
     tools_condition()
        │           │
        ▼           ▼
    Tool Node      END
        │
        └────────────► Assistant
"""
)

print("=" * 60)
# ==========================================================
# Helper Function
# ==========================================================

def display_messages(messages):
    """
    Display the conversation in a readable format.
    """

    print("\n" + "=" * 70)
    print("CONVERSATION")
    print("=" * 70)

    for message in messages:

        message_type = message.type.upper()

        print(f"\n[{message_type}]")

        if message.content:
            print(message.content)

        # Show tool calls made by the AI
        if hasattr(message, "tool_calls") and message.tool_calls:

            print("\nTool Calls:")

            for call in message.tool_calls:

                print(f"  Tool : {call['name']}")
                print(f"  Args : {call['args']}")

    print("\n" + "=" * 70)


# ==========================================================
# Run Demo
# ==========================================================

queries = [

    "What is (125 + 375) * 2?",

    "What is the weather in Chennai?",

    "Explain what LangGraph is.",

]

print("\n")
print("=" * 70)
print("Example 07 : ReAct Agent using LangGraph")
print("=" * 70)

for i, query in enumerate(queries, start=1):

    print(f"\n\nExample {i}")
    print("-" * 70)
    print(f"User : {query}")

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ]
        }
    )

    display_messages(result["messages"])

print("\n")
print("=" * 70)
print("Demo Complete")
print("=" * 70)

# ==========================================================
# Teaching Notes
# ==========================================================

print(
"""
==============================================================
Teaching Notes
==============================================================

ReAct = Reason + Act

Workflow:

User
 ↓
Assistant Node
 ↓
Need Tool?
 ↓
Tool Node
 ↓
Assistant Node
 ↓
Final Answer

Important Concepts

✓ MessagesState
Stores the complete conversation.

✓ Assistant Node
The LLM decides what to do next.

✓ ToolNode
Executes tools automatically.

✓ tools_condition()
Routes to ToolNode only when needed.

✓ ReAct Loop
Assistant
    ↓
Tool
    ↓
Assistant

This loop continues until the LLM no longer requests a tool.
"""
)

# ==========================================================
# Exercises
# ==========================================================

print(
"""
==============================================================
Exercises
==============================================================

1. Add a new Temperature Conversion tool.

2. Add a Currency Conversion tool.

3. Replace the dummy Weather tool with a real API.

4. Add a Wikipedia search tool.

5. Count how many tools were used in one conversation.

6. Add conversation memory.

7. Modify the assistant so it can use multiple tools
   in a single conversation.

==============================================================
Interview Questions
==============================================================

1. What is ReAct?

2. Why is MessagesState used?

3. What is ToolNode?

4. What does tools_condition() do?

5. Why does the graph contain a loop?

6. How is LangGraph different from LangChain Agents?

7. Why are graphs better than linear chains for
   building AI agents?

==============================================================
Best Practices
==============================================================

✓ Keep tools focused on one task.

✓ Use safe implementations for tools.

✓ Store conversation inside MessagesState.

✓ Keep the Assistant Node lightweight.

✓ Let ToolNode handle tool execution.

✓ Prefer conditional routing over manual if-else logic.

==============================================================
"""
)