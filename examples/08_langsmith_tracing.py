"""
====================================================================
Example 08 : LangSmith Tracing with LangGraph
====================================================================

Author : IITM Pravartak Workshop

Learning Objectives
-------------------
1. Enable LangSmith tracing.
2. Trace LangGraph executions.
3. View execution timeline.
4. Debug tool calls.
5. Understand observability in AI applications.

Prerequisites
-------------
1. LangSmith Account
2. API Key in .env
3. Ollama running
4. qwen3:4b installed

Required .env
-------------

LANGSMITH_API_KEY=your_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=LangGraph-Workshop
"""

from dotenv import load_dotenv

load_dotenv()

import ast
import operator

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from langgraph.graph import MessagesState
from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

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

    raise ValueError("Unsupported expression")


@tool
def calculator(expression: str) -> str:
    """Safely evaluate arithmetic expressions."""

    tree = ast.parse(expression, mode="eval")

    return str(
        evaluate(tree.body)
    )


tools = [calculator]

# ==========================================================
# Local LLM
# ==========================================================

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
)

llm = llm.bind_tools(tools)

SYSTEM_PROMPT = """
You are a helpful AI assistant.

Use the calculator tool whenever a mathematical
calculation is required.
"""


# ==========================================================
# Assistant Node
# ==========================================================

def assistant(state: MessagesState):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = llm.invoke(messages)

    return {
        "messages": [response]
    }


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
    ToolNode(tools),
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
# Run
# ==========================================================

question = "What is (245 + 755) * 3?"

print("=" * 60)
print("LangSmith Tracing Demo")
print("=" * 60)

result = graph.invoke(
    {
        "messages": [
            HumanMessage(content=question)
        ]
    }
)

print("\nConversation\n")

for message in result["messages"]:

    print(f"\n[{message.type.upper()}]")

    if message.content:
        print(message.content)

print("\n")
print("=" * 60)
print("Execution completed.")
print("=" * 60)

print("\nOpen LangSmith Dashboard.")

print("Project:")

print("LangGraph-Workshop")

print("\nYou should now see:")

print("""
Run
│
├── Assistant
├── ToolNode
├── Assistant
└── END
""")