from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ----------------------------
# Shared State
# ----------------------------
class GraphState(TypedDict):
    a: int
    b: int
    operation: str
    result: int


# ----------------------------
# Calculator Tool
# ----------------------------
def calculator_tool(a: int, b: int, operation: str) -> int:
    print("\n>>> Calling Calculator Tool")

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a // b

    else:
        raise ValueError(f"Unknown operation: {operation}")


# ----------------------------
# Tool Node
# ----------------------------
def execute_tool(state: GraphState):
    print("\n=== Tool Node ===")
    print("State:", state)

    answer = calculator_tool(
        state["a"],
        state["b"],
        state["operation"]
    )

    return {
        "result": answer
    }


# ----------------------------
# Build Graph
# ----------------------------
builder = StateGraph(GraphState)

builder.add_node("tool", execute_tool)

builder.add_edge(START, "tool")
builder.add_edge("tool", END)

graph = builder.compile()


# ----------------------------
# Execute
# ----------------------------
result = graph.invoke(
    {
        "a": 25,
        "b": 17,
        "operation": "add",
        "result": 0
    }
)

print("\n===================")
print("Final State")
print("===================")
print(result)