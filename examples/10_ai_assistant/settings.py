"""
Global settings for the workshop.
"""

LEARN_MODE = False

# Which LLM backend to use: "local" (Ollama, no API cost, no
# network dependency beyond localhost) or "cloud" (OpenAI,
# requires OPENAI_API_KEY).
#
# Can be overridden at runtime without editing this file by
# setting the LLM_BACKEND environment variable -- useful for
# batch/eval runs where you want to compare backends without
# a code change each time.
LLM_BACKEND = "local"