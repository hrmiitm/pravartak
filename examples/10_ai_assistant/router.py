"""
router.py

Intent detection for the LangGraph Supervisor.

The Supervisor should be lightweight and deterministic.
Instead of asking an LLM where to route every request,
we classify the user's intent using simple rules.
"""

import re


# ==========================================================
# Intent Patterns
# ==========================================================
MEMORY_PATTERNS = [
    r"\bremember our\b",
    r"\bwhat is our\b",
    r"\bwhat's our\b",
    r"\bremember\b",
]

WEATHER_PATTERNS = [
    r"\bweather\b",
    r"\btemperature\b",
    r"\brain\b",
    r"\bsunny\b",
    r"\bforecast\b",
    r"\bhumidity\b",
]

CALCULATOR_PATTERNS = [
    r"\bcalculate\b",
    r"\bsolve\b",
    r"\bcompute\b",
    r"\d+\s*[\+\-\*/]\s*\d+",
    r"\(",
]

WIKIPEDIA_PATTERNS = [
    r"\bwho is\b",
    r"\btell me about\b",
    r"\bhistory of\b",
    r"\bwhen was\b",
    r"\bwhere is\b",
    r"\bwho invented\b",
]

SECURITY_PATTERNS = [
    r"\bcve-\d{4}-\d{4,}\b",
    r"\bvulnerability\b",
    r"\bsecurity advisory\b",
    r"\bcvss\b",
    r"\bexploit\b",
    r"\bseverity\b",
]


# ==========================================================
# Pattern Matcher
# ==========================================================

def _matches(patterns, text):

    return any(
        re.search(pattern, text)
        for pattern in patterns
    )


# ==========================================================
# Intent Detector
# ==========================================================

def detect_intent(text: str) -> str:
    """
    Returns one of:

    memory
    weather
    calculator
    wikipedia
    assistant
    """

    text = text.lower()



    if _matches(MEMORY_PATTERNS, text):
        return "memory"

    if _matches(WEATHER_PATTERNS, text):
        return "weather"

    if _matches(SECURITY_PATTERNS, text):
        return "security"

    if _matches(CALCULATOR_PATTERNS, text):
        return "calculator"

    if _matches(WIKIPEDIA_PATTERNS, text):
        return "wikipedia"

    return "assistant"
