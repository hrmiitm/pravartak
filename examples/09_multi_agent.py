"""
====================================================================
Example 09 : Multi-Agent System using LangGraph
====================================================================

Author : IITM Pravartak Workshop

Learning Objectives
-------------------
1. Understand Multi-Agent Systems.
2. Build a Supervisor Agent.
3. Create specialized AI agents.
4. Route tasks between agents.
5. Understand modular AI architecture.

Architecture
------------

                    User
                      │
                      ▼
               Supervisor Agent
            ┌────────┼─────────┐
            ▼        ▼         ▼
       Math Agent  Weather   Knowledge
            │        │         │
            └────────┼─────────┘
                     ▼
                    END

Each agent has ONE responsibility.

Math Agent
-----------
Handles calculations.

Weather Agent
-------------
Handles weather questions.

Knowledge Agent
---------------
Handles general questions.

Supervisor
----------
Chooses the correct agent.
"""

# ==========================================================
# Imports
# ==========================================================

import ast
import operator

from typing import Literal
from typing import TypedDict

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from langchain_ollama import ChatOllama

from langgraph.graph import (
    START,
    END,
    StateGraph,
)

# ==========================================================
# State
# ==========================================================

class AgentState(TypedDict):

    question: str

    route: str

    answer: str


# ==========================================================
# Local LLM
# ==========================================================

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
)

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

    raise ValueError("Unsupported expression")


# ==========================================================
# Math Tool
# ==========================================================

def calculator(expression: str):

    tree = ast.parse(
        expression,
        mode="eval",
    )

    return str(
        evaluate(tree.body)
    )


# ==========================================================
# Weather Tool
# ==========================================================

def weather(city: str):

    return f"It is currently sunny in {city}."


print("\n")
print("=" * 65)
print("MULTI-AGENT ARCHITECTURE")
print("=" * 65)

print("""
                    User
                      │
                      ▼
               Supervisor Agent
            ┌────────┼─────────┐
            ▼        ▼         ▼
       Math Agent  Weather   Knowledge
            │        │         │
            └────────┼─────────┘
                     ▼
                    END
""")

print("=" * 65)
# ==========================================================
# Supervisor Agent
# ==========================================================

SUPERVISOR_PROMPT = """
You are a Supervisor Agent.

Your job is ONLY to decide which specialist should answer.

Available specialists:

1. math
   - arithmetic
   - calculations
   - numbers

2. weather
   - weather
   - temperature
   - rain
   - forecast

3. knowledge
   - everything else

Respond using ONLY one word.

math
weather
knowledge
"""


def supervisor(state: AgentState):

    print("\n" + "=" * 60)
    print("SUPERVISOR AGENT")
    print("=" * 60)

    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=state["question"]),
    ]

    response = llm.invoke(messages)

    route = response.content.lower().strip()

    print(f"Route Selected : {route}")

    return {
        "route": route,
    }


# ==========================================================
# Math Agent
# ==========================================================

def math_agent(state: AgentState):

    print("\nMath Agent Activated")

    expression = state["question"]

    # Very simple extraction for workshop purposes
    expression = (
        expression.replace("What is", "")
        .replace("?", "")
        .strip()
    )

    answer = calculator(expression)

    return {
        "answer": f"The answer is {answer}.",
    }


# ==========================================================
# Weather Agent
# ==========================================================

def weather_agent(state: AgentState):

    print("\nWeather Agent Activated")

    city = "Chennai"

    question = state["question"].lower()

    if "delhi" in question:
        city = "Delhi"

    elif "mumbai" in question:
        city = "Mumbai"

    elif "bangalore" in question:
        city = "Bangalore"

    elif "hyderabad" in question:
        city = "Hyderabad"

    answer = weather(city)

    return {
        "answer": answer,
    }


# ==========================================================
# Knowledge Agent
# ==========================================================

KNOWLEDGE_PROMPT = """
You are a helpful AI assistant.

Answer clearly and concisely.
"""


