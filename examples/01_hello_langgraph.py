from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# -----------------------------
# Define the Graph State
# -----------------------------
class GraphState(TypedDict):
    message: str


# -----------------------------
# Define a Node
# -----------------------------
def greet(state: GraphState):
    print("Hello from LangGraph!")

    return {
        "message": "Welcome to LangGraph!"
    }


# -----------------------------
# Build the Graph
# -----------------------------
builder = StateGraph(GraphState)

builder.add_node("greet", greet)

builder.add_edge(START, "greet")
builder.add_edge("greet", END)

graph = builder.compile()


# -----------------------------
# Execute
# -----------------------------
result = graph.invoke(
    {
        "message": ""
    }
)

print(result)