"""
wikipedia.py

Wikipedia service.

No LangChain code belongs here.
"""

import wikipedia


def search_wikipedia(query: str):
    """
    Fetch a short summary from Wikipedia.
    """

    wikipedia.set_lang("en")

    try:

        summary = wikipedia.summary(
            query,
            sentences=3,
            auto_suggest=False,
        )

        return summary

    except wikipedia.DisambiguationError as e:

        return (
            f"Your search is ambiguous. "
            f"Try one of these: {', '.join(e.options[:5])}"
        )

    except wikipedia.PageError:

        return "No Wikipedia page was found."

    except Exception as e:

        return f"Wikipedia Error: {e}"