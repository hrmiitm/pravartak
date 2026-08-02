"""
tools.py

All tools used by the AI Assistant.
"""

import ast
import operator
import settings

from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

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

    raise ValueError("Unsupported mathematical expression")


# ==========================================================
# Calculator Tool
# ==========================================================

@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    """

    if settings.LEARN_MODE:
        print("\n🛠 Current Node : ToolNode")
        print("⚙ Tool         : Calculator")
        print(f"📥 Input        : {expression}")

    try:

        tree = ast.parse(
            expression,
            mode="eval",
        )

        result = evaluate(tree.body)

        if settings.LEARN_MODE:
            print(f"📤 Output       : {result}")

        return str(result)

    except Exception as e:

        return f"Calculation Error: {e}"


# ==========================================================
# Weather Tool
# ==========================================================

@tool
def weather(city: str) -> str:
    """
    Dummy weather tool.

    Replace with a real API later.
    """

    if settings.LEARN_MODE:
        print("\n🛠 Current Node : ToolNode")
        print("⚙ Tool         : Weather")
        print(f"📍 City         : {city}")

    result = f"It is currently sunny in {city}."

    if settings.LEARN_MODE:
        print(f"📤 Output       : {result}")

    return result


# ==========================================================
# Register Tools
# ==========================================================

TOOLS = [
    calculator,
    weather,
]

tool_node = ToolNode(TOOLS)