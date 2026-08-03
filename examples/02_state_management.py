from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ----------------------------
# Define the shared state
# ----------------------------
class GraphState(TypedDict):
    message: str
    received: bool
    response: str


# ----------------------------
# Node 1
# ----------------------------
def receive_message(state: GraphState):
    print("\n=== Receive Message ===")
    print("Current State:", state)

    return {
        "received": True
    }


# ----------------------------
# Node 2
# ----------------------------
def process_message(state: GraphState):
    print("\n=== Process Message ===")
    print("Current State:", state)

    processed = state["message"].upper()

    return {
        "message": processed
    }


# ----------------------------
# Node 3
# ----------------------------
def generate_response(state: GraphState):
    print("\n=== Generate Response ===")
    print("Current State:", state)

    return {
        "response": f"Processed message: {state['message']}"
    }


# ----------------------------
# Build the graph
# ----------------------------
builder = StateGraph(GraphState)

builder.add_node("receive_message", receive_message)
builder.add_node("process_message", process_message)
builder.add_node("generate_response", generate_response)

builder.add_edge(START, "receive_message")
builder.add_edge("receive_message", "process_message")
builder.add_edge("process_message", "generate_response")
builder.add_edge("generate_response", END)

graph = builder.compile()


# ----------------------------
# Execute
# ----------------------------
result = graph.invoke(
    {
        "message": "hello langgraph",
        "received": False,
        "response": ""
    }
)

print("\n==============================")
print("Final State")
print("==============================")
print(result)