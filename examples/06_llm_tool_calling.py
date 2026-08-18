"""
Example 06: LLM Tool Calling with Ollama

This example demonstrates how an LLM can decide to use
external tools.

Author: IITM Pravartak Workshop
"""

from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# ==========================================================
# Tool Definitions
# ==========================================================

@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.

    Example:
        25 + 17
        (10 * 5) / 2
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def weather(city: str) -> str:
    """
    Return dummy weather information.
    """
    return f"It is currently sunny in {city}."


# ==========================================================
# Initialize Local LLM
# ==========================================================

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
)

# ==========================================================
# Bind Tools
# ==========================================================

llm_with_tools = llm.bind_tools(
    [calculator, weather]
)

# ==========================================================
# Test Queries
# ==========================================================

queries = [
    "What is 25 + 17?",
    "What is the weather in Chennai?",
    "Who created LangGraph?"
]

# ==========================================================
# Run
# ==========================================================

print("=" * 60)
print("Example 06 - LLM Tool Calling")
print("=" * 60)

for query in queries:

    print(f"\nUser: {query}")

    response = llm_with_tools.invoke(query)

    # Display model response
    if response.content:
        print("\nAI Response:")
        print(response.content)

    # Check if model requested tools
    if response.tool_calls:

        print("\nTool Requested:")

        for tool_call in response.tool_calls:

            print(f"Tool : {tool_call['name']}")
            print(f"Arguments : {tool_call['args']}")

            # Execute calculator
            if tool_call["name"] == "calculator":

                result = calculator.invoke(tool_call["args"])

            # Execute weather
            elif tool_call["name"] == "weather":

                result = weather.invoke(tool_call["args"])

            else:

                result = "Unknown Tool"

            print(f"\nTool Output: {result}")

        print("\nNOTE:")
        print("The tool result has NOT been sent back to the LLM yet.")
        print("Example 07 will use LangGraph to complete this loop.")

    else:

        print("\nNo tool was required.")

    print("-" * 60)