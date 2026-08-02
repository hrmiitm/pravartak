"""
config.py

Configuration for the AI Assistant.
"""

from langchain_ollama import ChatOllama

# ==========================================================
# LLM
# ==========================================================

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
)