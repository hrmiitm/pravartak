"""
config.py

LLM backend configuration.

Supports two backends, toggled via settings.LLM_BACKEND (or the
LLM_BACKEND environment variable, which takes precedence):

- "local" : Ollama, running qwen2.5:7b-instruct locally. No API
            cost, no network dependency beyond localhost. Requires
            Ollama installed and running, with the model pulled:
                ollama pull qwen2.5:7b-instruct

- "cloud" : OpenAI, gpt-4o-mini. Requires the OPENAI_API_KEY
            environment variable to be set, and the langchain-openai
            package installed (pip install langchain-openai if not
            already present).

Both backends are constructed with temperature=0 for deterministic
tool-calling behavior, matching the rest of this project's emphasis
on reproducibility.
"""

import os

import settings


_backend = os.environ.get(
    "LLM_BACKEND",
    settings.LLM_BACKEND,
).strip().lower()


if _backend == "local":

    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model="qwen2.5:7b-instruct",
        temperature=0,
    )

elif _backend == "cloud":

    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

else:

    raise ValueError(
        f"Unknown LLM_BACKEND: {_backend!r}. "
        "Expected 'local' or 'cloud'."
    )