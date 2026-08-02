"""
graph.py

Build and compile the LangGraph workflow.
"""

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.prebuilt import tools_condition

from state import AssistantState
from agents import (
    supervisor,
    memory_node,
    assistant_node,
    supervisor_router,
)
from tools import tool_node

# ==========================================================
# Build Graph
# ==========================================================

builder = StateGraph(AssistantState)

# ==========================================================
# Nodes
# ==========================================================

builder.add_node("supervisor", supervisor)
builder.add_node("memory", memory_node)
builder.add_node("assistant", assistant_node)
builder.add_node("tools", tool_node)

# ==========================================================
# Start
# ==========================================================

builder.add_edge(
    START,
    "supervisor",
)

# ==========================================================
# Supervisor Routing
# ==========================================================

builder.add_conditional_edges(
    "supervisor",
    supervisor_router,
)

# ==========================================================
# ReAct Loop
# ==========================================================

builder.add_conditional_edges(
    "assistant",
    tools_condition,
)

builder.add_edge(
    "tools",
    "assistant",
)

# ==========================================================
# Finish
# ==========================================================

builder.add_edge(
    "memory",
    END,
)

# IMPORTANT:
# Do NOT add assistant -> END directly.
# tools_condition automatically routes either
# to ToolNode or to END.

# ==========================================================
# Compile
# ==========================================================

app = builder.compile()