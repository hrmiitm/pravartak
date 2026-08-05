"""
app.py

AI Assistant (Capstone)

Run:
    python app.py
"""
from database import initialize_database
import time
import settings

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)

from graph import app

# ==========================================================
# Banner
# ==========================================================

print("=" * 70)
print("🤖 LANGGRAPH WORKSHOP")
print("=" * 70)
print("Choose a mode:\n")
print("1. Learn Mode (Visualize LangGraph)")
print("2. Chat Mode (Normal Assistant)\n")

mode = input("Select mode (1/2): ").strip()

settings.LEARN_MODE = (mode == "1")
initialize_database()
print()
print("=" * 70)

if settings.LEARN_MODE:
    print("🎓 Learn Mode Enabled")
else:
    print("💬 Chat Mode Enabled")

print("=" * 70)
print("Type 'exit' to quit.\n")
# ==========================================================
# Chat Loop
# ==========================================================

while True:

    question = input("You > ").strip()

    if question.lower() in ("exit", "quit"):

        print("\nAssistant > Goodbye! 👋")
        break

    try:
        start = time.perf_counter()

        result = app.invoke(
            {
                "messages": [
                    HumanMessage(content=question)
                ],
                "route": "",
                "profile": {},
            }
        )
        end = time.perf_counter()

        print("\nAssistant >")

        ai_messages = [
            m for m in result["messages"]
            if isinstance(m, AIMessage)
        ]

        if ai_messages:

            print(ai_messages[-1].content)

        else:

            print("No response generated.")

        if settings.LEARN_MODE:
            print("\n" + "=" * 70)
            print("📊 EXECUTION SUMMARY")
            print("=" * 70)
            print(f"⏱ Total Time : {end - start:.3f} sec")
            print("=" * 70)
            print()

    except Exception as e:

        print("\nError:")
        print(e)

