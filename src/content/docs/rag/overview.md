---
title: RAG (Retrieval-Augmented Generation)
description: Build a local RAG pipeline with ChromaDB, Ollama embeddings, and hybrid BM25 + vector search, then augment a prompt and generate a grounded answer.
sidebar:
  order: 1
---

By the end of this lesson, you will be able to turn a set of documents into embeddings, store and search them in a vector database, combine semantic (cosine similarity) and keyword (BM25) retrieval with reciprocal rank fusion, augment a prompt with retrieved context, and generate a grounded answer with a local LLM.

:::caution[Local services required]
This lesson runs entirely on your machine through [Ollama](https://ollama.com). Start Ollama and pull the two models used below before running any code:

```bash
ollama pull nomic-embed-text
ollama pull gemma3:12b
```
:::

## Setup

The project uses ChromaDB for the vector store, Ollama for embeddings and generation, and `rank-bm25` for keyword search. Dependencies are defined in `pyproject.toml`:

```toml
dependencies = [
    "fastapi[standard]>=0.139.0",
    "langchain>=1.3.13",
    "langchain-chroma>=1.1.0",
    "langchain-classic>=1.0.8",
    "langchain-community>=0.4.2",
    "ollama>=0.6.2",
    "rank-bm25>=0.2.2",
]
```

Install them with:

```bash
uv sync
```

The example works over a small in-memory document set and a single query:

```python
query = "What is my name ?"
docs = [
    "My name is nikhil",
    "This is a document about pineapple",
    "I drive a blue car.",
    "Oranges are orange in color.",
    "We are going to be grandparents soon.",
    "Pineapples are green in color.",
    "This is a document about oranges",
    "I have been driving for 3 years now.",
]
```

## What is RAG?

A language model only knows what was in its training data. **Retrieval-Augmented Generation (RAG)** grounds the model in *your* documents by fetching the most relevant passages at question time and placing them into the prompt. This reduces hallucination and lets the model answer from private or up-to-date sources.

Every RAG system has three stages:

```text
              ┌── RETRIEVE ──┐   ┌── AUGMENT ──┐   ┌── GENERATE ──┐
question ───▶ vector + BM25 ─▶  build a prompt ─▶  LLM answers ─▶ answer
              search          with the context     from context
```

1. **Retrieve** — find the passages most relevant to the question.
2. **Augment** — insert those passages into the prompt as context.
3. **Generate** — have the LLM answer *using only that context*.

## Embedding models

Search over meaning requires turning text into numbers. An **embedding** is a vector (a list of floats) that captures the semantic content of a piece of text; similar meanings produce nearby vectors.

This project uses Ollama's `nomic-embed-text` model as the embedding function:

```python
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

embedding_func = OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)
```

The same embedding function must be used for both the stored documents and the query, so that both live in the same vector space and can be compared.

## Vector databases

A **vector database** stores embeddings and indexes them for fast similarity search. Here we use ChromaDB. Creating a collection with the embedding function means Chroma will embed documents automatically as you add them:

```python
import chromadb

COLLECTION_NAME = "my_collection"

def initialize_vectordb(docs=None, embedding_func=None):
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func,
    )
    ids = [f"id{i}" for i in range(1, len(docs) + 1)]
    collection.add(ids=ids, documents=docs)
    return collection

collection = initialize_vectordb(docs, embedding_func)
```

Each document gets a unique `id`. Chroma embeds each `document`, stores the vector alongside the id, and keeps the original text for retrieval.

## Retrieval — vector search (cosine similarity)

To search, embed the query and find the stored vectors closest to it. Closeness is measured with **cosine similarity** — the cosine of the angle between two vectors. A value near `1` means the meanings are very similar; near `0` means unrelated.

```python
def search_vectordb(query, n_results=2):
    results = collection.query(
        query_texts=[query],  # Chroma embeds this with the same function
        n_results=n_results,  # how many results to return
    )
    return results["documents"][0]

retrieved_chunks = search_vectordb(query=query)
```

For `"What is my name ?"`, the semantically closest document is `"My name is nikhil"`, even though the query and document share almost no words. That is the strength of vector search: it matches on *meaning*, not exact tokens.

## Retrieval — keyword search (BM25)

Vector search can miss exact terms, product codes, or rare names. **BM25** is a classic lexical ranking function that scores documents by term overlap with the query, weighting rarer words more heavily.

```python
from rank_bm25 import BM25Okapi

tokenized_docs = [doc.lower().split() for doc in docs]
bm25 = BM25Okapi(tokenized_docs)

tokenized_query = query.lower().split()
bm25_scores = bm25.get_scores(tokenized_query)

bm25_rank = sorted(
    range(len(bm25_scores)),
    key=lambda i: bm25_scores[i],
    reverse=True,
)
```

`bm25_rank` is the list of document indices ordered from most to least relevant by keyword overlap.

## Hybrid search & Reciprocal Rank Fusion

Semantic and keyword search have complementary strengths, so combine them. First get the vector ranking across all documents:

```python
vector_results = collection.query(query_texts=[query], n_results=len(docs))

vector_rank = [
    int(doc_id.replace("id", "")) - 1
    for doc_id in vector_results["ids"][0]
]
```

Now merge the two rankings with **Reciprocal Rank Fusion (RRF)**. RRF ignores raw scores (which are on different scales) and instead rewards documents that rank highly in *either* list. Each document earns `1 / (k + rank)` from each ranker, and the contributions are summed:

```python
from collections import defaultdict

rrf_scores = defaultdict(float)
k = 60

for rank, doc_id in enumerate(bm25_rank):
    rrf_scores[doc_id] += 1 / (k + rank)

for rank, doc_id in enumerate(vector_rank):
    rrf_scores[doc_id] += 1 / (k + rank)

final_rank = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

for idx, score in final_rank:
    print(f"{score:.4f}  {docs[idx]}")
```

The constant `k` (commonly `60`) dampens the influence of the very top ranks so lower-ranked-but-agreed-upon documents still contribute. In LangChain the same idea is available through `EnsembleRetriever`, which fuses a `BM25Retriever` and a vector retriever for you.

## Augmentation

With the best chunks retrieved, build the prompt. The retrieved text becomes the **context**, and a strict instruction keeps the model from answering beyond it:

```python
context = "\n".join(retrieved_chunks)
prompt = f"""You are a intelligent chatbot which answers the user query, using the context information given.
If you dont have enough information in the context to answer the user query, reply with 'I dont have enough information.'
<CONTEXT>
{context}
<CONTEXT>

<User Query>
{query}
<User Query>
"""
```

The "I dont have enough information." guardrail is what makes the answer *grounded*: the model is told to refuse rather than guess when the context does not contain the answer.

## Generation

Finally, send the augmented prompt to a local LLM (`gemma3:12b`) through Ollama's generate endpoint:

```python
import requests

def ollama_generate(prompt, OLLAMA_MODEL="gemma3:12b", temperature=0.8, top_p=0.95, max_tokens=1024):
    """Call an LLM via Ollama and return the generated text."""
    OLLAMA_URL = "http://localhost:11434/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        },
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["response"]

response = ollama_generate(prompt)
print(response)
```

- `temperature` controls randomness; lower values give more deterministic answers.
- `top_p` (nucleus sampling) limits the model to the most probable tokens.
- `num_predict` (`max_tokens`) caps the length of the response.

Because the prompt only contains the retrieved chunks, the model answers `"What is my name ?"` from `"My name is nikhil"` rather than from its training data.

## Key takeaways

| Concept | What it does |
|---|---|
| Embeddings | Turn text into vectors so meaning can be compared numerically |
| Vector database | Stores and indexes embeddings for fast similarity search (ChromaDB) |
| Cosine similarity | Ranks documents by semantic closeness to the query |
| BM25 | Ranks documents by keyword overlap; strong on exact terms |
| Hybrid + RRF | Fuses semantic and keyword rankings into one robust order |
| Augmentation | Injects retrieved context into a grounded prompt |
| Generation | LLM answers using only the supplied context |

## Knowledge check

1. Why must the query and the documents use the *same* embedding function?
2. When would BM25 outperform vector search, and vice versa?
3. What problem does Reciprocal Rank Fusion solve that simply adding raw scores does not?
4. What is the purpose of the "I dont have enough information." instruction in the prompt?
5. Which generation parameter would you lower to make answers more deterministic?

<details>
<summary>Suggested answers</summary>

1. Both must live in the same vector space; comparing vectors from different models is meaningless.
2. BM25 wins on exact terms, names, codes, and rare tokens; vector search wins when the query and document share meaning but not words.
3. Raw scores from BM25 and vector search are on different, incomparable scales; RRF combines them fairly using rank position instead of magnitude.
4. It grounds the model, telling it to refuse rather than hallucinate when the context lacks the answer.
5. Lower the `temperature` (and optionally `top_p`).

</details>

## Assignment

1. Add metadata to each document (for example a `source` or `category`) and filter results by metadata during retrieval.
2. Experiment with `n_results` and the RRF constant `k`; observe how the final ranking changes.
3. Swap `nomic-embed-text` or `gemma3:12b` for another Ollama model and compare answer quality.
4. Replace the manual RRF code with LangChain's `EnsembleRetriever` combining a `BM25Retriever` and a Chroma vector retriever.
5. Wrap the retrieve → augment → generate flow in a FastAPI endpoint (the `fastapi` dependency is already included) that accepts a query and returns the grounded answer.
