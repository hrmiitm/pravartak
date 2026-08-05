from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ----------------------------
# Shared State
# ----------------------------
class GraphState(TypedDict):
    message: str
    route: str
    response: str


# ----------------------------
# Router Node
# ----------------------------
def router(state: GraphState):
    print("\n=== Router ===")
    print(state)

    message = state["message"].lower()

    if any(word in message for word in ["add", "sum", "multiply", "calculate"]):
        return {"route": "calculator"}

    return {"route": "search"}


# ----------------------------
# Calculator Node
# ----------------------------
def calculator(state: GraphState):
    print("\n=== Calculator Node ===")

    return {
        "response": "Calculator would solve the mathematical problem."
    }


# ----------------------------
# Search Node
# ----------------------------
def search(state: GraphState):
    print("\n=== Search Node ===")

    return {
        "response": "Search tool would retrieve information."
    }


# ----------------------------
# Routing Function
# ----------------------------
def decide_next_node(state: GraphState):
    return state["route"]


# ----------------------------
# Build Graph
# ----------------------------
builder = StateGraph(GraphState)

builder.add_node("router", router)
builder.add_node("calculator", calculator)
builder.add_node("search", search)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    decide_next_node,
    {
        "calculator": "calculator",
        "search": "search",
    },
)

builder.add_edge("calculator", END)
builder.add_edge("search", END)

graph = builder.compile()


# ----------------------------
# Execute
# ----------------------------
result = graph.invoke(
    {
        "message": "Please calculate 25 plus 17",
        "route": "",
        "response": "",
    }
)

print("\n====================")
print("Final State")
print("====================")
print(result)