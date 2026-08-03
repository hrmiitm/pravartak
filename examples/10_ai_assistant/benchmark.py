import time
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
)

start = time.perf_counter()

response = llm.invoke("Say hello in one sentence.")

end = time.perf_counter()

print(response.content)
print(f"\nTime: {end - start:.3f} sec")