def knowledge_agent(state: AgentState):

    print("\nKnowledge Agent Activated")

    messages = [
        SystemMessage(content=KNOWLEDGE_PROMPT),
        HumanMessage(content=state["question"]),
    ]

    response = llm.invoke(messages)

    return {
        "answer": response.content,
    }


# ==========================================================
# Router
# ==========================================================

def route_question(state: AgentState):

    route = state["route"]

    if "math" in route:
        return "math"

    if "weather" in route:
        return "weather"

    return "knowledge"


# ==========================================================
# Build Graph
# ==========================================================

builder = StateGraph(AgentState)

builder.add_node(
    "supervisor",
    supervisor,
)

builder.add_node(
    "math",
    math_agent,
)

builder.add_node(
    "weather",
    weather_agent,
)

builder.add_node(
    "knowledge",
    knowledge_agent,
)

builder.add_edge(
    START,
    "supervisor",
)

builder.add_conditional_edges(
    "supervisor",
    route_question,
)

builder.add_edge(
    "math",
    END,
)

builder.add_edge(
    "weather",
    END,
)

builder.add_edge(
    "knowledge",
    END,
)

graph = builder.compile()

# ==========================================================
# Helper Function
# ==========================================================

def print_result(state):

    print("\n" + "=" * 65)
    print("FINAL RESPONSE")
    print("=" * 65)

    print(state["answer"])

    print("=" * 65)


# ==========================================================
# Demo Queries
# ==========================================================

queries = [

    "What is (125 + 375) * 2?",

    "What is the weather in Chennai?",

    "Explain what LangGraph is.",

    "What is 250 * 16?",

]

print("\n")
print("=" * 65)
print("Example 09 : Multi-Agent System")
print("=" * 65)

for i, question in enumerate(queries, start=1):

    print(f"\n\nExample {i}")
    print("-" * 65)

    print(f"User : {question}")

    result = graph.invoke(
        {
            "question": question,
            "route": "",
            "answer": "",
        }
    )

    print_result(result)

print("\n")
print("=" * 65)
print("MULTI-AGENT DEMO COMPLETE")
print("=" * 65)

# ==========================================================
# Teaching Notes
# ==========================================================

print(
"""
================================================================

TEACHING NOTES

================================================================

Traditional AI

User
 │
 ▼
Single Agent
 │
 ▼
Answer

---------------------------------------------------------------

Multi-Agent AI

                 User
                   │
                   ▼
             Supervisor Agent
           ┌───────┼────────┐
           ▼       ▼        ▼
       Math     Weather   Knowledge
           │       │        │
           └───────┴────────┘
                   ▼
                Final Answer

----------------------------------------------------------------

Responsibilities

Supervisor
-----------
Routes the request.

Math Agent
----------
Handles calculations.

Weather Agent
-------------
Handles weather queries.

Knowledge Agent
---------------
Handles general questions.

Benefits

✓ Easier to maintain

✓ Easier to debug

✓ Easier to extend

✓ Better scalability

✓ Cleaner prompts

✓ Modular architecture

================================================================
"""
)

# ==========================================================
# Exercises
# ==========================================================

print(
"""
================================================================

Exercises

================================================================

1. Add a Finance Agent.

2. Add a Coding Agent.

3. Add a Translation Agent.

4. Add a Medical Agent.

5. Add a Travel Agent.

6. Add a News Agent.

7. Add a Research Agent.

8. Create a Hierarchical Multi-Agent System.

================================================================

Interview Questions

================================================================

1. What is a Multi-Agent System?

2. Why use a Supervisor Agent?

3. What are the benefits of specialization?

4. How does routing work?

5. How is this different from ReAct?

6. When should you choose Multi-Agent over a
   single agent?

7. What are the disadvantages of Multi-Agent
   systems?

================================================================

Best Practices

================================================================

✓ Give each agent one responsibility.

✓ Keep prompts small.

✓ Keep tools specific.

✓ Route before reasoning.

✓ Make agents reusable.

✓ Keep agents independent.

✓ Add tracing with LangSmith.

================================================================
"""
)