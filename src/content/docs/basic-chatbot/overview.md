---
title: Basic Chatbot
description: Build a conversational chatbot with LangChain and Google Gemini, moving from single prompts to multi-turn chat and dynamic prompt templates.
sidebar:
  order: 1
---

By the end of this lesson, you will be able to send a single-turn prompt to an LLM, structure multi-turn conversations with message types, use prompt templates with dynamic variables, and understand how chaining connects steps into a pipeline.


:::caution[API keys]
The example embeds an API key in the source file for brevity. In a real project, store it in a `.env` file and use `python-dotenv` to load it. Never commit a key to Git.
:::

## Setup

The script uses LangChain with Google Gemini. Dependencies are defined in `pyproject.toml`:

```toml
dependencies = [
    "langchain>=1.3.12",
    "langchain-google-genai>=4.2.7",
    "python-dotenv>=1.2.2",
]
```

Install them with:

```bash
uv sync
```

Set the API key and initialise the model:

```python
import os
from langchain_google_genai import ChatGoogleGenerativeAI

os.environ["GOOGLE_API_KEY"] = "your-key-here"

model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=1.0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
```

`ChatGoogleGenerativeAI` wraps the Gemini chat endpoint. The `temperature` controls randomness — higher values produce more varied output.

## Lesson 1: basic prompting

A prompt is just a list of message tuples. The simplest form pairs a role with a string:

```python
query = "What is your name, who built you ?"
messages = [("human", query)]
response = model.invoke(messages)
```

The `("human", query)` tuple is shorthand for `HumanMessage(query)`. The model receives the message and returns an `AIMessage` with the generated text.

## Lesson 2: chat history

A conversation uses multiple messages. The model sees the full sequence and treats it as a dialogue:

```python
from langchain_core.messages import HumanMessage, AIMessage

messages = [
    HumanMessage("Hello, my name is Nikhil !!"),
    AIMessage("Hello Nikhil, How can I help you today ?"),
    HumanMessage("What is my name?"),
]
response = model.invoke(messages)
```

Because the chat history contains `"Hello, my name is Nikhil !!"` followed by the assistant's acknowledgement, the model can answer `"What is my name?"` correctly. The order of messages matters — earlier messages establish context.

Three message types are available:

| Type | Purpose |
|---|---|
| `HumanMessage` | User input |
| `AIMessage` | Model response (also used to provide example turns) |
| `SystemMessage` | Instructions that set behaviour for the whole conversation |

## Lesson 3: prompt templates

Hard-coding every message works for fixed conversations, but real applications need dynamic values. `ChatPromptTemplate` lets you inject variables at runtime:

```python
from langchain_core.prompts import ChatPromptTemplate

query = "What is todays date and what day is it today ?"

chat_history = [
    HumanMessage("Hello, my name is Nikhil !!"),
    AIMessage("Hello Nikhil, How can I help you today ?"),
]
formatted_messages = []
for msg in messages:
    formatted_messages.append(f"{msg.type}: {msg.content}")
chat_history = "\n".join(formatted_messages)

prompt = ChatPromptTemplate(messages=[
    SystemMessage("""You are a strictly information-bounded assistant.

There is NO retrieved document context available for this turn.
You must follow these rules:

1. You are NOT allowed to use general knowledge.
2. You are NOT allowed to use any knowledge from training data.
3. You are NOT allowed to infer, assume, or guess.
4. You may use chat history ONLY if the required information is explicitly present there.
5. If the answer is not explicitly present in the chat history, respond exactly:
   "I don't have enough information to answer that."
6. Do not fabricate facts.
7. Do not provide partially correct answers.
"""),
    SystemMessage("""
CHAT HISTORY
<chat_history>
{chat_history}
</chat_history>
"""),
    HumanMessage("""
USER QUESTION:
{query}

Respond in Markdown.
"""),
    AIMessage("Here is a response in Markdown:\n---\n\n"),
])

messages = prompt.format_messages(
    chat_history=chat_history,
    query=query
)

response = model.invoke(messages)
print(response.content[0]['text'])
```

This template demonstrates several techniques:

1. **System messages enforce behaviour** — the first system message restricts the model to answer only from chat history.
2. **Placeholders `{chat_history}` and `{query}`** are replaced at call time by `format_messages()`.
3. **A seed `AIMessage`** primes the model to begin its answer in Markdown.

The `SystemMessage` rules act as a guard — the model will refuse to answer questions whose answer is not in the provided history, mimicking a retrieval-augmented system where the model has access only to retrieved context.

## Lesson 4: chaining (pipeline)

The fourth section is a placeholder for chaining — connecting the prompt template and model call into a reusable pipeline. In LangChain this is done with the `|` operator (LCEL):

```python
chain = prompt | model
response = chain.invoke({"chat_history": chat_history, "query": query})
```

A real pipeline might also add output parsing, memory, or retrieval steps. This pattern is the foundation of the RAG systems covered in later lessons.

## Key takeaways

| Concept | What it enables |
|---|---|
| Message tuples | Quick single-turn prompts with `("role", "content")` |
| Chat history | Multi-turn conversations with `HumanMessage` and `AIMessage` |
| `SystemMessage` | Behavioural instructions that persist across turns |
| `ChatPromptTemplate` | Dynamic prompts with variables like `{query}` and `{chat_history}` |
| Chaining (LCEL) | Composable pipelines that connect prompt → model → output parser |

## Knowledge check

1. What is the difference between `("human", "Hello")` and `HumanMessage("Hello")`?
2. Why does the model in Lesson 2 know the user's name?
3. What happens in Lesson 3 when the query asks something not in the chat history?
4. What role does the seed `AIMessage` play in the prompt template?

<details>
<summary>Suggested answers</summary>

1. They are equivalent — the tuple is shorthand that LangChain converts to `HumanMessage` internally.
2. The sequence contains `HumanMessage("Hello, my name is Nikhil !!")` followed by the assistant's greeting, so the model has the name in context when it sees the follow-up question.
3. The system message instructs the model to reply `"I don't have enough information to answer that."` — it will refuse to use its training data.
4. It provides an example start to the assistant's response, encouraging the model to continue in Markdown format rather than plain text.

</details>

## Assignment

1. Change the system prompt in Lesson 3 to require answers in JSON format instead of Markdown.
2. Add a third variable `user_name` to the prompt template and inject it in the system instructions.
3. Replace the hard-coded chat history with a list that grows as the conversation progresses.
4. Connect the prompt template to the model using the `|` operator (LCEL) and verify it produces the same result.
