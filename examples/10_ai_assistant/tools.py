"""
tools.py

All tools used by the AI Assistant.
"""

from apis.wikipedia import search_wikipedia
from apis.weather import get_weather
from apis.vulnerabilities import get_vulnerability

import ast
import operator
import json
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
    Get the current weather for a city.
    """

    if settings.LEARN_MODE:
        print("\n🛠 Current Node : ToolNode")
        print("⚙ Tool         : Weather")
        print(f"🌍 Looking up   : {city}")

    try:

        weather_data = get_weather(city)

        result = (
            f"Weather for {weather_data['city']}\n"
            f"Condition: {weather_data['condition']}\n"
            f"Temperature: {weather_data['temperature']}°C\n"
            f"Feels Like: {weather_data['feels_like']}°C\n"
            f"Humidity: {weather_data['humidity']}%\n"
            f"Wind Speed: {weather_data['wind_speed']} km/h"
        )

        if settings.LEARN_MODE:
            print("✅ API Call     : Successful")

        return result

    except Exception as e:

        if settings.LEARN_MODE:
            print("❌ API Error")

        return str(e)


# ==========================================================
# Wikipedia Tool
# ==========================================================

@tool
def wikipedia(query: str) -> str:
    """
    Search Wikipedia for factual information.
    """

    if settings.LEARN_MODE:
        print("\n🛠 Current Node : ToolNode")
        print("⚙ Tool         : Wikipedia")
        print(f"🔍 Searching    : {query}")

    try:

        result = search_wikipedia(query)

        if settings.LEARN_MODE:
            print("📄 Summary Retrieved")

        return result

    except Exception as e:

        if settings.LEARN_MODE:
            print("❌ Wikipedia API Error")

        return str(e)


# ==========================================================
# Vulnerability Intelligence Tool
# ==========================================================

@tool
def vulnerability_lookup(cve_id: str) -> str:
    """
    Look up a CVE vulnerability and return structured
    vulnerability intelligence as JSON.
    """

    if settings.LEARN_MODE:
        print("\n🔐 Current Node : ToolNode")
        print("⚙ Tool         : Vulnerability Lookup")
        print(f"🔐 CVE          : {cve_id}")

    try:

        vulnerability = get_vulnerability(cve_id)

        result = {
            "cve_id": vulnerability["cve_id"],
            "severity": vulnerability["severity"],
            "cvss_score": vulnerability["cvss_score"],
            "published": vulnerability["published"],
            "last_modified": vulnerability["last_modified"],
            "description": vulnerability["description"],
            "source": "NVD",
        }

        if settings.LEARN_MODE:
            print("✅ Vulnerability data retrieved.")

        return json.dumps(result)

    except Exception as exc:

        if settings.LEARN_MODE:
            print("❌ Vulnerability lookup failed.")

        return json.dumps({
            "cve_id": cve_id,
            "source": "NVD",
            "status": "error",
            "error": str(exc),
        })


# ==========================================================
# Register Tools
# ==========================================================

TOOLS = [
    calculator,
    weather,
    wikipedia,
    vulnerability_lookup,
]


tool_node = ToolNode(TOOLS)