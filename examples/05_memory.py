from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END


# ----------------------------
# Shared State
# ----------------------------
class GraphState(TypedDict):
    message: str
    conversation_count: int


# ----------------------------
# Node
# ----------------------------
def remember(state: GraphState):
    print("\n=== Memory Node ===")
    print("Current State:", state)

    return {
        "conversation_count": state["conversation_count"] + 1
    }


# ----------------------------
# Build Graph
# ----------------------------
builder = StateGraph(GraphState)

builder.add_node("remember", remember)

builder.add_edge(START, "remember")
builder.add_edge("remember", END)


# ----------------------------
# Add Memory
# ----------------------------
memory = InMemorySaver()

graph = builder.compile(
    checkpointer=memory
)


config = {
    "configurable": {
        "thread_id": "user-1"
    }
}


print("\n===== First Call =====")

result = graph.invoke(
    {
        "message": "Hello",
        "conversation_count": 0
    },
    config=config
)

print(result)


print("\n===== Second Call =====")

result = graph.invoke(
    {
        "message": "Hello Again",
        "conversation_count": result["conversation_count"]
    },
    config=config
)

print(result)