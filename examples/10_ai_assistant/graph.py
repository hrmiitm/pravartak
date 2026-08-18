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
    security_investigation_node,
    supervisor_router,
)

from tools import tool_node


# ==========================================================
# Tool Routing
# ==========================================================

def route_after_tools(state):
    """
    Decide what to do after ToolNode execution.

    Vulnerability investigations go through the
    Security Investigation node.

    Other tools return directly to the Assistant.
    """

    for message in reversed(state["messages"]):

        if getattr(message, "type", None) == "tool":

            if message.name == "vulnerability_lookup":
                return "security_investigation"

            return "assistant"

    return "assistant"


# ==========================================================
# Build Graph
# ==========================================================

builder = StateGraph(AssistantState)


# ==========================================================
# Nodes
# ==========================================================

builder.add_node(
    "supervisor",
    supervisor,
)

builder.add_node(
    "memory",
    memory_node,
)

builder.add_node(
    "assistant",
    assistant_node,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_node(
    "security_investigation",
    security_investigation_node,
)


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
# Assistant → Tools / END
# ==========================================================

builder.add_conditional_edges(
    "assistant",
    tools_condition,
)


# ==========================================================
# Tool Routing
# ==========================================================

builder.add_conditional_edges(
    "tools",
    route_after_tools,
)


# ==========================================================
# Security Investigation → Assistant
# ==========================================================

builder.add_edge(
    "security_investigation",
    "assistant",
)


# ==========================================================
# Memory → END
# ==========================================================

builder.add_edge(
    "memory",
    END,
)


# ==========================================================
# Compile
# ==========================================================

app = builder.compile()