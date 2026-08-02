"""
agents.py

All LangGraph nodes used by the AI Assistant.
"""
import settings

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from config import llm
from memory import (
    remember_name,
    get_name,
)
from prompts import (
    SUPERVISOR_PROMPT,
    ASSISTANT_PROMPT,
)
from tools import TOOLS


# ==========================================================
# ReAct Assistant
# ==========================================================

assistant_llm = llm.bind_tools(TOOLS)


# ==========================================================
# Supervisor Node
# ==========================================================

def supervisor(state):
    """
    Supervisor Node

    Decides which node should handle the user's request.
    """

    last_message = state["messages"][-1].content
    text = last_message.lower()

    if settings.LEARN_MODE:
        print("\n" + "=" * 70)
        print("🧭 LANGGRAPH EXECUTION")
        print("=" * 70)
        print(f"📍 Current Node : Supervisor")
        print(f"📨 User Query   : {last_message}")

    # Memory routing
    if (
        "my name is" in text
        or "what's my name" in text
        or "what is my name" in text
        or "remember" in text
    ):

        if settings.LEARN_MODE:
            print("✅ Decision     : Route → Memory Node")

        return {"route": "memory"}

    response = llm.invoke(
        [
            SystemMessage(content=SUPERVISOR_PROMPT),
            state["messages"][-1],
        ]
    )

    route = response.content.strip().lower()

    if settings.LEARN_MODE:
        print(f"✅ Decision     : Route → {route.title()} Node")

    return {"route": route}

  

# ==========================================================
# Memory Node
# ==========================================================
def memory_node(state):

    if settings.LEARN_MODE:
        print("\n🧠 Current Node : Memory")

    last_message = state["messages"][-1].content
    text = last_message.lower()

    # -------------------------------
    # Remember name
    # -------------------------------

    if "my name is" in text:

        name = last_message.split("is", 1)[1].strip()

        if settings.LEARN_MODE:
            print(f"💾 Action       : Store Name = {name}")

        remember_name(name)

        return {
            "messages": [
                AIMessage(
                    content=f"Nice to meet you, {name}! I'll remember your name."
                )
            ]
        }

    # -------------------------------
    # Recall name
    # -------------------------------

    if (
        "what is my name" in text
        or "what's my name" in text
    ):

        if settings.LEARN_MODE:
            print("🔍 Action       : Retrieve Name")

        name = get_name()

        if name:

            return {
                "messages": [
                    AIMessage(
                        content=f"Your name is {name}."
                    )
                ]
            }

        return {
            "messages": [
                AIMessage(
                    content="I don't know your name yet."
                )
            ]
        }

    return {
        "messages": [
            AIMessage(
                content="Nothing was stored in memory."
            )
        ]
    }


# ==========================================================
# Assistant Node
# ==========================================================

def assistant_node(state):

    if settings.LEARN_MODE:
        print("\n🤖 Current Node : Assistant")
        print("🧠 Action       : Thinking...")

    response = assistant_llm.invoke(
        [
            SystemMessage(content=ASSISTANT_PROMPT),
            *state["messages"],
        ]
    )

    if settings.LEARN_MODE:

        if response.tool_calls:
            print("🛠 Decision     : Tool Required")

        else:
            print("💬 Decision     : Respond Directly")

    return {
        "messages": [response]
    }


# ==========================================================
# Router
# ==========================================================

def supervisor_router(state):

    route = state["route"]

    if route == "memory":
        return "memory"

    return "assistant"