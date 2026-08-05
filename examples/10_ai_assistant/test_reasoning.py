from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:4b",
    reasoning=False,
    temperature=0,
)

response = llm.invoke("Say hello in one sentence.")

print(response.content)